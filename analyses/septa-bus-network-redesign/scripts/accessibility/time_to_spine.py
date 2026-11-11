"""Did the redesign make it faster to REACH the rapid-transit spine?

SEPTA's defence of the redesign is that it is a network: crosstown buses feed
the subway, and a transfer beats a long one-seat ride. That argument is testable
directly — if it holds, the walk-plus-bus time from each block group to its
nearest Metro station should FALL.

Transfers are already free (2020) and R5's travel-time model charges no fare, so
the assumption is made in SEPTA's favour throughout.
"""

import csv
import datetime
import io
import os
import time
import zipfile
from pathlib import Path

import geopandas as gpd
import pandas as pd
import r5py


BASE = Path(os.environ.get("ACCESSIBILITY_DIR", "./accessibility-work"))
BG = os.environ.get("BLOCK_GROUPS_ZIP", str(BASE / "data/tl_2023_42_bg.zip"))
NETS = {
    "2025": (
        ["septa_2025_google_bus_clean.zip", "septa_2025_google_rail_clean.zip"],
        datetime.datetime(2025, 10, 15, 7, 0),  # noqa: DTZ001
    ),
    "2026": (
        ["septa_2026_google_bus_clean.zip", "septa_2026_google_rail_clean.zip"],
        datetime.datetime(2026, 10, 14, 7, 0),  # noqa: DTZ001
    ),
}


def metro_stops(gtfs):
    z = zipfile.ZipFile(BASE / "data/gtfs" / gtfs)

    def rd(name):
        return csv.DictReader(io.TextIOWrapper(z.open(name)))

    routes = {r["route_id"] for r in rd("routes.txt") if r["route_type"] == "1"}
    trips = {t["trip_id"] for t in rd("trips.txt") if t["route_id"] in routes}
    ids = {s["stop_id"] for s in rd("stop_times.txt") if s["trip_id"] in trips}
    rows = [s for s in rd("stops.txt") if s["stop_id"] in ids]
    return gpd.GeoDataFrame(
        {"id": [s["stop_id"] for s in rows]},
        geometry=gpd.points_from_xy(
            [float(s["stop_lon"]) for s in rows], [float(s["stop_lat"]) for s in rows]
        ),
        crs="EPSG:4326",
    )


bg = gpd.read_file(BG)
bg = bg[bg.COUNTYFP == "101"][["GEOID", "geometry"]]
bg["geometry"] = bg.to_crs("EPSG:5070").geometry.centroid.to_crs("EPSG:4326")
origins = bg.rename(columns={"GEOID": "id"}).reset_index(drop=True)

out = {}
for label, (gtfs, dep) in NETS.items():
    net = r5py.TransportNetwork(
        str(BASE / "data/pennsylvania.osm.pbf"), [str(BASE / "data/gtfs" / g) for g in gtfs]
    )
    t0 = time.time()
    m = r5py.TravelTimeMatrix(
        net,
        origins=origins,
        destinations=metro_stops(gtfs[0]),
        departure=dep,
        departure_time_window=datetime.timedelta(minutes=120),
        max_time=datetime.timedelta(minutes=90),
        transport_modes=[r5py.TransportMode.TRANSIT, r5py.TransportMode.WALK],
    )
    out[label] = m.groupby("from_id").travel_time.min().rename(label)
    print(f"{label}: {time.time()-t0:.0f}s, {len(out[label]):,} BGs reach a station", flush=True)

j = pd.concat(out.values(), axis=1).dropna()
j["delta"] = j["2026"] - j["2025"]
j.to_csv(BASE / "data/time_to_spine.csv")
print(
    f"\nmedian time to nearest Metro station: {j['2025'].median():.1f} -> {j['2026'].median():.1f} min"
)
print(f"mean {j['2025'].mean():.1f} -> {j['2026'].mean():.1f} min  (delta {j.delta.mean():+.2f})")
print(
    f"faster {int((j.delta<-0.5).sum()):,} | slower {int((j.delta>0.5).sum()):,} | same {int(j.delta.abs().le(0.5).sum()):,}"
)
