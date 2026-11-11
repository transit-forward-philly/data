# Transportation bills for the 2027–28 session

**One-line summary:** The 20 transportation concepts in the 2027–28 prioritization memo, with their draft scores and bill references, plus the House and Senate floor votes we have on the transit funding bills.

## Source

- **Concepts and scores:** "Transportation Bill Prioritization for the 2027-28 Session" (Jon Geeting, Build Philly Now, 2026-11-10). Bill numbers, sponsors and stages are secondhand there (LegiScan, BillTrack50, Legilist, FastDemocracy, member releases) and need a final check on palegis.us.
- **Votes:** the transit votes dataset behind [vote-transit.netlify.app](https://vote-transit.netlify.app) (`/data/data.json`, as of 2026-10-05), which cites palegis.us roll calls.
- **Pulled on:** 2026-11-10

## Processing

The memo table was typed into one record per concept. Each memo score was recomputed from its components and all 20 match: effectiveness×3 + administrative×2 + governor×2 + cost×2, plus momentum×3. Tier follows the memo rule (45+ is Tier 1, 35–44 Tier 2, below 35 Tier 3, and an administrative score of 0 or 1 caps at Tier 3).

Concepts and roll calls are [gitsheets](../../../docs/gitsheets.md) (`.gitsheets/pa-transportation-concepts.toml` and `pa-roll-calls.toml`). Member-by-member votes are a CSV.

## Files

| File | Format | Description |
|---|---|---|
| `concepts/*.toml` | TOML | 20 concepts, ranked, with component scores, tier, bills, sponsor, furthest stage |
| `roll-calls/*.toml` | TOML | 4 roll calls: HB 1788 final passage; HB 257 Saval amendment tabling and final passage; SB 160 final passage |
| `member-votes.csv` | CSV | 353 member votes, one row per member per roll call |

## Known gaps and caveats

- **Scores are draft.** The memo says so; `scores_status` stays `draft` until calibrated.
- **Momentum labels are loose.** "Medium" stands for a momentum score of 2 in some rows and 3 in others, so `momentum_score_implied` is derived from the memo's own totals.
- **Most bills have no floor vote.** HB 2635, SB 509, HB 1146, SB 796, SB 1072, HB 1085, HB 2129 and SB 910 are in committee. Still to add: the HB 291 House vote (183-19, 2025-02-03) and the June 17, 2025 House vote on the trust fund transfer bill, whose number the memo says to confirm (HB 1364).
- **Every 2025–26 bill dies on 2026-11-30.** Bill numbers here are placeholders until re-introduction in January.
- **Cosponsor counts** are in the memo only for HB 2635 and are not in this dataset yet.

## License

CC BY 4.0. Please credit Transit Forward Philly and Build Philly Now.
