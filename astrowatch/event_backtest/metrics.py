"""
event_backtest/metrics.py
===========================
Real metric computations over a list of (event, PredictionResult) pairs
AFTER the actual winner has been revealed by engine.py. Every formula here
is standard and documented; no metric is invented or approximated without
saying so. Numerical safeguards (epsilon clipping) are applied wherever a
log() or division could blow up on a 0 or 1 probability.

EVENTS WITH status != "OK" (INSUFFICIENT_DATA / DATA_UNAVAILABLE) are
EXCLUDED from every metric below and counted separately -- they must never
silently count as a miss or be dropped without being reported (see
report.py).
"""
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from event_backtest.models import HistoricalPredictionEvent, PredictionResult

EPS = 1e-9  # numerical safeguard against log(0) / division by exactly 0


@dataclass
class EvaluatedPrediction:
    event_id: str
    event_type: str
    model_version: str
    status: str
    correct: Optional[bool]           # None if status != OK
    predicted_winner: Optional[str]
    actual_winner: Optional[str]
    brier: Optional[float]
    log_loss: Optional[float]
    predicted_rank_of_actual: Optional[int]   # 1 = predictor's top pick was correct
    reciprocal_rank: Optional[float]
    top_probability: Optional[float]           # predictor's confidence in ITS OWN top pick


def evaluate_one(event: HistoricalPredictionEvent, result: PredictionResult) -> EvaluatedPrediction:
    """Called by engine.py AFTER prediction is complete and actual_winner has
    been revealed -- never called with an unrevealed result."""
    if result.status != "OK" or event.actual_winner is None:
        return EvaluatedPrediction(
            event_id=event.event_id, event_type=event.event_type, model_version=result.model_version,
            status=result.status, correct=None, predicted_winner=result.predicted_winner,
            actual_winner=event.actual_winner, brier=None, log_loss=None,
            predicted_rank_of_actual=None, reciprocal_rank=None, top_probability=None,
        )

    probs = result.probabilities or {}
    candidate_ids = [c.candidate_id for c in event.candidates]
    n = len(candidate_ids)

    correct = (result.predicted_winner == event.actual_winner)

    # Brier score (multiclass / one-vs-all form): sum over candidates of
    # (predicted_prob - actual_indicator)^2. Standard multiclass Brier as
    # used in forecast verification (Brier, 1950).
    brier = None
    if probs:
        brier = sum(
            (probs.get(cid, 0.0) - (1.0 if cid == event.actual_winner else 0.0)) ** 2
            for cid in candidate_ids
        )

    # Multiclass log loss: -log(p_actual), clipped to avoid log(0).
    log_loss = None
    if probs and event.actual_winner in probs:
        p_actual = max(EPS, min(1.0 - EPS, probs[event.actual_winner]))
        log_loss = -math.log(p_actual)
    elif probs:
        # actual_winner had probability exactly 0 / was excluded from probs
        # (e.g. every feature was missing for that one candidate) --
        # treated as EPS probability, not silently skipped.
        log_loss = -math.log(EPS)

    # Rank of the actual winner among candidates sorted by predicted
    # probability (descending); ties broken by candidate_id for
    # reproducibility.
    predicted_rank_of_actual = None
    reciprocal_rank = None
    top_probability = None
    if probs:
        ranked = sorted(candidate_ids, key=lambda cid: (-probs.get(cid, 0.0), cid))
        if event.actual_winner in ranked:
            predicted_rank_of_actual = ranked.index(event.actual_winner) + 1
            reciprocal_rank = 1.0 / predicted_rank_of_actual
        if ranked:
            top_probability = probs.get(ranked[0], None)

    return EvaluatedPrediction(
        event_id=event.event_id, event_type=event.event_type, model_version=result.model_version,
        status=result.status, correct=correct, predicted_winner=result.predicted_winner,
        actual_winner=event.actual_winner, brier=brier, log_loss=log_loss,
        predicted_rank_of_actual=predicted_rank_of_actual, reciprocal_rank=reciprocal_rank,
        top_probability=top_probability,
    )


@dataclass
class AggregateMetrics:
    n_total: int
    n_ok: int
    n_excluded: int              # status != OK
    top1_accuracy: Optional[float]
    mean_brier: Optional[float]
    mean_log_loss: Optional[float]
    mean_reciprocal_rank: Optional[float]
    mean_predicted_rank_of_actual: Optional[float]
    by_event_type: Dict[str, "AggregateMetrics"] = field(default_factory=dict)
    by_model_version: Dict[str, "AggregateMetrics"] = field(default_factory=dict)


def _mean(values: List[Optional[float]]) -> Optional[float]:
    vals = [v for v in values if v is not None]
    return sum(vals) / len(vals) if vals else None


def aggregate(evaluated: List[EvaluatedPrediction], _recurse: bool = True) -> AggregateMetrics:
    ok = [e for e in evaluated if e.status == "OK"]
    excluded = [e for e in evaluated if e.status != "OK"]

    agg = AggregateMetrics(
        n_total=len(evaluated), n_ok=len(ok), n_excluded=len(excluded),
        top1_accuracy=_mean([1.0 if e.correct else 0.0 for e in ok]) if ok else None,
        mean_brier=_mean([e.brier for e in ok]),
        mean_log_loss=_mean([e.log_loss for e in ok]),
        mean_reciprocal_rank=_mean([e.reciprocal_rank for e in ok]),
        mean_predicted_rank_of_actual=_mean([e.predicted_rank_of_actual for e in ok]),
    )

    if _recurse:
        by_type: Dict[str, List[EvaluatedPrediction]] = {}
        by_version: Dict[str, List[EvaluatedPrediction]] = {}
        for e in evaluated:
            by_type.setdefault(e.event_type, []).append(e)
            by_version.setdefault(e.model_version, []).append(e)
        agg.by_event_type = {k: aggregate(v, _recurse=False) for k, v in by_type.items()}
        agg.by_model_version = {k: aggregate(v, _recurse=False) for k, v in by_version.items()}

    return agg
