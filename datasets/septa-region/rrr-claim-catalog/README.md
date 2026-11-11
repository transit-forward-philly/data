# Reimagining Regional Rail claim catalog

**One-line summary:** Factual claims made in a 2020 5th Square webinar on regional rail, each with a status showing whether we have confirmed, corroborated or still need to check it.

## Source

- **Original source:** Transit Forward Philly's "Reimagining Regional Rail Research Roadmap" (2026-09-21), which catalogs claims from the 5th Square webinar "Transforming Regional Rail in the Philadelphia Metro" (2020, 105 minutes). Checks cite SEPTA's station layer and fare page, the 2021 Philadelphia Transit Plan, and phillytru.org's board tracker.
- **Pulled on:** 2026-11-10
- **Status as of:** 2026-09-21 (the roadmap's date); not rechecked since.

## Processing

Typed from the roadmap's claim table into one record per claim. This is a [gitsheet](../../../docs/gitsheets.md): one TOML file per claim in `records/<number>.toml`, validated by `.gitsheets/rrr-claims.toml`. Volunteers can update a claim's status by pull request, and the history shows who changed what.

## Files

| File | Format | Description |
|---|---|---|
| `records/*.toml` | TOML | 16 claims |

## Fields

| Field | Description |
|---|---|
| `claim_number` | Number in the full 21-claim catalog |
| `claim`, `speaker` | The claim and who made it (surname as the roadmap gives it) |
| `status` | `confirmed`, `corroborated`, `complicated`, `to_check`, or `source_unrecoverable` |
| `evidence`, `next_check` | What the check found, and what is still to do |
| `as_of` | Date of the status |

## Known gaps and caveats

- **Only 16 of the 21 claims are here.** The roadmap's table lists claims 1–5, 10–12 and 14–21. Claims 6–9 and 13 were cataloged but are not in the roadmap document, so they are missing. Add them from the original catalog.
- **Statuses are three months old** and are not rechecked. Claim 14 (MBTA's 2026 target) and claim 18 (fare prices) are the most time-sensitive.
- The roadmap's open question about whether the Reimagining Regional Rail report names the Airport Line or the Manayunk/Norristown Line is not a claim from the webinar and is not tracked here.

## License

CC BY 4.0. Please credit Transit Forward Philly and 5th Square.
