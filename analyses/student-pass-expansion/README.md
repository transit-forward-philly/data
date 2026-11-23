# Student pass expansion: who needs a pass for the school trip, and what it costs

Supporting analysis for the [student pass expansion dataset](../../datasets/philadelphia/student-pass-expansion/), responding to SDP's $63.8M estimate (Exhibit A, City Council hearing of October 6, 2026) for expanding SEPTA student passes from grades 7–12 to grades 5–12.

## The question

How many students would plausibly use a pass to get to school at each expansion step (adding grades 5–6, removing the 1.5-mile rule), and how much of the cost estimate depends on that, on which months are billed, and on the rate?

## Data used

- 2025–26 enrollment: SDP October 1 count and PDE non-public enrollment ([`enrollment_by_grade_band.csv`](../../datasets/philadelphia/student-pass-expansion/enrollment_by_grade_band.csv))
- SDP catchment retention (students by home catchment and school attended, 2025–26) and catchment boundaries (2024–25), via the [Philly School Data Explorer](https://github.com/jongeeting/philly-school-data-explorer) core tables
- SEPTA's fall 2026 GTFS schedule, OpenStreetMap streets and 2020 Census blocks for travel times
- Exhibit A and the current program's billing ([`current_program.csv`](../../datasets/philadelphia/student-pass-expansion/current_program.csv))

## Method

1. **Travel times.** Each home-catchment-to-school flow was spread over the populated census blocks in the home catchment, and walking, transit and driving times were computed from each block to the school with r5py (weekday 8 AM arrival, transit as the median over 7:00–8:00 departures). These estimate trip lengths from where a catchment's residents live; no student addresses or travel records are used.
2. **School-trip tiers.** Students count toward a tier when the walk is long and transit saves real time: low (walk over 45 minutes and transit saves 15 or more), medium (over 30 and 10 or more), high (over 20 and 5 or more).
3. **Eligibility scenarios.** Eligible students at each step times the current program's monthly active rate (57%), with students within 1.5 miles at half that rate, times $110.20, under three assumptions about which months are billed.

The full method and caveats are in the [dataset README](../../datasets/philadelphia/student-pass-expansion/README.md).

## Findings

- About 55,000 to 80,000 grade 5–12 students attend a school where transit plausibly helps with the daily trip; SEPTA's projection of 71,036 monthly active cards falls inside that range.
- Inside 1.5 miles, transit rarely beats walking: a median 8 minutes either way in middle school catchments, 20.5 minutes walking against 18 by transit in high school catchments.
- Most grade 7–12 students with a long school trip are already eligible today. The new school-trip need the expansion adds is about 15,000 to 19,500 public students.
- Which months are billed moves the cost about as much as which expansion step is chosen (see [`eligibility_scenarios.csv`](../../datasets/philadelphia/student-pass-expansion/eligibility_scenarios.csv)).

## What's here

| Path | What it is |
|---|---|
| `scripts/build_dataset_files.py` | Writes the travel-time summary CSVs, the eligibility and cost scenarios, and the catchment breakdown into the dataset folder |

Run it with the school data core tables, either from a built checkout or from a [release](https://github.com/jongeeting/philly-school-data-explorer/releases) (download `core__catchment_flow.parquet`, `core__school_year_attr.parquet` and `core__school_placeholder.parquet` into one folder):

```bash
pip install duckdb pandas
python scripts/build_dataset_files.py --core path/to/core-tables
```

## Known limitations

- The routing run itself (r5py scripts and per-trip outputs from 2026-10-22) was not kept. The script carries its published summaries as constants; re-running the routing is a follow-up.
- Estimates are by catchment, not by student, and the flow file has no grades: grade bands are scaled from each school's grade mix.
- Use of passes by students within 1.5 miles of school, and summer billing in the current program, are unknown; both are assumptions in the scenarios.
- Enrollment is 2025–26; the 2026–27 count was not yet posted as of 2026-11-23.
