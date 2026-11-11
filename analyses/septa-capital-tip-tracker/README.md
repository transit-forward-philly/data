# SEPTA capital projects, the TIP, and who represents them

A working tracker of SEPTA's capital program: what is funded, what is on the regional Transportation Improvement Program (TIP), what is **unfunded**, and which legislators represent the places involved. It is meant as the base layer for advocacy and for the district-level reporting TFP wants to do.

## The question

For any SEPTA capital project: is it funded, does it appear on the TIP, who represents it, and if it is unfunded, is there related funded work?

## What's here

| Path | What it is |
|---|---|
| `web/index.html` + `web/data/` | The tracker, a static page with five views: stations by legislator, legislators, projects, Regional Rail platform punch list, and **At risk (unfunded)** |
| `data/septa_fy27_capital_projects.csv` | SEPTA's FY27 capital budget, one row per project, with the TIP MPMS number SEPTA assigns it |
| `data/dvrpc_pa_tip_ffy2027_draft.csv` | All 344 listings in DVRPC's PA TIP, including projects with no map point |
| `data/capital_tip_crosswalk.csv` | Capital budget joined to the TIP by MPMS, with the funding gap between the two |
| `data/unfunded_crosswalk.csv` | SEPTA's 46 unfunded projects linked, where possible, to the capital budget and TIP |
| `scripts/` | Parsers for the two source PDFs and the two crosswalk builders |

To view the tracker, serve the folder (the page loads JSON, so opening the file directly will not work):

```bash
cd web && python3 -m http.server 8000   # then open http://localhost:8000
```

## Sources

| Data | Source |
|---|---|
| Capital budget | SEPTA [FY2027 Operating and Capital Budget Proposal](https://wwww.septa.org/wp-content/uploads/page/planning/SEPTA-FY-2027-Operating-Capital-Budget-Proposal.pdf), capital project list |
| TIP | DVRPC Draft FFY2027 TIP for Pennsylvania (FY27–30) |
| Unfunded projects | [`datasets/septa-region/septa-fy27-unfunded-projects`](../../datasets/septa-region/septa-fy27-unfunded-projects/) |
| Mapped TIP projects and districts | [`datasets/septa-region/dvrpc-pa-tip-ffy2027`](../../datasets/septa-region/dvrpc-pa-tip-ffy2027/) (same TIP, 255 unique projects). The tracker's `tip_projects.json` is a narrower cut: the 14 SEPTA-area transit projects, grouped by project |
| Station platform types | SEPTA Regional Rail Stations ArcGIS layer (last edited 2021, so stale in places) |
| NJ and DE projects | DVRPC FY2024 NJ TIP (PATCO, NJ Transit) and WILMAPCO FY2027–30 TIP |
| Legislators | 2025–26 members (see caveats) |

Pulled September 2026 for the tracker data; the capital and TIP files are as of that pull.

## Method

**Capital budget to TIP.** SEPTA's budget lists a TIP MPMS number for each project. The TIP funds SEPTA at the **program level**, so one MPMS covers many capital projects (MPMS 77183 covers every station project). `build_capital_tip_crosswalk.py` therefore compares totals per MPMS: capital 12-year total (FY27–38) against TIP total programmed (FY27–30 plus future). A gap near zero means the two documents agree. SEPTA's fiscal year starts July 1 and the TIP's starts October 1, so small gaps may be timing, not real differences.

**Unfunded to capital budget.** `build_unfunded_crosswalk.py` links by a hand-reviewed list, not by fuzzy name matching: a first fuzzy pass paired unrelated projects (for example Exton Station with Bristol Station). Each link is typed:

- **same project:** the funded row and the unfunded row are the same project, and the unfunded amount is what SEPTA could not fund.
- **same program:** the funded row is the same recurring program; the unfunded row is extra scope or a later phase.
- **related:** a nearby or overlapping project, not the same line item.

17 of the 46 unfunded projects are linked; 29 are not, mostly because unfunded projects often have no capital budget row at all. **Unlinked does not mean the work is unrelated to anything funded.** It means no matching row was found, and the list is a starting point for review. Pairs are in `PAIRS` at the top of the script, so adding or correcting one is a one-line change.

## Findings so far

- Conshohocken station parking has $27.6M in the TIP but $0 in SEPTA's 12-year plan (the budget shows it fully funded in prior years). Federal preventive maintenance ($131.5M) is on the TIP only.
- The Regional Rail Master Plan program management line (MPMS 123967, $4M) is not on the TIP. Downingtown station (MPMS 93586) is on the TIP under PennDOT, not SEPTA.
- The Broad Street Line railcar replacement, $726.31M of the $2.04B unfunded, has only $1.0M in the 12-year capital plan.
- 15 of the 46 unfunded projects are ADA projects, $1,352.36M together.

## Known gaps and caveats

- **Legislators are the 2025–26 members.** Districts and members predate the November 2026 election and do not reflect new members taking office in January 2027. See [`dvrpc-pa-tip-ffy2027`](../../datasets/septa-region/dvrpc-pa-tip-ffy2027/) for unofficial 2026 results.
- **Unfunded projects have no districts yet.** Only the 17 linked projects show legislators, and those come from the TIP program they sit under, which can span many districts. Assigning each unfunded project to a district by its own location is still to do.
- **The tracker's district data is a snapshot.** `web/data/` was built once from the sources above and is not regenerated by the scripts here. `capital_budget.json` and `tip_projects.json` came from the same pulls as the CSVs, but nothing checks that they stay in sync.
- **Draft TIP.** Check whether DVRPC's adopted version has replaced the draft layer.
- **TIP equity scores** (`LI`, `T6`, `Comp`) are DVRPC's columns; their metadata does not define them. Confirm with DVRPC before citing.
- **Platform data is from 2021.** It missed some rebuilds (Yardley, finished 2018, still shows Low). Wawa station is missing from SEPTA's public database and is flagged, not filled in.
- **Delaware:** the Claymont decommissioning note is an inference from the WILMAPCO TIP and is marked "verify before publishing" in the data. The tracker shows only 2 of WILMAPCO's 49 mapped projects, those matched to SEPTA-served stations.
- **The source PDFs are not stored here.** The parsers expect `pdftotext -layout` output. See each script's header.
- **Take-action buttons are placeholders** and do nothing yet.

## License

Data CC BY 4.0, code MIT. Please credit Transit Forward Philly, SEPTA and DVRPC.
