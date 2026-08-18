#!/usr/bin/env python3
"""
Astrowatch -- natal chart + office-entry progressed Mahadasha for the leaders_corpus.py
figures (US Presidents, Indian PMs, current global leaders).

For each leader: compute the natal kundli, then WALK the Vimshottari sequence forward
from birth (same correct birth-progressed method used for Trump's Sept-2026 dasha
earlier this session) to find which Mahadasha/Antardasha was active the day they
TOOK OFFICE, and (for leaders who have left office) the day they LEFT. This is the
real classical computation -- not a re-derivation from a later moment's Moon position.

Stored separately from kundli_mass.db (events) and historical_events*.db (frozen) --
new file leaders_kundli.db.
"""
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone as dt_timezone, timedelta
from zoneinfo import ZoneInfo

ASTROWATCH_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ASTROWATCH_DIR)
import coordinates
from kundli import compute_kundli
from mahadasha import (compute_dasha_state, DASHA_SEQUENCE, _lord_index,
                        _compute_antardasha, DashaPeriod, _SIDEREAL_YEAR_DAYS)

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, THIS_DIR)
from leaders_corpus import LEADERS

DB_PATH = os.path.join(THIS_DIR, "leaders_kundli.db")
JSON_PATH = os.path.join(THIS_DIR, "leaders_kundli_records.json")

SCHEMA = """
CREATE TABLE IF NOT EXISTS leaders (
    leader_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    birth_date TEXT NOT NULL,
    birth_time_source TEXT NOT NULL,  -- DOCUMENTED | ASSUMED_NOON
    country TEXT,
    group_tag TEXT NOT NULL,
    ascendant_rashi TEXT,
    ascendant_nakshatra TEXT,
    moon_rashi TEXT,
    moon_nakshatra TEXT,
    sun_rashi TEXT,
    mars_rashi TEXT,
    natal_mahadasha_lord TEXT,
    office_entry_mahadasha_lord TEXT,
    office_entry_antardasha_lord TEXT,
    office_exit_mahadasha_lord TEXT,
    office_exit_antardasha_lord TEXT,
    left_reason TEXT
);
"""


def _jd_for(date_iso, time_hhmm, tz_name):
    y, m, d = (int(x) for x in date_iso.split("-"))
    if time_hhmm:
        hh, mm = (int(x) for x in time_hhmm.split(":"))
        time_source = "DOCUMENTED"
    else:
        hh, mm = 12, 0
        time_source = "ASSUMED_NOON"
    local_dt = datetime(y, m, d, hh, mm, tzinfo=ZoneInfo(tz_name))
    utc_dt = local_dt.astimezone(dt_timezone.utc)
    jd = coordinates.julian_day(utc_dt.year, utc_dt.month, utc_dt.day,
                                 utc_dt.hour + utc_dt.minute / 60.0)
    return jd, time_source


def _progress_dasha(birth_jd, natal_moon_lon, target_jd):
    """Walks the Vimshottari sequence forward from the birth-balance Mahadasha to
    find the Mahadasha/Antardasha active at target_jd. Correct birth-progressed
    method (not re-derived from the Moon's position at target_jd)."""
    birth_dasha = compute_dasha_state(birth_jd, natal_moon_lon)
    cursor = birth_dasha.mahadasha
    idx = _lord_index(cursor.lord)
    # If target predates birth's own mahadasha end, birth_dasha already covers it.
    while cursor.end_jd_ut < target_jd:
        idx = (idx + 1) % 9
        lord, years = DASHA_SEQUENCE[idx]
        start = cursor.end_jd_ut
        end = start + years * _SIDEREAL_YEAR_DAYS
        cursor = DashaPeriod(lord=lord, start_jd_ut=start, end_jd_ut=end, level="mahadasha")
    antardasha = _compute_antardasha(target_jd, cursor, idx)
    return cursor.lord, antardasha.lord


def build_all():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    conn.execute("DELETE FROM leaders")
    records = []

    for idx, (name, bdate, btime, btz, country, lat, lon, group, tstart, tyears,
              reelected, left_reason) in enumerate(LEADERS):
        birth_jd, time_source = _jd_for(bdate, btime, btz)
        chart = compute_kundli(birth_jd, lat, lon)
        natal_moon_lon = chart.grahas["moon"].sidereal_lon_deg
        birth_dasha = compute_dasha_state(birth_jd, natal_moon_lon)

        entry_lord = entry_antar = exit_lord = exit_antar = None
        if tstart:
            # Office-entry date: use noon UTC as a location-neutral instant (the
            # office/seat location, not the birthplace, would matter for houses, but
            # dasha lords don't depend on location -- only the Moon's sidereal
            # longitude and elapsed time do).
            y, m, d = (int(x) for x in tstart.split("-"))
            entry_jd = coordinates.julian_day(y, m, d, 12.0)
            entry_lord, entry_antar = _progress_dasha(birth_jd, natal_moon_lon, entry_jd)
            if tyears is not None:
                exit_jd = entry_jd + tyears * 365.25
                exit_lord, exit_antar = _progress_dasha(birth_jd, natal_moon_lon, exit_jd)

        rec = {
            "leader_id": idx, "name": name, "birth_date": bdate,
            "birth_time_source": time_source, "country": country, "group": group,
            "ascendant_rashi": chart.ascendant_rashi.rashi_name,
            "ascendant_nakshatra": chart.ascendant_nakshatra.nakshatra_name,
            "moon_rashi": chart.grahas["moon"].rashi.rashi_name,
            "moon_nakshatra": chart.grahas["moon"].nakshatra.nakshatra_name,
            "sun_rashi": chart.grahas["sun"].rashi.rashi_name,
            "mars_rashi": chart.grahas["mars"].rashi.rashi_name,
            "natal_mahadasha_lord": birth_dasha.mahadasha.lord,
            "office_entry_mahadasha_lord": entry_lord,
            "office_entry_antardasha_lord": entry_antar,
            "office_exit_mahadasha_lord": exit_lord,
            "office_exit_antardasha_lord": exit_antar,
            "left_reason": left_reason,
        }
        conn.execute(
            "INSERT INTO leaders (leader_id, name, birth_date, birth_time_source, "
            "country, group_tag, ascendant_rashi, ascendant_nakshatra, moon_rashi, "
            "moon_nakshatra, sun_rashi, mars_rashi, natal_mahadasha_lord, "
            "office_entry_mahadasha_lord, office_entry_antardasha_lord, "
            "office_exit_mahadasha_lord, office_exit_antardasha_lord, left_reason) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (idx, name, bdate, time_source, country, group,
             rec["ascendant_rashi"], rec["ascendant_nakshatra"], rec["moon_rashi"],
             rec["moon_nakshatra"], rec["sun_rashi"], rec["mars_rashi"],
             rec["natal_mahadasha_lord"], entry_lord, entry_antar, exit_lord,
             exit_antar, left_reason),
        )
        records.append(rec)

    conn.commit()
    conn.close()
    with open(JSON_PATH, "w") as f:
        json.dump(records, f, indent=1)
    print(f"Built {len(records)} leader charts -> {DB_PATH}")
    return records


if __name__ == "__main__":
    build_all()
