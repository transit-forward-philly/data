# Transportation votes

**One-line summary:** House and Senate floor and committee roll calls on the transit funding and bike lane bills in the 2027–28 prioritization memo, with every member's vote. Nearly all are from the 2025–26 session; SB 121's votes are from 2023–24. Each record carries a `session` field.

## Source

- **HB 1788, HB 257, SB 160:** the transit votes dataset behind [vote-transit.netlify.app](https://vote-transit.netlify.app) (`/data/data.json`, as of 2026-10-05), which cites palegis.us roll calls.
- **Everything else:** palegis.us roll calls fetched with the PA Housing Votes pipeline on 2026-11-10. The roll call numbers came from the [bill info scan](../transportation-priorities-2027-28/bill-info/) of each bill's palegis page.
- **Pulled on:** 2026-11-10

## Processing

Roll call summaries are [gitsheets](../../../docs/gitsheets.md) (`.gitsheets/pa-roll-calls.toml`), one record per vote. Member-by-member votes are a CSV. District and party come from the House and Senate rosters; see the caveats.

## Files

| File | Format | Description |
|---|---|---|
| `roll-calls/*.toml` | TOML | 21 roll calls, each with a `session` field |
| `member-votes.csv` | CSV | 1,193 member votes, one row per member per roll call |

## Which votes are included

**2025–26 session**

| Bill | What | Votes |
|---|---|---|
| HB 1364 | Public Transportation Trust Fund Transfer Act | House final passage 107-96 (June 17, 2025); Appropriations 22-15 (June 16, 2025); House Transportation 16-10 (May 5, 2025) |
| HB 1788 | Transit and roads funding package | House final passage 108-95 (Aug 11, 2025); House Transportation 16-10 (Aug 6); Rules 19-14 and Appropriations 22-15 (Aug 10) |
| HB 257 | Senate transit funding amendments | Senate: tabling of the Saval amendment and final passage, both 27-22 (Aug 12, 2025) |
| SB 160 | General Appropriation Act of 2025 | Senate final passage 27-22 (Aug 12, 2025) |
| HB 291 | Parking-protected bike lanes | House final passage 183-19 (Feb 3, 2025); House Transportation 26-0 (Jan 27); Appropriations 37-0 (Feb 3) |
| SB 509 | Local police radar | Senate final passage 49-1 (Oct 20, 2026); Appropriations 22-0 (Oct 19); Transportation 14-0 on the amendment and 14-0 reported as amended (Oct 6) |
| HB 1085 | State Police off the Motor License Fund | House Transportation 26-0 (Apr 7, 2025); no floor vote |

**2023–24 session**

| Bill | What | Votes |
|---|---|---|
| SB 121 | Capping transfers from the Motor License Fund to State Police | Senate final passage 28-21 (Feb 28, 2023); Appropriations 15-9 (Feb 28); Transportation 9-5 (Jan 9) |

**No floor vote in 2025–26:** HB 2635, HB 1955, HB 1146, SB 796, SB 1072, HB 2129, SB 910 (all in committee), and HB 1085 (committee vote only). SB 509 passed the Senate and is in House Transportation.

**Earlier sessions, cited by the memo but not included:** HB 291's predecessor passing the House 198-5 ("last session", 2023–24), and the other House passages of transit funding (the memo says five in all; we have two, and it does not say which sessions the rest were in).

## Known gaps and caveats

- **SB 121's 2023 Senate roll has 49 votes.** Sen. Judy Ward has no recorded vote on that roll call, so she has no row. Her absence is recorded by palegis as missing.
- **Some committee members have no district or party** (13 rows), because the fetcher looks members up in the 2025–26 rosters. This affects Siegel and Ecker and former members on the 2023 and early 2025 committee votes.
- **Every 2025–26 bill dies on 2026-11-30.** These numbers will not carry over to 2027–28.
- **Two committee members have no district or party.** Joshua Siegel and Torren Ecker voted in the Appropriations votes but are not in the May 2026 roster, so those fields are blank for them. Siegel left the House to become Lehigh County Executive. Ecker resigned in December 2025 after being elected a judge on the Adams County Court of Common Pleas, per press reports, not yet confirmed on palegis.
- **HB 291's floor vote has 202 members**, one fewer than a full House; the reason is not confirmed.

## License

CC BY 4.0. Please credit Transit Forward Philly and the PA General Assembly.
