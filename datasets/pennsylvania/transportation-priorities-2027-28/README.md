# Transportation priorities for the 2027–28 session

**One-line summary:** The 20 transportation concepts from the 2027–28 prioritization memo, with their draft scores, tiers, and the 2025–26 bills that currently carry each idea.

## Source

- **Original source:** "Transportation Bill Prioritization for the 2027-28 Session" (Jon Geeting, Build Philly Now, 2026-11-10). Bill numbers, sponsors and stages are secondhand in the memo (LegiScan, BillTrack50, Legilist, FastDemocracy, member releases) and need a final check on palegis.us.
- **Pulled on:** 2026-11-10
- **Time period covered:** priorities for the 2027–28 session; bill numbers are from the 2025–26 session

## Processing

The memo table was typed into one record per concept. Each memo score was recomputed from its components and all 20 match: effectiveness×3 + administrative×2 + governor×2 + cost×2, plus momentum×3. Tier follows the memo rule (45+ is Tier 1, 35–44 Tier 2, below 35 Tier 3, and an administrative score of 0 or 1 caps at Tier 3).

This is a [gitsheet](../../../docs/gitsheets.md): one TOML file per concept in `concepts/`, validated by `.gitsheets/pa-transportation-concepts.toml`.

## Files

| File | Format | Description |
|---|---|---|
| `concepts/*.toml` | TOML | 20 concepts, ranked, with component scores, tier, bills, sponsor, furthest stage |

## Bills and sessions

Every bill number in a concept is a **2025–26** session number, marked by `bills_session`. That session ends on 2026-11-30, so those numbers will not carry over: bills must be re-introduced in January 2027 with new numbers. Votes on these bills are in [`transportation-votes-2025-26`](../transportation-votes-2025-26/).

Concepts with no bill number have no bill on record. Earlier-session items the memo cites (HB 291's predecessor, SB 121 of 2023, HB 1307 and HB 902, Act 38 of 2023, Act 101 of 2016) are mentioned in each concept's `notes` or `furthest_stage` text and are not separate records.

## Known gaps and caveats

- **Scores are draft.** The memo says so; `scores_status` stays `draft` until calibrated.
- **Momentum labels are loose.** "Medium" stands for a momentum score of 2 in some rows and 3 in others, so `momentum_score_implied` is derived from the memo's own totals.
- **Sponsors and cosponsor counts are incomplete.** The memo marks many sponsors "confirm" and gives cosponsor counts only for HB 2635.
- **HB 1364 is the trust fund transfer bill**, confirmed from palegis roll call 416. The memo's "confirm number" is resolved.

## License

CC BY 4.0. Please credit Transit Forward Philly and Build Philly Now.
