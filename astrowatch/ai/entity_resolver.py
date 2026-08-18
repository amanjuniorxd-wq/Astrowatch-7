"""
Astrowatch Online -- entity resolution.
==========================================
Converts a natural-language prediction question into structured fields
(task spec Section 7A example: "What does astrology indicate for India in
September 2026?" -> {"entity": "India", "entity_type": "country", ...}), then
attempts to resolve that entity against the real entities_db (Phase 2b) so the
caller gets back REAL coordinates/timezone/inception data, not just OpenAI's
guess at them. OpenAI is only ever used here to parse the QUESTION's intent
(what entity/domain/dates is the user asking about) -- it never supplies the
entity's actual astronomical input data; that always comes from entities_db or
is reported as missing.
"""

from typing import Any, Dict, Optional

from . import openai_client, prompts, tools

RESOLUTION_SCHEMA = {
    "type": "object",
    "properties": {
        "entity": {"type": "string", "description": "The primary entity's name, or empty string if none identifiable."},
        "entity_type": {
            "type": "string",
            "enum": ["person", "country", "government", "political_party", "company",
                     "organization", "sports_team", "institution", "city", "event",
                     "technology", "other", "unclear"],
        },
        "domain": {
            "type": "string",
            "enum": ["politics", "geopolitics", "economics", "finance", "technology",
                     "sports", "business", "social", "environment",
                     "international_relations", "conflict", "personal", "other", "unclear"],
        },
        "start_date": {"type": "string", "description": "YYYY-MM-DD or empty string if not stated/inferable."},
        "end_date": {"type": "string", "description": "YYYY-MM-DD or empty string if not stated/inferable."},
        "location_hint": {"type": "string", "description": "Any place name mentioned, else empty string."},
    },
    "required": ["entity", "entity_type", "domain", "start_date", "end_date", "location_hint"],
    "additionalProperties": False,
}


def resolve_question(question: str, today_iso: Optional[str] = None) -> Dict[str, Any]:
    """Returns {"parsed": {...structured fields from OpenAI...},
    "matched_entity": {...real entities_db row, or None...},
    "status": "resolved" | "entity_not_found" | "unclear"}.
    Raises ai.openai_client.AIUnavailable if OpenAI isn't configured -- callers
    (api.py handlers) catch that and return a clear error, never a guess."""
    import datetime
    today_iso = today_iso or datetime.date.today().isoformat()
    user_prompt = (
        f"Today's date is {today_iso}. Parse this prediction question:\n\n{question}"
    )
    parsed = openai_client.complete_json(
        system_prompt=prompts.SYSTEM_PROMPT + "\n\n" + prompts.ENTITY_RESOLUTION_INSTRUCTIONS,
        user_prompt=user_prompt,
        schema_name="entity_resolution",
        schema=RESOLUTION_SCHEMA,
    )

    if not parsed.get("entity"):
        return {"parsed": parsed, "matched_entity": None, "status": "unclear"}

    entity_type = parsed.get("entity_type")
    matches = tools.search_entities(
        query=parsed["entity"],
        entity_type=None if entity_type in (None, "unclear") else entity_type,
        limit=5,
    )
    exact = [m for m in matches if m["name"].lower() == parsed["entity"].lower()]
    matched = exact[0] if exact else (matches[0] if matches else None)

    return {
        "parsed": parsed,
        "matched_entity": matched,
        "status": "resolved" if matched else "entity_not_found",
    }
