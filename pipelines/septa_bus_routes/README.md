# SEPTA bus routes

Lists every SEPTA bus and trackless trolley route with how often it runs on a weekday, Saturday and Sunday, SEPTA's weekday frequent marking, and the House, Senate and Council districts it runs through, plus a GeoJSON of the route lines. Output: [`datasets/septa-region/septa-bus-routes/`](../../datasets/septa-region/septa-bus-routes/).

- **Run:** `python build.py ../../datasets/septa-region/septa-bus-routes [CACHE_DIR]`
- **Needs:** `geopandas`. Downloads SEPTA GTFS release `v202611010` from GitHub, Philadelphia's 2024 Council districts from the City's ArcGIS layer, and Census TIGER/Line 2024 House and Senate polygons. Files are reused from `CACHE_DIR` if present, otherwise downloaded into it (or into a temporary folder). It shares that cache with `septa_accelerate_stations`, whose `build.py` it imports for the downloads and district joins.
- **Produces:** `septa-bus-routes.csv` (one row per route) and `septa-bus-routes.geojson` (one feature per route).
- **Hand-entered rules:** the three measured days, the 7:00 to 19:00 window, the Frequent Red color and the Metro and trolley routes left out are constants at the top of `build.py`. The `service_kind` rules (school, overnight, rail replacement) are in `service_kind()`. Change the days and `GTFS_TAG` in `septa_accelerate_stations/build.py` together when moving to a newer schedule.
