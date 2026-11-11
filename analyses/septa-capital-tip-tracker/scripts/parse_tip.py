"""Parse DVRPC's TIP for Pennsylvania project listings into one row per MPMS project.

Usage: python parse_tip.py <tip.txt> <out.csv>

Input is `pdftotext -layout` output of the DVRPC TIP for PA document (built on the Draft FFY2027 TIP,
FFY27-FFY30). Each listing is:

    <MPMS> - <Title>
    <description paragraph>
    Lead Agency: ...   Project Type: ...   County: ...   Total Cost: $...
    Phase | Fund Source | Prior | FY2027 | FY2028 | FY2029 | FY2030 | Future | Total
    ...
    Total Programmed  $prior $fy1 $fy2 $fy3 $fy4 $future $total

Money columns are whole dollars in the source; written here as $ millions.
"""

import csv
import re
import sys

TITLE_RE = re.compile(r"^(\d{4,6}) - (\S.*)$")
FIELD_RE = re.compile(r"^(Lead Agency|Project Type|County|Town|Air Quality Code|MRP ID|Total Cost):\s+(.*)$")
MONEY_RE = re.compile(r"\$[\d,]+")
FIELD_KEYS = {"Lead Agency": "lead_agency", "Project Type": "project_type", "County": "county",
              "Town": "town", "Air Quality Code": "aq_code", "MRP ID": "mrp_id", "Total Cost": "total_cost"}
YEAR_COLS = ["prior", "ffy2027", "ffy2028", "ffy2029", "ffy2030", "future", "total_programmed"]


def to_musd(text: str) -> float:
    return round(int(text.replace("$", "").replace(",", "")) / 1e6, 3)


def parse(lines: list[str]) -> list[dict]:
    rows: list[dict] = []
    current: dict | None = None
    in_description = False
    for raw in lines:
        line = raw.strip()
        m = TITLE_RE.match(line)
        if m and not m.group(2).startswith("Future Years"):  # skip wrapped "(FY 2031 - FY 2037 Future Years)"
            current = {"mpms": m.group(1), "title": m.group(2).strip(), "description": ""}
            rows.append(current)
            in_description = True
            continue
        if current is None or not line:
            continue
        f = FIELD_RE.match(line)
        if f:
            in_description = False
            value = f.group(2).strip()
            current[FIELD_KEYS[f.group(1)]] = to_musd(value) if f.group(1) == "Total Cost" and "$" in value \
                else value
            continue
        if in_description:
            current["description"] += (" " if current["description"] else "") + line
            continue
        if line.startswith("Total Programmed"):
            amounts = MONEY_RE.findall(line)
            if len(amounts) == len(YEAR_COLS):
                current.update({k: to_musd(v) for k, v in zip(YEAR_COLS, amounts)})
            current = None  # a listing ends at its Total Programmed row
    return rows


def main() -> None:
    src, out = sys.argv[1], sys.argv[2]
    with open(src, errors="ignore") as fh:
        rows = parse(fh.read().split("\n"))
    # The same MPMS can appear in summary tables before its full listing; keep the listing with money.
    by_mpms: dict[str, dict] = {}
    for r in rows:
        if "total_programmed" in r or r["mpms"] not in by_mpms:
            by_mpms[r["mpms"]] = r
    fields = ["mpms", "title", "lead_agency", "project_type", "county", "town", "aq_code", "mrp_id",
              "total_cost", *YEAR_COLS, "description"]
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(by_mpms.values())
    print(f"wrote {len(by_mpms)} MPMS projects -> {out}")


if __name__ == "__main__":
    main()
