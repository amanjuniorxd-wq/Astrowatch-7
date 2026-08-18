"""
Astrowatch Online -- final synthesis.
========================================
Turns ALREADY-COMPUTED structured Astrowatch results (from ai/tools.py, which
in turn wraps kundli.py/world_astrology/*/forecast.py) into natural-language
prose. This module never adds a new fact -- prompts.synthesis_user_prompt()
serializes the structured results as the ONLY factual input, and the shared
SYSTEM_PROMPT (Section 30/31 integrity rules) instructs the model not to
introduce anything beyond it. Astrological calculation stays fully separate
from this synthesis step (task spec Section 17): callers keep the raw
structured dict AND the prose separately, never merged into one opaque blob.
"""

from typing import Any, Dict, List, Optional

from . import openai_client, prompts


SHORT_SYNTHESIS_SUFFIX = (
    "\n\nWrite this as a SHORT prediction, at most 240 characters, suitable "
    "for a social-media post. End with a one-line disclaimer that this is an "
    "astrological prediction, not a scientific forecast, if space allows."
)

DETAILED_SYNTHESIS_SUFFIX = (
    "\n\nWrite a DETAILED synthesis prose section covering: agreement between "
    "traditions, disagreement between traditions, the strongest recurring "
    "theme, and explicit limitations/insufficient-data notes. Do not repeat "
    "the raw structured data verbatim -- interpret it."
)


def synthesize(question: str, structured_results: Dict[str, Any],
               mode: str = "detailed") -> str:
    """mode: 'short' | 'detailed'. Raises AIUnavailable if OpenAI isn't
    configured -- callers must handle that (return the raw structured_results
    with a note, never a fabricated prose reading) rather than let it crash."""
    suffix = SHORT_SYNTHESIS_SUFFIX if mode == "short" else DETAILED_SYNTHESIS_SUFFIX
    user_prompt = prompts.synthesis_user_prompt(question, structured_results) + suffix
    max_tokens = 200 if mode == "short" else None  # short mode: hard cost/length cap
    return openai_client.complete_text(prompts.SYSTEM_PROMPT, user_prompt,
                                        max_output_tokens=max_tokens)


def build_final_result(question: str, entities: List[str], structured_results: Dict[str, Any],
                        traditions_used: List[str], time_window: Optional[str] = None,
                        mode: str = "detailed") -> Dict[str, Any]:
    """Assembles the structured final-result shape from task spec Section 17.
    Calculation (structured_results) and AI synthesis (primary_prediction etc.)
    are kept as separate top-level keys, never merged into one field."""
    agreement = structured_results.get("cross_tradition", {}).get("agreement_classification")
    jy_score = structured_results.get("cross_tradition", {}).get("jyotisha_score")
    he_score = structured_results.get("cross_tradition", {}).get("hellenistic_score")

    supporting_factors, limitations = [], []
    if agreement:
        supporting_factors.append(f"Jyotisha/Hellenistic cross-tradition agreement: {agreement}")
    if jy_score is not None:
        supporting_factors.append(f"Jyotisha dignity score: {jy_score:+.1f}")
    if he_score is not None:
        supporting_factors.append(f"Hellenistic dignity score: {he_score:+.1f}")

    entity_chart = structured_results.get("entity_chart", {})
    if entity_chart.get("time_accuracy") and entity_chart["time_accuracy"] != "documented":
        limitations.append(
            f"Birth/inception time was not documented and was assumed "
            f"({entity_chart['time_accuracy']}) -- Ascendant and house-based "
            f"findings carry real extra uncertainty."
        )
    if not agreement or agreement in ("Insufficient", "Tradition-specific"):
        limitations.append(
            "Cross-tradition signal is weak or not comparable for this "
            "reading -- treat the prediction as tentative."
        )
    uncomputed = structured_results.get("cross_tradition", {}).get("all_cataloged_traditions", [])
    computed = structured_results.get("cross_tradition", {}).get("computed_traditions", [])
    if uncomputed and computed:
        skipped = [t for t in uncomputed if t not in computed]
        if skipped:
            limitations.append(
                f"The following traditions are catalogued but not computed in "
                f"this reading: {', '.join(skipped)}."
            )

    try:
        primary = synthesize(question, structured_results, mode=mode)
        secondary = None
        model_score = 0.5
        if agreement == "Strong":
            model_score = 0.75
        elif agreement == "Contradictory":
            model_score = 0.3
        elif agreement in ("Insufficient", None):
            model_score = 0.2
        status = "ok"
    except openai_client.AIUnavailable as e:
        primary = None
        secondary = None
        model_score = None
        status = "insufficient_data"
        limitations.append(f"AI synthesis unavailable: {e}")

    return {
        "status": status,
        "question": question,
        "primary_prediction": primary,
        "secondary_prediction": secondary,
        "time_window": time_window,
        "entities": entities,
        "traditions_used": traditions_used,
        "agreement": [agreement] if agreement else [],
        "disagreement": [agreement] if agreement == "Contradictory" else [],
        "supporting_factors": supporting_factors,
        "limitations": limitations,
        "model_score": model_score,
        "calculation_data": structured_results,
    }
