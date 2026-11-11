# Regional Rail stations to districts

Places each Regional Rail station in a Pennsylvania House and Senate district by point-in-polygon, then attaches the 2025–26 member and the 2026 election status of each seat.

- **Run:** `python build.py ../../datasets/septa-region/regional-rail-station-districts/regional-rail-station-districts.csv [TIGER_DIR]`
- **Needs:** `geopandas`. District polygons come from Census TIGER/Line 2024 (`tl_2024_42_sldl.zip`, `tl_2024_42_sldu.zip`, the post-2022 maps). They are read from `TIGER_DIR` if present, otherwise downloaded from census.gov.
- **Also reads:** the stations, 2025–26 legislators and 2026 election flips datasets in this repo.
