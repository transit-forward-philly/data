# SEPTA bus network redesign: what changed, and who can still get where

Analysis of SEPTA's redesigned Philadelphia bus network, which took effect **August 23, 2026**. Compares it to the network it replaced, using only public data.

## The question

Did the redesign cut service, and did it make it easier or harder for people to reach jobs and the subway?

## Short answer

- **The redesign is close to service-neutral.** Weekday bus trips changed −0.1% and departures −0.7% against Fall 2025. It is a restructuring, not a cut and not an expansion.
- **The bigger story is the decline since 2019.** Bus service is down about 18% from the fall of 2019, mostly in the weekday morning peak (−26% for 7–9 a.m. departures).
- **Service moved from radial to crosstown routes.** Crosstown trips rose 2.1% and trips on routes through Center City fell 5.3%.
- **Jobs reachable by transit fell.** Median jobs within 45 minutes dropped 1.77% across Philadelphia block groups. The loss is largest at 30 minutes (−3.10%) and nearly gone at 60 (−0.60%). Trips got longer more than they disappeared.
- **Time to reach a Metro station did not improve.** The median block group needs 18.0 minutes before and after.
- **Stops were not consolidated.** Median stop spacing went from 250 m to 248 m. Only 134 stops were truly removed, carrying about 0.05% of boardings.
- **Neighborhoods split nearly evenly.** 64 neighborhoods gained service and 60 lost it.

Details and tables are below.

## Data used

| Data | Source | Used for |
|---|---|---|
| SEPTA GTFS releases `v201910301`, `v202509141`, `v202608233` (plus `v202602220` as a cross-check) | [septadev/GTFS releases](https://github.com/septadev/GTFS/releases) | Schedules before and after |
| Philadelphia neighborhoods | [OpenDataPhilly](https://opendataphilly.org/) | Neighborhood summaries |
| 2023 TIGER block groups, Pennsylvania | [Census](https://www2.census.gov/geo/tiger/TIGER2023/BG/tl_2023_42_bg.zip) | Access scoring geography |
| LEHD LODES 2020 workplace area characteristics | [Census LEHD](https://lehd.ces.census.gov/data/) | Jobs per block group |
| Pennsylvania OpenStreetMap extract | [Geofabrik](https://download.geofabrik.de/north-america/us/pennsylvania.html) | Walking network |
| SEPTA APC ridership (bus stop summary, route monthly) | [OpenDataPhilly](https://opendataphilly.org/datasets/septa-ridership-statistics/) | Rider weighting |

GTFS zips are not stored here (see [CONTRIBUTING](../../CONTRIBUTING.md)). `gtfs_network_diff.py` downloads and caches them.

## Method

**Schedule comparison** (`scripts/gtfs_network_diff.py`). Every number is tied to a named calendar date, resolved through `calendar.txt` and `calendar_dates.txt`, using matched Wednesdays, Saturdays, and Sundays. Anchor dates: Oct 15, 2025 (before) and Oct 14, 2026 (after), with Oct 18 and 19, 2025 against Oct 17 and 18, 2026 for weekends. Metrics are computed per stop and rolled up by route and neighborhood. Maximum headway uses 6 a.m.–8 p.m. operating hours.

**Frequent-service access.** Parcels and population within a quarter mile of a bus stop with a maximum headway of 15 minutes or less, before and after. Population is area-weighted from block groups. The script that produced these files depends on a parcel layer and helper code outside this repo, so only its outputs are included (`results/schedule/parcel_access_by_neighborhood.csv`, `population_access.csv`).

**Jobs access** (`scripts/accessibility/`). Uses [r5py](https://r5py.readthedocs.io/) to compute transit travel times from every Philadelphia block group to every Pennsylvania block group, on both networks, with identical geography, parameters and job data. Counts jobs reachable within 30, 45 and 60 minutes. Parameters were set to reproduce TransitCenter's published 2024 scores (see Validation).

**Rider weighting.** SEPTA's APC stop-level boardings, joined to GTFS stops on `Stop_Code` = `stop_id` (99.8% match).

## Findings

### Service level (matched weekdays, Philadelphia bus)

| Comparison | Trips | Departures | Wed 7–9 a.m. | Wed 9–11 p.m. |
|---|---|---|---|---|
| 2019 → 2025 | −17.6% | −14.7% | −23.3% | −4.4% |
| 2025 → 2026 (the redesign) | −0.1% | −0.7% | −4.2% | +0.1% |
| 2019 → 2026 | −17.7% | −15.3% | −26.5% | −4.4% |

Our 2019-to-2026 service level (85% by departures) is consistent with SEPTA's published Ridership Recovery Dashboard figure of 86% for June 2026, though that figure covers the whole system.

### Routes and stops

- Two new routes (72, 76). Six retired (35, 47M, 62, 78, 80, 89). Route 106 merged into 105.
- 134 stops removed, 142 added. An initial count of 389 removed stop IDs was wrong: two thirds had a served stop within 200 m, from renumbering and relocation.
- Of 307 route-directions, 285 kept the same stop spacing, 16 widened and 6 tightened. New routes 72 and 76 average 228 m between stops, tighter than the network.

### Jobs reachable by transit

| Threshold | Median jobs before → after | Change | Block groups better | Block groups worse |
|---|---|---|---|---|
| 30 min | 31,853 → 29,947 | −3.10% | 322 | 803 |
| 45 min | 360,280 → 346,985 | −1.77% | 385 | 901 |
| 60 min | 536,447 → 530,536 | −0.60% | 550 | 783 |

Population-weighted, the 45-minute change is −1.25%. Loss was smallest within a quarter mile of the subway spine (−0.66%) and largest more than 2 miles away (−3.43%).

### Who gained and lost

By schedule, the neighborhoods losing service skew toward more car-free households (−4.0% in the most car-free decile, +2.1% in the least), but those neighborhoods still have four to five times the service per resident. By jobs reached, the pattern runs the other way and is mild (−2.22% in the least car-free decile against −1.61% in the most). Declines since 2019 were even across demographic groups (28–34% in every decile).

### Riders

Bus and trolley ridership is down 22.8% (Oct 2025 vs Oct 2019) and 20.3% (Apr 2026 vs Apr 2019), against service down 17.7%. Rider-weighted service change for the redesign is −1.81%, versus −0.72% unweighted. No post-redesign ridership data had been published as of this writing.

## Validation

We reproduced TransitCenter's published 2024 Philadelphia scores at a block group correlation of 0.986 (median ratio ours/theirs 0.987; 76% of block groups within ±10%). Four parameters have to be matched to get there that are not obvious from the public methodology page: a 120-minute departure window, a 180-minute maximum trip time, 2020 LODES jobs, and block group centroids as origins. Absolute levels should be treated as accurate to about ±2%. The before-to-after change is more reliable because both networks used identical inputs. **Do not quote our absolute levels as TransitCenter numbers.**

## Files

| Path | Description |
|---|---|
| `results/schedule/route_changes.csv` | Per route and day: trips before/after, status (added, removed, retained), renames |
| `results/schedule/neighborhood_changes.csv` | Per neighborhood and day: stops, departures, AM peak departures, median max headway |
| `results/schedule/parcel_access_by_neighborhood.csv` | Parcels gaining/losing frequent bus access by neighborhood |
| `results/schedule/population_access.csv` | Population near frequent service, by block group |
| `results/schedule/summary.json`, `access_summary.json` | Totals and provenance of the runs |
| `results/accessibility/redesign_accessibility.csv` | Jobs reachable in 30/45/60 min before and after, by block group |
| `results/accessibility/validation_comparison.csv` | Our scores vs. TransitCenter's, by block group |
| `results/accessibility/jobs_by_bg_2020.csv` | LODES 2020 jobs per block group (input) |
| `scripts/gtfs_network_diff.py` | Snapshots two GTFS releases and diffs them |
| `scripts/accessibility/` | `clean_gtfs.py`, `score_redesign.py`, `validate.py`, `time_to_spine.py` |

Column descriptions for each CSV follow the [dataset template](../../docs/dataset-template.md) and still need to be written out in full. The headers are self-describing in the meantime. In `route_changes.csv`, `trips` counts distinct trips. In stop and neighborhood files, `departures` counts one per stop served, so the two are not comparable.

## Reproducing

Needs Python 3.11+, `geopandas`, `pandas`, `numpy`, `requests`, `shapely`, and for scoring `r5py` (Java 21).

```bash
# Schedule diff (downloads and caches GTFS releases)
python scripts/gtfs_network_diff.py \
    --baseline v202509141 --baseline-dates 20251015,20251018,20251019 \
    --current  v202608233 --current-dates  20261014,20261017,20261018
```

The diff reads neighborhoods from `data/processed/geojson_cache/phila_neighborhoods.geojson` (a path constant at the top of the script); download the boundaries from OpenDataPhilly and place them there or edit the constant.

For jobs scoring, set `ACCESSIBILITY_DIR` to a working folder containing the OSM extract, the cleaned GTFS (`clean_gtfs.py` produces it), the jobs table and the block groups zip (or point `BLOCK_GROUPS_ZIP` at it). A cold run of both networks takes about 6.5 hours on a laptop (peak memory about 3 GB). Do not interrupt a network build, which leaves a corrupt cache that fails on the next run.

## Known limitations and caveats

- **Compare like seasons.** School-year feeds carry about 26 extra 400-series school-tripper routes that do not run in summer. Never diff a fall feed against a summer one.
- **Never total `trips.txt` directly.** Feeds split service into different numbers of `service_id`s. Raw totals fell 24% across the redesign while matched-day service was flat.
- **The 15-minute frequency cutoff misleads.** About 400 stops moved from the 20–30 minute band into 15–20. A 15-minute threshold scores that as a loss of 17,164 parcels (46,922 people); a 20-minute threshold scores it as a gain of 23,649 parcels (60,742 people). Do not quote a single threshold as "access lost."
- **Philadelphia bus only for schedule metrics.** Regional Rail is included in jobs scoring but the Pennsylvania-only network omits New Jersey and Delaware services.
- **Single anchor day per day type.** Results use one Wednesday, Saturday and Sunday per feed. A second feed (Spring 2026) agreed with the neighborhood pattern in 95% of cases (r = 0.87).
- **Parcel-level results** are not included because of size. Neighborhood totals count a parcel in every neighborhood it touches, so they sum to more than the citywide total.

## License

Data CC BY 4.0, code MIT. Please credit Transit Forward Philly and the original sources.
