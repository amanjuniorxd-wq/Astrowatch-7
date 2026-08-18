#!/usr/bin/env python3
"""
Astrowatch — build ASTROWATCH-HIST-002: a quality-improved successor to
ASTROWATCH-HIST-001, per an explicit follow-up instruction to raise data quality
through independent verification rather than expand raw event count.

Does NOT touch historical_events.db's existing ASTROWATCH-HIST-001 rows (immutable
via schema trigger — see historical_events_schema.sql). Builds a second
dataset_version in a separate database file, historical_events_v2.db, so 001 stays
exactly as frozen and inspectable on its own.

Changes versus HIST-001:
  1. Applies data/verification_updates.py's 12 real WebSearch-checked corrections/
     upgrades (UNVERIFIED -> MULTI_SOURCE_CONFIRMED, with real source citations).
  2. Adds historical/ingestion/noaa.py's real NOAA tsunami data (6 events, Tier 1,
     exact date/time/location) -- see that adapter's docstring for how it was
     obtained.
  3. Drops the 2 curated placeholder tsunami entries ("2004 Indian Ocean tsunami",
     "2011 Tōhoku tsunami") in favor of the NOAA-sourced versions of the same real
     events, avoiding duplication while upgrading precision and source tier.
  4. Re-runs the improved (broader-signal) deduplication scan.
"""
import csv
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from historical import database, deduplication, models, repository  # noqa: E402
from historical.ingestion.usgs import USGSEarthquakeAdapter, RAW_FILE_RELATIVE as USGS_RAW  # noqa: E402
from historical.ingestion.noaa import NOAATsunamiAdapter, RAW_FILE_RELATIVE as NOAA_RAW  # noqa: E402
from historical.ingestion.base import NormalizedEventRecord  # noqa: E402
from data.curated_events import as_dicts  # noqa: E402
from data.verification_updates import VERIFICATION_UPDATES  # noqa: E402

DB_PATH = "historical_events_v2.db"
DATASET_VERSION = "ASTROWATCH-HIST-002"
NOW = datetime.now(timezone.utc).isoformat(timespec="seconds")

DROPPED_CURATED_EVENT_NAMES = {
    "2004 Indian Ocean tsunami",
    "2011 Tōhoku tsunami",
}

BASE_SOURCES = [
    models.Source(
        "SRC-USGS-EARTHQUAKE", "USGS Earthquake Catalog (FDSNWS event API)",
        "United States Geological Survey", "government_scientific_agency", 1,
        "https://earthquake.usgs.gov/fdsnws/event/1/query", "2026-08-14",
        "Global earthquake catalog, M>=8.3, 1900-2026", "Tier 1.",
    ),
    models.Source(
        "SRC-NOAA-TSUNAMI", "NOAA NGDC Significant Tsunami Database",
        "National Oceanic and Atmospheric Administration", "government_scientific_agency", 1,
        "https://www.ngdc.noaa.gov/hazel/hazard-service/api/v1/tsunamis/events", "2026-08-14",
        "Significant historical tsunamis with 1000+ recorded deaths, 1880-2025",
        "Tier 1. Real query executed via web_fetch this pass (see historical/ingestion/noaa.py).",
    ),
    models.Source(
        "SRC-GENERAL-REFERENCE", "General historical reference knowledge (uncited)",
        None, "general_reference_recall", 4, None, None,
        "Broad, but not independently re-verified via a specific live source",
        "Used only for events not covered by this pass's WebSearch verification batch.",
    ),
    models.Source(
        "SRC-PBS-ARGENTINA-2001", "PBS NewsHour — Argentina coverage, Dec 2001",
        "PBS", "news_archive", 3,
        "https://www.pbs.org/newshour/politics/latin_america-july-dec01-argentina_12-24",
        "2026-08-14", "Argentina's Dec 2001 crisis", "Carried over from HIST-001.",
    ),
    models.Source(
        "SRC-HISTORY-1918FLU", "History.com — 'This Day in History: March 4'",
        "A&E Television Networks", "encyclopedia", 3,
        "https://www.history.com/this-day-in-history/march-4/first-cases-reported-in-deadly-influenza-epidemic",
        "2026-08-14", "1918 influenza pandemic first cases", "Carried over from HIST-001.",
    ),
    models.Source(
        "SRC-LIVESCIENCE-PENICILLIN", "Live Science — Fleming penicillin discovery article",
        "Future US Inc.", "encyclopedia", 3,
        "https://www.livescience.com/health/science-history-alexander-fleming-wakes-up-to-funny-mold-in-his-petri-dish-and-accidentally-discovers-the-first-antibiotic",
        "2026-08-14", "Fleming's discovery of penicillin", "Carried over from HIST-001.",
    ),
]

CARRIED_OVER_EVENT_SOURCE_MAP = {
    "Argentina declares sovereign debt default": ["SRC-PBS-ARGENTINA-2001"],
    "First documented cases of the 1918 influenza pandemic": ["SRC-HISTORY-1918FLU", "SRC-GENERAL-REFERENCE"],
    "Alexander Fleming observes penicillin's antibacterial effect": ["SRC-LIVESCIENCE-PENICILLIN", "SRC-GENERAL-REFERENCE"],
}


def assign_event_id(start_date: str, counters: dict) -> str:
    year_key = start_date[:4]
    counters[year_key] = counters.get(year_key, 0) + 1
    return f"EVENT-{year_key}-{counters[year_key]:03d}"


def build_events():
    counters: dict = {}
    events = []            # (event_id, rec, verification, n_sources)
    event_source_links = []  # (event_id, [source_id...])
    extra_sources = []       # models.Source objects introduced by verification updates

    # --- USGS earthquakes (unchanged from HIST-001) ---
    adapter = USGSEarthquakeAdapter()
    with open(USGS_RAW) as f:
        usgs_records = adapter.normalize(adapter.parse(f.read()))
    for rec in usgs_records:
        eid = assign_event_id(rec.start_date, counters)
        events.append((eid, rec, "SINGLE_SOURCE", 1))
        event_source_links.append((eid, ["SRC-USGS-EARTHQUAKE"]))

    # --- NOAA tsunamis (NEW this pass) ---
    noaa_adapter = NOAATsunamiAdapter()
    with open(NOAA_RAW) as f:
        noaa_records = noaa_adapter.normalize(noaa_adapter.parse(f.read()))
    for rec in noaa_records:
        eid = assign_event_id(rec.start_date, counters)
        events.append((eid, rec, "SINGLE_SOURCE", 1))
        event_source_links.append((eid, ["SRC-NOAA-TSUNAMI"]))

    # --- curated events, with verification updates applied, dropped ones skipped ---
    for d in as_dicts():
        if d["event_name"] in DROPPED_CURATED_EVENT_NAMES:
            continue
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
        verification = d["verification"]
        src_ids = CARRIED_OVER_EVENT_SOURCE_MAP.get(d["event_name"], ["SRC-GENERAL-REFERENCE"])

        update = VERIFICATION_UPDATES.get(d["event_name"])
        if update:
            verification = update["verification_status"]
            for field, value in update.get("corrections", {}).items():
                setattr(rec, field, value)
            if "source_quality_tier_override" in update:
                rec.source_quality_tier = update["source_quality_tier_override"]
            else:
                rec.source_quality_tier = min(s[4] for s in update["sources"])
            src_ids = []
            for sid, dname, org, stype, tier, url in update["sources"]:
                extra_sources.append(models.Source(sid, dname, org, stype, tier, url, "2026-08-14", None, None))
                src_ids.append(sid)

        eid = assign_event_id(rec.start_date, counters)
        n_sources = len(src_ids)
        events.append((eid, rec, verification, n_sources))
        event_source_links.append((eid, src_ids))

    return events, event_source_links, extra_sources


def main():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = database.initialize_db(DB_PATH)

    dv = models.DatasetVersion(
        version_id=DATASET_VERSION, created_date=NOW[:10],
        description="Astrowatch historical event database — quality-improved successor to "
                     "ASTROWATCH-HIST-001. Adds 12 real WebSearch-verified corrections, real "
                     "NOAA tsunami data (replacing 2 placeholder tsunami entries), and an "
                     "expanded-signal deduplication scan. Does not touch HIST-001.",
    )
    repository.create_dataset_version(conn, dv)

    events, links, extra_sources = build_events()

    seen_source_ids = set()
    for s in BASE_SOURCES + extra_sources:
        if s.source_id in seen_source_ids:
            continue
        seen_source_ids.add(s.source_id)
        repository.insert_source(conn, s)

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
                event_id=eid, source_id=sid, link_verification_status="CONFIRMED", created_at=NOW,
            ))
    conn.commit()

    # --- deduplication candidate scan (broader signal set this pass) ---
    all_events = [dict(row) for row in conn.execute(
        "SELECT event_id, event_name, event_type, event_subtype, start_date, end_date, "
        "country_code, region, location_name, description FROM events"
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
        for row in conn.execute(
            "SELECT event_id, event_name, date_confidence FROM events WHERE date_confidence = 'DISPUTED'"
        ).fetchall():
            w.writerow([row["event_id"], f"date_confidence=DISPUTED: {row['event_name']}",
                        "DISPUTED", "confirm which cited date this project should treat as canonical, "
                        "or keep as DISPUTED permanently", "see event_sources for this event_id", "OPEN"])

    conn.close()
    print(f"Ingested {len(events)} events into {DATASET_VERSION}.")
    print(f"Duplicate candidates found: {len(candidates)}")
    for c in candidates:
        print(f"  [{c.confidence}] {c.event_id_a} / {c.event_id_b}: {c.reason}")


if __name__ == "__main__":
    main()
