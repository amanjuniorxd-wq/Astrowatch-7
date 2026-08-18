"""
Astrowatch — forecast evaluation
=================================
Compares a saved prediction (predictions.db) against an actual, independently-reported
event and classifies the outcome. STATUS: written this pass, NOT executed (no sqlite3
execution available -- see VALIDATION_REPORT.md).

STRICTNESS (per instruction: do not automatically mark a forecast correct merely
because something vaguely related happened): classification is a forced manual choice
by whoever runs this tool, not automated text-matching against news. This file provides
structure and immutable record-keeping; it deliberately does NOT contain any keyword-
matching or NLP "did this happen" heuristic, because that would be exactly the kind of
"AI decides" step Astrowatch's rule engine was built to avoid at the forecasting stage
too.
"""

import argparse
import datetime
import sqlite3
from dataclasses import dataclass

VALID_CLASSIFICATIONS = {"CORRECT", "PARTIAL", "MISS", "NO-EVENT", "UNRESOLVED"}


@dataclass
class Evaluation:
    prediction_id: str
    actual_event_description: str
    classification: str
    evaluated_at: str


def record_evaluation(db_path: str, prediction_id: str, actual_event_description: str,
                        classification: str) -> Evaluation:
    if classification not in VALID_CLASSIFICATIONS:
        raise ValueError(f"classification must be one of {sorted(VALID_CLASSIFICATIONS)}")
    evaluated_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM predictions WHERE prediction_id = ?", (prediction_id,))
        if cur.fetchone() is None:
            raise ValueError(
                f"prediction_id {prediction_id!r} not found -- refusing to record an "
                f"evaluation against a prediction that was never actually saved before "
                f"its forecast window (that would defeat the whole point of "
                f"pre-registering predictions)."
            )
        cur.execute(
            "INSERT INTO forecast_evaluations "
            "(prediction_id, evaluated_at, actual_event_description, classification) "
            "VALUES (?, ?, ?, ?)",
            (prediction_id, evaluated_at, actual_event_description, classification),
        )
        conn.commit()
    finally:
        conn.close()
    return Evaluation(prediction_id=prediction_id,
                       actual_event_description=actual_event_description,
                       classification=classification, evaluated_at=evaluated_at)


def summarize(db_path: str) -> dict:
    """Aggregate counts per classification -- purely descriptive, no scoring formula
    invented here (a scoring/accuracy metric should be designed deliberately, with its
    own validation, not bolted on as an afterthought)."""
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("SELECT classification, COUNT(*) FROM forecast_evaluations GROUP BY classification")
        rows = cur.fetchall()
    finally:
        conn.close()
    return {cls: count for cls, count in rows}


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Astrowatch forecast evaluation (manual classification only)")
    p.add_argument("--db", default="predictions.db")
    sub = p.add_subparsers(dest="cmd", required=True)

    rec = sub.add_parser("record")
    rec.add_argument("--prediction-id", required=True)
    rec.add_argument("--actual-event", required=True)
    rec.add_argument("--classification", required=True, choices=sorted(VALID_CLASSIFICATIONS))

    sub.add_parser("summarize")
    return p


def main(argv=None):
    args = build_arg_parser().parse_args(argv)
    if args.cmd == "record":
        result = record_evaluation(args.db, args.prediction_id, args.actual_event, args.classification)
        print(result)
    elif args.cmd == "summarize":
        print(summarize(args.db))


if __name__ == "__main__":
    main()
