"""
Astrowatch World Astrology -- Japanese computational engine.
===================================================================
Implements Nine Star Ki (Kyusei, based on the Chinese Lo Shu magic-square
numerology adopted into Japanese Onmyodo-adjacent popular astrology), using
the year-boundary convention (Risshun/Lichun, the same solar-term boundary
BaZi uses -- Nine Star Ki descends from the same Chinese solar-calendar
tradition) already computed by chinese_engine.py, reused here rather than
re-derived.

Formula source: the digital-root year formula below is consistently
published across modern Nine Star Ki / Kyusei reference works (e.g. books by
Michio Kushi and other 20th-century popularizers of the system in the West),
but this session could not independently trace it to a single primary
pre-modern source -- marked historical_status="traditional" rather than
"documented" for this reason, with confidence="low".

NOT implemented: Onmyodo ritual/directional timing (kimon direction-taboo
calculations, specific date-selection rituals) -- a substantially larger,
separately-sourced body of technique this session did not attempt; the
monthly/daily Nine Star Ki cycle (only the annual star is computed here).
"""

from typing import Any, Dict, List

from ..engine_interface import AstrologyEngine, PredictionContext, HistoricalStatus, PredictiveRule
from . import _shared
from .chinese_engine import ChineseEngine

STAR_ELEMENT = {
    1: "Water", 2: "Earth", 3: "Wood", 4: "Wood", 5: "Earth",
    6: "Metal", 7: "Metal", 8: "Earth", 9: "Fire",
}
STAR_NAMES = {  # traditional color-number naming convention
    1: "Ichihaku (One White)", 2: "Jikoku (Two Black)", 3: "Sanpeki (Three Jade/Indigo)",
    4: "Rokuroku (Four Green)", 5: "Goo (Five Yellow)", 6: "Roppaku (Six White)",
    7: "Shichisei (Seven Red)", 8: "Hakuji (Eight White)", 9: "Kyushi (Nine Purple)",
}

NOT_IMPLEMENTED_TECHNIQUES = {
    "monthly_daily_star": "Only the annual Nine Star Ki number is computed; the monthly and "
        "daily star cycles (used for finer-grained timing in the living tradition) are not "
        "implemented this session.",
    "onmyodo_directional_timing": "Kimon (direction-taboo) calculations and date-selection "
        "rituals are a substantially larger, separately-sourced body of technique -- not "
        "attempted this session.",
    "gogyo_directional_compatibility": "Full Five-Element directional/compatibility charts "
        "built on top of the annual star are not implemented -- only the star number and its "
        "own element are reported.",
}

RULES: Dict[str, PredictiveRule] = {
    "japanese.nine_star_ki": PredictiveRule(
        rule_id="japanese.nine_star_ki", tradition="japanese", school="Kyusei (Nine Star Ki)",
        name="Nine Star Ki annual number",
        description="Digital-root-of-birth-year formula (year boundary at Risshun/Lichun, "
                    "reusing the Chinese engine's already-computed solar year) yielding a "
                    "number 1-9, each mapped to a Wu-Xing-derived element via the Lo Shu "
                    "magic square association.",
        historical_source="Consistently published in modern Nine Star Ki / Kyusei reference "
                          "works (e.g. Michio Kushi's popularizations); exact pre-modern "
                          "primary-source lineage not independently traced this session.",
        calculation="digital_root(solar_year) via repeated digit-summing (9 stays 9); "
                    "star = 11 - digital_root, wrapped to 1 if the result is 10.",
        interpretation="Each of the 9 stars carries a traditional element/personality "
                       "association; used for annual and directional forecasting.",
        prediction_domain=["natal", "annual_timing"],
        historical_status=HistoricalStatus.TRADITIONAL.value, confidence="low",
    ),
}


def _digital_root(n: int) -> int:
    n = abs(n)
    while n > 9:
        n = sum(int(c) for c in str(n))
    return n


class JapaneseEngine(AstrologyEngine):
    tradition_name = "japanese"

    def is_applicable(self, context: PredictionContext) -> bool:
        return True

    def calculate(self, context: PredictionContext) -> Dict[str, Any]:
        chinese_result = ChineseEngine().calculate(context)
        solar_year = chinese_result["solar_year"]
        dr = _digital_root(solar_year)
        star = 11 - dr
        if star == 10:
            star = 1
        return {
            "zodiac_system": "N/A (Lo Shu magic-square numerology, not a zodiac-sign system)",
            "calendar_system": "Solar-term (Risshun) year boundary, reused from Chinese engine",
            "coordinate_system": "N/A", "ayanamsha": "N/A",
            "epoch": context.birth_or_inception_date,
            "solar_year": solar_year, "digital_root": dr,
            "star_number": star, "star_name": STAR_NAMES[star], "star_element": STAR_ELEMENT[star],
            "time_accuracy": context.time_accuracy,
        }

    def interpret(self, calculation: Dict[str, Any]) -> Dict[str, Any]:
        themes = [f"{calculation['star_name']} ({calculation['star_element']})"]
        factors = [
            {"name": "Nine Star Ki number", "value": calculation["star_number"], "rule_id": "japanese.nine_star_ki"},
            {"name": "Star name", "value": calculation["star_name"], "rule_id": "japanese.nine_star_ki"},
            {"name": "Star element", "value": calculation["star_element"], "rule_id": "japanese.nine_star_ki"},
        ]
        prediction_text = (
            f"Japanese (Nine Star Ki) reading: {calculation['star_name']}, "
            f"element {calculation['star_element']}."
        )
        limitations = [
            "Only the annual Nine Star Ki number is computed. Monthly/daily star cycles and "
            "Onmyodo directional-timing technique are not implemented -- see NOT_IMPLEMENTED_TECHNIQUES.",
            "The digital-root formula is consistently published in modern reference works but "
            "its exact pre-modern textual lineage was not independently verified this session "
            "-- marked 'traditional', not 'documented'.",
        ]
        return {
            "themes": themes, "factors": factors, "rules_used": ["japanese.nine_star_ki"],
            "prediction_text": prediction_text, "signal_strength": None,
            "historical_status": HistoricalStatus.TRADITIONAL.value,
            "limitations": limitations, "time_window": None,
        }
