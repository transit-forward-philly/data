"""Build the site's data files from the geocoded partner list and LODES district jobs.

    python3 -I pipelines/septa_key_advantage/build_site_data.py

Run geocode_partners.py and build_jobs_by_firm_size.py first.
Writes partners_all.json (the coded partner table) to datasets/, plus site-ready files (partners.geojson, districts.geojson, summary.json, key_advantage_partners.csv) to build/.
"""

import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from partner_industry import industry_label  # noqa: E402

HERE = Path(__file__).resolve().parent

REPO = Path(__file__).resolve().parents[2]
DATA = REPO / "datasets/philadelphia/septa-key-advantage"
ANALYSIS = REPO / "analyses/septa-key-advantage"
BUILD = Path(__file__).resolve().parent / "build"  # scratch output, not committed
OUT = BUILD

# Hand-coded display name per SEPTA partner label. Industry and ownership live in partner_industry.py.
PARTNERS = {
    "ABC Seniors": "Always Best Care Senior Services",
    "Arcadium Lithium (fmr Livent)": "Arcadium Lithium",
    "Brandywine": "Brandywine Realty Trust",
    "Center City District": "Center City District",
    "Center City Legal Reproductions, Inc.": "Center City Legal Reproductions",
    "City of Philadelphia": "City of Philadelphia",
    "City Year": "City Year Philadelphia",
    "County of Delaware": "Delaware County",
    "Curtis Institute of Music": "Curtis Institute of Music",
    "Defender Association of Philadelphia": "Defender Association of Philadelphia",
    "Dywer": "“Dywer” (not identified)",
    "FMC": "FMC Corporation",
    "Four Seasons": "Four Seasons Hotel Philadelphia",
    "Health Verity": "HealthVerity",
    "Inspiritec": "InspiriTec",
    "Integral Molecular": "Integral Molecular",
    "IONOS": "IONOS",
    "Launch Philly": "Launch of Philadelphia",
    "Moravia": "Moravia Health Network",
    "PA House of Representatives": "Pennsylvania House of Representatives",
    "PHDC": "Philadelphia Housing Development Corp.",
    "PPA": "Philadelphia Parking Authority",
    "Stateside": "Stateside Brands",
    "Swarthmore Employee": "Swarthmore College (staff)",
    "UPHS - Penn": "Penn Medicine",
    "Arcadia Land Company": "Arcadia Land Company",
    "Artist Year": "ArtistYear",
    "BOK Condo Association": "Bok Building Condominium Association",
    "Busy Bees": "Busy Bees Learning Center",
    "Campus ESP": "CampusESP",
    "Catalyst Group": "“Catalyst Group” (not identified)",
    "City Ave": "City Avenue District",
    "Clean Air Council": "Clean Air Council",
    "College Together - Employees": "College Together (staff)",
    "Disciplinary Board SCOP": "Disciplinary Board of the Supreme Court of Pa.",
    "DYAD": "“DYAD” (not identified)",
    "Econsult": "Econsult Solutions",
    "En Route Consulting LLC": "En Route Consulting",
    "FatBall Therapeutics": "FatBall Therapeutics",
    "Green Building United": "Green Building United",
    "Henry & Grogan, LLC": "Henry & Grogan",
    "Hofstein Weiner & Meyer": "Hofstein Meyer Rocco Finger & Weiner",
    "HVLAW": "HV Law Group",
    "International Raw Materials LTD": "International Raw Materials",
    "KMKM Law Group, P.C.": "KMKM Law Group",
    "L. Priori Jewelry": "L. Priori Jewelry",
    "Malooga Catering": "Malooga",
    "Metropolitan Acoustics": "Metropolitan Acoustics",
    "Mt. Vernon Manor": "Mt. Vernon Manor",
    "Noble Dental": "Noble Dental",
    "Nochumson PC": "Nochumson P.C.",
    "Permit Philly LLC": "Permit Philly",
    "PHENND": "PHENND",
    "Philadelphia Council AFL-CIO": "Philadelphia Council AFL-CIO",
    "Primrose School": "Primrose School of Center City",
    "Remark Glass": "Remark Glass",
    "Rock to the Future": "Rock to the Future",
    "Saint Mary's Nursery School": "St. Mary's Nursery School",
    "TAUP - Temple Assn. of Univ. Prof.": "Temple Association of University Professionals",
    "Tempest": "Tempest",
    "The Welcoming Center": "The Welcoming Center",
    "Thomas Center for Learning": "Thomas Center for Learning",
    "Vetigenics": "Vetigenics",
    "Visit Philadelphia": "Visit Philadelphia",
    "Voith & Mactavish": "Voith & Mactavish Architects",
    "World Affairs Council of Philadelphia": "World Affairs Council of Philadelphia",
    "Bryn Mawr College": "Bryn Mawr College",
    "Community College of Philadelphia": "Community College of Philadelphia",
    "College Together": "College Together",
    "Swarthmore College": "Swarthmore College",
}
COUNCIL = {"1": "Mark Squilla", "2": "Kenyatta Johnson", "3": "Jamie Gauthier", "4": "Curtis Jones Jr.", "5": "Jeffery Young Jr.",
           "6": "Mike Driscoll", "7": "Quetcy Lozada", "8": "Cindy Bass", "9": "Anthony Phillips", "10": "Brian O'Neill"}
# Bands match LODES firm-size classes so partners and jobs compare directly
BANDS = [(19, "1–19"), (49, "20–49"), (249, "50–249"), (499, "250–499"), (10**9, "500+")]
SUBURBS = {"County of Delaware": (-75.3913, 39.9192), "Swarthmore College": (-75.3511, 39.9064),
           "Swarthmore Employee": (-75.3511, 39.9064), "City Ave": (-75.2207, 40.0041), "Bryn Mawr College": (-75.3223, 40.0218)}


def band(n: int) -> str:
    return next(label for top, label in BANDS if n <= top)


def main() -> None:
    rows = list(csv.DictReader(open(DATA / "partners_geocoded.csv")))
    assert {r["partner"] for r in rows} == set(PARTNERS), "PARTNERS map out of sync with the partner list"
    feats, flat = [], []
    for r in rows:
        name, sector = PARTNERS[r["partner"]], industry_label(r["partner"])
        members = int(r["members"])
        students = r["program"] == "KAPU"
        xy = (float(r["lng"]), float(r["lat"])) if r["lng"] else SUBURBS.get(r["partner"])
        where = ("city" if r["council_district"] else "suburbs" if r["in_philadelphia"] == "no" else "not located")
        props = {
            "name": name, "septa_label": r["partner"], "program": r["program"], "students": students,
            "start": r["start_date"], "start_year": int(r["start_date"][:4]), "members": members,
            "size_band": "Students" if students else band(members), "sector": sector,
            "district": r["council_district"] or None, "where": where,
            "address": r["address"] or None, "city": r["city"] or None, "geo_confidence": r["confidence"],
        }
        flat.append(props)
        if xy:
            feats.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [round(xy[0], 5), round(xy[1], 5)]}, "properties": props})
    OUT.mkdir(parents=True, exist_ok=True)
    json.dump({"type": "FeatureCollection", "features": feats}, open(OUT / "partners.geojson", "w"))
    json.dump(flat, open(DATA / "partners_all.json", "w"))
    with open(OUT / "key_advantage_partners.csv", "w", newline="") as fh:
        cols = ["name", "septa_label", "program", "start", "members", "size_band", "sector", "district", "where", "address", "city", "geo_confidence"]
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(sorted(flat, key=lambda p: -p["members"]))

    jobs = {r["district"]: r for r in csv.DictReader(open(DATA / "district_jobs.csv"))}
    gj = json.load(open(DATA / "districts.geojson"))
    dist_stats = []
    for f in gj["features"]:
        d = f["properties"]["district"]
        ps = [p for p in flat if p["district"] == d and not p["students"]]
        j = jobs[d]
        small_jobs = int(j["private_firm_0-19"]) + int(j["private_firm_20-49"])
        s = {
            "district": d, "member": COUNCIL[d], "partners": len(ps), "members": sum(p["members"] for p in ps),
            "small_partners": sum(p["members"] < 50 for p in ps), "small_members": sum(p["members"] for p in ps if p["members"] < 50),
            "jobs": int(j["jobs_all"]), "private_jobs": int(j["jobs_private"]), "small_firm_jobs": small_jobs,
            "largest": max(ps, key=lambda p: p["members"])["name"] if ps else None,
        }
        s["members_per_1k_jobs"] = round(1000 * s["members"] / s["jobs"], 1)
        f["properties"] = s
        dist_stats.append(s)
    json.dump(gj, open(OUT / "districts.geojson", "w"))

    emp = [p for p in flat if not p["students"]]
    tot = jobs["Total"]
    by_band = []
    for (top, label), key in zip(BANDS, ["0-19", "20-49", "50-249", "250-499", "500+"]):
        ps = [p for p in emp if p["size_band"] == label]
        by_band.append({"band": label, "partners": len(ps), "members": sum(p["members"] for p in ps),
                        "private_jobs": int(tot[f"private_firm_{key}"])})
    summary = {
        "as_of": "September 2026", "partners": len(flat), "members": sum(p["members"] for p in flat),
        "employers": len(emp), "employer_members": sum(p["members"] for p in emp),
        "student_programs": len(flat) - len(emp), "student_members": sum(p["members"] for p in flat if p["students"]),
        "city_jobs": int(tot["jobs_all"]), "city_private_jobs": int(tot["jobs_private"]),
        "city_small_firm_jobs": int(tot["private_firm_0-19"]) + int(tot["private_firm_20-49"]),
        "by_band": by_band, "districts": dist_stats,
        "by_sector": {s: {"partners": sum(p["sector"] == s for p in flat), "members": sum(p["members"] for p in flat if p["sector"] == s)}
                      for s in sorted({p["sector"] for p in flat})},
    }
    json.dump(summary, open(OUT / "summary.json", "w"), indent=1)
    print(json.dumps({k: v for k, v in summary.items() if k not in ("districts", "by_sector")}, indent=1))
    print(json.dumps(summary["by_sector"], indent=1))


if __name__ == "__main__":
    main()
