# PA legislators, 2025–26 session

**One-line summary:** Who held each Pennsylvania House and Senate seat during the 2025–26 session, kept as a fixed snapshot so we can still say who represented a station or project during this session after the November 2026 election changes the roster.

## Source

- **Original source:** Pennsylvania General Assembly member directories ([House](https://www.palegis.us/house/members), [Senate](https://www.palegis.us/senate/members)), as collected for the [PA Housing Votes](https://github.com/jongeeting/pa-housing-votes) project
- **Captured on:** House 2026-05-06 (from the floor roll call on HB 2186, when every sitting member voted); Senate 2026-05-10 (member directory scrape)
- **Geography:** Pennsylvania, 203 House and 50 Senate districts (post-2022 maps)
- **Time period covered:** 2025–26 legislative session

## Processing

Converted from the PA Housing Votes member files (`src/data/members/pa-house-2025.ts` and `pa-senate-2025.ts`, last updated 2026-05-11) into one CSV, sorted by chamber and district. No members were added, removed or edited.

## Files

| File | Format | Description |
|---|---|---|
| `pa-legislators-2025-2026.csv` | CSV | One row per member: 201 House, 50 Senate |

## Columns

| Column | Type | Description |
|---|---|---|
| `chamber` | text | `House` or `Senate` |
| `district` | integer | District number |
| `full_name`, `last_name` | text | As palegis.us lists them |
| `party` | text | `D` or `R` |
| `status` | text | `current` as of the capture date |
| `term_end`, `term_end_note`, `email` | text | Optional, mostly empty |
| `palegis_bio_url` | text | Member's page on palegis.us |

## Known gaps and caveats

- **Two House seats are missing.** Districts 12 and 196 were vacant when the roster was captured, so the House has 201 rows.
- **Snapshot, not a history.** Anyone who left or joined after May 2026 is not reflected. Check the Senate in particular, which was captured four days after the House.
- **Not the incoming legislature.** Members elected on 2026-11-03 take office after this session ends and are not in this file.

## License

CC BY 4.0. Please credit Transit Forward Philly and the PA General Assembly.
