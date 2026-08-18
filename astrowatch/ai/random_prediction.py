"""
Astrowatch Online -- autonomous random prediction selection.
================================================================
Selects (category, entity, time horizon, question) for an autonomous
prediction, per task spec Sections 12-13. Deliberately NOT
`random.choice(all_entities)`: candidates are pulled from the real
entities_db (Phase 2b, seeded from this project's own vetted corpora), scored
on several real signals, and the FINAL pick is a weighted-random draw among
the higher-scoring candidates -- genuinely random (you don't get the same
entity every time), but weighted toward entities that are actually worth
asking about right now (see _score_candidate).

This module does NOT call OpenAI to pick a category/entity/question (that
would be an unnecessary, costlier round-trip for something a few lines of
scoring logic already does deterministically-but-randomly) -- OpenAI is only
used, optionally, to phrase the final question more naturally; a clear
template-based question is always the safe fallback if OpenAI is unconfigured
or fails, so this module works with zero AI configuration.
"""

import random
import time as _time
from typing import Any, Dict, List, Optional

from . import openai_client, tools
import entities_db
import predictions_db

CATEGORIES = (
    "personal", "politics", "country", "business", "finance", "sports",
    "technology", "world", "historical", "custom",
)

# Maps a category to (entity_type filter, category filter, question template,
# default prediction-horizon days). category filter is matched against
# entities_db.category (e.g. 'ATHLETE', 'US_PRESIDENT', 'nation') -- None
# means "any category within this entity_type".
_CATEGORY_RULES: Dict[str, Dict[str, Any]] = {
    "personal":   {"entity_type": "person", "category": None, "horizon_days": 365,
                   "template": "What does Astrowatch indicate for {name}'s next year?"},
    "politics":   {"entity_type": "person", "category": None, "horizon_days": 90,
                   "template": "What does Astrowatch indicate for {name}'s political standing over the next {horizon} days?",
                   "category_prefixes": ("PRESIDENT", "PM", "LEADER")},  # matched by substring, see below
    "country":    {"entity_type": "country", "category": None, "horizon_days": 90,
                   "template": "What does Astrowatch indicate for {name} over the next {horizon} days?"},
    "world":      {"entity_type": "country", "category": None, "horizon_days": 180,
                   "template": "What does Astrowatch indicate for {name}'s broader trajectory over the next {horizon} days?"},
    "sports":     {"entity_type": "person", "category": "ATHLETE", "horizon_days": 270,
                   "template": "What does Astrowatch indicate about {name}'s upcoming competitive period?"},
    "business":   {"entity_type": "person", "category": "BUSINESS", "horizon_days": 180,
                   "template": "What does Astrowatch indicate for {name}'s business trajectory over the next {horizon} days?"},
    "technology": {"entity_type": "person", "category": "SCIENTIST", "horizon_days": 180,
                   "template": "What does Astrowatch indicate for {name}'s influence in their field over the next {horizon} days?"},
    "finance":    {"entity_type": "country", "category": None, "horizon_days": 90,
                   "template": "What does Astrowatch indicate for {name}'s economic period over the next {horizon} days?"},
    "historical": {"entity_type": "person", "category": None, "horizon_days": 0,
                   "template": "What did Astrowatch's methodology indicate for {name} during their lifetime?"},
    "custom":     {"entity_type": None, "category": None, "horizon_days": 90,
                   "template": "What does Astrowatch indicate for {name} over the next {horizon} days?"},
}


def _score_candidate(row: Dict[str, Any], conn_pred) -> float:
    """Higher is better. Combines:
    - data quality (documented time beats an assumed default -- more of the
      chart, incl. the Ascendant, is trustworthy)
    - novelty (heavily penalizes an entity predicted about recently)
    - historical importance (a rough, transparent heuristic: entities with a
      real 'notes'/'category' field -- i.e. this project actually researched
      something about them -- score higher than bare entries)
    - public interest proxy (same idea: category presence + source_reliability)
    """
    quality = 1.0 if row.get("time_accuracy") == "documented" else 0.5
    recent_n = predictions_db.recent_predictions_for_entity(conn_pred, row["name"], days=30)
    novelty = max(0.0, 1.0 - recent_n / 3.0)
    importance = 0.5
    if row.get("category"):
        importance += 0.25
    if row.get("source_reliability") == "HIGH":
        importance += 0.25
    elif row.get("source_reliability") == "MEDIUM":
        importance += 0.1
    public_interest = 0.5 + (0.3 if row.get("notes") else 0.0)
    return (quality * 0.25) + (novelty * 0.35) + (importance * 0.25) + (public_interest * 0.15)


def select_candidate(category: Optional[str] = None,
                      candidate_pool_size: int = 40,
                      top_n_for_weighted_choice: int = 8) -> Dict[str, Any]:
    """Returns {"category", "entity" (entities_db row dict), "horizon_days",
    "question"}. Raises ValueError if no eligible candidate exists for the
    chosen category (never fabricates one)."""
    category = category or random.choice(CATEGORIES)
    rule = _CATEGORY_RULES[category]

    conn_ent = entities_db.get_connection()
    conn_pred = predictions_db.get_connection()

    prefixes = rule.get("category_prefixes")
    if prefixes:
        # A prefix filter (e.g. politics -> "*_PRESIDENT"/"*_PM"/"LEADER") can
        # only match a small minority of this entity_type -- querying with the
        # default small pool size and THEN filtering would almost always yield
        # an empty result (the alphabetically-first N rows rarely happen to be
        # the matching ones). Query broadly first, filter second.
        broad_pool = entities_db.search_entities(conn_ent, entity_type=rule["entity_type"],
                                                   limit=5000)
        pool = [r for r in broad_pool if r.category and any(p in r.category for p in prefixes)]
    else:
        pool = entities_db.search_entities(
            conn_ent, entity_type=rule["entity_type"], category=rule["category"],
            limit=candidate_pool_size,
        )
    if not pool:
        # Fall back to a broader query within the same entity_type before giving up.
        pool = entities_db.search_entities(conn_ent, entity_type=rule["entity_type"],
                                            limit=candidate_pool_size)
    if not pool:
        raise ValueError(f"No eligible entities found in entities_db for category={category!r}.")

    scored = [(r, _score_candidate(r.__dict__, conn_pred)) for r in pool]
    scored.sort(key=lambda t: t[1], reverse=True)
    top = scored[:top_n_for_weighted_choice] or scored
    weights = [max(s, 0.01) for _, s in top]
    chosen_row, chosen_score = random.choices(top, weights=weights, k=1)[0]

    horizon = rule["horizon_days"]
    question = rule["template"].format(name=chosen_row.name, horizon=horizon)

    return {
        "category": category, "entity": chosen_row.__dict__,
        "horizon_days": horizon, "question": question, "selection_score": chosen_score,
    }


def generate_random_prediction(category: Optional[str] = None, mode: str = "short",
                                persist: bool = True) -> Dict[str, Any]:
    """End-to-end: select a candidate, then run it through
    ai.prediction_agent.run_prediction() (the same pipeline POST /api/predict
    uses) with source='agent'. Marks the entity as predicted in entities_db
    (for future novelty scoring) only when persist=True -- a dry run must not
    affect future novelty scoring, since nothing was actually recorded."""
    from . import prediction_agent  # local import: avoids a circular import at module load

    selection = select_candidate(category=category)
    entity = selection["entity"]
    row = entity

    import datetime
    start = datetime.date.today()
    end = start + datetime.timedelta(days=max(selection["horizon_days"], 1))

    payload = {
        "entity": row["name"], "entity_type": row["entity_type"],
        "question": selection["question"], "start_date": start.isoformat(),
        "end_date": end.isoformat(), "mode": mode, "source": "agent",
    }
    result = prediction_agent.run_prediction(payload, persist=persist)
    result["category"] = selection["category"]
    result["selection_score"] = selection["selection_score"]
    result["source"] = "agent"

    if persist and row.get("id") is not None:
        conn_ent = entities_db.get_connection()
        entities_db.mark_predicted(conn_ent, row["id"])

    return result
