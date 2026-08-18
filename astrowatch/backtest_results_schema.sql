-- Astrowatch — backtest_results.db schema
-- =========================================
-- Completely separate database from historical_events.db / historical_events_v2.db /
-- astronomy.db / panchang.db. This file is written to ONLY by the backtest engine.
-- Nothing in astrowatch/backtest/*.py ever opens historical_events_v2.db for writing --
-- see backtest/repository.py, which only ever calls historical.database.connect() in
-- read-only usage patterns (SELECT-only, never INSERT/UPDATE/DELETE against that file).

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------------
-- experiments: one immutable row per backtest run (e.g. ASTROWATCH-BT-001).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS experiments (
    experiment_id           TEXT PRIMARY KEY,           -- 'ASTROWATCH-BT-001'
    dataset_version          TEXT NOT NULL,               -- 'ASTROWATCH-HIST-002'
    dataset_db_path           TEXT NOT NULL,
    dataset_checksum_before     TEXT NOT NULL,
    dataset_checksum_after      TEXT,
    dataset_integrity          TEXT CHECK (dataset_integrity IN ('UNCHANGED', 'CHANGED', NULL)),
    rule_registry_version       TEXT NOT NULL,               -- hash, see reproducibility.py
    astronomy_version          TEXT NOT NULL,               -- hash, see reproducibility.py
    astrowatch_version         TEXT NOT NULL,               -- forecast.ASTROWATCH_VERSION
    random_seed               INTEGER NOT NULL,
    sampling_method            TEXT NOT NULL,
    test_window_start          TEXT,
    test_window_end            TEXT,
    control_method             TEXT NOT NULL,
    region_used                TEXT NOT NULL DEFAULT 'GLOBAL',
    allow_ayanamsha_fallback    INTEGER NOT NULL CHECK (allow_ayanamsha_fallback IN (0, 1)),
    configuration_hash          TEXT NOT NULL,               -- hash of the full config dict
    created_at                TEXT NOT NULL,
    completed_at               TEXT,
    status                   TEXT NOT NULL DEFAULT 'RUNNING'
                              CHECK (status IN ('RUNNING', 'COMPLETED', 'FAILED', 'ABORTED')),
    frozen                   INTEGER NOT NULL DEFAULT 0 CHECK (frozen IN (0, 1)),
    frozen_at                 TEXT,
    notes                    TEXT
);

-- ---------------------------------------------------------------------------
-- test_cases: one row per sampled unit (event-derived or control-derived) that
-- was actually run through the blind predictor.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS test_cases (
    test_case_id            TEXT PRIMARY KEY,
    experiment_id            TEXT NOT NULL REFERENCES experiments(experiment_id),
    case_kind               TEXT NOT NULL CHECK (case_kind IN ('EVENT', 'CONTROL')),
    source_event_id           TEXT,                        -- events.event_id, NULL for CONTROL
    source_control_id          TEXT,                        -- control_dates.control_id, NULL for EVENT
    test_date               TEXT NOT NULL,
    time_precision_mode        TEXT NOT NULL CHECK (time_precision_mode IN ('MODE_A_EXACT_TIME', 'MODE_B_DATE_ONLY', 'MODE_C_TIME_WINDOW')),
    input_time              TEXT,                        -- HH:MM if legitimately known (Mode A/C center), else NULL
    input_timezone            TEXT,
    input_location_precision    TEXT,                        -- from location_confidence, CONTROL = 'UNKNOWN'
    sample_hours_utc           TEXT,                        -- JSON list of UTC hours actually sampled
    generated_at              TEXT NOT NULL,
    UNIQUE (experiment_id, source_event_id),
    UNIQUE (experiment_id, source_control_id)
);
CREATE INDEX IF NOT EXISTS idx_test_cases_experiment ON test_cases(experiment_id);
CREATE INDEX IF NOT EXISTS idx_test_cases_kind ON test_cases(case_kind);

-- ---------------------------------------------------------------------------
-- predictions: exactly what Astrowatch predicted for a test case, generated
-- BEFORE the actual_events row for the same test case is ever read by any
-- scoring code. Contains no historical-event fields whatsoever.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS predictions (
    prediction_id            TEXT PRIMARY KEY,
    experiment_id             TEXT NOT NULL REFERENCES experiments(experiment_id),
    test_case_id              TEXT NOT NULL REFERENCES test_cases(test_case_id),
    predicted_at               TEXT NOT NULL,
    predicted_fired             INTEGER NOT NULL CHECK (predicted_fired IN (0, 1)),
    predicted_categories         TEXT NOT NULL,             -- JSON list, e.g. ["MILITARY"]
    predicted_subtypes          TEXT NOT NULL DEFAULT '[]',  -- JSON list (always empty -- registry has no subtype-level rules; see KNOWN_LIMITATIONS)
    rule_matches               TEXT NOT NULL,             -- JSON list of rule_ids that fired
    confidence_score            REAL,                       -- NULL if not meaningfully computable
    astronomical_inputs_jd_ut     TEXT NOT NULL,             -- JSON list of JD(UT) values actually used
    ayanamsha_source            TEXT NOT NULL,             -- 'live_swisseph' | 'linear_fallback', per sample
    ephemeris_precision_flag      TEXT NOT NULL,             -- from ephemeris_source.py, e.g. 'SWIEPH' | 'MOSEPH'
    panchang_snapshot            TEXT,                       -- JSON, union across samples
    rashi_nakshatra_snapshot       TEXT,                       -- JSON, union across samples
    raw_rule_evaluations          TEXT NOT NULL,             -- JSON, full evaluate_rules() output, all samples
    astronomy_extrapolated_unvalidated INTEGER NOT NULL DEFAULT 0 CHECK (astronomy_extrapolated_unvalidated IN (0,1)),
    UNIQUE (experiment_id, test_case_id)
);
CREATE INDEX IF NOT EXISTS idx_predictions_experiment ON predictions(experiment_id);

-- ---------------------------------------------------------------------------
-- actual_events: revealed ONLY after prediction. What actually happened
-- (or, for CONTROL cases, the documented absence of a dataset event).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS actual_events (
    test_case_id             TEXT PRIMARY KEY REFERENCES test_cases(test_case_id),
    experiment_id             TEXT NOT NULL REFERENCES experiments(experiment_id),
    revealed_at               TEXT NOT NULL,
    actual_kind               TEXT NOT NULL CHECK (actual_kind IN ('EVENT', 'PRESUMED_NO_EVENT')),
    actual_event_id             TEXT,                       -- events.event_id, NULL for controls
    actual_category             TEXT,                       -- NULL for controls
    actual_subtype              TEXT,
    actual_event_name            TEXT
);
CREATE INDEX IF NOT EXISTS idx_actual_events_experiment ON actual_events(experiment_id);

-- ---------------------------------------------------------------------------
-- prediction_matches: per (test_case, category) scoring unit -- TP/FP/TN/FN.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS prediction_matches (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    experiment_id            TEXT NOT NULL REFERENCES experiments(experiment_id),
    test_case_id             TEXT NOT NULL REFERENCES test_cases(test_case_id),
    category                TEXT NOT NULL,               -- 'ANY' for the binary/global row, else one of the 6 categories
    predicted_positive          INTEGER NOT NULL CHECK (predicted_positive IN (0, 1)),
    actual_positive            INTEGER NOT NULL CHECK (actual_positive IN (0, 1)),
    outcome                 TEXT NOT NULL CHECK (outcome IN ('TP', 'FP', 'TN', 'FN')),
    UNIQUE (experiment_id, test_case_id, category)
);
CREATE INDEX IF NOT EXISTS idx_prediction_matches_experiment ON prediction_matches(experiment_id);
CREATE INDEX IF NOT EXISTS idx_prediction_matches_category ON prediction_matches(category);

-- ---------------------------------------------------------------------------
-- control_results: aggregate fire-rate comparison, event-dates vs control-dates.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS control_results (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    experiment_id           TEXT NOT NULL REFERENCES experiments(experiment_id),
    category               TEXT NOT NULL,                -- 'ANY' or one of the 6 categories
    event_case_count          INTEGER NOT NULL,
    event_fired_count          INTEGER NOT NULL,
    event_fire_rate           REAL NOT NULL,
    control_case_count         INTEGER NOT NULL,
    control_fired_count         INTEGER NOT NULL,
    control_fire_rate          REAL NOT NULL,
    rate_difference           REAL NOT NULL,
    permutation_p_value         REAL,
    permutation_iterations       INTEGER,
    UNIQUE (experiment_id, category)
);

-- ---------------------------------------------------------------------------
-- baseline_results: random / historical-frequency / control-date baselines,
-- scored with the identical metric set as the real predictor.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS baseline_results (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    experiment_id           TEXT NOT NULL REFERENCES experiments(experiment_id),
    baseline_name            TEXT NOT NULL CHECK (baseline_name IN ('RANDOM', 'HISTORICAL_FREQUENCY', 'CONTROL_DATE')),
    category                TEXT NOT NULL,
    tp                    INTEGER NOT NULL,
    fp                    INTEGER NOT NULL,
    tn                    INTEGER NOT NULL,
    fn                    INTEGER NOT NULL,
    precision               REAL,
    recall                 REAL,
    f1                    REAL,
    accuracy                REAL,
    specificity              REAL,
    false_positive_rate        REAL,
    sample_flag              TEXT NOT NULL DEFAULT 'OK' CHECK (sample_flag IN ('OK', 'INSUFFICIENT_SAMPLE')),
    UNIQUE (experiment_id, baseline_name, category)
);

-- ---------------------------------------------------------------------------
-- metrics: the real (non-baseline) Astrowatch predictor's own scores, at
-- 'ANY' (global binary) level, per-category, and per-subtype.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS metrics (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    experiment_id           TEXT NOT NULL REFERENCES experiments(experiment_id),
    metric_level             TEXT NOT NULL CHECK (metric_level IN ('GLOBAL', 'CATEGORY', 'SUBTYPE')),
    category                TEXT,                        -- NULL for GLOBAL
    subtype                 TEXT,                        -- NULL unless metric_level = 'SUBTYPE'
    sample_size              INTEGER NOT NULL,
    tp                    INTEGER NOT NULL,
    fp                    INTEGER NOT NULL,
    tn                    INTEGER NOT NULL,
    fn                    INTEGER NOT NULL,
    precision               REAL,
    recall                 REAL,
    f1                    REAL,
    accuracy                REAL,
    specificity              REAL,
    false_positive_rate        REAL,
    wilson_ci_low_accuracy       REAL,
    wilson_ci_high_accuracy      REAL,
    sample_flag              TEXT NOT NULL DEFAULT 'OK' CHECK (sample_flag IN ('OK', 'INSUFFICIENT_SAMPLE')),
    notes                  TEXT,
    UNIQUE (experiment_id, metric_level, category, subtype)
);

-- ---------------------------------------------------------------------------
-- calibration_bins: confidence-score calibration, if confidence scores are
-- meaningfully produced (see KNOWN_LIMITATIONS if not).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS calibration_bins (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    experiment_id           TEXT NOT NULL REFERENCES experiments(experiment_id),
    bin_label               TEXT NOT NULL,
    predicted_confidence_mid    REAL,
    case_count              INTEGER NOT NULL,
    actual_success_rate        REAL
);

-- ---------------------------------------------------------------------------
-- audit_tests: results of the blindness / leakage / determinism self-tests,
-- stored alongside the experiment they were run against.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_tests (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    experiment_id           TEXT NOT NULL REFERENCES experiments(experiment_id),
    test_name               TEXT NOT NULL,
    result                 TEXT NOT NULL CHECK (result IN ('PASS', 'FAIL')),
    detail                 TEXT,
    run_at                 TEXT NOT NULL,
    UNIQUE (experiment_id, test_name)
);

-- ---------------------------------------------------------------------------
-- Immutability: once experiments.frozen = 1, reject further writes to that
-- experiment's rows anywhere in this database. Mirrors the pattern used by
-- historical_events_schema.sql's trg_events_immutable_after_freeze.
-- ---------------------------------------------------------------------------
CREATE TRIGGER IF NOT EXISTS trg_experiments_immutable_after_freeze
BEFORE UPDATE ON experiments
WHEN OLD.frozen = 1 AND NEW.frozen = 1
BEGIN
    SELECT RAISE(ABORT, 'experiment is frozen -- create a new experiment_id instead of editing this one');
END;

CREATE TRIGGER IF NOT EXISTS trg_experiments_no_unfreeze
BEFORE UPDATE ON experiments
WHEN OLD.frozen = 1 AND NEW.frozen = 0
BEGIN
    SELECT RAISE(ABORT, 'cannot unfreeze an experiment');
END;
