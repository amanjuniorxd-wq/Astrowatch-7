#!/usr/bin/env python3
"""Astrowatch — initialize historical_events.db from the schema. Real, executable."""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from historical import database  # noqa: E402


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--db", default="historical_events.db")
    p.add_argument("--overwrite", action="store_true")
    args = p.parse_args()
    conn = database.initialize_db(args.db, overwrite=args.overwrite)
    conn.close()
    print(f"initialized {args.db}")


if __name__ == "__main__":
    main()
