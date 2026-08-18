"""
Astrowatch World Astrology -- Historical backtesting scaffold.
===================================================================
A NEW, separate SQLite store (world_astrology_backtest.db) for recording
individual tradition-engine predictions against real, later-known outcomes,
so that this project can eventually measure per-tradition/technique/rule
performance rather than merely asserting it.

Deliberately kept SEPARATE from the older backtest_results.db / experiments
schema (backtest_results_schema.sql), which backtests the ORIGINAL
mundane-astrology rule-detector system (forecast.evaluate_rules) against
historical_events.db -- that system is untouched by this module. This is the
new-engines' (world_astrology/engines/*.py) own backtest ledger.

STATUS: SCAFFOLD ONLY. This module ships with an EMPTY table. No historical
test records are seeded here or anywhere else in this session -- inventing
"this tradition was right 73% of the time" data would be exactly the kind of
fabrication the whole task explicitly forbids. Real backtest records can only
be added by actually running a tradition engine's prediction against a
verified historical case and recording the real, later-confirmed outcome.

Outcome values (documented, no invented category): 'correct', 'partial',
'incorrect', 'unclear' -- 'unclear' exists specifically so ambiguous/
uninterpretable real-world outcomes are recorded honestly rather than forced
into correct/incorrect.

Performance aggregation NEVER reports a percentage/accuracy figure for a
sample smaller than MIN_SAMPLE_SIZE_FOR_RATE -- below that threshold it
reports the raw counts only and an explicit "insufficient_sample_size" flag,
per the project-wide rule against inventing numerical confidence from too
little data.
"""

import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "world_astrology_backtest.db")

MIN_SAMPLE_SIZE_FOR_RATE = 5  # below this, report counts only -- no rate/percentage claimed

SCHEMA = """
CREATE TABLE IF NOT EXISTS historical_prediction_tests (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at          TEXT NOT NULL,
    tradition           TEXT NOT NULL,
    rule_id             TEXT,
    entity_name         TEXT NOT NULL,
    entity_type         TEXT NOT NULL,
    prediction_domain   TEXT,
    prediction_text     TEXT NOT NULL,
    prediction_date     TEXT NOT NULL,     -- date the prediction was FOR
    time_window_start   TEXT,
    time_window_end     TEXT,
    location            TEXT,
    actual_event        TEXT NOT NULL,     -- description of what actually happened, sourced
    actual_event_source TEXT,              -- citation for the actual outcome
    outcome             TEXT NOT NULL CHECK (outcome IN ('correct', 'partial', 'incorrect', 'unclear')),
    evaluated_by        TEXT,
    evaluated_at        TEXT,
    notes               TEXT
);
CREATE INDEX IF NOT EXISTS idx_hpt_tradition ON historical_prediction_tests(tradition);
CREATE INDEX IF NOT EXISTS idx_hpt_rule ON historical_prediction_tests(rule_id);
CREATE INDEX IF NOT EXISTS idx_hpt_domain ON historical_prediction_tests(prediction_domain);
"""


def _connect(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


@dataclass
class HistoricalPredictionTest:
    tradition: str
    entity_name: str
    entity_type: str
    prediction_text: str
    prediction_date: str
    actual_event: str
    outcome: str  # 'correct' | 'partial' | 'incorrect' | 'unclear'
    rule_id: Optional[str] = None
    prediction_domain: Optional[str] = None
    time_window_start: Optional[str] = None
    time_window_end: Optional[str] = None
    location: Optional[str] = None
    actual_event_source: Optional[str] = None
    evaluated_by: Optional[str] = None
    notes: Optional[str] = None


def record_test(test: HistoricalPredictionTest, db_path: str = DB_PATH) -> int:
    if test.outcome not in ("correct", "partial", "incorrect", "unclear"):
        raise ValueError(f"Invalid outcome '{test.outcome}' -- must be one of "
                        f"correct/partial/incorrect/unclear.")
    conn = _connect(db_path)
    try:
        now = datetime.now(timezone.utc).isoformat()
        cur = conn.execute(
            """INSERT INTO historical_prediction_tests
               (created_at, tradition, rule_id, entity_name, entity_type, prediction_domain,
                prediction_text, prediction_date, time_window_start, time_window_end, location,
                actual_event, actual_event_source, outcome, evaluated_by, evaluated_at, notes)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (now, test.tradition, test.rule_id, test.entity_name, test.entity_type,
             test.prediction_domain, test.prediction_text, test.prediction_date,
             test.time_window_start, test.time_window_end, test.location,
             test.actual_event, test.actual_event_source, test.outcome,
             test.evaluated_by, now, test.notes),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def _performance_row(rows: List[sqlite3.Row]) -> Dict[str, Any]:
    n = len(rows)
    counts = {"correct": 0, "partial": 0, "incorrect": 0, "unclear": 0}
    for r in rows:
        counts[r["outcome"]] += 1
    result = {"sample_size": n, "counts": counts}
    if n < MIN_SAMPLE_SIZE_FOR_RATE:
        result["rate"] = "insufficient_sample_size"
        result["note"] = (f"Sample size {n} is below the minimum ({MIN_SAMPLE_SIZE_FOR_RATE}) "
                          f"this project reports a rate for -- raw counts only.")
    else:
        result["correct_rate"] = round(counts["correct"] / n, 3)
        result["correct_or_partial_rate"] = round((counts["correct"] + counts["partial"]) / n, 3)
    return result


def performance_by(dimension: str, db_path: str = DB_PATH) -> Dict[str, Any]:
    """dimension: one of 'tradition', 'rule_id', 'prediction_domain'. Aggregates
    raw historical_prediction_tests rows -- returns {} if the table is empty
    (the honest, expected state until real backtest data is entered)."""
    if dimension not in ("tradition", "rule_id", "prediction_domain"):
        raise ValueError("dimension must be 'tradition', 'rule_id', or 'prediction_domain'")
    conn = _connect(db_path)
    try:
        rows = conn.execute(f"SELECT * FROM historical_prediction_tests").fetchall()
    finally:
        conn.close()
    grouped: Dict[str, List[sqlite3.Row]] = {}
    for r in rows:
        key = r[dimension] or "(unspecified)"
        grouped.setdefault(key, []).append(r)
    return {key: _performance_row(group_rows) for key, group_rows in grouped.items()}


def performance_by_time_horizon(db_path: str = DB_PATH) -> Dict[str, Any]:
    """Buckets by (time_window_end - prediction_date) in days, coarse-bucketed
    into short (<=30d) / medium (<=180d) / long (>180d) / unspecified."""
    from datetime import date as _date

    def bucket(row: sqlite3.Row) -> str:
        if not row["time_window_end"]:
            return "unspecified"
        try:
            start = _date.fromisoformat(row["prediction_date"])
            end = _date.fromisoformat(row["time_window_end"])
            days = (end - start).days
        except (ValueError, TypeError):
            return "unspecified"
        if days <= 30:
            return "short (<=30d)"
        if days <= 180:
            return "medium (<=180d)"
        return "long (>180d)"

    conn = _connect(db_path)
    try:
        rows = conn.execute("SELECT * FROM historical_prediction_tests").fetchall()
    finally:
        conn.close()
    grouped: Dict[str, List[sqlite3.Row]] = {}
    for r in rows:
        grouped.setdefault(bucket(r), []).append(r)
    return {key: _performance_row(group_rows) for key, group_rows in grouped.items()}
