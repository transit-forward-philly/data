# Gitsheets: when we use records instead of CSVs

[Gitsheets](https://github.com/JarvusInnovations/gitsheets) stores each record as a small TOML file in git, validates every write against a schema, and makes every change a commit. We use it for **small, human-reviewed record sets** where a diff is the review tool. We use plain CSV or GeoJSON for large or regenerated tables.

| Use gitsheets | Use CSV / GeoJSON |
|---|---|
| Rosters and officeholders (hundreds of records) | Boundaries, ridership, delay, census and permit tables |
| Election results and flips by seat | Anything a script regenerates from an upstream source |
| Bill concepts, scores and roll-call summaries | Member-by-member vote tables |
| Project cards we expect volunteers to edit | Anything over a few thousand rows |

## How it works here

- Sheet configs live in [`.gitsheets/`](../.gitsheets/). Each names where records live and what a valid record looks like.
- Records live beside their dataset README, under `records/` (or a named folder).
- Read: `npx -y gitsheets query <sheet> --filter chamber=senate --format=csv`
- Write: `npx -y gitsheets upsert <sheet> < records.json` (a JSON array; one commit). Gitsheets commits without touching your working tree, so run `git reset --hard` afterward to see the files.
- Edit one record: `npx -y gitsheets edit <sheet> <path>`

Needs Node 20 or newer. Nothing else to install.
