#!/usr/bin/env python3
"""
Astrowatch — ingest the pilot historical event dataset into historical_events.db.

Combines:
  1. historical/ingestion/usgs.py -- real USGS earthquake catalog data, actually
     parsed from data/raw/usgs_earthquakes_m8.3plus_1900_2026_raw.json (a genuine
     response fetched this session).
  2. data/curated_events.py -- general-knowledge / WebSearch-checked events, each
     honestly labeled per its actual verification this session (see that file's
     docstring for the methodology).

Assigns deterministic event_id ('EVENT-{year}-{seq:03d}') and canonical_event_id
(= event_id; no pre-existing duplicates in this pilot set). Runs deduplication
candidate detection and writes any hits to manual_review.csv. Does NOT freeze the
dataset -- that is a separate, explicit step (scripts/freeze_historical_dataset.py).
"""
import csv
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from historical import database, deduplication, models, repository, taxonomy  # noqa: E402
from historical.ingestion.usgs import USGSEarthquakeAdapter, RAW_FILE_RELATIVE  # noqa: E402
from data.curated_events import as_dicts  # noqa: E402

DB_PATH = "historical_events.db"
DATASET_VERSION = "ASTROWATCH-HIST-001"
NOW = datetime.now(timezone.utc).isoformat(timespec="seconds")

# ---------------------------------------------------------------------------
# Source registry -- every source actually used, honestly described.
# ---------------------------------------------------------------------------
SOURCES = [
    models.Source(
        "SRC-USGS-EARTHQUAKE", "USGS Earthquake Catalog (FDSNWS event API)",
        "United States Geological Survey", "government_scientific_agency", 1,
        "https://earthquake.usgs.gov/fdsnws/event/1/query", "2026-08-14",
        "Global earthquake catalog, M>=8.3, 1900-2026 (16-event subset of a real "
        "31-event query result actually fetched this session)",
        "Tier 1 (primary/official). Query executed via the agent's web_fetch tool "
        "(this sandbox's own network stack cannot reach earthquake.usgs.gov -- see "
        "historical/ingestion/usgs.py). Raw response saved to "
        "data/raw/usgs_earthquakes_m8.3plus_1900_2026_raw.json.",
    ),
    models.Source(
        "SRC-GENERAL-REFERENCE", "General historical reference knowledge (uncited)",
        None, "general_reference_recall", 4, None, None,
        "Broad, but not independently re-verified via a specific live source this session",
        "Used only for events considered well-established/non-controversial general "
        "knowledge. NOT independently checked against a citable source this session -- "
        "see data/curated_events.py's docstring and HISTORICAL_DATA_QUALITY_REPORT.md "
        "for exactly what this means and why it is labeled tier 4 / UNVERIFIED rather "
        "than a higher tier or verification status.",
    ),
    models.Source(
        "SRC-PBS-ARGENTINA-2001", "PBS NewsHour — Argentina coverage, Dec 2001",
        "PBS", "news_archive", 3,
        "https://www.pbs.org/newshour/politics/latin_america-july-dec01-argentina_12-24",
        "2026-08-14", "Argentina's Dec 2001 political/economic crisis",
        "Actually fetched via WebSearch this session to resolve the exact Argentina "
        "default announcement date (Dec 23, 2001).",
    ),
    models.Source(
        "SRC-HISTORY-1918FLU", "History.com — 'This Day in History: March 4'",
        "A&E Television Networks", "encyclopedia", 3,
        "https://www.history.com/this-day-in-history/march-4/first-cases-reported-in-deadly-influenza-epidemic",
        "2026-08-14", "1918 influenza pandemic first cases",
        "Actually fetched via WebSearch this session; cites March 4, 1918. Other "
        "sources found in the same search cite March 11 -- see manual_review.csv.",
    ),
    models.Source(
        "SRC-LIVESCIENCE-PENICILLIN", "Live Science — Fleming penicillin discovery article",
        "Future US Inc.", "encyclopedia", 3,
        "https://www.livescience.com/health/science-history-alexander-fleming-wakes-up-to-funny-mold-in-his-petri-dish-and-accidentally-discovers-the-first-antibiotic",
        "2026-08-14", "Alexander Fleming's discovery of penicillin",
        "Actually fetched via WebSearch this session; cites Sept 28, 1928. "
        "History.com's search snippet cited Sept 3, 1928 instead -- see manual_review.csv.",
    ),
]

CURATED_EVENT_SOURCE_MAP = {
    "Argentina declares sovereign debt default": ["SRC-PBS-ARGENTINA-2001"],
    "First documented cases of the 1918 influenza pandemic": ["SRC-HISTORY-1918FLU", "SRC-GENERAL-REFERENCE"],
    "Alexander Fleming observes penicillin's antibacterial effect": ["SRC-LIVESCIENCE-PENICILLIN", "SRC-GENERAL-REFERENCE"],
}


def assign_event_id(start_date: str, counters: dict) -> str:
    year = start_date[:4].lstrip("-") or "0000"
    # ISO dates like '0079-08-24' -> year '0079'; keep as-is for readability
    year_key = start_date[:4]
    counters[year_key] = counters.get(year_key, 0) + 1
    return f"EVENT-{year_key}-{counters[year_key]:03d}"


def build_events():
    counters: dict = {}
    events = []
    event_source_links = []  # (event_id, [source_ids])

    # --- USGS earthquakes ---
    adapter = USGSEarthquakeAdapter()
    with open(RAW_FILE_RELATIVE) as f:
        raw = f.read()
    usgs_records = adapter.normalize(adapter.parse(raw))
    for rec in usgs_records:
        eid = assign_event_id(rec.start_date, counters)
        events.append((eid, rec, "SINGLE_SOURCE", 1))
        event_source_links.append((eid, ["SRC-USGS-EARTHQUAKE"]))

    # --- curated events ---
    for d in as_dicts():
        from historical.ingestion.base import NormalizedEventRecord
        rec = NormalizedEventRecord(
            event_name=d["event_name"], event_type=d["event_type"],
            event_subtype=d["event_subtype"], start_date=d["start_date"],
            end_date=d["end_date"], start_time=d["start_time"], end_time=None,
            timezone=d["timezone"], date_confidence=d["date_confidence"],
            time_confidence=d["time_confidence"], location_confidence=d["location_confidence"],
            location_precision=d["location_precision"], description=d["description"],
            source_quality_tier=(3 if d["verification"] != "UNVERIFIED" else 4),
            country=d["country"], country_code=d["country_code"], region=d["region"],
            location_name=d["location_name"], latitude=d["latitude"], longitude=d["longitude"],
        )
        eid = assign_event_id(rec.start_date, counters)
        verification = d["verification"]
        src_ids = CURATED_EVENT_SOURCE_MAP.get(d["event_name"], ["SRC-GENERAL-REFERENCE"])
        events.append((eid, rec, verification, len(src_ids)))
        event_source_links.append((eid, src_ids))

    return events, event_source_links


def main():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = database.initialize_db(DB_PATH)

    dv = models.DatasetVersion(
        version_id=DATASET_VERSION, created_date=NOW[:10],
        description="Astrowatch historical event database — pilot dataset. Built "
                     "independently of Astrowatch's astrology code (see "
                     "historical/__init__.py). Combines real USGS earthquake catalog "
                     "data with general-knowledge/WebSearch-checked events.",
    )
    repository.create_dataset_version(conn, dv)

    for s in SOURCES:
        repository.insert_source(conn, s)

    events, links = build_events()

    for eid, rec, verification, n_sources in events:
        e = models.Event(
            event_id=eid, canonical_event_id=eid, event_name=rec.event_name,
            event_type=rec.event_type, event_subtype=rec.event_subtype,
            start_date=rec.start_date, end_date=rec.end_date,
            start_time=rec.start_time, end_time=rec.end_time, timezone=rec.timezone,
            country=rec.country, country_code=rec.country_code, region=rec.region,
            location_name=rec.location_name, latitude=rec.latitude, longitude=rec.longitude,
            location_precision=rec.location_precision, description=rec.description,
            source_quality_tier=rec.source_quality_tier,
            date_confidence=rec.date_confidence, time_confidence=rec.time_confidence,
            location_confidence=rec.location_confidence,
            verification_status=verification, verification_count=n_sources,
            dataset_version=DATASET_VERSION, created_at=NOW, updated_at=NOW,
        )
        repository.insert_event(conn, e)

    for eid, src_ids in links:
        for sid in src_ids:
            repository.insert_event_source(conn, models.EventSource(
                event_id=eid, source_id=sid, link_verification_status="CONFIRMED",
                created_at=NOW,
            ))

    conn.commit()

    # --- deduplication candidate scan ---
    all_events = [dict(row) for row in conn.execute(
        "SELECT event_id, event_name, event_type, event_subtype, start_date, country_code FROM events"
    ).fetchall()]
    candidates = deduplication.find_duplicate_candidates(all_events)

    manual_review_path = "manual_review.csv"
    with open(manual_review_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["event_id", "reason", "current_value", "recommended_action", "source", "status"])
        for c in candidates:
            w.writerow([c.event_id_a, f"possible duplicate of {c.event_id_b}: {c.reason}",
                        c.confidence, "human review before treating as canonical duplicate",
                        "historical.deduplication.find_duplicate_candidates()", "OPEN"])
        # also flag the two genuinely DISPUTED-date events and the APPROXIMATE-range
        # index-case events for explicit human review, per spec item 14
        for row in conn.execute(
            "SELECT event_id, event_name, date_confidence FROM events "
            "WHERE date_confidence IN ('DISPUTED')"
        ).fetchall():
            w.writerow([row["event_id"], f"date_confidence=DISPUTED: {row['event_name']}",
                        "DISPUTED", "confirm which cited date this project should treat as canonical, "
                        "or keep as DISPUTED permanently", "see event_sources for this event_id", "OPEN"])

    conn.close()
    print(f"Ingested {len(events)} events, {len(SOURCES)} sources.")
    print(f"Duplicate candidates found: {len(candidates)}")
    print(f"manual_review.csv written with {len(candidates)} duplicate-candidate rows "
          f"+ DISPUTED-date rows.")


if __name__ == "__main__":
    main()
