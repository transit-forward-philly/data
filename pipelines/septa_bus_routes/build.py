"""Every SEPTA bus and trackless trolley route: how often it runs, SEPTA's frequent marking, its
map lines and the legislative and council districts it crosses.

Usage (needs geopandas):
    python build.py OUTPUT_DIR [CACHE_DIR]

Sources:
    SEPTA GTFS release v202611010 (https://github.com/septadev/GTFS/releases/tag/v202611010,
        schedule starting 2026-11-01): routes, trips, stop_times, calendars and shapes from
        google_bus.zip.
    Census TIGER/Line 2024 House and Senate districts and Philadelphia Council Districts 2024,
        through the helpers in ../septa_accelerate_stations/build.py (which uses
        ../regional_rail_station_districts/build.py for the TIGER files).
    SEPTA's frequent network: GTFS `route_color` EF3340 ("Frequent Red"). SEPTA's maps-and-signs
        page defines red routes as arriving "every 15 minutes or better from 6 am to 9 pm weekdays"
        (https://wwww.septa.org/initiatives/bus/maps-signs/). This is the weekday network running
        now (25 routes). The Accelerate plan counts 29 routes "every 15 minutes or better, 7 days a
        week" for the full New Bus Network (phases through 2027); SEPTA has not published which
        routes make up the 29.
Downloads go to CACHE_DIR if given (and are reused from there), otherwise to a temporary folder.

Frequency is measured from the schedule: for each route and direction, the trips that start
between 7:00 and 19:00 on Wednesday 2026-11-18, Saturday 2026-11-21 and Sunday 2026-11-22.
`*_avg_headway_min` is 720 minutes divided by those trips, taking the less frequent direction.
`*_max_gap_min` is the longest wait in that window, counting from 7:00 to the first trip and
from the last trip to 19:00. Only directions with at least two trips in the window are measured,
so a loop that runs one way only (310, LUCYGO, LUCYGR) gets a value from that one direction. A
day is blank only when no direction has two trips.

`service_kind`, from the GTFS route_id, so district counts can leave out special services:
    no trips          the route has no trips at all in this release
    overnight         route_id ends in _OWL (L1 OWL, B1 OWL)
    rail replacement  route_id ends in _BUS (M1 Bus, D1 Bus, D2 Bus, NOR Bus; FOX, T and WTR Bus have no trips)
    school            route_id is a number from 400 to 499 (SEPTA's school trippers)
    regular           everything else

Writes to OUTPUT_DIR:
    septa-bus-routes.csv      one row per GTFS bus and trackless trolley route (trolley and Metro routes
                              left out). 27 rows have a blank Wednesday headway: 18 school trippers,
                              4 routes with no trips in this release, 3 rail-replacement shuttles
                              with no trips that day (D1 Bus, D2 Bus, NOR Bus) and 2 overnight OWL
                              routes that run outside 7:00 to 19:00
    septa-bus-routes.geojson  one feature per route: its GTFS shapes dissolved into one MultiLineString
                              (see map_lines), for mapping
"""
import csv
import importlib.util
import io
import json
import sys
import tempfile
import zipfile
from collections import defaultdict
from pathlib import Path

import geopandas as gpd
from shapely.geometry import LineString, MultiLineString
from shapely.ops import linemerge, unary_union

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("accelerate_build", HERE.parent / "septa_accelerate_stations" / "build.py")
ab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ab)

DAYS = {"wed": ("20261118", "wednesday"), "sat": ("20261121", "saturday"), "sun": ("20261122", "sunday")}
WINDOW = (7 * 3600, 19 * 3600)
NOT_BUS = {"L1", "B1", "B2", "B3", "M1", "T1", "T2", "T3", "T4", "T5", "D1", "D2", "G1"}
FREQUENT_RED = "EF3340"  # SEPTA's "Frequent Red" route color
BUS_TYPES = {"3", "11"}  # bus and trackless trolley (Routes 59, 66, 75)
ROUTE_TYPES = {"3": "bus", "11": "trackless trolley"}
CHAMBERS = ("house", "senate", "council")
SIMPLIFY_DEG = 0.00001  # about 1 m, for the GeoJSON map lines only; districts use the full shapes


def seconds(hms):
    h, m, s = map(int, hms.split(":"))
    return h * 3600 + m * 60 + s


def service_kind(rid, has_trips):
    """What kind of service a route is, from its GTFS route_id (rules listed in the module docstring)."""
    if not has_trips:
        return "no trips"
    if rid.endswith("_OWL"):
        return "overnight"
    if rid.endswith("_BUS"):
        return "rail replacement"
    if rid.isdigit() and 400 <= int(rid) <= 499:
        return "school"
    return "regular"


def map_lines(lines):
    """GeoJSON MultiLineString for a route's shapes, small enough to commit.

    Shape variants mostly run over the same streets, so the shapes are dissolved into one network
    (each street segment once), simplified to about 1 m and rounded to 5 decimals (about 1 m).
    """
    if not lines:
        return None
    u = unary_union(MultiLineString(lines))
    u = linemerge(u) if u.geom_type == "MultiLineString" else u
    out = []
    for ln in getattr(u.simplify(SIMPLIFY_DEG), "geoms", [u.simplify(SIMPLIFY_DEG)]):
        c = [(round(x, 5), round(y, 5)) for x, y in ln.coords]
        c = [p for i, p in enumerate(c) if i == 0 or p != c[i - 1]]
        if len(c) > 1:
            out.append(c)
    return dict(type="MultiLineString", coordinates=out)


def main(out_dir, cache_dir=None):
    cache_dir = cache_dir or tempfile.mkdtemp()
    outer = zipfile.ZipFile(ab.fetch(f"septa_gtfs_{ab.GTFS_TAG}.zip", ab.GTFS_URL, cache_dir))
    inner = zipfile.ZipFile(io.BytesIO(outer.read("google_bus.zip")))
    read = lambda f: csv.DictReader(io.TextIOWrapper(inner.open(f"{f}.txt"), encoding="utf-8-sig"))

    cal, cdates = list(read("calendar")), list(read("calendar_dates"))
    active = {}
    for k, (date, dow) in DAYS.items():
        s = {c["service_id"] for c in cal if c[dow] == "1" and c["start_date"] <= date <= c["end_date"]}
        for x in cdates:
            if x["date"] == date:
                (s.add if x["exception_type"] == "1" else s.discard)(x["service_id"])
        active[k] = s

    routes = {r["route_id"]: r for r in read("routes") if r["route_id"] not in NOT_BUS and r["route_type"] in BUS_TYPES}
    trips = {t["trip_id"]: t for t in read("trips") if t["route_id"] in routes}
    first = {}
    for st in read("stop_times"):
        tid = st["trip_id"]
        if tid in trips:
            seq = int(st["stop_sequence"])
            if tid not in first or seq < first[tid][0]:
                first[tid] = (seq, seconds(st["departure_time"]))
    starts = defaultdict(list)
    for tid, (_, dep) in first.items():
        t = trips[tid]
        for k in DAYS:
            if t["service_id"] in active[k]:
                starts[(t["route_id"], t["direction_id"], k)].append(dep)

    has_trips = {t["route_id"] for t in trips.values()}
    shape_ids = defaultdict(set)
    for t in trips.values():
        shape_ids[t["route_id"]].add(t["shape_id"])
    wanted = set().union(*shape_ids.values())
    pts = defaultdict(list)
    for s in read("shapes"):
        if s["shape_id"] in wanted:
            pts[s["shape_id"]].append((int(s["shape_pt_sequence"]), float(s["shape_pt_lon"]), float(s["shape_pt_lat"])))

    places = ab.Places(cache_dir)
    rows, features = [], []
    for rid in sorted(routes, key=lambda r: (not r.isdigit(), int(r) if r.isdigit() else 0, r)):
        r = routes[rid]
        row = dict(route=r["route_short_name"] or rid, name=r["route_long_name"], route_type=ROUTE_TYPES[r["route_type"]],
                   service_kind=service_kind(rid, rid in has_trips))
        for k in DAYS:
            avg = gap = None
            for d in ("0", "1"):
                xs = sorted(x for x in starts.get((rid, d, k), []) if WINDOW[0] <= x < WINDOW[1])
                if len(xs) < 2:
                    continue  # a loop runs one way only; measure the directions that have trips
                gaps = [xs[0] - WINDOW[0]] + [b - a for a, b in zip(xs, xs[1:])] + [WINDOW[1] - xs[-1]]
                a, g = 720 / len(xs), max(gaps) / 60
                avg, gap = (a, g) if avg is None else (max(avg, a), max(gap, g))
            row[f"{k}_avg_headway_min"] = f"{avg:.1f}" if avg is not None else ""
            row[f"{k}_max_gap_min"] = f"{gap:.1f}" if gap is not None else ""
        row["septa_frequent_weekday"] = str(r["route_color"].upper() == FREQUENT_RED).lower()
        lines = [LineString([(x, y) for _, x, y in sorted(pts[s])]) for s in sorted(shape_ids[rid]) if len(pts[s]) > 1]
        features.append(dict(type="Feature", geometry=map_lines(lines),
                             properties=dict(route=row["route"], name=row["name"],
                                             septa_frequent_weekday=row["septa_frequent_weekday"] == "true")))
        if lines:
            g = gpd.GeoDataFrame(geometry=[MultiLineString(lines)], crs="EPSG:4326").to_crs(ab.PROJ)
            for ch in CHAMBERS:
                j = gpd.sjoin(g, places.layers[ch], how="inner", predicate="intersects")
                row[f"{ch}_districts"] = "; ".join(sorted(set(j["district"].astype(str)), key=lambda d: (len(d), d)))
        else:
            for ch in CHAMBERS:
                row[f"{ch}_districts"] = ""
        row["route_url"] = r["route_url"]
        rows.append(row)

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    ab.write(out / "septa-bus-routes.csv", rows, list(rows[0].keys()))
    with open(out / "septa-bus-routes.geojson", "w", encoding="utf-8") as fh:
        json.dump(dict(type="FeatureCollection", features=features), fh, separators=(",", ":"))
        fh.write("\n")
    print("bus routes:", len(rows), "with shapes:", sum(f["geometry"] is not None for f in features))


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2] if len(sys.argv) == 3 else None)
