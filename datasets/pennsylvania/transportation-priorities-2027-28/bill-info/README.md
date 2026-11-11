# Palegis bill info for the transportation memo bills

**One-line summary:** Prime sponsor, cosponsors, last action and roll call links for the 14 bills in the 2027–28 transportation memo, plus SB 121 from 2023, scanned from palegis.us.

## Source

- **Original source:** palegis.us bill pages (public), fetched with [`pipelines/pa_bill_info/fetch.py`](../../../../pipelines/pa_bill_info/README.md)
- **Pulled on:** 2026-11-10
- **Time period covered:** the 2025–26 session, plus SB 121 (2023–24)

## Files

| File | Format | Description |
|---|---|---|
| `bill-info.csv` | CSV | One row per bill: title, short name, prime sponsor with party and district, cosponsor counts by party, last action, whether it passed a chamber, printer's number |
| `cosponsors.csv` | CSV | One row per cosponsor per bill, with party, chamber and district |
| `roll-calls.csv` | CSV | Every roll call link on each bill page: floor and committee, with the numbers `fetch_rollcall.py` needs |
| `raw/*.html` | HTML | The pages as fetched |

## What the scan changed in the memo's picture

- **SB 509 (local police radar) passed the Senate 49-1 on Oct 20, 2026** and was referred to House Transportation on Oct 29. The memo has it "in Senate Transportation since Mar 26, 2025".
- **HB 2635 cosponsors:** palegis lists 10 (9 D, 1 R); the memo says 9 D and 5 R.
- **Sponsors the memo marked "confirm":** HB 1788 is Sean Dougherty (D-172); HB 1146 is Joseph Hohenstein (D-177); HB 1085 is Ed Neilson (D-174); SB 910 is Art Haywood (D-4); SB 796 is Lindsey Williams (D-38); SB 1072 is Wayne Fontana (D-42).
- **HB 291:** prime sponsor is Mary Jo Daley (D-148), with David Maloney (R-130) as a cosponsor; 29 cosponsors.

The verified facts are also recorded in each concept's `notes`, with `palegis_checked`.

## Known gaps and caveats

- **A snapshot.** Bills change daily. Rerun the scanner before citing.
- **Cosponsors are as palegis lists them now,** including any added after introduction.
- **Roll call labels that are vote counts** (for example "26 0") are the page's yea and nay tallies.
- **Not every roll call is in the votes dataset yet.** Run `pipelines/pa_bill_info/fetch-rollcalls.sh` to fetch the ones found here.

## License

CC BY 4.0. Please credit Transit Forward Philly and the PA General Assembly.
