"""
Astrowatch Online -- World Astrology Prediction orchestration.
===================================================================
The entry point behind POST /api/world-prediction. Reuses
ai.prediction_agent._resolve_entity (the SAME entity-resolution logic that
POST /api/predict uses -- caller-supplied real birth/inception data takes
priority, otherwise looked up in entities_db, otherwise a clear 4xx error;
never fabricates missing birth/inception details) rather than duplicating it.

Runs world_astrology.unified_engine.UnifiedAstrologyEngine -- every
applicable tradition engine runs independently, producing individually
traceable TraditionPrediction results, before any text synthesis happens.
Optionally hands the already-final structured result to OpenAI (ai/synthesis.py's
existing SYSTEM_PROMPT/integrity-rules machinery) for natural-language polish
of the (already computed, already honest) short/detailed reading -- if
OPENAI_API_KEY is not configured, the template-based short_reading()/
detailed_reading() text from world_astrology/unified_engine.py is returned
as-is (this endpoint is fully functional without AI, per the project's
standing "AI is orchestration/NLG only, never the calculation" rule).
"""

from typing import Any, Dict, List, Optional

from . import tools
from .prediction_agent import _resolve_entity, PredictionInputError
from world_astrology.engine_interface import PredictionContext
from world_astrology.unified_engine import UnifiedAstrologyEngine, short_reading, detailed_reading


ALL_TRADITIONS = ["jyotisha", "hellenistic", "western", "babylonian", "persian_islamic",
                  "chinese", "tibetan", "japanese", "egyptian", "mesoamerican"]


def run_world_prediction(payload: Dict[str, Any], persist: bool = True) -> Dict[str, Any]:
    """payload keys: entity, entity_type, question, prediction_date,
    prediction_period, geographic_scope, prediction_domain, event_type, mode
    ('short'|'detailed'), traditions (list, default = all 10, i.e. 'All
    Applicable' per the task's specified UI convention), and optionally
    date/time/latitude/longitude/timezone to chart an entity not already in
    entities_db.

    persist=False mirrors run_prediction's dry_run support -- runs the full
    real pipeline, only skips the predictions_db insert."""
    resolved = _resolve_entity(payload)
    question = payload.get("question") or f"What does Astrowatch's multi-tradition World Astrology reading indicate for {resolved['name']}?"
    mode = payload.get("mode", "detailed")
    if mode not in ("short", "detailed"):
        raise PredictionInputError("'mode' must be 'short' or 'detailed'.")

    traditions = payload.get("traditions")  # None = all applicable (default)
    if traditions is not None:
        unknown = [t for t in traditions if t not in ALL_TRADITIONS]
        if unknown:
            raise PredictionInputError(
                f"Unknown tradition(s) {unknown}. Known traditions: {ALL_TRADITIONS}."
            )

    ctx = PredictionContext(
        entity_name=resolved["name"], entity_type=resolved["entity_type"],
        birth_or_inception_date=resolved["date"], birth_or_inception_time=resolved.get("time"),
        latitude=float(resolved["latitude"]), longitude=float(resolved["longitude"]),
        timezone_name=resolved["timezone"],
        time_accuracy="documented" if resolved.get("time") else "assumed_midnight",
        prediction_date=payload.get("prediction_date"),
        prediction_period=payload.get("prediction_period"),
        geographic_scope=payload.get("geographic_scope"),
        prediction_domain=payload.get("prediction_domain"),
        event_type=payload.get("event_type"),
    )

    engine = UnifiedAstrologyEngine(traditions=traditions)
    unified = engine.generate_unified_prediction(ctx)

    reading_text = short_reading(unified) if mode == "short" else detailed_reading(unified)

    import dataclasses
    result: Dict[str, Any] = {
        "question": question, "entity": resolved["name"], "entity_type": resolved["entity_type"],
        "entity_resolution": resolved, "mode": mode,
        "traditions_evaluated": unified.traditions_evaluated,
        "traditions_applicable": unified.traditions_applicable,
        "traditions_calculated": unified.traditions_calculated,
        "traditions_unavailable": unified.traditions_unavailable,
        "status_by_tradition": unified.status_by_tradition,
        "agreement_classification": unified.agreement.classification,
        "contradiction_detected": unified.agreement.contradiction_detected,
        "reading_text": reading_text,
        "individual_predictions": {name: dataclasses.asdict(p)
                                    for name, p in unified.individual_predictions.items()},
        "limitations": unified.limitations,
    }
    if mode == "detailed":
        result["theme_clusters"] = [dataclasses.asdict(c) for c in unified.theme_clusters]
        result["weighting"] = [dataclasses.asdict(w) for w in unified.weighting]

    if persist:
        prediction_id = tools.save_prediction(
            entity=resolved["name"], question=question, prediction=reading_text,
            calculation_data=result, entity_type=resolved["entity_type"],
            time_window=payload.get("prediction_period"),
            traditions_used=[n for n, s in unified.status_by_tradition.items() if s == "calculated"],
            confidence=unified.agreement.classification, model_score=None, mode=mode,
            source=payload.get("source", "user"),
        )
        result["prediction_id"] = prediction_id
    else:
        result["prediction_id"] = None
        result["dry_run"] = True
    return result
