"""Fetch palegis.us bill pages and pull out sponsors, cosponsors, status and roll call links.

Usage:
    python fetch.py OUTDIR BILLS_FILE [--html-dir DIR] [--delay SECONDS]

BILLS_FILE has one bill per line: hb291 or hb291:2023 (session start year, default 2025).

Writes into OUTDIR:
    bill-info.csv     one row per bill
    cosponsors.csv    one row per cosponsor per bill
    roll-calls.csv    every roll call link on each bill page (floor and committee)
    raw/<bill>-<year>.html   the pages as fetched, so parsing can be rerun and diffed

palegis.us rejects requests that do not look like a browser's, so requests are sent with a
browser-style User-Agent, as the PA Housing Votes pipeline does (see its scan_bills.py).
The pages are public. Keep --delay at 1 second or more.

With --html-dir, pages are read from DIR/<bill>-<year>.html instead of fetched, which is how
the parser is tested offline.
Needs: requests, beautifulsoup4.
"""
import argparse
import csv
import re
import sys
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

UA = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}
NBSP = "\xa0"
PERSON = re.compile(r"^(Rep\.|Sen\.|Representative|Senator)\s+(.*)$")
DIST = re.compile(r"^(House|Senate) District (\d+)$")
MONTHS = {m: i for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1)}


def url(bill, year):
    return f"https://www.palegis.us/legislation/bills/{year}/{bill}"


def lines(soup):
    return [t.replace(NBSP, " ").strip() for t in soup.get_text("\n", strip=True).split("\n") if t.strip()]


def person_at(t, i):
    """Read name, party, chamber, district from a 'Rep. X / D / House District N' triple at index i."""
    m = PERSON.match(t[i])
    if not m or i + 2 >= len(t):
        return None
    d = DIST.match(t[i + 2])
    if t[i + 1] not in ("D", "R", "I") or not d:
        return None
    return {"name": m.group(2).strip(), "party": t[i + 1], "chamber": d.group(1).lower(), "district": d.group(2)}


def iso(text):
    m = re.search(r"([A-Z][a-z]{2})[a-z]*\.?\s+(\d{1,2}),\s+(\d{4})", text)
    return f"{m.group(3)}-{MONTHS[m.group(1)]:02d}-{int(m.group(2)):02d}" if m and m.group(1) in MONTHS else ""


def parse(html, bill, year):
    soup = BeautifulSoup(html, "html.parser")
    t = lines(soup)
    info = {"bill": bill.upper(), "session_start_year": year, "source_url": url(bill, year)}

    # Title: the long "An Act ..." / "A Resolution ..." line near the top
    info["title"] = next((x for x in t[:120] if re.match(r"^(An Act|A Resolution|A Joint Resolution)", x)), "")
    info["short_name"] = ""
    if "Co-Sponsorship Memo" in t:
        j = t.index("Co-Sponsorship Memo")
        nxt = t[j + 1] if j + 1 < len(t) else ""
        info["short_name"] = "" if nxt.startswith("-") or nxt in ("Current Text",) else nxt

    # Prime sponsor and cosponsors
    prime, cos = None, []
    if "Prime Sponsor" in t:
        k = t.index("Prime Sponsor")
        prime = person_at(t, k + 1)
        end = next((n for n in range(k, len(t)) if t[n] == "Bill Status & History"), len(t))
        n = k + 1
        while n < end:
            p = person_at(t, n) if n != k + 1 else None
            if p and PERSON.match(t[n]) and t[n].startswith(("Rep.", "Sen.")):
                cos.append(p)
                n += 3
            else:
                n += 1
    info["prime_sponsor"] = prime["name"] if prime else ""
    info["prime_party"] = prime["party"] if prime else ""
    info["prime_district"] = prime["district"] if prime else ""
    info["cosponsors_total"] = len(cos)
    info["cosponsors_d"] = sum(c["party"] == "D" for c in cos)
    info["cosponsors_r"] = sum(c["party"] == "R" for c in cos)

    # Status and history
    status = {"last_action": "", "last_action_date": "", "last_action_chamber": ""}
    hist = []
    if "Bill Status & History" in t:
        s = t.index("Bill Status & History")
        e = next((n for n in range(s, len(t)) if t[n] == "Printers Numbers"), len(t))
        block = t[s:e]
        if "Last Action:" in block:
            a = block.index("Last Action:")
            parts = []
            for c in block[a + 1:a + 8]:
                if c in ("House", "Senate") and parts:
                    status["last_action_chamber"] = c.lower()
                    break
                parts.append(c)
            la = re.sub(r"\s+,\s+", ", ", " ".join(parts))
            status["last_action"] = la
            status["last_action_date"] = iso(la)
        hist = [x for x in block if re.search(r"(20\d\d)", x) and not x.startswith("PN")]
    info.update(status)
    info["history"] = " | ".join(hist)
    info["first_action_text"] = hist[0] if hist else ""
    pns = [x.replace("PN ", "") for x in t if x.startswith("PN ") and re.fullmatch(r"PN \d+", x)]
    info["latest_printers_number"] = pns[0] if pns else ""
    info["floor_passed"] = "yes" if any("final passage" in h.lower() for h in hist) else "no"

    # Roll call links
    rcs, seen = [], set()
    for a in soup.find_all("a"):
        href = a.get("href", "")
        if "roll-call" not in href.lower():
            continue
        r = {"bill": bill.upper(), "session_start_year": year, "label": a.get_text(" ", strip=True).replace(NBSP, " ")}
        if m := re.search(r"rcNum=(\d+)", href):
            r.update(type="floor", chamber="senate" if "senate/" in href else "house", id=m.group(1))
        elif m := re.search(r"rollcallid=(\d+)", href):
            cc = re.search(r"committeecode=(\d+)", href)
            r.update(type="committee", chamber="senate" if "senate/" in href else "house", id=m.group(1),
                     committee_code=cc.group(1) if cc else "")
        else:
            continue
        key = (r["type"], r["chamber"], r["id"])
        if key in seen:
            continue
        seen.add(key)
        r["href"] = href if href.startswith("http") else "https://www.palegis.us" + href
        rcs.append(r)
    info["roll_calls_found"] = len(rcs)
    return info, cos, rcs


def write(path, rows, fields):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("outdir")
    ap.add_argument("bills_file")
    ap.add_argument("--html-dir")
    ap.add_argument("--delay", type=float, default=1.5)
    a = ap.parse_args()
    out = Path(a.outdir)
    (out / "raw").mkdir(parents=True, exist_ok=True)
    bills = []
    for ln in Path(a.bills_file).read_text().splitlines():
        ln = ln.strip().lower()
        if ln and not ln.startswith("#"):
            b, _, y = ln.partition(":")
            bills.append((b, y or "2025"))
    infos, allcos, allrcs = [], [], []
    for b, y in bills:
        name = f"{b}-{y}.html"
        if a.html_dir:
            html = (Path(a.html_dir) / name).read_text()
        else:
            r = requests.get(url(b, y), headers=UA, timeout=30)
            if r.status_code != 200:
                print(f"{b} {y}: HTTP {r.status_code}, skipped", file=sys.stderr)
                time.sleep(a.delay)
                continue
            html = r.text
            (out / "raw" / name).write_text(html)
            time.sleep(a.delay)
        info, cos, rcs = parse(html, b, y)
        for c in cos:
            allcos.append({"bill": info["bill"], "session_start_year": y, **c})
        infos.append(info)
        allrcs += rcs
        print(f"{info['bill']} ({y}): {info['prime_sponsor'] or '?'}; {len(cos)} cosponsors; {len(rcs)} roll calls; {info['last_action'][:70]}")
    write(out / "bill-info.csv", infos, ["bill", "session_start_year", "title", "short_name", "prime_sponsor", "prime_party",
          "prime_district", "cosponsors_total", "cosponsors_d", "cosponsors_r", "last_action", "last_action_date",
          "last_action_chamber", "floor_passed", "latest_printers_number", "roll_calls_found", "source_url"])
    write(out / "cosponsors.csv", allcos, ["bill", "session_start_year", "name", "party", "chamber", "district"])
    write(out / "roll-calls.csv", allrcs, ["bill", "session_start_year", "type", "chamber", "id", "committee_code", "label", "href"])


if __name__ == "__main__":
    main()
