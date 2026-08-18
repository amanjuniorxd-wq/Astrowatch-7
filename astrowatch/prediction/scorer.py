"""
prediction/scorer.py
=====================
Configurable weighted combiner: turns a per-candidate feature dict into a
single scalar score, and turns a set of candidate scores into normalized
(but NOT claimed-calibrated) model scores.

MODEL_CONFIG below reproduces the exact weight dict given in this project's
own build spec, verbatim:
    {"dasha": 0.20, "dasha_lord_strength": 0.15, "antardasha": 0.10,
     "transit": 0.20, "moon_activation": 0.10, "entity_chart": 0.10,
     "event_chart": 0.10, "key_personnel": 0.05}

THESE ARE INITIAL WEIGHTS ONLY. They are NOT empirically optimized, NOT
derived from the exploratory pattern analysis in
kundli_mass/CRICKET_DASHA_PATTERN_ANALYSIS.md (that analysis found no strong
single-feature signal on this project's 806-match corpus and is explicitly
NOT used to inflate any weight here -- see that file's closing section), and
NOT validated by any backtest at the time this file was written. Changing
them requires walk-forward backtest evidence (event_backtest/) showing a
real accuracy/Brier/log-loss improvement, documented in BACKTEST.md.

Resolving an ambiguity in the spec's example dict: "dasha" and
"dasha_lord_strength" are both dasha-related keys with no further
definition given. This module resolves them as two DISTINCT signals so
neither key is redundant:
  - "dasha":              is the active Mahadasha lord a natural JYOTISHA
                           benefic (Jupiter/Venus/Mercury/Moon) vs malefic
                           (Sun/Mars/Saturn/Rahu/Ketu)? Graded 1.0/0.0.
  - "dasha_lord_strength": the Mahadasha lord's sign+house DIGNITY score
                           (exalted/own-sign/debilitated/etc, normalized
                           0..1) -- independent of whether it's a natural
                           benefic or malefic.
  - "antardasha":          the Antardasha lord's dignity score (mirrors
                           dasha_lord_strength, one dasha level finer).
This resolution is a documented judgment call, not a value found in the
spec text itself.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional

from world_astrology import dignity_tables as dt
from prediction.features import EntityFeatureSet

MODEL_CONFIG: Dict[str, float] = {
    "dasha": 0.20,
    "dasha_lord_strength": 0.15,
    "antardasha": 0.10,
    "transit": 0.20,
    "moon_activation": 0.10,
    "entity_chart": 0.10,
    "event_chart": 0.10,
    "key_personnel": 0.05,
}
assert abs(sum(MODEL_CONFIG.values()) - 1.0) < 1e-9, "MODEL_CONFIG weights must sum to 1.0"

MODEL_VERSION = "vedic-weighted-v1"

# Ablation variants: name -> subset of MODEL_CONFIG feature keys included.
# Weights are RENORMALIZED to sum to 1.0 over only the included subset (see
# score_candidate()'s renormalization logic) -- not simply zeroed out, which
# would silently shrink every score toward 0 rather than really comparing
# "what if we only had this information."
MODEL_VARIANTS: Dict[str, List[str]] = {
    "vedic-core":       ["dasha", "dasha_lord_strength", "antardasha"],
    "vedic-transit":    ["dasha", "dasha_lord_strength", "antardasha", "transit", "moon_activation"],
    "vedic-entity":     ["dasha", "dasha_lord_strength", "antardasha", "transit", "moon_activation", "entity_chart"],
    "vedic-event":      ["dasha", "dasha_lord_strength", "antardasha", "transit", "moon_activation",
                          "entity_chart", "event_chart"],
    "complete":         list(MODEL_CONFIG.keys()),
}


def _dasha_benefic_score(mahadasha_lord: Optional[str]) -> Optional[float]:
    if mahadasha_lord is None:
        return None
    return 1.0 if mahadasha_lord in dt.JYOTISHA_BENEFICS else 0.0


def _feature_value(features: EntityFeatureSet, key: str) -> Optional[float]:
    if key == "dasha":
        return _dasha_benefic_score(features.mahadasha_lord)
    if key == "dasha_lord_strength":
        return features.mahadasha_lord_score
    if key == "antardasha":
        return features.antardasha_lord_score
    if key == "transit":
        return features.transit_strength
    if key == "moon_activation":
        return features.moon_activation
    if key == "entity_chart":
        return features.entity_chart_strength
    if key == "event_chart":
        return features.event_chart_strength
    if key == "key_personnel":
        return features.key_personnel_strength
    raise ValueError(f"Unknown MODEL_CONFIG feature key: {key!r}")


@dataclass
class ScoreResult:
    candidate_id: str
    raw_score: Optional[float]     # None if EVERY feature in the variant was missing
    weights_used: Dict[str, float]  # renormalized weights actually applied
    missing_features: List[str]


def score_candidate(features: EntityFeatureSet, model_variant: str = "complete") -> ScoreResult:
    """Combines features into one weighted scalar in [0, 1] (since every
    component feature is itself normalized to [0, 1] -- see features.py).
    Missing components are EXCLUDED and remaining weights renormalized to
    sum to 1.0, rather than treated as 0 (which would silently penalize a
    candidate for missing data rather than just reducing confidence, and
    would NOT be honest per this project's "reduce confidence, don't
    silently substitute a value" rule)."""
    if model_variant not in MODEL_VARIANTS:
        raise ValueError(f"Unknown model_variant {model_variant!r}. Options: {list(MODEL_VARIANTS)}")
    keys = MODEL_VARIANTS[model_variant]

    available: Dict[str, float] = {}
    missing: List[str] = []
    for key in keys:
        value = _feature_value(features, key)
        if value is None:
            missing.append(key)
        else:
            available[key] = value

    if not available:
        return ScoreResult(candidate_id=features.candidate_id, raw_score=None,
                            weights_used={}, missing_features=missing)

    base_weight_sum = sum(MODEL_CONFIG[k] for k in available)
    weights_used = {k: MODEL_CONFIG[k] / base_weight_sum for k in available}
    raw_score = sum(weights_used[k] * available[k] for k in available)
    return ScoreResult(candidate_id=features.candidate_id, raw_score=raw_score,
                        weights_used=weights_used, missing_features=missing)


def normalize_scores(scores: Dict[str, Optional[float]]) -> Optional[Dict[str, float]]:
    """Turns raw per-candidate scores into normalized model scores summing
    to 1.0. These are NOT probabilities in the calibrated sense -- see
    predictor.py, which labels them 'probabilities_are_calibrated=False'
    unless/until calibration.py demonstrates otherwise on real backtest
    data. Returns None if every candidate's score is None (fully
    INSUFFICIENT_DATA)."""
    valid = {cid: s for cid, s in scores.items() if s is not None}
    if not valid:
        return None
    total = sum(valid.values())
    if total <= 0:
        # Numerical safeguard: all-zero or degenerate scores -- fall back to
        # a uniform distribution over candidates with a valid (non-None)
        # score rather than dividing by zero or fabricating a preference.
        n = len(valid)
        return {cid: 1.0 / n for cid in valid}
    return {cid: s / total for cid, s in valid.items()}
