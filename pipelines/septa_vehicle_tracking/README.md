# SEPTA vehicle tracking → bus delay by route

Turns a raw dump of SEPTA's real-time vehicle positions into delay tables by
route, stop, month and scheduled start hour. Output: [`datasets/septa_bus_delay/`](../../datasets/septa_bus_delay/).

## Source

A TFP volunteer polled SEPTA's real-time vehicle feed (the data behind
TransitView) about every 30 seconds from November 2025 to October 2026. The dump is a single
CSV (13.6 GB, ~133M rows) with one row per vehicle per poll:

| Column | Example | Meaning |
|---|---|---|
| `delay_minutes` | `5.5` | Minutes behind schedule as SEPTA reports it; negative = early |
| `next_stop_id` | `38` | GTFS `stop_id` the vehicle is heading toward |
| `timestamp` | `1762880329` | Time of the vehicle's GPS report (Unix seconds) |
| `snapshot_timestamp` | `1762880350530363562` | Time of the poll (Unix nanoseconds) |
| `lat`, `lng`, `heading` | `39.916`, `-75.180`, `160.7` | Position and direction of travel |
| `seat_availability` | `MANY_SEATS_AVAILABLE` | GTFS-realtime crowding level; blank on ~38% of rows |
| `vehicle_ids` | `{3086}` | Vehicle number(s); Regional Rail lists every car in the train |
| `trip_id`, `route_id` | `434475`, `2` | GTFS trip and route |

The raw file is too large for GitHub. To get a copy, open an issue or ask in
the TFP data committee.

## How to run

Needs Python 3.11+ and about 20 GB of free disk for working files (an external
drive is fine). On a laptop writing to a USB drive the steps took about 20,
10, 25 and 20 minutes.

```bash
pip install -r requirements.txt
export TFP_DATA_DIR=/path/to/working/folder

python ingest.py /path/to/septa_tracking_20261014.zip           # zip → monthly Parquet
python ../septa_gtfs_archive/fetch.py 2025-11-01 2026-10-31      # past schedules
python stop_visits.py                                            # one row per trip per stop
python aggregate.py                                              # writes the CSVs
```

Each step skips work that is already done, except `ingest.py`, which refuses
to overwrite existing output, so a crashed run can be restarted. On a machine
with little memory, lower `TFP_MEMORY_LIMIT` (default `3GB`) and `TFP_THREADS`
(default `2`); 8 GB laptops did fine at `1500MB` and 2 threads.

## Method

1. **Ingest.** The CSV is read straight from the zip. Rows with no GPS fix
   (timestamp 0, blank position; mostly Regional Rail) are dropped.
2. **Stop visits.** The feed records each vehicle on every poll, so a bus stuck
   in traffic shows up many more times than one running on time. Averaging raw
   rows would overweight slow trips. Instead, each trip is cut into stop
   visits: an unbroken stretch of polls with the same `next_stop_id`. The
   delay at the last poll of that stretch is the delay as the vehicle reaches
   the stop. SEPTA reuses a `trip_id` every day a trip runs, so a gap of more
   than 90 minutes starts a new run. Runs are assembled with a day of data on
   either side of each month, so trips crossing midnight at a month's end stay
   whole.
3. **Match to the schedule.** Each run is matched to the GTFS version in force
   on its service day (the latest release that took effect on or before that
   day). A `trip_id` missing from that version is left unmatched rather than
   looked up in an older one, since SEPTA occasionally reuses IDs for other
   routes. The match supplies the published route name, direction and
   scheduled start time. Route names are upper-cased because SEPTA spells some
   inconsistently between versions (`T5 Bus` / `T5 BUS`). The service day comes
   from the scheduled start: GTFS writes an owl trip leaving at 2:50 a.m. as
   `26:50` on the previous day, and the trip is counted on that day.
4. **Summarize.** Counts and delay percentiles by route, direction, month,
   day type and scheduled start hour. No on-time cutoff or peak windows are
   applied. See the dataset README for column definitions.

## Known limits

- `delay_minutes` is SEPTA's own figure, not an independent measurement.
- Bus, trolley and Metro only. Regional Rail appears in the dump for
  November 2025 only (375k rows); it is kept in the Parquet but not
  summarized. Its delay is in whole minutes and its next-stop field is mostly
  a placeholder.
- Holidays are counted as the weekday they fall on.
