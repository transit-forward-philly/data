# DVRPC FFY2027 Pennsylvania TIP projects, by legislative district

**One-line summary:** The 407 mapped projects in DVRPC's draft FFY2027 Pennsylvania Transportation Improvement Program (FFY27–30), each placed in its PA House and Senate district with the 2025–26 member and the unofficial 2026 seat status.

## Source

- **Original source:** DVRPC, [Draft DVRPC FFY2027 TIP for PA (FY27-30) - Points](https://catalog.dvrpc.org/dataset/draft-dvrpc-ffy2027-tip-for-pa-fy27-30-points) (public ArcGIS FeatureServer)
- **Pulled on:** 2026-11-10
- **Geography:** DVRPC's five Pennsylvania counties (Bucks, Chester, Delaware, Montgomery, Philadelphia) plus SEPTA and multi-county programs
- **Time period covered:** FFY2027–2030 (in effect Oct 1, 2026 to Sept 30, 2028)

## Processing

Every DVRPC attribute was kept except the internal object ID. Each project point was placed in a House and Senate district by point-in-polygon against Census TIGER/Line 2024, then joined to the [2025–26 legislators](../../pennsylvania/legislators-2025-2026/) and the [2026 election flips](../../pennsylvania/election-2026-flips/). Script: [`pipelines/dvrpc_pa_tip/build.py`](../../../pipelines/dvrpc_pa_tip/build.py).

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
| `*_seat_2026_status` | `flip_r_to_d`, `flip_d_to_r`, `uncalled`, or `no_change_listed`. Unofficial, as of 2026-11-04. |

## Known gaps and caveats

- **Draft.** DVRPC's metadata still has the board adoption date blank ("July __, 2026"). Check whether an adopted version has replaced the layer.
- **No dollar amounts or schedules.** This layer has locations and scores only. Costs and phasing are in DVRPC's TIP document.
- **Not every project is mapped**, per DVRPC.
- **Two projects have no district**, because their points fall outside Pennsylvania's legislative maps.
- **"No change listed" is not "confirmed."** The election file lists only flipped and uncalled seats.
- **Point-in-polygon only.** A linear project can touch several districts; this assigns it to the district of its representative point.

## License

DVRPC data are provided under [DVRPC's data license](https://catalog.dvrpc.org/dvrpc_data_license.html). Joined columns CC BY 4.0. Please credit Transit Forward Philly and DVRPC.
