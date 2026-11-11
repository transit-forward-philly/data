# SEPTA FY27 Unfunded Capital Projects

**One-line summary:** SEPTA's list of 46 capital projects that are deferred or descoped for lack of funding, totaling $2.04 billion.

## Source

- **Original source:** SEPTA, Unfunded Projects list, updated May 2026 for the [FY2027 Operating and Capital Budget Proposal](https://wwww.septa.org/wp-content/uploads/page/planning/SEPTA-FY-2027-Operating-Capital-Budget-Proposal.pdf)
- **Pulled on:** 2026-10-15
- **Geography:** SEPTA's five-county service area, plus multi-county programs
- **Time period covered:** FY2027 budget cycle

SEPTA's note on the list: these projects "may remain deferred/descoped if rising costs and inadequate funding require prioritizing current capital commitments, emergency needs, or safety, legal, and regulatory mandates," and they represent only a fraction of SEPTA's $10.2 billion state of good repair backlog.

## Processing

Typed from the source PDF into one row per project. Totals were checked against SEPTA's own subtotals: 46 projects, $2,041.12 million, 30 deferred and 16 descoped, and every county subtotal matches.

## Files

| File | Format | Description |
|---|---|---|
| `septa-fy27-unfunded-projects.csv` | CSV | One row per project |

## Columns

| Column | Type | Units | Description |
|---|---|---|---|
| `county` | text | | Bucks, Chester, Delaware, Montgomery, Philadelphia, or Multi-county |
| `status` | text | | `Deferred` (pushed to a later year) or `Descoped` (scope cut) |
| `project` | text | | Project name as SEPTA lists it |
| `value_millions` | number | USD millions | Project value as SEPTA lists it |
| `ada_project` | true/false | | SEPTA marks it as an ADA accessibility project |
| `source_note` | text | | Anything unusual in the source |

## Summary

| County | Projects | Value ($M) |
|---|---|---|
| Philadelphia | 11 | 947.98 |
| Multi-county | 22 | 752.25 |
| Montgomery | 5 | 129.28 |
| Chester | 3 | 109.09 |
| Delaware | 4 | 98.77 |
| Bucks | 1 | 3.75 |
| **Total** | **46** | **2,041.12** |

15 of the 46 are ADA projects, worth $1,352.36 million together. Most of that is the Broad Street Line railcar replacement ($726.31M).

## Known gaps and caveats

- The Broad Street Line railcar row carries a double asterisk in the source, and the list doesn't explain it.
- Projects aren't matched to DVRPC TIP MPMS IDs yet. That match is a good first task.
- Projects aren't assigned to council or legislative districts yet.

## License

CC BY 4.0. Please credit Transit Forward Philly and SEPTA.
