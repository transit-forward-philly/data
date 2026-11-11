# Regional Rail stations by legislative district

**One-line summary:** Each of the 155 Regional Rail station rows placed in its Pennsylvania House and Senate district, county and municipality, with the 2025–26 member and the unofficial 2026 election result for that seat.

## Source

- **Derived from:** [SEPTA Regional Rail stations](../septa-regional-rail-stations/) (coordinates), US Census Bureau TIGER/Line 2024 state legislative districts, counties and county subdivisions, [PA legislators 2025–26](../../pennsylvania/legislators-2025-2026/) and [2026 election results](../../pennsylvania/election-2026-results/)
- **Built on:** 2026-11-10
- **Geography:** SEPTA Regional Rail network; stations outside Pennsylvania have no district

## Processing

Station coordinates were placed in district polygons by point-in-polygon. Script: [`pipelines/regional_rail_station_districts/build.py`](../../../pipelines/regional_rail_station_districts/build.py). SEPTA's own district fields are kept beside the computed ones so disagreements are visible.

## Files

| File | Format | Description |
|---|---|---|
| `regional-rail-station-districts.csv` | CSV | One row per station per line, 155 rows |

## Columns

| Column | Description |
|---|---|
| `line`, `station`, `stop_id`, `latitude`, `longitude` | From the SEPTA layer |
| `septa_county`, `septa_municipality` | SEPTA's values, unchanged |
| `county`, `municipality` | Computed from Census boundaries; blank outside Pennsylvania |
| `county_matches_septa` | `true` or `false` |
| `location_basis` | `coordinates`, or `septa_address_near_line` for stations whose point sits within about 100 m of a municipal line (see caveats) |
| `septa_house_district`, `septa_senate_district` | SEPTA's district assignment |
| `house_district`, `senate_district` | Computed from Census boundaries; blank outside Pennsylvania |
| `house_matches_septa`, `senate_matches_septa` | `true` or `false` |
| `house_near_boundary`, `senate_near_boundary` | `true` if the station is within 100 m of a district edge |
| `house_member_2025_26`, `house_party_2025_26` (and Senate) | Member for the computed district |
| `house_seat_2026_status`, `senate_seat_2026_status` | `hold`, `flip_r_to_d`, `flip_d_to_r`, `uncounted`, or `not_up` (Senate seats not on the 2026 ballot). Unofficial, as of 2026-11-10. |
| `*_winner_2026`, `*_winner_party_2026` | Unofficial winner of that seat; blank where the count is unfinished or the seat was not up |

## Key findings

- **SEPTA's district fields are mostly out of date.** They disagree with the current maps for 51 of 149 Pennsylvania station rows in the House and 26 of 149 in the Senate. Use the computed columns.
- **6 stations are in House seats that flipped R to D:** Cornwells Heights, Eddington, Neshaminy Falls and Trevose (HD-18, Bryan F. Allen Jr. replacing K.C. Tomlinson) and Langhorne and Woodbourne (HD-142, Kristin Egan replacing Joe Hogan). **8 are in Senate seats that flipped R to D:** SD-6 (Eileen Hartnett Albillar replacing Frank Farry) and SD-24 (Christopher Thomas replacing Tracy Pennycuick). No station sits in a seat still being counted.
- **SEPTA's county is wrong for 6 station rows:** Bala, Cynwyd and Rosemont (Montgomery, not Philadelphia), Hatboro (Montgomery, not Bucks), and Highland and Angora (Philadelphia, not Delaware). Use `county` and `municipality`.
- Six rows (Delaware and New Jersey stations) are outside Pennsylvania and have no district.

## Known gaps and caveats

- **Results are unofficial.** They come from MultiState's election page, not certified returns.
- **Member names are for 2025–26.** They will change in January 2027 where seats flipped or incumbents left.
- **Stations on a municipal line.** Two stations, Lawndale and Primos, have coordinates within about 100 m of a municipal line, on the other side from the municipality SEPTA's street address names. For those rows (`location_basis = septa_address_near_line`) we trust SEPTA's municipality and take the districts from just inside it. Lawndale's coordinates fall 1 m inside Cheltenham Township, but its address is 105 Devereaux Ave, Philadelphia 19111, so it is treated as Philadelphia.
- **Edge cases.** Rows flagged `near_boundary` could land in a neighboring district with small coordinate differences. Fernwood-Yeadon differs depending on boundary precision.
- **Station coordinates are SEPTA's** and were not checked.

## License

CC BY 4.0. Please credit Transit Forward Philly, SEPTA and the US Census Bureau.
