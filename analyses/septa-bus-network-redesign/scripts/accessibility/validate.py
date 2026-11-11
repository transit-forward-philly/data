"""Validate our accessibility implementation against TransitCenter's published scores.

Runs every Philadelphia County block group for the WEDAM period of their
2024-03-04 vintage and compares jobs-within-45-minutes against their published
`C000_c45`, block group by block group.

Per-block-group comparison is the only meaningful test. Comparing our median
against their published county median is invalid unless we run every origin —
an unrepresentative origin sample shifts the median on its own, which is exactly
the trap a first pass here fell into.

Parameters mirror ted-data/ted/run.py:611-623:
  departure window 120 min, max_time 180 min, WALK + TRANSIT, median percentile.

Geometry mirrors theirs too: `centroid`, not `representative_point`. The two
diverge sharply on irregular block groups — airports, parks, riverfront — and
those were the largest outliers in the first pass.

Known remaining difference: our network is Pennsylvania OSM with SEPTA only.
Theirs spans PA/NJ/DE with PATCO, NJ Transit and DART, and drops "premium"
routes (for Philadelphia, most likely Regional Rail). Both omissions are
expected to show up as a modest, structured gap rather than noise.
"""

from __future__ import annotations

import datetime
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
GTFS = [
    BASE / "data/gtfs/septa_2024_google_bus_clean.zip",
    BASE / "data/gtfs/septa_2024_google_rail_clean.zip",
]
# TIGER block groups, keyless: www2.census.gov/geo/tiger/TIGER2023/BG/tl_2023_42_bg.zip
BG_ZIP = os.environ.get("BLOCK_GROUPS_ZIP", str(BASE / "data/tl_2023_42_bg.zip"))
THEIRS = Path(
    os.environ.get(
        "TRANSITCENTER_SCORES",
        str(BASE / "data/acs_PHL_20240304_WEDAM.csv"),
    )
)

# Naive local time on purpose: r5py interprets the departure in the GTFS
# agency timezone, so attaching tzinfo would shift it. ted-data does the same.
DEPARTURE = datetime.datetime(2024, 3, 6, 7, 0)  # noqa: DTZ001
DEPARTURE_WINDOW = datetime.timedelta(minutes=120)
MAX_TIME = datetime.timedelta(minutes=180)
THRESHOLD_MINUTES = 45


def log(message: str) -> None:
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024**3
    print(f"[{time.strftime('%H:%M:%S')}] {message} (peak {peak:.1f} GB)", flush=True)


def main() -> None:
    import r5py

    blocks = gpd.read_file(BG_ZIP)
    blocks = blocks[blocks.STATEFP == "42"][["GEOID", "geometry"]]
    # Their geometry choice, not ours — see module docstring.
    blocks["geometry"] = blocks.geometry.centroid
    blocks = blocks.rename(columns={"GEOID": "id"})

    jobs = pd.read_csv(BASE / "data/jobs_by_bg_2020.csv", dtype={"bgrp": str})
    destinations = blocks[blocks.id.isin(jobs.bgrp)].reset_index(drop=True)
    origins = blocks[blocks.id.str.startswith("42101")].reset_index(drop=True)
    log(f"{len(origins):,} origins x {len(destinations):,} destinations")

    log("building/loading network")
    network = r5py.TransportNetwork(str(OSM), [str(p) for p in GTFS])

    t0 = time.time()
    matrix = r5py.TravelTimeMatrix(
        network,
        origins=origins,
        destinations=destinations,
        departure=DEPARTURE,
        departure_time_window=DEPARTURE_WINDOW,
        max_time=MAX_TIME,
        transport_modes=[r5py.TransportMode.TRANSIT, r5py.TransportMode.WALK],
    )
    log(f"matrix done in {time.time() - t0:.0f}s -> {len(matrix):,} rows")
    matrix.to_parquet(BASE / "data/validation_matrix.parquet")

    jobs_map = jobs.set_index("bgrp").C000
    reached = matrix[matrix.travel_time <= THRESHOLD_MINUTES].copy()
    reached["jobs"] = reached.to_id.map(jobs_map).fillna(0)
    ours = reached.groupby("from_id").jobs.sum().rename("ours")

    theirs = pd.read_csv(THEIRS, dtype={"BG20": str}).set_index("BG20").C000_c45.rename("theirs")
    joined = pd.concat([ours, theirs], axis=1, join="inner")
    joined["ratio"] = joined.ours / joined.theirs.replace(0, pd.NA)
    joined.to_csv(BASE / "data/validation_comparison.csv")

    log(f"matched {len(joined):,} block groups")
    log(f"correlation           {joined.ours.corr(joined.theirs):.4f}")
    log(f"median ours / theirs  {joined.ratio.median():.3f}")
    log(f"county median ours    {joined.ours.median():,.0f}")
    log(f"county median theirs  {joined.theirs.median():,.0f}")
    within = joined.ratio.between(0.9, 1.1).mean() * 100
    log(f"within +/-10%         {within:.0f}% of block groups")


if __name__ == "__main__":
    main()
