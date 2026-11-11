"""Drop empty optional tables from a GTFS zip so R5 will load it.

R5 (via gtfs-lite) refuses a feed containing a table that exists but has no
data rows — SEPTA's rail feed ships an empty `calendar_dates.txt`, which is
legal GTFS (the table is optional when `calendar.txt` is present) but fatal to
the loader:

    EmptyTableError: calendar_dates line 0: Table is present in zip file,
                     but it has no entries.

Dropping an empty optional table is lossless: an empty file and an absent file
carry the same information. A REQUIRED table that is empty is a real defect and
raises instead of being silently dropped.

Usage:
    python clean_gtfs.py in.zip out.zip
"""

from __future__ import annotations

import shutil
import sys
import zipfile
from pathlib import Path


# GTFS tables that must be present and non-empty for a usable feed.
REQUIRED = {"agency.txt", "routes.txt", "trips.txt", "stops.txt", "stop_times.txt"}


class EmptyRequiredTableError(Exception):
    """A table GTFS requires is present but has no data rows."""


def row_count(payload: bytes) -> int:
    """Data rows in a CSV payload, excluding the header."""
    lines = payload.decode("utf8", "replace").strip().splitlines()
    return max(0, len(lines) - 1)


def clean(source: Path, destination: Path) -> list[str]:
    """Copy `source` to `destination`, omitting empty optional tables."""
    dropped = []
    with zipfile.ZipFile(source) as src:
        with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as out:
            for name in src.namelist():
                payload = src.read(name)
                if name.endswith(".txt") and row_count(payload) == 0:
                    if name in REQUIRED:
                        raise EmptyRequiredTableError(
                            f"{source.name}: required table {name} has no rows — "
                            "this feed is not usable, not merely untidy"
                        )
                    dropped.append(name)
                    continue
                out.writestr(name, payload)
    return dropped


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    source, destination = Path(sys.argv[1]), Path(sys.argv[2])
    dropped = clean(source, destination)
    if dropped:
        print(f"{source.name}: dropped empty {', '.join(dropped)}")
    else:
        shutil.copy(source, destination)
        print(f"{source.name}: nothing to drop")


if __name__ == "__main__":
    main()
