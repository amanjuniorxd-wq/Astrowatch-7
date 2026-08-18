#!/usr/bin/env python3
"""Astrowatch — freeze a dataset_version. After this, the schema's own triggers
reject any silent edit/delete to that version's events/control_dates rows."""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from historical import database, versioning  # noqa: E402

KNOWN_LIMITATIONS = (
    "136 events total, far below the 500-2000 target (quality over quantity, per "
    "spec item 20). 117/136 events (86%) are UNVERIFIED (general reference "
    "knowledge, not independently re-checked via a live source this session) -- "
    "see HISTORICAL_DATA_QUALITY_REPORT.md. Only USGS earthquake events (16) carry "
    "machine-precision date/time/location; nearly everything else has "
    "time_confidence UNKNOWN or APPROXIMATE and no coordinates. UCDP/ACLED/GDELT/"
    "EM-DAT/NOAA integrations are interface-only, not executed (network/credential "
    "constraints -- see historical/ingestion/*.py). Deduplication is heuristic, "
    "not exhaustive. 3 events carry DISPUTED date_confidence with the specific "
    "source disagreement documented in manual_review.csv."
)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--db", default="historical_events.db")
    p.add_argument("--version", default="ASTROWATCH-HIST-001")
    args = p.parse_args()

    conn = database.connect(args.db)
    result = versioning.freeze_dataset_version(conn, args.db, args.version, KNOWN_LIMITATIONS)
    conn.close()
    print(f"Froze {args.version}:")
    for k, v in result.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
