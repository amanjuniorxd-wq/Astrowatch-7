#!/usr/bin/env python3
"""
Astrowatch -- FULL lifetime Vimshottari Mahadasha/Antardasha timeline (formation
date through today) for every nation in nations_corpus.py. Same method as
build_famous_lifetime_dasha.py, now shared via mundane/dasha_timeline.py.
"""
import os
import sqlite3
import sys
from datetime import datetime, timezone as dt_timezone

ASTROWATCH_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ASTROWATCH_DIR)
import coordinates
from mundane.entity_chart import compute_entity_chart, full_lifetime_dasha
from mundane.dasha_timeline import jd_to_iso_date

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, THIS_DIR)
from nations_corpus import NATIONS

DB_PATH = os.path.join(THIS_DIR, "nations_lifetime_dasha.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS lifetime_dasha (
    nation_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    mahadasha_index INTEGER NOT NULL,
    mahadasha_lord TEXT NOT NULL,
    maha_start_date TEXT NOT NULL,
    maha_end_date TEXT NOT NULL,
    antardasha_index INTEGER NOT NULL,
    antardasha_lord TEXT NOT NULL,
    antar_start_date TEXT NOT NULL,
    antar_end_date TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_nations_lifetime_dasha_nation ON lifetime_dasha(nation_id);
CREATE INDEX IF NOT EXISTS idx_nations_lifetime_dasha_name ON lifetime_dasha(name);
"""

TODAY = datetime(2026, 8, 17, tzinfo=dt_timezone.utc)
TODAY_JD = coordinates.julian_day(TODAY.year, TODAY.month, TODAY.day, 0.0)


def build_all():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    conn.execute("DELETE FROM lifetime_dasha")

    rows_written = 0
    nations_ok = nations_err = 0
    for nation_id, (name, date, capital, lat, lon, tz, note) in enumerate(NATIONS):
        try:
            entity = compute_entity_chart(name, "nation", date, lat, lon, tz)
            for rec in full_lifetime_dasha(entity, TODAY_JD):
                (maha_i, maha_lord, maha_s, maha_e, ant_i, ant_lord, ant_s, ant_e) = rec
                conn.execute(
                    "INSERT INTO lifetime_dasha (nation_id, name, mahadasha_index, "
                    "mahadasha_lord, maha_start_date, maha_end_date, antardasha_index, "
                    "antardasha_lord, antar_start_date, antar_end_date) VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (nation_id, name, maha_i, maha_lord, jd_to_iso_date(maha_s),
                     jd_to_iso_date(maha_e), ant_i, ant_lord, jd_to_iso_date(ant_s), jd_to_iso_date(ant_e))
                )
                rows_written += 1
            nations_ok += 1
        except Exception as e:
            nations_err += 1
            print(f"ERROR {name}: {e}")

    conn.commit()
    conn.close()
    print(f"nations_ok={nations_ok} nations_err={nations_err} antardasha_rows_written={rows_written}")


if __name__ == "__main__":
    build_all()
