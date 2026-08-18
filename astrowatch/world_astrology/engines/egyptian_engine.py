"""
Astrowatch World Astrology -- Egyptian computational engine.
===================================================================
Implements the (Greco-Egyptian, post ~500 BCE) 36-decan system: each decan
spans 10 degrees of the tropical zodiac (3 decans per 30-degree sign),
originally descended from the older native Egyptian practice of using 36
decanal star groups as a night-sky "star clock" (Neugebauer & Parker,
Egyptian Astronomical Texts, 1960-69), later merged with the Babylonian-
derived zodiac during the Hellenistic period and transmitted onward into
Hellenistic/Perso-Arabic/Renaissance astrology (where decan rulers are used
for dignity -- see world_astrology/dignity_tables.py, already used by this
project's Hellenistic engine).

IMPORTANT SCOPE NOTE (explicit task instruction: do NOT invent an Egyptian
natal astrology system that did not historically exist): ancient Egypt did
NOT have a natal-horoscope tradition of its own comparable to Hellenistic
astrology -- the decans' original function was calendrical/temporal (marking
hours of night via heliacal risings) and later religious/funerary (decan
gods depicted on coffin lids and temple ceilings), not personal prediction.
This engine therefore does NOT produce a natal reading; it reports which
decan is CURRENTLY active (at the prediction date, via the Sun's position)
as a calendrical/thematic marker, consistent with the decans' original
star-clock/calendrical function -- is_applicable() returns False for the
"natal" prediction_domain specifically (reported via a limitation) even
though the engine itself always runs (the decan is a feature of the current
sky, not of the entity's birth).

NOT implemented: heliacal-rising-based decan timing (the original method --
requires a fixed-star ephemeris with atmospheric-extinction/visibility
modeling this project does not have); Sirius (Sopdet) heliacal rising /
Egyptian New Year calendrical calculation (same missing capability).
"""

from typing import Any, Dict, List

from ..engine_interface import AstrologyEngine, PredictionContext, HistoricalStatus, PredictiveRule
from . import _shared
from kundli import compute_kundli

TROPICAL_SIGN_NAMES = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
# Decan names are only reliably attested for a subset in surviving temple/coffin texts;
# rather than inventing plausible-sounding names for all 36, this engine reports decans
# by their well-documented positional description (sign + which third) only.
DECAN_THIRDS = ["1st decan (0-10 deg)", "2nd decan (10-20 deg)", "3rd decan (20-30 deg)"]

NOT_IMPLEMENTED_TECHNIQUES = {
    "heliacal_rising_decans": "The original native-Egyptian decan function (marking hours of "
        "night via each decan star's heliacal rising) requires a fixed-star ephemeris with "
        "atmospheric-extinction/visibility modeling this project does not have -- not "
        "implemented; this engine instead reports the LATER Greco-Egyptian zodiacal-decan "
        "position (Sun's current 10-degree band), a documented but distinct system.",
    "sirius_heliacal_rising": "The Sirius (Sopdet) heliacal rising, which marked the ancient "
        "Egyptian New Year and Nile-flood season, requires the same missing fixed-star "
        "visibility capability -- not implemented this session.",
    "egyptian_natal_astrology": "Deliberately not attempted -- ancient Egypt did not have a "
        "personal natal-horoscope tradition comparable to Hellenistic astrology; inventing one "
        "would be fabrication (explicit task instruction).",
}

RULES: Dict[str, PredictiveRule] = {
    "egyptian.active_decan": PredictiveRule(
        rule_id="egyptian.active_decan", tradition="egyptian", school="Greco-Egyptian (post ~500 BCE)",
        name="Currently Active Decan",
        description="Which of the 36 zodiacal decans (10-degree bands, 3 per sign) the Sun "
                    "currently occupies at the prediction date -- a calendrical/thematic "
                    "marker, not a natal reading.",
        historical_source="Neugebauer & Parker, Egyptian Astronomical Texts (1960-1969); decan "
                          "rulership tables also used in this project's dignity_tables.py "
                          "(Hellenistic engine).",
        calculation="decan_index = floor(sun_tropical_lon / 10); sign = decan_index // 3; "
                    "third = decan_index % 3.",
        interpretation="Decans were used calendrically (marking time of night/year) and later, "
                       "in the Hellenistic/Perso-Arabic tradition, for finer-grained planetary "
                       "dignity -- not for individual prediction in the native Egyptian tradition.",
        prediction_domain=["mundane", "calendrical"],
        historical_status=HistoricalStatus.DOCUMENTED.value, confidence="low",
    ),
}


class EgyptianEngine(AstrologyEngine):
    tradition_name = "egyptian"

    def is_applicable(self, context: PredictionContext) -> bool:
        # Not a natal system -- explicitly not_applicable when the prediction is framed
        # as a natal/individual-outcome question (still runs for mundane/general context).
        return context.prediction_domain != "natal"

    def calculate(self, context: PredictionContext) -> Dict[str, Any]:
        jd = _shared.prediction_date_jd_ut(context)
        chart = compute_kundli(jd, context.latitude, context.longitude)
        sun_lon = chart.grahas["sun"].tropical_lon_deg
        decan_index = int(sun_lon // 10.0) % 36
        sign_idx = decan_index // 3
        third_idx = decan_index % 3

        return {
            "zodiac_system": "tropical (decan bands over the tropical zodiac)",
            "calendar_system": "N/A (this engine reports the current zodiacal decan, not the "
                              "native Egyptian civil calendar)",
            "coordinate_system": "ecliptic", "ayanamsha": "N/A (tropical)",
            "epoch": context.prediction_date or "today",
            "decan_index": decan_index, "decan_sign": TROPICAL_SIGN_NAMES[sign_idx],
            "decan_third": DECAN_THIRDS[third_idx],
            "time_accuracy": context.time_accuracy,
        }

    def interpret(self, calculation: Dict[str, Any]) -> Dict[str, Any]:
        themes = [f"active decan: {calculation['decan_sign']}, {calculation['decan_third']}"]
        factors = [
            {"name": "Active decan", "value": f"{calculation['decan_sign']} {calculation['decan_third']}",
             "rule_id": "egyptian.active_decan"},
        ]
        prediction_text = (
            f"Egyptian (Greco-Egyptian decan) reading: the Sun is currently in the "
            f"{calculation['decan_third']} of {calculation['decan_sign']}."
        )
        limitations = [
            "This is a calendrical/thematic marker (which decan is currently active), not a "
            "natal prediction -- ancient Egypt did not have a personal natal-horoscope "
            "tradition; this engine deliberately does not invent one.",
            "Heliacal-rising-based decan timing (the original native-Egyptian method) and "
            "Sirius/Sopdet heliacal rising are not implemented -- see NOT_IMPLEMENTED_TECHNIQUES.",
        ]
        return {
            "themes": themes, "factors": factors, "rules_used": ["egyptian.active_decan"],
            "prediction_text": prediction_text, "signal_strength": None,
            "historical_status": HistoricalStatus.DOCUMENTED.value,
            "limitations": limitations, "time_window": None,
        }
