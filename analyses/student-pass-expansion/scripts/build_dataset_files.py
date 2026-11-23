"""Build the school-trip, scenario and catchment CSVs in
datasets/philadelphia/student-pass-expansion.

Travel-time summaries are transcribed from the 2026-10-22 r5py runs (grades 7-12 and
5-6), whose per-trip outputs were not kept. Scenarios are computed here from one
formula. The catchment breakdown is regenerated from the Philly School Data Explorer's
core tables (catchment_flow, school_year_attr, school_placeholder).

    pip install duckdb pandas
    python build_dataset_files.py --core <dir>

<dir> is either a built checkout's core/ folder, or a folder holding the
core__catchment_flow.parquet, core__school_year_attr.parquet and
core__school_placeholder.parquet assets from a release of
https://github.com/jongeeting/philly-school-data-explorer (v0.2.0 or later).
"""

import argparse
import csv
from pathlib import Path

import duckdb

HERE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
parser.add_argument("--core", type=Path, required=True, help="folder with the school data core tables")
parser.add_argument(
    "--out", type=Path, default=HERE.parents[2] / "datasets/philadelphia/student-pass-expansion"
)
args = parser.parse_args()
OUT = args.out


def core_table(name):
    for candidate in (args.core / f"{name}.parquet", args.core / f"core__{name}.parquet"):
        if candidate.exists():
            return candidate
    raise SystemExit(f"{name}.parquet (or core__{name}.parquet) not found in {args.core}")


def write(name, header, rows):
    with open(OUT / name, "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)


# ---------------------------------------------------------------- school-trip tiers
RULES = {
    "low": "walk over 45 min and transit saves 15+ min",
    "medium": "walk over 30 min and transit saves 10+ min",
    "high": "walk over 20 min and transit saves 5+ min",
}
tiers = []


def tier_rows(band, group_type, group, total, values, walk="3.0 mph (4.8 km/h)", shares=False):
    for t, v in zip(["low", "medium", "high"], values, strict=True):
        if shares:
            n, pct = "", v
        else:
            n, pct = v, round(100 * v / total, 1)
        tiers.append([band, walk, group_type, group, total, t, RULES[t], n, pct])


tier_rows("7-12", "all", "all public", 82806, [38665, 47625, 55466])
for g, tot, h, m, lo in [
    ("middle", 4652, 48.2, 35.8, 24.6), ("k_8", 16477, 33.6, 27.0, 19.8),
    ("6_12", 8533, 84.3, 76.4, 65.1), ("high", 41199, 75.8, 65.1, 53.6),
    ("k_12", 11946, 77.4, 68.5, 55.5),
]:
    tier_rows("7-12", "school_level", g, tot, [lo, m, h], shares=True)
for g, tot, h, m, lo in [
    ("district", 53982, 62.0, 52.5, 42.5), ("charter", 26694, 75.6, 66.1, 53.7),
    ("contracted alternative", 2130, 84.5, 76.7, 66.0),
]:
    tier_rows("7-12", "sector", g, tot, [lo, m, h], shares=True)
tier_rows("5-6", "all", "all public", 27514, [7285, 9539, 11618])
tier_rows("5-6", "all", "all public", 27514, [8949, 11444, 14188], walk="2.5 mph (4.0 km/h)")
# Low end: the 1,632 grade 5-6 students routed from high school catchments (6-12 and
# K-12 schools with no other catchment) left out, and the remaining students' tier
# shares (24.2%, 32.1%, 39.6%) applied to all 27,514.
G56_LOW_END_PCT = [24.2, 32.1, 39.6]
G56_LOW_END = [round(27514 * p / 100) for p in G56_LOW_END_PCT]
tier_rows("5-6", "all", "all public, excluding high school catchment routing", 27514, G56_LOW_END)
for g, tot, lo, m, h in [
    ("elementary", 3757, 426, 609, 810), ("k_8", 16252, 3400, 4576, 5688),
    ("middle", 2803, 740, 1058, 1397), ("6_12", 1131, 744, 865, 958),
    ("k_12", 3565, 1975, 2431, 2764),
]:
    tier_rows("5-6", "school_level", g, tot, [lo, m, h])
write(
    "school_trip_tiers.csv",
    ["grade_band", "walk_speed", "group_type", "group", "group_students_est", "tier", "rule",
     "students_est", "pct_of_group"],
    tiers,
)

# Combined 5-12 estimate: non-public assumed to match grade 7-12 public shares
NP = 19284
comb = []
for i, t in enumerate(["low", "medium", "high"]):
    g712 = [38665, 47625, 55466][i]
    g56 = [7285, 9539, 11618][i]
    g56_low = G56_LOW_END[i]
    np_est = round(NP * g712 / 82806)
    comb.append([t, RULES[t], g712, g56_low, g56, np_est,
                 g712 + g56_low + np_est, g712 + g56 + np_est])
write(
    "school_trip_tiers_5_12.csv",
    ["tier", "rule", "grades_7_12_public", "grades_5_6_public_low_end",
     "grades_5_6_public_high_end", "nonpublic_5_12_assumed", "total_5_12_low_end",
     "total_5_12_high_end"],
    comb,
)

# ---------------------------------------------------------------- within 1.5 miles
within = [
    ["7-12", "all", "all public", 82610, 44.8, 36.9],
    ["7-12", "school_level", "middle", 4650, 66.9, 58.6],
    ["7-12", "school_level", "k_8", 16470, 74.7, 68.9],
    ["7-12", "school_level", "6_12", 8520, 25.3, 19.9],
    ["7-12", "school_level", "high", 41070, 37.5, 28.5],
    ["7-12", "school_level", "k_12", 11910, 33.9, 25.4],
    ["7-12", "sector", "district", 53840, 49.9, 42.0],
    ["7-12", "sector", "charter", 26640, 36.0, 28.1],
    ["7-12", "sector", "contracted alternative", 2130, 24.9, 18.6],
    ["5-6", "all", "all public", 27514, 67.0, 60.6],
    ["5-6", "school_level", "elementary", 3757, 85.1, 79.0],
    ["5-6", "school_level", "k_8", 16252, 73.4, 67.7],
    ["5-6", "school_level", "middle", 2803, "", 56.7],
    ["5-6", "school_level", "6_12", 1131, "", 19.1],
    ["5-6", "school_level", "k_12", 3565, "", 25.2],
]
write(
    "within_1_5_miles.csv",
    ["grade_band", "group_type", "group", "group_students_est", "pct_within_straight_line",
     "pct_within_walking_route"],
    within,
)

# ---------------------------------------------------------------- walk-time and saving bands
bands = [
    ["7-12", "walk_minutes", "under 20", 19761, 23.9],
    ["7-12", "walk_minutes", "20-30", 10139, 12.2],
    ["7-12", "walk_minutes", "30-45", 12149, 14.7],
    ["7-12", "walk_minutes", "45-60", 8877, 10.7],
    ["7-12", "walk_minutes", "over 60", 31880, 38.5],
    ["7-12", "transit_saving_minutes", "under 1", 19251, 23.2],
    ["7-12", "transit_saving_minutes", "1-5", 7771, 9.4],
    ["7-12", "transit_saving_minutes", "5-10", 7465, 9.0],
    ["7-12", "transit_saving_minutes", "10-20", 11853, 14.3],
    ["7-12", "transit_saving_minutes", "20-30", 7725, 9.3],
    ["7-12", "transit_saving_minutes", "30 or more", 28740, 34.7],
    ["5-6", "walk_minutes", "under 20", "", 48.7],
    ["5-6", "walk_minutes", "20-30", "", 11.3],
    ["5-6", "walk_minutes", "30-45", "", 11.6],
    ["5-6", "walk_minutes", "45-60", "", 7.9],
    ["5-6", "walk_minutes", "over 60", "", 20.5],
    ["5-6", "transit_saving_minutes", "under 1", "", 47.6],
]
write("walk_and_saving_bands.csv",
      ["grade_band", "measure", "band", "students_est", "pct_of_grade_band"], bands)

# ---------------------------------------------------------------- inside the 1.5-mile zone
zone = [
    ["middle", 126, "walk 3.0 mph", 8, 13, 17],
    ["middle", 126, "transit", 8, "", ""],
    ["high", 22, "walk 3.0 mph", 20.5, 33, 39],
    ["high", 22, "walk 2.5 mph", 25.5, "", ""],
    ["high", 22, "transit", 18, 25, 30],
]
write("zone_travel_times.csv",
      ["catchment_level", "catchments", "mode", "median_minutes", "p90_minutes",
       "max_minutes"], zone)

# ---------------------------------------------------------------- eligibility scenarios
POOL = {"7-12": 83399 + 14674, "5-6": 27893 + 4610}
WITHIN = {"7-12": 0.40, "5-6": 0.64}
ACTIVE, REL_WITHIN, RATE, SUMMER = 0.57, 0.50, 110.20, 0.53
CURRENT = 30150580
groups = {}
for band in POOL:
    groups[(band, "beyond")] = POOL[band] * (1 - WITHIN[band])
    groups[(band, "within")] = POOL[band] * WITHIN[band]
steps = [
    ("current_pool", "Grades 7-12, keep 1.5-mile rule (today's pool)", [("7-12", "beyond")]),
    ("add_56_keep_rule", "Add grades 5-6, keep 1.5-mile rule",
     [("7-12", "beyond"), ("5-6", "beyond")]),
    ("remove_rule_712", "Grades 7-12, remove 1.5-mile rule",
     [("7-12", "beyond"), ("7-12", "within")]),
    ("add_56_rule_remove_712", "Add 5-6 with rule; remove rule for 7-12",
     [("7-12", "beyond"), ("5-6", "beyond"), ("7-12", "within")]),
    ("all_512_no_rule", "Grades 5-12, remove 1.5-mile rule", list(groups)),
]
scen = []
for key, label, on in steps:
    elig = sum(groups[g] for g in on)
    cards = sum(groups[g] * ACTIVE * (REL_WITHIN if g[1] == "within" else 1) for g in on)
    m = cards * RATE
    scen.append([key, label, round(elig), round(cards), RATE, round(m * 12),
                 round(m * (10 + 2 * SUMMER)), round(m * 10)])
same = POOL["7-12"] + POOL["5-6"]
m = same * ACTIVE * RATE
scen.append(["all_512_no_rule_same_use", "Grades 5-12, no rule, students near school ride as much",
             same, round(same * ACTIVE), RATE, round(m * 12), round(m * (10 + 2 * SUMMER)),
             round(m * 10)])
write(
    "eligibility_scenarios.csv",
    ["scenario", "label", "eligible_students", "active_cards_monthly", "monthly_rate",
     "total_all_12_months", "total_reduced_summer", "total_school_year_only"],
    scen,
)

# ---------------------------------------------------------------- corrected cost scenarios
def cost(cards, rate, months, summer):
    return cards * rate * (months + (12 - months) * summer)


sc = {s[0]: s for s in scen}
rows = [
    ["current_program", 34030, 88.60, 10, 0, CURRENT, 0, "Actual FY billing (Exhibit A)"],
    ["exhibit_a", 71036, 110.20, 12, 1.00, 93938641, 93938641 - CURRENT,
     "SDP estimate as printed in Exhibit A; 71,036 x $110.20 x 12 = $93,938,006"],
]
for key, cards, rate, months, summer, note in [
    ("school_year_only", 71036, 110.20, 10, 0, "No summer billing"),
    ("full_year_reduced_summer", 71036, 110.20, 10, 0.53, "Summer at 53% of school-year level"),
    ("current_rate_12mo", 71036, 88.60, 12, 1.00, "Keep current rate"),
    ("current_rate_10mo", 71036, 88.60, 10, 0, "Current rate, school year only"),
    ("discount_25pct_12mo", 71036, 87.00, 12, 1.00, "25% off $116 retail"),
]:
    t = round(cost(cards, rate, months, summer))
    rows.append([key, cards, rate, months, summer, t, t - CURRENT, note])
t = 130576 * 505
rows.append(["flat_505_all_512", "", "", "", "", t, t - CURRENT,
             "Flat $505 per eligible student per year (current $30,150,580 / 59,706), "
             "all 130,576 grade 5-12 students"])
for key in ["add_56_keep_rule", "remove_rule_712"]:
    s = sc[key]
    t = s[5]  # same total as eligibility_scenarios.csv (all 12 months)
    rows.append([key, s[3], 110.20, 12, 1.00, t, t - CURRENT,
                 f"{s[1]}; active cards from eligibility_scenarios.csv (57% beyond 1.5 mi, "
                 "50% of that within)"])
write(
    "cost_scenarios.csv",
    ["scenario", "active_cards_monthly", "monthly_rate", "months_billed", "summer_factor",
     "total_annual", "additional_over_current", "notes"],
    rows,
)

# ---------------------------------------------------------------- catchment destinations
c = duckdb.connect()
d = c.sql(f"""
with f as (select * from '{core_table("catchment_flow")}'
           where sy=2026 and catchment_status='reported'),
a as (select school_id, name, level, governance, admission_type
      from '{core_table("school_year_attr")}' where sy=2026),
p as (select school_id, kind from '{core_table("school_placeholder")}')
select ca.level catchment_level, ca.name catchment_school, f.count,
 case when f.enrolled_school_id=f.catchment_school_id then 'own_catchment_school'
      when p.kind='cyber charter' then 'cyber_charter'
      when p.kind is not null then 'outside_district_list'
      when ea.governance='Charter' then 'philadelphia_charter'
      when ea.admission_type='Alternative' then 'alternative'
      when ea.admission_type='Virtual' then 'district_virtual'
      when ea.admission_type='Catchment' then 'other_district_neighborhood'
      when ea.admission_type='Criteria-Based' then 'district_criteria_based'
      when ea.admission_type='Citywide' then 'district_citywide'
      else 'outside_district_list' end dest
from f join a ca on ca.school_id=f.catchment_school_id
left join a ea on ea.school_id=f.enrolled_school_id
left join p on p.school_id=f.enrolled_school_id
where ca.level in ('High','Middle')
""").df()
cols = ["own_catchment_school", "other_district_neighborhood", "district_criteria_based",
        "district_citywide", "philadelphia_charter", "cyber_charter", "district_virtual",
        "alternative", "outside_district_list"]
w = d.pivot_table(index=["catchment_level", "catchment_school"], columns="dest", values="count",
                  aggfunc="sum", fill_value=0).reindex(columns=cols, fill_value=0)
out = []
for (lvl, name), r in w.sort_index().iterrows():
    v = {k: float(r[k]) for k in cols}
    total = sum(v.values())
    sup = {k for k in cols if 0 < v[k] < 20}
    if len(sup) == 1:  # one hidden cell could be recovered from the total
        rest = sorted((k for k in cols if k not in sup and v[k] > 0), key=lambda k: v[k])
        if rest:
            sup.add(rest[0])
    own = "suppressed" if "own_catchment_school" in sup else round(
        100 * v["own_catchment_school"] / total, 1)
    out.append([lvl.lower(), name, int(total)] + [
        "suppressed" if k in sup else int(v[k]) for k in cols] + [own])
write(
    "catchment_destinations.csv",
    ["catchment_level", "catchment_school", "resident_students"] + cols
    + ["pct_own_catchment_school"],
    out,
)
print("wrote", sorted(p.name for p in OUT.glob("*.csv")))
