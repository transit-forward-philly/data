"""Shared settings for the SEPTA vehicle-tracking pipeline."""

import os
from pathlib import Path

# DuckDB spills to TFP_DATA_DIR past this, which keeps laptops out of swap.
MEMORY_LIMIT = os.environ.get("TFP_MEMORY_LIMIT", "3GB")
THREADS = int(os.environ.get("TFP_THREADS", "2"))


def data_dir():
    """Where large working files live. Set TFP_DATA_DIR to a disk with ~20 GB free."""
    path = os.environ.get("TFP_DATA_DIR")
    if not path:
        raise SystemExit("Set TFP_DATA_DIR to a folder for working data, e.g. an external drive.")
    return Path(path)
