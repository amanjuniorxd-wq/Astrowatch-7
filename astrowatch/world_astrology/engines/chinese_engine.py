"""
Astrowatch World Astrology -- Chinese (BaZi / Four Pillars) computational engine.
===================================================================
Implements the Year Pillar and Month Pillar of BaZi (Four Pillars of
Destiny), using the SOLAR-TERM-based year/month boundaries this tradition
actually uses (Lichun for the year boundary, NOT January 1 or Chinese lunar
New Year; the 12 "Jie" solar terms for month boundaries) -- computed
precisely via Swiss Ephemeris solar longitude, not a fixed calendar-date
approximation.

Per Derek Walters, "The Complete Guide to Chinese Astrology" (2005 rev. ed.)
and the standard BaZi reference literature:

  1. Year Pillar: sexagenary (Stem+Branch) cycle from the proleptic Gan-Zhi
     year count, using Lichun (solar longitude 315 deg) as the year boundary.
     Verified against the well-documented fact that 1984 CE was a "Jiazi"
     (Stem 0, Branch 0) year -- the start of a 60-year cycle.
  2. Month Pillar branch: from which of the 12 solar-term ("Jie") 30-degree
     bands the birth falls in, starting from Lichun. Month Pillar stem: via
     the "Five Tigers" rule (wu hu dun), which derives the first month's
     (Yin/Tiger month) stem from the Year Stem, then increments by one stem
     per subsequent month branch -- a standard, widely documented mnemonic
     formula in BaZi literature.
  3. Chinese Zodiac animal (from Year Branch) and Wu Xing (Five Element) +
     Yin-Yang polarity of each Stem -- standard, uncontested mappings.

NO FABRICATION NOTE: the Day Pillar and Hour Pillar (and therefore the Da Yun
"Luck Cycle" decade pillars, which are counted relative to the Month Pillar
but whose starting AGE depends on precise days-to-solar-term counting from an
exact birth TIME, and whose forward/backward DIRECTION depends on the
entity's gender -- a field PredictionContext does not model) are NOT
implemented this session. The Day Pillar specifically requires a sexagenary
day-count epoch anchor (a specific historical date's known Stem-Branch); this
session could not independently verify a specific anchor date with enough
confidence to trust the offset constant, and guessing one risks a silently
wrong pillar for every calculation -- so it is marked not_implemented rather
than guessed. Zi Wei Dou Shu, Qi Men Dun Jia, and Tai Yi are separate,
substantially more complex systems not attempted this session.

Do NOT force this into Western zodiac-sign logic anywhere in this module --
Stems/Branches/solar-term bands are this tradition's own native framework.
"""

from typing import Any, Dict, List, Optional

from ..engine_interface import AstrologyEngine, PredictionContext, HistoricalStatus, PredictiveRule
from . import _shared
from kundli import compute_kundli
import coordinates

STEM_NAMES = ["Jia", "Yi", "Bing", "Ding", "Wu", "Ji", "Geng", "Xin", "Ren", "Gui"]
STEM_ELEMENT = {"Jia": "Wood", "Yi": "Wood", "Bing": "Fire", "Ding": "Fire", "Wu": "Earth",
                "Ji": "Earth", "Geng": "Metal", "Xin": "Metal", "Ren": "Water", "Gui": "Water"}
BRANCH_NAMES = ["Zi", "Chou", "Yin", "Mao", "Chen", "Si", "Wu", "Wei", "Shen", "You", "Xu", "Hai"]
ANIMALS = ["Rat", "Ox", "Tiger", "Rabbit", "Dragon", "Snake", "Horse", "Goat",
           "Monkey", "Rooster", "Dog", "Pig"]

# Five Tigers rule (wu hu dun yue): Year Stem (mod 5, since Jia/Ji share a row,
# etc.) -> Month Stem of the first (Yin/Tiger) BaZi month.
FIVE_TIGERS_FIRST_MONTH_STEM = {0: 2, 5: 2,   # Jia/Ji -> Bing
                                 1: 4, 6: 4,   # Yi/Geng -> Wu
                                 2: 6, 7: 6,   # Bing/Xin -> Geng
                                 3: 8, 8: 8,   # Ding/Ren -> Ren
                                 4: 0, 9: 0}   # Wu/Gui -> Jia

NOT_IMPLEMENTED_TECHNIQUES = {
    "day_pillar": "Requires a sexagenary day-count epoch anchor (a specific verified "
        "historical date's known Stem-Branch) that this session could not independently "
        "confirm with enough confidence to trust the offset constant -- an incorrect "
        "epoch would silently mis-date every Day Pillar. Not implemented rather than guessed.",
    "hour_pillar": "Depends on the Day Stem (via the 'Five Rats' rule) -- not implemented "
        "because Day Pillar is not implemented (see above).",
    "da_yun_luck_cycles": "Starting age depends on precise days-to-nearest-solar-term "
        "counting (computable) but DIRECTION (forward/backward) depends on the entity's "
        "gender, a field PredictionContext does not model -- not implemented this session.",
    "zi_wei_dou_shu": "A substantially more complex, separate divinatory system (Purple "
        "Star Astrology) with its own star-placement tables -- not attempted this session.",
    "qi_men_dun_jia": "A separate divinatory/strategic system with its own complex "
        "time-based board configuration -- not attempted this session.",
    "tai_yi": "A separate, rarer divinatory system -- not attempted this session; this "
        "project has no reliably sourced reconstruction of its calculation method.",
}

RULES: Dict[str, PredictiveRule] = {
    "chinese.year_pillar": PredictiveRule(
        rule_id="chinese.year_pillar", tradition="chinese", school="BaZi (Four Pillars of Destiny)",
        name="Year Pillar (Gan-Zhi)",
        description="Sexagenary Stem+Branch for the solar year containing the birth moment, "
                    "bounded by Lichun (solar longitude 315 deg), not January 1 or lunar New Year.",
        historical_source="Derek Walters, The Complete Guide to Chinese Astrology (2005); "
                          "standard BaZi reference literature. Verified against the documented "
                          "fact that 1984 CE was a Jiazi year.",
        calculation="solar_year = birth_year if birth_jd >= Lichun(birth_year) else "
                    "birth_year - 1; stem_idx = (solar_year - 4) mod 10; "
                    "branch_idx = (solar_year - 4) mod 12.",
        interpretation="The Year Pillar traditionally represents ancestry/early-life "
                       "background and (in mundane use) the year's overall thematic Stem/"
                       "Branch/Element/Animal.",
        prediction_domain=["natal", "mundane", "annual_timing"],
        historical_status=HistoricalStatus.DOCUMENTED.value, confidence="moderate",
    ),
    "chinese.month_pillar": PredictiveRule(
        rule_id="chinese.month_pillar", tradition="chinese", school="BaZi (Four Pillars of Destiny)",
        name="Month Pillar (Gan-Zhi)",
        description="Branch from which of the 12 solar-term ('Jie') 30-degree bands the "
                    "birth falls in (starting at Lichun); Stem via the Five Tigers rule "
                    "applied to the Year Stem.",
        historical_source="Standard BaZi reference literature (Five Tigers / wu hu dun yue mnemonic).",
        calculation="month_index_from_yin = floor(((sun_tropical_lon - 315) mod 360) / 30); "
                    "branch_idx = (2 + month_index_from_yin) mod 12; "
                    "stem_idx = (FIVE_TIGERS_FIRST_MONTH_STEM[year_stem_idx] + month_index_from_yin) mod 10.",
        interpretation="The Month Pillar traditionally represents parents/early adulthood "
                       "and, in this engine's mundane use, the current solar month's Element/Stem theme.",
        prediction_domain=["natal", "mundane", "monthly_timing"],
        historical_status=HistoricalStatus.DOCUMENTED.value, confidence="moderate",
    ),
}


def _sun_tropical_lon(jd: float) -> float:
    return compute_kundli(jd, 0.0, 0.0).grahas["sun"].tropical_lon_deg


def _solar_longitude_crossing_jd(target_lon: float, guess_jd: float) -> float:
    """Bisection search for the JD nearest guess_jd where the Sun's tropical
    longitude equals target_lon (mod 360). Search window +/-10 days."""
    def f(jd):
        diff = (_sun_tropical_lon(jd) - target_lon + 180.0) % 360.0 - 180.0
        return diff

    jd_lo, jd_hi = guess_jd - 10.0, guess_jd + 10.0
    f_lo, f_hi = f(jd_lo), f(jd_hi)
    if (f_lo > 0) == (f_hi > 0):
        # Widen search if the naive window didn't bracket a root.
        jd_lo, jd_hi = guess_jd - 20.0, guess_jd + 20.0
        f_lo, f_hi = f(jd_lo), f(jd_hi)
    for _ in range(60):
        jd_mid = (jd_lo + jd_hi) / 2.0
        f_mid = f(jd_mid)
        if (f_mid > 0) == (f_lo > 0):
            jd_lo, f_lo = jd_mid, f_mid
        else:
            jd_hi, f_hi = jd_mid, f_mid
    return (jd_lo + jd_hi) / 2.0


def _pillar(stem_idx: int, branch_idx: int) -> Dict[str, Any]:
    stem = STEM_NAMES[stem_idx % 10]
    branch = BRANCH_NAMES[branch_idx % 12]
    return {
        "stem": stem, "branch": branch, "element": STEM_ELEMENT[stem],
        "polarity": "Yang" if stem_idx % 2 == 0 else "Yin",
        "animal": ANIMALS[branch_idx % 12],
    }


class ChineseEngine(AstrologyEngine):
    tradition_name = "chinese"

    def is_applicable(self, context: PredictionContext) -> bool:
        return True

    def calculate(self, context: PredictionContext) -> Dict[str, Any]:
        birth_jd = _shared.context_jd_ut(context)
        y, m, d = (int(x) for x in context.birth_or_inception_date.split("-"))

        # Lichun of the birth's Gregorian calendar year (guess ~Feb 4).
        lichun_guess = coordinates.julian_day(y, 2, 4, 0.0)
        lichun_jd = _solar_longitude_crossing_jd(315.0, lichun_guess)
        solar_year = y if birth_jd >= lichun_jd else y - 1

        year_stem_idx = (solar_year - 4) % 10
        year_branch_idx = (solar_year - 4) % 12
        year_pillar = _pillar(year_stem_idx, year_branch_idx)

        birth_sun_lon = _sun_tropical_lon(birth_jd)
        month_index_from_yin = int(((birth_sun_lon - 315.0) % 360.0) // 30.0)
        month_branch_idx = (2 + month_index_from_yin) % 12
        month_stem_idx = (FIVE_TIGERS_FIRST_MONTH_STEM[year_stem_idx] + month_index_from_yin) % 10
        month_pillar = _pillar(month_stem_idx, month_branch_idx)

        return {
            "zodiac_system": "N/A (sexagenary Stem-Branch system, not a zodiac-sign system)",
            "calendar_system": "Chinese solar-term (Jie) calendar for pillar boundaries",
            "coordinate_system": "ecliptic (solar longitude used for term boundaries)",
            "ayanamsha": "N/A", "epoch": context.birth_or_inception_date,
            "solar_year": solar_year, "lichun_date": _shared.jd_to_iso_date(lichun_jd),
            "year_pillar": year_pillar, "month_pillar": month_pillar,
            "time_accuracy": context.time_accuracy,
        }

    def interpret(self, calculation: Dict[str, Any]) -> Dict[str, Any]:
        yp, mp = calculation["year_pillar"], calculation["month_pillar"]
        themes: List[str] = [
            f"Year Pillar {yp['stem']}-{yp['branch']} ({yp['polarity']} {yp['element']}, "
            f"Year of the {yp['animal']})",
            f"Month Pillar {mp['stem']}-{mp['branch']} ({mp['polarity']} {mp['element']})",
        ]
        factors = [
            {"name": "Year Pillar", "value": f"{yp['stem']}-{yp['branch']}", "rule_id": "chinese.year_pillar"},
            {"name": "Year Element/Polarity", "value": f"{yp['polarity']} {yp['element']}", "rule_id": "chinese.year_pillar"},
            {"name": "Chinese Zodiac Animal", "value": yp["animal"], "rule_id": "chinese.year_pillar"},
            {"name": "Month Pillar", "value": f"{mp['stem']}-{mp['branch']}", "rule_id": "chinese.month_pillar"},
            {"name": "Month Element/Polarity", "value": f"{mp['polarity']} {mp['element']}", "rule_id": "chinese.month_pillar"},
        ]
        prediction_text = (
            f"Chinese (BaZi) reading: Year Pillar {yp['stem']}-{yp['branch']} "
            f"({yp['polarity']} {yp['element']}, Year of the {yp['animal']}); "
            f"Month Pillar {mp['stem']}-{mp['branch']} ({mp['polarity']} {mp['element']})."
        )
        limitations = [
            "Only Year and Month Pillars are computed. Day Pillar, Hour Pillar, and Da Yun "
            "(Luck Cycle) decade pillars are not implemented this session -- see "
            "NOT_IMPLEMENTED_TECHNIQUES for why (epoch-anchor confidence and gender-field gaps).",
        ]
        if calculation.get("time_accuracy") != "documented":
            limitations.append("Birth/inception time was assumed (midnight); this does not "
                              "affect Year/Month Pillar (which use solar longitude, not clock "
                              "time) except in the rare case a birth falls within hours of a "
                              "Lichun/solar-term boundary.")
        return {
            "themes": themes, "factors": factors,
            "rules_used": ["chinese.year_pillar", "chinese.month_pillar"],
            "prediction_text": prediction_text, "signal_strength": None,
            "historical_status": HistoricalStatus.DOCUMENTED.value,
            "limitations": limitations, "time_window": None,
        }
