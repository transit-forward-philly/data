"""Crosswalk SEPTA FY2027 capital projects to DVRPC PA TIP (Draft FFY2027) programs by MPMS.

Inputs (../data/): septa_fy27_capital_projects.csv, dvrpc_pa_tip_ffy2027_draft.csv
Output: ../data/capital_tip_crosswalk.csv, one row per MPMS present in either source.

The TIP funds SEPTA at the program level (one MPMS covers many capital projects, e.g. 77183 is every
station project), so the comparison is capital 12-year total (FY27-38) vs TIP total programmed
(FY27-30 plus Future). A gap_musd near zero means the two documents agree.
"""

import csv
from collections import defaultdict
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"


def main() -> None:
    with open(DATA / "dvrpc_pa_tip_ffy2027_draft.csv") as fh:
        tip = {r["mpms"]: r for r in csv.DictReader(fh)}
    with open(DATA / "septa_fy27_capital_projects.csv") as fh:
        cap = list(csv.DictReader(fh))
    by_mpms: dict[str, list[dict]] = defaultdict(list)
    for row in cap:
        by_mpms[row["tip_mpms"] or "(none)"].append(row)
    septa_tip = {m for m, r in tip.items() if r["lead_agency"] == "SEPTA"}
    out = []
    for mpms in sorted(set(by_mpms) | septa_tip):
        rows, t = by_mpms.get(mpms, []), tip.get(mpms, {})
        cap_12yr = round(sum(float(r["twelve_year_total_musd"] or 0) for r in rows), 2)
        tip_total = float(t["total_programmed"]) if t.get("total_programmed") else None
        out.append({
            "mpms": mpms,
            "tip_title": t.get("title", ""),
            "in_tip": "Yes" if t else "No",
            "capital_project_count": len(rows),
            "capital_budget_musd": round(sum(float(r["budget_musd"] or 0) for r in rows), 2),
            "capital_12yr_musd": cap_12yr,
            "tip_total_programmed_musd": "" if tip_total is None else tip_total,
            "gap_musd": "" if tip_total is None else round(cap_12yr - tip_total, 2),
            "capital_projects": "; ".join(r["project"] for r in rows),
        })
    with open(DATA / "capital_tip_crosswalk.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    print(f"wrote {len(out)} MPMS rows")


if __name__ == "__main__":
    main()
