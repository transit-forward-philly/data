# PA bill info scanner

Fetches palegis.us bill pages and extracts prime sponsor, cosponsors (with party and district), last action, and every roll call link (floor and committee). The roll call links give the numbers needed by PA Housing Votes' `fetch_rollcall.py` to pull member-by-member votes.

- **Run:**
  ```bash
  ~/projects/pa-housing-votes/pipeline/.venv/bin/python pipelines/pa_bill_info/fetch.py \
    datasets/pennsylvania/transportation-priorities-2027-28/bill-info \
    pipelines/pa_bill_info/transportation-bills.txt
  ```
  Needs `requests` and `beautifulsoup4` (the PA Housing Votes pipeline environment has both).
- **Bills file:** one per line, `hb291` or `hb291:2023` (session start year, default 2025). `transportation-bills.txt` lists the bills in the 2027–28 transportation memo.
- **Writes:** `bill-info.csv`, `cosponsors.csv`, `roll-calls.csv`, and the raw pages in `raw/`.
- **Offline test:** `--html-dir DIR` reads `DIR/<bill>-<year>.html` instead of fetching. It was checked against cached HB 2109 and HB 2186 pages: sponsors, 25 and 26 cosponsors, and roll calls 1119, 2264, 1075, 2201 and 1054 all match known values.

**Browser header.** palegis.us returns 403 to requests that don't look like a browser's, so the script sends a browser-style `User-Agent`, as PA Housing Votes' `scan_bills.py` does. The pages are public. Keep the delay at 1 second or more.

**Caveats.** Roll call labels that are vote counts (for example "145 56") are the page's yea and nay tallies, not bill names. Bills introduced in an earlier session have a different number there; look up the earlier number on the bill's current page first.
