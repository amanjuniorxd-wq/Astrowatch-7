#!/usr/bin/env python3
"""
Astrowatch -- maps nations_events_corpus.py's real dated national events against
each nation's mechanically-computed lifetime Mahadasha/Antardasha timeline
(nations_lifetime_dasha.db). Same method as life_events_dasha_mapping.py.
"""
import os
import sqlite3

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
DASHA_DB = os.path.join(THIS_DIR, "nations_lifetime_dasha.db")
OUT_DB = os.path.join(THIS_DIR, "nations_events_dasha_mapping.db")

import sys
sys.path.insert(0, THIS_DIR)
from nations_events_corpus import EVENTS

SCHEMA = """
CREATE TABLE IF NOT EXISTS nations_events_dasha (
    nation_name TEXT NOT NULL,
    event_date TEXT NOT NULL,
    event_type TEXT NOT NULL,
    description TEXT NOT NULL,
    mahadasha_lord TEXT,
    antardasha_lord TEXT,
    match_status TEXT NOT NULL
);
"""


def dasha_for(conn_dasha, name, date_iso):
    cur = conn_dasha.execute(
        "SELECT mahadasha_lord, antardasha_lord FROM lifetime_dasha "
        "WHERE name=? AND antar_start_date<=? AND antar_end_date>? "
        "ORDER BY mahadasha_index, antardasha_index LIMIT 1",
        (name, date_iso, date_iso),
    )
    return cur.fetchone()


def build():
    conn_dasha = sqlite3.connect(DASHA_DB)
    conn_out = sqlite3.connect(OUT_DB)
    conn_out.executescript(SCHEMA)
    conn_out.execute("DELETE FROM nations_events_dasha")

    matched = unmatched = 0
    for name, date_iso, etype, desc in EVENTS:
        row = dasha_for(conn_dasha, name, date_iso)
        if row:
            maha, antar = row
            status = "MATCHED"
            matched += 1
        else:
            maha, antar = None, None
            status = "OUT_OF_COMPUTED_RANGE"
            unmatched += 1
        conn_out.execute(
            "INSERT INTO nations_events_dasha (nation_name, event_date, event_type, "
            "description, mahadasha_lord, antardasha_lord, match_status) VALUES (?,?,?,?,?,?,?)",
            (name, date_iso, etype, desc, maha, antar, status),
        )
    conn_out.commit()
    print(f"events={len(EVENTS)} matched={matched} unmatched={unmatched}")
    conn_out.close()
    conn_dasha.close()


if __name__ == "__main__":
    build()
