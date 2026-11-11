# 2026 PA general election: seats that changed or are uncalled

**One-line summary:** The Pennsylvania House and Senate seats that flipped party, or were still uncalled, in the Nov 3, 2026 general election, with the prior incumbent from our 2025–26 roster.

> **Preliminary.** These are unofficial, morning-after (2026-11-04) results. Re-verify against certified Department of State returns before publishing, and change `result_status` from `unofficial` once a seat is certified.

## Source

- **Original source:** Build Philly Now election brief of 2026-11-04, which compiled unofficial results from MultiState, Spotlight PA, the Inquirer, WHYY, Daily Voice and PublicSource. The flip lists come from `coalition-memos/2026-election-assets/render_flip_maps.py` in [PA Housing Votes](https://github.com/jongeeting/pa-housing-votes).
- **Pulled on:** 2026-11-10
- **Geography:** Pennsylvania House (203 seats) and Senate (odd-numbered seats were up)
- **Time period covered:** 2026 general election, results as of 2026-11-04

## Processing

Typed from the flip lists above and joined to [`legislators-2025-2026`](../legislators-2025-2026/) for the prior incumbent and party. This is a [gitsheet](../../../docs/gitsheets.md): one record per seat in `records/<chamber>/<district>.toml`, validated by `.gitsheets/pa-election-2026-flips.toml`.

## Files

| File | Format | Description |
|---|---|---|
| `records/house/*.toml`, `records/senate/*.toml` | TOML | 18 records: 6 House R→D flips, 7 uncalled House seats, 4 Senate R→D flips, 1 Senate D→R flip |

## Fields

| Field | Description |
|---|---|
| `chamber`, `district` | Seat |
| `outcome` | `flip_r_to_d`, `flip_d_to_r`, or `uncalled` |
| `prior_party`, `prior_incumbent` | From the 2025–26 roster |
| `new_party` | Party of the winner, when called |
| `winner_name` | Only where the source names the winner (SD-36) |
| `result_status`, `as_of` | `unofficial` and the date of the count |
| `note`, `source` | Context and provenance |

## Known gaps and caveats

- **Flips only.** Seats held by the same party are not listed, so this is not a full roster of the incoming legislature. We do not have certified per-seat winners yet.
- **Winners' names are missing** except SD-36. Add them from certified results rather than press accounts.
- **Seven House races were uncalled** (HD-12, 13, 41, 131, 143, 147, 187) on 2026-11-04. Update them as they are called.
- **Chamber totals differ across our own documents.** The election brief says about 108 House Democrats with 7 races uncalled. The transportation prioritization memo says at least 111. Settle this against certified results.
- **HD-12 was vacant** in the 2025–26 roster, so it has no prior incumbent. The brief calls it a Democratic seat.

## License

CC BY 4.0. Please credit Transit Forward Philly and Build Philly Now.
