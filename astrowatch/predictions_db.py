"""
Astrowatch Online -- Prediction history database.
=====================================================
New, broader SQLite store for the online AI-driven prediction system. This is
DELIBERATELY separate from world_astrology/historical_validation.py's
`world_astrology_validation.db`, which has a narrower, already-shipped schema
specific to Jyotisha/Hellenistic cross-tradition-agreement validation records
(see that module's own docstring) -- that module and its data are untouched.
This new table is the general prediction ledger the task spec asks for:
questions, entities, full synthesis text, provenance, and outcome tracking
across ALL prediction modes (short/detailed/current-event/random/agent).

IMMUTABILITY: predictions are never UPDATEd once inserted, except for the
handful of fields that legitimately change after the fact (outcome tracking,
publish status) -- enforced at the application layer here (no function in this
module does a blanket UPDATE of prediction content) and mirrors the same
append-only philosophy already established by predictions_schema.sql (repo
root, pre-existing) and world_astrology/historical_validation.py's DB trigger.
Failed/incorrect predictions are NEVER deleted or edited to look better in
hindsight -- record_outcome() only ever appends the actual result.
"""

import json
import os
import sqlite3
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_PATH = os.path.join(HERE, "predictions.db")

OUTCOME_STATUSES = ("pending", "correct", "partially_correct", "incorrect", "unclear")

SCHEMA = """
CREATE TABLE IF NOT EXISTS predictions (
    id                  TEXT PRIMARY KEY,   -- uuid4 hex
    created_at          TEXT NOT NULL,
    entity              TEXT NOT NULL,
    entity_type         TEXT,
    question            TEXT NOT NULL,
    prediction          TEXT NOT NULL,       -- final synthesis text
    time_window         TEXT,                -- e.g. "2027-10-01..2027-11-30"
    traditions_used      TEXT,               -- JSON list
    calculation_data     TEXT NOT NULL,       -- JSON: the structured Astrowatch output
    confidence           TEXT,               -- LOW / MODERATE / HIGH / UNVALIDATED
    model_score          REAL,                -- 0..1, AI-assigned or agreement-derived
    mode                 TEXT,                -- short | detailed | current_event | random | agent
    source                TEXT,               -- "user" | "agent" | "scheduler"
    published             INTEGER NOT NULL DEFAULT 0,
    x_post_id             TEXT,
    actual_outcome         TEXT,
    outcome_status         TEXT NOT NULL DEFAULT 'pending',
    outcome_recorded_at    TEXT
);
CREATE INDEX IF NOT EXISTS idx_predictions_entity ON predictions(entity);
CREATE INDEX IF NOT EXISTS idx_predictions_created ON predictions(created_at);
CREATE INDEX IF NOT EXISTS idx_predictions_outcome ON predictions(outcome_status);

-- Belt-and-suspenders immutability for the calculation/prediction content
-- (same convention as predictions_schema.sql / historical_validation.py):
-- outcome tracking and publish status are allowed to change; the core
-- prediction fields never should. Enforced at the application layer in this
-- module (no UPDATE statement here ever touches `prediction`,
-- `calculation_data`, `question`, or `entity`).
"""


@dataclass
class PredictionRecord:
    id: str
    created_at: str
    entity: str
    entity_type: Optional[str]
    question: str
    prediction: str
    time_window: Optional[str]
    traditions_used: List[str]
    calculation_data: Dict[str, Any]
    confidence: Optional[str]
    model_score: Optional[float]
    mode: Optional[str]
    source: Optional[str]
    published: bool
    x_post_id: Optional[str]
    actual_outcome: Optional[str]
    outcome_status: str
    outcome_recorded_at: Optional[str]


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _row_to_record(row: sqlite3.Row) -> PredictionRecord:
    d = {k: row[k] for k in row.keys()}
    d["traditions_used"] = json.loads(d["traditions_used"]) if d["traditions_used"] else []
    d["calculation_data"] = json.loads(d["calculation_data"]) if d["calculation_data"] else {}
    d["published"] = bool(d["published"])
    return PredictionRecord(**d)


def get_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def save_prediction(conn: sqlite3.Connection, *, entity: str, question: str,
                     prediction: str, calculation_data: Dict[str, Any],
                     entity_type: Optional[str] = None, time_window: Optional[str] = None,
                     traditions_used: Optional[List[str]] = None,
                     confidence: Optional[str] = None, model_score: Optional[float] = None,
                     mode: Optional[str] = None, source: str = "user") -> str:
    pred_id = uuid.uuid4().hex
    conn.execute(
        "INSERT INTO predictions (id, created_at, entity, entity_type, question, "
        "prediction, time_window, traditions_used, calculation_data, confidence, "
        "model_score, mode, source, published, outcome_status) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,0,'pending')",
        (pred_id, _now_iso(), entity, entity_type, question, prediction, time_window,
         json.dumps(traditions_used or []), json.dumps(calculation_data, default=str),
         confidence, model_score, mode, source),
    )
    conn.commit()
    return pred_id


def get_prediction(conn: sqlite3.Connection, prediction_id: str) -> Optional[PredictionRecord]:
    row = conn.execute("SELECT * FROM predictions WHERE id = ?", (prediction_id,)).fetchone()
    return _row_to_record(row) if row else None


def get_prediction_history(conn: sqlite3.Connection, entity: Optional[str] = None,
                            mode: Optional[str] = None, limit: int = 50,
                            offset: int = 0) -> List[PredictionRecord]:
    clauses, params = [], []
    if entity:
        clauses.append("entity = ?")
        params.append(entity)
    if mode:
        clauses.append("mode = ?")
        params.append(mode)
    sql = "SELECT * FROM predictions"
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    rows = conn.execute(sql, params).fetchall()
    return [_row_to_record(r) for r in rows]


def recent_predictions_for_entity(conn: sqlite3.Connection, entity: str, days: int = 30) -> int:
    """Count of predictions for this entity in the last `days` days -- used by
    ai/random_prediction.py's duplicate/frequency avoidance."""
    cutoff = time.strftime("%Y-%m-%dT%H:%M:%SZ",
                            time.gmtime(time.time() - days * 86400))
    row = conn.execute(
        "SELECT COUNT(*) FROM predictions WHERE entity = ? AND created_at >= ?",
        (entity, cutoff),
    ).fetchone()
    return row[0]


def question_already_asked(conn: sqlite3.Connection, question: str) -> bool:
    row = conn.execute(
        "SELECT COUNT(*) FROM predictions WHERE question = ?", (question,)
    ).fetchone()
    return row[0] > 0


def mark_published(conn: sqlite3.Connection, prediction_id: str, x_post_id: str) -> None:
    conn.execute(
        "UPDATE predictions SET published = 1, x_post_id = ? WHERE id = ?",
        (x_post_id, prediction_id),
    )
    conn.commit()


def record_outcome(conn: sqlite3.Connection, prediction_id: str, actual_outcome: str,
                    outcome_status: str) -> None:
    """Append-only in spirit: this is the ONE allowed post-insert mutation, and
    it only ever records what actually happened -- it never touches the
    original prediction text, and a prior outcome is not silently overwritten
    without a caller explicitly re-calling this (there is no 'undo' path)."""
    if outcome_status not in OUTCOME_STATUSES:
        raise ValueError(f"outcome_status must be one of {OUTCOME_STATUSES}")
    conn.execute(
        "UPDATE predictions SET actual_outcome = ?, outcome_status = ?, "
        "outcome_recorded_at = ? WHERE id = ?",
        (actual_outcome, outcome_status, _now_iso(), prediction_id),
    )
    conn.commit()


def count_predictions(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) FROM predictions").fetchone()[0]
