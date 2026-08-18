#!/usr/bin/env python3
"""
Astrowatch — predict a "future event" theme from a kundli+Mahadasha pattern match
against the exploratory correlation table (see KUNDLI_CORRELATION_REPORT.md).

UNVALIDATED. This looks up which event category each chart feature was most often
associated with among 28 historical events and reports the raw evidence -- it does
NOT claim statistical validation (see build_kundli_correlations.py's methodology
note). Treat output as a lead, not a forecast with any calibrated confidence.

Usage:
    python3 scripts/predict_kundli_event.py --date 2026-12-25 --time 12:00 \
        --lat 35.0 --lon 139.0 [--tz UTC]
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone as dt_timezone
from zoneinfo import ZoneInfo

ASTROWATCH_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ASTROWATCH_DIR)

import coordinates
import historical.database as hdb
from build_kundli_correlations import build_all, predict_for_date, HIST_DB_PATH  # noqa: E402


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--date", required=True, help="YYYY-MM-DD")
    p.add_argument("--time", default="12:00", help="HH:MM local time")
    p.add_argument("--tz", default="UTC", help="IANA timezone name")
    p.add_argument("--lat", type=float, required=True)
    p.add_argument("--lon", type=float, required=True)
    args = p.parse_args()

    y, m, d = (int(x) for x in args.date.split("-"))
    hh, mm = (int(x) for x in args.time.split(":"))
    local_dt = datetime(y, m, d, hh, mm, tzinfo=ZoneInfo(args.tz))
    utc_dt = local_dt.astimezone(dt_timezone.utc)
    jd_ut = coordinates.julian_day(utc_dt.year, utc_dt.month, utc_dt.day,
                                     utc_dt.hour + utc_dt.minute / 60.0)

    conn = hdb.connect(HIST_DB_PATH)
    records = build_all(conn)
    conn.close()

    result = predict_for_date(jd_ut, args.lat, args.lon, records)
    print(json.dumps(result, indent=2, default=str))

    print("\n--- SUMMARY ---")
    print(f"UNVALIDATED pattern match for {args.date} {args.time} {args.tz} @ "
          f"({args.lat}, {args.lon}):")
    for feature, ev in result["evidence"].items():
        if ev["n"] == 0:
            print(f"  {feature}={ev['observed_value']}: no historical match in the "
                  f"28-event eligible sample (not seen before -- not evidence of "
                  f"anything, just an empty cell)")
        else:
            top = max(ev["historical_matches"].items(), key=lambda kv: kv[1])
            print(f"  {feature}={ev['observed_value']}: n={ev['n']} historical "
                  f"matches, most common category = {top[0]} ({top[1]}/{ev['n']})")
    print("\nThis is NOT a validated forecast. See KUNDLI_CORRELATION_REPORT.md caveats.")


if __name__ == "__main__":
    main()
