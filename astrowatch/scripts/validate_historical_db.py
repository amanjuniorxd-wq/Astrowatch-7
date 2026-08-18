#!/usr/bin/env python3
"""Astrowatch — validate historical_events.db. Flags issues; never silently repairs.
Exits non-zero on any FATAL issue (spec item 21)."""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from historical import database, validation  # noqa: E402


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--db", default="historical_events.db")
    args = p.parse_args()

    conn = database.connect(args.db)
    issues = validation.validate(conn)
    conn.close()

    fatal = [i for i in issues if i.severity == "FATAL"]
    warnings = [i for i in issues if i.severity == "WARNING"]

    print(f"Validation of {args.db}")
    print(f"  FATAL issues:   {len(fatal)}")
    print(f"  WARNING issues: {len(warnings)}")
    print()
    for i in issues:
        print(f"[{i.severity}] {i.check} | {i.event_id} | {i.detail}")

    code = validation.exit_code_for(issues)
    print()
    print("RESULT:", "FAIL (fatal issues present)" if code else "PASS (no fatal issues)")
    sys.exit(code)


if __name__ == "__main__":
    main()
