# SEPTA GTFS archive

Downloads past versions of SEPTA's published schedule (GTFS) so analyses can use
the schedule that was actually in force on a given day, not today's.

- **Source:** [septadev/GTFS releases](https://github.com/septadev/GTFS/releases).
  Each release is one schedule version. The tag gives the date it took effect
  (`v202608233` started 2026-08-23, the bus network redesign). Releases go back
  to July 2015.
- **Produces:** `$TFP_DATA_DIR/septa_gtfs/<tag>/{bus,rail}/*.txt` (unpacked
  feeds, about 140 MB per version) and `trips_index.parquet` (one row per trip
  per version with route, direction, headsign and first departure time).
- **Run:** `python fetch.py START END` with ISO dates, e.g.
  `python fetch.py 2025-11-01 2026-10-31`. It fetches every version that took
  effect in that window plus the one already in force at the start. Versions
  already on disk are skipped. Needs `duckdb`.

**Trap:** SEPTA reissues the feed every week or two, and most `trip_id`s carry
over between versions, but not all of them mean the same trip. Across the 28
versions from Oct 2025 to Oct 2026, 714 of 162,690 bus `trip_id`s point to a
different route in different versions. Always match on version and `trip_id`
together.
