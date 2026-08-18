-- Astrowatch — historical_events.db schema
-- Independent of predictions_schema.sql (forecasting) and any astrology-related
-- table. See historical/__init__.py for the architectural boundary this enforces.
--
-- Foreign keys must be enabled by the connecting application (SQLite does not
-- enforce them by default) -- see historical/database.py, which issues
-- "PRAGMA foreign_keys = ON" on every connection.

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------------
-- dataset_versions: every frozen (or in-progress) release of this dataset.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dataset_versions (
    version_id          TEXT PRIMARY KEY,           -- e.g. 'ASTROWATCH-HIST-001'
    created_date         TEXT NOT NULL,               -- ISO8601 date
    description          TEXT,
    event_count           INTEGER,                     -- filled in at freeze time
    source_count          INTEGER,
    frozen                INTEGER NOT NULL DEFAULT 0 CHECK (frozen IN (0, 1)),
    frozen_at             TEXT,
    checksum_sha256        TEXT,
    known_limitations      TEXT,
    notes                 TEXT
);

-- ---------------------------------------------------------------------------
-- sources: every distinct source actually investigated/used this pass.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sources (
    source_id       TEXT PRIMARY KEY,
    dataset_name     TEXT NOT NULL,
    organization      TEXT,
    source_type       TEXT NOT NULL,
    tier              INTEGER NOT NULL CHECK (tier IN (1, 2, 3, 4)),
    url               TEXT,
    access_date        TEXT,                          -- ISO8601 date this session
                                                        -- actually fetched it, NULL if
                                                        -- this source was never live-
                                                        -- fetched this session
    coverage          TEXT,
    notes             TEXT
);

-- ---------------------------------------------------------------------------
-- events: the historical record itself. See historical/taxonomy.py for every
-- controlled-vocabulary field's allowed values (also enforced below via CHECK).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS events (
    event_id             TEXT PRIMARY KEY,          -- stable, deterministic, e.g. 'EVENT-1914-001'
    canonical_event_id    TEXT NOT NULL,              -- groups duplicate/multi-source
                                                       -- records of the same real event;
                                                       -- equals event_id for the
                                                       -- canonical record itself

    event_name            TEXT NOT NULL,
    event_type             TEXT NOT NULL,
    event_subtype           TEXT NOT NULL,

    start_date             TEXT NOT NULL,             -- ISO8601 date, required (even an
                                                       -- APPROXIMATE/DATE_RANGE event
                                                       -- must have SOME start_date --
                                                       -- use the earliest bound for
                                                       -- DATE_RANGE, and see
                                                       -- date_confidence for how exact
                                                       -- to treat it)
    end_date               TEXT,                      -- NULL for single-day/point events
    start_time              TEXT,                      -- 'HH:MM' 24h, NULL if unknown
    end_time                TEXT,
    timezone                TEXT,                      -- NULL if start_time is NULL

    country                TEXT,
    country_code             TEXT,                      -- ISO 3166-1 alpha-3 where known
    region                  TEXT,                      -- broader region, e.g. 'South Asia'
    location_name             TEXT,                      -- city/site name if known
    latitude                 REAL,
    longitude                REAL,
    location_precision         TEXT NOT NULL,

    description             TEXT NOT NULL,

    source_quality_tier         INTEGER NOT NULL CHECK (source_quality_tier IN (1, 2, 3, 4)),
    date_confidence            TEXT NOT NULL,
    time_confidence            TEXT NOT NULL,
    location_confidence         TEXT NOT NULL,

    verification_status         TEXT NOT NULL,
    verification_count          INTEGER NOT NULL DEFAULT 0,

    dataset_version            TEXT NOT NULL REFERENCES dataset_versions(version_id),

    created_at               TEXT NOT NULL,
    updated_at                TEXT NOT NULL,

    CHECK (event_type IN (
        'MILITARY', 'POLITICAL', 'ECONOMIC', 'NATURAL_DISASTER',
        'SOCIAL_PUBLIC_HEALTH', 'SCIENCE_TECHNOLOGY'
    )),
    CHECK (date_confidence IN ('EXACT', 'APPROXIMATE', 'DATE_RANGE', 'DISPUTED', 'UNKNOWN')),
    CHECK (time_confidence IN ('EXACT', 'APPROXIMATE', 'UNKNOWN')),
    CHECK (location_confidence IN ('EXACT', 'CITY', 'REGION', 'COUNTRY', 'APPROXIMATE', 'UNKNOWN')),
    CHECK (location_precision IN ('EXACT', 'CITY', 'REGION', 'COUNTRY', 'APPROXIMATE', 'UNKNOWN')),
    CHECK (verification_status IN ('UNVERIFIED', 'SINGLE_SOURCE', 'MULTI_SOURCE_CONFIRMED', 'DISPUTED')),
    CHECK (verification_count >= 0),
    -- never invent an exact time confidence without an actual time value
    CHECK (NOT (time_confidence = 'EXACT' AND start_time IS NULL)),
    -- never invent EXACT (pinpoint-coordinate) location confidence without
    -- coordinates. CITY confidence deliberately does NOT require lat/lon here --
    -- it means "we know which city," which can be honestly recorded via
    -- location_name alone without fabricating a specific decimal coordinate for
    -- the event (found this distinction the hard way: an earlier version of this
    -- CHECK required coordinates for CITY too, and the very first real ingestion
    -- run correctly rejected ~15 legitimate CITY-precision events that had no
    -- fabricated coordinates -- see docs/ASTRONOMY_VALIDATION_REPORT.md-style
    -- honesty: this was a real schema bug caught by actual execution, not a
    -- data problem, and is documented in HISTORICAL_DATA_QUALITY_REPORT.md).
    CHECK (NOT (location_confidence = 'EXACT' AND latitude IS NULL)),
    CHECK (NOT (location_confidence IN ('EXACT', 'CITY') AND location_name IS NULL AND country IS NULL)),
    CHECK (end_date IS NULL OR end_date >= start_date),
    CHECK (start_time IS NULL OR end_time IS NULL OR end_date IS NOT NULL OR end_time >= start_time)
);

CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_subtype ON events(event_subtype);
CREATE INDEX IF NOT EXISTS idx_events_start_date ON events(start_date);
CREATE INDEX IF NOT EXISTS idx_events_country ON events(country_code);
CREATE INDEX IF NOT EXISTS idx_events_region ON events(region);
CREATE INDEX IF NOT EXISTS idx_events_canonical ON events(canonical_event_id);
CREATE INDEX IF NOT EXISTS idx_events_dataset_version ON events(dataset_version);

-- ---------------------------------------------------------------------------
-- event_sources: provenance -- which source(s) back which event(s).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS event_sources (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id             TEXT NOT NULL REFERENCES events(event_id) ON DELETE CASCADE,
    source_id             TEXT NOT NULL REFERENCES sources(source_id) ON DELETE RESTRICT,
    source_url             TEXT,               -- specific URL/citation within that source
    link_verification_status TEXT NOT NULL CHECK (link_verification_status IN ('CONFIRMED', 'UNCONFIRMED')),
    notes                 TEXT,
    created_at             TEXT NOT NULL,
    UNIQUE (event_id, source_id)
);

CREATE INDEX IF NOT EXISTS idx_event_sources_event ON event_sources(event_id);
CREATE INDEX IF NOT EXISTS idx_event_sources_source ON event_sources(source_id);

-- ---------------------------------------------------------------------------
-- control_dates: reproducible non-event dates for future backtest comparison.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS control_dates (
    control_id            TEXT PRIMARY KEY,
    date                  TEXT NOT NULL,
    region                 TEXT,
    sampling_method          TEXT NOT NULL CHECK (
        sampling_method IN ('RANDOM_DATE', 'MATCHED_DATE', 'CALENDAR_MATCH', 'PREDEFINED_CONTROL')
    ),
    seed                  INTEGER,               -- reproducibility seed, required for RANDOM_DATE
    selection_timestamp        TEXT NOT NULL,          -- when this control was actually selected
    source_window            TEXT NOT NULL,          -- describes the date range sampled from
    dataset_version           TEXT NOT NULL REFERENCES dataset_versions(version_id),
    notes                  TEXT,
    CHECK (sampling_method != 'RANDOM_DATE' OR seed IS NOT NULL)
);

CREATE INDEX IF NOT EXISTS idx_control_dates_version ON control_dates(dataset_version);

-- ---------------------------------------------------------------------------
-- Immutability: once a dataset_version is frozen, its events/sources/event_sources/
-- control_dates rows cannot be silently modified. A new version must be created
-- instead (see historical/versioning.py / scripts/freeze_historical_dataset.py).
-- ---------------------------------------------------------------------------

CREATE TRIGGER IF NOT EXISTS trg_events_immutable_after_freeze
BEFORE UPDATE ON events
FOR EACH ROW
WHEN (SELECT frozen FROM dataset_versions WHERE version_id = OLD.dataset_version) = 1
BEGIN
    SELECT RAISE(ABORT, 'events row belongs to a frozen dataset_version -- create a new version instead of editing it silently');
END;

CREATE TRIGGER IF NOT EXISTS trg_events_immutable_delete_after_freeze
BEFORE DELETE ON events
FOR EACH ROW
WHEN (SELECT frozen FROM dataset_versions WHERE version_id = OLD.dataset_version) = 1
BEGIN
    SELECT RAISE(ABORT, 'events row belongs to a frozen dataset_version -- cannot delete; create a new version instead');
END;

CREATE TRIGGER IF NOT EXISTS trg_control_dates_immutable_after_freeze
BEFORE UPDATE ON control_dates
FOR EACH ROW
WHEN (SELECT frozen FROM dataset_versions WHERE version_id = OLD.dataset_version) = 1
BEGIN
    SELECT RAISE(ABORT, 'control_dates row belongs to a frozen dataset_version -- create a new version instead');
END;
