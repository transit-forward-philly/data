# DVRPC FFY2027 Pennsylvania TIP projects, by legislative district

**One-line summary:** The 407 mapped projects in DVRPC's draft FFY2027 Pennsylvania Transportation Improvement Program (FFY27–30), each placed in its PA House and Senate district with the 2025–26 member and the unofficial 2026 winner.

## Source

- **Original source:** DVRPC, [Draft DVRPC FFY2027 TIP for PA (FY27-30) - Points](https://catalog.dvrpc.org/dataset/draft-dvrpc-ffy2027-tip-for-pa-fy27-30-points) (public ArcGIS FeatureServer)
- **Pulled on:** 2026-11-10
- **Geography:** DVRPC's five Pennsylvania counties (Bucks, Chester, Delaware, Montgomery, Philadelphia) plus SEPTA and multi-county programs
- **Time period covered:** FFY2027–2030 (in effect Oct 1, 2026 to Sept 30, 2028)

## Processing

Every DVRPC attribute was kept except the internal object ID. Each project point was placed in a House and Senate district by point-in-polygon against Census TIGER/Line 2024, then joined to the [2025–26 legislators](../../pennsylvania/legislators-2025-2026/) and the [2026 election results](../../pennsylvania/election-2026-results/). Script: [`pipelines/dvrpc_pa_tip/build.py`](../../../pipelines/dvrpc_pa_tip/build.py).

## Files

| File | Format | Description |
|---|---|---|
| `dvrpc-pa-tip-ffy2027.csv` | CSV | 407 rows: 318 highway (`H`), 70 transit (`T`), 19 intermodal (`INT`) |

## Columns

| Column | Description |
|---|---|
| `mpms_id` | PennDOT project ID. A few projects have more than one point. |
| `prog` | Program: `H` highway, `T` transit, `INT` intermodal |
| `road_name`, `descriptio` | Project name and type of work |
| `cty` | DVRPC county, or `SEPTA` or `Various` for programs |
| `mappingfea` | `Point` or `Linear`. For linear projects the point is a representative location, not the full extent. |
| `max_li`, `max_t6`, `max_comp` | DVRPC score columns. DVRPC's metadata does not define them; the research roadmap treats them as equity scores. Confirm with DVRPC before citing. |
| `latitude`, `longitude` | As DVRPC gives them |
| `house_district`, `senate_district` | Computed from Census boundaries |
| `*_member_2025_26`, `*_party_2025_26` | Member for that district |
| `*_seat_2026_status` | `hold`, `flip_r_to_d`, `flip_d_to_r`, `uncounted`, or `not_up` (Senate seats not on the 2026 ballot). Unofficial, as of 2026-11-10. |
| `*_winner_2026`, `*_winner_party_2026` | Unofficial winner of that seat; blank where the count is unfinished or the seat was not up |

## Related DVRPC layer, not yet pulled

**CHSTP** is DVRPC's Coordinated Human Services Transportation Plan; its [Priority Score layer](https://catalog.dvrpc.org/dataset/coordinated-human-services-transportation-plan-chstp-priority-score) scores areas by essential services, jobs and transit accessibility to show where service could help vulnerable populations. The roadmap's planned comparison of CHSTP scores with TIP investment is not built yet. The updated plan ("Equity Through Access") was accepted by the DVRPC Board on Jan 23, 2025.

## Known gaps and caveats

- **Draft.** DVRPC's metadata still has the board adoption date blank ("July __, 2026"). Check whether an adopted version has replaced the layer.
- **No dollar amounts or schedules.** This layer has locations and scores only. Costs and phasing are in DVRPC's TIP document.
- **Not every project is mapped**, per DVRPC.
- **Two projects have no district**, because their points fall outside Pennsylvania's legislative maps.
- **Results are unofficial and incomplete.** They come from MultiState, and three House races (HD-41, 143, 147) were still being counted; 16 projects fall in those seats.
- **Point-in-polygon only.** A linear project can touch several districts; this assigns it to the district of its representative point.

## License

DVRPC data are provided under [DVRPC's data license](https://catalog.dvrpc.org/dvrpc_data_license.html). Joined columns CC BY 4.0. Please credit Transit Forward Philly and DVRPC.
