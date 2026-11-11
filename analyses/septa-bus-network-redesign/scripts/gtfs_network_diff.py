"""Snapshot SEPTA GTFS releases and diff two networks by route and neighborhood.

Built for the bus network redesign that took effect 2026-08-23 (feed
v202608233), but the tooling is tag- and date-agnostic: point it at any two
SEPTA GTFS release tags and it produces a comparable before/after.

─── Why this exists ───────────────────────────────────────────────────

The main pipeline pulls septadev/GTFS releases/latest and overwrites its
outputs, so it keeps no history. "What changed?" is only answerable against an
archived feed. This script archives the release zips under
data/gtfs_snapshots/ and derives the comparison from them.

─── Two counting traps this script exists to avoid ────────────────────

1. SEASON, NOT NETWORK. SEPTA publishes summer and school-year feeds. A
   school-year feed carries ~26 extra 400-series "school tripper" routes
   (1-2 trips/week, weekdays only) that vanish every summer. Diffing a fall
   feed against a summer feed reports those trippers as a network expansion.
   Always compare school-year to school-year. The `low_trip_route` column
   flags the trippers so they can be excluded from headline numbers.

2. service_id SPLITTING. Totalling rows in trips.txt is not a service level.
   The two feeds split service into different numbers of service_ids, so raw
   trips.txt totals moved -24% across the 2026 redesign while actual service
   was flat. Every metric here is anchored to named calendar dates, resolved
   through calendar.txt plus calendar_dates.txt exceptions.

   This differs deliberately from the main pipeline's
   GTFSTransformer._identify_valid_service_patterns(), which picks
   representative weekday service_ids by greedy route coverage rather than by
   date. That heuristic is self-consistent within one feed but is not stable
   across feeds, which is exactly what a diff requires.

─── Metric definitions (per stop, per anchor date) ────────────────────

  departures                  departures at the stop on that date; a trip
                              serving 60 stops contributes 60 departures, so
                              this is never comparable to route-level `trips`
  routes                      distinct routes serving the stop
  <window>_departures         departures inside each --windows span
  <window>_avg_headway_mins   mean gap between consecutive departures in it
  max_headway_operating_mins  largest gap between consecutive departures during
                              operating hours (06:00-20:00, sub-minute intervals
                              discarded) — reproduces the shipped field of the
                              same name that drives tod_rail_bus_freq
  service_span_hours          first to last departure

Departures are not deduplicated across routes: two routes leaving a shared
stop in the same minute are two departures, matching the main transformer.

─── Output ────────────────────────────────────────────────────────────

  <out>/route_changes.csv          per route and day: trip delta, add/remove
  <out>/neighborhood_changes.csv   per neighborhood and day: stops, trips, headway
  <out>/stop_changes.csv           per stop and day: trips, headway, neighborhood
  <out>/summary.json               totals plus the run's provenance

Usage (run from the pipeline/ directory):

    python scripts/gtfs_network_diff.py \
        --baseline v202509141 --baseline-dates 20251015,20251018,20251019 \
        --current  v202608233 --current-dates  20261014,20261017,20261018

Date lists are positionally paired and must be the same length. Pair
equivalent non-holiday days: the script refuses a date outside a feed's
service span and warns when a pair falls on different weekdays.
"""

from __future__ import annotations

import argparse
import io
import json
import logging
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import requests
from shapely.geometry import Point


logger = logging.getLogger("gtfs_network_diff")

RELEASE_URL = "https://github.com/septadev/GTFS/releases/download/{tag}/gtfs_public.zip"
SNAPSHOT_DIR = Path("data/gtfs_snapshots")
NEIGHBORHOODS_PATH = Path("data/processed/geojson_cache/phila_neighborhoods.geojson")
NEIGHBORHOOD_FIELD = "MAPNAME"
OUTSIDE_LABEL = "Outside Philadelphia"

# GTFS route_type -> mode. SEPTA's Metro trolley lines (T1-T5) are type 0.
ROUTE_TYPE_MODES = {0: "trolley", 1: "metro", 2: "regionalRail", 3: "bus"}
BUS_METRO_SUBFEED = "google_bus"
RAIL_SUBFEED = "google_rail"

# Default analysis windows. Override with --windows to line up with an outside
# source: the TransitCenter Equity Dashboard, for instance, scores
# Wed 07:00-09:00, Wed 21:00-23:00 and Sat 10:00-12:00, and comparing our
# service numbers to its accessibility scores across different windows would be
# meaningless. Matching windows makes the two comparable in time-of-day; it does
# NOT make the metrics equivalent (departures and headway are not jobs reached).
DEFAULT_WINDOWS = "am=06:00-09:00,pm=15:00-19:00"

# max_headway_operating_mins is defined by the main transformer over 6 AM-8 PM
# (overnight service is not counted for TOD), discarding sub-minute intervals
# produced by several routes leaving a shared stop at once. Both constants are
# reproduced here so the diff is comparable to the shipped field.
OPERATING_HOURS = (6 * 3600, 20 * 3600)
MIN_REALISTIC_INTERVAL_MINS = 1.0

DOW = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

# A route running this few departures on its anchor day is a school tripper or
# similar special, not a network change. Flagged, never silently dropped.
LOW_TRIP_THRESHOLD = 5


class GTFSDiffError(Exception):
    """Raised when a feed cannot be snapshotted or an anchor date is invalid."""


@dataclass
class Feed:
    """One GTFS subfeed (SEPTA ships google_bus and google_rail separately)."""

    tag: str
    subfeed: str
    feed_version: str
    routes: pd.DataFrame
    trips: pd.DataFrame
    stops: pd.DataFrame
    stop_times: pd.DataFrame
    calendar: pd.DataFrame
    calendar_dates: pd.DataFrame

    def span(self) -> tuple[str, str]:
        """Return the feed's overall service span as (start_date, end_date)."""
        return str(self.calendar["start_date"].min()), str(self.calendar["end_date"].max())


# ─── Snapshot ──────────────────────────────────────────────────────────


def _download(url: str, dest: Path) -> None:
    """Stream `url` to `dest` via a temp file so a partial write is never kept."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    try:
        with requests.get(url, stream=True, timeout=180) as response:
            response.raise_for_status()
            with open(tmp, "wb") as fh:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        fh.write(chunk)
        tmp.replace(dest)
        # Guard against 200-with-HTML-body responses that raise_for_status misses.
        if not zipfile.is_zipfile(dest):
            dest.unlink(missing_ok=True)
            raise GTFSDiffError(f"Downloaded file is not a valid zip (HTML error page?): {url}")
    except GTFSDiffError:
        tmp.unlink(missing_ok=True)
        raise
    except Exception as exc:
        tmp.unlink(missing_ok=True)
        raise GTFSDiffError(f"Failed to download {url}: {exc}") from exc


def fetch_snapshot(tag: str, snapshot_dir: Path) -> Path:
    """Return the cached zip for a release tag, downloading it once if absent.

    Unlike the main pipeline's data/septa_gtfs.zip, caching by immutable
    release tag is safe: a tag's asset never changes, so a cache hit can never
    silently pin the wrong network.
    """
    dest = snapshot_dir / f"{tag}.zip"
    if dest.exists() and zipfile.is_zipfile(dest):
        logger.info(f"Snapshot cached: {dest}")
        return dest
    logger.info(f"Downloading snapshot {tag}")
    _download(RELEASE_URL.format(tag=tag), dest)
    logger.info(f"Saved {dest} ({dest.stat().st_size / 1024 / 1024:.1f} MB)")
    return dest


def load_feed(zip_path: Path, tag: str, subfeed: str) -> Feed:
    """Read one nested subfeed out of a SEPTA release zip into DataFrames."""
    with zipfile.ZipFile(zip_path) as outer:
        nested_name = f"{subfeed}.zip"
        if nested_name not in outer.namelist():
            raise GTFSDiffError(f"{zip_path} has no {nested_name} (has: {outer.namelist()})")
        nested_bytes = io.BytesIO(outer.read(nested_name))

    with zipfile.ZipFile(nested_bytes) as inner:

        def read(name: str, **kwargs) -> pd.DataFrame:
            if name not in inner.namelist():
                return pd.DataFrame()
            with inner.open(name) as fh:
                return pd.read_csv(fh, **kwargs)

        feed_info = read("feed_info.txt", dtype=str)
        version = (
            str(feed_info.iloc[0]["feed_version"])
            if not feed_info.empty and "feed_version" in feed_info.columns
            else tag
        )
        return Feed(
            tag=tag,
            subfeed=subfeed,
            feed_version=version,
            routes=read("routes.txt", dtype=str),
            trips=read(
                "trips.txt", dtype=str, usecols=lambda c: c in {"route_id", "service_id", "trip_id"}
            ),
            stops=read("stops.txt", dtype=str),
            stop_times=read(
                "stop_times.txt",
                dtype=str,
                usecols=lambda c: c in {"trip_id", "stop_id", "departure_time"},
            ),
            calendar=read("calendar.txt", dtype=str),
            calendar_dates=read("calendar_dates.txt", dtype=str),
        )


# ─── Date-anchored service resolution ──────────────────────────────────


def active_services(feed: Feed, datestr: str) -> set[str]:
    """Resolve the set of service_ids running on `datestr` (YYYYMMDD).

    Applies calendar.txt weekday flags within the service window, then layers
    calendar_dates.txt exceptions (type 1 adds, type 2 removes).
    """
    day = datetime.strptime(datestr, "%Y%m%d").date()
    weekday = DOW[day.weekday()]

    cal = feed.calendar
    in_window = (cal["start_date"] <= datestr) & (cal["end_date"] >= datestr)
    runs_today = cal[weekday] == "1"
    active = set(cal.loc[in_window & runs_today, "service_id"])

    cd = feed.calendar_dates
    if not cd.empty:
        today = cd[cd["date"] == datestr]
        active |= set(today.loc[today["exception_type"] == "1", "service_id"])
        active -= set(today.loc[today["exception_type"] == "2", "service_id"])

    if not active:
        raise GTFSDiffError(
            f"{feed.tag}/{feed.subfeed}: no service on {datestr} "
            f"(feed span {feed.span()[0]}-{feed.span()[1]})"
        )
    return active


def gtfs_time_to_seconds(series: pd.Series) -> pd.Series:
    """Vectorized HH:MM:SS -> seconds, tolerating GTFS hours past 24."""
    parts = series.str.strip().str.split(":", expand=True)
    if parts.shape[1] < 3:
        return pd.Series(np.nan, index=series.index)
    return (
        pd.to_numeric(parts[0], errors="coerce") * 3600
        + pd.to_numeric(parts[1], errors="coerce") * 60
        + pd.to_numeric(parts[2], errors="coerce")
    )


def day_departures(feed: Feed, datestr: str, modes: set[str]) -> pd.DataFrame:
    """Return every departure on `datestr` for routes in `modes`.

    Columns: stop_id, route_id, route_key, dep (seconds since midnight).
    """
    services = active_services(feed, datestr)

    routes = feed.routes.copy()
    routes["route_type_int"] = pd.to_numeric(routes["route_type"], errors="coerce")
    routes["mode"] = routes["route_type_int"].map(ROUTE_TYPE_MODES)
    routes = routes[routes["mode"].isin(modes)]
    if routes.empty:
        raise GTFSDiffError(f"{feed.tag}/{feed.subfeed}: no routes matching modes {sorted(modes)}")

    trips = feed.trips[
        feed.trips["service_id"].isin(services) & feed.trips["route_id"].isin(routes["route_id"])
    ]
    departures = feed.stop_times.merge(trips[["trip_id", "route_id"]], on="trip_id", how="inner")
    departures["dep"] = gtfs_time_to_seconds(departures["departure_time"])
    departures = departures[departures["dep"].notna()]

    # route_key is the rider-facing identity and the only stable join key across
    # feeds; SEPTA reuses route_ids for renamed services.
    routes["route_key"] = routes["route_short_name"].fillna("").replace("", np.nan)
    routes["route_key"] = routes["route_key"].fillna(routes["route_id"])
    return departures.merge(
        routes[["route_id", "route_key", "route_long_name", "mode"]], on="route_id", how="left"
    )


# ─── Metrics ───────────────────────────────────────────────────────────


def _gaps_by_group(frame: pd.DataFrame, group: str, value: str) -> pd.Series:
    """Minute gaps between consecutive `value`s within each `group`.

    The first departure of each group has no predecessor and yields NaN.
    """
    ordered = frame.sort_values([group, value])
    gap = ordered[value].diff() / 60.0
    gap[ordered[group] != ordered[group].shift()] = np.nan
    return gap.set_axis(ordered.index).reindex(frame.index)


def max_headway_operating(frame: pd.DataFrame) -> pd.Series:
    """Longest gap between departures during operating hours, per stop.

    Reproduces GTFSTransformer._calculate_stop_frequency_metrics: restrict to
    6 AM-8 PM, drop intervals under a minute (simultaneous arrivals by several
    routes at a shared stop), and fall back to the largest raw interval when
    every interval is sub-minute. A stop with fewer than two operating-hours
    departures scores 0, matching the shipped field.
    """
    start, end = OPERATING_HOURS
    window = frame[(frame["dep"] >= start) & (frame["dep"] < end)].copy()
    window["gap"] = _gaps_by_group(window, "stop_id", "dep")

    all_gaps = window.groupby("stop_id")["gap"].max()
    realistic = window[window["gap"] >= MIN_REALISTIC_INTERVAL_MINS].groupby("stop_id")["gap"].max()
    return realistic.reindex(all_gaps.index).fillna(all_gaps).fillna(0).round(1)


def stop_metrics(departures: pd.DataFrame, windows: dict[str, tuple[int, int]]) -> pd.DataFrame:
    """Per-stop service metrics for one anchor day.

    Emits `<name>_departures` and `<name>_avg_headway_mins` per configured
    window, so the columns follow --windows rather than a fixed AM/PM pair.
    """
    frame = departures.copy()

    grouped = frame.groupby("stop_id")
    metrics = pd.DataFrame(
        {
            "departures": grouped.size(),
            "routes": grouped["route_key"].nunique(),
            "service_span_hours": ((grouped["dep"].max() - grouped["dep"].min()) / 3600).round(1),
        }
    )
    metrics["max_headway_operating_mins"] = max_headway_operating(frame).reindex(metrics.index)

    count_columns = []
    for label, (start, end) in windows.items():
        window = frame[(frame["dep"] >= start) & (frame["dep"] < end)].copy()
        metrics[f"{label}_departures"] = window.groupby("stop_id").size()
        count_columns.append(f"{label}_departures")
        window["gap"] = _gaps_by_group(window, "stop_id", "dep")
        metrics[f"{label}_avg_headway_mins"] = window.groupby("stop_id")["gap"].mean().round(1)

    metrics[count_columns] = metrics[count_columns].fillna(0).astype(int)
    return metrics.reset_index()


def route_metrics(departures: pd.DataFrame) -> pd.DataFrame:
    """Per-route trip and stop counts for one anchor day."""
    # A "trip" is a distinct trip_id, not a departure row (one trip touches
    # many stops), so route-level and stop-level totals are not comparable.
    grouped = departures.groupby("route_key")
    return pd.DataFrame(
        {
            "trips": grouped["trip_id"].nunique(),
            "stops_served": grouped["stop_id"].nunique(),
            "route_long_name": grouped["route_long_name"].first(),
            "mode": grouped["mode"].first(),
        }
    ).reset_index()


# ─── Spatial ───────────────────────────────────────────────────────────


def load_neighborhoods(path: Path) -> gpd.GeoDataFrame:
    """Load neighborhood polygons in WGS84."""
    if not path.exists():
        raise GTFSDiffError(
            f"Neighborhoods not found at {path}. Run from the analysis folder, "
            "or refresh the geojson cache."
        )
    gdf = gpd.read_file(path)[[NEIGHBORHOOD_FIELD, "geometry"]]
    return gdf.to_crs("EPSG:4326") if gdf.crs else gdf.set_crs("EPSG:4326")


def attach_neighborhoods(stops: pd.DataFrame, neighborhoods: gpd.GeoDataFrame) -> pd.DataFrame:
    """Point-in-polygon each stop to its neighborhood.

    Stops are points, so unlike the parcel joins they land in one polygon;
    where neighborhood polygons overlap the matches are aggregated to a
    comma-separated value rather than dropped, matching the pipeline
    convention. Stops outside the city are labelled, never discarded.
    """
    points = gpd.GeoDataFrame(
        stops.copy(),
        geometry=[
            Point(lon, lat)
            for lon, lat in zip(
                pd.to_numeric(stops["stop_lon"], errors="coerce"),
                pd.to_numeric(stops["stop_lat"], errors="coerce"),
                strict=True,
            )
        ],
        crs="EPSG:4326",
    )
    joined = gpd.sjoin(points, neighborhoods, how="left", predicate="intersects")

    names = (
        joined.groupby(joined.index)[NEIGHBORHOOD_FIELD]
        .agg(lambda vals: ", ".join(sorted({str(v) for v in vals if pd.notna(v)})))
        .replace("", OUTSIDE_LABEL)
    )
    out = stops.copy()
    out["neighborhood"] = names.reindex(out.index).fillna(OUTSIDE_LABEL)
    return out


# ─── Diff ──────────────────────────────────────────────────────────────


def _delta(frame: pd.DataFrame, column: str) -> pd.DataFrame:
    """Add `<column>_delta` from the `_before`/`_after` pair."""
    frame[f"{column}_delta"] = frame[f"{column}_after"] - frame[f"{column}_before"]
    return frame


def diff_routes(before: pd.DataFrame, after: pd.DataFrame, day: str) -> pd.DataFrame:
    """Route-level before/after with an added/removed/retained status."""
    merged = before.merge(after, on="route_key", how="outer", suffixes=("_before", "_after"))
    merged["day"] = day
    merged["status"] = np.select(
        [merged["trips_before"].isna(), merged["trips_after"].isna()],
        ["added", "removed"],
        default="retained",
    )
    for column in ("trips", "stops_served"):
        merged[[f"{column}_before", f"{column}_after"]] = merged[
            [f"{column}_before", f"{column}_after"]
        ].fillna(0)
        merged = _delta(merged, column)

    merged["renamed"] = (
        merged["route_long_name_before"].notna()
        & merged["route_long_name_after"].notna()
        & (merged["route_long_name_before"] != merged["route_long_name_after"])
    )
    merged["low_trip_route"] = (
        merged[["trips_before", "trips_after"]].max(axis=1) <= LOW_TRIP_THRESHOLD
    )
    return merged.sort_values(["day", "trips_delta"])


def diff_neighborhoods(
    before: pd.DataFrame, after: pd.DataFrame, day: str, windows: list[str]
) -> pd.DataFrame:
    """Aggregate stop metrics to neighborhoods and diff them."""

    def rollup(stops: pd.DataFrame) -> pd.DataFrame:
        grouped = stops.groupby("neighborhood")
        return pd.DataFrame(
            {
                "stops": grouped.size(),
                "departures": grouped["departures"].sum(),
                **{f"{w}_departures": grouped[f"{w}_departures"].sum() for w in windows},
                "median_max_headway_mins": grouped["max_headway_operating_mins"].median().round(1),
                "stops_under_15min": grouped["max_headway_operating_mins"]
                .apply(lambda s: int((s <= 15).sum()))
                .astype(int),
            }
        )

    merged = rollup(before).join(rollup(after), how="outer", lsuffix="_before", rsuffix="_after")
    numeric = ["stops", "departures", "stops_under_15min"] + [f"{w}_departures" for w in windows]
    for column in numeric:
        merged[[f"{column}_before", f"{column}_after"]] = merged[
            [f"{column}_before", f"{column}_after"]
        ].fillna(0)
        merged = _delta(merged, column)
    merged = _delta(merged, "median_max_headway_mins")
    merged["day"] = day
    return merged.reset_index().sort_values(["day", "departures_delta"])


def diff_stops(
    before: pd.DataFrame, after: pd.DataFrame, day: str, windows: list[str]
) -> pd.DataFrame:
    """Stop-level before/after, keyed on stop_id."""
    merged = before.merge(after, on="stop_id", how="outer", suffixes=("_before", "_after"))
    merged["day"] = day
    merged["neighborhood"] = merged["neighborhood_after"].fillna(merged["neighborhood_before"])
    merged["stop_name"] = merged["stop_name_after"].fillna(merged["stop_name_before"])
    merged["status"] = np.select(
        [merged["departures_before"].isna(), merged["departures_after"].isna()],
        ["added", "removed"],
        default="retained",
    )
    for column in ["departures", "routes"] + [f"{w}_departures" for w in windows]:
        merged[[f"{column}_before", f"{column}_after"]] = merged[
            [f"{column}_before", f"{column}_after"]
        ].fillna(0)
        merged = _delta(merged, column)
    merged = _delta(merged, "max_headway_operating_mins")
    for window in windows:
        merged = _delta(merged, f"{window}_avg_headway_mins")
    keep = [
        "day",
        "stop_id",
        "stop_name",
        "neighborhood",
        "status",
        "departures_before",
        "departures_after",
        "departures_delta",
        "routes_before",
        "routes_after",
        "routes_delta",
        "max_headway_operating_mins_before",
        "max_headway_operating_mins_after",
        "max_headway_operating_mins_delta",
    ]
    for window in windows:
        keep += [
            f"{window}_departures_delta",
            f"{window}_avg_headway_mins_before",
            f"{window}_avg_headway_mins_after",
            f"{window}_avg_headway_mins_delta",
        ]
    return merged[keep].sort_values(["day", "departures_delta"])


# ─── Orchestration ─────────────────────────────────────────────────────


def build_day(
    feed: Feed,
    datestr: str,
    modes: set[str],
    neighborhoods: gpd.GeoDataFrame,
    windows: dict[str, tuple[int, int]],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (stop metrics with neighborhood, route metrics) for one day."""
    departures = day_departures(feed, datestr, modes)
    stops = stop_metrics(departures, windows)
    stops = stops.merge(
        feed.stops[["stop_id", "stop_name", "stop_lat", "stop_lon"]], on="stop_id", how="left"
    )
    stops = attach_neighborhoods(stops, neighborhoods)
    return stops, route_metrics(departures)


def _window_time_to_seconds(text: str, context: str) -> int:
    """HH:MM -> seconds. `context` names the window for the error message."""
    try:
        hours, minutes = (int(part) for part in text.strip().split(":"))
    except ValueError as exc:
        raise GTFSDiffError(f"Bad time {text!r} in window {context!r}") from exc
    return hours * 3600 + minutes * 60


def parse_windows(spec: str) -> dict[str, tuple[int, int]]:
    """Parse "name=HH:MM-HH:MM,..." into {name: (start_sec, end_sec)}.

    End times past midnight are allowed (GTFS counts service hours past 24), so
    a window may legitimately end beyond 86400.
    """
    windows: dict[str, tuple[int, int]] = {}
    for chunk in (c.strip() for c in spec.split(",") if c.strip()):
        if "=" not in chunk or "-" not in chunk:
            raise GTFSDiffError(f"Bad window {chunk!r}; expected name=HH:MM-HH:MM")
        name, span = chunk.split("=", 1)
        start_text, end_text = span.split("-", 1)
        start = _window_time_to_seconds(start_text, chunk)
        end = _window_time_to_seconds(end_text, chunk)
        if end <= start:
            raise GTFSDiffError(f"Window {chunk!r} ends at or before it starts")
        windows[name.strip()] = (start, end)
    if not windows:
        raise GTFSDiffError(f"No windows parsed from {spec!r}")
    return windows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--baseline", required=True, help="Baseline release tag, e.g. v202509141")
    parser.add_argument("--current", required=True, help="Current release tag, e.g. v202608233")
    parser.add_argument(
        "--baseline-dates", required=True, help="Comma-separated YYYYMMDD anchor dates"
    )
    parser.add_argument(
        "--current-dates", required=True, help="Comma-separated YYYYMMDD anchor dates"
    )
    parser.add_argument(
        "--modes",
        default="bus",
        help="Comma-separated modes to include: bus,trolley,metro,regionalRail (default: bus)",
    )
    parser.add_argument(
        "--subfeed",
        default=BUS_METRO_SUBFEED,
        choices=[BUS_METRO_SUBFEED, RAIL_SUBFEED],
        help=f"Which nested feed to read (default: {BUS_METRO_SUBFEED})",
    )
    parser.add_argument(
        "--windows",
        default=DEFAULT_WINDOWS,
        help=(
            "Comma-separated name=HH:MM-HH:MM analysis windows "
            f"(default: {DEFAULT_WINDOWS}). To match the TransitCenter dashboard: "
            "'wedam=07:00-09:00,wedpm=21:00-23:00' with a Saturday anchor for "
            "'satam=10:00-12:00'."
        ),
    )
    parser.add_argument("--snapshot-dir", type=Path, default=SNAPSHOT_DIR)
    parser.add_argument("--out", type=Path, default=Path("data/processed/gtfs_network_diff"))
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = parse_args()

    baseline_dates = [d.strip() for d in args.baseline_dates.split(",") if d.strip()]
    current_dates = [d.strip() for d in args.current_dates.split(",") if d.strip()]
    if len(baseline_dates) != len(current_dates):
        raise GTFSDiffError(
            f"--baseline-dates has {len(baseline_dates)} entries but "
            f"--current-dates has {len(current_dates)}; they are paired positionally"
        )
    windows = parse_windows(args.windows)
    modes = {m.strip() for m in args.modes.split(",") if m.strip()}
    unknown = modes - set(ROUTE_TYPE_MODES.values())
    if unknown:
        raise GTFSDiffError(f"Unknown mode(s): {sorted(unknown)}")

    args.snapshot_dir.mkdir(parents=True, exist_ok=True)
    args.out.mkdir(parents=True, exist_ok=True)

    baseline_feed = load_feed(
        fetch_snapshot(args.baseline, args.snapshot_dir), args.baseline, args.subfeed
    )
    current_feed = load_feed(
        fetch_snapshot(args.current, args.snapshot_dir), args.current, args.subfeed
    )
    logger.info(
        f"baseline {baseline_feed.feed_version} span {baseline_feed.span()} | "
        f"current {current_feed.feed_version} span {current_feed.span()}"
    )

    neighborhoods = load_neighborhoods(NEIGHBORHOODS_PATH)

    route_frames, neighborhood_frames, stop_frames, summary_days = [], [], [], []
    for before_date, after_date in zip(baseline_dates, current_dates, strict=True):
        before_day = datetime.strptime(before_date, "%Y%m%d").date()
        after_day = datetime.strptime(after_date, "%Y%m%d").date()
        if before_day.weekday() != after_day.weekday():
            logger.warning(
                f"Anchor pair {before_date}/{after_date} spans different weekdays "
                f"({DOW[before_day.weekday()]} vs {DOW[after_day.weekday()]}); "
                "service levels will not be comparable"
            )
        label = DOW[after_day.weekday()]
        logger.info(f"Building {label}: {before_date} -> {after_date}")

        before_stops, before_routes = build_day(
            baseline_feed, before_date, modes, neighborhoods, windows
        )
        after_stops, after_routes = build_day(
            current_feed, after_date, modes, neighborhoods, windows
        )

        window_names = list(windows)
        route_frames.append(diff_routes(before_routes, after_routes, label))
        neighborhood_frames.append(
            diff_neighborhoods(before_stops, after_stops, label, window_names)
        )
        stop_frames.append(diff_stops(before_stops, after_stops, label, window_names))
        summary_days.append(
            {
                "day": label,
                "baseline_date": before_date,
                "current_date": after_date,
                "trips_before": int(before_routes["trips"].sum()),
                "trips_after": int(after_routes["trips"].sum()),
                "routes_before": int(len(before_routes)),
                "routes_after": int(len(after_routes)),
                "stops_before": int(len(before_stops)),
                "stops_after": int(len(after_stops)),
            }
        )

    outputs = {
        "route_changes.csv": pd.concat(route_frames, ignore_index=True),
        "neighborhood_changes.csv": pd.concat(neighborhood_frames, ignore_index=True),
        "stop_changes.csv": pd.concat(stop_frames, ignore_index=True),
    }
    for name, frame in outputs.items():
        frame.to_csv(args.out / name, index=False)
        logger.info(f"Wrote {args.out / name} ({len(frame):,} rows)")

    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "baseline": {
            "tag": args.baseline,
            "feed_version": baseline_feed.feed_version,
            "span": baseline_feed.span(),
        },
        "current": {
            "tag": args.current,
            "feed_version": current_feed.feed_version,
            "span": current_feed.span(),
        },
        "modes": sorted(modes),
        "subfeed": args.subfeed,
        "windows": {name: list(span) for name, span in windows.items()},
        "days": summary_days,
    }
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2))
    logger.info(f"Wrote {args.out / 'summary.json'}")


if __name__ == "__main__":
    main()
