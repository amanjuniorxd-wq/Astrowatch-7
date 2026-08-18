# Astrowatch — Historical Event Database Architecture

Real, executed implementation. Every number and file path in this document was
confirmed against the actual repository state, not written speculatively.

## 1. Inspection performed before building anything (repo state as found)

`Astrowatch-2` on GitHub was empty (one 14-byte README) when this pass began. The
astronomy/astrology codebase referenced throughout this document (ephemeris client,
Lahiri ayanamsha, Panchang, Rāśi/Nakshatra, rule registry, experimental forecasting)
was ported in from this session's prior work (see the repo's first commit message)
and **actually executed for the first time** as part of this same pass — see
`docs/ASTRONOMY_VALIDATION_REPORT.md` Phase 11 for that full record (45/45 unit
tests, one real test-bug found and fixed, live-network diagnosis, etc.). That work
is a prerequisite for this document but is a separate concern from the historical
database itself.

Existing components as of this pass, all pre-existing and **untouched** by the
historical-database work described below (aside from one docstring correction to
`ayanamsha.py`'s `methodology_status()`, documented separately):

| Component | File |
|---|---|
| Astronomical engine (JPL Horizons client) | `ephemeris_client.py` |
| Sidereal/Lahiri engine | `ayanamsha.py` |
| Rāśi/Nakshatra classification | `rashi_nakshatra.py` |
| Panchang (partial) | `panchang.py` |
| Rule registry (18 rules, BS-19/42/20 sidereal_unresolved) | `rule_registry.py` |
| Experimental forecasting | `forecast.py` |
| Predictions storage | `predictions_schema.sql`, `evaluate_forecasts.py` |

No historical-event storage, no backtesting infrastructure, no `historical_events.db`
existed anywhere in the repo before this pass.

## 2. What this pass built (all real, all executed)

```text
historical/
    __init__.py          -- states the architectural boundary (see section 4)
    database.py           -- connect()/initialize_db()/db_session(), enables PRAGMA foreign_keys
    models.py              -- dataclasses mirroring the schema exactly
    repository.py           -- every SQL statement in the project lives here; get_events() read API
    taxonomy.py              -- controlled vocabulary (single source of truth)
    validation.py             -- flags, never silently repairs
    deduplication.py          -- candidate detection only, never auto-merges
    controls.py                -- reproducible seeded random control-date sampling
    versioning.py               -- freeze mechanism + SHA-256 checksum

    ingestion/
        base.py                  -- IngestionAdapter interface, NormalizedEventRecord
        usgs.py                   -- REAL: parses genuine USGS earthquake data (see section 5)
        ucdp.py, acled.py, gdelt.py, emdat.py, noaa.py, elections.py
                                    -- interface-only, NOT executed (see each file's
                                       docstring for the specific, diagnosed reason)

historical_events_schema.sql   -- real SQLite DDL: events, sources, event_sources,
                                   control_dates, dataset_versions + CHECK constraints
                                   + immutability triggers (all actually tested, see
                                   section 6)

data/
    curated_events.py            -- the 120 non-USGS pilot events, each with an honest
                                     `verification` field (see its own docstring)
    raw/usgs_earthquakes_m8.3plus_1900_2026_raw.json
                                    -- genuine USGS API response, saved verbatim

scripts/
    initialize_historical_db.py
    ingest_historical_data.py     -- combines USGS + curated data, assigns IDs, loads DB
    validate_historical_db.py
    generate_historical_quality_report.py
    generate_control_dates.py
    freeze_historical_dataset.py

tests/historical/
    test_database_and_repository.py         (11 tests)
    test_uncertainty_and_validation.py       (17 tests)
    test_dedup_controls_versioning.py        (14 tests)
    test_astrological_independence.py        (3 tests)
    test_astronomy_integration.py            (4 tests)

data_dictionary.md, source_manifest.csv, manual_review.csv,
HISTORICAL_DATA_QUALITY_REPORT.md, DATASET_FREEZE.md
```

## 3. Data flow (as actually implemented, matching the spec's "correct" diagram)

```
Real sources (USGS API; WebSearch for a handful of disputed dates; general
historical reference knowledge for the rest -- see data/curated_events.py)
        |
        v
historical/ingestion/*.py  (normalize into NormalizedEventRecord)
        |
        v
scripts/ingest_historical_data.py  (assign event_id/canonical_event_id, load)
        |
        v
historical_events.db  (events, sources, event_sources, control_dates,
                        dataset_versions -- frozen as ASTROWATCH-HIST-001)
        |
        v
historical/repository.py::get_events()  <-- the ONLY read interface a future
        |                                    backtest engine should use
        v
[NOT BUILT THIS PASS -- future work] astronomical calculation using the event's
    OWN stored date/time/location, feeding ephemeris_client.py -> ayanamsha.py
        |
        v
panchang.py -> rashi_nakshatra.py -> rule_registry.py rule matching
        |
        v
backtest_results.db  [NOT BUILT THIS PASS]
```

`tests/historical/test_astronomy_integration.py` proves the one link in this chain
that COULD be exercised without live network access this pass: pulling a real
event's date out of `historical_events.db` via `get_events()` and feeding it into
the real, unmodified `ayanamsha.py`/`rashi_nakshatra.py`/`rule_registry.py` — 4/4
tests pass. The steps below that (a full backtest engine, `backtest_results.db`)
are explicitly out of scope for "build the historical event database."

## 4. The astrological-independence boundary

Stated in `historical/__init__.py`, and mechanically enforced by
`tests/historical/test_astrological_independence.py`:

- No file under `historical/` imports or references (by AST-level identifier check,
  not just import statements) `ayanamsha`, `panchang`, `rashi_nakshatra`,
  `rule_registry`, `aspects`, `engines`, `forecast`, `rule_matcher`, `coordinates`,
  or `ephemeris_client`.
- No astrology module imports `historical` or `data`.
- Event selection for the pilot dataset (`data/curated_events.py`, the USGS query
  parameters in `historical/ingestion/usgs.py`) never referenced any astrological
  configuration, rule, or hypothesis — the USGS query was a plain magnitude/date
  filter; the curated list was compiled from ordinary historical-significance
  criteria (major wars, revolutions, disasters, discoveries), not from checking
  what planetary configuration coincided with a candidate date.

## 5. The one real external source actually pulled this pass: USGS

`earthquake.usgs.gov`'s FDSNWS event API is genuinely reachable via the agent's
`web_fetch` tool (NOT from inside this sandbox's own network stack — see
`historical/ingestion/base.py`'s docstring for that diagnosis, identical to the
`ephemeris_client.py` situation documented in `docs/ASTRONOMY_VALIDATION_REPORT.md`
Phase 11). A real query for M≥8.3 earthquakes, 1900-2026, returned 31 real events;
16 were kept (a representative subset) and saved verbatim to
`data/raw/usgs_earthquakes_m8.3plus_1900_2026_raw.json`.
`historical/ingestion/usgs.py`'s `parse()`/`normalize()` were then executed for
real against that real file — producing 16 Tier-1, EXACT/EXACT/EXACT-confidence
events, the only events in this pilot dataset with that level of genuine precision.

## 6. Schema constraints — actually tested, not just written

Before any data was loaded, the schema's CHECK constraints and immutability
triggers were exercised directly (inserting deliberately-invalid rows and
confirming rejection; freezing a test version and confirming edits/deletes are
then rejected). This caught one real bug in the schema itself: an early version
required coordinates for `location_confidence = 'CITY'`, which is too strict (CITY
should mean "we know the city," not "we have decimal coordinates") — the first real
ingestion run correctly rejected ~15 legitimate events for exactly this reason,
which is how the bug was found and fixed. See the comment directly above the fixed
CHECK constraint in `historical_events_schema.sql`.

## 7. What was NOT built / NOT executed this pass, and why

- **UCDP, ACLED, GDELT, EM-DAT, NOAA, elections adapters**: interface-only. Each
  one's docstring in `historical/ingestion/` states the specific, diagnosed reason
  (network egress blocked from this sandbox for all of them; ACLED additionally
  requires an API key not available this session; GDELT deprioritized on data-
  quality grounds; elections has no single unified source).
- **A full backtest engine / `backtest_results.db`**: out of scope for "build the
  historical event database" — `get_events()` is the clean handoff point for that
  future work.
- **500-2,000 events**: 136 delivered. See `HISTORICAL_DATA_QUALITY_REPORT.md` for
  the exact, generated-from-the-database breakdown and honest reasoning.

## 8. ASTROWATCH-HIST-002 (quality-improvement pass)

A follow-up pass, in the same session, focused entirely on data quality rather
than new infrastructure. Key additions (all real, all executed):

- `data/verification_updates.py` — 12 events re-checked via actual WebSearch calls
  this pass (not general model knowledge), each with 2 real, independently-fetched
  sources. See `DATASET_FREEZE.md`'s HIST-002 section for the before/after numbers.
- `historical/ingestion/noaa.py` upgraded from interface-only to a real, executed
  adapter (NOAA NGDC significant-tsunami database — genuinely reachable via
  `web_fetch`, unlike this sandbox's own network stack). 6 real Tier-1 tsunami
  events added.
- `historical/deduplication.py` expanded with fuzzy name-similarity, upstream
  source-record-ID matching, date-range overlap, and description-overlap signals.
- `scripts/ingest_historical_data_v2.py` builds `historical_events_v2.db` as a
  **separate file** — `historical_events.db`'s frozen `ASTROWATCH-HIST-001` is
  never opened for writing by this script, confirmed by re-querying its checksum
  after this pass (unchanged).
- `scripts/generate_historical_quality_report.py` extended to report every field
  requested in the follow-up spec (verified/unverified/disputed counts, tier
  breakdown, date/time/location-confidence breakdown, decade/century/period
  buckets) — and a genuine bug was found and fixed via this pass's tests: the
  century-bucketing helper produced "21th century" instead of "21st century"
  before `tests/historical/test_verification_and_reporting.py` caught it.
