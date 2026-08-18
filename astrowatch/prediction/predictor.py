"""
prediction/predictor.py
========================
predict(public_event_fields, cutoff_date, model_variant) -- the single
entry point event_backtest/engine.py (and any live use) calls.

HINDSIGHT DISCIPLINE (convention-enforced, see event_backtest/models.py's
module docstring for why this is convention-level rather than AST-level like
backtest/blindness.py): this function's signature takes NO actual_winner
parameter at all -- there is no field to accidentally read. engine.py is
responsible for calling this BEFORE it ever looks at
HistoricalPredictionEvent.actual_winner, and for passing only
event.public_fields() (never the raw event object) -- see engine.py.

Event/match charts (Section 9 of the build spec): this project's cutoff.py
conservatively treats ANY astronomical-calculation target date after the
prediction cutoff as a hindsight risk (see cutoff.calc_date_within_cutoff's
docstring) -- so a match/final's own chart is only computed here when the
match date is AT OR BEFORE the cutoff (i.e., extremely rare for a genuine
pre-tournament prediction, where the final hasn't been played yet). For the
headline pre-tournament use case, event_chart_strength is correctly left as
None with a documented missing_components note, not silently skipped.
"""
from typing import Any, Dict, Optional

from event_backtest.models import CandidateRef, FeatureBreakdown, PredictionResult
from event_backtest.cutoff import calc_date_within_cutoff, HindsightError
from kundli import compute_kundli, EphemerisDataUnavailable
from world_astrology import dignity_tables as dt
import coordinates

from prediction.features import extract_entity_features, EntityFeatureSet, _normalize_jyotisha_score
from prediction.scorer import score_candidate, normalize_scores, MODEL_VERSION, MODEL_VARIANTS


def _event_chart_strength(candidate_features: EntityFeatureSet, event_date: str,
                           cutoff_date: str, lat: Optional[float], lon: Optional[float]) -> Optional[str]:
    """Returns None if the event/match chart cannot be legitimately computed
    without a hindsight risk or missing location. Only computes a real value
    when event_date <= cutoff_date (see module docstring) AND a real venue
    location is known."""
    if lat is None or lon is None:
        return None, "event_chart not computed: no real venue location supplied for this event."
    try:
        calc_date_within_cutoff(event_date, cutoff_date)
    except HindsightError:
        return None, ("event_chart not computed: the match date is after the prediction cutoff "
                       "-- this project's cutoff.py conservatively treats any astronomical "
                       "calculation targeting a post-cutoff date as a hindsight risk (see "
                       "cutoff.calc_date_within_cutoff), so no event/match chart is computed for "
                       "genuine pre-event predictions. This is a deliberate, documented choice, "
                       "not a bug.")
    return None, "event_chart feature not yet implemented for event_date <= cutoff_date case."


def _feature_breakdown_from(features: EntityFeatureSet) -> FeatureBreakdown:
    fb = FeatureBreakdown(
        candidate_id=features.candidate_id,
        dasha_lord=features.mahadasha_lord, dasha_lord_strength=features.mahadasha_lord_score,
        antardasha_lord=features.antardasha_lord, antardasha_strength=features.antardasha_lord_score,
        transit_strength=features.transit_strength, moon_activation=features.moon_activation,
        entity_chart_strength=features.entity_chart_strength,
        event_chart_strength=features.event_chart_strength,
        key_personnel_strength=features.key_personnel_strength,
        confidence_notes=list(features.confidence_notes),
        missing_components=list(features.missing_components),
    )
    return fb


def predict(public_event_fields: Dict[str, Any], model_variant: str = "complete") -> PredictionResult:
    """public_event_fields: exactly the dict returned by
    HistoricalPredictionEvent.public_fields() -- event_id, event_type,
    event_name, prediction_cutoff_date, location(+lat/lon/tz),
    candidates: List[CandidateRef]. Deliberately does NOT accept
    actual_winner as a parameter at all."""
    event_id = public_event_fields["event_id"]
    cutoff_date = public_event_fields["prediction_cutoff_date"]
    candidates = public_event_fields["candidates"]

    if model_variant not in MODEL_VARIANTS:
        return PredictionResult(
            event_id=event_id, cutoff_date=cutoff_date, model_version=MODEL_VERSION,
            predicted_winner=None, scores={}, probabilities=None,
            probabilities_are_calibrated=False, feature_breakdown={},
            status="INSUFFICIENT_DATA", status_reason=f"Unknown model_variant {model_variant!r}.",
        )

    if not candidates:
        return PredictionResult(
            event_id=event_id, cutoff_date=cutoff_date, model_version=MODEL_VERSION,
            predicted_winner=None, scores={}, probabilities=None,
            probabilities_are_calibrated=False, feature_breakdown={},
            status="DATA_UNAVAILABLE", status_reason="Event has no candidates.",
        )

    event_lat = public_event_fields.get("location_latitude")
    event_lon = public_event_fields.get("location_longitude")

    feature_breakdowns: Dict[str, FeatureBreakdown] = {}
    raw_scores: Dict[str, Optional[float]] = {}

    for candidate in candidates:
        try:
            features = extract_entity_features(
                candidate, cutoff_date,
                event_location=(event_lat, event_lon) if event_lat is not None and event_lon is not None else None,
            )
        except HindsightError as exc:
            return PredictionResult(
                event_id=event_id, cutoff_date=cutoff_date, model_version=MODEL_VERSION,
                predicted_winner=None, scores={}, probabilities=None,
                probabilities_are_calibrated=False, feature_breakdown={},
                status="INSUFFICIENT_DATA",
                status_reason=f"HindsightError for candidate {candidate.candidate_id!r}: {exc}",
            )

        # event_chart_strength: only meaningfully computable when the match
        # date is known and at/before cutoff -- see module docstring. For
        # this dataset's headline pre-tournament predictions this always
        # returns None with a documented reason, which is the honest,
        # intended outcome (not a bug or an omission).
        event_date = public_event_fields.get("event_date")
        if event_date:
            strength, reason = _event_chart_strength(features, event_date, cutoff_date, event_lat, event_lon)
            features.event_chart_strength = strength
            features.missing_components.append(reason)

        # key_personnel_strength: conservatively left None in this initial
        # version -- see features.extract_key_personnel_features's
        # docstring (computing it would require fabricating a captain
        # birthplace, which this project's rules forbid).
        if candidate.captain_birth_date:
            features.missing_components.append(
                f"key_personnel_strength not computed for captain {candidate.captain_name!r}: "
                f"would require a real, sourced birthplace to compute Ascendant/house-dependent "
                f"features, which is not available -- this project does not fabricate a "
                f"birthplace (see mundane/entity_chart.py's rule)."
            )
        else:
            features.missing_components.append(
                f"key_personnel_strength not computed: no captain birth date on file for "
                f"{candidate.display_name!r}."
            )

        score_result = score_candidate(features, model_variant)
        raw_scores[candidate.candidate_id] = score_result.raw_score
        fb = _feature_breakdown_from(features)
        if score_result.missing_features:
            fb.missing_components.append(
                f"Model variant {model_variant!r} excluded/renormalized around missing features: "
                f"{score_result.missing_features}"
            )
        feature_breakdowns[candidate.candidate_id] = fb

    if all(s is None for s in raw_scores.values()):
        return PredictionResult(
            event_id=event_id, cutoff_date=cutoff_date, model_version=MODEL_VERSION,
            predicted_winner=None, scores={}, probabilities=None,
            probabilities_are_calibrated=False, feature_breakdown=feature_breakdowns,
            status="INSUFFICIENT_DATA",
            status_reason="Every candidate had no computable features for this model variant.",
        )

    probabilities = normalize_scores(raw_scores)
    scored = {cid: s for cid, s in raw_scores.items() if s is not None}
    predicted_winner = max(scored, key=scored.get) if scored else None

    return PredictionResult(
        event_id=event_id, cutoff_date=cutoff_date, model_version=f"{MODEL_VERSION}:{model_variant}",
        predicted_winner=predicted_winner,
        scores={cid: (s if s is not None else 0.0) for cid, s in raw_scores.items()},
        probabilities=probabilities,
        probabilities_are_calibrated=False,   # never claimed True without calibration.py evidence
        feature_breakdown=feature_breakdowns,
        status="OK",
        status_reason=None,
    )
