#!/usr/bin/env python3
"""
Astrowatch -- FULL lifetime Vimshottari Mahadasha/Antardasha timeline for every
person in famous_people_corpus.py.

Unlike famous_people_kundli.db (which stores only the natal/birth-balance dasha),
this script walks the Vimshottari sequence forward from birth through every
Mahadasha (and its 9 Antardashas) from birth up to min(today, birth + 120 years,
one full Vimshottari cycle). This is pure mechanical computation -- the same
birth-progressed-walk method already used and documented for Trump/Modi/leaders
in this project (_progress_dasha in build_leaders_kundli.py) -- extended here to
emit the FULL sequence rather than just the state at one target date. No web
research or fabrication involved in this step; that's a separate, bounded pass
layered on top for a smaller diverse subset.
"""
import os
import sqlite3
import sys
from datetime import datetime, timezone as dt_timezone
from zoneinfo import ZoneInfo

ASTROWATCH_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ASTROWATCH_DIR)
import coordinates
from kundli import compute_kundli
from mahadasha import (compute_dasha_state, DASHA_SEQUENCE, _lord_index,
                        _compute_antardasha, DashaPeriod, _SIDEREAL_YEAR_DAYS)

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, THIS_DIR)
from famous_people_corpus import PEOPLE

DB_PATH = os.path.join(THIS_DIR, "famous_people_lifetime_dasha.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS lifetime_dasha (
    person_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    field TEXT,
    mahadasha_index INTEGER NOT NULL,
    mahadasha_lord TEXT NOT NULL,
    maha_start_date TEXT NOT NULL,
    maha_end_date TEXT NOT NULL,
    antardasha_index INTEGER NOT NULL,
    antardasha_lord TEXT NOT NULL,
    antar_start_date TEXT NOT NULL,
    antar_end_date TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_lifetime_dasha_person ON lifetime_dasha(person_id);
CREATE INDEX IF NOT EXISTS idx_lifetime_dasha_name ON lifetime_dasha(name);
"""

TODAY = datetime(2026, 8, 15, tzinfo=dt_timezone.utc)
TODAY_JD = coordinates.julian_day(TODAY.year, TODAY.month, TODAY.day, 0.0)


def jd_to_iso_date(jd_ut: float) -> str:
    jd = jd_ut + 0.5
    z = int(jd)
    f = jd - z
    if z < 2299161:
        a = z
    else:
        alpha = int((z - 1867216.25) / 36524.25)
        a = z + 1 + alpha - alpha // 4
    b = a + 1524
    c = int((b - 122.1) / 365.25)
    d = int(365.25 * c)
    e = int((b - d) / 30.6001)
    day = b - d - int(30.6001 * e) + f
    month = e - 1 if e < 14 else e - 13
    year = c - 4716 if month > 2 else c - 4715
    day_int = int(day)
    return f"{year:04d}-{month:02d}-{day_int:02d}"


def _jd_for(date_iso, time_hhmm, tz_name):
    y, m, d = (int(x) for x in date_iso.split("-"))
    if time_hhmm:
        hh, mm = (int(x) for x in time_hhmm.split(":"))
    else:
        hh, mm = 12, 0
    local_dt = datetime(y, m, d, hh, mm, tzinfo=ZoneInfo(tz_name))
    utc_dt = local_dt.astimezone(dt_timezone.utc)
    return coordinates.julian_day(utc_dt.year, utc_dt.month, utc_dt.day,
                                   utc_dt.hour + utc_dt.minute / 60.0)


def full_lifetime_sequence(birth_jd, natal_moon_lon, end_jd):
    birth_dasha = compute_dasha_state(birth_jd, natal_moon_lon)
    cursor = birth_dasha.mahadasha
    idx = _lord_index(cursor.lord)
    cycle_end_jd = birth_jd + 120 * _SIDEREAL_YEAR_DAYS
    hard_end_jd = min(end_jd, cycle_end_jd)

    maha_i = 0
    while cursor.start_jd_ut < hard_end_jd:
        maha_lord_years = DASHA_SEQUENCE[idx][1]
        sub_cursor_jd = cursor.start_jd_ut
        for offset in range(9):
            sub_idx = (idx + offset) % 9
            sub_lord, sub_lord_years = DASHA_SEQUENCE[sub_idx]
            sub_duration_days = (sub_lord_years * maha_lord_years / 120.0) * _SIDEREAL_YEAR_DAYS
            sub_end_jd = sub_cursor_jd + sub_duration_days
            if sub_cursor_jd >= hard_end_jd:
                break
            yield (maha_i, cursor.lord, cursor.start_jd_ut, cursor.end_jd_ut,
                   offset, sub_lord, sub_cursor_jd, min(sub_end_jd, hard_end_jd))
            sub_cursor_jd = sub_end_jd
        idx = (idx + 1) % 9
        lord, years = DASHA_SEQUENCE[idx]
        start = cursor.end_jd_ut
        end = start + years * _SIDEREAL_YEAR_DAYS
        cursor = DashaPeriod(lord=lord, start_jd_ut=start, end_jd_ut=end, level="mahadasha")
        maha_i += 1


def build_all():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    conn.execute("DELETE FROM lifetime_dasha")

    rows_written = 0
    people_ok = 0
    people_err = 0
    for person_id, (name, date, time_hhmm, tz, country, lat, lon, field, note) in enumerate(PEOPLE):
        try:
            birth_jd = _jd_for(date, time_hhmm, tz)
            chart = compute_kundli(birth_jd, lat, lon)
            natal_moon_lon = chart.grahas["moon"].sidereal_lon_deg
            for rec in full_lifetime_sequence(birth_jd, natal_moon_lon, TODAY_JD):
                (maha_i, maha_lord, maha_s, maha_e, ant_i, ant_lord, ant_s, ant_e) = rec
                conn.execute(
                    "INSERT INTO lifetime_dasha (person_id, name, field, mahadasha_index, "
                    "mahadasha_lord, maha_start_date, maha_end_date, antardasha_index, "
                    "antardasha_lord, antar_start_date, antar_end_date) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (person_id, name, field, maha_i, maha_lord, jd_to_iso_date(maha_s),
                     jd_to_iso_date(maha_e), ant_i, ant_lord, jd_to_iso_date(ant_s), jd_to_iso_date(ant_e))
                )
                rows_written += 1
            people_ok += 1
        except Exception as e:
            people_err += 1
            print(f"ERROR {name}: {e}")
    conn.commit()
    conn.close()
    print(f"people_ok={people_ok} people_err={people_err} antardasha_rows_written={rows_written}")


if __name__ == "__main__":
    build_all()
