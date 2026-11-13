"""Aggregate SEPTA Key Advantage partners into published summary tables. No partner is named.

    python3 pipelines/septa_key_advantage/aggregate_partners.py PARTNERS.json

PARTNERS.json is a private partner-level table (one object per partner with `members`, `sector`, `district`,
`where`, `students`). It is not part of this repo. Writes to datasets/philadelphia/septa-key-advantage-summary/.

Disclosure rules:
- College student programs are not employers and are excluded.
- Partners are grouped into member-count cohorts, never listed.
- Sectors with fewer than MIN_CELL partners are merged into "All other sectors".
- A council district's small-partner split is blank when it has fewer than MIN_CELL partners.
- No sector-by-cohort or sector-by-district tables, and no member totals by district.
"""

import csv
import json
import sys
from collections import Counter
from pathlib import Path

OUT = Path(__file__).resolve().parents[2] / "datasets/philadelphia/septa-key-advantage-summary"
MIN_CELL = 5
SMALL = 50  # "small" partner = fewer than 50 Key Advantage members
COHORTS = [("1-19 members", 0, 20), ("20-49 members", 20, 50), ("50-249 members", 50, 250), ("250+ members", 250, 10**9)]


def pct(n: int, d: int) -> str:
    return f"{100 * n / d:.1f}"


def main(path: str) -> None:
    ps = [p for p in json.load(open(path)) if not p["students"]]
    n = len(ps)
    OUT.mkdir(parents=True, exist_ok=True)

    tot_members = sum(p["members"] for p in ps)
    with open(OUT / "size_cohorts.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["cohort", "partners", "pct_of_partners", "members", "pct_of_members"])
        for name, lo, hi in COHORTS:
            g = [p for p in ps if lo <= p["members"] < hi]
            m = sum(p["members"] for p in g)
            w.writerow([name, len(g), pct(len(g), n), m, pct(m, tot_members)])
        w.writerow(["All employer partners", n, "100.0", tot_members, "100.0"])

    sectors = Counter(p["sector"] for p in ps)
    merged = Counter()
    for s, c in sectors.items():
        merged[s if c >= MIN_CELL else "All other sectors"] += c
    with open(OUT / "sectors.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["sector", "partners", "pct_of_partners"])
        rows = sorted(((s, c) for s, c in merged.items() if s != "All other sectors"), key=lambda r: -r[1])
        rows.append(("All other sectors", merged["All other sectors"]))
        for s, c in rows:
            w.writerow([s, c, pct(c, n)])

    def district(p: dict) -> str:
        if p["district"]:
            return p["district"]
        return "Outside Philadelphia" if p["where"] == "suburbs" else "Not located"

    by = {}
    for p in ps:
        d = by.setdefault(district(p), [0, 0])
        d[0] += 1
        d[1] += p["members"] < SMALL
    order = [str(i) for i in range(1, 11)] + ["Outside Philadelphia", "Not located"]
    with open(OUT / "council_districts.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["council_district", "partners", "partners_under_50_members", "pct_under_50_members"])
        for k in order:
            c, s = by.get(k, [0, 0])
            show = c >= MIN_CELL
            w.writerow([k, c, s if show else "", pct(s, c) if show else ""])
    print(f"{n} employer partners; wrote {OUT}")


if __name__ == "__main__":
    main(sys.argv[1])
