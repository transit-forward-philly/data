# DVRPC long-range plan: SEPTA projects and costs

**One-line summary:** The 84 Pennsylvania transit projects (SEPTA) in DVRPC's long-range plan, 39 funded and 45 unfunded, each with its scope and cost.

## Source

- **Original source:** DVRPC, [Update: Connections 2050 Long-Range Plan, Appendices](https://www.dvrpc.org/Reports/25140.pdf) (May 2026), Appendix F Financial Plan: Table F-25 "Pennsylvania Transit MRPs, Funded" (PDF pp. 251–256) and the transit rows of Table F-30 "Pennsylvania MRPs, Unfunded" (PDF pp. 271–277). Funded costs are revised where DVRPC's [Amendment 1](https://www.dvrpc.org/Reports/26140.pdf) (adopted September 2026), Table 5, changed them.
- **Pulled on:** 2026-11-24
- **Geography:** SEPTA's five Pennsylvania counties, plus Mercer County, New Jersey, for three Trenton-area projects (PAT072, PAT075, PAT078)
- **Time period covered:** plan periods 2026–2050

## Processing

Script: [`pipelines/dvrpc_lrp_septa_projects/build.py`](../../../pipelines/dvrpc_lrp_septa_projects/build.py). It downloads both PDFs, reads the tables from `pdftotext -layout` output, and stops if the row counts (39 funded, 45 unfunded, 6 amended) change or a scope does not end in a period. Text that wraps across lines or onto the next page is joined, and a word split at a line-ending hyphen or dash is rejoined without a space. Footnote markers are removed from the Amendment 1 notes. Nothing is retyped by hand.

## Files

| File | Format | Description |
|---|---|---|
| `dvrpc-lrp-septa-projects.csv` | CSV | One row per Major Regional Project (MRP) with an ID beginning PAT |

## Columns

| Column | Type | Units | Description |
|---|---|---|---|
| `table` | text | | `F-25 funded` or `F-30 unfunded` |
| `mrp_id` | text | | DVRPC's MRP ID |
| `facility`, `scope`, `location` | text | | As printed in the May 2026 appendix. Amendment 1 does not change `scope`; where it changed a project's scope, `amendment1_note` says how |
| `cost_millions` | number | $ millions | As printed in the May 2026 appendix |
| `amendment1_cost_millions`, `amendment1_note` | number, text | $ millions | Amendment 1's cost and its note, for the six projects in Amendment 1 Table 5; blank for the rest. PAT041's amended cost equals the original; its amendment changed the scope |
| `current_cost_millions` | number | $ millions | Amendment 1 cost where there is one, otherwise the appendix cost |
| `dollar_basis` | text | | `year of expenditure` (funded) or `2025 dollars` (unfunded) |

## Known gaps and caveats

- **Funded and unfunded costs are in different dollars** (year of expenditure versus 2025 dollars). Do not add them together.
- **The plan period and project categories columns are not kept.** Table F-25 (funded) has a plan period column; see the PDF for each project's period. Table F-30 (unfunded) has none. Both tables have a Project Categories column (T1, T2, T3 shares), which is left out.
- **Unfunded items are not commitments.** They are projects DVRPC lists as needs without identified funding.
- **Amendment 1's PAT001 note says the cost rose "from $98.53 million"**, while the May appendix prints $96.5M. Both are kept as printed. Likewise PAT085 (B cars): the appendix prints $173.6M and Amendment 1 says the cost rose "from $127 million" to $727.3M, of which "approximately $726.3 million is deferred after FY 2038." Amendment 1's footnote on PAT085 reads: "The Connections 2050 Plan listed this project from 2041–2050 for $1,031.5 million. For the Board-adopted version of Update: Connections 2050, the project was de-scoped to include only preliminary infrastructure."
- **Locations are as DVRPC printed them.** "Mercer" is Mercer County, New Jersey. PAT082 (Wilmington/Newark Yard) lists "Delaware, Philadelphia" while its scope says the yard would be built "in Delaware", so "Delaware" there may mean the state and not Delaware County.
- **PAT052's scope is as DVRPC printed it.** The facility is "NHSL Station Accessibility Projects", but the scope describes a road project "near I-295 and NJ Turnpike Exit 6A". This looks like a copy error in the appendix; it is kept as printed. Likewise PAT066's facility reads "Doylestown Line Double" in the PDF, and PAT087's scope has no closing period.

## License

DVRPC data are provided under [DVRPC's data license](https://catalog.dvrpc.org/dvrpc_data_license.html). Joined columns CC BY 4.0. Please credit Transit Forward Philly and DVRPC.
