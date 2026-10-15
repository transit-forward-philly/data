# SEPTA bus, trolley and Metro delay

**One-line summary:** How far behind (or ahead of) schedule SEPTA vehicles ran,
by route, stop, month and scheduled start hour, from SEPTA's own real-time feed.

## Source

- **Original source:** SEPTA real-time vehicle positions (the feed behind
  TransitView), polled by a TFP volunteer; schedules from
  [septadev/GTFS](https://github.com/septadev/GTFS/releases)
- **Pulled on:** raw dump received 2026-10-15; last observation 2026-10-14
- **Geography:** SEPTA bus, trolley and Metro (city and suburban)
- **Time period covered:** 2025-11-09 to 2026-10-14, 281 service days with data (see below)

## Processing

Built by [`pipelines/septa_vehicle_tracking/`](../../pipelines/septa_vehicle_tracking/),
which describes the method in full. In short:

1. The feed records each vehicle on every poll. Each trip is cut into **stop
   visits**: the delay at the last poll before the vehicle's next stop changes.
   This avoids overweighting slow trips, which show up in more polls.
2. Each trip is matched to the GTFS schedule version in force that day, for
   route, direction and scheduled start time. 95.6% of 3.13M trip runs matched;
   unmatched trips are left out of these tables.
3. The tables give counts and delay percentiles only. **No on-time cutoff or
   peak-period definition is applied**; use the hourly table to group hours
   however you need. Medians and percentiles are approximate (DuckDB's
   t-digest `approx_quantile`); means are exact. Checked against exact values
   for `route_month.csv`: medians within 0.1 minute everywhere; p90 within
   0.2 minute in 99% of rows. Small groups can be off by more.

## Files

| File | Rows | Description |
|---|---|---|
| `route_month.csv` | 1,939 | Route × month |
| `route_month_hour.csv` | 167,563 | Route × direction × month × day type × scheduled start hour |
| `route_end_of_trip_month.csv` | 1,939 | Route × month, delay at the last stop observed on each trip |
| `stop_route_month.csv` | 222,986 | Stop × route × direction × month (groups with 20+ stop visits) |
| `coverage_by_day.csv` | 281 | Trips and stop visits observed each service day |

## Columns

| Column | Type | Units | Description |
|---|---|---|---|
| `mode` | text | | `bus`, `trolley`, `trackless_trolley` (routes 59, 66, 75) or `metro`, from GTFS `route_type` |
| `route` | text | | Route as published in GTFS (`route_short_name`), upper-cased so variant spellings combine, e.g. `47`, `T1`, `T5 BUS` |
| `direction_id` | text | | GTFS direction, `0` or `1`; see `trip_headsign` in GTFS for names |
| `stop_id` | text | | GTFS `stop_id` |
| `month` | text | YYYY-MM | Month of the service day |
| `day_type` | text | | `weekday`, `saturday` or `sunday`; holidays count as their weekday |
| `scheduled_start_hour` | integer | hour, 0–27 | Hour of the trip's first scheduled departure; GTFS writes after-midnight trips as 24–27 |
| `service_date` | date | | Service day from the schedule; after-midnight trips scheduled as 24:00+ count toward the day before |
| `trips_observed` | integer | trips | Distinct trip runs in the group |
| `stop_visits` | integer | visits | Stop visits in the group (see caveat on poll rate) |
| `median_delay_min` | number | minutes | Median delay; positive = late, negative = early |
| `mean_delay_min` | number | minutes | Mean delay |
| `p10_delay_min` | number | minutes | 10th percentile delay (the early end) |
| `p90_delay_min` | number | minutes | 90th percentile delay (the late end) |
| `routes` | integer | | Routes with at least one trip that day (`coverage_by_day.csv`) |

In `route_end_of_trip_month.csv` the delay columns describe one value per trip:
the delay at the last stop observed.

## Known gaps and caveats

- **Delay is SEPTA's own figure**, as reported in its real-time feed. It is not
  an independent measurement.
- **Collection gaps.** Some days are missing or thin. **March 2026 has data only
  for Mar 6–13.** Check `coverage_by_day.csv` before comparing periods. A
  typical full day has about 12,800 trips observed. Days with data by month
  (days with at least 3,000 trips in parentheses):

  | 2025-11 | 2025-12 | 2026-01 | 2026-02 | 2026-03 | 2026-04 | 2026-05 | 2026-06 | 2026-07 | 2026-08 | 2026-09 | 2026-10 |
  |---|---|---|---|---|---|---|---|---|---|---|---|
  | 18 (17) | 26 (26) | 24 (21) | 25 (24) | 8 (7) | 23 (22) | 31 (31) | 30 (30) | 24 (23) | 29 (25) | 29 (28) | 14 (14) |

- **Poll rate varied.** The feed was polled about every 30 seconds most of the
  time but about every 10 seconds during Mar 6–13. Faster polling catches more
  of the stops a vehicle passes, so `stop_visits` counts are not comparable
  across periods. Delay values per visit are.
- **The bus network redesign took effect 2026-08-23.** Some routes were renamed,
  merged, retired or added (e.g. 106 merged into 105; 72 and 76 are new).
  Route-level comparisons across that date need care.
- **Metro is almost absent.** The only Metro line in the feed is the M1 (Norristown
  High Speed Line); the B and L lines do not appear.
- **Regional Rail is not included.** It appears in the raw dump only for
  November 2025.
- 400-series routes (409–495) are school trips that run a few times a week.

## License

CC BY 4.0. Please credit Transit Forward Philly and SEPTA as the original source.
