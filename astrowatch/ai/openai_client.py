"""
Astrowatch Online -- OpenAI client wrapper.
==============================================
Single choke point for every OpenAI API call in this project. Responsibilities:

  1. Read OPENAI_API_KEY / OPENAI_MODEL / OPENAI_MAX_OUTPUT_TOKENS from the
     environment -- NEVER hard-code a key or a permanently-fixed model name.
  2. Fail gracefully (raise AIUnavailable, a plain, catchable exception -- never
     let an unconfigured key crash a request handler) when the key is missing,
     the `openai` package isn't installed, or the API call itself errors.
  3. Use the Responses API (client.responses.create), per the task spec, with
     a small structured-JSON-output helper for the callers in this package that
     need a strict schema back (entity_resolver, event_scanner) rather than free
     text.
  4. Centralize cost controls: every call goes through here, so max-output-length
     and model selection are configured once, not scattered across the package.

Astrowatch's core calculation functionality (kundli.py, mahadasha.py,
world_astrology/*, api.py's POST /api/chart) does not import this module and
keeps working with zero OpenAI configuration.
"""

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_MAX_OUTPUT_TOKENS = 1200


class AIUnavailable(Exception):
    """Raised whenever the AI layer cannot run -- missing key, missing package,
    or a failed API call. Callers (api.py route handlers) catch this and return
    a clear JSON error, never a fabricated reading. This is the ONE exception
    type every ai/ module should raise for "AI could not run" conditions, so
    api.py has a single except clause to handle them all consistently."""


def is_configured() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY"))


def get_model() -> str:
    """Configurable model -- read fresh from the environment on every call
    (not cached at import time) so changing OPENAI_MODEL doesn't require a
    process restart in dev, and so tests can monkeypatch the environment
    per-test without import-order issues."""
    return os.environ.get("OPENAI_MODEL") or DEFAULT_MODEL


def get_max_output_tokens() -> int:
    raw = os.environ.get("OPENAI_MAX_OUTPUT_TOKENS")
    if not raw:
        return DEFAULT_MAX_OUTPUT_TOKENS
    try:
        return int(raw)
    except ValueError:
        return DEFAULT_MAX_OUTPUT_TOKENS


def _client():
    if not is_configured():
        raise AIUnavailable(
            "OPENAI_API_KEY is not set. Astrowatch's calculation engine works "
            "fully without it; AI-synthesis features (prediction question "
            "understanding, entity resolution, current-event scanning, "
            "natural-language synthesis) require it. Set OPENAI_API_KEY (and "
            "optionally OPENAI_MODEL) in the environment or .env to enable them."
        )
    try:
        from openai import OpenAI
    except ImportError as e:
        raise AIUnavailable(
            "The 'openai' package is not installed. Run "
            "`pip install -r requirements.txt`."
        ) from e
    try:
        return OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    except Exception as e:  # noqa: BLE001 -- surfaced as AIUnavailable, not a crash
        raise AIUnavailable(f"Could not construct OpenAI client: {e}") from e


def complete_text(system_prompt: str, user_prompt: str,
                   max_output_tokens: Optional[int] = None) -> str:
    """Free-text completion via the Responses API. Used by synthesis.py for the
    final natural-language reading, where the shape of the output is prose, not
    strict JSON."""
    client = _client()
    try:
        resp = client.responses.create(
            model=get_model(),
            instructions=system_prompt,
            input=user_prompt,
            max_output_tokens=max_output_tokens or get_max_output_tokens(),
        )
    except Exception as e:  # noqa: BLE001
        raise AIUnavailable(f"OpenAI API call failed: {e}") from e
    text = getattr(resp, "output_text", None)
    if not text:
        raise AIUnavailable("OpenAI returned an empty response.")
    return text.strip()


def complete_json(system_prompt: str, user_prompt: str,
                   schema_name: str, schema: Dict[str, Any],
                   max_output_tokens: Optional[int] = None) -> Dict[str, Any]:
    """Structured-output completion via the Responses API's json_schema response
    format. Used by entity_resolver.py and event_scanner.py, which need a
    strict, predictable shape back (never free text that has to be re-parsed
    with regex) -- this is also a cost-control measure: constrained JSON output
    is shorter and more reliably parseable than asking a model to "reply in
    JSON" in prose and hoping."""
    client = _client()
    try:
        resp = client.responses.create(
            model=get_model(),
            instructions=system_prompt,
            input=user_prompt,
            max_output_tokens=max_output_tokens or get_max_output_tokens(),
            text={
                "format": {
                    "type": "json_schema",
                    "name": schema_name,
                    "schema": schema,
                    "strict": True,
                }
            },
        )
    except Exception as e:  # noqa: BLE001
        raise AIUnavailable(f"OpenAI structured-output call failed: {e}") from e
    text = getattr(resp, "output_text", None)
    if not text:
        raise AIUnavailable("OpenAI returned an empty structured response.")
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise AIUnavailable(f"OpenAI structured response was not valid JSON: {e}") from e
