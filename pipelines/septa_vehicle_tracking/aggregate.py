"""Match stop visits to the published schedule and summarize delay by route.

Source:   $TFP_DATA_DIR/septa_tracking/stop_visits/   (from stop_visits.py)
          $TFP_DATA_DIR/septa_gtfs/trips_index.parquet (from ../septa_gtfs_archive)
Produces: $TFP_DATA_DIR/septa_tracking/trip_runs.parquet (one row per trip run)
          datasets/septa_bus_delay/*.csv                  (committed to the repo)
Run:      python aggregate.py

Each trip run is matched to the GTFS schedule version in force on its service
day (the latest version that took effect on or before that day). Trips whose
trip_id is not in that version are left unmatched rather than borrowed from an
older version, because SEPTA sometimes reuses a trip_id for a different route.
The match gives the published route, direction and scheduled start time, and
the scheduled start time sets the service day.

The tables are descriptive only (counts and delay percentiles). Choices like
an on-time cutoff or peak-period windows are left to whoever uses the data.
"""

import hashlib
import shutil
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


def input_fingerprint(work):
    """Changes whenever this script, the stop visits or the GTFS index change."""
    h = hashlib.sha256(Path(__file__).read_bytes())
    inputs = sorted((work / "septa_tracking" / "stop_visits").glob("month=*/*.parquet"))
    inputs.append(work / "septa_gtfs" / "trips_index.parquet")
    for path in inputs:
        stat = path.stat()
        h.update(f"{path}|{stat.st_size}|{stat.st_mtime_ns}\n".encode())
    return h.hexdigest()


def match_sql(trips, source, date_col):
    """Match each run in `source` to the GTFS version in force on `date_col`."""
    return f"""
        SELECT s.*, t.feed_version, upper(t.route_short_name) AS route_short_name,
               {MODES} AS mode, t.direction_id, t.trip_headsign,
               CAST(split_part(t.first_departure, ':', 1) AS INTEGER) AS start_hour,
               CAST(split_part(t.first_departure, ':', 1) AS INTEGER) * 3600
                 + CAST(split_part(t.first_departure, ':', 2) AS INTEGER) * 60
                 + CAST(split_part(t.first_departure, ':', 3) AS INTEGER) AS start_seconds
        FROM {source} s
        LEFT JOIN (
            SELECT s.trip_id, s.run_start, v.feed_version
            FROM {source} s ASOF JOIN versions v ON s.{date_col} >= v.feed_effective
        ) f USING (trip_id, run_start)
        LEFT JOIN {trips} t
          ON t.feed = 'bus' AND t.feed_version = f.feed_version AND t.trip_id = s.trip_id
    """


def build_runs(con, visits, work, runs_path):
    trips = f"read_parquet('{work}/septa_gtfs/trips_index.parquet')"
    con.execute(
        f"""
        COPY (
        WITH r AS (
            SELECT trip_id, run_start, any_value(service_date) AS observed_date,
                   count(*) AS stop_visits,
                   arg_min(delay_minutes, reached_at) AS first_delay_min,
                   arg_max(delay_minutes, reached_at) AS last_delay_min
            FROM {visits} GROUP BY trip_id, run_start
        ),
        -- SEPTA sometimes reissues a version for the same start date (v202608232,
        -- then v202608233). Keep only the latest reissue for each date, so the
        -- match is the same on every run.
        versions AS (
            SELECT feed_effective, max(feed_version) AS feed_version
            FROM {trips} GROUP BY feed_effective
        ),
        -- Pass 1: a rough match on the observed date, only to read the trip's
        -- scheduled start time. The service day is the local date whose midnight
        -- plus that start time lands nearest the first poll, which puts a 26:50
        -- (2:50 a.m.) owl trip on the day before, however late it was first seen.
        first_pass AS ({match_sql(trips, 'r', 'observed_date')}),
        dated AS (
            SELECT r.*,
                   coalesce(
                       CAST(timezone('America/New_York', r.run_start)
                            - to_seconds(m.start_seconds) + INTERVAL 12 HOUR AS DATE),
                       r.observed_date) AS service_date
            FROM r JOIN first_pass m USING (trip_id, run_start)
        ),
        -- Pass 2: the real match, against the version in force on the service day.
        final AS ({match_sql(trips, 'dated', 'service_date')})
        SELECT * EXCLUDE (start_seconds, observed_date),
               strftime(service_date, '%Y-%m') AS month,
               CASE dayofweek(service_date) WHEN 0 THEN 'sunday'
                    WHEN 6 THEN 'saturday' ELSE 'weekday' END AS day_type
        FROM final
        ) TO '{runs_path}' (FORMAT parquet)
        """
    )


def natural(col):
    """Sort numerically where the value is a number (route 2 before 10), else as text."""
    return f"TRY_CAST({col} AS INTEGER) NULLS LAST, {col}"


def month_index(month):
    year, mon = month.split("-")
    return int(year) * 12 + int(mon)


def main():
    work = data_dir()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute(f"SET temp_directory = '{work / 'duckdb_tmp'}'")
    con.execute(f"SET memory_limit = '{MEMORY_LIMIT}'")
    con.execute(f"SET threads = {THREADS}")
    con.execute("SET preserve_insertion_order = false")

    tracking = work / "septa_tracking"
    visit_dirs = tracking / "stop_visits"
    visits = f"read_parquet('{visit_dirs}/month=*/*.parquet', hive_partitioning = true)"
    runs_path = tracking / "trip_runs.parquet"
    parts = tracking / "csv_parts"

    # trip_runs.parquet and csv_parts/ let a crashed run resume. Throw both away
    # whenever the inputs or this script change, so stale results are never reused.
    fingerprint = input_fingerprint(work)
    stamp = tracking / "aggregate_inputs.sha256"
    if not stamp.exists() or stamp.read_text() != fingerprint:
        runs_path.unlink(missing_ok=True)
        shutil.rmtree(parts, ignore_errors=True)
        stamp.unlink(missing_ok=True)

    # One row per trip run (about 3M), matched to its schedule.
    if not runs_path.exists():
        tmp = runs_path.with_name(runs_path.name + ".tmp")
        build_runs(con, visits, work, tmp)
        tmp.rename(runs_path)
        stamp.write_text(fingerprint)
    matched, total = con.execute(
        f"SELECT count(route_short_name), count(*) FROM '{runs_path}'"
    ).fetchone()
    print(f"matched {matched:,} of {total:,} trip runs to a schedule ({matched / total:.1%})")

    con.execute(f"CREATE TABLE runs AS SELECT * FROM '{runs_path}' "
                "WHERE route_short_name IS NOT NULL")
    months = [r[0] for r in con.execute("SELECT DISTINCT month FROM runs ORDER BY 1").fetchall()]
    visit_months = sorted(p.name.split("=")[1] for p in visit_dirs.glob("month=*"))

    # Tables with many groups are built a month at a time, so DuckDB never has
    # to hold the whole year's state.
    by_month = {
        "route_month.csv": (f"""
            SELECT mode, route_short_name AS route, month, {VISIT_METRICS}
            FROM vm GROUP BY ALL""", f"mode, {natural('route')}, month"),
        "route_month_hour.csv": (f"""
            SELECT mode, route_short_name AS route, direction_id, month, day_type,
                   start_hour AS scheduled_start_hour, {VISIT_METRICS}
            FROM vm GROUP BY ALL""",
            f"mode, {natural('route')}, direction_id, month, day_type, "
            "CAST(scheduled_start_hour AS INTEGER)"),
        "stop_route_month.csv": (f"""
            SELECT stop_id, mode, route_short_name AS route, direction_id, month,
                   {VISIT_METRICS}
            FROM vm GROUP BY ALL HAVING count(*) >= 20""",
            f"{natural('stop_id')}, mode, {natural('route')}, direction_id, month"),
    }
    whole_year = {
        "route_end_of_trip_month.csv": f"""
            SELECT * FROM (
                SELECT mode, route_short_name AS route, month, count(*) AS trips_observed,
                       {delay_stats('last_delay_min')}
                FROM runs GROUP BY ALL
            ) ORDER BY mode, {natural('route')}, month""",
        "coverage_by_day.csv": """
            SELECT service_date, count(*) AS trips_observed,
                   sum(stop_visits) AS stop_visits, count(DISTINCT route_short_name) AS routes
            FROM runs GROUP BY ALL ORDER BY service_date""",
    }

    parts.mkdir(exist_ok=True)
    for month in months:
        todo = [name for name in by_month if not (parts / f"{name}.{month}").exists()]
        if not todo:
            continue
        # A run's service month can differ from the month it started in (a trip
        # just after midnight on the 1st can belong to the last day of the month
        # before), so read the visit files for this month and its neighbors.
        nearby = [m for m in visit_months if abs(month_index(m) - month_index(month)) <= 1]
        files = ", ".join(f"'{visit_dirs}/month={m}/*.parquet'" for m in nearby)
        con.execute(
            f"""
            CREATE OR REPLACE TEMP TABLE vm AS
            SELECT s.stop_id, s.delay_minutes, s.trip_id || '|' || s.run_start AS run_key,
                   runs.mode, runs.route_short_name, runs.direction_id, runs.month,
                   runs.day_type, runs.start_hour
            FROM read_parquet([{files}]) s
            JOIN runs USING (trip_id, run_start)
            WHERE runs.month = '{month}'
            """
        )
        for name in todo:
            part = parts / f"{name}.{month}"
            tmp = part.with_name(part.name + ".tmp")
            con.execute(f"COPY ({by_month[name][0]}) TO '{tmp}' (HEADER, DELIMITER ',')")
            tmp.rename(part)
        print(f"{month}: done", flush=True)
    con.execute("DROP TABLE IF EXISTS vm")

    for name, (_, order) in by_month.items():
        # Only finished parts (name.YYYY-MM), never a .tmp left by a crash.
        whole_year[name] = (f"SELECT * FROM read_csv('{parts}/{name}.????-??', "
                            f"all_varchar = true) ORDER BY {order}")
    for name, sql in whole_year.items():
        path = OUT_DIR / name
        con.execute(f"COPY ({sql}) TO '{path}' (HEADER, DELIMITER ',')")
        rows = con.execute(
            f"SELECT count(*) FROM read_csv('{path}', all_varchar = true)").fetchone()[0]
        print(f"wrote {name}: {rows:,} rows, {path.stat().st_size / 1e6:.1f} MB", flush=True)


if __name__ == "__main__":
    main()
