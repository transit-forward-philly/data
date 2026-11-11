"""Pull DVRPC's FFY2027 Pennsylvania TIP project points and place each in a PA House and Senate district.

Usage (needs geopandas):
    python build.py OUTPUT.csv [TIGER_DIR]

Source layer (public ArcGIS FeatureServer, listed in catalog.dvrpc.org):
    https://arcgis.dvrpc.org/portal/rest/services/transportation/patip_ffy2027_2030_point/FeatureServer/0

TLS note: arcgis.dvrpc.org does not send its intermediate certificate. If you get
"unable to get local issuer certificate", download the intermediate named in the
server certificate's Authority Information Access field, append it to your CA
bundle, and point SSL_CERT_FILE at the combined file. Do not disable verification.

District polygons come from Census TIGER/Line 2024 (see regional_rail_station_districts/build.py).
"""
import csv
import json
import os
import ssl
import sys
import tomllib
import urllib.parse
import urllib.request
from pathlib import Path

import geopandas as gpd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "regional_rail_station_districts"))
from build import PROJ, tiger_districts, records  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "datasets"
LAYER = "https://arcgis.dvrpc.org/portal/rest/services/transportation/patip_ffy2027_2030_point/FeatureServer/0"
FIELDS = ["mpms_id", "prog", "road_name", "descriptio", "cty", "mappingfea", "max_li", "max_t6", "max_comp", "latitude", "longitude"]


def ssl_context():
    """Default verifying context, plus the CA bundle named in SSL_CERT_FILE if set."""
    return ssl.create_default_context(cafile=os.environ.get("SSL_CERT_FILE"))


def get(url, **params):
    with urllib.request.urlopen(f"{url}?{urllib.parse.urlencode(params)}", timeout=90, context=ssl_context()) as r:
        return json.load(r)


def main(out, tiger_dir=None):
    total = get(LAYER + "/query", where="1=1", returnCountOnly="true", f="json")["count"]
    feats, offset = [], 0
    while offset < total:
        page = get(LAYER + "/query", where="1=1", outFields="*", outSR="4326", orderByFields="objectid",
                   resultOffset=offset, resultRecordCount=500, f="json")
        got = page.get("features", [])
        if not got:
            break
        feats += got
        offset += len(got)
    if len(feats) != total:
        sys.exit(f"expected {total} projects, got {len(feats)}")
    rows = [f["attributes"] for f in feats]
    pts = gpd.GeoDataFrame(rows, geometry=gpd.points_from_xy([f["geometry"]["x"] for f in feats], [f["geometry"]["y"] for f in feats]), crs="EPSG:4326").to_crs(PROJ)
    legs = {ch: records(D / f"pennsylvania/legislators-2025-2026/records/{ch}") for ch in ("house", "senate")}
    flips = {ch: records(D / f"pennsylvania/election-2026-flips/records/{ch}") for ch in ("house", "senate")}
    place = {}
    for ch in ("house", "senate"):
        g = tiger_districts(ch, tiger_dir)
        j = gpd.sjoin(pts, g, how="left", predicate="within")
        j = j[~j.index.duplicated(keep="first")]
        place[ch] = [d if isinstance(d, str) else "" for d in j["district"]]
    out_rows = []
    for i, r in enumerate(rows):
        o = {k: r.get(k, "") if r.get(k) is not None else "" for k in FIELDS}
        for ch in ("house", "senate"):
            d = place[ch][i]
            m = legs[ch].get(d)
            fl = flips[ch].get(d)
            o[f"{ch}_district"] = d
            o[f"{ch}_member_2025_26"] = m["full_name"] if m else ""
            o[f"{ch}_party_2025_26"] = m["party"] if m else ""
            o[f"{ch}_seat_2026_status"] = fl["outcome"] if fl else ("" if not d else "no_change_listed")
        out_rows.append(o)
    out_rows.sort(key=lambda o: (o["prog"], str(o["mpms_id"]), o["road_name"]))
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out_rows[0]))
        w.writeheader()
        w.writerows(out_rows)
    print(f"wrote {len(out_rows)} projects to {out}")


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2] if len(sys.argv) == 3 else None)
