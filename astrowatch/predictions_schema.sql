-- Astrowatch — predictions database schema
-- ==========================================
-- STATUS: written this pass, NOT executed (no sqlite3/Python execution available this
-- session -- see VALIDATION_REPORT.md). Run via:
--     sqlite3 predictions.db < predictions_schema.sql
-- once an environment is available.
--
-- IMMUTABILITY (item 7): the `predictions` table has no UPDATE path in the application
-- layer (forecast.py never issues UPDATE against it) -- corrections must go into
-- `prediction_revisions`, which references the original by prediction_id and never
-- overwrites it. This is an application-level convention; the schema also adds a
-- trigger below that rejects UPDATEs at the database level as a second layer of
-- enforcement, not just a promise in application code.

CREATE TABLE IF NOT EXISTS predictions (
    prediction_id           TEXT PRIMARY KEY,
    created_at              TEXT NOT NULL,   -- ISO 8601 UTC, set BEFORE forecast window begins
    forecast_start          TEXT NOT NULL,
    forecast_end            TEXT NOT NULL,
    region                  TEXT NOT NULL,   -- e.g. "GLOBAL", "USA" -- see geographic_specificity
    country                 TEXT,
    domain                  TEXT NOT NULL,   -- POLITICAL / MILITARY / ECONOMIC / SOCIAL / ENVIRONMENTAL / TECHNOLOGY / GENERAL
    configuration_json      TEXT NOT NULL,   -- raw detected configuration (aspects/grahayuddha), JSON
    planetary_positions_json TEXT NOT NULL,  -- tropical + sidereal longitudes, JSON
    panchang_json           TEXT,            -- partial panchang (tithi/vara/nakshatra), JSON, nullable
    rule_id                 TEXT,            -- NULL if no rule fired (NO FORECAST)
    source                  TEXT,            -- "<author>, Ch. <chapter>, <citation>"
    traditional_interpretation TEXT,
    historical_sample_size  INTEGER NOT NULL DEFAULT 0,
    historical_matches      INTEGER NOT NULL DEFAULT 0,
    historical_misses       INTEGER NOT NULL DEFAULT 0,
    baseline                TEXT,
    evidence_level          TEXT NOT NULL,   -- LIMITED / MODERATE / STRONG / UNVALIDATED
    confidence              TEXT NOT NULL,   -- LOW / MODERATE / HIGH / UNVALIDATED
    prediction_text         TEXT NOT NULL,
    status                  TEXT NOT NULL DEFAULT 'EXPERIMENTAL',
    validation_status       TEXT NOT NULL DEFAULT 'UNVALIDATED',  -- UNVALIDATED / PARTIALLY_VALIDATED / VALIDATED
    temporal_precision      TEXT NOT NULL,
    geographic_specificity  TEXT NOT NULL DEFAULT 'NONE'
);

CREATE TABLE IF NOT EXISTS prediction_revisions (
    revision_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    prediction_id    TEXT NOT NULL REFERENCES predictions(prediction_id),
    revised_at       TEXT NOT NULL,
    reason           TEXT NOT NULL,
    revised_fields_json TEXT NOT NULL   -- {"field": "new_value", ...}, original row untouched
);

CREATE TABLE IF NOT EXISTS forecast_evaluations (
    evaluation_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    prediction_id    TEXT NOT NULL REFERENCES predictions(prediction_id),
    evaluated_at     TEXT NOT NULL,
    actual_event_description TEXT,
    classification   TEXT NOT NULL   -- CORRECT / PARTIAL / MISS / NO-EVENT / UNRESOLVED
);

-- Second-layer immutability enforcement (belt-and-suspenders on top of the application
-- layer never issuing UPDATE): reject any UPDATE against predictions outright.
CREATE TRIGGER IF NOT EXISTS predictions_immutable
BEFORE UPDATE ON predictions
BEGIN
    SELECT RAISE(ABORT, 'predictions rows are immutable -- insert a prediction_revisions row instead');
END;
