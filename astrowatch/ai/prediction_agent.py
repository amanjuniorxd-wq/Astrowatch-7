"""
Astrowatch Online -- prediction orchestration.
=================================================
The one place that wires together: entity resolution -> Astrowatch tool calls
(ai/tools.py) -> cross-tradition comparison -> OpenAI synthesis (ai/synthesis.py)
-> persistence (predictions_db via ai/tools.save_prediction). This is the
engine behind POST /api/predict, and is reused by ai/random_prediction.py and
ai/event_scanner.py's current-event pipeline (both just supply a different
`question`/entity-selection strategy upstream of this same core).

ASTROLOGICAL CALCULATION STAYS SEPARATE FROM AI SYNTHESIS throughout: every
tool call below returns real Astrowatch output BEFORE any OpenAI call is made;
synthesis.build_final_result() only ever writes prose FROM that already-final
structured data, never the reverse.
"""

import datetime
from typing import Any, Dict, Optional

from . import openai_client, synthesis, tools


class PredictionInputError(Exception):
    """Raised for a caller-facing 4xx-worthy problem (missing/invalid entity
    data) -- distinct from AIUnavailable (OpenAI not configured) and
    tools.ToolError (a downstream calculation failure)."""


def _resolve_entity(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Resolves the entity to chart. Priority:
    1. Caller supplied full real birth/inception data directly in the request
       (date + latitude + longitude + timezone) -- used as-is, never second-
       guessed, since the caller is asserting it's real.
    2. Otherwise, look up by name (+ optional entity_type) in entities_db --
       the project's own vetted corpus.
    If neither yields real date+place data, raises PredictionInputError --
    per the integrity rules, this system never invents birth/inception
    details to force a reading through."""
    name = payload.get("entity")
    if not name:
        raise PredictionInputError("'entity' (name) is required.")
    entity_type = payload.get("entity_type") or "other"

    if payload.get("date") and payload.get("latitude") is not None and \
            payload.get("longitude") is not None and payload.get("timezone"):
        return {
            "name": name, "entity_type": entity_type, "date": payload["date"],
            "time": payload.get("time"), "latitude": float(payload["latitude"]),
            "longitude": float(payload["longitude"]), "timezone": payload["timezone"],
            "resolution_source": "caller_supplied",
        }

    matches = tools.search_entities(query=name, entity_type=None if entity_type == "other" else entity_type, limit=5)
    exact = [m for m in matches if m["name"].lower() == name.lower()]
    match = exact[0] if exact else (matches[0] if matches else None)
    if match is None:
        raise PredictionInputError(
            f"Entity {name!r} was not found in Astrowatch's entities database and no "
            f"real birth/inception date+place+timezone was supplied in the request. "
            f"Per this project's standing rule, an entity can only be analyzed with a "
            f"real, defensible date and place -- supply 'date', 'latitude', "
            f"'longitude', and 'timezone' explicitly, or use an entity already known "
            f"to Astrowatch (see GET /api/predictions or search_entities)."
        )
    return {
        "name": match["name"], "entity_type": match["entity_type"],
        "date": match["birth_or_inception_date"], "time": match["birth_or_inception_time"],
        "latitude": match["latitude"], "longitude": match["longitude"],
        "timezone": match["timezone"], "resolution_source": "entities_db",
        "matched_entity_id": match["id"],
    }


def run_prediction(payload: Dict[str, Any], persist: bool = True) -> Dict[str, Any]:
    """payload keys: entity, entity_type, question, start_date, end_date, mode
    ('short'|'detailed'), and optionally date/time/latitude/longitude/timezone
    to chart an entity not already in entities_db. Returns the Section 17
    final-result JSON shape plus a 'prediction_id' if it was saved.

    persist=False (used by POST /api/agent/run's dry_run=true, task spec
    Section 21) runs the ENTIRE real calculation + synthesis pipeline exactly
    as normal -- nothing about the astrology or AI synthesis is skipped or
    faked -- it only skips the final predictions_db insert, so a dry run never
    pollutes prediction history or novelty scoring."""
    resolved = _resolve_entity(payload)
    question = payload.get("question") or f"What does Astrowatch indicate for {resolved['name']}?"
    mode = payload.get("mode", "detailed")
    if mode not in ("short", "detailed"):
        raise PredictionInputError("'mode' must be 'short' or 'detailed'.")

    start_date = payload.get("start_date")
    end_date = payload.get("end_date")
    as_of_date = start_date or datetime.date.today().isoformat()
    time_window = f"{start_date}..{end_date}" if start_date and end_date else None

    chart_kwargs = dict(
        name=resolved["name"], entity_type=resolved["entity_type"], date=resolved["date"],
        latitude=resolved["latitude"], longitude=resolved["longitude"],
        timezone=resolved["timezone"], time=resolved.get("time"),
    )

    structured: Dict[str, Any] = {"entity_resolution": resolved}
    structured["entity_chart"] = tools.calculate_entity_chart(**chart_kwargs)
    structured["jyotisha"] = tools.run_jyotisha_prediction(**chart_kwargs, as_of_date=as_of_date)
    structured["cross_tradition"] = tools.run_cross_tradition_analysis(**chart_kwargs, as_of_date=as_of_date)
    if resolved["entity_type"] in ("country", "government", "political_party", "organization"):
        structured["world_reading"] = tools.run_world_astrology(**chart_kwargs, as_of_date=as_of_date)
    if mode == "detailed":
        structured["detailed_reading"] = tools.generate_detailed_reading(**chart_kwargs, as_of_date=as_of_date)
    else:
        structured["short_reading"] = tools.generate_short_reading(**chart_kwargs, as_of_date=as_of_date, max_sentences=4)

    traditions_used = list(structured["cross_tradition"].get("computed_traditions", []))

    result = synthesis.build_final_result(
        question=question, entities=[resolved["name"]], structured_results=structured,
        traditions_used=traditions_used, time_window=time_window, mode=mode,
    )

    if persist:
        prediction_id = tools.save_prediction(
            entity=resolved["name"], question=question,
            prediction=result.get("primary_prediction") or "(no AI synthesis -- see limitations)",
            calculation_data=structured, entity_type=resolved["entity_type"],
            time_window=time_window, traditions_used=traditions_used,
            confidence=structured["cross_tradition"].get("agreement_classification"),
            model_score=result.get("model_score"), mode=mode,
            source=payload.get("source", "user"),
        )
        result["prediction_id"] = prediction_id
    else:
        result["prediction_id"] = None
        result["dry_run"] = True
    return result
