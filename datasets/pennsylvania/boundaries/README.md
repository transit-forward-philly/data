# Pennsylvania boundaries with demographic and permit facts

**One-line summary:** Pennsylvania House districts, Senate districts, counties and municipalities as GeoJSON, with population, income, housing cost and building permit figures attached to each district and municipality.

## Source

- **Original source:** US Census Bureau TIGER/Line 2024 (state legislative districts, county subdivisions, counties); 2020 Census block populations (TIGER TABBLOCK20); ACS 2023 5-year estimates; Census building permits survey; Census population estimates. Assembled by the [PA Housing Votes](https://github.com/jongeeting/pa-housing-votes) project (`pipeline/scripts/build_districts.py`). The municipality and county files were built 2026-05-18; the House and Senate district files were rebuilt 2026-11-12.
- **Pulled on:** 2026-11-10; House and Senate district files refreshed 2026-11-12
- **Geography:** Pennsylvania, post-2022 legislative maps

## Files

| File | Features | Properties |
|---|---|---|
| `pa_house_districts.geojson` | 203 | `district`, `population`, `landAreaSqMi`, `topMunicipalities`, `topCounties`, `classShares`, `medianIncome`, `medianHomeValue`, `rentBurdenedPct`, `ownerBurdenedPct`, `permitsPer1kPerYear`, `permits5yrTotal`, `popChange2020to2024Pct`, `parentSenateDistricts` |
| `pa_senate_districts.geojson` | 50 | Same, with `nestedHouseDistricts` instead of `parentSenateDistricts` |
| `pa_counties.geojson` | 67 | `geoid`, `name` |
| `pa_municipalities.geojson` | 2,573 | `geoid`, `name`, `classCode`, `countyName`, `population`, `landAreaSqMi`, `populationDensity`, income and housing cost fields, `permitsPer1kPerYear`, `permitsYearsCovered`, `popChange2020to2024Pct`, `nestedHouseDistricts`, `nestedSenateDistricts` |

Coordinates are WGS84 (EPSG:4326).

## Known gaps and caveats

- **Prepared for web maps.** Use the Census TIGER files directly for precise spatial joins such as station-in-district.
- **District population is split by where people live.** Before 2026-11-12, each municipality's population was split among its districts by land area, which was badly wrong inside cities that span several districts: Philadelphia's House districts came out between 18,000 and 168,000 people. Each district's share of a municipality now comes from the 2020 Census block populations inside it. House districts now range from 60,214 to 67,970 people, and Senate districts from about 246,000 to 272,000.
- **Some figures are still apportioned.** Permits and population change are municipal figures split among districts by that same population share. Population change exists only at the municipality level, so every district inside one city shows that city's rate. Income, home value and cost-burden figures are built from census tracts.
- **Mostly built in May 2026.** Rebuild with the upstream script before relying on newer ACS or permit data.

## License

CC BY 4.0. Please credit Transit Forward Philly and the US Census Bureau.
