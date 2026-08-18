#!/usr/bin/env python3
"""
Astrowatch — build kundli charts + Mahadasha state for every eligible HIST-002 event,
and extract simple frequency correlations against event category.

ELIGIBILITY: an event needs a real geographic location (latitude/longitude present)
AND a known time (time_confidence EXACT or APPROXIMATE, so a real start_time value
exists) to get a genuine Ascendant/house chart -- a house-sensitive chart computed
from a fabricated or unknown time/location would be meaningless. This is a REAL
subset of HIST-002 (read-only query; nothing is written back to
historical_events_v2.db), not a new/fabricated dataset.

METHODOLOGY NOTE (explicit, per user instruction for this task): this pass optimizes
for speed over statistical rigor -- it reports every correlation it finds in the
eligible 28-event sample without holding out a validation set, without correcting for
multiple comparisons, and without a significance test. That is a deliberate choice for
this specific exploratory task, NOT the same standard as ASTROWATCH-BT-001/BT-002's
blind-backtest methodology elsewhere in this project. Every output is labeled
UNVALIDATED / PATTERN-BASED, not a validated predictor, and every reported frequency
carries its raw sample size so nobody has to take "correlated" on faith.
"""
import csv
import json
import os
import sys
from collections import defaultdict

ASTROWATCH_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ASTROWATCH_DIR)

import historical.database as hdb
import historical.repository as hrepo
import coordinates
from kundli import compute_kundli
from mahadasha import compute_dasha_state

HIST_DB_PATH = os.path.join(ASTROWATCH_DIR, "historical_events_v2.db")
DATASET_VERSION = "ASTROWATCH-HIST-002"
OUT_DIR = os.path.join(ASTROWATCH_DIR, "kundli_analysis")


def eligible_events(conn):
    rows = hrepo.get_events(conn, dataset_version=DATASET_VERSION)
    out = []
    for r in rows:
        if r["latitude"] is None or r["longitude"] is None:
            continue
        if r["time_confidence"] not in ("EXACT", "APPROXIMATE") or not r["start_time"]:
            continue
        out.append(r)
    return out


def jd_ut_for_event(row) -> float:
    """Uses the event's own stored timezone (IANA name) to convert local start_time
    to UT, same convention as backtest/predictor.py's _local_to_utc_hour()."""
    from datetime import datetime, timezone as dt_timezone
    from zoneinfo import ZoneInfo
    y, m, d = (int(x) for x in row["start_date"].split("-"))
    hh, mm = (int(x) for x in row["start_time"].split(":"))
    tzname = row["timezone"]
    if tzname:
        local_dt = datetime(y, m, d, hh, mm, tzinfo=ZoneInfo(tzname))
        utc_dt = local_dt.astimezone(dt_timezone.utc)
    else:
        utc_dt = datetime(y, m, d, hh, mm, tzinfo=dt_timezone.utc)
    return coordinates.julian_day(utc_dt.year, utc_dt.month, utc_dt.day,
                                    utc_dt.hour + utc_dt.minute / 60.0)


def build_all(conn):
    events = eligible_events(conn)
    records = []
    for row in events:
        jd_ut = jd_ut_for_event(row)
        chart = compute_kundli(jd_ut, row["latitude"], row["longitude"])
        dasha = compute_dasha_state(jd_ut, chart.grahas["moon"].sidereal_lon_deg)
        records.append({
            "event_id": row["event_id"], "event_name": row["event_name"],
            "event_type": row["event_type"], "event_subtype": row["event_subtype"],
            "start_date": row["start_date"], "start_time": row["start_time"],
            "time_confidence": row["time_confidence"],
            "ascendant_rashi": chart.ascendant_rashi.rashi_name,
            "ascendant_nakshatra": chart.ascendant_nakshatra.nakshatra_name,
            "moon_rashi": chart.grahas["moon"].rashi.rashi_name,
            "moon_nakshatra": chart.grahas["moon"].nakshatra.nakshatra_name,
            "moon_house": chart.grahas["moon"].house,
            "mahadasha_lord": dasha.mahadasha.lord,
            "antardasha_lord": dasha.antardasha.lord,
            "ayanamsha_source": chart.ayanamsha_source,
            **{f"{g}_rashi": p.rashi.rashi_name for g, p in chart.grahas.items()},
            **{f"{g}_house": p.house for g, p in chart.grahas.items()},
        })
    return records


def correlate(records, feature_key):
    """{feature_value: {event_type: count}} plus overall event_type base rates."""
    table = defaultdict(lambda: defaultdict(int))
    base_rate = defaultdict(int)
    for r in records:
        table[r[feature_key]][r["event_type"]] += 1
        base_rate[r["event_type"]] += 1
    return table, base_rate


def format_correlation_report(records) -> str:
    lines = [
        "# Kundli / Mahadasha Correlation Report (exploratory, unvalidated)",
        "",
        f"Built from `historical_events_v2.db` (ASTROWATCH-HIST-002), read-only. "
        f"{len(records)} of 140 events had both a known time (EXACT or APPROXIMATE) "
        f"and known coordinates -- the minimum needed for a real Ascendant/house "
        f"chart. This is NOT a validated predictor -- see the methodology note in "
        f"`scripts/build_kundli_correlations.py` and the caveats at the end of this "
        f"file.",
        "",
        "## Sample composition",
        "",
    ]
    base = defaultdict(int)
    for r in records:
        base[r["event_type"]] += 1
    for etype, n in sorted(base.items(), key=lambda kv: -kv[1]):
        lines.append(f"- {etype}: {n}")
    lines.append("")
    lines.append(
        f"**{base.get('NATURAL_DISASTER', 0)} of {len(records)} eligible events are "
        f"NATURAL_DISASTER** (mostly USGS/NOAA earthquakes and tsunamis, the only "
        f"category with machine-precision timestamps in this dataset). Every "
        f"correlation below involving another category is based on 1-2 events and "
        f"should be read as an anecdote, not a pattern."
    )
    lines.append("")

    for feature_key, label in [
        ("mahadasha_lord", "Mahadasha lord"), ("antardasha_lord", "Antardasha lord"),
        ("ascendant_rashi", "Ascendant Rāśi"), ("moon_rashi", "Moon Rāśi"),
        ("moon_nakshatra", "Moon Nakshatra"),
    ]:
        table, _ = correlate(records, feature_key)
        lines.append(f"## {label} vs. event category")
        lines.append("")
        lines.append("| " + label + " | event_type: count |")
        lines.append("|---|---|")
        for value, counts in sorted(table.items(), key=lambda kv: -sum(kv[1].values())):
            total = sum(counts.values())
            breakdown = ", ".join(f"{k}={v}" for k, v in sorted(counts.items(), key=lambda kv: -kv[1]))
            lines.append(f"| {value} (n={total}) | {breakdown} |")
        lines.append("")

    lines.append("## Caveats (read before using any of the above)")
    lines.append("")
    lines.append(
        "- **No held-out test set.** Every number above is in-sample -- the same 28 "
        "events used to find a pattern are the only events available to describe it."
    )
    lines.append(
        "- **No multiple-comparison correction.** 5 feature tables x up to a dozen "
        "distinct values each x 6 event categories is a large number of cells; some "
        "will look strongly \"correlated\" by chance alone at this sample size."
    )
    lines.append(
        "- **Category imbalance.** 24/28 events are NATURAL_DISASTER; any apparent "
        "association with POLITICAL, MILITARY, or SCIENCE_TECHNOLOGY is 1-2 data "
        "points and should not be trusted."
    )
    lines.append(
        "- **This was explicitly requested as a fast, non-rigorous pass** (see the "
        "conversation this was built from) -- it has NOT been run through this "
        "project's blind-backtest engine (backtest/) the way the rule-registry rules "
        "were in ASTROWATCH-BT-001. Treat every line above as a lead to investigate, "
        "not a validated claim."
    )
    return "\n".join(lines)


def predict_for_date(jd_ut, latitude, longitude, records) -> dict:
    """Casts a chart for an arbitrary (e.g. future) date/location and looks up which
    event_type each of its features was most associated with in the eligible-event
    table above. Returns the raw evidence, not a single confident answer -- there
    isn't enough data for that, and this function does not pretend otherwise."""
    chart = compute_kundli(jd_ut, latitude, longitude)
    dasha = compute_dasha_state(jd_ut, chart.grahas["moon"].sidereal_lon_deg)
    features = {
        "mahadasha_lord": dasha.mahadasha.lord,
        "antardasha_lord": dasha.antardasha.lord,
        "ascendant_rashi": chart.ascendant_rashi.rashi_name,
        "moon_rashi": chart.grahas["moon"].rashi.rashi_name,
        "moon_nakshatra": chart.grahas["moon"].nakshatra.nakshatra_name,
    }
    evidence = {}
    for feature_key, value in features.items():
        table, _ = correlate(records, feature_key)
        counts = dict(table.get(value, {}))
        evidence[feature_key] = {"observed_value": value, "historical_matches": counts,
                                   "n": sum(counts.values())}
    return {"jd_ut": jd_ut, "latitude": latitude, "longitude": longitude,
            "features": features, "evidence": evidence,
            "disclaimer": "UNVALIDATED / exploratory pattern match against a 28-event "
                            "in-sample table -- not a statistically tested prediction."}


def main():
    conn = hdb.connect(HIST_DB_PATH)
    records = build_all(conn)
    conn.close()

    os.makedirs(OUT_DIR, exist_ok=True)
    csv_path = os.path.join(OUT_DIR, "kundli_chart_data.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0].keys()))
        writer.writeheader()
        writer.writerows(records)
    print(f"Wrote {csv_path} ({len(records)} rows)")

    report = format_correlation_report(records)
    report_path = os.path.join(OUT_DIR, "KUNDLI_CORRELATION_REPORT.md")
    with open(report_path, "w") as f:
        f.write(report)
    print(f"Wrote {report_path}")

    records_path = os.path.join(OUT_DIR, "kundli_records.json")
    with open(records_path, "w") as f:
        json.dump(records, f, indent=2)
    print(f"Wrote {records_path}")

    return records


if __name__ == "__main__":
    main()
