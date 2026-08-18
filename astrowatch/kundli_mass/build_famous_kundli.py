#!/usr/bin/env python3
"""
Astrowatch -- natal kundli + birth Mahadasha for the famous_people_corpus.py dataset
(459 real, cross-field public figures). Same conventions as build_leaders_kundli.py:
DOCUMENTED birth time used where known, else ASSUMED_NOON.
"""
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone as dt_timezone
from zoneinfo import ZoneInfo

ASTROWATCH_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ASTROWATCH_DIR)
import coordinates
from kundli import compute_kundli
from mahadasha import compute_dasha_state

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, THIS_DIR)
from famous_people_corpus import PEOPLE

DB_PATH = os.path.join(THIS_DIR, "famous_people_kundli.db")
JSON_PATH = os.path.join(THIS_DIR, "famous_people_kundli_records.json")

SCHEMA = """
CREATE TABLE IF NOT EXISTS famous_people (
    person_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    birth_date TEXT NOT NULL,
    birth_time_source TEXT NOT NULL,
    country TEXT,
    field TEXT NOT NULL,
    note TEXT,
    status TEXT NOT NULL,
    ascendant_rashi TEXT,
    ascendant_nakshatra TEXT,
    moon_rashi TEXT,
    moon_nakshatra TEXT,
    sun_rashi TEXT,
    mars_rashi TEXT,
    natal_mahadasha_lord TEXT,
    natal_antardasha_lord TEXT,
    error TEXT
);
"""


def build_all():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    conn.execute("DELETE FROM famous_people")
    records = []
    n_ok = n_err = 0

    for idx, (name, date, time, tz, country, lat, lon, field, note) in enumerate(PEOPLE):
        try:
            y, m, d = (int(x) for x in date.split("-"))
            if time:
                hh, mm = (int(x) for x in time.split(":"))
                time_source = "DOCUMENTED"
            else:
                hh, mm = 12, 0
                time_source = "ASSUMED_NOON"
            local_dt = datetime(y, m, d, hh, mm, tzinfo=ZoneInfo(tz))
            utc_dt = local_dt.astimezone(dt_timezone.utc)
            jd_ut = coordinates.julian_day(utc_dt.year, utc_dt.month, utc_dt.day,
                                            utc_dt.hour + utc_dt.minute / 60.0)
            chart = compute_kundli(jd_ut, lat, lon)
            dasha = compute_dasha_state(jd_ut, chart.grahas["moon"].sidereal_lon_deg)
            rec = {
                "person_id": idx, "name": name, "birth_date": date,
                "birth_time_source": time_source, "country": country, "field": field,
                "note": note, "status": "COMPUTED",
                "ascendant_rashi": chart.ascendant_rashi.rashi_name,
                "ascendant_nakshatra": chart.ascendant_nakshatra.nakshatra_name,
                "moon_rashi": chart.grahas["moon"].rashi.rashi_name,
                "moon_nakshatra": chart.grahas["moon"].nakshatra.nakshatra_name,
                "sun_rashi": chart.grahas["sun"].rashi.rashi_name,
                "mars_rashi": chart.grahas["mars"].rashi.rashi_name,
                "natal_mahadasha_lord": dasha.mahadasha.lord,
                "natal_antardasha_lord": dasha.antardasha.lord,
            }
            conn.execute(
                "INSERT INTO famous_people (person_id, name, birth_date, "
                "birth_time_source, country, field, note, status, ascendant_rashi, "
                "ascendant_nakshatra, moon_rashi, moon_nakshatra, sun_rashi, "
                "mars_rashi, natal_mahadasha_lord, natal_antardasha_lord) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (idx, name, date, time_source, country, field, note, "COMPUTED",
                 rec["ascendant_rashi"], rec["ascendant_nakshatra"], rec["moon_rashi"],
                 rec["moon_nakshatra"], rec["sun_rashi"], rec["mars_rashi"],
                 rec["natal_mahadasha_lord"], rec["natal_antardasha_lord"]),
            )
            records.append(rec)
            n_ok += 1
        except Exception as e:
            conn.execute(
                "INSERT INTO famous_people (person_id, name, birth_date, "
                "birth_time_source, country, field, note, status, error) "
                "VALUES (?,?,?,?,?,?,?,?,?)",
                (idx, name, date, "ERROR", country, field, note, "ERROR", str(e)),
            )
            n_err += 1

    conn.commit()
    conn.close()
    with open(JSON_PATH, "w") as f:
        json.dump(records, f, indent=1)
    print(f"computed={n_ok} errors={n_err} total={len(PEOPLE)} -> {DB_PATH}")
    return records


if __name__ == "__main__":
    build_all()
