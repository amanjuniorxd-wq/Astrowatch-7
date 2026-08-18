#!/usr/bin/env python3
"""
Astrowatch — pattern extraction + prediction scan over kundli_mass.db (519 charted
events, ASSUMED_NOON/APPROX_FROM_LONGITUDE time basis, see build_mass_kundli.py's
docstring for full caveats before trusting anything below).

LABELING RULE (explicit user instruction, this session): every output of the
"prediction" function in this file must be labeled as an ASTROLOGICAL CALCULATION --
a mechanical pattern-match against an unvalidated in-sample table -- and explicitly
NOT called a "forecast" and explicitly flagged as not to be relied on. This is
enforced in code (the disclaimer string below), not just in prose, so it can't be
silently dropped by a future caller of predict_window().
"""
import json
import os
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime, timedelta

ASTROWATCH_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ASTROWATCH_DIR)
import coordinates
from kundli import compute_kundli
from mahadasha import compute_dasha_state

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(THIS_DIR, "kundli_mass.db")
OUT_REPORT = os.path.join(THIS_DIR, "MASS_KUNDLI_CORRELATION_REPORT.md")
OUT_PREDICTION = os.path.join(THIS_DIR, "US_AUG20_SEP30_2026_ASTROLOGICAL_CALCULATION.md")

ASTROLOGICAL_CALCULATION_DISCLAIMER = (
    "This is an ASTROLOGICAL CALCULATION -- a mechanical pattern-match of a future "
    "date's kundli/Mahadasha features against an unvalidated, in-sample table of 519 "
    "historical events (themselves computed from an ASSUMED noon local time and a "
    "longitude-approximated timezone, not researched exact times). It is NOT a "
    "forecast, NOT a statistically validated prediction, and NOT something to be "
    "relied on for any real-world decision. Astrowatch's own blind-backtest "
    "experiment (ASTROWATCH-BT-001, a separate and more rigorous pipeline) found "
    "that its astrological rule set did not predict real event dates better than "
    "chance (permutation p=1.0). Nothing below overrides that result -- treat this "
    "purely as a description of what a mechanical pattern-match algorithm outputs "
    "when pointed at this date range, not as evidence about what will actually "
    "happen in the United States in this window."
)


def load_records():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM mass_events WHERE status='COMPUTED'"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def correlate(records, feature_key, label_key="category"):
    table = defaultdict(lambda: defaultdict(int))
    for r in records:
        table[r[feature_key]][r[label_key]] += 1
    return table


def format_report(records) -> str:
    lines = [
        "# Mass Kundli/Mahadasha Correlation Report (519 events, exploratory, UNVALIDATED)",
        "",
        "Built from `kundli_mass.db` -- 519 of 527 corpus events successfully charted "
        "(8 pre-Common-Era events excluded; see `build_mass_kundli.py` docstring). "
        "**Every event's chart uses an ASSUMED 12:00 local time and a "
        "longitude-approximated timezone, not a researched exact time** -- this is a "
        "materially less precise input than the 28-event `kundli_analysis/` report "
        "built earlier in this project from real recorded times. Read every number "
        "below with that in mind.",
        "",
        "## Sample composition",
        "",
    ]
    base = defaultdict(int)
    for r in records:
        base[r["category"]] += 1
    for cat, n in sorted(base.items(), key=lambda kv: -kv[1]):
        lines.append(f"- {cat}: {n}")
    lines.append("")

    for feature_key, label in [
        ("mahadasha_lord", "Mahadasha lord"), ("antardasha_lord", "Antardasha lord"),
        ("ascendant_rashi", "Ascendant Rasi"), ("moon_rashi", "Moon Rasi"),
        ("moon_nakshatra", "Moon Nakshatra"), ("sun_rashi", "Sun Rasi"),
    ]:
        table = correlate(records, feature_key)
        lines.append(f"## {label} vs. event category")
        lines.append("")
        lines.append(f"| {label} | n | MILITARY | POLITICAL | ECONOMIC |")
        lines.append("|---|---|---|---|---|")
        for value, counts in sorted(table.items(), key=lambda kv: -sum(kv[1].values())):
            total = sum(counts.values())
            lines.append(
                f"| {value} | {total} | {counts.get('MILITARY',0)} | "
                f"{counts.get('POLITICAL',0)} | {counts.get('ECONOMIC',0)} |"
            )
        lines.append("")

    lines.append("## Caveats (read before using any of the above)")
    lines.append("")
    lines.append(
        "- **Time precision is deliberately degraded.** Every chart uses ASSUMED_NOON "
        "+ APPROX_FROM_LONGITUDE timezone, per explicit user instruction this "
        "session. The Ascendant (Lagna) and house placements are the features most "
        "sensitive to this error -- a real event time even 1-2 hours off can shift "
        "the Ascendant by 15-30 degrees (a full sign or more). Mahadasha "
        "lord/Nakshatra placements are far less time-sensitive (the Moon moves ~13 "
        "deg/day, so a several-hour error rarely changes its Nakshatra) and are "
        "comparatively more trustworthy of the features tabulated here.",
    )
    lines.append(
        "- **No held-out test set, no significance testing, no multiple-comparison "
        "correction** -- 6 feature tables here, each with a dozen+ distinct values, "
        "is a large number of cells; many will look 'correlated' by chance alone. "
        "Per the user's own earlier explicit choice in this session, this pass "
        "optimizes for speed, not rigor."
    )
    lines.append(
        "- **Sample is curated from general historical knowledge**, not independently "
        "re-verified per-event this pass (same disclosure as the events_corpus.py "
        "header) -- a handful of dates/locations could be off by days or have minor "
        "factual imprecision at this volume."
    )
    lines.append(
        "- **This is completely separate from ASTROWATCH-BT-001**, the project's "
        "actual blind-backtest experiment, which found the rule-registry did NOT "
        "beat chance. This mass-kundli pass has not been run through that rigorous "
        "pipeline at all."
    )
    return "\n".join(lines)


def predict_window(start_date: str, end_date: str, latitude: float, longitude: float,
                    records, label="United States") -> dict:
    """Casts a chart for every day in [start_date, end_date] (ASSUMED_NOON local, same
    convention as the training data) and, for each day, looks up how often each
    feature value co-occurred with MILITARY/POLITICAL/ECONOMIC events historically.
    Returns per-day evidence AND a simple sum-of-matches "resonance score" per
    category -- a mechanical tally, not a probability estimate."""
    y0, m0, d0 = (int(x) for x in start_date.split("-"))
    y1, m1, d1 = (int(x) for x in end_date.split("-"))
    cur = datetime(y0, m0, d0)
    end = datetime(y1, m1, d1)

    tables = {
        fk: correlate(records, fk)
        for fk in ("mahadasha_lord", "antardasha_lord", "ascendant_rashi",
                   "moon_rashi", "moon_nakshatra", "sun_rashi")
    }

    days = []
    while cur <= end:
        date_iso = cur.strftime("%Y-%m-%d")
        offset = max(-12, min(14, round(longitude / 15.0)))
        utc_dt = datetime(cur.year, cur.month, cur.day, 12) - timedelta(hours=offset)
        jd_ut = coordinates.julian_day(utc_dt.year, utc_dt.month, utc_dt.day,
                                        utc_dt.hour + utc_dt.minute / 60.0)
        chart = compute_kundli(jd_ut, latitude, longitude)
        dasha = compute_dasha_state(jd_ut, chart.grahas["moon"].sidereal_lon_deg)
        features = {
            "mahadasha_lord": dasha.mahadasha.lord,
            "antardasha_lord": dasha.antardasha.lord,
            "ascendant_rashi": chart.ascendant_rashi.rashi_name,
            "moon_rashi": chart.grahas["moon"].rashi.rashi_name,
            "moon_nakshatra": chart.grahas["moon"].nakshatra.nakshatra_name,
            "sun_rashi": chart.grahas["sun"].rashi.rashi_name,
        }
        score = defaultdict(int)
        evidence = {}
        for fk, value in features.items():
            counts = dict(tables[fk].get(value, {}))
            evidence[fk] = {"value": value, "historical_counts": counts}
            for cat, n in counts.items():
                score[cat] += n
        days.append({
            "date": date_iso, "features": features, "evidence": evidence,
            "resonance_score": dict(score),
        })
        cur += timedelta(days=1)

    top_military = sorted(days, key=lambda d: -d["resonance_score"].get("MILITARY", 0))[:5]
    top_political = sorted(days, key=lambda d: -d["resonance_score"].get("POLITICAL", 0))[:5]
    top_economic = sorted(days, key=lambda d: -d["resonance_score"].get("ECONOMIC", 0))[:5]

    return {
        "location_label": label, "latitude": latitude, "longitude": longitude,
        "start_date": start_date, "end_date": end_date, "n_days": len(days),
        "days": days,
        "top_military_resonance_days": [(d["date"], d["resonance_score"]) for d in top_military],
        "top_political_resonance_days": [(d["date"], d["resonance_score"]) for d in top_political],
        "top_economic_resonance_days": [(d["date"], d["resonance_score"]) for d in top_economic],
        "disclaimer": ASTROLOGICAL_CALCULATION_DISCLAIMER,
    }


def format_prediction_report(result: dict) -> str:
    lines = [
        "# US Astrological Calculation -- Aug 20-Sep 30, 2026",
        "",
        "**LABEL: astrological calculation, not a forecast. Not to be relied on.**",
        "",
        result["disclaimer"],
        "",
        f"Location used: {result['location_label']} "
        f"(lat={result['latitude']}, lon={result['longitude']}) -- Washington, DC used "
        "as a single representative US reference point; a chart-based method has no "
        "principled way to represent an entire country at once, so this is one "
        "necessarily-arbitrary choice among many defensible ones (e.g. NYC, "
        "geographic center of the US) and a different reference point would shift "
        f"the Ascendant/house results below (Moon Rasi/Nakshatra/Mahadasha would not "
        f"change, since those don't depend on location).",
        "",
        f"Window scanned: {result['start_date']} to {result['end_date']} "
        f"({result['n_days']} days), each cast at ASSUMED local noon.",
        "",
        "## Mechanical 'resonance score' -- top days per category",
        "",
        "The score is simply: for each of the day's 6 chart features (Mahadasha "
        "lord, Antardasha lord, Ascendant Rasi, Moon Rasi, Moon Nakshatra, Sun Rasi), "
        "count how many of the 519 historical training events shared that exact "
        "feature value and fell in the given category, then sum across features. "
        "This is a naive frequency tally, not a calibrated probability -- a common "
        "Mahadasha lord (e.g. Venus, 20/120 years) will score high almost every day "
        "regardless of anything else.",
        "",
    ]
    for cat_key, cat_label in [
        ("top_military_resonance_days", "MILITARY"),
        ("top_political_resonance_days", "POLITICAL"),
        ("top_economic_resonance_days", "ECONOMIC"),
    ]:
        lines.append(f"### Highest mechanical {cat_label} resonance")
        lines.append("")
        lines.append("| Date | MILITARY score | POLITICAL score | ECONOMIC score |")
        lines.append("|---|---|---|---|")
        for date, scores in result[cat_key]:
            lines.append(
                f"| {date} | {scores.get('MILITARY',0)} | {scores.get('POLITICAL',0)} | "
                f"{scores.get('ECONOMIC',0)} |"
            )
        lines.append("")

    # Single highest-combined-score day as the closest thing to a headline
    combined = sorted(
        result["days"],
        key=lambda d: -sum(d["resonance_score"].get(c, 0) for c in ("MILITARY", "POLITICAL", "ECONOMIC")),
    )
    top = combined[0]
    lines.append("## Single highest combined-resonance day in the window")
    lines.append("")
    lines.append(f"**{top['date']}** -- chart features: " +
                 ", ".join(f"{k}={v['value']}" for k, v in top["evidence"].items()))
    lines.append("")
    lines.append(
        f"Combined mechanical score: MILITARY={top['resonance_score'].get('MILITARY',0)}, "
        f"POLITICAL={top['resonance_score'].get('POLITICAL',0)}, "
        f"ECONOMIC={top['resonance_score'].get('ECONOMIC',0)} (out of 519 training "
        f"events total; a uniform/no-signal baseline would put every day's score "
        f"near the category base rate times a small constant, so these numbers "
        f"should be compared to each other, not treated as percentages)."
    )
    lines.append("")
    lines.append(
        "**Again: this ranks days by mechanical feature-frequency overlap with a "
        "519-event, ASSUMED-noon-time, unvalidated table. It is a calculation "
        "output, not a forecast, and Astrowatch's own rigorous backtest "
        "(ASTROWATCH-BT-001) found this general approach does not beat chance. "
        "Do not use this to make real decisions.**"
    )
    return "\n".join(lines)


def main():
    records = load_records()
    report = format_report(records)
    with open(OUT_REPORT, "w") as f:
        f.write(report)
    print(f"Wrote {OUT_REPORT}")

    # Washington, DC as a single representative US reference point (see report note).
    result = predict_window("2026-08-20", "2026-09-30", 38.9072, -77.0369, records,
                             label="United States (Washington, DC reference point)")
    with open(os.path.join(THIS_DIR, "us_aug20_sep30_2026_prediction.json"), "w") as f:
        json.dump(result, f, indent=1, default=str)
    pred_report = format_prediction_report(result)
    with open(OUT_PREDICTION, "w") as f:
        f.write(pred_report)
    print(f"Wrote {OUT_PREDICTION}")


if __name__ == "__main__":
    main()
