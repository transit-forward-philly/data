# SEPTA Student Pass Expansion

**One-line summary:** Cost, enrollment, utilization and school-trip travel-time data behind SDP's $63.8M estimate for expanding the student pass from grades 7–12 to grades 5–12, drawn from public hearing testimony, enrollment records and SEPTA's published schedule.

## Source

- **SDP Exhibit A:** Resolution 260441, presented to the City Council Transportation & Public Utilities Committee on October 6, 2026 (CM Landau hearing record)
- **SDP enrollment:** 2025–26 October 1 count, [OpenDataPhilly](https://opendataphilly.org/datasets/sdp-school-enrollment-and-demographics/). The 2026–27 count was not yet posted as of 2026-11-23.
- **SDP catchment retention:** students by home catchment and enrolled school, 2025–26, [OpenDataPhilly](https://opendataphilly.org/datasets/sdp-school-catchment-retention/); [catchment boundaries](https://opendataphilly.org/datasets/sdp-school-catchment-areas/) for 2024–25
- **PDE non-public enrollment:** [Private and Nonpublic Schools Enrollment 2025–26](https://www.pa.gov/agencies/education/data-and-reporting/enrollment), schools located in Philadelphia
- **Student Fares That Work:** [phillystudentfares.netlify.app/costs](https://phillystudentfares.netlify.app/costs), SDP materials from December 2024
- **Travel times:** SEPTA GTFS schedule (fall 2026 feed, service on Wednesday 2026-10-14), OpenStreetMap streets (Geofabrik Pennsylvania extract, 2026-10-22), 2020 Census blocks
- **Geography:** Philadelphia
- **Time period covered:** 2025–26 enrollment; current-program billing from Exhibit A (fiscal year not stated); weekday morning travel times on the fall 2026 schedule

## Processing

**Hearing and enrollment figures** were transcribed from Exhibit A (a one-page PDF), SDP written testimony and the Student Fares That Work website. Derived measures (monthly active rates, cost scenarios) are calculated from those figures and documented in the `notes` columns.

**School-trip travel times** were computed with [r5py](https://r5py.readthedocs.io/) on October 22, 2026:

1. Every 2025–26 home-catchment-to-school flow in SDP's catchment retention file was spread over the populated 2020 census blocks in the home catchment, weighted by population. No student addresses or travel records exist: these estimate trip length from where a catchment's residents live, not trips students reported.
2. Flows were scaled to grades 7–12 (or 5–6) by each school's share of October 1 enrollment in those grades. The flow file has no grades, and it does not say whether a student is counted under their elementary, middle or high school catchment. Middle, K–8 and 6–12 schools use the middle school catchment, high schools the high school catchment, and elementary schools the elementary catchment.
3. From each block to each school: walking at 3 mph (4.8 km/h; also 2.5 mph for grades 5–6), SEPTA transit (median trip over departures between 7:00 and 8:00 AM, walking at 3 mph to and from stops), and walking-route distance.
4. Students were grouped into three cumulative school-trip tiers by walk time and the time transit saves. Counts under 20 students were suppressed.

The per-trip outputs and scripts from that run were not kept, so the travel-time files here are its published summaries. A reproducible version will go in `analyses/`.

**Eligibility scenarios** build monthly active cards from the eligible pool: students beyond 1.5 miles at the current program's monthly active rate (57% of eligible students in a school-year month), and students within 1.5 miles at half that rate (an assumption; no data exists). Shares within 1.5 miles are 40% for grades 7–12 (estimated 37–45%) and 64% for grades 5–6 (estimated 61–67%). The current-pool step (58,844) is close to the program's actual 59,706 eligible students.

**Catchment destinations** come from SDP's catchment retention file, grouped by the type of school students attend. Counts under 20 are suppressed, along with a second cell wherever one hidden cell could be recovered from the total.

## Files

| File | Format | Description |
|---|---|---|
| `current_program.csv` | CSV | Current grades 7–12 program: eligible students, cards, billing, rates |
| `enrollment_by_grade_band.csv` | CSV | Grades 5–6 and 7–12 enrollment by school type (public and non-public) |
| `exhibit_a_assumptions.csv` | CSV | Every assumption in SDP's expansion cost estimate |
| `utilization_data.csv` | CSV | Monthly active card rates from two sources plus SEPTA's projection |
| `cost_scenarios.csv` | CSV | Expansion cost under different program designs (billing months, rate, flat payment, eligibility) |
| `eligibility_scenarios.csv` | CSV | Eligible students, active cards and cost at each expansion step |
| `school_trip_tiers.csv` | CSV | Students for whom transit plausibly helps with the school trip, by tier, grade band, school level and sector |
| `school_trip_tiers_5_12.csv` | CSV | The tiers combined for grades 5–12, public and non-public |
| `within_1_5_miles.csv` | CSV | Share of students attending a school within 1.5 miles, by straight line and walking route |
| `walk_and_saving_bands.csv` | CSV | Students by walk time to school and by minutes transit saves |
| `zone_travel_times.csv` | CSV | Walking and transit times inside the 1.5-mile zone around middle and high school catchment schools |
| `catchment_destinations.csv` | CSV | For each middle and high school catchment, where the students who live there attend school |

## Columns

The first four files are unchanged; their columns are described in their headers and `notes`/`source` columns.

**`cost_scenarios.csv`**

| Column | Type | Units | Description |
|---|---|---|---|
| `scenario` | text | | Scenario key |
| `active_cards_monthly` | integer | cards | Cards billed in a school-year month (blank for the flat payment) |
| `monthly_rate` | number | dollars per card per month | Rate per active card |
| `months_billed` | integer | months | School-year months billed at the full level |
| `summer_factor` | number | share | Remaining months billed as a share of the school-year level |
| `total_annual` | integer | dollars | Annual cost |
| `additional_over_current` | integer | dollars | Annual cost minus the current $30,150,580 |
| `notes` | text | | How the row was calculated |

**`eligibility_scenarios.csv`**

| Column | Type | Units | Description |
|---|---|---|---|
| `scenario` | text | | Scenario key |
| `label` | text | | What the step includes |
| `eligible_students` | integer | students | Public and non-public students eligible at this step |
| `active_cards_monthly` | integer | cards | Estimated cards active in a school-year month |
| `monthly_rate` | number | dollars | $110.20, the rate in Exhibit A |
| `total_all_12_months` | integer | dollars | Annual cost billing all 12 months at the school-year level, as Exhibit A does |
| `total_reduced_summer` | integer | dollars | July and August at 53% of the school-year level |
| `total_school_year_only` | integer | dollars | 10 school-year months only |

**`school_trip_tiers.csv`**

| Column | Type | Units | Description |
|---|---|---|---|
| `grade_band` | text | | `7-12` or `5-6` |
| `walk_speed` | text | | Walking speed used for the walk time |
| `group_type` | text | | `all`, `school_level` or `sector` of the school attended |
| `group` | text | | The group |
| `group_students_est` | integer | students | Estimated students in the group |
| `tier` | text | | `low` (heaviest likely school users), `medium` or `high`; each tier includes the ones above it |
| `rule` | text | | Walk time and transit saving that define the tier |
| `students_est` | integer | students | Estimated students in the tier (blank where only the share was kept) |
| `pct_of_group` | number | percent | Share of the group in the tier |

**`school_trip_tiers_5_12.csv`**

| Column | Type | Units | Description |
|---|---|---|---|
| `tier` | text | | `low`, `medium` or `high` |
| `rule` | text | | Tier rule |
| `grades_7_12_public` | integer | students | From `school_trip_tiers.csv` |
| `grades_5_6_public` | integer | students | From `school_trip_tiers.csv`, at 3 mph |
| `nonpublic_5_12_assumed` | integer | students | The 19,284 non-public students at the grade 7–12 public share; there is no catchment data for them |
| `total_5_12` | integer | students | Sum |

**`within_1_5_miles.csv`**

| Column | Type | Units | Description |
|---|---|---|---|
| `grade_band` | text | | `7-12` or `5-6` |
| `group_type` | text | | `all`, `school_level` or `sector` |
| `group` | text | | The group |
| `group_students_est` | integer | students | Estimated students in the group |
| `pct_within_straight_line` | number | percent | Attending a school within 1.5 miles in a straight line (blank where not kept) |
| `pct_within_walking_route` | number | percent | Within 1.5 miles by walking route |

**`walk_and_saving_bands.csv`**

| Column | Type | Units | Description |
|---|---|---|---|
| `grade_band` | text | | `7-12` or `5-6` |
| `measure` | text | | `walk_minutes` (walking at 3 mph) or `transit_saving_minutes` (walk minus transit) |
| `band` | text | minutes | Band |
| `students_est` | integer | students | Estimated students (grades 7–12 only) |
| `pct_of_grade_band` | number | percent | Share of the grade band |

**`zone_travel_times.csv`**

| Column | Type | Units | Description |
|---|---|---|---|
| `catchment_level` | text | | `middle` or `high` |
| `catchments` | integer | | Catchments summarized |
| `mode` | text | | Walking speed or transit |
| `median_minutes` | number | minutes | Median across catchments of each zone's population-weighted median |
| `p90_minutes` | number | minutes | Same, 90th percentile (blank where not kept) |
| `max_minutes` | number | minutes | Same, maximum (blank where not kept) |

**`catchment_destinations.csv`**

| Column | Type | Units | Description |
|---|---|---|---|
| `catchment_level` | text | | `middle` or `high` |
| `catchment_school` | text | | School whose catchment the students live in |
| `resident_students` | integer | students | Public school students living in the catchment, all grades |
| `own_catchment_school` through `outside_district_list` | integer or `suppressed` | students | Students by the type of school they attend: their own catchment school, another district neighborhood school, district criteria-based, district citywide, Philadelphia charter, cyber charter, district virtual, alternative, or outside the district's list |
| `pct_own_catchment_school` | number | percent | Share attending their own catchment school |

## Key context

The current SEPTA student pass covers grades 7–12, with a 1.5-mile distance rule. SDP pays SEPTA a monthly rate ($88.60) for every card tapped at least once that month. Exhibit A projects 71,036 monthly active cards at $110.20 for 12 months = $93.9M total, $63.8M more than the current $30.15M program.

The 71,036 is labeled a "utilization estimate" and at 54% of the eligible pool matches the current monthly active rate (47–57%), suggesting SEPTA already discounted for students who won't ride. The remaining questions are about summer billing, the rate, the billing model, and how students who live close to school are treated.

On the school trip itself: an estimated 38,700 to 55,500 grade 7–12 public students and 7,300 to 11,600 grade 5–6 public students attend a school where transit plausibly helps; with non-public students, about 55,000 to 80,000 for grades 5–12. Inside 1.5 miles, transit rarely beats walking: a median 8 minutes either way in middle school catchments, and 20.5 minutes walking against 18 by transit in high school catchments. Most grade 7–12 students with a long school trip are already eligible today, since a 30-minute walk is about 1.5 miles.

An interactive calculator is at [phillystudentfares.netlify.app/calculator](https://phillystudentfares.netlify.app/calculator).

## Known gaps and caveats

- **Month-by-month billing not available.** The biggest gap: we don't know how summer compares to school-year billing. Exhibit A gives only the annual total.
- **71,036 methodology unknown.** SEPTA hasn't clarified whether this means card holders or monthly active cards.
- **$88.60 is 23.6% off the $116 retail pass,** though it is often described as 25%; 25% off would be $87.00.
- **Travel times are estimates by catchment, not by student.** Students are spread across where their catchment's residents live. High school catchments are large, so those estimates are coarser.
- **No grades in the flow file.** Grade 7–12 and 5–6 counts are scaled from each school's grade mix. For grades 5–6, 1,632 students (5.9%) at 6–12 and K–12 schools were routed from high school catchments because no other catchment applies; without them the grade 5–6 tiers are 24.2%, 32.1% and 39.6% instead of 26.5%, 34.7% and 42.2%.
- **Tiers cover the school trip only.** Students also ride for jobs, activities and weekends, so the high tier is not a ceiling on card use. The tiers leave out being driven, safety, weather and cost.
- **Use by students within 1.5 miles is unknown.** The eligibility scenarios assume half the farther-away rate; `all_512_no_rule_same_use` shows the result if they ride as much.
- **Non-public enrollment is by school location, not student residence.** PDE counts students at schools in Philadelphia; some may commute from outside the city. Non-public students are not in the travel-time work.
- **524 publicly funded non-public students** may overlap with SDP's counts. Using private-pay only (18,760) avoids double counting.
- **Cyber charter students (14,827, all grades)** are excluded from the pools and travel times; they have no daily trip to a school building.
- **2025–26 data.** The 2026–27 enrollment count was not yet posted as of 2026-11-23.

## License

CC BY 4.0. Please credit Transit Forward Philly and the original source.
