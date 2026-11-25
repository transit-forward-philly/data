"""Pull the Pennsylvania transit projects (SEPTA) out of DVRPC's long-range plan, with costs.

Usage (needs `pdftotext` from poppler):
    python build.py OUTPUT_CSV [CACHE_DIR]

Sources:
    DVRPC, Update: Connections 2050 Long-Range Plan, Appendices (May 2026),
        https://www.dvrpc.org/Reports/25140.pdf, Appendix F, Financial Plan:
        Table F-25 "Pennsylvania Transit MRPs, Funded" (PDF pp. 251-256), millions of
        year-of-expenditure dollars, and the transit rows of Table F-30 "Pennsylvania MRPs,
        Unfunded" (PDF pp. 271-277), millions of 2025 dollars.
    DVRPC, Connections 2050 Amendment 1 (adopted September 2026),
        https://www.dvrpc.org/Reports/26140.pdf, Table 5 "Revised Major Regional Transit
        Projects", which updates six funded SEPTA costs from SEPTA's FY27 capital budget.

Every row is a Major Regional Project (MRP) with an ID beginning PAT. Rows are read from the PDF
text layout; the checks at the end fail loudly if the counts change or a scope looks cut off.
"""
import csv
import re
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

APPENDIX = "https://www.dvrpc.org/Reports/25140.pdf"
AMENDMENT = "https://www.dvrpc.org/Reports/26140.pdf"
FUNDED_PAGES, UNFUNDED_PAGES = (251, 256), (271, 277)
EXPECT = {"funded": 39, "unfunded": 45, "amended": 6}


def fetch(url, cache):
    path = Path(cache) / url.rsplit("/", 1)[1]
    # a cached file that is not a PDF (say, a saved HTML error page) is fetched again
    if not path.exists() or path.read_bytes()[:4] != b"%PDF":
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read()
        if body[:4] != b"%PDF":
            raise SystemExit(f"{url} did not return a PDF")
        path.write_bytes(body)
    return path


def text(pdf, first=None, last=None):
    args = ["pdftotext", "-layout"] + (["-f", str(first), "-l", str(last)] if first else []) + [str(pdf), "-"]
    return subprocess.run(args, capture_output=True, text=True, check=True).stdout.split("\n")


STOP = ("Source", "Table", "F-", "Unfunded", "DELAWARE", "MRP ID", "UPDATE:")
HEADER_REST = re.compile(r"^\s*(Period\*|\(Millions|\(YOE|of \$)")
ID = re.compile(r"^\s*PA[A-Z]\d{3}")
# scopes that DVRPC printed without a closing period
NO_PERIOD = {"PAT087"}


def join(parts):
    """Join wrapped pieces with a space, except after a line-ending hyphen or dash."""
    out = ""
    for p in (p.strip() for p in parts):
        if p:
            out += p if not out or out.endswith(("-", "—")) else " " + p
    return out


def rows(lines, table, basis):
    out, i = [], 0
    last = None  # the most recent PAT row, still open for text that resumes on the next page
    header = None  # column starts from the most recent page header
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("MRP ID"):
            header = {k: line.index(k) for k in ("Facility", "Project Scope", "Location")}
            i += 1
            continue
        m = re.match(r"^(\s*)(PAT\d{3})(\s+)", line)
        cost = re.search(r"\$\s?([\d,]+\.\d)", line)
        if ID.match(line):
            last = None
        if not (m and cost):
            # text at the top of a page, after the repeated header and before the first ID,
            # continues the last row of the previous page
            if last and header and line.strip() and not HEADER_REST.match(line) \
                    and not line.strip().startswith(STOP):
                cols = sorted((v, k) for k, v in header.items())
                for seg in re.finditer(r"\S+(?: \S+)*", line):
                    col = [k for v, k in cols if v <= seg.start() + 2]
                    key = {"Facility": "fac", "Project Scope": "scope", "Location": "loc"}.get(col[-1] if col else "")
                    if key:
                        last[key].append(seg.group())
            i += 1
            continue
        fac0 = m.end()
        sc0 = fac0 + re.search(r"\S(\s{2,})\S", line[fac0:]).end() - 1
        segs = [s.start() for s in re.finditer(r"\S+(?: \S+)*", line)]
        # the location column starts at least 40 characters right of where the scope starts;
        # the scope column is never narrower than that, so nearer segments are scope text
        loc0 = next((p for p in segs if sc0 + 40 <= p < cost.start()), cost.start())
        parts = dict(fac=[line[fac0:sc0]], scope=[line[sc0:loc0]], loc=[line[loc0:cost.start()]])
        j = i + 1
        while j < len(lines) and lines[j].strip() and not ID.match(lines[j]) \
                and not lines[j].strip().startswith(STOP):
            t = lines[j]
            parts["fac"].append(t[fac0:sc0]); parts["scope"].append(t[sc0:loc0]); parts["loc"].append(t[loc0:cost.start()])
            j += 1
        last = parts
        out.append(dict(table=table, mrp_id=m.group(2), parts=parts,
                        cost_millions=cost.group(1).replace(",", ""), dollar_basis=basis))
        i = j
    for r in out:
        p = r.pop("parts")
        keep = lambda xs: [x for x in xs if not re.fullmatch(r"[\d–-]+", x.strip())]
        # the plan-period column (e.g. "1–2") sits beside the location in the layout; drop it
        loc = re.sub(r"(?<!\S)\d(?:[–-]\d)?(?!\S)", " ", join(keep(p["loc"])))
        r.update(facility=join(keep(p["fac"])), scope=join(keep(p["scope"])),
                 location=re.sub(r"\s+", " ", loc).strip())
    return out


def amendments(lines):
    # the last match is the table itself; earlier ones are the table of contents
    start = [i for i, l in enumerate(lines) if l.strip().startswith("Table 5: Revised Major Regional Transit")][-1]
    out = {}
    for i in range(start, min(start + 80, len(lines))):
        m = re.search(r"(PAT\d{3})\s+(.+?)\s{2,}(.+?)\s{2,}\$\s?([\d,]+\.\d)", lines[i])
        if m:
            note = [m.group(3).strip()]
            col = lines[i].find(m.group(3))
            for t in lines[i + 1:i + 20]:
                if re.search(r"PAT\d{3}", t) or t.strip().startswith(("Source", "Table", "Updates to transit")):
                    break
                if re.search(r"MRP ID|YOE|Categories|UPDATE:", t):
                    continue  # repeated header at a page break
                indent = len(t) - len(t.lstrip())
                # after a page break the column sits further right, alone on its line
                piece = t.strip() if indent >= col else (t[col:col + 45].strip() if len(t) > col else "")
                if piece:
                    note.append(piece)
            # drop footnote markers, e.g. the "5" in "preliminary infrastructure work, 5 and shift"
            text_ = re.sub(r"(?<=[,.;]) \d{1,2}(?= )", "", join(note))
            out[m.group(1)] = (m.group(4).replace(",", ""), text_)
    return out


def main(out_csv, cache=None):
    cache = cache or tempfile.mkdtemp()
    app, amd = fetch(APPENDIX, cache), fetch(AMENDMENT, cache)
    funded = rows(text(app, *FUNDED_PAGES), "F-25 funded", "year of expenditure")
    unfunded_lines = text(app, *UNFUNDED_PAGES)
    unfunded = rows(unfunded_lines, "F-30 unfunded", "2025 dollars")
    amended = amendments(text(amd))
    got = {"funded": len(funded), "unfunded": len(unfunded), "amended": len(amended)}
    if got != EXPECT:
        raise SystemExit(f"row counts changed: {got} (expected {EXPECT}); check the PDF layout")
    cut = [r["mrp_id"] for r in funded + unfunded if not r["scope"].endswith(".") and r["mrp_id"] not in NO_PERIOD]
    if cut:
        raise SystemExit(f"scope text looks cut off (no closing period): {cut}; check the PDF layout")
    for r in funded + unfunded:
        a = amended.get(r["mrp_id"]) if r["table"] == "F-25 funded" else None
        r["amendment1_cost_millions"] = a[0] if a else ""
        r["amendment1_note"] = a[1] if a else ""
        r["current_cost_millions"] = a[0] if a else r["cost_millions"]
    cols = ["table", "mrp_id", "facility", "scope", "location", "cost_millions", "amendment1_cost_millions",
            "amendment1_note", "current_cost_millions", "dollar_basis"]
    with open(out_csv, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, lineterminator="\n")
        w.writeheader()
        w.writerows(funded + unfunded)
    print(got)


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2] if len(sys.argv) == 3 else None)
