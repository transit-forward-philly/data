"""Geocode SEPTA Key Advantage partner worksites to Philadelphia council districts (2024 lines) via AIS.

Usage (from repo root):
    python3 pipelines/septa_key_advantage/geocode_partners.py

Reads key_advantage_partners_sep2026.csv + partner_addresses.csv, writes partners_geocoded.csv,
district_summary.csv, and maps/data/{districts,worksites}.geojson.
"""

import csv
import json
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent
REPO = Path(__file__).resolve().parents[2]
DATA = REPO / "datasets/philadelphia/septa-key-advantage"
ANALYSIS = REPO / "analyses/septa-key-advantage"
BUILD = Path(__file__).resolve().parent / "build"  # scratch output, not committed

DISTRICTS = DATA / "raw/council_districts.geojson"  # 2024 council district boundaries; see README


def ais(address: str) -> dict | None:
    url = "https://api.phila.gov/ais/v1/search/" + urllib.parse.quote(address)
    try:
        with urllib.request.urlopen(url, timeout=20) as r:
            feats = json.load(r).get("features") or []
    except Exception as e:  # AIS 404s on addresses it can't match
        print(f"  AIS miss: {address} ({e})")
        return None
    return feats[0] if feats else None


def main() -> None:
    members = {r["partner"]: r for r in csv.DictReader(open(DATA / "key_advantage_partners_sep2026.csv"))}
    addrs = list(csv.DictReader(open(DATA / "partner_addresses.csv")))
    assert {a["partner"] for a in addrs} == set(members), "partner names drifted between the two CSVs"

    rows = []
    for a in addrs:
        m = members[a["partner"]]
        row = {**m, **{k: a[k] for k in ("resolved_name", "address", "city", "in_philadelphia", "confidence", "notes")}}
        row.update(lng="", lat="", council_district="")
        if a["address"] and a["in_philadelphia"] != "no":
            f = ais(a["address"])
            if f:
                row["lng"], row["lat"] = f["geometry"]["coordinates"]
                row["council_district"] = f["properties"].get("council_district_2024") or ""
        rows.append(row)

    with open(DATA / "partners_geocoded.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    by = defaultdict(lambda: {"employers": 0, "members": 0, "names": []})
    for r in rows:
        key = r["council_district"] or ("Outside Philadelphia" if r["in_philadelphia"] == "no" else "Not located")
        by[key]["employers"] += 1
        by[key]["members"] += int(r["members"])
        by[key]["names"].append(r["partner"])
    with open(DATA / "district_summary.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["council_district", "employers", "members", "partners"])
        for k in sorted(by, key=lambda k: (not k.isdigit(), int(k) if k.isdigit() else 0, k)):
            w.writerow([k, by[k]["employers"], by[k]["members"], "; ".join(by[k]["names"])])
            print(f"{k:>22}  {by[k]['employers']:>3} employers  {by[k]['members']:>7,} members")

    out = DATA
    out.mkdir(parents=True, exist_ok=True)
    gj = json.load(open(DISTRICTS))
    for f in gj["features"]:
        s = by.get(f["properties"]["district"], {"employers": 0, "members": 0})
        f["properties"].update(employers=s["employers"], members=s["members"])
    json.dump(gj, open(out / "districts.geojson", "w"))
    pts = [{"type": "Feature", "geometry": {"type": "Point", "coordinates": [r["lng"], r["lat"]]},
            "properties": {k: r[k] for k in ("partner", "members", "council_district")}} for r in rows if r["lng"]]
    json.dump({"type": "FeatureCollection", "features": pts}, open(out / "worksites.geojson", "w"))


if __name__ == "__main__":
    main()
