#!/usr/bin/env python3
"""
Astrowatch -- national ("mundane") natal kundli + founding Mahadasha for every
entry in nations_corpus.py. Uses astrowatch.mundane.entity_chart, the shared
implementation of the user's mundane-astrology rule (see
MUNDANE_ASTROLOGY_RULE.md): formation date + capital location + assumed 00:00
local civil time (no nation has a documented minute-level founding time, unlike
a person's birth certificate).
"""
import os
import sqlite3
import sys

ASTROWATCH_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ASTROWATCH_DIR)
from mundane.entity_chart import compute_entity_chart

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, THIS_DIR)
from nations_corpus import NATIONS

DB_PATH = os.path.join(THIS_DIR, "nations_kundli.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS nations (
    nation_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    formation_date TEXT NOT NULL,
    time_source TEXT NOT NULL,
    capital TEXT,
    note TEXT,
    status TEXT NOT NULL,
    ascendant_rashi TEXT,
    ascendant_nakshatra TEXT,
    moon_rashi TEXT,
    moon_nakshatra TEXT,
    sun_rashi TEXT,
    mars_rashi TEXT,
    saturn_rashi TEXT,
    jupiter_rashi TEXT,
    natal_mahadasha_lord TEXT,
    natal_antardasha_lord TEXT,
    error TEXT
);
"""


def build_all():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    conn.execute("DELETE FROM nations")
    n_ok = n_err = 0

    for idx, (name, date, capital, lat, lon, tz, note) in enumerate(NATIONS):
        try:
            entity = compute_entity_chart(name, "nation", date, lat, lon, tz)
            chart = entity.chart
            dasha = entity.natal_dasha
            conn.execute(
                "INSERT INTO nations (nation_id, name, formation_date, time_source, "
                "capital, note, status, ascendant_rashi, ascendant_nakshatra, moon_rashi, "
                "moon_nakshatra, sun_rashi, mars_rashi, saturn_rashi, jupiter_rashi, "
                "natal_mahadasha_lord, natal_antardasha_lord, error) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (idx, name, date, entity.time_source, capital, note, "COMPUTED",
                 chart.ascendant_rashi.rashi_name, chart.ascendant_nakshatra.nakshatra_name,
                 chart.grahas["moon"].rashi.rashi_name, chart.grahas["moon"].nakshatra.nakshatra_name,
                 chart.grahas["sun"].rashi.rashi_name, chart.grahas["mars"].rashi.rashi_name,
                 chart.grahas["saturn"].rashi.rashi_name, chart.grahas["jupiter"].rashi.rashi_name,
                 dasha.mahadasha.lord, dasha.antardasha.lord, None)
            )
            n_ok += 1
        except Exception as e:
            conn.execute(
                "INSERT INTO nations (nation_id, name, formation_date, time_source, capital, "
                "note, status, error) VALUES (?,?,?,?,?,?,?,?)",
                (idx, name, date, "ERROR", capital, note, "ERROR", str(e))
            )
            n_err += 1
            print(f"ERROR {name}: {e}")

    conn.commit()
    conn.close()
    print(f"nations_ok={n_ok} nations_err={n_err} total={len(NATIONS)}")


if __name__ == "__main__":
    build_all()
