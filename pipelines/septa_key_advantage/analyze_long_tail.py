"""Who is in Key Advantage beyond the four largest employer partners?

    python3 -I pipelines/septa_key_advantage/analyze_long_tail.py

Compares the remaining employer partners (college student programs excluded) with Philadelphia's jobs by industry
(LODES 2023, all jobs). Writes long_tail_summary.csv and build/long_tail.json.
"""

import csv
import gzip
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[2]
DATA = REPO / "datasets/philadelphia/septa-key-advantage"
ANALYSIS = REPO / "analyses/septa-key-advantage"
BUILD = Path(__file__).resolve().parent / "build"  # scratch output, not committed

sys.path.insert(0, str(HERE))
from partner_industry import CNS, INDUSTRY, SHORT  # noqa: E402

TOP_N = 4
CENTER_CITY = (-75.183, 39.9415, -75.140, 39.9585)  # river to river, South St to Vine St
COHORTS = [("2022-01", "Pilot and large-employer launch (2022 to Apr. 2023)"), ("2023-05", "Small-business tier opens (May 2023 to Aug. 2025)"),
           ("2025-09", "After the September 2025 price reset")]


def city_jobs_by_industry() -> dict[str, int]:
    tot = defaultdict(int)
    with gzip.open(DATA / "raw/pa_wac_S000_JT00_2023.csv.gz", "rt") as fh:
        for r in csv.DictReader(fh):
            if r["w_geocode"].startswith("42101"):
                for k in CNS:
                    tot[k] += int(r[k])
    return dict(tot)


def cohort(start: str) -> str:
    return [label for begin, label in COHORTS if start[:7] >= begin][-1]


def main() -> None:
    rows = list(csv.DictReader(open(DATA / "partners_geocoded.csv")))
    names = {p["septa_label"]: p for p in json.load(open(DATA / "partners_all.json"))}
    employers = []
    for r in rows:
        cns, own, checked = INDUSTRY[r["partner"]]
        if own == "students":
            continue
        p = names[r["partner"]]
        lng, lat = (float(r["lng"]), float(r["lat"])) if r["lng"] else (None, None)
        employers.append({
            "label": r["partner"], "name": p["name"], "members": int(r["members"]), "start": r["start_date"],
            "industry": SHORT.get(cns, "Not identified"), "cns": cns, "ownership": own or "unknown", "ownership_checked": checked,
            "district": r["council_district"] or None, "where": p["where"], "size_band": p["size_band"],
            "center_city": bool(lng and CENTER_CITY[0] <= lng <= CENTER_CITY[2] and CENTER_CITY[1] <= lat <= CENTER_CITY[3]),
        })
    employers.sort(key=lambda e: -e["members"])
    top, rest = employers[:TOP_N], employers[TOP_N:]
    rest_members = sum(e["members"] for e in rest)
    jobs = city_jobs_by_industry()
    jobs_total = sum(jobs.values())

    def group(key: str, items: list[dict]) -> list[dict]:
        g = defaultdict(lambda: {"partners": 0, "members": 0, "names": []})
        for e in items:
            g[e[key]]["partners"] += 1
            g[e[key]]["members"] += e["members"]
            g[e[key]]["names"].append(e["name"])
        return [{key: k, **v} for k, v in sorted(g.items(), key=lambda kv: -kv[1]["members"])]

    by_industry = []
    for cns in CNS:
        ps = [e for e in rest if e["cns"] == cns]
        by_industry.append({
            "industry": SHORT[cns], "cns": cns, "partners": len(ps), "members": sum(e["members"] for e in ps),
            "member_share": sum(e["members"] for e in ps) / rest_members, "city_jobs": jobs[cns], "job_share": jobs[cns] / jobs_total,
            "names": [e["name"] for e in ps],
        })
    unknown = [e for e in rest if e["cns"] is None]
    if unknown:
        by_industry.append({"industry": "Not identified", "cns": None, "partners": len(unknown), "members": sum(e["members"] for e in unknown),
                            "member_share": sum(e["members"] for e in unknown) / rest_members, "city_jobs": None, "job_share": None,
                            "names": [e["name"] for e in unknown]})

    out = {
        "top": [{"name": e["name"], "members": e["members"], "industry": e["industry"], "ownership": e["ownership"]} for e in top],
        "top_members": sum(e["members"] for e in top), "employer_members": sum(e["members"] for e in employers),
        "rest_partners": len(rest), "rest_members": rest_members, "rest_median": statistics.median(e["members"] for e in rest),
        "rest_center_city": sum(e["center_city"] for e in rest), "rest_in_city": sum(e["where"] == "city" for e in rest),
        "by_ownership": group("ownership", rest), "by_industry": by_industry, "by_size": group("size_band", rest),
        "by_cohort": group("cohort", [{**e, "cohort": cohort(e["start"])} for e in rest]),
        "city_jobs_total": jobs_total, "rest": rest,
    }
    BUILD.mkdir(parents=True, exist_ok=True)
    json.dump(out, open(BUILD / "long_tail.json", "w"), indent=1)
    with open(ANALYSIS / "long_tail_summary.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["industry", "partners", "members", "share_of_rest_members", "philly_jobs_2023", "share_of_philly_jobs", "partners_named"])
        for r in by_industry:
            w.writerow([r["industry"], r["partners"], r["members"], f"{r['member_share']:.3f}", r["city_jobs"] or "",
                        f"{r['job_share']:.3f}" if r["job_share"] is not None else "", "; ".join(r["names"])])

    print(f"Top {TOP_N}: {', '.join(e['name'] for e in top)} = {out['top_members']:,} of {out['employer_members']:,} employer members")
    print(f"Rest: {len(rest)} partners, {rest_members:,} members, median {out['rest_median']}, "
          f"{out['rest_center_city']} in Center City of {out['rest_in_city']} placed in the city\n")
    for name, key in [("ownership", "by_ownership"), ("size", "by_size"), ("cohort", "by_cohort")]:
        for g in out[key]:
            print(f"  {name:<9} {g[name if name != 'size' else 'size_band']:<55} {g['partners']:>3} partners {g['members']:>6,} members")
        print()
    print(f"{'industry':<52}{'partners':>9}{'members':>9}{'mem %':>7}{'jobs %':>8}")
    for r in sorted(by_industry, key=lambda r: -(r["job_share"] or 0)):
        js = f"{100 * r['job_share']:.1f}" if r["job_share"] is not None else "—"
        print(f"{r['industry']:<52}{r['partners']:>9}{r['members']:>9,}{100 * r['member_share']:>7.1f}{js:>8}")


if __name__ == "__main__":
    main()
