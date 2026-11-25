# SEPTA bus routes

**One-line summary:** Every SEPTA bus and trackless trolley route with how often it runs on a weekday, Saturday and Sunday, whether SEPTA marks it as part of its weekday frequent network, its route line for mapping, and the Pennsylvania House, Senate and Philadelphia Council districts it runs through.

## Source

- **Original source:** SEPTA GTFS release [`v202611010`](https://github.com/septadev/GTFS/releases/tag/v202611010) (schedule starting 2026-11-01), the bus feed `google_bus.zip`: routes, trips, stop times, calendars and shapes.
- **Frequent network:** SEPTA colors its weekday frequent routes red in GTFS (`route_color` EF3340). Its [maps and signs page](https://wwww.septa.org/initiatives/bus/maps-signs/) defines Frequent Red routes as arriving "every 15 minutes or better from 6 am to 9 pm weekdays."
- **Districts:** Census TIGER/Line 2024 Pennsylvania House and Senate districts, and the City of Philadelphia [Council Districts 2024](https://services.arcgis.com/fLeGjb7u4uXqeF9q/arcgis/rest/services/Council_Districts_2024/FeatureServer/0) layer (the ArcGIS layer behind OpenDataPhilly), pulled 2026-11-17.
- **Pulled on:** 2026-11-17 (GTFS); built 2026-11-25
- **Geography:** SEPTA's city and suburban bus and trackless trolley routes. Districts cover Pennsylvania only; Council districts cover Philadelphia only.
- **Time period covered:** The schedule in force from 2026-11-01, measured on Wednesday 2026-11-18, Saturday 2026-11-21 and Sunday 2026-11-22.

## Processing

Script: [`pipelines/septa_bus_routes/build.py`](../../../pipelines/septa_bus_routes/build.py).

- **Routes.** Every GTFS route of type bus (3) or trackless trolley (11; Routes 59, 66 and 75). Trolley (T, D, G) and Metro (L, B, M) routes are left out. Four routes listed in the feed with no trips (FOX Bus, MANN, T Bus, WTR Bus) are kept with blank frequency, districts and map line.
- **Service kind.** `service_kind` labels special services so district counts can leave them out. It comes from the GTFS `route_id`: `no trips` for a route with no trips in this release; `overnight` where the id ends in `_OWL` (L1 OWL, B1 OWL); `rail replacement` where it ends in `_BUS` (M1 Bus, D1 Bus, D2 Bus, NOR Bus); `school` for numbers 400 to 499, SEPTA's school trippers; `regular` for everything else. That gives 119 regular, 26 school, 4 rail replacement, 2 overnight and 4 no trips.
- **Frequency.** For each route and direction, the trips that start between 7:00 and 19:00 on each of the three days. The average headway is 720 minutes divided by the number of those trips, and the maximum gap is the longest wait in the window, counting from 7:00 to the first trip and from the last trip to 19:00. Each value is for the less frequent direction. Only directions with at least two trips in the window count, so loops that run one way only (310, LUCYGO, LUCYGR) are measured on that direction. A value is blank when no direction has two trips.
- **Blank headways.** 27 rows have no Wednesday headway: 18 school trippers, 4 routes with no trips in this release, 3 rail-replacement shuttles with no trips that day (D1 Bus, D2 Bus, NOR Bus) and the 2 overnight OWL routes, which run outside 7:00 to 19:00.
- **Frequent network.** `septa_frequent_weekday` is `true` where the route's GTFS color is SEPTA's Frequent Red. This column is SEPTA's own marking. The headway columns are measured from the schedule. All 25 red routes measure an average headway of 15 minutes or better on the Wednesday. Only 3 routes (33, 52 and Boulevard Direct) average 15 minutes or better on all three days measured.
- **Districts.** Each route's GTFS shapes are joined to the district polygons; a route counts in every district any of its shapes touches. The joins reuse the district helpers in [`pipelines/septa_accelerate_stations/build.py`](../../../pipelines/septa_accelerate_stations/build.py).
- **Map lines.** For the GeoJSON, each route's shapes are dissolved so each street segment appears once, simplified to about 1 m and rounded to 5 decimal places. Districts are computed from the full shapes before this step.

## Files

| File | Format | Description |
| --- | --- | --- |
| `septa-bus-routes.csv` | CSV | One row per route, 155 rows (152 bus, 3 trackless trolley) |
| `septa-bus-routes.geojson` | GeoJSON | One feature per route, a MultiLineString in WGS 84, with `route`, `name` and `septa_frequent_weekday` (true/false). The four shuttle routes have no geometry. About 1.1 MB |

## Columns

`septa-bus-routes.csv`

| Column | Type | Units | Description |
| --- | --- | --- | --- |
| `route` | text | | Route number or name as riders see it (GTFS `route_short_name`, or `route_id` where that is blank) |
| `name` | text | | GTFS `route_long_name` |
| `route_type` | text | | `bus` or `trackless trolley` |
| `service_kind` | text | | `regular`, `school`, `overnight`, `rail replacement` or `no trips`. See Processing |
| `wed_avg_headway_min`, `sat_avg_headway_min`, `sun_avg_headway_min` | number | minutes | Average time between trips from 7:00 to 19:00, in the less frequent direction. Blank where no direction has at least two trips in that window that day |
| `wed_max_gap_min`, `sat_max_gap_min`, `sun_max_gap_min` | number | minutes | Longest wait from 7:00 to 19:00, in the less frequent direction. Blank as above |
| `septa_frequent_weekday` | true/false | | On SEPTA's weekday Frequent Red network |
| `house_districts`, `senate_districts`, `council_districts` | text | | Districts the route's shapes touch, separated by `;`. Council is blank for the 36 routes with a map line that run entirely outside Philadelphia (32 regular, 4 rail replacement), and for the 4 routes with no trips |
| `route_url` | text | | SEPTA's schedule page for the route (GTFS `route_url`) |

## Known gaps and caveats

- **The Accelerate plan's 29 frequent routes are not listed route by route.** SEPTA has not published which routes make up the 29 that will run "every 15 minutes or better, 7 days a week" once the New Bus Network is complete in 2027, so `septa_frequent_weekday` shows the 25-route weekday network running now. The closest public list, SEPTA's [April 2024 Recommended Route Change Sheets](https://web.archive.org/web/2024/https://septabusrevolution.com/wp-content/uploads/2024/05/SEPTA-CHANGE-SHEET-TEM-2024-0503.pdf), marks about 40 routes "15 MAX" and predates later changes.
- **Districts are generous.** A route counts in every district it touches, including districts it only runs along the edge of or crosses briefly. Do not read a district's route count as service to the people living there.
- **This is the schedule.** Headways are what SEPTA scheduled. For how late buses actually ran, see [SEPTA bus delay](../septa-bus-delay/).
- **The measured window is narrower than SEPTA's definition.** SEPTA defines Frequent Red as 6 am to 9 pm; the measurement here covers 7:00 to 19:00. An average headway can also hide uneven spacing, so check the maximum gap.
- **One schedule version.** SEPTA reissues GTFS every week or two. These numbers are for `v202611010`.
- **Map lines are simplified.** The GeoJSON is for maps. Use the district columns, which come from the full shapes, rather than re-joining the simplified lines.

## License

CC BY 4.0. Please credit Transit Forward Philly, SEPTA, the City of Philadelphia and the US Census Bureau.
