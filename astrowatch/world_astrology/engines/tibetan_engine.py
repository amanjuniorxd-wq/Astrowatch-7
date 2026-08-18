"""
Astrowatch World Astrology -- Tibetan computational engine.
===================================================================
Implements the Tibetan Elemental Year (part of the "Rabjung" 60-year cycle
system), which the Tibetan calendar adopted from the Chinese sexagenary
Stem-Branch system starting 1027 CE, keeping the SAME year-to-cycle-position
correspondence (this synchronization is well documented -- e.g. Svante
Janson, "Tibetan Calendar Mathematics" (2014); Edward Henning's Kalacakra
calendar studies) -- only the labels differ (5 Elements + Male/Female
polarity instead of the 10 Chinese Stem names; the same 12 animals).

Rather than re-deriving the sexagenary position from a separately-recalled
epoch constant (which would duplicate world_astrology/engines/chinese_engine.py's
already-verified computation and risk a second, independent source of error),
this engine explicitly REUSES ChineseEngine's Year Pillar Stem/Branch indices
and relabels them with the Tibetan Element+Polarity+Animal names -- since
both traditions are computing the identical underlying 60-year position.

NOT implemented (see NOT_IMPLEMENTED_TECHNIQUES): the deeper Phugpa/Tsurphu
astronomical calendar systems (true-longitude planetary/lunar calculations
with tradition-specific correction tables), which require specialized
astronomical tables this project does not have; Month/Day-level Tibetan
calendrical calculation (the Tibetan lunar month/day system has irregular
leap-month and skipped/doubled-day rules requiring a dedicated ephemeris this
project has not built).
"""

from typing import Any, Dict, List

from ..engine_interface import AstrologyEngine, PredictionContext, HistoricalStatus, PredictiveRule
from .chinese_engine import ChineseEngine

# Same 10-position cycle as Chinese Stems, relabeled: 2 consecutive years per
# Element (Male year then Female year), matching Jia/Yi=Wood etc. exactly.
TIBETAN_ELEMENT = {"Jia": "Wood", "Yi": "Wood", "Bing": "Fire", "Ding": "Fire", "Wu": "Earth",
                    "Ji": "Earth", "Geng": "Iron", "Xin": "Iron", "Ren": "Water", "Gui": "Water"}
TIBETAN_ANIMAL = {  # identical animal cycle/order to the Chinese Branch, per the shared
                    # Sino-Tibetan sexagenary correspondence.
    "Zi": "Rat", "Chou": "Ox", "Yin": "Tiger", "Mao": "Rabbit", "Chen": "Dragon", "Si": "Snake",
    "Wu": "Horse", "Wei": "Sheep", "Shen": "Monkey", "You": "Bird", "Xu": "Dog", "Hai": "Pig",
}

NOT_IMPLEMENTED_TECHNIQUES = {
    "phugpa_tsurphu_astronomy": "The two main Tibetan astronomical-calendar schools (Phugpa "
        "and Tsurphu) compute true planetary/lunar longitudes via their own tradition-specific "
        "mean-motion and correction tables -- this project does not have those tables sourced; "
        "not implemented this session.",
    "tibetan_month_day": "The Tibetan lunar calendar has irregular leap-month insertion and "
        "skipped/doubled-day rules (tied to the true-longitude calculations above) -- not "
        "implemented this session, dependent on the same missing tables.",
    "elemental_compatibility": "Traditional Element/Animal-based compatibility and 'life force' "
        "(lungta) systems build on the Elemental Year computed here but add further rules this "
        "session did not independently verify against a primary source -- not implemented.",
}

RULES: Dict[str, PredictiveRule] = {
    "tibetan.elemental_year": PredictiveRule(
        rule_id="tibetan.elemental_year", tradition="tibetan", school="Rabjung 60-year cycle",
        name="Elemental Year (Element + Polarity + Animal)",
        description="The Tibetan calendar's 60-year Rabjung cycle shares its year-to-position "
                    "correspondence with the Chinese sexagenary cycle (adopted 1027 CE); this "
                    "rule reuses chinese_engine.ChineseEngine's Year Pillar computation and "
                    "relabels it with the Tibetan Element (Wood/Fire/Earth/Iron/Water) + "
                    "Male/Female polarity + Animal names.",
        historical_source="Svante Janson, Tibetan Calendar Mathematics (2014); Edward Henning's "
                          "Kalacakra calendar studies, on the documented Sino-Tibetan sexagenary "
                          "synchronization.",
        calculation="See chinese_engine.py's chinese.year_pillar rule; Stem->Element via "
                    "TIBETAN_ELEMENT, Branch->Animal via TIBETAN_ANIMAL (identical animal cycle).",
        interpretation="The Elemental Year is traditionally used for annual astrological "
                       "themes and compatibility calculations.",
        prediction_domain=["natal", "mundane", "annual_timing"],
        historical_status=HistoricalStatus.DOCUMENTED.value, confidence="moderate",
    ),
}


class TibetanEngine(AstrologyEngine):
    tradition_name = "tibetan"

    def is_applicable(self, context: PredictionContext) -> bool:
        return True

    def calculate(self, context: PredictionContext) -> Dict[str, Any]:
        chinese_result = ChineseEngine().predict(context)
        # Pull the underlying stem/branch names back out of the Chinese engine's
        # factor list (avoids recomputing -- single source of truth for the
        # sexagenary position).
        year_pillar_factor = next(f for f in chinese_result.factors if f["name"] == "Year Pillar")
        stem_name, branch_name = year_pillar_factor["value"].split("-")
        polarity = "Male" if stem_name in ("Jia", "Bing", "Wu", "Geng", "Ren") else "Female"

        return {
            "zodiac_system": "N/A (Element-Animal sexagenary system, not a zodiac-sign system)",
            "calendar_system": "Rabjung 60-year cycle (shared Sino-Tibetan sexagenary position)",
            "coordinate_system": "N/A", "ayanamsha": "N/A",
            "epoch": context.birth_or_inception_date,
            "element": TIBETAN_ELEMENT[stem_name], "polarity": polarity,
            "animal": TIBETAN_ANIMAL[branch_name],
            "chinese_stem": stem_name, "chinese_branch": branch_name,
            "time_accuracy": context.time_accuracy,
        }

    def interpret(self, calculation: Dict[str, Any]) -> Dict[str, Any]:
        themes = [f"{calculation['polarity']} {calculation['element']} {calculation['animal']} Year"]
        factors = [
            {"name": "Elemental Year", "value": f"{calculation['polarity']} {calculation['element']} {calculation['animal']}",
             "rule_id": "tibetan.elemental_year"},
        ]
        prediction_text = (
            f"Tibetan reading: {calculation['polarity']} {calculation['element']} {calculation['animal']} Year "
            f"(shared sexagenary position with Chinese {calculation['chinese_stem']}-{calculation['chinese_branch']})."
        )
        limitations = [
            "Only the Elemental Year (reused from the Chinese engine's already-verified Year "
            "Pillar) is computed. Phugpa/Tsurphu true-longitude astronomy and Tibetan lunar "
            "month/day calculation are not implemented -- see NOT_IMPLEMENTED_TECHNIQUES.",
        ]
        return {
            "themes": themes, "factors": factors, "rules_used": ["tibetan.elemental_year"],
            "prediction_text": prediction_text, "signal_strength": None,
            "historical_status": HistoricalStatus.DOCUMENTED.value,
            "limitations": limitations, "time_window": None,
        }
