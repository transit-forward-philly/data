"""Parse the "Capital Project Summary List" of a SEPTA budget book into one row per capital project.

Usage: python parse_capital_projects.py <budget_book.txt> <out.csv>

Input is `pdftotext -layout` output of a SEPTA budget book (built on the FY2027 Budget Proposal,
pp.170-175). The summary list is a single table across several pages:

    Project Name | CPMS ID | S/TIP MPMS # | Project Budget | Prior Funding | FY Budget | 12-Year Total

grouped under ALL-CAPS program headers. Long names wrap onto a second line, which carries no numbers.
Money is $ millions. Blank cells mean the book left them blank; they are written as empty strings.
"""

import csv
import re
import sys

MONEY_RE = re.compile(r"\$\s?-?[\d,]+\.\d+")
HEADER_LINE = "Capital Project Summary List"
TABLE_END = "How to Read a Capital Project Profile"
SKIP_RE = re.compile(r"Project Name|Southeastern Pennsylvania|12-Year Capital Investments|12-Year$|Program$|"
                     r"FY 20\d\d\s+Program|Capital Project Summary List")


def is_code_list(text: str) -> bool:
    """CPMS IDs look like 'CRLBI, CRLJS' or 'CCPRS': short all-caps/digit tokens, comma-separated."""
    tokens = [t for t in re.split(r"[,\s]+", text) if t]
    return bool(tokens) and all(re.fullmatch(r"[A-Z0-9]{4,6}", t) and re.search(r"[A-Z]", t) for t in tokens)


def money_columns(line: str) -> dict[str, float | str]:
    """Map each $ amount to its column by x-position, since blank cells shift the count."""
    hits = [(m.start(), float(m.group().replace("$", "").replace(",", ""))) for m in MONEY_RE.finditer(line)]
    cols = {"budget_musd": "", "prior_funding_musd": "", "fy_budget_musd": "", "twelve_year_total_musd": ""}
    if not hits:
        return cols
    # Budget is always the first amount and the 12-year total always the last; middle cells may be blank.
    cols["budget_musd"] = hits[0][1]
    if len(hits) >= 2:
        cols["twelve_year_total_musd"] = hits[-1][1]
    middle = hits[1:-1]
    if len(middle) == 2:
        cols["prior_funding_musd"], cols["fy_budget_musd"] = middle[0][1], middle[1][1]
    elif len(middle) == 1:
        # Decide prior vs FY by x-position relative to the budget/total span.
        pos = (middle[0][0] - hits[0][0]) / max(hits[-1][0] - hits[0][0], 1)
        cols["prior_funding_musd" if pos < 0.55 else "fy_budget_musd"] = middle[0][1]
    return cols


def parse(lines: list[str]) -> list[dict]:
    start = next(i for i, line in enumerate(lines) if line.startswith(HEADER_LINE))
    end = next(i for i in range(start, len(lines)) if TABLE_END in lines[i])
    rows, program = [], ""
    for raw in lines[start:end]:
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped or SKIP_RE.search(stripped):
            continue
        if not MONEY_RE.search(line):
            parts = [p for p in re.split(r"\s{2,}", stripped) if p]
            if len(parts) == 1 and not is_code_list(stripped) and stripped.upper() == stripped \
                    and len(re.findall(r"[A-Z]{3,}", stripped)) >= 2:
                program = stripped
            elif rows:
                # Wrapped continuation: name text and/or overflow CPMS codes.
                for part in parts:
                    if is_code_list(part):
                        rows[-1]["cpms"] = f"{rows[-1]['cpms']} {part}".strip()
                    else:
                        # A wrapped line can mix words and a trailing CPMS code with single spacing.
                        words = part.split()
                        while len(words) > 1 and is_code_list(words[-1]):
                            rows[-1]["cpms"] = f"{rows[-1]['cpms']} {words.pop()}".strip()
                        rows[-1]["project"] += " " + " ".join(words)
            continue
        first_money = MONEY_RE.search(line).start()
        left = line[:first_money].rstrip()
        # Left side = name, CPMS, MPMS separated by runs of 2+ spaces.
        parts = [p for p in re.split(r"\s{2,}", left.strip()) if p]
        mpms = parts.pop() if parts and re.fullmatch(r"\d{4,6}|N/A", parts[-1]) else ""
        cpms = parts.pop() if len(parts) > 1 else ""
        rows.append({"program": program, "project": " ".join(parts), "cpms": cpms, "tip_mpms": mpms,
                     **money_columns(line)})
    return rows


def main() -> None:
    src, out = sys.argv[1], sys.argv[2]
    with open(src, errors="ignore") as fh:
        rows = parse(fh.read().split("\n"))
    fields = ["program", "project", "cpms", "tip_mpms", "budget_musd", "prior_funding_musd",
              "fy_budget_musd", "twelve_year_total_musd"]
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    total = sum(r["twelve_year_total_musd"] or 0 for r in rows)
    print(f"wrote {len(rows)} projects, 12-year total ${total:,.1f}M -> {out}")


if __name__ == "__main__":
    main()
