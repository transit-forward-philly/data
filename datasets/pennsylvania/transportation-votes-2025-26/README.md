# Transportation votes, 2025–26 session

**One-line summary:** House and Senate floor and committee roll calls on the transit funding and bike lane bills in the 2027–28 prioritization memo, with every member's vote. All votes are from the 2025–26 session.

## Source

- **HB 1788, HB 257, SB 160:** the transit votes dataset behind [vote-transit.netlify.app](https://vote-transit.netlify.app) (`/data/data.json`, as of 2026-10-05), which cites palegis.us roll calls.
- **HB 291 and HB 1364:** palegis.us roll calls fetched with the PA Housing Votes pipeline on 2026-11-10 (HB 291: House roll call 13 and Appropriations vote 40; HB 1364: House roll call 416 and Appropriations vote 751).
- **Pulled on:** 2026-11-10

## Processing

Roll call summaries are [gitsheets](../../../docs/gitsheets.md) (`.gitsheets/pa-roll-calls.toml`), one record per vote. Member-by-member votes are a CSV. District and party come from the House and Senate rosters; see the caveats.

## Files

| File | Format | Description |
|---|---|---|
| `roll-calls/*.toml` | TOML | 8 roll calls, each with a `session` field |
| `member-votes.csv` | CSV | 832 member votes, one row per member per roll call |

## Which votes are included

| Bill | What | Votes |
|---|---|---|
| HB 1364 | Public Transportation Trust Fund Transfer Act | House final passage 107-96 (June 17, 2025); Appropriations 22-15 (June 16, 2025) |
| HB 1788 | Transit and roads funding package | House final passage 108-95 (Aug 11, 2025) |
| HB 257 | Senate transit funding amendments | Senate: tabling of the Saval amendment and final passage, both 27-22 (Aug 12, 2025) |
| SB 160 | General Appropriation Act of 2025 | Senate final passage 27-22 (Aug 12, 2025) |
| HB 291 | Parking-protected bike lanes | House final passage 183-19 (Feb 3, 2025); Appropriations 37-0 (Feb 3, 2025) |

**No floor vote in 2025–26:** HB 2635, SB 509, HB 1955, HB 1146, SB 796, SB 1072, HB 1085, HB 2129, SB 910. All are in committee.

**Earlier sessions, cited by the memo but not included:** HB 291's predecessor passing the House 198-5 ("last session", 2023–24), SB 121 passing the Senate 28-21 in 2023, and the other House passages of transit funding (the memo says five in all; we have two, and it does not say which sessions the rest were in).

## Known gaps and caveats

- **Every 2025–26 bill dies on 2026-11-30.** These numbers will not carry over to 2027–28.
- **Two committee members have no district or party.** Joshua Siegel and Torren Ecker voted in the Appropriations votes but are not in the May 2026 roster, so those fields are blank for them. Siegel left the House to become Lehigh County Executive. Ecker resigned in December 2025 after being elected a judge on the Adams County Court of Common Pleas, per press reports, not yet confirmed on palegis.
- **HB 291's floor vote has 202 members**, one fewer than a full House; the reason is not confirmed.

## License

CC BY 4.0. Please credit Transit Forward Philly and the PA General Assembly.
