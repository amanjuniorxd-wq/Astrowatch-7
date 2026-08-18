"""
Astrowatch World Astrology -- corpus pattern lookup.

Loads the real, already-computed field-by-field structural pattern from
kundli_mass/multi_tradition_archetype_patterns.json (produced by
kundli_mass/analyze_multi_tradition_archetypes.py against the full 1305-person
famous_people_corpus.py) and exposes one function, compare_to_corpus(), that
reading_engine.py's full-horoscope narrative uses to add a real, sourced
comparison sentence: "how does this chart's 10th-lord dignity compare to the
base rate observed across N real charted people in the same field."

ONLY the Jyotisha dignity numbers are used here, deliberately -- the
Hellenistic sect numbers in that same JSON file are explicitly documented (see
MULTI_TRADITION_ARCHETYPE_REPORT.md's "CRITICAL CAVEAT" section) as confounded
by the ASSUMED_NOON birth-time convention used for the vast majority of that
corpus, and are NOT treated as a real per-field pattern. Using them here would
smuggle a known-artifact statistic into a live reading as if it were a real
finding, which is exactly what that caveat exists to prevent.
"""
import json
import os
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
PATTERNS_JSON = os.path.normpath(os.path.join(HERE, "..", "kundli_mass",
                                                "multi_tradition_archetype_patterns.json"))

_cache = None


def _load():
    global _cache
    if _cache is None:
        if not os.path.exists(PATTERNS_JSON):
            _cache = {}
        else:
            with open(PATTERNS_JSON) as f:
                _cache = json.load(f)
    return _cache


VALID_FIELDS = {"ACTOR", "MUSICIAN", "ATHLETE", "SCIENTIST", "BUSINESS", "AUTHOR", "ARTIST_DIRECTOR"}


def compare_to_corpus(field: str, this_chart_dignity: str) -> Optional[str]:
    """Returns a sourced, human-readable comparison sentence, or None if the
    field isn't recognized or the pattern data isn't available (e.g. the
    analysis script hasn't been run in this environment) -- callers must
    handle None gracefully rather than assume this always succeeds."""
    data = _load()
    if not data or field not in VALID_FIELDS:
        return None
    field_key = field.upper()
    jy = data.get("tenth_dignity_jyotisha", {}).get(field_key)
    n = data.get("n_by_field", {}).get(field_key)
    if not jy or not n:
        return None

    well_dignified = jy.get("EXALTED", 0) + jy.get("OWN_SIGN", 0)
    rate = well_dignified / n * 100.0
    this_is_well = this_chart_dignity in ("EXALTED", "OWN_SIGN")

    return (
        f"For comparison: across {n} real, individually-charted people in this project's "
        f"{field_key.title().replace('_', ' ')} corpus, the 10th-house lord is exalted or in "
        f"its own sign (a traditionally favorable career-house placement) in {rate:.0f}% of "
        f"charts. This chart's own 10th-lord dignity ({this_chart_dignity.lower().replace('_',' ')}) "
        + ("falls into that favorably-dignified group." if this_is_well else
           "does not fall into that favorably-dignified group -- for whatever that's worth against "
           "a base rate that, it should be said, is itself not a validated predictor of anything, "
           "just an observed distribution across this specific corpus.")
    )
