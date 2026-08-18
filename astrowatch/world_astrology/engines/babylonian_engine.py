"""
Astrowatch World Astrology -- Babylonian/Mesopotamian computational engine.
===================================================================
Implements real, computable celestial-omen phenomena from the Mesopotamian
tradition (Enuma Anu Enlil and the later Assyrian/Babylonian astrological
report corpus), per the modern Assyriological scholarship synthesized in
Francesca Rochberg's "The Heavenly Writing" (2004) and Hermann Hunger's
"Astrological Reports to Assyrian Kings" (SAA 8, 1992):

  1. Lunar/solar eclipse detection (real Swiss-Ephemeris eclipse search) --
     eclipses were among the most significant omens in this tradition.
  2. Venus visibility-phase (heliacal rising/setting via Sun-Venus
     elongation) -- the Venus Tablet of Ammisaduqa (Enuma Anu Enlil Tablet
     63) records omens tied to Venus's appearance/disappearance cycle.
  3. Planetary conjunctions among the five classically-visible planets --
     documented as omen triggers throughout the astronomical diaries and
     the Assyrian royal correspondence (SAA 8).

IMPORTANT SCOPE NOTE (no fabrication): this engine reconstructs the
ASTRONOMICAL PHENOMENA (eclipse timing, Venus visibility, conjunctions) with
real precision via Swiss Ephemeris. It does NOT reconstruct the specific
omen TEXTS (e.g. "if the moon is eclipsed on day 14, the king of Elam will
die") -- those are individually attested, numerous, and often contradictory
across tablets; inventing a general-purpose mapping from phenomenon to a
specific political outcome would be fabrication. Instead this engine reports
only the well-documented GENERAL omen category each phenomenon type was
associated with (e.g. "lunar eclipses were read as omens concerning the king
and the land in which they were visible" -- Hunger SAA 8 introduction;
Rochberg 2004 ch. 3), explicitly marked as a category, not a specific
prediction.

Babylonian celestial-omen astrology was fundamentally MUNDANE/ROYAL --
concerned with king, state, land, weather, and war -- not personal natal
astrology (personal Babylonian horoscopes are a separate, much later, minor
corpus of ~32 known cuneiform texts from 410 BCE onward, and are NOT
implemented here). is_applicable() therefore returns False for person /
company / sports_team entities.
"""

from typing import Any, Dict, List

from ..engine_interface import AstrologyEngine, PredictionContext, HistoricalStatus, PredictiveRule
from . import _shared
from kundli import compute_kundli
import swisseph as swe

MUNDANE_ENTITY_TYPES = {"country", "government", "political_party", "city",
                        "organization", "institution", "event"}

CLASSICAL_PLANETS = ["mercury", "venus", "mars", "jupiter", "saturn"]
CONJUNCTION_ORB_DEG = 3.0
ECLIPSE_WINDOW_DAYS = 90.0

NOT_IMPLEMENTED_TECHNIQUES = {
    "astronomical_diary_full_reconstruction": "The astronomical diaries recorded a broad "
        "range of nightly observations (weather, river levels, market prices, planetary "
        "phenomena together) as a single integrated genre; reconstructing that full "
        "integrated-observation format is out of scope -- this engine implements only the "
        "individually well-documented astronomical phenomena (eclipses, Venus visibility, "
        "conjunctions) that the diaries and EAE draw on.",
    "specific_omen_text_matching": "Enuma Anu Enlil's ~7000 individual omens (protasis/"
        "apodosis pairs) are not comprehensively digitized/available to this project in a "
        "form that could be reliably matched programmatically; inventing a general phenomenon "
        "-> specific-outcome mapping would be fabrication. Only documented general omen "
        "CATEGORIES are reported, never a specific invented apodosis.",
    "lunar_omens_monthly_appearance": "The 'lunar omens' concerning the moon's monthly "
        "first-visibility date/appearance/halo (EAE Tablets 1-13) require reconstructing "
        "the Babylonian lunar calendar's month-start convention (first visibility of the "
        "crescent, itself weather-dependent and only approximately predictable) -- not "
        "built this session; distinct from the eclipse-omen technique implemented here.",
}

RULES: Dict[str, PredictiveRule] = {
    "babylonian.eclipse_omen": PredictiveRule(
        rule_id="babylonian.eclipse_omen", tradition="babylonian", school="Enuma Anu Enlil / Assyrian royal astrology",
        name="Lunar/Solar Eclipse Omen",
        description="Detects the nearest lunar eclipse (globally visible) and solar eclipse "
                    "(visible from the entity's location) to the prediction date; reports the "
                    "documented general omen category, not a specific invented outcome.",
        historical_source="Enuma Anu Enlil Tablets 15-22 (lunar eclipses), 3-7 (solar); "
                          "Hunger, Astrological Reports to Assyrian Kings (SAA 8, 1992); "
                          "Rochberg, The Heavenly Writing (2004) ch. 3.",
        calculation="Swiss Ephemeris eclipse search (swe.lun_eclipse_when / "
                    "swe.sol_eclipse_when_loc) for the nearest eclipse within "
                    f"{ECLIPSE_WINDOW_DAYS:.0f} days of the prediction date.",
        interpretation="Lunar eclipses were read as concerning the king and the land in "
                       "which they were visible; solar eclipses were read as concerning the "
                       "king personally (per SAA 8's recurring pattern) -- reported here only "
                       "as this general category, never a specific invented event.",
        prediction_domain=["mundane", "political", "eclipse_timing"],
        historical_status=HistoricalStatus.DOCUMENTED.value, confidence="low",
    ),
    "babylonian.venus_visibility": PredictiveRule(
        rule_id="babylonian.venus_visibility", tradition="babylonian", school="Enuma Anu Enlil (Venus Tablet of Ammisaduqa)",
        name="Venus Visibility Phase",
        description="Sun-Venus elongation classified into morning-star visible / evening-star "
                    "visible / invisible (near conjunction) phases.",
        historical_source="Enuma Anu Enlil Tablet 63 (Venus Tablet of Ammisaduqa); Reiner & "
                          "Pingree, Babylonian Planetary Omens Part 3 (1998).",
        calculation="elongation = angular_separation(Venus_tropical_lon, Sun_tropical_lon); "
                    "visible if elongation > 8 deg (approximate heliacal-visibility "
                    "threshold), phase (morning/evening) by whether Venus leads or trails the "
                    "Sun in longitude.",
        interpretation="Periods of Venus's appearance and disappearance were each associated "
                       "with omens in the Ammisaduqa corpus; this engine reports only the "
                       "observational phase, not a specific invented omen text.",
        prediction_domain=["mundane", "agricultural", "venus_cycle"],
        historical_status=HistoricalStatus.DOCUMENTED.value, confidence="low",
    ),
    "babylonian.planetary_conjunction": PredictiveRule(
        rule_id="babylonian.planetary_conjunction", tradition="babylonian", school="Astronomical diaries / EAE",
        name="Planetary Conjunction",
        description="Two of the five classically-visible planets (Mercury, Venus, Mars, "
                    "Jupiter, Saturn) within a tight angular orb of each other.",
        historical_source="Astronomical diaries (Sachs & Hunger, Astronomical Diaries and "
                          "Related Texts from Babylonia); EAE planetary omen tablets.",
        calculation=f"angular_separation(planet_A, planet_B) <= {CONJUNCTION_ORB_DEG} deg, "
                    "checked pairwise across the five classical planets.",
        interpretation="Planetary conjunctions were recorded as notable celestial events "
                       "and omen triggers throughout the diaries and EAE; reported here as "
                       "an observational fact, not a specific invented outcome.",
        prediction_domain=["mundane", "political", "celestial_event"],
        historical_status=HistoricalStatus.DOCUMENTED.value, confidence="low",
    ),
}


def _sep(a: float, b: float) -> float:
    d = abs(a - b) % 360.0
    return d if d <= 180.0 else 360.0 - d


class BabylonianEngine(AstrologyEngine):
    tradition_name = "babylonian"

    def is_applicable(self, context: PredictionContext) -> bool:
        return context.entity_type in MUNDANE_ENTITY_TYPES

    def calculate(self, context: PredictionContext) -> Dict[str, Any]:
        jd = _shared.prediction_date_jd_ut(context)

        # 1. Eclipses.
        lunar_eclipse = None
        try:
            retflag, tret = swe.lun_eclipse_when(jd - 45.0, swe.FLG_SWIEPH, 0, False)
            if tret[0] and abs(tret[0] - jd) <= ECLIPSE_WINDOW_DAYS:
                lunar_eclipse = {"jd": tret[0], "date": _shared.jd_to_iso_date(tret[0])}
        except Exception:
            lunar_eclipse = None

        solar_eclipse = None
        try:
            retflags, tret, attr = swe.sol_eclipse_when_loc(
                jd - 45.0, (context.longitude, context.latitude, 0.0), swe.FLG_SWIEPH, False)
            if tret[0] and abs(tret[0] - jd) <= ECLIPSE_WINDOW_DAYS:
                solar_eclipse = {"jd": tret[0], "date": _shared.jd_to_iso_date(tret[0])}
        except Exception:
            solar_eclipse = None

        # 2. Venus visibility.
        chart = compute_kundli(jd, context.latitude, context.longitude)
        venus_lon = chart.grahas["venus"].tropical_lon_deg
        sun_lon = chart.grahas["sun"].tropical_lon_deg
        elongation = _sep(venus_lon, sun_lon)
        signed_diff = (venus_lon - sun_lon + 180.0) % 360.0 - 180.0
        if elongation < 8.0:
            venus_phase = "invisible (near conjunction with the Sun)"
        elif signed_diff > 0:
            venus_phase = "evening star (visible after sunset)"
        else:
            venus_phase = "morning star (visible before sunrise)"

        # 3. Planetary conjunctions.
        conjunctions = []
        longs = {p: chart.grahas[p].tropical_lon_deg for p in CLASSICAL_PLANETS}
        for i, p1 in enumerate(CLASSICAL_PLANETS):
            for p2 in CLASSICAL_PLANETS[i + 1:]:
                sep = _sep(longs[p1], longs[p2])
                if sep <= CONJUNCTION_ORB_DEG:
                    conjunctions.append({"planets": [p1, p2], "separation_deg": round(sep, 2)})

        return {
            "zodiac_system": "N/A (omen tradition predates zodiac-sign astrology; positions "
                              "used only for elongation/conjunction geometry)",
            "calendar_system": "Babylonian lunisolar (historically); Gregorian used for this "
                              "engine's date reporting",
            "coordinate_system": "ecliptic", "ayanamsha": "N/A",
            "epoch": context.prediction_date or "today",
            "lunar_eclipse": lunar_eclipse, "solar_eclipse": solar_eclipse,
            "venus_elongation_deg": round(elongation, 2), "venus_phase": venus_phase,
            "conjunctions": conjunctions,
            "time_accuracy": context.time_accuracy,
        }

    def interpret(self, calculation: Dict[str, Any]) -> Dict[str, Any]:
        themes: List[str] = []
        factors: List[Dict[str, Any]] = []
        rules_used = ["babylonian.venus_visibility"]

        factors.append({"name": "Venus visibility phase", "value": calculation["venus_phase"],
                        "rule_id": "babylonian.venus_visibility"})
        themes.append(f"Venus {calculation['venus_phase']}")

        if calculation.get("lunar_eclipse"):
            rules_used.append("babylonian.eclipse_omen")
            themes.append("lunar eclipse omen window active "
                         f"({calculation['lunar_eclipse']['date']}) -- traditionally read as "
                         "concerning the king/state in the land of visibility")
            factors.append({"name": "Lunar eclipse date", "value": calculation["lunar_eclipse"]["date"],
                            "rule_id": "babylonian.eclipse_omen"})
        if calculation.get("solar_eclipse"):
            if "babylonian.eclipse_omen" not in rules_used:
                rules_used.append("babylonian.eclipse_omen")
            themes.append("solar eclipse omen window active "
                         f"({calculation['solar_eclipse']['date']}) -- traditionally read as "
                         "concerning the king personally")
            factors.append({"name": "Solar eclipse date", "value": calculation["solar_eclipse"]["date"],
                            "rule_id": "babylonian.eclipse_omen"})

        if calculation.get("conjunctions"):
            rules_used.append("babylonian.planetary_conjunction")
            for c in calculation["conjunctions"]:
                themes.append(f"conjunction of {c['planets'][0]} and {c['planets'][1]}")
                factors.append({"name": f"Conjunction: {c['planets'][0]}-{c['planets'][1]}",
                                "value": f"separation {c['separation_deg']} deg",
                                "rule_id": "babylonian.planetary_conjunction"})

        prediction_text = (
            f"Babylonian omen reading: Venus is {calculation['venus_phase']}."
            + (f" A lunar eclipse omen window is active ({calculation['lunar_eclipse']['date']})."
               if calculation.get("lunar_eclipse") else "")
            + (f" A solar eclipse omen window is active ({calculation['solar_eclipse']['date']})."
               if calculation.get("solar_eclipse") else "")
            + (f" {len(calculation['conjunctions'])} planetary conjunction(s) observed."
               if calculation.get("conjunctions") else " No eclipse or planetary-conjunction "
                                                       "omens active within the search window.")
        )

        limitations = [
            "Only the general documented omen CATEGORY for each phenomenon type is reported "
            "(e.g. 'lunar eclipses concern the king/state') -- this engine does not reconstruct "
            "or invent a specific omen text/outcome for any individual eclipse or conjunction.",
            "Lunar-omen (monthly moon appearance) and full astronomical-diary reconstruction "
            "are not implemented -- see NOT_IMPLEMENTED_TECHNIQUES.",
        ]

        return {
            "themes": themes, "factors": factors, "rules_used": rules_used,
            "prediction_text": prediction_text, "signal_strength": None,
            "historical_status": HistoricalStatus.DOCUMENTED.value,
            "limitations": limitations, "time_window": None,
        }
