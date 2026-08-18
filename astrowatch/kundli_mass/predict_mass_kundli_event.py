#!/usr/bin/env python3
"""
Astrowatch — one-off astrological calculation for an arbitrary date/time/location,
pattern-matched against the 519-event kundli_mass table.

LABEL (enforced in output, per explicit user instruction): this is an ASTROLOGICAL
CALCULATION, not a forecast, not statistically validated, not to be relied on. See
analyze_mass_kundli.ASTROLOGICAL_CALCULATION_DISCLAIMER and MASS_KUNDLI_CORRELATION_
REPORT.md's caveats for why.

Usage:
    python3 kundli_mass/predict_mass_kundli_event.py --date 2026-09-05 --time 12:00 \
        --tz America/New_York --lat 40.7128 --lon -74.0060
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone as dt_timezone
from zoneinfo import ZoneInfo
from collections import defaultdict

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
ASTROWATCH_DIR = os.path.dirname(THIS_DIR)
sys.path.insert(0, ASTROWATCH_DIR)
sys.path.insert(0, THIS_DIR)

import coordinates
from kundli import compute_kundli
from mahadasha import compute_dasha_state
from analyze_mass_kundli import load_records, correlate, ASTROLOGICAL_CALCULATION_DISCLAIMER


def predict_single(jd_ut, lat, lon, records):
    chart = compute_kundli(jd_ut, lat, lon)
    dasha = compute_dasha_state(jd_ut, chart.grahas["moon"].sidereal_lon_deg)
    features = {
        "mahadasha_lord": dasha.mahadasha.lord,
        "antardasha_lord": dasha.antardasha.lord,
        "ascendant_rashi": chart.ascendant_rashi.rashi_name,
        "ascendant_nakshatra": chart.ascendant_nakshatra.nakshatra_name,
        "moon_rashi": chart.grahas["moon"].rashi.rashi_name,
        "moon_nakshatra": chart.grahas["moon"].nakshatra.nakshatra_name,
        "sun_rashi": chart.grahas["sun"].rashi.rashi_name,
    }
    evidence = {}
    score = defaultdict(int)
    for fk, value in features.items():
        if fk == "ascendant_nakshatra":
            continue  # not tabulated in the mass correlation tables (kept for display only)
        table = correlate(records, fk)
        counts = dict(table.get(value, {}))
        evidence[fk] = {"value": value, "historical_counts": counts, "n": sum(counts.values())}
        for cat, n in counts.items():
            score[cat] += n
    return {
        "jd_ut": jd_ut, "latitude": lat, "longitude": lon,
        "chart_features": features, "evidence": evidence,
        "resonance_score": dict(score),
        "label": "ASTROLOGICAL CALCULATION -- not a forecast, not to be relied on",
        "disclaimer": ASTROLOGICAL_CALCULATION_DISCLAIMER,
    }


def main():
    p = argparse.ArgumentParser(description="Astrological calculation for a given date/time/location "
                                             "(pattern-match, NOT a forecast).")
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

    records = load_records()
    result = predict_single(jd_ut, args.lat, args.lon, records)

    print("=== ASTROLOGICAL CALCULATION (not a forecast) ===")
    print(f"Input: {args.date} {args.time} {args.tz} @ ({args.lat}, {args.lon})\n")
    print("Chart features:")
    for k, v in result["chart_features"].items():
        print(f"  {k}: {v}")
    print("\nHistorical co-occurrence (519-event table, unvalidated):")
    for fk, ev in result["evidence"].items():
        if ev["n"] == 0:
            print(f"  {fk}: no historical match in the sample")
        else:
            top = max(ev["historical_counts"].items(), key=lambda kv: kv[1])
            print(f"  {fk}={ev['value']}: n={ev['n']}, most-associated category="
                  f"{top[0]} ({top[1]}/{ev['n']})")
    print(f"\nMechanical resonance score: {result['resonance_score']}")
    print(f"\n{result['disclaimer']}")

    out_path = os.path.join(THIS_DIR, "last_single_calculation.json")
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2, default=str)
    print(f"\n(Full result also written to {out_path})")


if __name__ == "__main__":
    main()
