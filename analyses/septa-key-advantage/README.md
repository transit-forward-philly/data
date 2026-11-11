# Who is in SEPTA Key Advantage?

## Question

Which employers participate in SEPTA's Key Advantage employer pass program, where are they, and how well does the list match where Philadelphia's jobs are?

## Data

[SEPTA Key Advantage partners](../../datasets/philadelphia/septa-key-advantage/) (SEPTA's September 2026 participation list, with worksite addresses and council districts). Jobs by industry and firm size come from Census LEHD LODES 2023.

## Method

Each partner was placed at its main worksite and assigned to a 2024 council district. Partners were hand-coded by industry (NAICS sector) and ownership (business, nonprofit, public). Partner industries were compared with Philadelphia's job shares by industry. See the pipelines in [`pipelines/septa_key_advantage/`](../../pipelines/septa_key_advantage/); `analyze_long_tail.py` produces `long_tail_summary.csv`.

## Findings

**By council district** (employers / members):

| District | Employers | Members |
|---|---|---|
| D1 | 17 | 1,913 |
| D2 | 10 | 3,109 |
| D3 | 9 | 27,204 |
| D4 | 1 | 33 |
| D5 | 21 | 26,609 |
| D8 | 1 | 5 |
| D6, D7, D9, D10 | 0 | 0 |
| Outside Philadelphia | 5 | 5,663 |
| Not located | 6 | 359 |

Four employers hold 91% of employer members: Penn Medicine, the City of Philadelphia, Moravia Health Network and Delaware County. The rest of the program is a long tail of small, mostly Center City employers, and it is thin in industries such as finance, transportation, construction and retail. See [LONG_TAIL_FINDINGS.md](LONG_TAIL_FINDINGS.md) for ownership, industry, size and timing breakdowns and [long_tail_summary.csv](long_tail_summary.csv) for the industry table.

## Known limitations

- Worksites are not residences or trips; they say where employers are, not where pass holders live or ride.
- Large employers with many sites are shown at one address.
- Industry and ownership coding is ours, and ownership for 9 partners is inferred from what they do. Member counts are not employee counts, and a comparison with job shares shows representation, not demand.
- Six partners are not located. SEPTA declined to release members per employer by trip or mode.
