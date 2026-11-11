# SEPTA Regional Rail stations

Pulls SEPTA's public Regional Rail Stations layer (ArcGIS FeatureServer) into
`datasets/septa-region/septa-regional-rail-stations/`.

- **Run:** `python fetch.py ../../datasets/septa-region/septa-regional-rail-stations/septa-regional-rail-stations.csv`
  Standard library only. It checks the row count against the server's own count
  and sorts rows so reruns diff cleanly.
- **Source layer:** `services2.arcgis.com/9U43PSoL47wawX5S/.../Regional_Rail_Stations/FeatureServer/0`
