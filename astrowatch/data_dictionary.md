# Astrowatch — Historical Event Database Data Dictionary

Describes every table/field in `historical_events_schema.sql`. This is the single
source of truth for the controlled taxonomy (also encoded in `historical/taxonomy.py`).

## Table: `dataset_versions`

| Field | Type | Notes |
|---|---|---|
| version_id | TEXT PK | e.g. `ASTROWATCH-HIST-001` |
| created_date | TEXT | ISO8601 date |
| description | TEXT | |
| event_count / source_count | INTEGER | filled in at freeze time, from a live query, never hand-typed |
| frozen | INTEGER (0/1) | once 1, schema triggers block edits/deletes to this version's events/control_dates |
| frozen_at | TEXT | ISO8601 timestamp |
| checksum_sha256 | TEXT | SHA-256 of the `.db` file at freeze time |
| known_limitations | TEXT | honest, specific — not boilerplate |

## Table: `sources`

| Field | Type | Notes |
|---|---|---|
| source_id | TEXT PK | e.g. `SRC-USGS-EARTHQUAKE` |
| dataset_name / organization / source_type | TEXT | |
| tier | INTEGER 1-4 | 1=primary/official, 2=academic/structured, 3=high-quality secondary, 4=discovery-only/uncited |
| url / access_date | TEXT, nullable | NULL for tier-4 uncited-recall sources — never fabricated |
| coverage / notes | TEXT | |

## Table: `events`

| Field | Type | Notes |
|---|---|---|
| event_id | TEXT PK | deterministic, `EVENT-{year}-{seq:03d}` |
| canonical_event_id | TEXT | groups duplicate/multi-source records of the same real event; equals event_id when there's no duplicate |
| event_name / event_type / event_subtype | TEXT | event_type/subtype pairs constrained to the taxonomy below |
| start_date | TEXT, NOT NULL | ISO8601. For DATE_RANGE/APPROXIMATE events, the earliest reasonable bound |
| end_date | TEXT, nullable | NULL for point-in-time events |
| start_time / end_time | TEXT `HH:MM`, nullable | NULL unless genuinely known — see date/time confidence below |
| timezone | TEXT, nullable | should be non-NULL whenever start_time is set |
| country / country_code / region / location_name | TEXT, nullable | |
| latitude / longitude | REAL, nullable | -90..90 / -180..180; NEVER fabricated — see location_confidence |
| location_precision | TEXT | same vocabulary as location_confidence |
| description | TEXT, NOT NULL | |
| source_quality_tier | INTEGER 1-4 | best/primary tier among this event's linked sources |
| date_confidence | TEXT | `EXACT`, `APPROXIMATE`, `DATE_RANGE`, `DISPUTED`, `UNKNOWN` |
| time_confidence | TEXT | `EXACT`, `APPROXIMATE`, `UNKNOWN` — EXACT requires start_time to be set (schema-enforced) |
| location_confidence | TEXT | `EXACT`, `CITY`, `REGION`, `COUNTRY`, `APPROXIMATE`, `UNKNOWN` — EXACT requires coordinates; EXACT/CITY require a location_name or country (schema-enforced) |
| verification_status | TEXT | `UNVERIFIED`, `SINGLE_SOURCE`, `MULTI_SOURCE_CONFIRMED`, `DISPUTED` — see "Verification status, precisely" below |
| verification_count | INTEGER | number of independent sources actually checked this session (not the total sources ever cited elsewhere) |
| dataset_version | TEXT FK → dataset_versions | |
| created_at / updated_at | TEXT | ISO8601 timestamps |

### Verification status, precisely

This project is stricter than the minimum spec here, on purpose:

- **UNVERIFIED**: not checked against any specific citable source THIS session. May
  still be well-established historical fact (most of this pilot's 136 events are in
  this category) — the label describes this session's verification effort, not the
  event's actual truth-value.
- **SINGLE_SOURCE**: exactly one specific source was actually fetched/read this
  session and used to confirm the record.
- **MULTI_SOURCE_CONFIRMED**: two or more independent specific sources were actually
  checked this session. Note: if those sources *disagree*, the event should be
  `DISPUTED`, not `MULTI_SOURCE_CONFIRMED` — see the 1918 flu and penicillin events
  for real examples of this.
- **DISPUTED**: sources actually checked this session disagree with each other.

## Table: `event_sources`

| Field | Type | Notes |
|---|---|---|
| event_id, source_id | FK | UNIQUE together — one link per (event, source) pair |
| source_url | TEXT, nullable | the specific citation URL, which may differ from the source's base url |
| link_verification_status | TEXT | `CONFIRMED` / `UNCONFIRMED` |

## Table: `control_dates`

| Field | Type | Notes |
|---|---|---|
| control_id | TEXT PK | |
| date | TEXT | |
| sampling_method | TEXT | `RANDOM_DATE`, `MATCHED_DATE`, `CALENDAR_MATCH`, `PREDEFINED_CONTROL` |
| seed | INTEGER, required for RANDOM_DATE | reproducibility contract — see `historical/controls.py` |
| selection_timestamp / source_window | TEXT | when and over what date range the control was actually generated |

## Controlled event taxonomy

See `historical/taxonomy.py::EVENT_TAXONOMY` for the canonical, importable version.
Six top-level categories, each with 6-9 subtypes (MILITARY, POLITICAL, ECONOMIC,
NATURAL_DISASTER, SOCIAL_PUBLIC_HEALTH, SCIENCE_TECHNOLOGY) — see the original spec
for the exact subtype lists, reproduced verbatim in `taxonomy.py`.

## Source quality tiers

1. Primary/official (government record, official statistics, primary treaty text)
2. Academic/structured dataset (peer-reviewed, documented methodology)
3. High-quality secondary source (established encyclopedia, major news archive)
4. Discovery-only/uncited general reference

## What this database deliberately does NOT contain

No tithi, nakshatra, rāśi, planetary position, aspect, yoga, karana, ayanamsha, or
any other astrological/astronomical derived value. Those are computed downstream,
on demand, from an event's own start_date/start_time/location — never stored here.
See `historical/__init__.py` for why, and
`tests/historical/test_astrological_independence.py` for the automated guard.
