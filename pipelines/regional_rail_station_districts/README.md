# Regional Rail stations to districts

Places each Regional Rail station in a Pennsylvania House and Senate district, county and municipality by point-in-polygon, then attaches the 2025–26 member and the 2026 election status of each seat.

- **Run:** `python build.py ../../datasets/septa-region/regional-rail-station-districts/regional-rail-station-districts.csv [TIGER_DIR]`
- **Needs:** `geopandas`. Polygons come from Census TIGER/Line 2024 (`tl_2024_42_sldl.zip` and `tl_2024_42_sldu.zip` for the post-2022 districts, `tl_2024_us_county.zip` and `tl_2024_42_cousub.zip`). They are read from `TIGER_DIR` if present, otherwise downloaded from census.gov.
- **Also reads:** the stations, 2025–26 legislators and 2026 election results datasets in this repo.
