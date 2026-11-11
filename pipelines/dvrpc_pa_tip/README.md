# DVRPC PA TIP projects

Pulls DVRPC's FFY2027 Pennsylvania TIP project points and places each in a PA House and Senate district.

- **Run:** `python build.py ../../datasets/septa-region/dvrpc-pa-tip-ffy2027/dvrpc-pa-tip-ffy2027.csv [TIGER_DIR]`
- **Needs:** `geopandas`. District polygons come from Census TIGER/Line 2024 (see `regional_rail_station_districts`).
- **Source layer:** `arcgis.dvrpc.org/.../transportation/patip_ffy2027_2030_point/FeatureServer/0`

**TLS trap:** `arcgis.dvrpc.org` does not send its intermediate certificate, so some machines fail with "unable to get local issuer certificate". Fetch the intermediates from the CA addresses in the server certificate's Authority Information Access field (Sectigo), append them to your CA bundle, and set `SSL_CERT_FILE` to it. Do not turn verification off.
