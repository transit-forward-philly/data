"""Sanity-check the published CSVs in datasets/septa_bus_delay/.

Run:      python validate.py
Needs:    duckdb (no working data; it reads only the committed CSVs)

Checks that every table has one row per key, that counts and delay columns are
plausible, and that the tables agree with each other. Run it after
aggregate.py, before committing new data. It exits with an error listing every
failed check.
"""

import sys
from pathlib import Path

import duckdb

DATASET = Path(__file__).resolve().parents[2] / "datasets" / "septa_bus_delay"

KEYS = {
    "route_month.csv": "mode, route, month",
    "route_month_hour.csv": "mode, route, direction_id, month, day_type, scheduled_start_hour",
    "stop_route_month.csv": "stop_id, mode, route, direction_id, month",
    "route_end_of_trip_month.csv": "mode, route, month",
    "coverage_by_day.csv": "service_date",
}
MODES = {"bus", "trolley", "trackless_trolley", "metro"}
MIN_VISITS = 20


def main():
    con = duckdb.connect()
    failures = []

    def check(ok, message):
        print(("ok    " if ok else "FAIL  ") + message)
        if not ok:
            failures.append(message)

    for name, key in KEYS.items():
        con.execute(f"CREATE TABLE \"{name}\" AS SELECT * FROM read_csv('{DATASET / name}', sample_size = -1)")
        rows, unique = con.execute(
            f"SELECT count(*), count(DISTINCT ({key})) FROM \"{name}\"").fetchone()
        check(rows > 0, f"{name}: has rows ({rows:,})")
        check(rows == unique, f"{name}: one row per ({key})")
        if name != "coverage_by_day.csv":
            bad = con.execute(f"""
                SELECT count(*) FROM "{name}"
                WHERE mode NOT IN ({', '.join(f"'{m}'" for m in sorted(MODES))})
                   OR trips_observed < 1
                   OR NOT (p10_delay_min <= median_delay_min AND median_delay_min <= p90_delay_min)
                   OR abs(mean_delay_min) > 120""").fetchone()[0]
            check(bad == 0, f"{name}: modes known, counts positive, p10 <= median <= p90")

    for name in ("route_month_hour.csv", "stop_route_month.csv"):
        small = con.execute(f'SELECT count(*) FROM "{name}" WHERE stop_visits < {MIN_VISITS}').fetchone()[0]
        check(small == 0, f"{name}: every group has at least {MIN_VISITS} stop visits")

    hours = con.execute('SELECT min(scheduled_start_hour), max(scheduled_start_hour) '
                        'FROM "route_month_hour.csv"').fetchone()
    check(0 <= hours[0] and hours[1] <= 30, f"route_month_hour.csv: start hours in 0-30 ({hours})")

    # The route x month tables and the daily coverage table describe the same trips.
    mismatched = con.execute("""
        SELECT count(*) FROM "route_month.csv" a
        FULL JOIN "route_end_of_trip_month.csv" b USING (mode, route, month)
        WHERE a.trips_observed IS DISTINCT FROM b.trips_observed""").fetchone()[0]
    check(mismatched == 0, "route_month and route_end_of_trip_month agree on trips per route-month")
    by_route, by_day = con.execute("""
        SELECT (SELECT sum(trips_observed) FROM "route_month.csv"),
               (SELECT sum(trips_observed) FROM "coverage_by_day.csv")""").fetchone()
    check(by_route == by_day, f"total trips match across tables ({by_route:,} vs {by_day:,})")

    if failures:
        sys.exit(f"\n{len(failures)} check(s) failed")
    print("\nall checks passed")


if __name__ == "__main__":
    main()
