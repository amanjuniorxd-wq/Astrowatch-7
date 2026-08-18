"""
Astrowatch World Astrology -- Mesoamerican (Maya) computational engine.
===================================================================
Implements the three core Maya calendrical cycles from real Julian Day
Number arithmetic, anchored to the GMT (Goodman-Martinez-Thompson)
correlation constant:

  1. Tzolk'in -- 260-day cycle (13 numbers x 20 day names).
  2. Haab' -- 365-day "vague year" (18 months of 20 days + 5 Wayeb days).
  3. Long Count -- modified-vigesimal positional day count (baktun/katun/
     tun/winal/kin).

GMT correlation constant: Long Count 13.0.0.0.0 (4 Ajaw 8 Kumk'u) =
Julian Day Number 584283 (the modern scholarly-consensus default, used by
the standard Maya calendar conversion software this project's implementation
was cross-checked against). Per Michael Coe, "The Maya" (2015 rev. ed.) and
J. Eric S. Thompson's original correlation work: an alternate GMT variant
using JDN 584285 (differing by exactly 2 days) also has real currency in the
scholarly literature. This constant-choice ambiguity is REAL, not this
project's own uncertainty -- marked historical_status="scholarly_disputed"
on the rule itself for that reason; this engine computes using the more
commonly cited 584283 default and reports the alternate explicitly in
limitations, never silently picking one without disclosure.

Day-name/number offsets were derived by construction (not guessed) to
satisfy the anchor identity "JDN 584283 = 4 Ajaw 8 Kumk'u" exactly -- see
the inline derivation comments before TZOLKIN_NUMBER_OFFSET/HAAB_DAY_OFFSET.

Keeps Maya day-sign/omen associations OUT of scope (not_implemented) --
those vary by source region/period and this project has not independently
verified a specific sourced table this session. Aztec and other
Mesoamerican calendar variants (which use similar but not identical
structures, e.g. the Aztec tonalpohualli/xiuhpohualli) are NOT conflated
with the Maya system here -- this engine implements the Maya system
specifically and is named/scoped accordingly, per the task's explicit
instruction to keep different Mesoamerican traditions separate.
"""

from typing import Any, Dict, List

from ..engine_interface import AstrologyEngine, PredictionContext, HistoricalStatus, PredictiveRule
from . import _shared
import coordinates

GMT_CORRELATION_JDN = 584283  # 4 Ajaw 8 Kumk'u = this JDN (modern scholarly-consensus default)
GMT_CORRELATION_ALT_JDN = 584285  # documented alternate (Thompson's original / GMT+2 variant)

TZOLKIN_DAY_NAMES = ["Imix", "Ik", "Akbal", "Kan", "Chicchan", "Cimi", "Manik", "Lamat", "Muluc",
                     "Oc", "Chuen", "Eb", "Ben", "Ix", "Men", "Cib", "Caban", "Etznab", "Cauac", "Ajaw"]
# Anchor: JDN 584283 -> tzolkin day-name "Ajaw" (index 19) and number 4.
# day_idx(JDN) = (JDN - GMT_CORRELATION_JDN + 19) mod 20  [+19 so JDN==GMT_CORRELATION_JDN gives 19]
# number(JDN)  = ((JDN - GMT_CORRELATION_JDN + 3) mod 13) + 1  [+3 so the mod-13 term is 3, giving 3+1=4]

HAAB_MONTH_NAMES = ["Pop", "Wo", "Sip", "Sotz", "Sek", "Xul", "Yaxkin", "Mol", "Chen", "Yax",
                    "Sak", "Keh", "Mak", "Kankin", "Muwan", "Pax", "Kayab", "Kumku"]
# Anchor: JDN 584283 -> Haab' "8 Kumk'u" (Kumku is month index 17, day-in-month 8 [0-indexed 0-19]).
# haab_day_of_year(JDN=584283) must equal 17*20 + 8 = 348.

NOT_IMPLEMENTED_TECHNIQUES = {
    "day_sign_omens": "Traditional Tzolk'in day-sign meanings/omens vary meaningfully by "
        "source, region, and period (Yucatec vs K'iche' vs colonial-era sources); this project "
        "has not independently verified a single sourced table this session -- not implemented "
        "to avoid presenting a possibly-syncretic or invented interpretation as documented fact.",
    "venus_table_correlation": "The Dresden Codex Venus Table's precise correlation to specific "
        "historical dates (used for Venus-cycle omen timing) requires additional scholarly "
        "correlation work this project has not sourced -- not implemented; the raw Venus "
        "synodic cycle (584 days) itself is available via world_astrology/engines/_shared.py's "
        "SYNODIC constants if a future engine needs it.",
    "aztec_tonalpohualli": "The Aztec 260-day tonalpohualli and 365-day xiuhpohualli use a "
        "structurally similar but not identical day-name/glyph set and correlation -- "
        "deliberately kept separate from (not conflated with) this Maya-specific engine, and "
        "not implemented itself this session.",
    "eclipse_lunar_series": "The Maya Lunar Series (recorded in Long Count inscriptions, "
        "tracking lunation count and eclipse-half-year membership) requires additional "
        "glyphic-correlation work not attempted this session.",
}

RULES: Dict[str, PredictiveRule] = {
    "mesoamerican.tzolkin": PredictiveRule(
        rule_id="mesoamerican.tzolkin", tradition="mesoamerican", school="Maya",
        name="Tzolk'in (260-day cycle)",
        description="13 numbers x 20 day names = 260-day ritual/divinatory cycle.",
        historical_source="Michael Coe, The Maya (2015 rev.); standard Maya epigraphy/"
                          "calendrics literature; GMT correlation constant.",
        calculation="See module docstring's anchor derivation.",
        interpretation="Historically used for ritual/divinatory timing; day-sign-specific "
                       "omens are NOT reconstructed here (see NOT_IMPLEMENTED_TECHNIQUES).",
        prediction_domain=["mundane", "ritual_timing"],
        historical_status=HistoricalStatus.SCHOLARLY_DISPUTED.value, confidence="low",
    ),
    "mesoamerican.haab": PredictiveRule(
        rule_id="mesoamerican.haab", tradition="mesoamerican", school="Maya",
        name="Haab' (365-day vague year)",
        description="18 months of 20 days + 5 unlucky Wayeb days = 365-day civil/agricultural "
                    "calendar (not corrected for the true 365.24-day solar year, hence 'vague').",
        historical_source="Michael Coe, The Maya (2015 rev.); standard Maya epigraphy/"
                          "calendrics literature.",
        calculation="See module docstring's anchor derivation.",
        interpretation="Civil/agricultural calendar; the Wayeb 5-day period was traditionally "
                       "considered dangerous/unlucky.",
        prediction_domain=["mundane", "agricultural", "calendrical"],
        historical_status=HistoricalStatus.SCHOLARLY_DISPUTED.value, confidence="low",
    ),
    "mesoamerican.long_count": PredictiveRule(
        rule_id="mesoamerican.long_count", tradition="mesoamerican", school="Maya",
        name="Long Count",
        description="Modified-vigesimal positional day count (baktun.katun.tun.winal.kin) from "
                    "the GMT correlation epoch.",
        historical_source="Michael Coe, The Maya (2015 rev.); GMT correlation.",
        calculation="days_since_epoch = JDN - GMT_CORRELATION_JDN; baktun=days//144000; "
                    "katun=(days%144000)//7200; tun=(days%7200)//360; winal=(days%360)//20; kin=days%20.",
        interpretation="Absolute historical dating system; used epigraphically for dynastic/"
                       "historical event dating, not personal prediction.",
        prediction_domain=["mundane", "historical_dating"],
        historical_status=HistoricalStatus.SCHOLARLY_DISPUTED.value, confidence="low",
    ),
}


def _jdn_for_date(date_str: str) -> int:
    y, m, d = (int(x) for x in date_str.split("-"))
    return int(round(coordinates.julian_day(y, m, d, 12.0)))


class MesoamericanEngine(AstrologyEngine):
    tradition_name = "mesoamerican"

    def is_applicable(self, context: PredictionContext) -> bool:
        return True

    def calculate(self, context: PredictionContext) -> Dict[str, Any]:
        date_str = context.prediction_date or context.birth_or_inception_date
        jdn = _jdn_for_date(date_str)
        offset = jdn - GMT_CORRELATION_JDN

        tzolkin_day_idx = (offset + 19) % 20
        tzolkin_number = ((offset + 3) % 13) + 1
        tzolkin_day_name = TZOLKIN_DAY_NAMES[tzolkin_day_idx]

        haab_day_of_year = (offset + 348) % 365
        if haab_day_of_year >= 360:
            haab_month = "Wayeb"
            haab_day_in_month = haab_day_of_year - 360  # 0-4
        else:
            haab_month = HAAB_MONTH_NAMES[haab_day_of_year // 20]
            haab_day_in_month = haab_day_of_year % 20

        baktun = offset // 144000
        rem = offset % 144000
        katun = rem // 7200
        rem %= 7200
        tun = rem // 360
        rem %= 360
        winal = rem // 20
        kin = rem % 20

        # Alternate correlation, reported for transparency (see docstring).
        alt_offset = jdn - GMT_CORRELATION_ALT_JDN
        alt_tzolkin_day_idx = (alt_offset + 19) % 20
        alt_tzolkin_number = ((alt_offset + 3) % 13) + 1

        return {
            "zodiac_system": "N/A (calendrical cycle system, not a zodiac-sign system)",
            "calendar_system": "Maya Tzolk'in/Haab'/Long Count (GMT correlation)",
            "coordinate_system": "N/A", "ayanamsha": "N/A", "epoch": date_str,
            "jdn": jdn,
            "tzolkin_number": tzolkin_number, "tzolkin_day_name": tzolkin_day_name,
            "haab_month": haab_month, "haab_day_in_month": haab_day_in_month,
            "long_count": f"{baktun}.{katun}.{tun}.{winal}.{kin}",
            "alt_correlation_tzolkin": f"{alt_tzolkin_number} {TZOLKIN_DAY_NAMES[alt_tzolkin_day_idx]}",
            "time_accuracy": context.time_accuracy,
        }

    def interpret(self, calculation: Dict[str, Any]) -> Dict[str, Any]:
        themes = [
            f"Tzolk'in {calculation['tzolkin_number']} {calculation['tzolkin_day_name']}",
            f"Haab' {calculation['haab_day_in_month']} {calculation['haab_month']}",
            f"Long Count {calculation['long_count']}",
        ]
        factors = [
            {"name": "Tzolk'in", "value": f"{calculation['tzolkin_number']} {calculation['tzolkin_day_name']}",
             "rule_id": "mesoamerican.tzolkin"},
            {"name": "Haab'", "value": f"{calculation['haab_day_in_month']} {calculation['haab_month']}",
             "rule_id": "mesoamerican.haab"},
            {"name": "Long Count", "value": calculation["long_count"], "rule_id": "mesoamerican.long_count"},
        ]
        prediction_text = (
            f"Mesoamerican (Maya) calendrical reading: {calculation['tzolkin_number']} "
            f"{calculation['tzolkin_day_name']} (Tzolk'in), {calculation['haab_day_in_month']} "
            f"{calculation['haab_month']} (Haab'), Long Count {calculation['long_count']}."
        )
        limitations = [
            "Day-sign-specific omens/meanings are not reconstructed (see NOT_IMPLEMENTED_TECHNIQUES) "
            "-- only the calendrical positions themselves are computed.",
            f"Uses the GMT 584283 correlation (modern scholarly-consensus default); the "
            f"documented alternate 584285 correlation gives a different Tzolk'in reading: "
            f"{calculation['alt_correlation_tzolkin']}.",
            "Aztec and other Mesoamerican calendar systems are separate traditions, not "
            "computed by (or conflated with) this Maya-specific engine.",
        ]
        return {
            "themes": themes, "factors": factors,
            "rules_used": ["mesoamerican.tzolkin", "mesoamerican.haab", "mesoamerican.long_count"],
            "prediction_text": prediction_text, "signal_strength": None,
            "historical_status": HistoricalStatus.SCHOLARLY_DISPUTED.value,
            "limitations": limitations, "time_window": None,
        }
