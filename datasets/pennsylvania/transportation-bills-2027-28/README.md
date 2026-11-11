# Transportation bills for the 2027–28 session

**One-line summary:** The 20 transportation concepts in the 2027–28 prioritization memo, with their draft scores and bill references, plus the House and Senate floor votes we have on the transit funding bills.

## Source

- **Concepts and scores:** "Transportation Bill Prioritization for the 2027-28 Session" (Jon Geeting, Build Philly Now, 2026-11-10). Bill numbers, sponsors and stages are secondhand there (LegiScan, BillTrack50, Legilist, FastDemocracy, member releases) and need a final check on palegis.us.
- **Votes:** the transit votes dataset behind [vote-transit.netlify.app](https://vote-transit.netlify.app) (`/data/data.json`, as of 2026-10-05) for HB 1788, HB 257 and SB 160; palegis.us roll calls fetched with the PA Housing Votes pipeline on 2026-11-10 for HB 291 (House roll call 13 and Appropriations vote 40) and HB 1364 (House roll call 416 and Appropriations vote 751).
- **Pulled on:** 2026-11-10

## Processing

The memo table was typed into one record per concept. Each memo score was recomputed from its components and all 20 match: effectiveness×3 + administrative×2 + governor×2 + cost×2, plus momentum×3. Tier follows the memo rule (45+ is Tier 1, 35–44 Tier 2, below 35 Tier 3, and an administrative score of 0 or 1 caps at Tier 3).

Concepts and roll calls are [gitsheets](../../../docs/gitsheets.md) (`.gitsheets/pa-transportation-concepts.toml` and `pa-roll-calls.toml`). Member-by-member votes are a CSV.

## Which session is which

The concepts are **2027–28 priorities**. Every bill number and vote in this dataset is from the **2025–26 session**, which ends Nov 30, 2026, so those numbers will not carry over. Bills must be re-introduced in January 2027 with new numbers. Each roll call and member vote carries a `session` field, and each concept with bills has `bills_session`.

**2025–26 session, in this dataset**

| Bill | What | Votes included |
|---|---|---|
| HB 1364 | Public Transportation Trust Fund Transfer Act | House final passage 107-96 (June 17, 2025); Appropriations 22-15 (June 16, 2025) |
| HB 1788 | Transit and roads funding package | House final passage 108-95 (Aug 11, 2025) |
| HB 257 | Senate transit funding amendments | Senate: tabling of the Saval amendment and final passage, both 27-22 (Aug 12, 2025) |
| SB 160 | General Appropriation Act of 2025 | Senate final passage 27-22 (Aug 12, 2025) |
| HB 291 | Parking-protected bike lanes | House final passage 183-19 (Feb 3, 2025); Appropriations 37-0 (Feb 3, 2025) |

**2025–26 session bills named in the memo with no floor vote:** HB 2635, SB 509, HB 1955, HB 1146, SB 796, SB 1072, HB 1085, HB 2129, SB 910. All are in committee.

**Earlier sessions, cited by the memo but not in this dataset:** the House passing HB 291's predecessor 198-5 ("last session", 2023–24), the Senate passing SB 121 on State Police funding 28-21 in 2023, prior-session local-option tax bills HB 1307 and HB 902, Act 38 of 2023 (HB 1284) on speed cameras, and the red light sunset in Act 101 of 2016 (HB 950 of 2015). The memo says the House has passed a transit funding bill five times; we have two of those votes (HB 1364 and HB 1788), and the memo does not say which sessions the other three were in.

## Files

| File | Format | Description |
|---|---|---|
| `concepts/*.toml` | TOML | 20 concepts, ranked, with component scores, tier, bills, sponsor, furthest stage |
| `roll-calls/*.toml` | TOML | 8 roll calls: HB 1788 final passage; HB 257 Saval amendment tabling and final passage; SB 160 final passage; HB 291 and HB 1364 House final passage and House Appropriations re-report |
| `member-votes.csv` | CSV | 832 member votes, one row per member per roll call |

## Known gaps and caveats

- **Scores are draft.** The memo says so; `scores_status` stays `draft` until calibrated.
- **Momentum labels are loose.** "Medium" stands for a momentum score of 2 in some rows and 3 in others, so `momentum_score_implied` is derived from the memo's own totals.
- **Most bills have no floor vote.** HB 2635, SB 509, HB 1146, SB 796, SB 1072, HB 1085, HB 2129 and SB 910 are in committee. - **HB 1364 is the trust fund transfer bill.** The memo's "confirm number" is resolved: HB 1364 (PN 1912), "Public Transportation Trust Fund transfers and increases," passed the House 107-96 on June 17, 2025 after the Appropriations Committee reported it 22-15 on June 16.
- **Two committee members have no district or party.** Joshua Siegel and Torren Ecker voted in the HB 291 Appropriations vote but are not in the May 2026 roster, so those fields are blank for them in `member-votes.csv`. Siegel left the House to become Lehigh County Executive. We have not confirmed why Ecker is missing.
- **Every 2025–26 bill dies on 2026-11-30.** Bill numbers here are placeholders until re-introduction in January.
- **Cosponsor counts** are in the memo only for HB 2635 and are not in this dataset yet.

## License

CC BY 4.0. Please credit Transit Forward Philly and Build Philly Now.
