# SEPTA Student Pass Expansion

**One-line summary:** Cost, enrollment, and utilization data behind SDP's $63.8M expansion estimate, drawn from public hearing testimony and enrollment records.

## Source

- **SDP Exhibit A:** Resolution 260441, presented to City Council Transportation & Public Utilities Committee on October 6, 2026. [CM Landau hearing record]
- **SDP Enrollment:** 2025–26 October 1 count via [OpenDataPhilly](https://opendataphilly.org/datasets/sdp-school-enrollment-and-demographics/)
- **PDE Non-public enrollment:** [Private and Nonpublic Schools Enrollment 2025–26](https://www.education.pa.gov/DataAndReporting/Enrollment/Pages/NonPubEnroll.aspx), schools located in Philadelphia
- **Student Fares That Work:** [phillystudentfares.netlify.app/costs](https://phillystudentfares.netlify.app/costs), SDP materials from December 2024
- **Geography:** Philadelphia
- **Time period covered:** 2025–26 enrollment; FY billing from Exhibit A (year unspecified)

## Processing

Figures were transcribed from Exhibit A (a one-page PDF), SDP written testimony, and the Student Fares That Work website. Derived measures (monthly active rates, cost scenarios) are calculated from those figures and documented in the `notes` column.

## Files

| File | Format | Description |
|---|---|---|
| `current_program.csv` | CSV | Current 7–12 program: eligible students, cards, billing, rates |
| `enrollment_by_grade_band.csv` | CSV | Grades 5–6 and 7–12 enrollment by school type (public and non-public) |
| `exhibit_a_assumptions.csv` | CSV | Every assumption in SDP's expansion cost estimate |
| `utilization_data.csv` | CSV | Monthly active card rates from two sources plus SEPTA's projection |
| `cost_scenarios.csv` | CSV | Expansion cost under different program designs (billing months, rate, flat payment) |

## Key context

The current SEPTA student pass covers grades 7–12, with a 1.5-mile distance rule. SDP pays SEPTA a flat monthly rate ($88.60) for every card tapped at least once that month. Exhibit A projects 71,036 monthly active cards at $110.20 for 12 months = $93.9M total, $63.8M more than the current $30.15M program.

The 71,036 is labeled a "utilization estimate" and at 54% of the eligible pool matches the current monthly active rate (47–57%), suggesting SEPTA already discounted for students who won't ride. The remaining questions are about summer billing, the rate, and the billing model.

An interactive calculator is at [phillystudentfares.netlify.app/calculator](https://phillystudentfares.netlify.app/calculator).

## Known gaps and caveats

- **Month-by-month billing not available.** The biggest gap: we don't know how summer compares to school-year billing. Exhibit A gives only the annual total.
- **71,036 methodology unknown.** SEPTA hasn't clarified whether this means card holders or monthly active cards.
- **Non-public enrollment is by school location, not student residence.** PDE counts students at schools in Philadelphia; some may commute from outside the city.
- **524 publicly funded non-public students** may overlap with SDP's counts. Using private-pay only (18,760) avoids double counting.
- **2025–26 data.** 2026–27 enrollment not yet published (expected December 2026/January 2027).

## License

CC BY 4.0. Please credit Transit Forward Philly and the original source.
