"""
Astrowatch Online -- current-event intelligence.
====================================================
Extracts structured fields from a piece of current-event text (a headline or
summary the user/an automated scan supplies -- this module does NOT itself
fetch live news; the platform's web-search/news-ingestion layer, if any, is
the caller's responsibility, consistent with this project's existing
"no invented external data" stance). Then determines whether Astrowatch can
meaningfully analyze it: only if a concrete, resolvable entity is identified
AND that entity (or a close match) exists in entities_db with real date/place
data. If not, this returns can_analyze=False rather than fabricating entity
details to force a reading through -- per task spec Section 10's explicit
instruction.
"""

from typing import Any, Dict, Optional

from . import openai_client, prompts, tools

EVENT_SCHEMA = {
    "type": "object",
    "properties": {
        "event_summary": {"type": "string"},
        "entities": {"type": "array", "items": {"type": "string"}},
        "domain": {
            "type": "string",
            "enum": ["politics", "geopolitics", "economics", "finance", "technology",
                     "sports", "business", "social", "environment",
                     "international_relations", "conflict", "other"],
        },
        "location": {"type": "string"},
        "approximate_date": {"type": "string", "description": "YYYY-MM-DD if known, else empty string."},
        "importance": {"type": "number", "description": "0.0-1.0 subjective importance score."},
        "prediction_horizon_days": {"type": "integer"},
        "can_analyze": {"type": "boolean"},
        "reason": {"type": "string", "description": "Why can_analyze is true/false."},
    },
    "required": ["event_summary", "entities", "domain", "location", "approximate_date",
                 "importance", "prediction_horizon_days", "can_analyze", "reason"],
    "additionalProperties": False,
}


def scan_event(event_text: str) -> Dict[str, Any]:
    """Returns {"extracted": {...}, "resolved_entities": [...real entities_db
    rows...], "can_analyze": bool, "question": str|None}. Never fabricates an
    entity's astronomical input data -- if none of the extracted entity names
    resolve to a real entities_db row, can_analyze is forced False regardless
    of what the model said, and the caller is told exactly why."""
    extracted = openai_client.complete_json(
        system_prompt=prompts.SYSTEM_PROMPT + "\n\n" + prompts.EVENT_EXTRACTION_INSTRUCTIONS,
        user_prompt=f"Current-event text:\n\n{event_text}",
        schema_name="event_extraction",
        schema=EVENT_SCHEMA,
    )

    resolved = []
    for name in extracted.get("entities", []):
        matches = tools.search_entities(query=name, limit=3)
        exact = [m for m in matches if m["name"].lower() == name.lower()]
        if exact:
            resolved.append(exact[0])
        elif matches:
            resolved.append(matches[0])

    can_analyze = bool(extracted.get("can_analyze")) and len(resolved) > 0
    reason = extracted.get("reason", "")
    if extracted.get("can_analyze") and not resolved:
        can_analyze = False
        reason = (
            f"Model judged this analyzable, but none of the extracted entities "
            f"({extracted.get('entities')}) resolve to a real entity with known "
            f"date/place data in Astrowatch's entities database -- refusing to "
            f"fabricate entity details to force an analysis."
        )

    question = None
    if can_analyze and resolved:
        primary = resolved[0]
        horizon = extracted.get("prediction_horizon_days") or 30
        question = (
            f"What does Astrowatch indicate about {primary['name']}'s "
            f"situation regarding \"{extracted.get('event_summary', event_text)[:120]}\" "
            f"over the next {horizon} days?"
        )

    return {
        "extracted": extracted, "resolved_entities": resolved,
        "can_analyze": can_analyze, "reason": reason, "question": question,
    }

def analyze_current_event(event_text: str, mode: str = "detailed") -> Dict[str, Any]:
    """Full current-event pipeline (task spec Section 20/35):
    current event -> entity identification -> entity verification -> Astrowatch
    calculation -> applicable traditions -> individual predictions ->
    cross-tradition comparison -> OpenAI synthesis.

    Delegates the 'run Astrowatch, compare, synthesize' half to
    ai.prediction_agent.run_prediction() (the exact same pipeline
    POST /api/predict uses) once scan_event() has produced a question and a
    verified, resolved entity -- no duplicated orchestration logic. If the
    event cannot be analyzed (no resolvable entity), returns a clear
    can_analyze=False result instead of a fabricated reading -- never calls
    prediction_agent in that case."""
    from . import prediction_agent  # local import: avoids a circular import at module load

    scan = scan_event(event_text)
    if not scan["can_analyze"]:
        return {
            "status": "cannot_analyze", "event_text": event_text,
            "extracted": scan["extracted"], "resolved_entities": scan["resolved_entities"],
            "reason": scan["reason"],
        }

    primary = scan["resolved_entities"][0]
    extracted = scan["extracted"]
    payload = {
        "entity": primary["name"], "entity_type": primary["entity_type"],
        "question": scan["question"], "mode": mode,
    }
    if extracted.get("approximate_date"):
        payload["start_date"] = extracted["approximate_date"]

    result = prediction_agent.run_prediction(payload)
    result["event_text"] = event_text
    result["event_extraction"] = extracted
    result["resolved_entities"] = scan["resolved_entities"]
    return result
