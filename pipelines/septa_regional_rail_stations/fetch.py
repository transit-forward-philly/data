"""Pull SEPTA's public Regional Rail Stations layer into a CSV.

Usage: python fetch.py OUTPUT.csv

Standard library only. Pages through the ArcGIS FeatureServer, drops the
internal ID columns, and writes one row per station sorted by line then
station name so reruns diff cleanly.
"""
import csv
import json
import sys
import urllib.parse
import urllib.request

LAYER = ("https://services2.arcgis.com/9U43PSoL47wawX5S/arcgis/rest/services/"
         "Regional_Rail_Stations/FeatureServer/0")
DROP = {"OBJECTID", "GlobalID"}
PAGE = 500


def get(url, **params):
    q = urllib.parse.urlencode(params)
    with urllib.request.urlopen(f"{url}?{q}", timeout=60) as r:
        return json.load(r)


def main(out):
    meta = get(LAYER, f="json")
    fields = [f["name"] for f in meta["fields"] if f["name"] not in DROP]
    total = get(LAYER + "/query", where="1=1", returnCountOnly="true", f="json")["count"]
    rows, offset = [], 0
    while offset < total:
        page = get(LAYER + "/query", where="1=1", outFields="*", returnGeometry="false",
                   orderByFields="OBJECTID", resultOffset=offset, resultRecordCount=PAGE, f="json")
        feats = page.get("features", [])
        if not feats:
            break
        rows += [f["attributes"] for f in feats]
        offset += len(feats)
    if len(rows) != total:
        sys.exit(f"expected {total} stations, got {len(rows)}")
    rows.sort(key=lambda r: ((r.get("Line_Name") or ""), (r.get("Station_Name") or "")))
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} stations, {len(fields)} columns to {out}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
