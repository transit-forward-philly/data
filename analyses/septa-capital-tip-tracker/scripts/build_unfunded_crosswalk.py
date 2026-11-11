"""Link SEPTA's FY27 unfunded (deferred/descoped) projects to the capital budget and the TIP.

Inputs:
  ../../../datasets/septa-region/septa-fy27-unfunded-projects/septa-fy27-unfunded-projects.csv
  ../data/septa_fy27_capital_projects.csv   (SEPTA FY27 capital budget, 12-year program)
  ../data/dvrpc_pa_tip_ffy2027_draft.csv    (DVRPC PA TIP, all listings)
  ../web/data/tip_projects.json             (mapped TIP projects with legislators)
Outputs:
  ../data/unfunded_crosswalk.csv
  ../web/data/unfunded_projects.json

Matching is by hand-reviewed pairs, not fuzzy name matching: a first fuzzy pass paired
unrelated projects (e.g. "Exton Station" with "Bristol Station"). Each pair carries a type:

  same_project  the funded capital row and the unfunded row are the same project; the
                unfunded amount is the part SEPTA could not fund.
  same_program  the capital row is the same recurring program; the unfunded row is
                additional scope or a later phase of that program.
  related       a nearby or overlapping project, not the same line item. Read the note.

Everything else is left unmatched on purpose. Unfunded projects usually have no capital
budget row at all, which is the point of being unfunded.
"""

import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data"
WEB = HERE.parent / "web" / "data"
UNFUNDED = HERE.parents[2] / "datasets/septa-region/septa-fy27-unfunded-projects/septa-fy27-unfunded-projects.csv"

# (unfunded project name starts with, capital project name starts with, type, note)
PAIRS = [
    ("Trolley Tunnel Track", "Trolley Tunnel Track", "same_project", ""),
    ("Broad St. Line [B] Railcar", "Broad Street Line (B) Vehicle Replacement", "same_project",
     "Capital budget carries $1.0M in the 12-year plan; the unfunded list holds the bulk of the project."),
    ("69th Street TC Multi-Modal", "69th Street Transportation Center Multi-Modal", "same_project", ""),
    ("Noble Station (Construction)", "Noble Station on the West Trenton Line", "same_project",
     "Unfunded row is the construction phase; the capital budget row carries $2.0M in the 12-year plan."),
    ("Fern Rock Transportation Center Pedestrian", "Fern Rock Transportation Center Safety", "related",
     "Same station, different named project."),
    ("Facilities Critical Infrastructure Program", "Facilities Critical Infrastructure Program", "same_program", ""),
    ("Maintenance & Training Facilities Improvement", "Maintenance & Training Facilities Improv", "same_program", ""),
    ("Vehicle Engineering & Maintenance Shop Equipment", "Vehicle Engineering & Maintenance Shop E", "same_program", ""),
    ("Wheel Truing Program", "Wheel Truing Program", "same_program", "Unfunded row is Phase 2."),
    ("Climate Adaptation & Mitigation Program", "Climate Adaptation and Mitigation Program", "same_program", ""),
    ("On-Site Power for Major Facilities", "On-Site Power for Major Facilities", "same_program", ""),
    ("Cleaning Equipment", "Cleaning Equipment", "same_program", ""),
    ("Safety and Security Infrastructure Hardening Program", "Safety and Security Infrastructure Hardening Program", "same_program", ""),
    ("Safety and Security Shop, Yards", "Safety and Security Infrastructure Hardening Program", "related",
     "Separate unfunded line for shops, yards and offices under the same hardening effort."),
    ("Rail Transit Wayfinding and Signage", "Rail Transit Wayfinding & Signage", "same_program", ""),
    ("Transit Priority Projects", "Transit Priority Projects", "same_program",
     "Capital budget row has $0 in the 12-year plan."),
    ("Transit Substation Program", "Regional and Transit Rail Substation Program", "same_program", ""),
]


def main() -> None:
    unfunded = list(csv.DictReader(open(UNFUNDED)))
    capital = list(csv.DictReader(open(DATA / "septa_fy27_capital_projects.csv")))
    tip = {r["mpms"]: r for r in csv.DictReader(open(DATA / "dvrpc_pa_tip_ffy2027_draft.csv"))}
    mapped = {str(p["MPMS_ID"]): p for p in json.load(open(WEB / "tip_projects.json"))}

    used = set()
    out = []
    for u in unfunded:
        pair = next((p for p in PAIRS if u["project"].startswith(p[0])), None)
        row = {**u, "match_type": "", "capital_project": "", "capital_12yr_musd": "", "tip_mpms": "",
               "tip_title": "", "tip_total_programmed_musd": "", "match_note": ""}
        if pair:
            used.add(pair[0])
            hits = [c for c in capital if c["project"].startswith(pair[1])]
            assert len(hits) == 1, f"{pair[1]!r} matched {len(hits)} capital rows"
            c = hits[0]
            t = tip.get(c["tip_mpms"], {})
            row.update(
                match_type=pair[2], capital_project=c["project"], capital_12yr_musd=c["twelve_year_total_musd"],
                tip_mpms=c["tip_mpms"], tip_title=t.get("title", ""),
                tip_total_programmed_musd=t.get("total_programmed", ""), match_note=pair[3],
            )
        out.append(row)
    missing = [p[0] for p in PAIRS if p[0] not in used]
    assert not missing, f"unused pairs: {missing}"

    fields = list(out[0])
    with open(DATA / "unfunded_crosswalk.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(out)

    web = []
    for r in out:
        m = mapped.get(r["tip_mpms"])
        web.append({
            "county": r["county"], "status": r["status"], "project": r["project"],
            "value_millions": float(r["value_millions"]), "ada": r["ada_project"].upper() == "TRUE",
            "note": r["source_note"], "match_type": r["match_type"], "capital_project": r["capital_project"],
            "capital_12yr_musd": float(r["capital_12yr_musd"]) if r["capital_12yr_musd"] else None,
            "tip_mpms": r["tip_mpms"], "tip_title": r["tip_title"], "match_note": r["match_note"],
            "houses": m["Houses"] if m else [], "senates": m["Senates"] if m else [],
        })
    json.dump(web, open(WEB / "unfunded_projects.json", "w"), indent=1)
    matched = sum(1 for r in out if r["match_type"])
    print(f"{len(out)} unfunded projects, {matched} linked to a capital budget row, "
          f"{sum(1 for r in out if r['tip_mpms'])} with a TIP MPMS")


if __name__ == "__main__":
    main()
