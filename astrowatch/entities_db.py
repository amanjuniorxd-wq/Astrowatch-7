"""
Astrowatch Online -- Entity database.
========================================
New SQLite store (does not replace or modify kundli_mass/*_corpus.py or any of
their existing .db files -- this is a NEW, broader table purpose-built for the
AI intelligence layer's entity resolution / random-prediction eligibility
scoring, per the task spec's Section 9 field list). Seeded from this project's
own already-vetted real corpora (kundli_mass/nations_corpus.py,
famous_people_corpus.py, leaders_corpus.py) rather than fabricated demo rows.

Implements the standing project rule (see mundane/entity_chart.py's own
docstring, and MUNDANE_ASTROLOGY_RULE.md): any entity with a real, defensible
date and place can be analyzed. If time is unavailable, 00:00 local time is
used, but this is ALWAYS recorded honestly via `time_accuracy` -- never
represented as a verified fact. Note the two conventions already in use
upstream in this project's corpora: nations/organizations use
'assumed_midnight' (the mundane-astrology rule's own default); the
famous-people corpus historically used 'assumed_noon' for undocumented birth
times (a different, pre-existing convention from an earlier phase of this
project) -- both are preserved exactly as their source data actually recorded
them, never silently normalized to look more precise than they are.
"""

import os
import sqlite3
import time
from dataclasses import dataclass, field
from typing import List, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_PATH = os.path.join(HERE, "entities.db")

ENTITY_TYPES = (
    "person", "country", "government", "political_party", "company",
    "organization", "sports_team", "institution", "city", "event",
    "technology", "other",
)

TIME_ACCURACY_VALUES = ("documented", "assumed_midnight", "assumed_noon")

SCHEMA = """
CREATE TABLE IF NOT EXISTS entities (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    name                    TEXT NOT NULL,
    entity_type             TEXT NOT NULL,
    birth_or_inception_date TEXT NOT NULL,   -- YYYY-MM-DD
    birth_or_inception_place TEXT,
    birth_or_inception_time TEXT,            -- HH:MM, real or the 00:00 default
    timezone                TEXT NOT NULL,   -- IANA zone name
    latitude                REAL NOT NULL,
    longitude               REAL NOT NULL,
    source                  TEXT,
    source_reliability      TEXT,            -- e.g. HIGH / MEDIUM / LOW / UNVERIFIED
    time_accuracy           TEXT NOT NULL,   -- documented | assumed_midnight | assumed_noon
    notes                   TEXT,
    category                TEXT,            -- free-text sub-grouping (field/office/etc)
    created_at              TEXT NOT NULL,
    last_predicted_at       TEXT,            -- updated by ai/random_prediction.py
    prediction_count        INTEGER NOT NULL DEFAULT 0,
    UNIQUE(name, entity_type, birth_or_inception_date)
);
CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(entity_type);
CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name);
"""


@dataclass
class Entity:
    id: Optional[int]
    name: str
    entity_type: str
    birth_or_inception_date: str
    birth_or_inception_place: Optional[str]
    birth_or_inception_time: Optional[str]
    timezone: str
    latitude: float
    longitude: float
    source: Optional[str]
    source_reliability: Optional[str]
    time_accuracy: str
    notes: Optional[str]
    category: Optional[str] = None
    created_at: Optional[str] = None
    last_predicted_at: Optional[str] = None
    prediction_count: int = 0


def _row_to_entity(row: sqlite3.Row) -> Entity:
    return Entity(**{k: row[k] for k in row.keys()})


def get_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def add_entity(conn: sqlite3.Connection, *, name: str, entity_type: str,
               birth_or_inception_date: str, latitude: float, longitude: float,
               timezone: str, birth_or_inception_place: Optional[str] = None,
               birth_or_inception_time: Optional[str] = None,
               source: Optional[str] = None, source_reliability: Optional[str] = None,
               time_accuracy: Optional[str] = None, notes: Optional[str] = None,
               category: Optional[str] = None) -> int:
    if entity_type not in ENTITY_TYPES:
        raise ValueError(f"entity_type must be one of {ENTITY_TYPES}, got {entity_type!r}")
    if time_accuracy is None:
        time_accuracy = "documented" if birth_or_inception_time else "assumed_midnight"
    if time_accuracy not in TIME_ACCURACY_VALUES:
        raise ValueError(f"time_accuracy must be one of {TIME_ACCURACY_VALUES}")
    cur = conn.execute(
        "INSERT OR IGNORE INTO entities (name, entity_type, birth_or_inception_date, "
        "birth_or_inception_place, birth_or_inception_time, timezone, latitude, "
        "longitude, source, source_reliability, time_accuracy, notes, category, "
        "created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (name, entity_type, birth_or_inception_date, birth_or_inception_place,
         birth_or_inception_time, timezone, latitude, longitude, source,
         source_reliability, time_accuracy, notes, category, _now_iso()),
    )
    conn.commit()
    return cur.lastrowid


def get_entity(conn: sqlite3.Connection, entity_id: int) -> Optional[Entity]:
    row = conn.execute("SELECT * FROM entities WHERE id = ?", (entity_id,)).fetchone()
    return _row_to_entity(row) if row else None


def search_entities(conn: sqlite3.Connection, query: Optional[str] = None,
                     entity_type: Optional[str] = None, category: Optional[str] = None,
                     limit: int = 25) -> List[Entity]:
    clauses, params = [], []
    if query:
        clauses.append("name LIKE ?")
        params.append(f"%{query}%")
    if entity_type:
        clauses.append("entity_type = ?")
        params.append(entity_type)
    if category:
        clauses.append("category = ?")
        params.append(category)
    sql = "SELECT * FROM entities"
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY name ASC LIMIT ?"
    params.append(limit)
    rows = conn.execute(sql, params).fetchall()
    return [_row_to_entity(r) for r in rows]


def get_entity_by_name(conn: sqlite3.Connection, name: str,
                        entity_type: Optional[str] = None) -> Optional[Entity]:
    matches = search_entities(conn, query=name, entity_type=entity_type, limit=5)
    exact = [e for e in matches if e.name.lower() == name.lower()]
    if exact:
        return exact[0]
    return matches[0] if matches else None


def mark_predicted(conn: sqlite3.Connection, entity_id: int) -> None:
    conn.execute(
        "UPDATE entities SET last_predicted_at = ?, prediction_count = prediction_count + 1 "
        "WHERE id = ?", (_now_iso(), entity_id),
    )
    conn.commit()


def count_entities(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0]


# ---------------------------------------------------------------------------
# Seeding from this project's existing, real, already-vetted corpora.
# ---------------------------------------------------------------------------

def seed_from_existing_corpora(conn: sqlite3.Connection) -> dict:
    """Populates `entities` from kundli_mass/{nations,famous_people,leaders}_corpus.py
    -- real data this project already researched and committed, not fabricated
    for this feature. Idempotent (UNIQUE constraint + INSERT OR IGNORE): safe to
    call every server startup."""
    import sys
    kundli_mass_dir = os.path.join(HERE, "kundli_mass")
    if kundli_mass_dir not in sys.path:
        sys.path.insert(0, kundli_mass_dir)

    counts = {"country": 0, "person": 0, "government": 0}

    from nations_corpus import NATIONS
    for name, date, capital, lat, lon, tz, note in NATIONS:
        add_entity(conn, name=name, entity_type="country",
                   birth_or_inception_date=date, birth_or_inception_place=capital,
                   latitude=lat, longitude=lon, timezone=tz,
                   source="kundli_mass/nations_corpus.py",
                   source_reliability="MEDIUM", time_accuracy="assumed_midnight",
                   notes=note, category="nation")
        counts["country"] += 1

    from famous_people_corpus import PEOPLE
    for name, date, ptime, tz, country, lat, lon, pfield, note in PEOPLE:
        add_entity(conn, name=name, entity_type="person",
                   birth_or_inception_date=date, birth_or_inception_place=country,
                   birth_or_inception_time=ptime, latitude=lat, longitude=lon, timezone=tz,
                   source="kundli_mass/famous_people_corpus.py",
                   source_reliability="MEDIUM" if ptime else "LOW",
                   time_accuracy="documented" if ptime else "assumed_noon",
                   notes=note, category=pfield)
        counts["person"] += 1

    from leaders_corpus import LEADERS
    for name, date, ltime, tz, country, lat, lon, group, tenure_start, tenure_years, \
            reelected, left_reason in LEADERS:
        add_entity(conn, name=name, entity_type="person",
                   birth_or_inception_date=date, birth_or_inception_place=country,
                   birth_or_inception_time=ltime, latitude=lat, longitude=lon, timezone=tz,
                   source="kundli_mass/leaders_corpus.py",
                   source_reliability="MEDIUM" if ltime else "LOW",
                   time_accuracy="documented" if ltime else "assumed_noon",
                   notes=f"{group}; tenure_start={tenure_start}; left={left_reason}",
                   category=group)
        counts["government"] += 1

    return counts


if __name__ == "__main__":
    conn = get_connection()
    before = count_entities(conn)
    counts = seed_from_existing_corpora(conn)
    after = count_entities(conn)
    print(f"Entities before: {before}, after: {after} (delta {after - before})")
    print(f"Seeded from corpora: {counts}")
