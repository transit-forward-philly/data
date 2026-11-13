# SEPTA Key Advantage partners: summary tables

**One-line summary:** Aggregate counts of the employers on SEPTA's September 2026 Key Advantage participation list, by size cohort, sector and Philadelphia council district. No partner is named.

## Source

- **Original source:** SEPTA, "Key Advantage Participation List – September 2026," released Oct. 27, 2026 in response to a Right-to-Know request. The list has 70 partners and 64,895 members.
- **Pulled on:** 2026-10-27
- **Geography:** Employer worksites in Philadelphia and nearby suburbs
- **Time period covered:** Participation as of September 2026

The partner-level list is not republished here. These tables are built from it by [`aggregate_partners.py`](../../../pipelines/septa_key_advantage/aggregate_partners.py).

## Processing

- Four college student programs are dropped because they are not employers. That leaves **66 employer partners** and 60,260 members.
- Each partner was placed at its main worksite (web research, then geocoding) and assigned to a 2024 council district. Six could not be placed.
- Each partner was coded by industry (a NAICS-style sector) by hand.
- Disclosure rules, to keep any one partner from being picked out:
  - Partners are grouped into cohorts, never listed.
  - Sectors with fewer than 5 partners are merged into "All other sectors."
  - A district's small-partner split is blank when it has fewer than 5 partners.
  - There are no sector-by-size or sector-by-district tables, and no member totals by district.

## Files

| File | Format | Description |
|---|---|---|
| `size_cohorts.csv` | CSV | Partners and members by size cohort |
| `sectors.csv` | CSV | Partners by sector |
| `council_districts.csv` | CSV | Partners per council district, and how many are small |

## Columns

**`size_cohorts.csv`:** `cohort` (members enrolled through the partner: 1-19, 20-49, 50-249, 250+), `partners`, `pct_of_partners`, `members`, `pct_of_members`.

**`sectors.csv`:** `sector`, `partners`, `pct_of_partners`. Sector is the partner's main line of business, such as professional services (law firms, consultants, architects), health care, or unions, associations and civic groups.

**`council_districts.csv`:** `council_district` (1–10, "Outside Philadelphia" or "Not located"), `partners`, `partners_under_50_members`, `pct_under_50_members`.

## Findings

- 42 of 66 employer partners (64%) have fewer than 50 Key Advantage members, and 57 (86%) have fewer than 250.
- Nine partners with 250 or more members account for 96% of all members.
- Partners are concentrated in District 5 (20), District 1 (16), District 2 (10) and District 3 (9). Districts 6, 7, 9 and 10 have none.

## Known gaps and caveats

- **"Small" here means few Key Advantage members, not a small company.** SEPTA's list gives members per partner, not employees. A partner with 30 members could be a 5,000-person firm with a few people enrolled.
- Partners are placed at one worksite. A partner with staff at many sites counts once, in one district.
- Employer worksites are not where pass holders live or ride.
- Sector coding is ours and has not been checked with the partners.

## License

CC BY 4.0. Please credit Transit Forward Philly and the original source (SEPTA).
