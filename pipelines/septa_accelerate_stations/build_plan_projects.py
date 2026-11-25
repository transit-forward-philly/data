"""Place every named project in SEPTA's Accelerate plan in legislative and council districts.

Usage (needs geopandas; run build.py first, since this reads its station output):
    python build_plan_projects.py OUTPUT_DIR [CACHE_DIR]

Sources:
    sources/jeff-maki-septa-accelerate-projects-2026-11-11.geojson
        Jeff Maki's catalog of the 39 named projects in the Accelerate plan (Sept 2026), made with
        AI help and shared in TFP Slack on 2026-11-11. Names, programs, statuses, quantities and
        page numbers come from it. Each name was checked against the plan text and each page
        number against the plan PDF (printed page = 2 x PDF page - 4) on 2026-11-24.
    SEPTA GTFS release v202611010: station locations (through septa-accelerate-stations.csv) and
        bus route shapes for Routes 47, 72 and 76.
    City of Philadelphia Council Districts 2024 and Census TIGER/Line 2024 House and Senate
        districts, through the helpers in build.py.

Reads, relative to the repo root:
    datasets/septa-region/septa-accelerate-station-service/septa-accelerate-stations.csv

Location, in order of preference:
    gtfs_station        the project is at a station in septa-accelerate-stations.csv; its districts are copied
    gtfs_route_shape    a bus route in GTFS; districts are those its shapes cross
    approximate_point   a site with no GTFS station (transit center, viaduct); Jeff's hand-placed point
    schematic_line      a street corridor the plan names without an extent; Jeff's hand-drawn line
    covered_elsewhere   already placed by station or route in another file of this dataset
    none                systemwide, or the plan names no site

Writes to OUTPUT_DIR:
    septa-accelerate-plan-projects.csv      one row per named project, with districts
    septa-accelerate-plan-projects.geojson  the same rows with geometry, for mapping
"""
import csv
import importlib.util
import io
import json
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

import geopandas as gpd
from shapely.geometry import LineString, MultiLineString, MultiPoint, Point, shape, mapping

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SRC = HERE / "sources" / "jeff-maki-septa-accelerate-projects-2026-11-11.geojson"
STATIONS = ROOT / "datasets/septa-region/septa-accelerate-station-service/septa-accelerate-stations.csv"

spec = importlib.util.spec_from_file_location("accelerate_build", HERE / "build.py")
ab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ab)

DS = "septa-accelerate-station-service"
# Projects at stations: id -> [(mode, station name in septa-accelerate-stations.csv)]
AT_STATIONS = {
    # the plan: "on the [B] Broad Street Line and [L] Market-Frankford Line vehicles when they reach the end of
    # the line" (PDF p. 17); the line ends are the B1 and L1 terminals in GTFS
    "ACC-003": [("Metro", "69th St Transit Center"), ("Metro", "Frankford Transit Center"),
                ("Metro", "Fern Rock Transit Center"), ("Metro", "NRG Station")],
    "ACC-004": [("Metro", "69th St Transit Center")],
    "ACC-006": [("Metro", "Tasker-Morris")],
    "ACC-007": [("Metro", "Drexel Station at 30th St")],
    "ACC-008": [("Metro", "Susquehanna-Dauphin")],
    "ACC-029": [("Regional Rail", "Conshohocken")],
    "ACC-030": [("Regional Rail", "Ambler")],
    "ACC-031": [("Regional Rail", "Germantown")],
    "ACC-032": [("Metro", "69th St Transit Center")],
    "ACC-036": [("Metro", "15th St/City Hall")],
    "ACC-037": [("Metro", "15th St/City Hall")],
    "ACC-038": [("Regional Rail", "Paoli")],
}
BUS_ROUTES = {"ACC-010": "72", "ACC-011": "76", "ACC-028": "47"}
NOT_PLACED = set()  # located in Jeff's file, but the plan names no site
APPROX_POINTS = {"ACC-022", "ACC-023", "ACC-039"}
SCHEMATIC = {"ACC-026", "ACC-027"}
COVERED = {  # id -> where this dataset already places it
    "ACC-014": f"{DS}/septa-accelerate-trolley-routes.csv",
    "ACC-015": f"{DS}/septa-accelerate-trolley-routes.csv",
    "ACC-016": f"{DS}/septa-accelerate-stations.csv (Metro rows, L)",
    "ACC-017": f"{DS}/septa-accelerate-stations.csv (Metro rows, B)",
    "ACC-018": f"{DS}/septa-accelerate-stations.csv (Metro rows, M)",
    "ACC-021": f"{DS}/fy27-named-station-projects.csv (Mainline-Schuylkill Bridges and Interlockings)",
    "ACC-033": f"{DS}/septa-accelerate-stations.csv (proposed_frequency_minutes)",
    "ACC-034": f"{DS}/septa-accelerate-stations.csv (proposed_frequency_minutes)",
    "ACC-035": f"{DS}/septa-accelerate-stations.csv (accessibility_rebuild_proposed)",
}
NOTES = {  # corrections or context found while checking
    "ACC-003": "The plan says the cleaning happens on B and L vehicles 'when they reach the end of the line'; the line ends are the B1 and L1 terminals in GTFS.",
    "ACC-034": "Jeff's file says the pairing of endpoints into the three S Lines is not given; the Regional Rail Master Plan gives it (S1 Airport-Norristown, S2 Chestnut Hill East-Wawa, S3 Paoli-Fox Chase).",
    "ACC-036": "The FY27 capital budget still carries City Hall & 15th Street Stations ($216.66M).",
    "ACC-037": "The FY27 capital budget still carries City Hall & 15th Street Stations ($216.66M).",
    "ACC-011": "GTFS v202611010 Route 76 runs Rising Sun-Olney to Columbus Commons.",
    "ACC-028": "GTFS v202611010 Route 47 runs Whitman Plaza to 5th-Godfrey.",
}
RELATED_FY27 = {
    "ACC-021": "Mainline–Schuylkill Bridges and Interlockings (30th Street Station to Suburban Station)",
    "ACC-029": "Conshohocken Station Parking",
    "ACC-032": "69th Street Transportation Center Multi-Modal & ADA Improvements",
    "ACC-036": "City Hall & 15th Street Stations",
    "ACC-037": "City Hall & 15th Street Stations",
}
CHAMBERS = ("house", "senate", "council")


def bus_shapes(cache_dir, routes):
    """{route: MultiLineString of every GTFS shape the route uses}."""
    outer = zipfile.ZipFile(ab.fetch(f"septa_gtfs_{ab.GTFS_TAG}.zip", ab.GTFS_URL, cache_dir))
    inner = zipfile.ZipFile(io.BytesIO(outer.read("google_bus.zip")))
    read = lambda f: csv.DictReader(io.TextIOWrapper(inner.open(f"{f}.txt"), encoding="utf-8-sig"))
    want = defaultdict(set)
    for t in read("trips"):
        if t["route_id"] in routes:
            want[t["route_id"]].add(t["shape_id"])
    shape_ids = set().union(*want.values())
    pts = defaultdict(list)
    for s in read("shapes"):
        if s["shape_id"] in shape_ids:
            pts[s["shape_id"]].append((int(s["shape_pt_sequence"]), float(s["shape_pt_lon"]), float(s["shape_pt_lat"])))
    out = {}
    for r in routes:
        lines = [LineString([(x, y) for _, x, y in sorted(pts[sid])]) for sid in sorted(want[r]) if len(pts[sid]) > 1]
        if not lines:
            raise SystemExit(f"no GTFS shapes for bus route {r}")
        out[r] = MultiLineString(lines)
    return out


def districts_crossed(geom, places):
    """{chamber: sorted districts} that a line or point geometry touches."""
    g = gpd.GeoDataFrame(geometry=[geom], crs="EPSG:4326").to_crs(ab.PROJ)
    out = {}
    for ch in CHAMBERS:
        j = gpd.sjoin(g, places.layers[ch], how="inner", predicate="intersects")
        out[ch] = sorted(set(j["district"].astype(str)), key=lambda d: (len(d), d))
    return out


def joined(values):
    return "; ".join(values)


def main(out_dir, cache_dir=None):
    import tempfile
    cache_dir = cache_dir or tempfile.mkdtemp()
    src = json.load(open(SRC))
    feats = src["features"]
    if len(feats) != 39:
        raise SystemExit(f"expected 39 projects in {SRC.name}, found {len(feats)}")
    stations = {(r["mode"], r["station"]): r for r in csv.DictReader(open(STATIONS))}
    places = ab.Places(cache_dir)
    shapes = bus_shapes(cache_dir, set(BUS_ROUTES.values()))

    rows, geo = [], []
    for f in feats:
        p, pid = f["properties"], f["properties"]["id"]
        dist = {ch: [] for ch in CHAMBERS}
        geom, station_names = None, []
        if pid in AT_STATIONS:
            basis, pts = "gtfs_station", []
            for key in AT_STATIONS[pid]:
                s = stations.get(key)
                if s is None:
                    raise SystemExit(f"{pid}: station {key} is not in {STATIONS.name}")
                station_names.append(s["station"])
                pts.append(Point(float(s["longitude"]), float(s["latitude"])))
                for ch in CHAMBERS:
                    d = s[f"{ch}_district"]
                    if d and d not in dist[ch]:
                        dist[ch].append(d)
            geom = pts[0] if len(pts) == 1 else MultiPoint(pts)
        elif pid in BUS_ROUTES:
            basis, geom = "gtfs_route_shape", shapes[BUS_ROUTES[pid]]
            dist = districts_crossed(geom, places)
        elif pid in APPROX_POINTS or pid in SCHEMATIC:
            basis = "approximate_point" if pid in APPROX_POINTS else "schematic_line"
            geom = shape(f["geometry"])
            dist = districts_crossed(geom, places)
        elif pid in COVERED:
            basis = "covered_elsewhere"
        else:
            basis = "none"
            if f["geometry"] is not None and pid not in NOT_PLACED:
                raise SystemExit(f"{pid} has a geometry but no location rule")
        for ch in CHAMBERS:
            dist[ch] = sorted(dist[ch], key=lambda d: (len(d), d))
        row = dict(
            id=pid, name=p["name"], program=p["program"], project_type=p["project_type"], status=p["status"],
            quantities=p.get("quantities") or "", description=p.get("description") or "",
            plan_pages=p.get("source_pages") or "", location_basis=basis,
            location_note=p.get("location_note") or "", stations=joined(station_names),
            house_districts=joined(dist["house"]), senate_districts=joined(dist["senate"]),
            council_districts=joined(dist["council"]), covered_in=COVERED.get(pid, ""),
            related_fy27_project=RELATED_FY27.get(pid, ""),
            dvrpc_tip_mpms=str(p.get("dvrpc_tip_related") or ""), notes=NOTES.get(pid, ""),
        )
        rows.append(row)
        if geom is not None:
            geo.append(dict(type="Feature", properties=row, geometry=mapping(geom)))

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    ab.write(out / "septa-accelerate-plan-projects.csv", rows, list(rows[0].keys()))
    with open(out / "septa-accelerate-plan-projects.geojson", "w") as fh:
        json.dump(dict(type="FeatureCollection", features=geo), fh, separators=(",", ":"))
        fh.write("\n")
    counts = defaultdict(int)
    for r in rows:
        counts[r["location_basis"]] += 1
    print("projects:", len(rows), dict(counts))


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2] if len(sys.argv) == 3 else None)
