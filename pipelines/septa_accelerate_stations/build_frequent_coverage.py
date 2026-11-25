"""Count residents within a quarter mile of frequent transit in each House, Senate and Council district.

Usage (needs geopandas 1.0 or later, for the dwithin join; run build.py, ../septa_bus_routes/build.py and
build_district_summary.py first):
    python build_frequent_coverage.py OUTPUT_DIR [CACHE_DIR]

Sources:
    Census 2020 redistricting data (PL 94-171) for Pennsylvania, the legacy-format file
        (https://www2.census.gov/programs-surveys/decennial/2020/data/01-Redistricting_File--PL_94-171/Pennsylvania/pa2020.pl.zip,
        57 MB, not committed): total population P1_001N (segment 1, field P0010001) for every 2020 block,
        and each block's internal point from the geographic header. This is the same P1_001N the Census
        API serves; the API answered every keyless request with a "Missing Key" page on 2026-11-25. The
        five county totals are checked against the published 2020 counts below.
    SEPTA GTFS release v202611010 (through build.py): stops on the frequent bus routes and the trolley routes.
    datasets/septa-region/septa-bus-routes/septa-bus-routes.csv: which bus routes are frequent
        (septa_frequent_weekday) and their measured Wednesday, Saturday and Sunday average headways.
    datasets/septa-region/septa-accelerate-station-service/septa-accelerate-stations.csv:
        Metro station locations and the Regional Rail stations in the proposed 15-minute tier.
    datasets/septa-region/septa-accelerate-station-service/septa-accelerate-district-summary.csv:
        the list of districts (one output row per summary row).
    Census TIGER/Line 2024 House and Senate districts, Philadelphia Council Districts 2024 and TIGER 2024
        counties, through Places in build.py.
Downloads go to CACHE_DIR if given (and are reused from there), otherwise to a temporary folder.

Method:
    A block counts as near a stop when its Census internal point (INTPTLAT/INTPTLON in the geographic header) is within
    1,320 feet (a quarter mile, 402 m) in a straight line of the stop. That is a circle around the stop,
    not a walk along streets. The whole block's population counts or none of it does. Blocks are placed
    in districts by the same internal point. The 2022 legislative maps were drawn from 2020 blocks, so
    blocks nest inside House and Senate districts.

    Two stop sets:
    frequent bus      stops on the bus and trackless trolley routes with septa_frequent_weekday = true in the
                      bus routes dataset (SEPTA's "Frequent Red" color, every 15 minutes or better 6 am to
                      9 pm weekdays), 25 routes in this release.
                      Every stop the route serves counts, including stops on branches that get only part
                      of the route's trips.
    frequent transit  frequent bus, plus every Metro station (L, B, M), every stop on the trolley routes
                      T1-T5, D1, D2 and G1, and the Regional Rail stations in Accelerate's proposed 15-minute
                      tier. Those trains are the plan's end state (2030-2055), so the column name says so.
                      A middle column leaves the Regional Rail stations out.

    Blocks are read for the whole state, so a district that reaches outside the five SEPTA counties
    gets its full population.

Writes to OUTPUT_DIR:
    septa-frequent-transit-coverage-by-district.csv   one row per district in the district summary
Prints county totals (Philadelphia is the citywide figure) and chamber totals for checking, and two
Philadelphia checks on how much the definition moves the count (quoted in the dataset README):
    seven-day frequent  bus routes averaging 15 minutes or better on all three measured days (Wednesday,
                        Saturday, Sunday) in the bus routes file, plus Metro stations and T1-T5 stops
    eighth mile         the frequent bus stop set with 660 feet in place of 1,320
"""
import csv
import io
import importlib.util
import sys
import tempfile
import zipfile
from pathlib import Path

import geopandas as gpd
import pandas as pd

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("accelerate_build", HERE / "build.py")
ab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ab)

OUT_DIR = ab.D / "septa-region/septa-accelerate-station-service"
BUS_CSV = ab.D / "septa-region/septa-bus-routes/septa-bus-routes.csv"
QUARTER_MILE_FT = 1320  # PROJ is EPSG:2272, in feet
EIGHTH_MILE_FT = 660
T_ROUTES = ["T1", "T2", "T3", "T4", "T5"]
TROLLEY = ["T1", "T2", "T3", "T4", "T5", "D1", "D2", "G1"]
PL_URL = ("https://www2.census.gov/programs-surveys/decennial/2020/data/01-Redistricting_File--PL_94-171/"
          "Pennsylvania/pa2020.pl.zip")
# Geographic header fields used (0-based positions in the 2020 PL 94-171 pipe-delimited geoheader).
SUMLEV, LOGRECNO, GEOID, COUNTY, INTPTLAT, INTPTLON = 2, 7, 8, 14, 92, 93
# Published 2020 Census counts (P1_001N) for the five SEPTA counties, used as a checksum on the block files.
COUNTY_2020 = {"017": ("Bucks", 646538), "029": ("Chester", 534413), "045": ("Delaware", 576830),
               "091": ("Montgomery", 856553), "101": ("Philadelphia", 1603797)}
CHAMBERS = ("house", "senate", "council")


def points(lons, lats):
    return gpd.GeoDataFrame(geometry=gpd.points_from_xy(lons, lats), crs="EPSG:4326").to_crs(ab.PROJ)


def pl_blocks(cache_dir):
    """Every Pennsylvania 2020 block: GEOID, county, P1_001N and internal point, from the PL 94-171 file."""
    z = zipfile.ZipFile(ab.fetch("pa2020.pl.zip", PL_URL, cache_dir))
    geo = {}
    with z.open("pageo2020.pl") as fh:
        for line in io.TextIOWrapper(fh, encoding="latin-1"):
            f = line.rstrip("\n").split("|")
            if f[SUMLEV] == "750":
                geo[f[LOGRECNO]] = (f[GEOID][-15:], f[COUNTY], float(f[INTPTLON]), float(f[INTPTLAT]))
    rows = []
    with z.open("pa000012020.pl") as fh:  # segment 1: FILEID|STUSAB|CHARITER|CIFSN|LOGRECNO|P0010001|...
        for line in io.TextIOWrapper(fh, encoding="latin-1"):
            f = line.split("|", 6)
            if f[4] in geo:
                rows.append(geo[f[4]] + (int(f[5]),))
    b = pd.DataFrame(rows, columns=["geoid", "county", "lon", "lat", "P1_001N"])
    if len(b) != len(geo):
        raise SystemExit(f"{len(geo) - len(b)} blocks have no P1 row")
    return gpd.GeoDataFrame(b, geometry=points(b["lon"], b["lat"]).geometry.values, crs=ab.PROJ)


def near(blocks, stops, feet=QUARTER_MILE_FT):
    """Boolean array: block internal point within `feet` (default a quarter mile) of any stop."""
    j = gpd.sjoin(blocks[["geometry"]], stops, how="inner", predicate="dwithin", distance=feet)
    return blocks.index.isin(j.index.unique())


def main(out_dir, cache_dir=None):
    cache_dir = cache_dir or tempfile.mkdtemp()
    places = ab.Places(cache_dir)
    summary = list(csv.DictReader(open(OUT_DIR / "septa-accelerate-district-summary.csv", encoding="utf-8")))
    wanted = {(r["chamber"], r["district"]) for r in summary}

    blocks = pl_blocks(cache_dir)
    for c, (name, published) in COUNTY_2020.items():
        got = int(blocks.loc[blocks["county"] == c, "P1_001N"].sum())
        if got != published:
            raise SystemExit(f"{name} County block total {got:,} does not match the published {published:,}")

    # --- stops ---
    bus = ab.gtfs(cache_dir)["bus"]
    stop_xy = {s["stop_id"]: (float(s["stop_lon"]), float(s["stop_lat"])) for s in bus["stops"] if s["stop_lat"]}
    # The bus routes file names a route by GTFS route_short_name, or route_id where that is blank.
    route_id = {(r["route_short_name"] or r["route_id"]): r["route_id"] for r in bus["routes"]}
    bus_csv = list(csv.DictReader(open(BUS_CSV, encoding="utf-8")))
    frequent = {route_id[r["route"]] for r in bus_csv if r["septa_frequent_weekday"] == "true"}
    days = ("wed_avg_headway_min", "sat_avg_headway_min", "sun_avg_headway_min")
    seven_day = {route_id[r["route"]] for r in bus_csv
                 if r["service_kind"] == "regular" and all(r[k] and float(r[k]) <= 15 for k in days)}

    def route_stops(routes):
        ids = sorted({r["stop_id"] for r in bus["route_stops"] if r["route_id"] in routes and r["stop_id"] in stop_xy})
        return [stop_xy[i] for i in ids]

    stations = list(csv.DictReader(open(OUT_DIR / "septa-accelerate-stations.csv", encoding="utf-8")))
    metro = [(float(s["longitude"]), float(s["latitude"])) for s in stations if s["mode"] == "Metro"]
    rr15 = [(float(s["longitude"]), float(s["latitude"])) for s in stations
            if s["mode"] == "Regional Rail" and s["proposed_frequency_minutes"] == "15"]
    bus_xy, trolley_xy = route_stops(frequent), route_stops(set(TROLLEY))
    print(f"stops: {len(bus_xy)} frequent bus ({len(frequent)} routes), {len(metro)} Metro stations, "
          f"{len(trolley_xy)} trolley stops, {len(rr15)} Regional Rail 15-minute stations")

    as_gdf = lambda xy: points([p[0] for p in xy], [p[1] for p in xy])
    blocks["bus"] = near(blocks, as_gdf(bus_xy))
    blocks["excl_rr"] = blocks["bus"] | near(blocks, as_gdf(metro + trolley_xy))
    blocks["incl_rr15"] = blocks["excl_rr"] | near(blocks, as_gdf(rr15))

    # --- districts ---
    rows = []
    for ch in CHAMBERS:
        j = gpd.sjoin(blocks, places.layers[ch], how="inner", predicate="within")
        j = j[~j.index.duplicated(keep="first")]
        for d, g in j.groupby("district"):
            if (ch, d) not in wanted:
                continue
            pop = int(g["P1_001N"].sum())
            row = dict(chamber=ch, district=d, population_2020=pop)
            for key, col in (("bus", "frequent_bus"), ("excl_rr", "frequent_transit_excl_rr"),
                             ("incl_rr15", "frequent_transit_incl_rr15_plan")):
                n = int(g.loc[g[key], "P1_001N"].sum())
                row[f"pop_near_{col}"] = n
                row[f"share_near_{col}"] = f"{n / pop:.3f}" if pop else ""
            rows.append(row)
    missing = wanted - {(r["chamber"], r["district"]) for r in rows}
    if missing:
        raise SystemExit(f"no blocks found for {sorted(missing)}")
    order = {(r["chamber"], r["district"]): i for i, r in enumerate(summary)}
    rows.sort(key=lambda r: order[(r["chamber"], r["district"])])

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    cols = ["chamber", "district", "population_2020",
            "pop_near_frequent_bus", "share_near_frequent_bus",
            "pop_near_frequent_transit_excl_rr", "share_near_frequent_transit_excl_rr",
            "pop_near_frequent_transit_incl_rr15_plan", "share_near_frequent_transit_incl_rr15_plan"]
    with open(out / "septa-frequent-transit-coverage-by-district.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} district rows -> {out / 'septa-frequent-transit-coverage-by-district.csv'}")

    # --- checks ---
    print("\nresidents within a quarter mile, by county (2020 population)")
    print(f"{'county':<14}{'population':>12}{'freq bus':>12}{'+metro/trolley':>16}{'+RR 15 plan':>14}")
    region = blocks[blocks["county"].isin(COUNTY_2020)]
    for c, (name, _) in list(COUNTY_2020.items()) + [(None, ("Five counties", 0))]:
        g = region if c is None else region[region["county"] == c]
        p = g["P1_001N"].sum()
        vals = [g.loc[g[k], "P1_001N"].sum() for k in ("bus", "excl_rr", "incl_rr15")]
        print(f"{name:<14}{p:>12,}" + "".join(f"{v:>10,} {v / p:>4.0%}" for v in vals))
    for ch in CHAMBERS:
        tot = sum(r["population_2020"] for r in rows if r["chamber"] == ch)
        print(f"{ch}: {sum(r['chamber'] == ch for r in rows)} districts, population {tot:,}")

    # Definition checks, Philadelphia only (quoted in the dataset README).
    phl = blocks[blocks["county"] == "101"]
    seven = near(phl, as_gdf(route_stops(seven_day) + metro + route_stops(set(T_ROUTES))))
    eighth = near(phl, as_gdf(bus_xy), EIGHTH_MILE_FT)
    print("\nPhiladelphia definition checks (2020 population)")
    print(f"seven-day frequent bus ({', '.join(sorted(seven_day))}) + Metro + T1-T5, quarter mile: "
          f"{int(phl.loc[seven, 'P1_001N'].sum()):,}")
    print(f"frequent bus, quarter mile: {int(phl.loc[phl['bus'], 'P1_001N'].sum()):,}; "
          f"eighth mile: {int(phl.loc[eighth, 'P1_001N'].sum()):,}")


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2] if len(sys.argv) == 3 else None)
