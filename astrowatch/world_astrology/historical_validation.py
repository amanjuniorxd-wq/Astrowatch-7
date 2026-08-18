"""
Astrowatch World Astrology -- historical validation store.

SCOPE OF THIS MODULE, STATED UP FRONT: this is a SCHEMA AND STORAGE LAYER only.
It does not run a backtest experiment, and it does not claim any accuracy
number for the reading engine -- see historical_events.db / backtest/ for this
project's actual, already-executed backtest experiment (ASTROWATCH-BT-001),
which is a separate, much larger, pre-registered piece of work this module
deliberately does not duplicate or reopen.

What this module IS for: giving the reading engine (reading_engine.py) a real
place to record (a) exactly what it predicted, frozen at prediction time, and
(b) whatever real-world outcome is later found for that same entity/period,
recorded independently and separately, so nothing about a past prediction can
be quietly edited to look better in hindsight. This mirrors backtest/database.py's
predict-now/reveal-later separation (predictions vs. actual_events tables) at a
much smaller scale appropriate to one-off world-astrology readings rather than a
full sampled experiment.

IMMUTABILITY RULES (enforced in code, not just by convention):
  - record_prediction() INSERTs a validation_records row and returns its id.
    There is no update_prediction() function anywhere in this module. Once
    written, a prediction's content cannot be changed through this API.
  - record_outcome() INSERTs an outcome_records row (append-only, 1-to-many
    with validation_records). There is no update_outcome() either -- if new
    information changes the outcome assessment, record a NEW outcome_records
    row with a later revealed_at; the old row stays, so the full history of
    what was believed and when remains visible.
  - assess_match() computes (and only ever computes, never edits) whether a
    given outcome matches its prediction's valence; it writes its result onto
    the outcome_records row at insert time, not retroactively onto old rows.

This is intentionally a thin, sqlite3-direct module (no ORM), consistent with
historical/repository.py's own stated convention of keeping raw SQL in one
place per subsystem.
"""
import os
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_PATH = os.path.join(HERE, "world_astrology_validation.db")

VALID_VALENCES = {"favorable", "unfavorable", "neutral", "insufficient"}
VALID_OUTCOME_VALENCES = {"favorable", "unfavorable", "neutral", "mixed", "unclear"}
VALID_MATCH_ASSESSMENTS = {"MATCH", "MISMATCH", "AMBIGUOUS", "NOT_YET_ASSESSED"}

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS validation_records (
    validation_id           TEXT PRIMARY KEY,
    reading_mode             TEXT NOT NULL,   -- 'short' | 'detailed' | 'world'
    entity_name               TEXT NOT NULL,
    entity_type                TEXT NOT NULL,
    as_of_date                  TEXT NOT NULL,
    predicted_at                 TEXT NOT NULL,  -- real wall-clock ISO timestamp
    dominant_lord                 TEXT NOT NULL,
    jyotisha_dignity                TEXT,
    jyotisha_score                   REAL,
    hellenistic_dignity               TEXT,
    hellenistic_score                  REAL,
    agreement_classification            TEXT NOT NULL,
    agreement_reasoning                  TEXT NOT NULL,
    predicted_valence                     TEXT NOT NULL,  -- see VALID_VALENCES
    reading_text                           TEXT NOT NULL,  -- frozen verbatim reading output
    engine_version                          TEXT NOT NULL,
    linked_historical_event_id               TEXT,          -- optional FK into historical_events.db
    notes                                      TEXT
);

CREATE TABLE IF NOT EXISTS outcome_records (
    outcome_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    validation_id      TEXT NOT NULL REFERENCES validation_records(validation_id),
    revealed_at           TEXT NOT NULL,  -- real wall-clock ISO timestamp
    outcome_date            TEXT NOT NULL,  -- real date of the actual outcome/event
    outcome_description       TEXT NOT NULL,
    outcome_valence              TEXT NOT NULL,  -- see VALID_OUTCOME_VALENCES
    outcome_source                 TEXT NOT NULL,  -- citation/link -- never fabricated
    match_assessment                  TEXT NOT NULL,  -- see VALID_MATCH_ASSESSMENTS
    assessed_by                          TEXT NOT NULL,  -- 'automated' | 'manual'
    notes                                   TEXT
);
"""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def get_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_SQL)
    conn.commit()


@dataclass
class ValidationRecord:
    validation_id: str
    reading_mode: str
    entity_name: str
    entity_type: str
    as_of_date: str
    dominant_lord: str
    agreement_classification: str
    agreement_reasoning: str
    predicted_valence: str
    reading_text: str
    engine_version: str
    jyotisha_dignity: Optional[str] = None
    jyotisha_score: Optional[float] = None
    hellenistic_dignity: Optional[str] = None
    hellenistic_score: Optional[float] = None
    linked_historical_event_id: Optional[str] = None
    notes: str = ""
    predicted_at: str = field(default_factory=_now_iso)


def valence_from_agreement(classification: str, jyotisha_score: Optional[float]) -> str:
    """Derives a single predicted_valence label from the agreement classification
    and (as tiebreaker/fallback) the Jyotisha score's sign -- used so
    record_prediction() doesn't require the caller to separately decide this."""
    if classification in ("Insufficient",):
        return "insufficient"
    if jyotisha_score is None:
        return "insufficient"
    if jyotisha_score > 0:
        return "favorable"
    if jyotisha_score < 0:
        return "unfavorable"
    return "neutral"


def record_prediction(conn: sqlite3.Connection, rec: ValidationRecord) -> str:
    if rec.predicted_valence not in VALID_VALENCES:
        raise ValueError(f"predicted_valence must be one of {VALID_VALENCES}, got {rec.predicted_valence!r}")
    conn.execute(
        """INSERT INTO validation_records
           (validation_id, reading_mode, entity_name, entity_type, as_of_date,
            predicted_at, dominant_lord, jyotisha_dignity, jyotisha_score,
            hellenistic_dignity, hellenistic_score, agreement_classification,
            agreement_reasoning, predicted_valence, reading_text, engine_version,
            linked_historical_event_id, notes)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (rec.validation_id, rec.reading_mode, rec.entity_name, rec.entity_type,
         rec.as_of_date, rec.predicted_at, rec.dominant_lord, rec.jyotisha_dignity,
         rec.jyotisha_score, rec.hellenistic_dignity, rec.hellenistic_score,
         rec.agreement_classification, rec.agreement_reasoning, rec.predicted_valence,
         rec.reading_text, rec.engine_version, rec.linked_historical_event_id, rec.notes),
    )
    conn.commit()
    return rec.validation_id


def assess_match(predicted_valence: str, outcome_valence: str) -> str:
    """Deliberately conservative: only a clean favorable/unfavorable prediction
    against a clean favorable/unfavorable outcome is ever called MATCH or
    MISMATCH. Anything touching 'neutral', 'mixed', 'unclear', or 'insufficient'
    on either side is AMBIGUOUS -- this project does not stretch a neutral
    prediction into a claimed hit."""
    if predicted_valence == "insufficient" or outcome_valence in ("mixed", "unclear"):
        return "AMBIGUOUS"
    if predicted_valence == "neutral" or outcome_valence == "neutral":
        return "AMBIGUOUS"
    if predicted_valence == outcome_valence:
        return "MATCH"
    return "MISMATCH"


def record_outcome(
    conn: sqlite3.Connection, validation_id: str, outcome_date: str,
    outcome_description: str, outcome_valence: str, outcome_source: str,
    assessed_by: str = "manual", notes: str = "",
) -> int:
    if outcome_valence not in VALID_OUTCOME_VALENCES:
        raise ValueError(f"outcome_valence must be one of {VALID_OUTCOME_VALENCES}, got {outcome_valence!r}")
    row = conn.execute(
        "SELECT predicted_valence FROM validation_records WHERE validation_id = ?",
        (validation_id,),
    ).fetchone()
    if row is None:
        raise ValueError(f"no validation_records row for validation_id={validation_id!r} "
                          f"-- record the prediction first via record_prediction()")
    predicted_valence = row[0]
    match_assessment = assess_match(predicted_valence, outcome_valence)
    cur = conn.execute(
        """INSERT INTO outcome_records
           (validation_id, revealed_at, outcome_date, outcome_description,
            outcome_valence, outcome_source, match_assessment, assessed_by, notes)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (validation_id, _now_iso(), outcome_date, outcome_description, outcome_valence,
         outcome_source, match_assessment, assessed_by, notes),
    )
    conn.commit()
    return cur.lastrowid


def get_prediction(conn: sqlite3.Connection, validation_id: str) -> Optional[dict]:
    row = conn.execute(
        "SELECT * FROM validation_records WHERE validation_id = ?", (validation_id,)
    ).fetchone()
    if row is None:
        return None
    cols = [c[1] for c in conn.execute("PRAGMA table_info(validation_records)").fetchall()]
    return dict(zip(cols, row))


def get_outcomes(conn: sqlite3.Connection, validation_id: str) -> List[dict]:
    rows = conn.execute(
        "SELECT * FROM outcome_records WHERE validation_id = ? ORDER BY revealed_at",
        (validation_id,),
    ).fetchall()
    cols = [c[1] for c in conn.execute("PRAGMA table_info(outcome_records)").fetchall()]
    return [dict(zip(cols, r)) for r in rows]


def compute_accuracy_summary(conn: sqlite3.Connection) -> dict:
    """Aggregates match_assessment counts, grouped by agreement_classification,
    across every validation_record that has at least one outcome recorded.
    Returns an honest summary -- including the total n, since a summary with a
    tiny n is exactly the kind of thing that must not be presented as if it
    were a real accuracy claim. Records with zero outcomes are excluded (not
    counted as any kind of miss) and reported separately as `unassessed_count`."""
    rows = conn.execute(
        """SELECT v.agreement_classification, o.match_assessment, COUNT(*)
           FROM validation_records v JOIN outcome_records o
             ON v.validation_id = o.validation_id
           GROUP BY v.agreement_classification, o.match_assessment"""
    ).fetchall()
    summary: dict = {}
    for classification, outcome, count in rows:
        summary.setdefault(classification, {}).setdefault(outcome, 0)
        summary[classification][outcome] += count
    total_predictions = conn.execute("SELECT COUNT(*) FROM validation_records").fetchone()[0]
    predictions_with_outcomes = conn.execute(
        "SELECT COUNT(DISTINCT validation_id) FROM outcome_records"
    ).fetchone()[0]
    return {
        "by_classification": summary,
        "total_predictions": total_predictions,
        "predictions_with_outcomes": predictions_with_outcomes,
        "unassessed_count": total_predictions - predictions_with_outcomes,
        "caveat": "n is almost certainly too small for any statistical claim -- "
                  "see this module's docstring. This is a storage/audit layer, not "
                  "a completed backtest experiment.",
    }
