"""Every public dollar figure found for SEPTA's Accelerate plan, tied to the plan's projects.

Usage:
    python build_cost_sources.py [OUTPUT_CSV]
OUTPUT_CSV defaults to datasets/septa-region/septa-accelerate-station-service/septa-accelerate-cost-sources.csv.

The Accelerate plan gives no total and prices only a few items (the $89.9 million Crum Creek Viaduct, more
than $455 million for power). This collects those and the figures other public documents give, one row per figure, each with its source, page and wording. Nothing is added up
or divided by district: the figures come in different dollar bases (year of expenditure, 2025
dollars, unstated), cover different scopes, and several overlap.

Reads, relative to the repo root (run ../dvrpc_lrp_septa_projects/build.py first):
    datasets/septa-region/dvrpc-lrp-septa-projects/dvrpc-lrp-septa-projects.csv
    analyses/septa-capital-tip-tracker/data/septa_fy27_capital_projects.csv
    analyses/septa-capital-tip-tracker/data/dvrpc_pa_tip_ffy2027_draft.csv
Other figures are typed in below with the wording they come from; each was checked against the
source on 2026-11-24.

`match` says how a figure is tied to a plan project: `named` (the source names the same project or
program), `inferred` (same scope, but the source does not say it is part of Accelerate or the
Regional Rail Master Plan), or `related` (an overlapping budget line, not the same scope).
"""
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = {
    "plan": ("SEPTA, Accelerate (Sept 2026)", "https://www.septa.org/wp-content/uploads/page/communication/SEPTA_Accelerate_Web_Nov26.pdf"),
    "bucks": ("SEPTA, Accelerate Bucks County fact sheet", "https://www.septa.org/wp-content/uploads/page/communication/SEPTA_Accelerate_BucksCounty_Web_Nov26.pdf"),
    "chester": ("SEPTA, Accelerate Chester County fact sheet", "https://www.septa.org/wp-content/uploads/page/communication/SEPTA_Accelerate_ChesterCounty_Web_Nov26.pdf"),
    "rrmp07": ("SEPTA, Regional Rail Master Plan, Section 07 Implementation (Sept 2026, footer marked DRAFT)", "https://wwww.septa.org/wp-content/uploads/page/planning/RRMP_FINAL_07_Implementation_SEPTA.pdf"),
    "lrp": ("DVRPC, Update: Connections 2050, Appendix F (May 2026)", "https://www.dvrpc.org/Reports/25140.pdf"),
    "lrp_a1": ("DVRPC, Connections 2050 Amendment 1, Table 5 (Sept 2026)", "https://www.dvrpc.org/Reports/26140.pdf"),
    "fy27": ("SEPTA, FY2027 Capital Budget Proposal", "https://www.septa.org/wp-content/uploads/page/planning/SEPTA-FY-2027-Operating-Capital-Budget-Proposal.pdf"),
    "tip27": ("DVRPC, FFY2027 Pennsylvania TIP (draft)", "https://github.com/transit-forward-philly/data/tree/main/analyses/septa-capital-tip-tracker"),
    "ea": ("SEPTA, Accelerate efficiency and accountability fact sheet", "https://www.septa.org/wp-content/uploads/page/communication/SEPTA_Accelerate_EfficientAccountable_Web_Nov26.pdf"),
    "budget27": ("SEPTA, FY2027 Adopted Budget", "https://wwww.septa.org/wp-content/uploads/page/planning/SEPTA-Adopted-Budget-FY-2027.pdf"),
    "n_susq": ("SEPTA news release, Aug 21 2023", "https://wwww.septa.org/news/susquehannadauphin/"),
    "n_gates": ("SEPTA news release, fare gate contract", "https://wwww.septa.org/news/septa-expands-pilot-program-to-combat-fare-evasion/"),
    "n_drexel": ("SEPTA news release, Drexel Station at 30th Street", "https://wwww.septa.org/news/drexel-station-at-30th-street-welcomes-septa-customers/"),
    "tip25": ("DVRPC, FY2025 Pennsylvania TIP, MPMS 115472 Projects of Significance (SEPTA)", "https://www.dvrpc.org/tip/pa/map/115472"),
}
TEXT = [  # (plan ids, component, $M, qualifier, basis, status, source, page, wording, match)
    ("ACC-033; ACC-034; ACC-035", "Regional Rail Master Plan, full Network Vision", 12000, "more than", "not stated", "estimate, 30 years",
     "rrmp07", "PDF pp. 4-5", "will require a renewed investment totaling more than $12 billion over the course of the next 30 years", "named"),
    ("ACC-033; ACC-034; ACC-035", "Regional Rail Master Plan, share SEPTA already plans", 9000, "more than", "not stated", "planned",
     "rrmp07", "PDF pp. 4-5", "SEPTA is already planning to invest more than $9 billion in upgrading stations, renewing track and power systems", "named"),
    ("ACC-033; ACC-034; ACC-035", "Regional Rail Master Plan, additional investment needed", 3000, "", "not stated", "unfunded",
     "rrmp07", "PDF pp. 4-5", "The additional $3 billion investment necessary to fully realize the Network Vision", "named"),
    ("ACC-039", "Crum Creek Viaduct replacement", 89.9, "", "not stated", "completed",
     "plan", "PDF p. 12", "The $89.9 million project replaced the original viaduct", "named"),
    ("", "Power: substations and power improvements, systemwide", 455, "more than", "not stated", "need, 12 years",
     "plan", "PDF p. 13", "More than $455 million in substation and power improvements are required over the next 12 years", "named"),
    ("", "Cornwells Heights Station reconstruction (Bucks fact sheet; not in the main plan)", 71, "more than", "not stated", "planned",
     "bucks", "p. 2", "$71M+ Investment", "named"),
    ("", "Station and infrastructure investments, Chester County (fact sheet)", 1000, "more than", "not stated", "planned",
     "chester", "p. 1", "over $1B in station and infrastructure investments", "named"),
    ("ACC-029", "Conshohocken Station development: revenue to SEPTA (not a cost)", 332, "", "not stated", "revenue over the agreement",
     "plan", "PDF p. 27", "new revenue source valued at $332 million over the life of the agreement", "named"),
    ("ACC-030", "Ambler Station development: revenue to SEPTA (not a cost)", 236, "", "not stated", "revenue over the contract",
     "ea", "p. 2", "170-unit mixed-use development in Ambler Station's parking lot, valued at $236M in new revenue over the life of the contract", "named"),
    ("ACC-006", "Tasker-Morris Station (B) accessibility", 19.21, "", "not stated", "completed",
     "budget27", "PDF p. 330", "Tasker-Morris Station (B) 19.21 ... Project complete", "named"),
    ("ACC-008", "Susquehanna-Dauphin Station accessibility", 24, "", "not stated", "completed (Aug 2023)",
     "n_susq", "news release", "celebrate the completion of a $24 million project", "named"),
    ("ACC-007", "Drexel Station at 30th Street: federal BUILD grant", 15, "", "not stated", "completed; funding piece",
     "n_drexel", "news release", "funded in part through a $15 million U.S. Department of Transportation Better Utilizing Investments to Leverage Development (BUILD) Grant", "named"),
    ("ACC-007", "Drexel Station at 30th Street: PennDOT funding", 34.2, "", "not stated", "completed; funding piece",
     "n_drexel", "news release", "and $34.2 million in Pennsylvania Department of Transportation funding", "named"),
    ("ACC-004", "Full-height fare gates, phase 1 contract (100 gates, 9 stations)", 6.96, "", "not stated", "contract awarded",
     "n_gates", "news release", "Under the $6.96 million contract, the new gates will be installed at Somerset, Huntingdon", "named"),
    ("ACC-001", "Transit Police, FY2027 operating budget (294 positions)", 44.797, "", "FY2027 dollars", "annual operating",
     "budget27", "PDF p. 140", "Transit Police 292 2 294 35,899 8,898 (labor and non-labor, $ thousands)", "named"),
    ("ACC-009; ACC-012; ACC-013; ACC-022; ACC-023; ACC-026; ACC-028", "Bus Revolution capital investments", 184.82, "", "not stated", "programmed (FY2025 TIP)",
     "tip25", "MPMS 115472", "Bus Revolution Capital Investments ($184.82M)", "named"),
    ("ACC-026; ACC-028", "Transit prioritization corridors (incl. Olney Ave)", 59.7, "", "not stated", "programmed (FY2025 TIP)",
     "tip25", "MPMS 115472", "Transit Prioritization Projects $59.7M (Prior Years - FY 2036) ... Olney Avenue, 19th/20th Streets, 7th/8th Streets, Chestnut/Walnut", "named"),
    ("ACC-022; ACC-023", "Bus end-of-line facilities (Wissahickon TC, South Philadelphia TC, Knights Rd, Neshaminy Blvd)", 92.32, "", "not stated", "programmed (FY2025 TIP)",
     "tip25", "MPMS 115472", "Bus End-of-Line Projects $92.32M (Prior Years - FY 2036)", "named"),
    ("ACC-012", "Micro transit service (SEPTA GO zones)", 6.11, "", "not stated", "programmed (FY2025 TIP)",
     "tip25", "MPMS 115472", "Micro Transit Service $6.11M", "inferred"),
    ("ACC-014; ACC-015", "Trolley Modernization", 1983, "", "not stated", "programmed (FY2025 TIP)",
     "tip25", "MPMS 115472", "Trolley Modernization $1.983B (Prior Years - FY 2036)", "named"),
    ("ACC-016", "Market-Frankford Line vehicle replacement and infrastructure", 1165, "", "not stated", "programmed (FY2025 TIP)",
     "tip25", "MPMS 115472", "Market-Frankford Line Vehicle Replacement & Infrastructure $1.165B", "named"),
    ("ACC-017", "Broad Street Line vehicle replacement and infrastructure", 700, "", "not stated", "programmed (FY2025 TIP)",
     "tip25", "MPMS 115472", "Broad Street Line Vehicle Replacement & Infrastructure $700M", "named"),
    ("ACC-020", "Silverliner IV replacement (partial fleet)", 728.06, "", "not stated", "programmed (FY2025 TIP)",
     "tip25", "MPMS 115472", "Regional Rail Cars Silverliner IV Replacement $728.06M", "named"),
    ("ACC-033; ACC-034", "Airport corridor improvements", 24.56, "", "not stated", "programmed (FY2025 TIP)",
     "tip25", "MPMS 115472", "Airport Corridor Improvements $24.56M", "named"),
    ("ACC-033; ACC-034", "Norristown corridor improvements", 25.08, "", "not stated", "programmed (FY2025 TIP)",
     "tip25", "MPMS 115472", "Norristown Corridor Improvements $25.08M", "named"),
    ("ACC-033", "North Philadelphia infrastructure", 6.96, "", "not stated", "programmed (FY2025 TIP)",
     "tip25", "MPMS 115472", "North Philadelphia Infrastructure $6.96M", "inferred"),
    ("", "Coatesville service restoration (design)", 7, "", "not stated", "programmed (FY2025 TIP)",
     "tip25", "MPMS 115472", "Coatesville Service Restoration $7M", "named"),
    ("ACC-021", "Mainline-Schuylkill bridges and interlockings", 400, "", "not stated", "programmed (FY2025 TIP)",
     "tip25", "MPMS 115472", "Mainline-Schuylkill Bridges & Interlockings $400M", "named"),
    ("ACC-013", "Bus stop improvements", 24.30, "", "not stated", "programmed (FY2025 TIP)",
     "tip25", "MPMS 115472", "Bus Stop Improvements $24.30M", "inferred"),
]
TIP27_ITEMS = [  # sub-projects listed in FFY2027 TIP descriptions (repo table), checked against the text
    ("ACC-005", "Rail transit wayfinding and signage", 29.00, "77183", "Rail Transit Wayfinding & Signage - $29.00M (Prior Years – FY 2028)", "named"),
    ("ACC-032", "69th Street Transportation Center", 10.00, "77183", "69th Street Transportation Center - $10.00M (FY 2038 - FY 2039)", "related"),
    ("ACC-012", "Micro transit service", 8.50, "77183", "Micro Transit Service $8.50M (Prior Years - FY 2027) Activities include acquisition of 25 ADA accessible vehicles", "inferred"),
    ("ACC-023", "South Philadelphia Transportation Center", 21.56, "123962", "South Philadelphia Transportation Center – ($21.56M) – Prior Years – 2028", "named"),
    ("ACC-026; ACC-028", "Transit prioritization corridors (incl. Olney Ave)", 10.0, "123962", "Transit Prioritization Projects $10.0M (Prior Years - FY 2038) ... Olney Avenue, 19th/20th Streets, 7th/8th Streets", "named"),
    ("ACC-013", "Bus stop signage and ePaper", 6.0, "123962", "Bus Stop Signage & ePaper $6.0M (Prior Years – FY 2027)", "named"),
    ("ACC-004", "Fare evasion technology program", 28.03, "121367", "Fare Evasion Technology Program - $28.03M (Prior Years – FY2028)", "inferred"),
    ("ACC-002; ACC-003", "Vacuum cleaning trains", 66.81, "121367", "Vacuum Cleaning Trains - $66.81M (Prior Years – FY 2034)", "related"),
    ("ACC-002; ACC-003", "Cleaning equipment", 16.72, "121367", "Cleaning Equipment – $16.72M (Ongoing)", "related"),
    ("ACC-001", "Transit Police equipment (capital, not staffing)", 15.89, "121367", "SEPTA Transit Police Department Equipment – $15.89M (Ongoing)", "related"),
]
DVRPC = {  # DVRPC MRP id -> (plan ids, match)
    "PAT024": ("ACC-014; ACC-015", "named"), "PAT025": ("ACC-014", "named"), "PAT026": ("ACC-014", "named"),
    "PAT027": ("ACC-015", "named"), "PAT028": ("ACC-015", "related"), "PAT014": ("ACC-016", "named"),
    "PAT085": ("ACC-017", "named"), "PAT051": ("ACC-018", "named"), "PAT086": ("ACC-019", "named"),
    "PAT008": ("ACC-020", "named"), "PAT023": ("ACC-009", "named"), "PAT040": ("ACC-021", "named"),
    "PAT001": ("ACC-036; ACC-037", "named"), "PAT016": ("ACC-038", "named"), "PAT071": ("ACC-033", "inferred"),
    "PAT068": ("", "named"), "PAT002": ("", "related"), "PAT087": ("ACC-009", "related"),
}
# Unfunded rows that are expansions, parking, bridge programs or relocations, left out of the keyword match below
NOT_RRMP = {"PAT037", "PAT090", "PAT038", "PAT088", "PAT011", "PAT022", "PAT003", "PAT004", "PAT005", "PAT010",
            "PAT018", "PAT021", "PAT039", "PAT089"}
NOTES = {  # keyed by (source key or MRP id, component start)
    "RRMP9": "Part of the more-than-$12 billion above, not in addition to it.",
    "RRMP3": "Part of the more-than-$12 billion above, not in addition to it.",
    "BUSREV": "Total of the four MPMS 115472 bus rows below (transit priority, end of line, micro transit, bus stops); do not add it to them.",
    "NOID": "Not one of the plan's 39 named projects, or a systemwide figure, so no plan project id.",
    "DREXEL": "One of two funding pieces SEPTA names; SEPTA gives no total, so do not treat either as the project cost.",
    "POLICE": "Annual operating cost of the whole department, not the cost of reaching 220 officers.",
    "GATES": "Covers 100 gates at nine stations (Somerset, Huntingdon and others), not the 69th Street pilot or the 13 stations planned next.",
    "REVENUE": "Money SEPTA receives from the developer, not a cost; do not add it to costs.",
    "PAT085": "Listed as funded, but Amendment 1 says approximately $726.3 million is deferred after FY 2038; the FY27 capital budget's 12-year total for B cars is $1.0M.",
}
RR_UNFUNDED = ("Line", "Station", "Interlocking", "Flyover", "Yard", "Double Track", "Third Track", "Grade Crossing",
               "Quad", "Trunk", "Separation", "Turnback")
FY27 = {  # FY27 capital budget program line -> plan ids
    "Trolley Modernization Vehicles and Infrastructure": "ACC-014; ACC-015",
    "Regional Rail Cars Silverliner IV Vehicle Replacement": "ACC-020",
    "Regional Rail Cars Silverliner IV Infrastructure": "ACC-020",
    "Market-Frankford Line (L) Vehicle Replacement and Infrastructure": "ACC-016",
    "Broad Street Line (B) Vehicle Replacement and Infrastructure": "ACC-017",
}
TIP27 = {"123961": "ACC-014; ACC-015", "123962": "ACC-009"}


def main(out):
    rows = []
    for ids, comp, m, q, basis, status, src, page, words, match in TEXT:
        note = (NOTES["RRMP9"] if "already plans" in comp else NOTES["RRMP3"] if "additional investment" in comp
                else NOTES["BUSREV"] if comp.startswith("Bus Revolution") else NOTES["DREXEL"] if comp.startswith("Drexel")
                else NOTES["POLICE"] if comp.startswith("Transit Police, FY2027")
                else NOTES["REVENUE"] if "revenue to SEPTA" in comp
                else NOTES["GATES"] if comp.startswith("Full-height fare gates") else NOTES["NOID"] if not ids else "")
        rows.append(dict(plan_project_ids=ids, component=comp, figure_millions=f"{m:.2f}", qualifier=q, dollar_basis=basis,
                         status=status, source=SRC[src][0], source_url=SRC[src][1], page_or_id=page, wording=words, match=match, notes=note))
    for r in csv.DictReader(open(ROOT / "datasets/septa-region/dvrpc-lrp-septa-projects/dvrpc-lrp-septa-projects.csv", encoding="utf-8")):
        funded = r["table"].startswith("F-25")
        if r["mrp_id"] in DVRPC:
            ids, match = DVRPC[r["mrp_id"]]
        elif not funded and any(k.lower() in r["facility"].lower() for k in RR_UNFUNDED) and r["mrp_id"] not in NOT_RRMP:
            ids, match = "ACC-033", "inferred"  # Regional Rail items matched by keyword; the table does not name the Master Plan
        else:
            continue
        src = "lrp_a1" if r["amendment1_cost_millions"] else "lrp"
        rows.append(dict(plan_project_ids=ids, component=r["facility"], figure_millions=f'{float(r["current_cost_millions"]):.2f}', qualifier="",
                         dollar_basis="year of expenditure" if funded else "2025 dollars",
                         status="funded (long-range plan)" if funded else "unfunded (long-range plan)",
                         source=SRC[src][0], source_url=SRC[src][1], page_or_id=r["mrp_id"],
                         wording=(r["amendment1_note"] or r["scope"]), match=match,
                         notes=NOTES.get(r["mrp_id"], NOTES["NOID"] if not ids else "")))
    for r in csv.DictReader(open(ROOT / "analyses/septa-capital-tip-tracker/data/septa_fy27_capital_projects.csv", encoding="utf-8")):
        if r["project"] in FY27:
            rows.append(dict(plan_project_ids=FY27[r["project"]], component=r["project"], figure_millions=f'{float(r["budget_musd"]):.2f}', qualifier="",
                             dollar_basis="not stated", status="FY27 capital budget, total project cost", source=SRC["fy27"][0],
                             source_url=SRC["fy27"][1], page_or_id=r["cpms"], wording="Total project cost in the FY27 capital budget", match="named", notes=""))
    for r in csv.DictReader(open(ROOT / "analyses/septa-capital-tip-tracker/data/dvrpc_pa_tip_ffy2027_draft.csv", encoding="utf-8")):
        if r["mpms"] in TIP27:
            rows.append(dict(plan_project_ids=TIP27[r["mpms"]], component=r["title"], figure_millions=f'{float(r["total_cost"]):.2f}', qualifier="",
                             dollar_basis="not stated", status="programmed (FFY2027 TIP)", source=SRC["tip27"][0], source_url=SRC["tip27"][1],
                             page_or_id=f'MPMS {r["mpms"]}', wording=r["description"][:200], match="named", notes=""))
    for ids, comp, m, mpms, words, match in TIP27_ITEMS:
        rows.append(dict(plan_project_ids=ids, component=comp, figure_millions=f"{m:.2f}", qualifier="", dollar_basis="not stated",
                         status="programmed (FFY2027 TIP)", source=SRC["tip27"][0], source_url=SRC["tip27"][1],
                         page_or_id=f"MPMS {mpms}", wording=words, match=match, notes=""))
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(len(rows), "cost figures")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ROOT / "datasets/septa-region/septa-accelerate-station-service/septa-accelerate-cost-sources.csv")
