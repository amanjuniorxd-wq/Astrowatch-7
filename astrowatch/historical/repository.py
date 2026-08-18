"""
Astrowatch — historical_events.db repository layer.

All raw SQL for the historical database lives here (per spec item 4: "Do not
scatter raw SQL throughout the project"). No astrology imports.
"""

import sqlite3
from datetime import datetime, timezone
from typing import List, Optional

from .models import ControlDate, DatasetVersion, Event, EventSource, Source


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---------------------------------------------------------------------------
# Write path (used only by scripts/ingest_historical_data.py and versioning.py)
# ---------------------------------------------------------------------------

def create_dataset_version(conn: sqlite3.Connection, dv: DatasetVersion) -> None:
    conn.execute(
        """INSERT INTO dataset_versions
           (version_id, created_date, description, event_count, source_count,
            frozen, frozen_at, checksum_sha256, known_limitations, notes)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (dv.version_id, dv.created_date, dv.description, dv.event_count,
         dv.source_count, int(dv.frozen), dv.frozen_at, dv.checksum_sha256,
         dv.known_limitations, dv.notes),
    )


def insert_source(conn: sqlite3.Connection, s: Source) -> None:
    conn.execute(
        """INSERT INTO sources
           (source_id, dataset_name, organization, source_type, tier, url,
            access_date, coverage, notes)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (s.source_id, s.dataset_name, s.organization, s.source_type, s.tier,
         s.url, s.access_date, s.coverage, s.notes),
    )


def insert_event(conn: sqlite3.Connection, e: Event) -> None:
    conn.execute(
        """INSERT INTO events
           (event_id, canonical_event_id, event_name, event_type, event_subtype,
            start_date, end_date, start_time, end_time, timezone, country,
            country_code, region, location_name, latitude, longitude,
            location_precision, description, source_quality_tier, date_confidence,
            time_confidence, location_confidence, verification_status,
            verification_count, dataset_version, created_at, updated_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (e.event_id, e.canonical_event_id, e.event_name, e.event_type,
         e.event_subtype, e.start_date, e.end_date, e.start_time, e.end_time,
         e.timezone, e.country, e.country_code, e.region, e.location_name,
         e.latitude, e.longitude, e.location_precision, e.description,
         e.source_quality_tier, e.date_confidence, e.time_confidence,
         e.location_confidence, e.verification_status, e.verification_count,
         e.dataset_version, e.created_at, e.updated_at),
    )


def insert_event_source(conn: sqlite3.Connection, link: EventSource) -> None:
    conn.execute(
        """INSERT INTO event_sources
           (event_id, source_id, source_url, link_verification_status, notes, created_at)
           VALUES (?,?,?,?,?,?)""",
        (link.event_id, link.source_id, link.source_url,
         link.link_verification_status, link.notes, link.created_at),
    )


def insert_control_date(conn: sqlite3.Connection, c: ControlDate) -> None:
    conn.execute(
        """INSERT INTO control_dates
           (control_id, date, region, sampling_method, seed, selection_timestamp,
            source_window, dataset_version, notes)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (c.control_id, c.date, c.region, c.sampling_method, c.seed,
         c.selection_timestamp, c.source_window, c.dataset_version, c.notes),
    )


# ---------------------------------------------------------------------------
# Read path -- the ONLY interface a future backtest engine should use.
# Never mutates. Category/region/date/quality filters only, per spec item 25.
# ---------------------------------------------------------------------------

def get_events(
    conn: sqlite3.Connection,
    category: Optional[str] = None,
    region: Optional[str] = None,
    country_code: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    min_source_quality: Optional[int] = None,   # tier <= this value (1 is best)
    min_date_confidence: Optional[List[str]] = None,  # allowed confidence values
    min_time_confidence: Optional[List[str]] = None,
    dataset_version: Optional[str] = None,
) -> List[sqlite3.Row]:
    clauses = []
    params: list = []
    if category:
        clauses.append("event_type = ?")
        params.append(category)
    if region:
        clauses.append("region = ?")
        params.append(region)
    if country_code:
        clauses.append("country_code = ?")
        params.append(country_code)
    if start_date:
        clauses.append("start_date >= ?")
        params.append(start_date)
    if end_date:
        clauses.append("start_date <= ?")
        params.append(end_date)
    if min_source_quality is not None:
        clauses.append("source_quality_tier <= ?")
        params.append(min_source_quality)
    if min_date_confidence:
        placeholders = ",".join("?" for _ in min_date_confidence)
        clauses.append(f"date_confidence IN ({placeholders})")
        params.extend(min_date_confidence)
    if min_time_confidence:
        placeholders = ",".join("?" for _ in min_time_confidence)
        clauses.append(f"time_confidence IN ({placeholders})")
        params.extend(min_time_confidence)
    if dataset_version:
        clauses.append("dataset_version = ?")
        params.append(dataset_version)

    sql = "SELECT * FROM events"
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY start_date ASC, event_id ASC"
    return conn.execute(sql, params).fetchall()


def get_event(conn: sqlite3.Connection, event_id: str) -> Optional[sqlite3.Row]:
    return conn.execute("SELECT * FROM events WHERE event_id = ?", (event_id,)).fetchone()


def get_event_sources(conn: sqlite3.Connection, event_id: str) -> List[sqlite3.Row]:
    return conn.execute(
        """SELECT es.*, s.dataset_name, s.organization, s.tier, s.url AS source_base_url
           FROM event_sources es JOIN sources s ON es.source_id = s.source_id
           WHERE es.event_id = ?""",
        (event_id,),
    ).fetchall()


def get_control_dates(
    conn: sqlite3.Connection,
    region: Optional[str] = None,
    dataset_version: Optional[str] = None,
) -> List[sqlite3.Row]:
    clauses, params = [], []
    if region:
        clauses.append("region = ?")
        params.append(region)
    if dataset_version:
        clauses.append("dataset_version = ?")
        params.append(dataset_version)
    sql = "SELECT * FROM control_dates"
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY date ASC"
    return conn.execute(sql, params).fetchall()


def get_dataset_version(conn: sqlite3.Connection, version_id: str) -> Optional[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM dataset_versions WHERE version_id = ?", (version_id,)
    ).fetchone()
