"""Jobs by employer (firm) size in Philadelphia, from Census LEHD LODES 2023 workplace data.

Run from the pipeline env (needs geopandas):
    python3 pipelines/septa_key_advantage/build_jobs_by_firm_size.py

Inputs (datasets/philadelphia/septa-key-advantage/raw/, from lehd.ces.census.gov/data/lodes/LODES8/pa/):
  pa_wac_S000_JT00_2023.csv.gz  all jobs by workplace block
  pa_wac_S000_JT02_2023.csv.gz  private jobs by workplace block, with firm size (CFS01-05)
  pa_xwalk.csv.gz               block centroids
Firm size is the size of the whole firm nationally, not the worksite: a chain store counts as 500+.

Outputs: district_jobs.csv, build/jobs_grid.geojson
"""

from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[2]
DATA = REPO / "datasets/philadelphia/septa-key-advantage"
ANALYSIS = REPO / "analyses/septa-key-advantage"
BUILD = Path(__file__).resolve().parent / "build"  # scratch output, not committed

RAW = DATA / "raw"
SIZES = {"CFS01": "0-19", "CFS02": "20-49", "CFS03": "50-249", "CFS04": "250-499", "CFS05": "500+"}
CELL_FT = 2000  # grid cell edge in EPSG:2272 feet


def read_wac(name: str, cols: list[str]) -> pd.DataFrame:
    df = pd.read_csv(RAW / name, dtype={"w_geocode": str}, usecols=["w_geocode", *cols])
    return df[df.w_geocode.str.startswith("42101")].set_index("w_geocode")


def main() -> None:
    allj = read_wac("pa_wac_S000_JT00_2023.csv.gz", ["C000"]).rename(columns={"C000": "jobs_all"})
    priv = read_wac("pa_wac_S000_JT02_2023.csv.gz", ["C000", *SIZES]).rename(columns={"C000": "jobs_private"})
    blocks = allj.join(priv, how="left").fillna(0)

    xw = pd.read_csv(RAW / "pa_xwalk.csv.gz", dtype={"tabblk2020": str}, usecols=["tabblk2020", "blklatdd", "blklondd"])
    xw = xw[xw.tabblk2020.str.startswith("42101")].set_index("tabblk2020")
    blocks = blocks.join(xw, how="left")
    assert blocks.blklatdd.notna().all(), "blocks missing centroids"

    pts = gpd.GeoDataFrame(blocks, geometry=gpd.points_from_xy(blocks.blklondd, blocks.blklatdd), crs=4326)
    districts = gpd.read_file(DATA / "districts.geojson")[["district", "geometry"]]
    pts = gpd.sjoin(pts, districts, how="left", predicate="within")
    # a handful of centroids on the river edge miss every polygon; snap them to the nearest district
    miss = pts.district.isna()
    if miss.any():
        near = gpd.sjoin_nearest(pts[miss].drop(columns=["district", "index_right"]).to_crs(2272), districts.to_crs(2272))
        pts.loc[miss, "district"] = near.district.values
    num = ["jobs_all", "jobs_private", *SIZES]
    by = pts.groupby("district")[num].sum().astype(int)
    by = by.loc[sorted(by.index, key=int)]
    by.loc["Total"] = by.sum()
    by.rename(columns={k: f"private_firm_{v}" for k, v in SIZES.items()}).to_csv(DATA / "district_jobs.csv")
    print(by)

    # Grid of private jobs by firm size, for the map
    g = pts.to_crs(2272)
    g["cx"] = (np.floor(g.geometry.x / CELL_FT) * CELL_FT).astype(int)
    g["cy"] = (np.floor(g.geometry.y / CELL_FT) * CELL_FT).astype(int)
    g["small"] = g.CFS01 + g.CFS02
    g["mid"] = g.CFS03 + g.CFS04
    g["large"] = g.CFS05
    cells = g.groupby(["cx", "cy"])[["jobs_all", "jobs_private", "small", "mid", "large"]].sum().reset_index()
    cells = cells[cells.jobs_all > 0]
    from shapely.geometry import box

    grid = gpd.GeoDataFrame(
        cells.drop(columns=["cx", "cy"]).astype(int),
        geometry=[box(x, y, x + CELL_FT, y + CELL_FT) for x, y in zip(cells.cx, cells.cy)],
        crs=2272,
    ).to_crs(4326)
    out = BUILD
    out.mkdir(parents=True, exist_ok=True)
    grid["geometry"] = grid.geometry.apply(lambda p: p.simplify(0))
    grid.to_file(out / "jobs_grid.geojson", driver="GeoJSON", COORDINATE_PRECISION=5)
    print(len(grid), "grid cells; small-firm jobs max", grid.small.max())


if __name__ == "__main__":
    main()
