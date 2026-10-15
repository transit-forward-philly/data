"""Turn raw vehicle positions into one row per trip per stop.

Source:   $TFP_DATA_DIR/septa_tracking/positions/  (from ingest.py)
Produces: $TFP_DATA_DIR/septa_tracking/stop_visits/month=YYYY-MM/*.parquet
Run:      python stop_visits.py

Why: the raw feed records every vehicle on every poll, so a bus stuck in
traffic for 20 minutes appears far more often than one running on time.
Averaging raw rows overweights slow trips. Instead we keep one reading per
stop: the last poll before the vehicle's "next stop" changes, which is the
delay as it reaches that stop.

Steps, for bus, trolley and Metro (Regional Rail is left for later):
  1. Drop repeated polls of the same GPS report.
  2. Split each trip_id into runs. SEPTA reuses a trip_id every day it
     operates, so a gap of more than 90 minutes starts a new run.
  3. Within a run, each unbroken stretch of the same next_stop_id is one stop
     visit. Its delay is the delay at the last poll of that stretch.
"""

import duckdb

from common import MEMORY_LIMIT, THREADS, data_dir

RUN_GAP_MINUTES = 90


def main():
    root = data_dir() / "septa_tracking"
    positions = root / "positions"
    out_dir = root / "stop_visits"
    out_dir.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect()
    con.execute(f"SET temp_directory = '{data_dir() / 'duckdb_tmp'}'")
    con.execute(f"SET memory_limit = '{MEMORY_LIMIT}'")
    con.execute(f"SET threads = {THREADS}")
    con.execute("SET preserve_insertion_order = false")
    months = sorted(p.name.split("=")[1] for p in positions.glob("month=*"))

    for month in months:
        target = out_dir / f"month={month}"
        if target.exists():
            print(f"{month}: already built, skipping")
            continue
        target.mkdir()
        con.execute(
            f"""
            COPY (
            WITH obs AS (
                SELECT DISTINCT ON (trip_id, observed_at)
                       trip_id, route_id, next_stop_id, observed_at, delay_minutes,
                       seat_availability
                FROM read_parquet('{positions}/month={month}/*.parquet')
                WHERE feed = 'bus_metro' AND trip_id IS NOT NULL
                  AND next_stop_id IS NOT NULL AND delay_minutes IS NOT NULL
                ORDER BY trip_id, observed_at, polled_at DESC
            ),
            gaps AS (
                SELECT *,
                       CASE WHEN observed_at - lag(observed_at) OVER w
                                 <= INTERVAL {RUN_GAP_MINUTES} MINUTE
                            THEN 0 ELSE 1 END AS new_run,
                       CASE WHEN next_stop_id = lag(next_stop_id) OVER w
                                 AND observed_at - lag(observed_at) OVER w
                                     <= INTERVAL {RUN_GAP_MINUTES} MINUTE
                            THEN 0 ELSE 1 END AS new_stop
                FROM obs
                WINDOW w AS (PARTITION BY trip_id ORDER BY observed_at)
            ),
            numbered AS (
                SELECT *,
                       sum(new_run) OVER (PARTITION BY trip_id ORDER BY observed_at) AS run_no,
                       sum(new_stop) OVER (PARTITION BY trip_id ORDER BY observed_at) AS visit_no
                FROM gaps
            ),
            runs AS (
                SELECT *,
                       min(observed_at) OVER (PARTITION BY trip_id, run_no) AS run_start
                FROM numbered
            )
            SELECT
                trip_id,
                -- Service day: trips that start before 3 a.m. belong to the day before.
                CAST(timezone('America/New_York', run_start) - INTERVAL 3 HOUR AS DATE)
                    AS service_date,
                run_start,
                arg_max(route_id, observed_at) AS route_id_rt,
                next_stop_id AS stop_id,
                visit_no,
                max(observed_at) AS reached_at,
                arg_max(delay_minutes, observed_at) AS delay_minutes,
                arg_max(seat_availability, observed_at) AS seat_availability,
                count(*) AS polls
            FROM runs
            GROUP BY trip_id, run_no, run_start, visit_no, next_stop_id
            ) TO '{target}' (FORMAT parquet, COMPRESSION zstd, PER_THREAD_OUTPUT true)
            """
        )
        visits, runs = con.execute(
            f"""SELECT count(*), count(DISTINCT (trip_id, run_start))
                FROM read_parquet('{target}/*.parquet')"""
        ).fetchone()
        print(f"{month}: {runs:,} trip runs, {visits:,} stop visits")


if __name__ == "__main__":
    main()
