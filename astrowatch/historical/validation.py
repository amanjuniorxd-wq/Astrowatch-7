"""
Astrowatch — historical database validation checks.

Flags problems. Never silently repairs data (spec item 21: "Do not silently
repair questionable historical data. Flag it."). Used by scripts/validate_historical_db.py.
"""

import sqlite3
from dataclasses import dataclass
from datetime import date as _date
from typing import List

from . import taxonomy


@dataclass
class ValidationIssue:
    severity: str  # "FATAL" | "WARNING"
    check: str
    event_id: str
    detail: str


def _is_valid_iso_date(s: str) -> bool:
    if not s:
        return False
    try:
        y, m, d = (int(x) for x in s.split("-"))
        _date(y, m, d)
        return True
    except (ValueError, AttributeError):
        return False


def validate(conn: sqlite3.Connection) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []
    events = conn.execute("SELECT * FROM events").fetchall()
    event_ids = set()

    for e in events:
        eid = e["event_id"]

        # missing / duplicate event IDs
        if not eid:
            issues.append(ValidationIssue("FATAL", "missing_event_id", "<unknown>", "event_id is empty"))
            continue
        if eid in event_ids:
            issues.append(ValidationIssue("FATAL", "duplicate_event_id", eid, "event_id appears more than once"))
        event_ids.add(eid)

        # invalid dates
        if not _is_valid_iso_date(e["start_date"]):
            issues.append(ValidationIssue("FATAL", "invalid_start_date", eid, f"start_date={e['start_date']!r}"))
        if e["end_date"] and not _is_valid_iso_date(e["end_date"]):
            issues.append(ValidationIssue("FATAL", "invalid_end_date", eid, f"end_date={e['end_date']!r}"))
        if e["end_date"] and _is_valid_iso_date(e["start_date"]) and _is_valid_iso_date(e["end_date"]):
            if e["end_date"] < e["start_date"]:
                issues.append(ValidationIssue("FATAL", "start_after_end", eid,
                                               f"start_date={e['start_date']} > end_date={e['end_date']}"))
        if e["start_time"] and e["end_time"] and e["start_time"] > e["end_time"] and not e["end_date"]:
            issues.append(ValidationIssue("FATAL", "start_time_after_end_time", eid,
                                           f"start_time={e['start_time']} > end_time={e['end_time']} same day"))

        # invalid coordinates
        if e["latitude"] is not None and not (-90.0 <= e["latitude"] <= 90.0):
            issues.append(ValidationIssue("FATAL", "invalid_latitude", eid, f"latitude={e['latitude']}"))
        if e["longitude"] is not None and not (-180.0 <= e["longitude"] <= 180.0):
            issues.append(ValidationIssue("FATAL", "invalid_longitude", eid, f"longitude={e['longitude']}"))
        if (e["latitude"] is None) != (e["longitude"] is None):
            issues.append(ValidationIssue("FATAL", "partial_coordinates", eid,
                                           "exactly one of latitude/longitude is set"))

        # invalid taxonomy
        if not taxonomy.is_valid_type_subtype(e["event_type"], e["event_subtype"]):
            issues.append(ValidationIssue("FATAL", "invalid_taxonomy", eid,
                                           f"event_type={e['event_type']!r} event_subtype={e['event_subtype']!r}"))

        # inconsistent confidence fields (defense in depth -- schema CHECK already
        # blocks some of these at insert time; re-checked here in case of a future
        # non-repository write path)
        if e["time_confidence"] == "EXACT" and not e["start_time"]:
            issues.append(ValidationIssue("FATAL", "fake_time_precision", eid,
                                           "time_confidence=EXACT but start_time is NULL"))
        # EXACT requires real coordinates; CITY only requires a known city/country
        # name (not fabricated coordinates) -- see historical_events_schema.sql's
        # comment on this exact distinction, added after the first real ingestion
        # run correctly caught an overly strict version of this check.
        if e["location_confidence"] == "EXACT" and e["latitude"] is None:
            issues.append(ValidationIssue("FATAL", "fake_location_precision", eid,
                                           f"location_confidence=EXACT but no coordinates"))
        if e["location_confidence"] in ("EXACT", "CITY") and not e["location_name"] and not e["country"]:
            issues.append(ValidationIssue("FATAL", "fake_location_precision", eid,
                                           f"location_confidence={e['location_confidence']} but no location_name or country"))

        # impossible timezone values (loose check -- just non-empty and plausible)
        if e["start_time"] and not e["timezone"]:
            issues.append(ValidationIssue("WARNING", "missing_timezone_with_time", eid,
                                           "start_time is set but timezone is NULL"))

        # missing provenance
        n_sources = conn.execute(
            "SELECT COUNT(*) FROM event_sources WHERE event_id = ?", (eid,)
        ).fetchone()[0]
        if n_sources == 0:
            issues.append(ValidationIssue("FATAL", "missing_provenance", eid, "no event_sources rows at all"))

        # invalid dataset-version reference
        dv = conn.execute(
            "SELECT 1 FROM dataset_versions WHERE version_id = ?", (e["dataset_version"],)
        ).fetchone()
        if not dv:
            issues.append(ValidationIssue("FATAL", "invalid_dataset_version_ref", eid,
                                           f"dataset_version={e['dataset_version']!r} not found"))

    # orphaned source records (sources with zero event_sources links)
    orphan_sources = conn.execute(
        """SELECT s.source_id FROM sources s
           LEFT JOIN event_sources es ON es.source_id = s.source_id
           WHERE es.id IS NULL"""
    ).fetchall()
    for row in orphan_sources:
        issues.append(ValidationIssue("WARNING", "orphaned_source", row["source_id"],
                                       "source exists but is not linked to any event"))

    # orphaned event_sources rows (event_id not found in events)
    orphan_links = conn.execute(
        """SELECT es.id, es.event_id FROM event_sources es
           LEFT JOIN events e ON e.event_id = es.event_id
           WHERE e.event_id IS NULL"""
    ).fetchall()
    for row in orphan_links:
        issues.append(ValidationIssue("FATAL", "orphaned_event_source", str(row["event_id"]),
                                       f"event_sources.id={row['id']} references a nonexistent event"))

    # orphaned control_date dataset_version references
    orphan_controls = conn.execute(
        """SELECT c.control_id FROM control_dates c
           LEFT JOIN dataset_versions dv ON dv.version_id = c.dataset_version
           WHERE dv.version_id IS NULL"""
    ).fetchall()
    for row in orphan_controls:
        issues.append(ValidationIssue("FATAL", "invalid_control_dataset_version_ref",
                                       row["control_id"], "dataset_version not found"))

    # duplicate canonical IDs where inappropriate: a canonical_event_id group where
    # the events disagree wildly on start_date (>30 days apart) is suspicious --
    # flagged as WARNING, not auto-fixed.
    canon_groups: dict = {}
    for e in events:
        canon_groups.setdefault(e["canonical_event_id"], []).append(e)
    for canon_id, group in canon_groups.items():
        if len(group) > 1:
            dates = sorted({g["start_date"] for g in group if _is_valid_iso_date(g["start_date"])})
            if len(dates) > 1:
                y1, m1, d1 = (int(x) for x in dates[0].split("-"))
                y2, m2, d2 = (int(x) for x in dates[-1].split("-"))
                spread_days = (_date(y2, m2, d2) - _date(y1, m1, d1)).days
                if spread_days > 30:
                    issues.append(ValidationIssue(
                        "WARNING", "canonical_group_date_spread", canon_id,
                        f"{len(group)} records share canonical_event_id={canon_id} but their "
                        f"start_dates span {spread_days} days -- verify these are really the same event",
                    ))

    return issues


def exit_code_for(issues: List[ValidationIssue]) -> int:
    return 1 if any(i.severity == "FATAL" for i in issues) else 0
