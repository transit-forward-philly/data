"""Match stop visits to the published schedule and summarize delay by route.

Source:   $TFP_DATA_DIR/septa_tracking/stop_visits/   (from stop_visits.py)
          $TFP_DATA_DIR/septa_gtfs/trips_index.parquet (from ../septa_gtfs_archive)
Produces: $TFP_DATA_DIR/septa_tracking/trip_runs.parquet (one row per trip run)
          datasets/septa_bus_delay/*.csv                  (committed to the repo)
Run:      python aggregate.py

Each trip run is matched to the GTFS schedule version that was in force on its
service day: the latest version that took effect on or before that day and
contains the trip_id. That gives the route as published, direction, and
scheduled start hour.

The tables are descriptive only (counts and delay percentiles). Choices like
an on-time cutoff or peak-period windows are left to whoever uses the data.
"""

from pathlib import Path

import duckdb

from common import MEMORY_LIMIT, THREADS, data_dir

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "datasets" / "septa_bus_delay"

MODES = """
    CASE route_type WHEN '3' THEN 'bus' WHEN '0' THEN 'trolley'
                    WHEN '1' THEN 'metro' WHEN '2' THEN 'rail'
                    WHEN '11' THEN 'trackless_trolley' ELSE 'other' END
"""


def delay_stats(d="delay_minutes"):
    return f"""
        round(approx_quantile({d}, 0.5), 1) AS median_delay_min,
        round(avg({d}), 2) AS mean_delay_min,
        round(approx_quantile({d}, 0.1), 1) AS p10_delay_min,
        round(approx_quantile({d}, 0.9), 1) AS p90_delay_min
    """


VISIT_METRICS = f"""
    count(DISTINCT run_key) AS trips_observed,
    count(*) AS stop_visits,
    {delay_stats()}
"""


def build_runs(con, visits, work, runs_path):
    con.execute(
        f"""
        COPY (
        WITH r AS (
            SELECT trip_id, run_start, any_value(service_date) AS service_date,
                   count(*) AS stop_visits,
                   arg_min(delay_minutes, reached_at) AS first_delay_min,
                   arg_max(delay_minutes, reached_at) AS last_delay_min
            FROM {visits} GROUP BY trip_id, run_start
        ),
        candidates AS (
            SELECT r.trip_id, r.run_start, t.*,
                   row_number() OVER (PARTITION BY r.trip_id, r.run_start
                                      ORDER BY t.feed_effective DESC, t.feed_version DESC) AS pick
            FROM r
            JOIN read_parquet('{work}/septa_gtfs/trips_index.parquet') t
              ON t.trip_id = r.trip_id AND t.feed = 'bus'
             AND t.feed_effective <= r.service_date
        )
        SELECT r.*, strftime(r.service_date, '%Y-%m') AS month,
               CASE dayofweek(r.service_date) WHEN 0 THEN 'sunday'
                    WHEN 6 THEN 'saturday' ELSE 'weekday' END AS day_type,
               c.feed_version, c.route_short_name, {MODES} AS mode,
               c.direction_id, c.trip_headsign,
               CAST(split_part(c.first_departure, ':', 1) AS INTEGER) AS start_hour
        FROM r LEFT JOIN candidates c
          ON c.trip_id = r.trip_id AND c.run_start = r.run_start AND c.pick = 1
        ) TO '{runs_path}' (FORMAT parquet)
        """
    )


def main():
    work = data_dir()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute(f"SET temp_directory = '{work / 'duckdb_tmp'}'")
    con.execute(f"SET memory_limit = '{MEMORY_LIMIT}'")
    con.execute(f"SET threads = {THREADS}")
    con.execute("SET preserve_insertion_order = false")

    visits = (f"read_parquet('{work}/septa_tracking/stop_visits/*/*.parquet', "
              "hive_partitioning = true)")
    runs_path = work / "septa_tracking" / "trip_runs.parquet"

    # One row per trip run (about 3M), matched to its schedule. This is the only
    # table built up front; each CSV below streams the stop visits against it.
    # Delete trip_runs.parquet and csv_parts/ to rebuild from scratch.
    if not runs_path.exists():
        build_runs(con, visits, work, runs_path)
    matched, total = con.execute(
        f"SELECT count(route_short_name), count(*) FROM '{runs_path}'"
    ).fetchone()
    print(f"matched {matched:,} of {total:,} trip runs to a schedule ({matched / total:.1%})")


    con.execute(f"CREATE TABLE runs AS SELECT * FROM '{runs_path}' "
                "WHERE route_short_name IS NOT NULL")
    months = [r[0] for r in con.execute("SELECT DISTINCT month FROM runs ORDER BY 1").fetchall()]

    # Tables with many groups are built a month at a time, reading only that
    # month's files, so DuckDB never has to hold the whole year's state.
    by_month = {
        "route_month.csv": (f"""
            SELECT mode, route_short_name AS route, month, {VISIT_METRICS}
            FROM v GROUP BY ALL""", "mode, route, month"),
        "route_month_hour.csv": (f"""
            SELECT mode, route_short_name AS route, direction_id, month, day_type,
                   start_hour AS scheduled_start_hour, {VISIT_METRICS}
            FROM v GROUP BY ALL""",
            "mode, route, direction_id, month, day_type, scheduled_start_hour"),
        "stop_route_month.csv": (f"""
            SELECT stop_id, mode, route_short_name AS route, direction_id, month,
                   {VISIT_METRICS}
            FROM v GROUP BY ALL HAVING count(*) >= 20""",
            "stop_id, route, direction_id, month"),
    }
    whole_year = {
        "route_end_of_trip_month.csv": f"""
            SELECT mode, route_short_name AS route, month, count(*) AS trips_observed,
                   {delay_stats('last_delay_min')}
            FROM runs GROUP BY ALL ORDER BY mode, route, month""",
        "coverage_by_day.csv": """
            SELECT service_date, count(*) AS trips_observed,
                   sum(stop_visits) AS stop_visits, count(DISTINCT route_short_name) AS routes
            FROM runs GROUP BY ALL ORDER BY service_date""",
    }

    parts = work / "septa_tracking" / "csv_parts"
    parts.mkdir(exist_ok=True)
    visit_dirs = work / "septa_tracking" / "stop_visits"
    for i, month in enumerate(months):
        # A trip's service month can differ from the calendar month of its stop
        # visits (late-night trips cross midnight), so read this month's files
        # and the next month's, and keep only trips in this service month.
        files = [f"'{visit_dirs}/month={m}/*.parquet'" for m in months[i:i + 2]]
        con.execute(
            f"""
            CREATE OR REPLACE VIEW v AS
            SELECT s.stop_id, s.delay_minutes, s.trip_id || '|' || s.run_start AS run_key,
                   runs.*
            FROM read_parquet([{', '.join(files)}]) s
            JOIN runs USING (trip_id, run_start)
            WHERE runs.month = '{month}'
            """
        )
        for name, (sql, _) in by_month.items():
            part = parts / f"{name}.{month}"
            if not part.exists():
                tmp = part.with_name(part.name + ".tmp")
                con.execute(f"COPY ({sql}) TO '{tmp}' (HEADER, DELIMITER ',')")
                tmp.rename(part)
        print(f"{month}: done", flush=True)

    for name, (_, order) in by_month.items():
        whole_year[name] = (f"SELECT * FROM read_csv('{parts}/{name}.*', all_varchar = true) "
                            f"ORDER BY {order}")
    for name, sql in whole_year.items():
        path = OUT_DIR / name
        con.execute(f"COPY ({sql}) TO '{path}' (HEADER, DELIMITER ',')")
        rows = con.execute(f"SELECT count(*) FROM read_csv('{path}')").fetchone()[0]
        print(f"wrote {name}: {rows:,} rows, {path.stat().st_size / 1e6:.1f} MB", flush=True)


if __name__ == "__main__":
    main()
