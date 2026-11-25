"""Summarize the Accelerate station data by PA House, PA Senate and Philadelphia Council district.

Usage:
    python build_district_summary.py [OUTPUT_CSV]   (defaults to the district summary in OUT_DIR)

Reads only files already in this repo (no downloads), relative to the repo root:
    datasets/septa-region/septa-accelerate-station-service/septa-accelerate-stations.csv
    datasets/septa-region/septa-accelerate-station-service/septa-accelerate-trolley-stops-by-district.csv
    datasets/septa-region/septa-accelerate-station-service/septa-accelerate-plan-projects.csv
    datasets/septa-region/septa-bus-routes/septa-bus-routes.csv
    datasets/septa-region/septa-accelerate-station-service/septa-frequent-transit-coverage-by-district.csv
        (two population shares, copied as they are; a warning goes to stderr if the file is missing or its
        districts do not match this file's rows)
    datasets/septa-region/septa-regional-rail-stations/septa-regional-rail-stations.csv
        (Weekday_Total_Boards, matched on stop_id)
    datasets/pennsylvania/legislators-2025-2026/records/
    datasets/pennsylvania/election-2026-results/records/
    datasets/pennsylvania/transportation-votes/member-votes.csv
        (HB 1788 House final passage, Aug 11 2025; HB 257 Senate final passage, Aug 12 2025)

Run build.py, build_plan_projects.py, ../septa_bus_routes/build.py and build_frequent_coverage.py first; this script
reads their output. (build_frequent_coverage.py reads the district list from this file, so on a first build
run this once, then build_frequent_coverage.py, then this again.)

Counts only. Nothing is scored or ranked.
"""

import csv
import json
import sys
import tomllib
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "datasets"
OUT_DIR = D / "septa-region/septa-accelerate-station-service"

# The transit funding final passage vote in each chamber, 2025-26 session.
FUNDING_VOTE = {"house": "hb1788-final", "senate": "hb257-final"}

# Every House and Senate district with at least half its population in SEPTA's five Pennsylvania counties
# gets a row, even with no station or trolley stop, so no district in the region is silently left out.
REGION = {"Philadelphia", "Bucks", "Chester", "Delaware", "Montgomery"}

COLUMNS = [
    "chamber", "district",
    "member_2025_26", "party_2025_26", "seat_2026_status", "winner_2026", "winner_party_2026",
    "transit_funding_vote_bill", "transit_funding_vote_2025_26", "transit_funding_vote_pro_transit",
    "regional_rail_stations", "rr_15_min", "rr_30_min", "rr_60_min", "rr_frequency_not_specified",
    "metro_stations", "accessibility_rebuilds", "accessible_today_unknown",
    "trolley_routes", "trolley_stops",
    "fy27_named_projects", "fy27_named_projects_millions",
    "plan_projects", "plan_project_names",
    "bus_routes", "frequent_bus_routes", "frequent_bus_route_names",
    "share_near_frequent_bus", "share_near_frequent_transit_incl_rr15_plan",
    "rr_weekday_boardings", "rr_weekday_boardings_at_15_min_stations", "rr_stations_without_boardings",
    "near_boundary_stations",
]


def records(path):
    return {p.stem: tomllib.loads(p.read_text()) for p in sorted(path.glob("*.toml"))}


def main(out_path):
    stations = list(csv.DictReader(open(OUT_DIR / "septa-accelerate-stations.csv", encoding="utf-8")))
    trolley = list(csv.DictReader(open(OUT_DIR / "septa-accelerate-trolley-stops-by-district.csv", encoding="utf-8")))

    # SEPTA's station layer has one row per station per line; North Philadelphia appears twice with the
    # same count, so take the max per stop_id rather than summing.
    boards = {}
    for r in csv.DictReader(open(D / "septa-region/septa-regional-rail-stations/septa-regional-rail-stations.csv", encoding="utf-8")):
        v = r["Weekday_Total_Boards"].strip()
        if v:
            boards[r["Stop_ID"]] = max(boards.get(r["Stop_ID"], 0), int(float(v)))

    legs = {ch: records(D / f"pennsylvania/legislators-2025-2026/records/{ch}") for ch in ("house", "senate")}
    results = {ch: records(D / f"pennsylvania/election-2026-results/records/{ch}") for ch in ("house", "senate")}
    roll = {k: tomllib.loads((D / f"pennsylvania/transportation-votes/roll-calls/{k}.toml").read_text()) for k in FUNDING_VOTE.values()}
    PRO = {"Yea": "Y", "Nay": "N"}
    votes = {ch: {} for ch in FUNDING_VOTE}
    for r in csv.DictReader(open(D / "pennsylvania/transportation-votes/member-votes.csv", encoding="utf-8")):
        if FUNDING_VOTE.get(r["chamber"]) == r["vote_key"]:
            votes[r["chamber"]][r["district"]] = r

    cost = {r["project"]: float(r["total_cost_millions"])
            for r in csv.DictReader(open(OUT_DIR / "fy27-named-station-projects.csv", encoding="utf-8"))}

    # Named Accelerate plan projects placed at a site (not systemwide, not already counted by station or route).
    plan = defaultdict(list)
    for r in csv.DictReader(open(OUT_DIR / "septa-accelerate-plan-projects.csv", encoding="utf-8")):
        for ch in ("house", "senate", "council"):
            for d in filter(None, (x.strip() for x in r[f"{ch}_districts"].split(";"))):
                plan[(ch, d)].append(r["name"])

    # Bus routes whose GTFS shapes cross the district; "frequent" is SEPTA's weekday Frequent Red network.
    # Regular routes only: school trippers, overnight, rail replacement and no-trip routes are left out.
    bus, fbus = defaultdict(set), defaultdict(list)
    for r in csv.DictReader(open(D / "septa-region/septa-bus-routes/septa-bus-routes.csv", encoding="utf-8")):
        if r["service_kind"] != "regular":
            continue
        for ch in ("house", "senate", "council"):
            for d in filter(None, (x.strip() for x in r[f"{ch}_districts"].split(";"))):
                bus[(ch, d)].add(r["route"])
                if r["septa_frequent_weekday"] == "true":
                    fbus[(ch, d)].append(r["route"])

    # Residents within a quarter mile of frequent service, from build_frequent_coverage.py.
    coverage = {}
    cov_path = OUT_DIR / "septa-frequent-transit-coverage-by-district.csv"
    if cov_path.exists():
        coverage = {(r["chamber"], r["district"]): r for r in csv.DictReader(open(cov_path, encoding="utf-8"))}

    rows = defaultdict(lambda: defaultdict(int))
    routes = defaultdict(set)
    projects = defaultdict(set)

    for s in stations:
        rr = s["mode"] == "Regional Rail"
        for ch in ("house", "senate", "council"):
            d = s[f"{ch}_district"]
            if not d:
                continue
            row = rows[(ch, d)]
            if rr:
                row["regional_rail_stations"] += 1
                f = s["proposed_frequency_minutes"]
                if f:
                    row[f"rr_{f}_min"] += 1
                else:
                    row["rr_frequency_not_specified"] += 1
                if s["stop_id"] in boards:
                    row["rr_weekday_boardings"] += boards[s["stop_id"]]
                    if f == "15":
                        row["rr_weekday_boardings_at_15_min_stations"] += boards[s["stop_id"]]
                else:
                    row["rr_stations_without_boardings"] += 1
            else:
                row["metro_stations"] += 1
            if s["accessibility_rebuild_proposed"] == "true":
                row["accessibility_rebuilds"] += 1
            if s["accessible_today"] == "unknown":
                row["accessible_today_unknown"] += 1
            if s[f"{ch}_near_boundary"] == "true":
                row["near_boundary_stations"] += 1
            for p in filter(None, (x.strip() for x in s["fy27_named_projects"].split(";"))):
                projects[(ch, d)].add(p)

    for ch in ("house", "senate"):
        for f in json.load(open(D / f"pennsylvania/boundaries/pa_{ch}_districts.geojson", encoding="utf-8"))["features"]:
            pr = f["properties"]
            if sum(c["populationShare"] for c in pr["topCounties"] if c["name"] in REGION) >= 0.5:
                rows[(ch, str(pr["district"]))]  # creates an empty row if the district has no stops

    for key in plan:
        rows[key]  # a district reached only by a plan project still gets a row

    for t in trolley:
        key = (t["chamber"], t["district"])
        rows[key]["trolley_stops"] += int(t["stop_count"])
        routes[key].add(t["route"])

    out = []
    uncovered = []
    for (ch, d), counts in rows.items():
        row = {c: counts.get(c, 0) for c in COLUMNS}
        row.update(chamber=ch, district=d,
                   trolley_routes="; ".join(sorted(routes[(ch, d)])),
                   fy27_named_projects=len(projects[(ch, d)]),
                   fy27_named_projects_millions=f"{sum(cost[p] for p in projects[(ch, d)]):.2f}" if projects[(ch, d)] else "",
                   plan_projects=len(plan[(ch, d)]),
                   plan_project_names="; ".join(plan[(ch, d)]),
                   bus_routes=len(bus[(ch, d)]),
                   frequent_bus_routes=len(fbus[(ch, d)]),
                   frequent_bus_route_names="; ".join(fbus[(ch, d)]))
        cov = coverage.get((ch, d), {})
        if coverage and not cov:
            uncovered.append(f"{ch} {d}")
        for c in ("share_near_frequent_bus", "share_near_frequent_transit_incl_rr15_plan"):
            row[c] = cov.get(c, "")
        for c in ("member_2025_26", "party_2025_26", "seat_2026_status", "winner_2026", "winner_party_2026",
                  "transit_funding_vote_bill", "transit_funding_vote_2025_26", "transit_funding_vote_pro_transit"):
            row[c] = ""
        if ch in legs:
            m, f, v = legs[ch].get(d), results[ch].get(d), votes[ch].get(d)
            row["member_2025_26"] = m["full_name"] if m else ""
            row["party_2025_26"] = m["party"] if m else ""
            row["seat_2026_status"] = f["outcome"] if f else "not_up"
            row["winner_2026"] = f.get("winner", "") if f else ""
            row["winner_party_2026"] = f.get("winner_party", "") if f else ""
            row["transit_funding_vote_bill"] = v["bill"] if v else ""
            row["transit_funding_vote_2025_26"] = v["vote"] if v else ""
            # The pro-transit side differs by bill: "Nay" on the Senate's HB 257 (see its roll call record).
            pro = PRO[roll[FUNDING_VOTE[ch]]["pro_position"]]
            row["transit_funding_vote_pro_transit"] = ("true" if v["vote"] == pro else "false" if v["vote"] in ("Y", "N") else "") if v else ""
        out.append(row)

    if not coverage:
        print(f"warning: {cov_path.name} not found; share columns left blank. "
              "Run build_frequent_coverage.py, then this script again.", file=sys.stderr)
    extra = set(coverage) - {(r["chamber"], r["district"]) for r in out}
    if uncovered or extra:
        print(f"warning: {cov_path.name} does not match the summary rows "
              f"(no coverage row for {len(uncovered)}: {', '.join(sorted(uncovered)) or 'none'}; "
              f"{len(extra)} coverage rows not in the summary). Share columns are blank where missing. "
              "Rerun build_frequent_coverage.py, then this script again.", file=sys.stderr)

    order = {"house": 0, "senate": 1, "council": 2}
    out.sort(key=lambda r: (order[r["chamber"]], int(r["district"])))
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS, lineterminator="\n")
        w.writeheader()
        w.writerows(out)
    print(f"{len(out)} district rows -> {out_path}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else OUT_DIR / "septa-accelerate-district-summary.csv")
