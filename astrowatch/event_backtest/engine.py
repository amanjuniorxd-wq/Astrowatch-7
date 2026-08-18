"""
event_backtest/engine.py
==========================
Orchestrates one call-ordering discipline, strictly:

  1. LOAD EVENT (from dataset.py)
  2. VALIDATE SCHEMA (cutoff.validate_event_schema_dates -- cutoff must be
     strictly before the event date)
  3. CALL prediction.predictor.predict(event.public_fields(), model_variant)
     -- public_fields() has NO actual_winner key at all, so there is
     nothing for the predictor to accidentally read.
  4. ONLY AFTER step 3 returns, read event.actual_winner and call
     event_backtest.metrics.evaluate_one() to score the prediction.

This ordering (predict first, reveal second) is what prevents hindsight
bias at the orchestration level, on top of cutoff.py's per-datum
HindsightError checks inside the predictor itself. Both layers exist
because a single point of enforcement is more fragile than two independent
ones (defense in depth) -- see BACKTEST.md's "Known Limitations" for why
this is convention-level (Python doesn't stop you from reading
event.actual_winner one line earlier) rather than AST-enforced like
backtest/blindness.py's system for the separate, older BT-001 experiment.
"""
from typing import List, Optional

from event_backtest.models import HistoricalPredictionEvent
from event_backtest.cutoff import validate_event_schema_dates
from event_backtest.metrics import EvaluatedPrediction, evaluate_one
from prediction.predictor import predict


def run_one(event: HistoricalPredictionEvent, model_variant: str = "complete") -> EvaluatedPrediction:
    if event.excluded:
        from event_backtest.models import PredictionResult
        skipped = PredictionResult(
            event_id=event.event_id, cutoff_date=event.prediction_cutoff_date, model_version="n/a",
            predicted_winner=None, scores={}, probabilities=None, probabilities_are_calibrated=False,
            feature_breakdown={}, status="DATA_UNAVAILABLE",
            status_reason=event.exclusion_reason or "Event marked excluded by dataset curator.",
        )
        return evaluate_one(event, skipped)

    validate_event_schema_dates(event.event_date, event.prediction_cutoff_date)

    # Step 3: predict -- ONLY public_fields() is passed, actual_winner is
    # not accessible from here at all.
    result = predict(event.public_fields(), model_variant=model_variant)

    # Step 4: reveal + score -- the FIRST line in this function that reads
    # event.actual_winner.
    return evaluate_one(event, result)


def run_all(events: List[HistoricalPredictionEvent], model_variant: str = "complete") -> List[EvaluatedPrediction]:
    return [run_one(e, model_variant=model_variant) for e in events]


def run_ablation(events: List[HistoricalPredictionEvent], variants: Optional[List[str]] = None):
    """Runs every event under every model variant -- for the ablation table
    (build spec Section 14: Model A vedic-core through Model F complete)."""
    from prediction.scorer import MODEL_VARIANTS
    from event_backtest.metrics import aggregate

    variant_names = variants or list(MODEL_VARIANTS.keys())
    results = {}
    for variant in variant_names:
        evaluated = run_all(events, model_variant=variant)
        results[variant] = {"evaluated": evaluated, "aggregate": aggregate(evaluated)}
    return results
