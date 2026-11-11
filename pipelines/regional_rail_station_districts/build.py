"""Join Regional Rail stations to PA House and Senate districts and their 2025-26 members.

Usage (needs geopandas):
    python build.py OUTPUT.csv [TIGER_DIR]

District polygons come from the Census TIGER/Line 2024 state legislative district
files (tl_2024_42_sldl.zip and tl_2024_42_sldu.zip), which carry the post-2022 maps.
They are read from TIGER_DIR if given and present, otherwise downloaded from
www2.census.gov into a temporary folder.

Reads, relative to the repo root:
    datasets/septa-region/septa-regional-rail-stations/septa-regional-rail-stations.csv
    datasets/pennsylvania/legislators-2025-2026/records/{house,senate}/*.toml
    datasets/pennsylvania/election-2026-results/records/{house,senate}/*.toml

Each station point is placed in a district, county and municipality by point-in-polygon. Stations outside
Pennsylvania (Delaware, New Jersey) get no district. SEPTA's own district fields
are kept beside the computed ones so disagreements are visible.
"""
import csv
import sys
import tempfile
import tomllib
import urllib.request
from pathlib import Path

import geopandas as gpd

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "datasets"
NEAR_M = 100  # flag stations this close to a district edge
PROJ = "EPSG:2272"  # PA South, feet


TIGER = {
    "house": ("tl_2024_42_sldl.zip", "SLDLST", "https://www2.census.gov/geo/tiger/TIGER2024/SLDL/tl_2024_42_sldl.zip"),
    "senate": ("tl_2024_42_sldu.zip", "SLDUST", "https://www2.census.gov/geo/tiger/TIGER2024/SLDU/tl_2024_42_sldu.zip"),
}


PLACES = {
    "county": ("tl_2024_us_county.zip", "https://www2.census.gov/geo/tiger/TIGER2024/COUNTY/tl_2024_us_county.zip"),
    "municipality": ("tl_2024_42_cousub.zip", "https://www2.census.gov/geo/tiger/TIGER2024/COUSUB/tl_2024_42_cousub.zip"),
}


def tiger_file(name, url, tiger_dir):
    path = Path(tiger_dir) / name if tiger_dir else None
    if not path or not path.exists():
        path = Path(tempfile.mkdtemp()) / name
        urllib.request.urlretrieve(url, path)
    return path


def tiger_places(kind, tiger_dir):
    """Pennsylvania counties (NAME) or county subdivisions (NAMELSAD) with their geometry."""
    name, url = PLACES[kind]
    g = gpd.read_file(f"zip://{tiger_file(name, url, tiger_dir)}")
    g = g[g["STATEFP"] == "42"]
    g["place"] = g["NAME"] if kind == "county" else g["NAMELSAD"]
    return g[["place", "NAME", "COUNTYFP", "geometry"]].to_crs(PROJ)


def tiger_districts(ch, tiger_dir):
    name, col, url = TIGER[ch]
    path = tiger_file(name, url, tiger_dir)
    g = gpd.read_file(f"zip://{path}")
    g["district"] = g[col].astype(int).astype(str)
    return g[["district", "geometry"]].to_crs(PROJ)


def records(path):
    return {p.stem: tomllib.loads(p.read_text()) for p in sorted(path.glob("*.toml"))}


NEAR_LINE_FT = 330  # about 100 m


def adjust_near_line(pts, stations, munis, counties):
    """Resolve stations whose point sits on a municipal line.

    If SEPTA's municipality name belongs to a polygon within about 100 m of the point and is
    not the polygon the point falls in, trust SEPTA (its street address names that municipality)
    and move the point just inside that polygon so district assignment uses the same side.
    Returns the adjusted points and {station index: (municipality, county)} for adjusted rows.
    """
    county_name = dict(zip(counties["COUNTYFP"], counties["NAME"]))
    adjusted = {}
    geoms = list(pts.geometry)
    for i, s in enumerate(stations):
        pt = geoms[i]
        inside = munis[munis.geometry.contains(pt)]
        want = (s["Municipality"] or "").strip().lower()
        if not want or (len(inside) and inside.iloc[0]["NAME"].lower() == want):
            continue
        cand = munis[(munis["NAME"].str.lower() == want) & (munis.geometry.distance(pt) <= NEAR_LINE_FT)]
        if cand.empty:
            continue
        c = cand.iloc[0]
        inner = c.geometry.buffer(-15)  # 15 ft inside the line
        target = inner if not inner.is_empty else c.geometry
        geoms[i] = nearest_point(target, pt)
        adjusted[i] = (c["place"], county_name.get(c["COUNTYFP"], ""))
    return gpd.GeoDataFrame(pts.drop(columns="geometry"), geometry=geoms, crs=pts.crs), adjusted


def nearest_point(geom, pt):
    from shapely.ops import nearest_points
    return nearest_points(geom, pt)[0]


def main(out, tiger_dir=None):
    stations = list(csv.DictReader(open(D / "septa-region/septa-regional-rail-stations/septa-regional-rail-stations.csv")))
    pts = gpd.GeoDataFrame(
        stations,
        geometry=gpd.points_from_xy([float(s["Longitude"]) for s in stations], [float(s["Latitude"]) for s in stations]),
        crs="EPSG:4326",
    ).to_crs(PROJ)
    munis_all = tiger_places("municipality", tiger_dir)
    counties_all = tiger_places("county", tiger_dir)
    pts, adjusted = adjust_near_line(pts, stations, munis_all, counties_all)
    legs = {ch: records(D / f"pennsylvania/legislators-2025-2026/records/{ch}") for ch in ("house", "senate")}
    results = {ch: records(D / f"pennsylvania/election-2026-results/records/{ch}") for ch in ("house", "senate")}
    res = {}
    for ch in ("house", "senate"):
        g = tiger_districts(ch, tiger_dir)
        j = gpd.sjoin(pts, g, how="left", predicate="within")
        # a point can fall in two polygons on a shared edge; keep the lowest district for determinism
        j = j.sort_values("district").groupby(level=0).first()
        dist = {}
        edges = g.boundary.union_all()
        for i, row in j.iterrows():
            d = row["district"] if isinstance(row["district"], str) else ""
            near = bool(d) and pts.geometry.loc[i].distance(edges) * 0.3048 <= NEAR_M
            dist[i] = (d, near)
        res[ch] = dist
    for kind in ("county", "municipality"):
        j = gpd.sjoin(pts, tiger_places(kind, tiger_dir), how="left", predicate="within")
        j = j[~j.index.duplicated(keep="first")]
        res[kind] = {i: (p if isinstance(p, str) else "") for i, p in zip(j.index, j["place"])}
    for i, (muni, cty) in adjusted.items():
        res["municipality"][i], res["county"][i] = muni, cty
    rows = []
    for i, s in enumerate(stations):
        r = {
            "line": s["Line_Name"], "station": s["Station_Name"], "stop_id": s["Stop_ID"],
            "latitude": s["Latitude"], "longitude": s["Longitude"],
            "septa_county": s["County"], "septa_municipality": s["Municipality"],
            "county": res["county"][i], "municipality": res["municipality"][i],
        }
        r["location_basis"] = "septa_address_near_line" if i in adjusted else "coordinates"
        r["county_matches_septa"] = "" if not r["county"] else str(r["county"] == s["County"]).lower()
        for ch, septa_col in (("house", "PA_State_House_District"), ("senate", "PA_State_Senate_District")):
            d, near = res[ch][i]
            sd = (s[septa_col] or "").strip()
            r[f"septa_{ch}_district"] = sd
            r[f"{ch}_district"] = d
            r[f"{ch}_matches_septa"] = "" if not d else str(sd == d).lower()
            r[f"{ch}_near_boundary"] = "" if not d else str(near).lower()
            m = legs[ch].get(d)
            r[f"{ch}_member_2025_26"] = m["full_name"] if m else ""
            r[f"{ch}_party_2025_26"] = m["party"] if m else ""
            f = results[ch].get(d)
            r[f"{ch}_seat_2026_status"] = f["outcome"] if f else ("" if not d else "not_up")
            r[f"{ch}_winner_2026"] = f.get("winner", "") if f else ""
            r[f"{ch}_winner_party_2026"] = f.get("winner_party", "") if f else ""
        rows.append(r)
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} stations to {out}")


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2] if len(sys.argv) == 3 else None)
