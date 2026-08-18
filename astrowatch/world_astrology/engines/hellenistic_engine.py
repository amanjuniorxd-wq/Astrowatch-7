"""
Astrowatch World Astrology -- Hellenistic computational engine.
===================================================================
Extends this project's existing Hellenistic computation (dignity + sect,
world_astrology/dignity_tables.py + reading_engine.py) with three further
documented Hellenistic (Greco-Roman, 1st-7th century CE) techniques, per
Chris Brennan's "Hellenistic Astrology" (2017) synthesis of the primary
sources (Vettius Valens' Anthology, Dorotheus of Sidon's Carmen
Astrologicum, Ptolemy's Tetrabiblos) unless noted otherwise:

  1. Annual Profections -- the whole-sign "profected Ascendant" that
     advances one sign per year of age; its ruler is the "Lord of the Year".
  2. Lot of Fortune and Lot of Spirit -- the two primary Hermetic Lots,
     sect-dependent formulas.
  3. Zodiacal Releasing from Fortune (L1/major periods only) -- the
     chronocrator (time-lord) technique of walking forward through the signs
     from the Lot of Fortune, each sign's period length set by its ruling
     planet's classical "years" value.

Zodiacal Releasing's exact algorithmic reconstruction (loosing-of-the-bond
transitions, L2/L3/L4 sub-periods, peak periods) has real scholarly
reconstruction involved (marked historical_status="reconstructed" rather than
"documented") -- this engine implements the L1 (major period) backbone only,
which is the least disputed part of the technique.

Horary and full electional technique are NOT implemented -- see
NOT_IMPLEMENTED_TECHNIQUES.
"""

from typing import Any, Dict, List

from ..engine_interface import AstrologyEngine, PredictionContext, HistoricalStatus, PredictiveRule
from .. import dignity_tables as dt
from . import _shared

RASHI_NAMES = ["Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya",
               "Tula", "Vrischika", "Dhanu", "Makara", "Kumbha", "Meena"]
WESTERN_SIGN_NAMES = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                       "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]

# Classical "planetary years" (Valens) determining each sign's Zodiacal
# Releasing L1 period length, in years -- per Brennan (2017) Ch. 13.
# Keyed by this project's RASHI_NAMES (Sanskrit sign names used throughout, matching
# reading_engine.py's existing sidereal-sign convention for Hellenistic computation) --
# mapped 1:1 to the corresponding tropical/Western sign per WESTERN_SIGN_NAMES ordering.
ZR_SIGN_YEARS = {
    "Mesha": 15, "Vrishabha": 8, "Mithuna": 20, "Karka": 25, "Simha": 19, "Kanya": 20,
    "Tula": 8, "Vrischika": 15, "Dhanu": 12, "Makara": 27, "Kumbha": 30, "Meena": 12,
}
SIGN_RULER_HELLENISTIC = {  # classical (pre-outer-planet) rulership, per Hellenistic convention
    "Mesha": "mars", "Vrishabha": "venus", "Mithuna": "mercury", "Karka": "moon", "Simha": "sun",
    "Kanya": "mercury", "Tula": "venus", "Vrischika": "mars", "Dhanu": "jupiter",
    "Makara": "saturn", "Kumbha": "saturn", "Meena": "jupiter",
}

NOT_IMPLEMENTED_TECHNIQUES = {
    "horary": "Requires a query-moment chart with its own house-signification rule set "
              "distinct from natal/mundane technique -- not built this session.",
    "electional": "Requires searching a date range against multiple concurrent constraints "
                  "(sect, dignity, void-of-course, aspect timing) -- not built this session.",
    "zodiacal_releasing_l2_l4": "Sub-period (L2/L3/L4) computation and the 'loosing of the "
                                "bond' rule are real documented techniques but require a more "
                                "involved reconstruction than this session implements -- only "
                                "the L1 major-period backbone is computed here.",
}

RULES: Dict[str, PredictiveRule] = {
    "hellenistic.profection": PredictiveRule(
        rule_id="hellenistic.profection", tradition="hellenistic", school="Hellenistic (Valens/Dorotheus)",
        name="Annual Profection",
        description="The whole-sign Ascendant advances one sign per year of the native's/"
                    "entity's age; the profected sign's ruler becomes 'Lord of the Year'.",
        historical_source="Vettius Valens, Anthology; Dorotheus, Carmen Astrologicum",
        calculation="profected_sign = (natal_ascendant_sign_index + age_in_whole_years) mod 12",
        interpretation="The Lord of the Year's natal condition (dignity, sect status) colors "
                       "the year's dominant themes; the profected sign's house topics (from the "
                       "natal chart) are activated.",
        prediction_domain=["natal", "mundane", "annual_timing"],
        historical_status=HistoricalStatus.DOCUMENTED.value, confidence="moderate",
    ),
    "hellenistic.lot_of_fortune": PredictiveRule(
        rule_id="hellenistic.lot_of_fortune", tradition="hellenistic", school="Hellenistic",
        name="Lot of Fortune",
        description="Day chart: Ascendant + Moon - Sun. Night chart: Ascendant + Sun - Moon.",
        historical_source="Vettius Valens, Anthology; Ptolemy, Tetrabiblos III.10 (as one of "
                          "many lots Ptolemy discusses); Dorotheus, Carmen Astrologicum",
        calculation="See description; sect-dependent (see hellenistic.sect rule already in "
                    "world_astrology/traditions/hellenistic.py).",
        interpretation="Classically signifies the body, livelihood, and material fortune.",
        prediction_domain=["natal", "finance", "wellbeing"],
        historical_status=HistoricalStatus.DOCUMENTED.value, confidence="moderate",
    ),
    "hellenistic.lot_of_spirit": PredictiveRule(
        rule_id="hellenistic.lot_of_spirit", tradition="hellenistic", school="Hellenistic",
        name="Lot of Spirit",
        description="Day chart: Ascendant + Sun - Moon. Night chart: Ascendant + Moon - Sun "
                    "(the mirror-image formula of the Lot of Fortune).",
        historical_source="Vettius Valens, Anthology; Dorotheus, Carmen Astrologicum",
        calculation="See description.",
        interpretation="Classically signifies mind, career, and agency/will.",
        prediction_domain=["natal", "career"],
        historical_status=HistoricalStatus.DOCUMENTED.value, confidence="moderate",
    ),
    "hellenistic.zodiacal_releasing_l1": PredictiveRule(
        rule_id="hellenistic.zodiacal_releasing_l1", tradition="hellenistic", school="Hellenistic",
        name="Zodiacal Releasing from Fortune (L1 major periods)",
        description="A chronocrator (time-lord) technique: starting from the sign containing "
                    "the Lot of Fortune, each sign in order governs a major period whose length "
                    "(in years) is set by its ruling planet's classical 'years' value; the "
                    "currently active sign/period is found by walking forward from the natal "
                    "moment to the prediction date.",
        historical_source="Vettius Valens, Anthology, Book IV (reconstructed algorithmic detail "
                          "per Robert Schmidt/Robert Hand's Project Hindsight translations and "
                          "Chris Brennan's 2017 synthesis)",
        calculation="Walk forward from Lot-of-Fortune sign through the zodiac, accumulating each "
                    "sign's classical year-length, until the accumulated span reaches the "
                    "prediction date.",
        interpretation="The active L1 sign/ruling planet's natal condition sets the dominant "
                       "life theme for that multi-year period.",
        prediction_domain=["natal", "mundane", "long_range_timing"],
        historical_status=HistoricalStatus.RECONSTRUCTED.value, confidence="low",
    ),
}


def _lon_to_sign_deg(lon: float):
    idx = int(lon // 30) % 12
    return idx, lon - idx * 30.0


class HellenisticEngine(AstrologyEngine):
    tradition_name = "hellenistic"

    def is_applicable(self, context: PredictionContext) -> bool:
        return True

    def calculate(self, context: PredictionContext) -> Dict[str, Any]:
        natal = _shared.natal_chart(context)
        chart = natal.chart
        asc_idx = chart.ascendant_rashi.rashi_index  # whole-sign house 1 = ascendant's sign (tropical vs sidereal handled by same rashi convention this project already uses for Hellenistic per reading_engine.py's precedent)
        sun_house = chart.grahas["sun"].house
        is_day_chart = sun_house in range(7, 13)

        asc_lon = chart.ascendant_sidereal_deg
        sun_lon = chart.grahas["sun"].sidereal_lon_deg
        moon_lon = chart.grahas["moon"].sidereal_lon_deg

        if is_day_chart:
            fortune_lon = (asc_lon + moon_lon - sun_lon) % 360.0
            spirit_lon = (asc_lon + sun_lon - moon_lon) % 360.0
        else:
            fortune_lon = (asc_lon + sun_lon - moon_lon) % 360.0
            spirit_lon = (asc_lon + moon_lon - sun_lon) % 360.0
        fortune_sign_idx, _ = _lon_to_sign_deg(fortune_lon)
        spirit_sign_idx, _ = _lon_to_sign_deg(spirit_lon)

        # Annual profection: whole years of age at prediction_date.
        import datetime
        birth_date = datetime.date.fromisoformat(context.birth_or_inception_date)
        as_of = datetime.date.fromisoformat(context.prediction_date) if context.prediction_date \
            else datetime.date.today()
        age_years = as_of.year - birth_date.year - (
            (as_of.month, as_of.day) < (birth_date.month, birth_date.day))
        age_years = max(age_years, 0)
        profected_sign_idx = (asc_idx + age_years) % 12
        lord_of_year = SIGN_RULER_HELLENISTIC[RASHI_NAMES[profected_sign_idx]]

        # Zodiacal Releasing L1: walk forward from Fortune's sign.
        cursor_sign_idx = fortune_sign_idx
        elapsed_years = 0.0
        birth_ts = birth_date.toordinal()
        as_of_ts = as_of.toordinal()
        span_years = (as_of_ts - birth_ts) / 365.25
        zr_periods = []
        cursor_years = 0.0
        active_zr_sign = None
        for _ in range(48):  # generous cap; ZR cycles are long but bounded for any realistic span
            sign_name = RASHI_NAMES[cursor_sign_idx]
            length = ZR_SIGN_YEARS[sign_name]
            zr_periods.append({"sign": sign_name, "start_year_offset": cursor_years,
                               "end_year_offset": cursor_years + length})
            if cursor_years <= span_years < cursor_years + length:
                active_zr_sign = sign_name
            cursor_years += length
            cursor_sign_idx = (cursor_sign_idx + 1) % 12
            if cursor_years > span_years + 1 and active_zr_sign is not None:
                break

        return {
            "zodiac_system": "sidereal (this project's convention for Hellenistic, matching "
                              "reading_engine.py's existing precedent)",
            "calendar_system": "N/A", "coordinate_system": "ecliptic",
            "ayanamsha": "Lahiri", "epoch": context.birth_or_inception_date,
            "is_day_chart": is_day_chart,
            "fortune_sign": RASHI_NAMES[fortune_sign_idx], "spirit_sign": RASHI_NAMES[spirit_sign_idx],
            "profected_sign": RASHI_NAMES[profected_sign_idx], "lord_of_year": lord_of_year,
            "age_years": age_years,
            "active_zr_sign": active_zr_sign, "zr_periods_sample": zr_periods[:6],
            "lord_of_year_dignity": (
                dt.hellenistic_score(
                    lord_of_year,
                    chart.grahas[lord_of_year].rashi.rashi_name,
                    is_day_chart,
                )[1]
                if lord_of_year in chart.grahas else "N/A"
            ),
            "time_accuracy": context.time_accuracy,
        }

    def interpret(self, calculation: Dict[str, Any]) -> Dict[str, Any]:
        themes: List[str] = []
        factors: List[Dict[str, Any]] = []
        rules_used = ["hellenistic.profection", "hellenistic.lot_of_fortune",
                      "hellenistic.lot_of_spirit", "hellenistic.zodiacal_releasing_l1"]

        lord = calculation["lord_of_year"]
        dignity = calculation.get("lord_of_year_dignity", "N/A")
        themes.append(f"annual theme ruled by {lord} ({dignity.lower().replace('_', ' ') if dignity != 'N/A' else 'dignity unknown'})")
        factors.append({"name": "Lord of the Year", "value": lord, "rule_id": "hellenistic.profection"})
        factors.append({"name": "Profected sign", "value": calculation["profected_sign"], "rule_id": "hellenistic.profection"})
        factors.append({"name": "Lot of Fortune sign", "value": calculation["fortune_sign"], "rule_id": "hellenistic.lot_of_fortune"})
        factors.append({"name": "Lot of Spirit sign", "value": calculation["spirit_sign"], "rule_id": "hellenistic.lot_of_spirit"})
        if calculation.get("active_zr_sign"):
            themes.append(f"long-range Zodiacal Releasing period in {calculation['active_zr_sign']}")
            factors.append({"name": "Active ZR (Fortune) L1 sign", "value": calculation["active_zr_sign"],
                            "rule_id": "hellenistic.zodiacal_releasing_l1"})

        if dignity in ("EXALTED", "OWN_SIGN"):
            themes.append("favorable annual conditions (Lord of the Year well-dignified)")
        elif dignity == "DEBILITATED":
            themes.append("challenging annual conditions (Lord of the Year debilitated)")

        prediction_text = (
            f"Hellenistic reading: this is a year ruled by {lord} (profected to "
            f"{calculation['profected_sign']}), with Lot of Fortune in {calculation['fortune_sign']} "
            f"and Lot of Spirit in {calculation['spirit_sign']}."
            + (f" Currently in a Zodiacal Releasing major period of {calculation['active_zr_sign']}."
               if calculation.get("active_zr_sign") else "")
        )

        limitations = ["Zodiacal Releasing sub-periods (L2-L4) and the 'loosing of the bond' "
                       "rule are not implemented -- only the L1 major-period backbone is shown."]
        if calculation.get("time_accuracy") != "documented":
            limitations.append("Birth/inception time was assumed (midnight) -- the Ascendant "
                              "(and therefore profection/Lot signs) carries real extra uncertainty.")

        return {
            "themes": themes, "factors": factors, "rules_used": rules_used,
            "prediction_text": prediction_text, "signal_strength": None,
            "historical_status": HistoricalStatus.DOCUMENTED.value,
            "limitations": limitations, "time_window": None,
        }
