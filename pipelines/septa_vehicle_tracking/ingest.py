"""Convert a raw SEPTA vehicle-tracking CSV dump into monthly Parquet files.

Source:   a zip holding one CSV of SEPTA real-time vehicle positions, polled
          roughly every 30 seconds by a TFP volunteer (see README.md).
Produces: $TFP_DATA_DIR/septa_tracking/positions/month=YYYY-MM/*.parquet
Run:      python ingest.py /path/to/septa_tracking_YYYYMMDD.zip

The CSV is streamed straight out of the zip, so it never has to be unpacked.
Rows with no GPS fix (timestamp 0, blank lat/lng) are dropped. Everything else
is kept, including Regional Rail, so later steps can choose what to analyze.
"""

import sys
import zipfile

import duckdb
import pyarrow as pa
import pyarrow.csv as pacsv

from common import MEMORY_LIMIT, THREADS, data_dir

COLUMN_TYPES = {
    "delay_minutes": pa.float64(),
    "next_stop_id": pa.string(),
    "timestamp": pa.int64(),
    "snapshot_timestamp": pa.int64(),
    "lat": pa.float64(),
    "lng": pa.float64(),
    "heading": pa.float64(),
    "seat_availability": pa.string(),
    "vehicle_ids": pa.string(),
    "trip_id": pa.string(),
    "route_id": pa.string(),
}

# Regional Rail trip IDs look like "WAR433_20250902": line code, train number,
# and the date of the schedule the train runs on.
RAIL_TRIP_PATTERN = r"^[A-Z]{3}\d+_\d{8}$"


def main(zip_path):
    out_dir = data_dir() / "septa_tracking" / "positions"
    if out_dir.exists() and any(out_dir.iterdir()):
        sys.exit(f"{out_dir} already has data. Delete it first to re-ingest.")
    out_dir.mkdir(parents=True, exist_ok=True)

    archive = zipfile.ZipFile(zip_path)
    (csv_name,) = archive.namelist()
    reader = pacsv.open_csv(
        archive.open(csv_name),
        read_options=pacsv.ReadOptions(block_size=64 << 20),
        convert_options=pacsv.ConvertOptions(
            column_types=COLUMN_TYPES, strings_can_be_null=True
        ),
    )

    con = duckdb.connect()
    con.execute(f"SET temp_directory = '{data_dir() / 'duckdb_tmp'}'")
    con.execute(f"SET memory_limit = '{MEMORY_LIMIT}'")
    con.execute(f"SET threads = {THREADS}")
    con.register("raw", reader)
    con.execute(
        f"""
        COPY (
            SELECT
                to_timestamp("timestamp") AS observed_at,
                make_timestamp(snapshot_timestamp // 1000) AS polled_at,
                strftime(timezone('America/New_York', to_timestamp("timestamp")),
                         '%Y-%m') AS month,
                CASE WHEN regexp_matches(trip_id, '{RAIL_TRIP_PATTERN}')
                     THEN 'regional_rail' ELSE 'bus_metro' END AS feed,
                route_id AS route_id_raw,
                upper(replace(route_id, ' ', '_')) AS route_id,
                trip_id,
                next_stop_id,
                delay_minutes,
                lat,
                lng,
                heading,
                nullif(seat_availability, '') AS seat_availability,
                vehicle_ids
            FROM raw
            WHERE "timestamp" > 0 AND lat IS NOT NULL AND lng IS NOT NULL
        ) TO '{out_dir}' (FORMAT parquet, PARTITION_BY (month), COMPRESSION zstd)
        """
    )

    summary = con.execute(
        f"""
        SELECT month, feed, count(*) AS rows
        FROM read_parquet('{out_dir}/*/*.parquet', hive_partitioning = true)
        GROUP BY ALL ORDER BY ALL
        """
    ).fetchall()
    for month, feed, rows in summary:
        print(f"{month}  {feed:<14} {rows:>12,}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
