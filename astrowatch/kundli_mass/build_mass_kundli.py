#!/usr/bin/env python3
"""
Astrowatch — mass kundli/Mahadasha build over the events_corpus.py dataset (500+
real-world Political/Military/Economic events), per explicit user instruction to
"continue retrieving events ... assume time to be 12:00pm if no time is given."

HONESTY / SEPARATION NOTES (read before trusting anything downstream of this file):

1. TIME: every event in events_corpus.py lacks a specifically-researched clock time
   this pass. Per explicit user instruction, every event is assigned 12:00 LOCAL time.
   This is tagged time_source='ASSUMED_NOON' on every single row, distinctly and
   permanently, and this dataset is kept in its own database
   (kundli_mass/kundli_mass.db), NEVER merged into historical_events.db /
   historical_events_v2.db (HIST-001/HIST-002, which used only genuinely-recorded
   times/EXACT-or-APPROXIMATE confidence). This directly reverses the no-noon-
   fabrication rule enforced earlier in this project for HIST-001/002 -- that reversal
   is intentional and explicit per this session's user instruction, not an oversight.

2. TIMEZONE: events_corpus.py stores only country/city-level lat/lon, not a
   researched IANA timezone per event. UTC offset is APPROXIMATED from longitude
   (offset_hours = round(longitude / 15)), a standard but coarse simplification
   (ignores real timezone boundaries, DST, historical zone changes). Tagged
   tz_source='APPROX_FROM_LONGITUDE' on every row. This compounds with ASSUMED_NOON:
   the resulting UT instant for any given event could easily be off by 1-2 hours
   from the true local noon.

3. PRE-COMMON-ERA EVENTS: 8 events in the corpus have negative-year (BCE) dates.
   These are EXCLUDED from chart computation entirely (not approximated) -- this
   project's ayanamsha model and Julian-day conventions are not validated that far
   back, and fabricating a chart for them would compound two large uncertainties
   (ayanamsha drift + calendar conventions) silently. They remain in the corpus file
   for reference but get status=EXCLUDED_PRE_COMMON_ERA in the output.

4. RIGOR LEVEL: per the user's own EARLIER explicit choice in this same session
   ("Just extract whatever correlates, don't worry about rigor"), this pass does NOT
   hold out a validation set, does NOT correct for multiple comparisons, and does NOT
   run a significance test. Every correlation reported downstream is
   UNVALIDATED/PATTERN-BASED, exactly like kundli_analysis/'s earlier, smaller, more
   carefully-timed 28-event pass -- this pass is the same methodology at higher volume
   and lower time-precision, not a more rigorous exercise.

5. RELATIONSHIP TO BT-001/BT-002: this entire kundli_mass/ pipeline is completely
   separate from the rule-registry-based Astrowatch backtest system (rule_matcher.py,
   predictor.py/predictor_v2.py, backtest_results.db). It does not use rule_registry.py
   at all, does not touch backtest_results.db, and BT-001's null result stands
   completely independent of and unaffected by whatever this script finds.
"""
import json
import os
import sqlite3
import sys
from datetime import datetime, timedelta

ASTROWATCH_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ASTROWATCH_DIR)

import coordinates
from kundli import compute_kundli
from mahadasha import compute_dasha_state

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, THIS_DIR)
from events_corpus import EVENTS

DB_PATH = os.path.join(THIS_DIR, "kundli_mass.db")
JSON_PATH = os.path.join(THIS_DIR, "kundli_mass_records.json")

SCHEMA = """
CREATE TABLE IF NOT EXISTS mass_events (
    event_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    date_iso TEXT NOT NULL,
    country TEXT,
    latitude REAL,
    longitude REAL,
    category TEXT NOT NULL,
    subtype TEXT,
    time_source TEXT NOT NULL,
    tz_source TEXT,
    status TEXT NOT NULL,
    jd_ut REAL,
    ascendant_rashi TEXT,
    ascendant_nakshatra TEXT,
    moon_rashi TEXT,
    moon_nakshatra TEXT,
    sun_rashi TEXT,
    sun_nakshatra TEXT,
    mahadasha_lord TEXT,
    antardasha_lord TEXT,
    error TEXT
);
"""


def _utc_offset_hours(longitude: float) -> int:
    return max(-12, min(14, round(longitude / 15.0)))


def _jd_ut_for_noon_local(date_iso: str, longitude: float) -> float:
    y, m, d = (int(x) for x in date_iso.split("-"))
    offset = _utc_offset_hours(longitude)
    utc_dt = datetime(y, m, d, 12) - timedelta(hours=offset)
    return coordinates.julian_day(utc_dt.year, utc_dt.month, utc_dt.day,
                                   utc_dt.hour + utc_dt.minute / 60.0)


def build_all():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    conn.execute("DELETE FROM mass_events")

    records = []
    n_computed = 0
    n_excluded = 0
    n_error = 0

    for idx, (name, date_iso, country, lat, lon, category, subtype) in enumerate(EVENTS):
        if date_iso.startswith("-"):
            conn.execute(
                "INSERT INTO mass_events (event_id, name, date_iso, country, latitude, "
                "longitude, category, subtype, time_source, tz_source, status) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (idx, name, date_iso, country, lat, lon, category, subtype,
                 "EXCLUDED_PRE_COMMON_ERA", None, "EXCLUDED_PRE_COMMON_ERA"),
            )
            n_excluded += 1
            continue
        try:
            jd_ut = _jd_ut_for_noon_local(date_iso, lon)
            chart = compute_kundli(jd_ut, lat, lon)
            dasha = compute_dasha_state(jd_ut, chart.grahas["moon"].sidereal_lon_deg)
            rec = {
                "event_id": idx, "name": name, "date_iso": date_iso, "country": country,
                "latitude": lat, "longitude": lon, "category": category, "subtype": subtype,
                "time_source": "ASSUMED_NOON", "tz_source": "APPROX_FROM_LONGITUDE",
                "jd_ut": jd_ut,
                "ascendant_rashi": chart.ascendant_rashi.rashi_name,
                "ascendant_nakshatra": chart.ascendant_nakshatra.nakshatra_name,
                "moon_rashi": chart.grahas["moon"].rashi.rashi_name,
                "moon_nakshatra": chart.grahas["moon"].nakshatra.nakshatra_name,
                "sun_rashi": chart.grahas["sun"].rashi.rashi_name,
                "sun_nakshatra": chart.grahas["sun"].nakshatra.nakshatra_name,
                "mahadasha_lord": dasha.mahadasha.lord,
                "antardasha_lord": dasha.antardasha.lord,
                "all_grahas": {
                    g: {"rashi": p.rashi.rashi_name, "nakshatra": p.nakshatra.nakshatra_name,
                        "house": p.house}
                    for g, p in chart.grahas.items()
                },
            }
            conn.execute(
                "INSERT INTO mass_events (event_id, name, date_iso, country, latitude, "
                "longitude, category, subtype, time_source, tz_source, status, jd_ut, "
                "ascendant_rashi, ascendant_nakshatra, moon_rashi, moon_nakshatra, "
                "sun_rashi, sun_nakshatra, mahadasha_lord, antardasha_lord) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (idx, name, date_iso, country, lat, lon, category, subtype,
                 "ASSUMED_NOON", "APPROX_FROM_LONGITUDE", "COMPUTED", jd_ut,
                 rec["ascendant_rashi"], rec["ascendant_nakshatra"],
                 rec["moon_rashi"], rec["moon_nakshatra"],
                 rec["sun_rashi"], rec["sun_nakshatra"],
                 rec["mahadasha_lord"], rec["antardasha_lord"]),
            )
            records.append(rec)
            n_computed += 1
        except Exception as e:
            conn.execute(
                "INSERT INTO mass_events (event_id, name, date_iso, country, latitude, "
                "longitude, category, subtype, time_source, tz_source, status, error) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (idx, name, date_iso, country, lat, lon, category, subtype,
                 "ASSUMED_NOON", "APPROX_FROM_LONGITUDE", "ERROR", str(e)),
            )
            n_error += 1

    conn.commit()
    conn.close()

    with open(JSON_PATH, "w") as f:
        json.dump(records, f, indent=1)

    print(f"computed={n_computed} excluded_pre_ce={n_excluded} errors={n_error} "
          f"total={len(EVENTS)}")
    return records


if __name__ == "__main__":
    build_all()
