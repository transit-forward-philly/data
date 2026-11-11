# Datasets

Cleaned, documented datasets. Each dataset gets its own folder with its data files and a README based on [the template](../docs/dataset-template.md). Folders are grouped by geography. Small, human-reviewed record sets are stored as [gitsheets](../docs/gitsheets.md); large tables and map layers stay as CSV or GeoJSON.

## SEPTA region

| Dataset | Description | Format | Last updated |
|---|---|---|---|
| [SEPTA bus delay](septa-region/septa-bus-delay/) | Bus, trolley and Metro delay by route, stop, month and hour, Nov 2025 – Oct 2026 | CSV | 2026-10-15 |
| [SEPTA FY27 unfunded capital projects](septa-region/septa-fy27-unfunded-projects/) | 46 deferred or descoped projects, $2.04B, by county, ADA projects flagged | CSV | 2026-10-15 |
| [SEPTA Regional Rail stations](septa-region/septa-regional-rail-stations/) | 155 station rows with location, accessibility, amenities, ridership counts and SEPTA-assigned districts | CSV | 2026-11-10 |
| [Regional Rail stations by district](septa-region/regional-rail-station-districts/) | Each station placed in its PA House and Senate district, with 2025–26 member and 2026 seat status | CSV | 2026-11-10 |

## Philadelphia

| Dataset | Description | Format | Last updated |
|---|---|---|---|
| [Student pass expansion](philadelphia/student-pass-expansion/) | Cost, enrollment, and utilization data behind SDP's $63.8M expansion estimate | CSV | 2026-11-10 |

## Pennsylvania

| Dataset | Description | Format | Last updated |
|---|---|---|---|
| [PA legislators, 2025–26 session](pennsylvania/legislators-2025-2026/) | Fixed snapshot of 203 House and 50 Senate members (May 2026, plus two vacancies filled by October) | gitsheet | 2026-11-10 |
| [2026 election: flipped and uncalled seats](pennsylvania/election-2026-flips/) | 18 seats that changed party or were uncalled, unofficial as of 2026-11-04 | gitsheet | 2026-11-10 |
| [Transportation priorities, 2027–28](pennsylvania/transportation-priorities-2027-28/) | 20 scored concepts from the prioritization memo, with the 2025–26 bills that carry each | gitsheet | 2026-11-10 |
| [Transportation votes, 2025–26](pennsylvania/transportation-votes-2025-26/) | Floor and committee roll calls on transit funding and bike lane bills, with every member's vote | gitsheet + CSV | 2026-11-10 |
| [Boundaries](pennsylvania/boundaries/) | House and Senate districts, counties, municipalities, with census and permit facts | GeoJSON | 2026-11-10 |
