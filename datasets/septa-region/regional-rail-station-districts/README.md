# Regional Rail stations by legislative district

**One-line summary:** Each of the 155 Regional Rail station rows placed in its Pennsylvania House and Senate district, county and municipality, with the 2025–26 member and the unofficial 2026 election status of that seat.

## Source

- **Derived from:** [SEPTA Regional Rail stations](../septa-regional-rail-stations/) (coordinates), US Census Bureau TIGER/Line 2024 state legislative districts, counties and county subdivisions, [PA legislators 2025–26](../../pennsylvania/legislators-2025-2026/) and [2026 election flips](../../pennsylvania/election-2026-flips/)
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
| `septa_house_district`, `septa_senate_district` | SEPTA's district assignment |
| `house_district`, `senate_district` | Computed from Census boundaries; blank outside Pennsylvania |
| `house_matches_septa`, `senate_matches_septa` | `true` or `false` |
| `house_near_boundary`, `senate_near_boundary` | `true` if the station is within 100 m of a district edge |
| `house_member_2025_26`, `house_party_2025_26` (and Senate) | Member for the computed district |
| `house_seat_2026_status`, `senate_seat_2026_status` | `flip_r_to_d`, `flip_d_to_r`, `uncalled`, or `no_change_listed`. Unofficial, as of 2026-11-04. |

## Key findings

- **SEPTA's district fields are mostly out of date.** They disagree with the current maps for 51 of 149 Pennsylvania station rows in the House and 26 of 149 in the Senate. Use the computed columns.
- **6 stations are in House seats that flipped R to D** (Cornwells Heights, Eddington, Langhorne, Neshaminy Falls, Trevose, Woodbourne) and **8 are in Senate seats that flipped R to D**. No station sits in an uncalled seat.
- **SEPTA's county is wrong for 7 station rows:** Bala, Cynwyd and Rosemont (Montgomery, not Philadelphia), Hatboro (Montgomery, not Bucks), Highland and Angora (Philadelphia, not Delaware), and Lawndale (computed as Montgomery's Cheltenham Township; it sits on the city line, so check it). Use `county` and `municipality`.
- Six rows (Delaware and New Jersey stations) are outside Pennsylvania and have no district.

## Known gaps and caveats

- **"No change listed" is not "confirmed."** The election file lists only flipped and uncalled seats, so `no_change_listed` means the seat was not flagged, not that it was certified as held.
- **Member names are for 2025–26.** They will change in January 2027 where seats flipped or incumbents left.
- **Edge cases.** Rows flagged `near_boundary` could land in a neighboring district with small coordinate differences. Fernwood-Yeadon differs depending on boundary precision.
- **Station coordinates are SEPTA's** and were not checked.

## License

CC BY 4.0. Please credit Transit Forward Philly, SEPTA and the US Census Bureau.
