"""Score jobs accessibility before and after SEPTA's 2026 bus network redesign.

Runs the validated TransitCenter method across two archived networks and reports
the change in jobs reachable by transit from every Philadelphia County block
group.

This is the question schedule data cannot answer. Departures and headways say
service moved from job-rich areas toward job-poor ones; only routing says
whether total reach rose or fell.

─── Why the absolute level matters less than it looks ─────────────────

Validated against TransitCenter's published 2024 scores at correlation 0.986,
median ratio 0.987. Two known differences remain and pull in opposite
directions: our network omits NJ/DE and their operators (pulls us low), and
includes Regional Rail which their "premium route" filter probably drops (pulls
us high).

For a BEFORE/AFTER comparison that mostly cancels. Both networks are scored with
identical geography, identical parameters and identical job data, so the DELTA
is sound even where the absolute level sits a couple of percent off theirs. Do
not quote our absolute figures as TransitCenter numbers; do quote the change.

Parameters mirror ted-data/ted/run.py:611-623.

Runtime: each network builds in ~2.4 h (cached afterwards) and each matrix takes
~45 min, so a cold run of both is roughly 6.5 hours. Never interrupt a build —
a killed build leaves a corrupt mapdb that fails later as a checksum error.
"""

from __future__ import annotations

import datetime
import json
import os
import resource
import time
from pathlib import Path

import geopandas as gpd
import pandas as pd


# Working directory holding the OSM extract, GTFS, jobs table and R5 caches.
# Externalised deliberately: ted-data hardcodes an author's home directory and
# is unrunnable by anyone else as a result.
BASE = Path(os.environ.get("ACCESSIBILITY_DIR", "./accessibility-work"))
OSM = BASE / "data/pennsylvania.osm.pbf"
# TIGER block groups, keyless: www2.census.gov/geo/tiger/TIGER2023/BG/tl_2023_42_bg.zip
BG_ZIP = os.environ.get("BLOCK_GROUPS_ZIP", str(BASE / "data/tl_2023_42_bg.zip"))

# Anchor Wednesdays matching the schedule-side analysis, at their WEDAM hour.
# Naive local times on purpose — see DEPARTURE note in validate.py.
NETWORKS = {
    "2025": {
        "gtfs": ["septa_2025_google_bus_clean.zip", "septa_2025_google_rail_clean.zip"],
        "departure": datetime.datetime(2025, 10, 15, 7, 0),  # noqa: DTZ001
    },
    "2026": {
        "gtfs": ["septa_2026_google_bus_clean.zip", "septa_2026_google_rail_clean.zip"],
        "departure": datetime.datetime(2026, 10, 14, 7, 0),  # noqa: DTZ001
    },
}

DEPARTURE_WINDOW = datetime.timedelta(minutes=120)
MAX_TIME = datetime.timedelta(minutes=180)
THRESHOLDS = [30, 45, 60]


def log(message: str) -> None:
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024**3
    print(f"[{time.strftime('%H:%M:%S')}] {message} (peak {peak:.1f} GB)", flush=True)


def load_geographies() -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, pd.Series]:
    blocks = gpd.read_file(BG_ZIP)
    blocks = blocks[blocks.STATEFP == "42"][["GEOID", "geometry"]]
    # Projected before taking centroids — geopandas warns (correctly) that
    # centroids of geographic coordinates are approximate.
    blocks["geometry"] = blocks.to_crs("EPSG:5070").geometry.centroid.to_crs("EPSG:4326")
    blocks = blocks.rename(columns={"GEOID": "id"})

    jobs = pd.read_csv(BASE / "data/jobs_by_bg_2020.csv", dtype={"bgrp": str})
    destinations = blocks[blocks.id.isin(jobs.bgrp)].reset_index(drop=True)
    origins = blocks[blocks.id.str.startswith("42101")].reset_index(drop=True)
    return origins, destinations, jobs.set_index("bgrp").C000


def score(label: str, config: dict, origins, destinations, jobs_map) -> pd.DataFrame:
    import r5py

    log(f"{label}: building/loading network")
    network = r5py.TransportNetwork(
        str(OSM), [str(BASE / "data/gtfs" / name) for name in config["gtfs"]]
    )

    t0 = time.time()
    log(f"{label}: matrix {len(origins):,} x {len(destinations):,}")
    matrix = r5py.TravelTimeMatrix(
        network,
        origins=origins,
        destinations=destinations,
        departure=config["departure"],
        departure_time_window=DEPARTURE_WINDOW,
        max_time=MAX_TIME,
        transport_modes=[r5py.TransportMode.TRANSIT, r5py.TransportMode.WALK],
    )
    log(f"{label}: matrix done in {time.time() - t0:.0f}s -> {len(matrix):,} rows")
    matrix.to_parquet(BASE / f"data/matrix_{label}.parquet")

    matrix = matrix.assign(jobs=matrix.to_id.map(jobs_map).fillna(0))
    out = pd.DataFrame(index=origins.id).rename_axis("GEOID")
    for minutes in THRESHOLDS:
        reached = matrix[matrix.travel_time <= minutes]
        out[f"jobs_{minutes}"] = reached.groupby("from_id").jobs.sum()
    return out.fillna(0)


def main() -> None:
    origins, destinations, jobs_map = load_geographies()
    log(f"{len(origins):,} origins x {len(destinations):,} destinations")

    results = {
        label: score(label, config, origins, destinations, jobs_map)
        for label, config in NETWORKS.items()
    }

    before, after = results["2025"], results["2026"]
    combined = before.join(after, lsuffix="_before", rsuffix="_after")
    for minutes in THRESHOLDS:
        b, a = f"jobs_{minutes}_before", f"jobs_{minutes}_after"
        combined[f"delta_{minutes}"] = combined[a] - combined[b]
    combined.to_csv(BASE / "data/redesign_accessibility.csv")

    summary = {"generated_at": datetime.datetime.now().isoformat(timespec="seconds")}
    for minutes in THRESHOLDS:
        b, a = f"jobs_{minutes}_before", f"jobs_{minutes}_after"
        delta = combined[f"delta_{minutes}"]
        summary[f"{minutes}min"] = {
            "median_before": int(combined[b].median()),
            "median_after": int(combined[a].median()),
            "mean_change_pct": round((combined[a].sum() / combined[b].sum() - 1) * 100, 2),
            "block_groups_better": int((delta > 0).sum()),
            "block_groups_worse": int((delta < 0).sum()),
        }
        log(
            f"{minutes}min: median {summary[f'{minutes}min']['median_before']:,} -> "
            f"{summary[f'{minutes}min']['median_after']:,} | "
            f"total {summary[f'{minutes}min']['mean_change_pct']:+.2f}% | "
            f"better {summary[f'{minutes}min']['block_groups_better']:,} "
            f"worse {summary[f'{minutes}min']['block_groups_worse']:,}"
        )
    (BASE / "data/redesign_accessibility_summary.json").write_text(json.dumps(summary, indent=2))
    log("wrote redesign_accessibility.csv + summary.json")


if __name__ == "__main__":
    main()
