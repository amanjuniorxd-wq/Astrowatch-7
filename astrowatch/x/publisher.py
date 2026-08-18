"""
Astrowatch Online -- X publishing orchestration.
====================================================
The ONLY entry point other code should call for publishing (api.py does not
call x/client.py directly). Responsibilities:

  1. Check X_ENABLED first, before anything else -- if not "true", this is a
     safe, cheap no-op (does not import x.client, does not touch credentials).
  2. Format an already-generated prediction (this module never generates
     prediction text itself -- it receives one from predictions_db, per task
     spec Section 23 "Receive an already-generated prediction").
  3. Never publish a duplicate: checks predictions_db.PredictionRecord.published
     before doing anything.
  4. Publish via x.client.post_tweet(), store the returned post id back onto
     the prediction row, and handle/report errors without crashing the
     caller (api.py / scheduler.py).
"""

import os
from typing import Any, Dict, Optional

import predictions_db

MAX_TWEET_LENGTH = 280
DISCLAIMER = "\n\nAstrological prediction -- not a scientific forecast."


def is_enabled() -> bool:
    return os.environ.get("X_ENABLED", "false").strip().lower() in ("1", "true", "yes")


def format_for_x(prediction_text: str, entity: str) -> str:
    """Formats an already-generated prediction for X, per task spec Section 18's
    example shape (emoji header + prediction + disclaimer), truncated to fit
    MAX_TWEET_LENGTH. Never adds new factual content -- only wraps/truncates
    what was already generated."""
    header = "\U0001f52e ASTROWATCH\n\n"
    budget = MAX_TWEET_LENGTH - len(header) - len(DISCLAIMER)
    body = prediction_text.strip()
    if len(body) > budget:
        body = body[: max(budget - 1, 0)].rstrip() + "…"
    return header + body + DISCLAIMER


def publish_prediction(prediction_id: str, conn=None) -> Dict[str, Any]:
    """Looks up the prediction, checks X_ENABLED + not-already-published,
    formats it, and publishes. Returns {"published": bool, "reason": str,
    "x_post_id": str|None}. Never raises for a routine 'disabled' or
    'already published' case -- those are expected, reportable outcomes, not
    exceptions; genuine API/credential failures ARE surfaced (caught by the
    caller) so they aren't silently swallowed."""
    if not is_enabled():
        return {"published": False, "reason": "X_ENABLED is not true.", "x_post_id": None}

    conn = conn or predictions_db.get_connection()
    record = predictions_db.get_prediction(conn, prediction_id)
    if record is None:
        return {"published": False, "reason": f"No prediction with id={prediction_id!r}.",
                "x_post_id": None}
    if record.published:
        return {"published": False,
                "reason": f"Already published as X post {record.x_post_id!r} -- refusing to "
                          f"post a duplicate.",
                "x_post_id": record.x_post_id}

    from . import client  # local import: only touched when actually publishing
    text = format_for_x(record.prediction, record.entity)
    try:
        response = client.post_tweet(text)
    except client.XClientError as e:
        return {"published": False, "reason": f"X publish failed: {e}", "x_post_id": None}

    post_id = (response.get("data") or {}).get("id")
    if not post_id:
        return {"published": False, "reason": f"X API response had no post id: {response}",
                "x_post_id": None}

    predictions_db.mark_published(conn, prediction_id, post_id)
    return {"published": True, "reason": "ok", "x_post_id": post_id}
