"""Check the computed station districts against the Census Bureau's address geocoder.

Usage: python check_with_census_geocoder.py OUTPUT.csv

For each Pennsylvania station row, sends SEPTA's street address to the Census geocoder
(public, no key) and compares the State House and Senate districts it returns with the
ones in regional-rail-station-districts.csv. An independent check: the geocoder uses the
address, the join uses SEPTA's coordinates. About 0.2 s per request. Standard library only.
"""
import csv
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "datasets" / "septa-region"
API = "https://geocoding.geo.census.gov/geocoder/geographies/address?"
LOWER, UPPER = "2026 State Legislative Districts - Lower", "2026 State Legislative Districts - Upper"


def main(out):
    stations = list(csv.DictReader(open(D / "septa-regional-rail-stations/septa-regional-rail-stations.csv")))
    ours = {(r["line"], r["station"]): r for r in csv.DictReader(open(D / "regional-rail-station-districts/regional-rail-station-districts.csv"))}
    rows = []
    for s in stations:
        m = ours[(s["Line_Name"], s["Station_Name"])]
        if not m["house_district"]:
            continue  # outside Pennsylvania
        q = urllib.parse.urlencode({"street": s["Street_Address"], "city": s["City"], "state": "PA", "zip": s["Zip"],
                                    "benchmark": "Public_AR_Current", "vintage": "Current_Current", "layers": "all", "format": "json"})
        r = {"line": s["Line_Name"], "station": s["Station_Name"], "address": f"{s['Street_Address']}, {s['City']} {s['Zip']}",
             "our_house": m["house_district"], "our_senate": m["senate_district"], "near_house_edge": m["house_near_boundary"],
             "matched_address": "", "census_house": "", "census_senate": "", "result": "unmatched"}
        try:
            matches = json.load(urllib.request.urlopen(API + q, timeout=30))["result"]["addressMatches"]
            if matches:
                g = matches[0]["geographies"]
                r["matched_address"] = matches[0]["matchedAddress"]
                r["census_house"] = g[LOWER][0]["BASENAME"] if LOWER in g else ""
                r["census_senate"] = g[UPPER][0]["BASENAME"] if UPPER in g else ""
                r["result"] = "agree" if (r["census_house"], r["census_senate"]) == (r["our_house"], r["our_senate"]) else "differs"
        except Exception as e:
            r["result"] = f"error: {str(e)[:50]}"
        rows.append(r)
        time.sleep(0.2)
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} rows to {out}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
