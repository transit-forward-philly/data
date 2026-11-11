# SEPTA Key Advantage partners

**One-line summary:** The 70 employers on SEPTA's September 2026 Key Advantage participation list, with member counts, worksite addresses, and Philadelphia council districts.

## Source

- **Original source:** SEPTA, "Key Advantage Participation List – September 2026," released Oct. 27, 2026 in response to a Right-to-Know request. The list has 70 partners and 64,895 members. SEPTA denied the rest of the request (members per employer by trip, trips by mode, and similar) under RTKL §705, saying no such record exists, and §703, saying the request wasn't specific enough.
- **Pulled on:** 2026-10-27 (list); 2026-11-04 (addresses and geocoding)
- **Geography:** Employer worksites in Philadelphia and nearby suburbs
- **Time period covered:** Participation as of September 2026
- **Other sources:** Worksite addresses from web research (each row gives a source URL and a confidence level). Geocoding with the City of Philadelphia's [AIS](https://api.phila.gov/ais/v1/) and, for suburban worksites, the Census geocoder. Jobs by firm size from Census LEHD LODES 2023 (workplace area characteristics).

## Processing

1. SEPTA's list was typed into `key_advantage_partners_sep2026.csv`. The two Swarthmore rows are merged.
2. Each partner was placed at its main worksite by web research (`partner_addresses.csv`).
3. Addresses were geocoded and assigned to 2024 council districts (`pipelines/septa_key_advantage/geocode_partners.py`).
4. Industry and ownership were hand-coded for each partner (`partner_industry.py`, `build_site_data.py`), producing `partners_all.json`.
5. LODES 2023 workplace jobs were summed by council district and firm size (`build_jobs_by_firm_size.py`) for comparison.

## Files

| File | Format | Description |
|---|---|---|
| `key_advantage_partners_sep2026.csv` | CSV | SEPTA's list as released: partner, program, start date, members |
| `partner_addresses.csv` | CSV | Worksite address per partner, with confidence level and source URL |
| `partners_geocoded.csv` | CSV | List joined to addresses, with coordinates and council district |
| `district_summary.csv` | CSV | Employers and members per council district |
| `district_jobs.csv` | CSV | LODES 2023 jobs per council district, all and by firm size |
| `partners_all.json` | JSON | Partner table with display name, sector, size band and district |
| `districts.geojson` | GeoJSON | 2024 council districts with employer and member counts |
| `worksites.geojson` | GeoJSON | One point per located partner |

## Columns

**`key_advantage_partners_sep2026.csv`**

| Column | Type | Units | Description |
|---|---|---|---|
| `partner` | text | | Partner name as SEPTA lists it |
| `program` | text | | SEPTA program code (KAP, KAP3, KAPU). We have not confirmed what the codes stand for |
| `start_date` | date | | Date the partner joined |
| `members` | integer | people | Members enrolled through the partner |

**`partners_geocoded.csv`** has the four columns above plus:

| Column | Type | Units | Description |
|---|---|---|---|
| `resolved_name` | text | | Legal or common name we matched the partner to |
| `address`, `city` | text | | Main worksite |
| `in_philadelphia` | text | | yes, no, or blank/dispersed when there is no single worksite |
| `confidence` | text | | How sure we are of the address: high, medium or low |
| `notes` | text | | How the address was found, and caveats |
| `lng`, `lat` | number | degrees | Worksite coordinates; blank if not located |
| `council_district` | text | | 2024 Philadelphia council district; blank if outside the city or not located |

**`partner_addresses.csv`** has `partner`, `resolved_name`, `address`, `city`, `state`, `zip`, `in_philadelphia`, `confidence`, `source_url` and `notes`.

**`district_summary.csv`:** `council_district` (1–10, "Outside Philadelphia" or "Not located"), `employers`, `members`, `partners` (names, semicolon-separated).

**`district_jobs.csv`:** `district`, `jobs_all`, `jobs_private`, and `private_firm_*` jobs by the size of the whole firm (0-19, 20-49, 50-249, 250-499, 500+). Firm size is for the whole firm nationally, not the worksite, so a chain store counts as 500+.

**`partners_all.json`:** one object per partner with `name`, `septa_label`, `program`, `students` (college student program), `start`, `members`, `size_band` (partner's member count), `sector` (NAICS sector), `district`, `where` (city, suburbs or not located), `address`, `geo_confidence`.

## Known gaps and caveats

- These are employer worksites, not where pass holders live or ride.
- Some partners have staff at many sites. The City (24,450 members) is shown at City Hall, Penn Medicine (26,500) at HUP, and Moravia Health Network (2,148 home-care workers) at its headquarters.
- Six partners could not be placed: "Dywer," Catalyst Group, DYAD, FatBall Therapeutics, HVLAW (no published street address), and the PA House (staff spread across district offices).
- Several addresses are medium or low confidence; check `confidence` and `source_url` before relying on a single row.
- Industry and ownership are our coding, not SEPTA's.

## Rebuilding

Needs the 2024 council district boundaries at `raw/council_districts.geojson` and the LODES 2023 files for Pennsylvania (`pa_wac_S000_JT00_2023.csv.gz`, `pa_wac_S000_JT02_2023.csv.gz`, `pa_xwalk.csv.gz`) from [LEHD](https://lehd.ces.census.gov/data/lodes/LODES8/pa/) in `raw/`. Both are left out of the repo. Then run, in order:

```bash
python3 pipelines/septa_key_advantage/geocode_partners.py
python3 pipelines/septa_key_advantage/build_jobs_by_firm_size.py   # needs geopandas
python3 pipelines/septa_key_advantage/build_site_data.py
```

## License

CC BY 4.0. Please credit Transit Forward Philly and the original source (SEPTA).
