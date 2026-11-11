# 2026 PA general election results (legislature)

**One-line summary:** Unofficial winners of all 228 Pennsylvania legislative races on the Nov 3, 2026 ballot (203 House, 25 Senate), with each seat's 2025–26 incumbent and whether the seat held or flipped.

> **Unofficial.** These are MultiState's results as of 2026-11-10, not certified returns. Three House races were still being counted. Replace `result_status = "unofficial"` seat by seat once the Department of State certifies.

## Source

- **Original source:** MultiState, [Pennsylvania 2026 Election Results](https://www.multistate.us/elections/results/pennsylvania-2026), which cites Inquirer, WHYY and Spotlight PA reporting
- **Pulled on:** 2026-11-10
- **Geography:** Pennsylvania House (203 seats) and Senate (the 25 odd-numbered seats were up)
- **Time period covered:** 2026 general election

## Processing

Parsed from the page's legislative results table into one record per race, and joined to [`legislators-2025-2026`](../legislators-2025-2026/) for the prior incumbent and party. `outcome` is derived by comparing the winner's party with the prior incumbent's party. This is a [gitsheet](../../../docs/gitsheets.md): one record per seat in `records/<chamber>/<district>.toml`, validated by `.gitsheets/pa-election-2026-results.toml`.

## Files

| File | Format | Description |
|---|---|---|
| `records/house/*.toml`, `records/senate/*.toml` | TOML | 228 records: 203 House, 25 Senate |

## Fields

| Field | Description |
|---|---|
| `chamber`, `district` | Seat |
| `winner`, `winner_party` | As MultiState gives them; absent where the count is unfinished |
| `prior_incumbent`, `prior_party` | 2025–26 holder of the seat |
| `outcome` | `hold`, `flip_r_to_d`, `flip_d_to_r`, or `uncounted` |
| `incumbent_defeated` | `true` where MultiState notes the incumbent lost |
| `unopposed`, `other_candidates` | Whether there was no opponent, or who else ran |
| `result_status`, `as_of`, `source`, `note` | Status, date, provenance and context |

## What it shows

| | Democratic | Republican | Not yet called |
|---|---|---|---|
| House (203 seats) | 111 | 89 | 3 (HD-41, 143, 147) |
| Senate, of the 25 seats up | 16 | 9 | 0 |

- **15 seats changed party, and 14 incumbents lost,** matching MultiState's own summary. Thirteen flipped R to D: House HD-13, 18, 44, 88 (open seat), 131, 137, 142, 160 and 187, and Senate SD-6, 16, 24 and 40. Two flipped D to R: HD-12 (Scott Timko over Brandon Dukes) and SD-36 (Tom Jones over James Malone).
- **The House goes from 103-100 to 111-89** with three races uncounted. The Senate goes from 27-23 Republican to 26-24 Democratic, counting the 10 Democratic seats not on the ballot.
- **63 races were unopposed,** about three in four of them Democratic, per MultiState.

## Known gaps and caveats

- **Unofficial and incomplete.** HD-143 and HD-147 were narrowly trailing for the Republican incumbents and HD-41's Republican incumbent trailed by a few dozen votes, per MultiState. Do not publish seat totals as final.
- **Senate seats not on the ballot** have no record here. Their holders are in the 2025–26 roster.
- **Names are as MultiState writes them** (for example, "Bryan F Allen Jr"), and may differ from palegis.us.
- **HD-12 flipped back** in a rematch of the August 2026 special election that Dukes won by fewer than 100 votes. Dukes is in the 2025–26 roster as of 2026-10-05.
- **This replaces the earlier flips-only dataset.** That one, from the Nov 4 morning brief, had 6 House flips and 7 uncalled races; counting has since resolved four of the seven as flips (HD-12, 13, 131, 187).
- **Our two internal documents:** the Nov 4 election brief's "about 108 House Democrats" was a morning-after projection; the 111 in the transportation prioritization memo matches these results.

## License

CC BY 4.0. Please credit Transit Forward Philly and MultiState.
