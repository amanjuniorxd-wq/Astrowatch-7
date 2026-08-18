#!/usr/bin/env python3
"""Astrowatch — generate reproducible control (non-event) dates for the pilot
dataset. Fixed BEFORE any backtest is run, per spec item 15/16."""
import argparse
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from historical import controls, database, repository  # noqa: E402

DATASET_VERSION = "ASTROWATCH-HIST-001"
SEED = 20260814  # fixed, documented, equal to this session's date -- chosen before
                  # any astrological result was looked at, per the spec's own
                  # falsifiability requirement


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--db", default="historical_events.db")
    args = p.parse_args()

    conn = database.connect(args.db)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    cds = controls.build_random_controls(
        start_date="1900-01-01", end_date="2026-08-14", count=150, seed=SEED,
        region="GLOBAL", dataset_version=DATASET_VERSION, selection_timestamp=now,
        id_prefix="CTRL",
    )
    for c in cds:
        repository.insert_control_date(conn, c)
    conn.commit()
    conn.close()
    print(f"Generated {len(cds)} reproducible control dates (seed={SEED}, "
          f"window=1900-01-01..2026-08-14, method=RANDOM_DATE).")
    print(f"First 5: {[c.date for c in cds[:5]]}")


if __name__ == "__main__":
    main()
