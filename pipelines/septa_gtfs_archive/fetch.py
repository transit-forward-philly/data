"""Download past SEPTA GTFS schedule versions and index their trips.

Source:   https://github.com/septadev/GTFS/releases (one release per schedule
          version; the tag gives the date it took effect, e.g. v202608233 is
          the feed that started 2026-08-23).
Produces: $TFP_DATA_DIR/septa_gtfs/<tag>/{bus,rail}/*.txt  (unpacked feeds)
          $TFP_DATA_DIR/septa_gtfs/trips_index.parquet      (one row per trip
          per version: route, direction, headsign, first departure time)
Run:      python fetch.py 2025-11-01 2026-10-31
          (start and end dates of the period you need schedules for)

Already-downloaded versions are skipped, so rerunning only fetches new ones.
"""

import io
import json
import os
import sys
import urllib.request
import zipfile
from datetime import date
from pathlib import Path

import duckdb

RELEASES_URL = "https://api.github.com/repos/septadev/GTFS/releases?per_page=100&page={page}"


def data_dir():
    path = os.environ.get("TFP_DATA_DIR")
    if not path:
        raise SystemExit("Set TFP_DATA_DIR to a folder for working data.")
    return Path(path) / "septa_gtfs"


def effective_date(tag):
    return date(int(tag[1:5]), int(tag[5:7]), int(tag[7:9]))


def list_releases():
    releases, page = [], 1
    while True:
        with urllib.request.urlopen(RELEASES_URL.format(page=page)) as resp:
            batch = json.load(resp)
        if not batch:
            return releases
        for rel in batch:
            asset = next((a for a in rel["assets"] if a["name"] == "gtfs_public.zip"), None)
            if asset and rel["tag_name"][1:9].isdigit():
                releases.append((rel["tag_name"], asset["browser_download_url"]))
        page += 1


def pick_versions(releases, start, end):
    """Every version that took effect in the window, plus the one in force at its start."""
    ordered = sorted(releases, key=lambda r: r[0])
    before = [r for r in ordered if effective_date(r[0]) <= start]
    inside = [r for r in ordered if start < effective_date(r[0]) <= end]
    return before[-1:] + inside


def download(tag, url, root):
    target = root / tag
    if (target / "bus" / "trips.txt").exists():
        return
    print(f"downloading {tag}")
    with urllib.request.urlopen(url) as resp:
        outer = zipfile.ZipFile(io.BytesIO(resp.read()))
    # SEPTA ships two feeds inside one zip: google_bus.zip and google_rail.zip.
    for inner_name, mode in (("google_bus.zip", "bus"), ("google_rail.zip", "rail")):
        inner = zipfile.ZipFile(io.BytesIO(outer.read(inner_name)))
        dest = target / mode
        dest.mkdir(parents=True, exist_ok=True)
        for name in inner.namelist():
            if name.endswith(".txt") and "/" not in name:
                (dest / name).write_bytes(inner.read(name))


def build_index(root, tags):
    con = duckdb.connect()
    parts = []
    for tag in tags:
        for mode in ("bus", "rail"):
            feed = root / tag / mode
            parts.append(
                f"""
                SELECT '{tag}' AS feed_version,
                       DATE '{effective_date(tag)}' AS feed_effective,
                       '{mode}' AS feed,
                       t.trip_id, t.route_id, r.route_short_name, r.route_type,
                       t.direction_id, t.trip_headsign, t.service_id,
                       s.first_departure, s.stop_count
                FROM read_csv('{feed}/trips.txt', all_varchar = true) t
                JOIN read_csv('{feed}/routes.txt', all_varchar = true) r USING (route_id)
                LEFT JOIN (
                    SELECT trip_id,
                           min(departure_time) FILTER (WHERE departure_time <> '') AS first_departure,
                           count(*) AS stop_count
                    FROM read_csv('{feed}/stop_times.txt', all_varchar = true)
                    GROUP BY trip_id
                ) s USING (trip_id)
                """
            )
    out = root / "trips_index.parquet"
    con.execute(f"COPY ({' UNION ALL '.join(parts)}) TO '{out}' (FORMAT parquet)")
    rows = con.execute(f"SELECT count(*), count(DISTINCT feed_version) FROM '{out}'").fetchone()
    print(f"wrote {out}: {rows[0]:,} trips across {rows[1]} versions")


def main(start, end):
    root = data_dir()
    root.mkdir(parents=True, exist_ok=True)
    versions = pick_versions(list_releases(), start, end)
    for tag, url in versions:
        download(tag, url, root)
    build_index(root, [tag for tag, _ in versions])


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(date.fromisoformat(sys.argv[1]), date.fromisoformat(sys.argv[2]))
