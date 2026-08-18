"""
Astrowatch World Astrology -- (Modern) Western tropical computational engine.
===================================================================
Implements three real, documented Western natal/predictive techniques that
were previously only catalogued as knowledge-reference entries
(world_astrology/traditions/western.py), using the tropical longitudes
already computed (and validated) by kundli.py's Swiss Ephemeris pipeline --
kundli.py computes BOTH tropical_lon_deg and sidereal_lon_deg for every body,
so this engine simply reads the tropical fields rather than re-deriving them.

  1. Secondary Progressions -- the "a day for a year" symbolic technique:
     the chart cast for (birth date + N days), N = age in years, read as
     that year's psychological/developmental picture. Formalized in its
     modern form by 17th-19th century Western astrologers building on a
     principle attributed (with real scholarly disagreement over the
     attribution's precision) to Ptolemy's Tetrabiblos III.10's "kata to
     isodynamounta" (per-degree-for-a-year) climacteric doctrine -- marked
     historical_status="reconstructed" for this reason, not "documented".
  2. Solar Return -- the chart cast for the exact moment the transiting Sun
     returns to its natal tropical degree each year; a technique with
     continuous use from Hellenistic astrology (as the "annual revolution")
     through the modern period. Numeric root-find against Swiss-Ephemeris
     Sun longitude (Sun's near-linear ~0.9856 deg/day motion converges a
     secant search in 2-4 iterations).
  3. Transiting outer-planet aspects to natal Sun/Moon/Ascendant -- the
     standard modern "transit" technique (Jupiter/Saturn/Uranus/Neptune/
     Pluto), using conventional modern orb sizes. Marked
     historical_status="modern" (outer planets Uranus/Neptune/Pluto are
     telescopic-era discoveries with no ancient antecedent; even the
     Jupiter/Saturn transit-to-natal technique's specific modern orb
     conventions postdate Hellenistic astrology).

NOT implemented this session (see NOT_IMPLEMENTED_TECHNIQUES): Synastry
(requires a second entity's chart -- out of scope for this single-entity
PredictionContext), Lunar Returns, eclipse-based mundane technique (needs an
eclipse-finding algorithm this project doesn't have yet), horary, electional.
"""

import math
from typing import Any, Dict, List

from ..engine_interface import AstrologyEngine, PredictionContext, HistoricalStatus, PredictiveRule
from . import _shared
from kundli import (compute_kundli, _ensure_thread_ephemeris_configured,
                     _CALC_FLAGS_TROPICAL, EphemerisDataUnavailable)
import swisseph as swe

TROPICAL_SIGN_NAMES = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]

OUTER_PLANETS = ["jupiter", "saturn", "uranus", "neptune", "pluto"]
# kundli.py's classical-9 GRAHA_BODY_IDS doesn't include the telescopic-era outer
# planets; compute their tropical longitude directly here via the same
# thread-safe/Moshier-fallback-refusing pattern kundli.py's own
# _placement_from_calc uses, rather than re-deriving or silently approximating.
OUTER_PLANET_BODY_IDS = {"uranus": swe.URANUS, "neptune": swe.NEPTUNE, "pluto": swe.PLUTO}


def _outer_planet_tropical_lon(jd_ut: float, body_id: int) -> float:
    _ensure_thread_ephemeris_configured()
    result, flag = swe.calc_ut(jd_ut, body_id, _CALC_FLAGS_TROPICAL)
    if flag & swe.FLG_MOSEPH:
        raise EphemerisDataUnavailable(
            "swe.calc_ut() for an outer planet fell back to Moshier approximation "
            "mode instead of file-based ephemeris data -- refusing to return an "
            "approximate position silently."
        )
    return result[0] % 360.0
# Conventional modern orb sizes (degrees) by aspect -- practitioner convention,
# not a single fixed ancient source; varies by author (Lilly/Ptolemy used
# somewhat different values). See historical_status on the rule itself.
ASPECTS = {
    "conjunction": (0.0, 8.0), "opposition": (180.0, 8.0),
    "square": (90.0, 6.0), "trine": (120.0, 6.0), "sextile": (60.0, 4.0),
}

NOT_IMPLEMENTED_TECHNIQUES = {
    "synastry": "Requires a second entity's full natal chart for comparison; this "
               "engine's PredictionContext models a single entity -- not built this session.",
    "lunar_return": "Same root-find technique as Solar Return but for the Moon's ~27.3-day "
                    "cycle; the shorter period means many returns occur between any two "
                    "prediction dates and a specific-return-selection rule would be needed "
                    "-- not built this session, deferred alongside Solar Return's more "
                    "clearly-scoped annual cadence.",
    "eclipse_mundane": "Requires an eclipse-finding (syzygy + node-proximity search) "
                       "algorithm this project does not yet have -- not built this session.",
    "horary": "Requires a query-moment chart with its own house-signification rule set -- not built this session.",
    "electional": "Requires searching a date range against multiple concurrent constraints -- not built this session.",
}

RULES: Dict[str, PredictiveRule] = {
    "western.secondary_progression": PredictiveRule(
        rule_id="western.secondary_progression", tradition="western", school="Modern tropical (day-for-a-year)",
        name="Secondary Progressions",
        description="The chart cast for (birth date + N days), where N = the entity's age in "
                    "years at the prediction date; the progressed Moon (moves ~1 deg/day, i.e. "
                    "~1 sign per ~2.5 years) is the primary timing indicator read from it.",
        historical_source="Principle traced (with real scholarly disagreement over precision of "
                          "attribution) to Ptolemy, Tetrabiblos III.10; formalized in its modern "
                          "algorithmic form by later Western astrologers.",
        calculation="progressed_jd = natal_jd_ut + age_in_years_at_prediction_date (days); "
                    "chart cast at progressed_jd, natal location.",
        interpretation="Progressed Moon's sign/aspects describe the year's emotional/"
                       "developmental themes; progressed Sun's sign-ingress (rare, ~1 deg/year) "
                       "marks decades-long life-chapter shifts.",
        prediction_domain=["natal", "annual_timing", "psychological"],
        historical_status=HistoricalStatus.RECONSTRUCTED.value, confidence="low",
    ),
    "western.solar_return": PredictiveRule(
        rule_id="western.solar_return", tradition="western", school="Modern tropical / Hellenistic annual revolution",
        name="Solar Return",
        description="The chart cast for the exact moment the transiting Sun returns to its "
                    "exact natal tropical degree, once per year; read as that year's forecast.",
        historical_source="Continuous technique from Hellenistic 'annual revolution' astrology "
                          "(Valens, Dorotheus) through the modern period.",
        calculation="Numeric root-find: jd such that tropical_sun_longitude(jd) == "
                    "natal_tropical_sun_longitude (mod 360), searched near natal_jd + "
                    "N*365.2422 days.",
        interpretation="The Solar Return Ascendant/house placements and aspects describe the "
                       "year's dominant themes.",
        prediction_domain=["natal", "mundane", "annual_timing"],
        historical_status=HistoricalStatus.DOCUMENTED.value, confidence="moderate",
    ),
    "western.outer_planet_transit": PredictiveRule(
        rule_id="western.outer_planet_transit", tradition="western", school="Modern tropical",
        name="Transiting outer-planet aspect to natal Sun/Moon/Ascendant",
        description="Jupiter/Saturn/Uranus/Neptune/Pluto's current tropical position checked "
                    "for a major Ptolemaic aspect (conjunction/opposition/square/trine/sextile, "
                    "conventional modern orbs) to the natal Sun, Moon, or Ascendant.",
        historical_source="Aspect doctrine per Ptolemy, Tetrabiblos I; outer planets "
                          "(Uranus/Neptune/Pluto) are telescopic-era additions with no ancient "
                          "antecedent, and modern orb-size convention postdates Hellenistic use.",
        calculation="angular_separation = |transiting_lon - natal_point_lon| (mod 360, "
                    "minimized to 0-180); matched against ASPECTS table within orb.",
        interpretation="A transiting outer planet's aspect to a natal chart point is read as "
                       "activating that point's themes for the aspect's (planet-dependent) duration.",
        prediction_domain=["natal", "mundane", "annual_timing"],
        historical_status=HistoricalStatus.MODERN.value, confidence="low",
    ),
}


def _angular_sep(a: float, b: float) -> float:
    d = abs(a - b) % 360.0
    return d if d <= 180.0 else 360.0 - d


def _sign_of(lon: float) -> str:
    return TROPICAL_SIGN_NAMES[int(lon // 30) % 12]


def _solar_return_jd(natal_sun_lon: float, natal_jd: float, target_year_offset_days: float,
                      lat: float, lon: float) -> float:
    """Secant-method root-find for the Sun's tropical-longitude return, starting
    from a +/-3-day bracket around the mean-solar-year estimate. Sun's motion is
    ~0.9856 deg/day and nearly linear over a few days, so this converges fast."""
    guess_jd = natal_jd + target_year_offset_days
    jd0, jd1 = guess_jd - 2.0, guess_jd + 2.0

    def f(jd):
        chart = compute_kundli(jd, lat, lon)
        lon_now = chart.grahas["sun"].tropical_lon_deg
        diff = (lon_now - natal_sun_lon + 180.0) % 360.0 - 180.0
        return diff

    f0, f1 = f(jd0), f(jd1)
    for _ in range(20):
        if abs(f1 - f0) < 1e-9:
            break
        jd2 = jd1 - f1 * (jd1 - jd0) / (f1 - f0)
        f2 = f(jd2)
        jd0, f0 = jd1, f1
        jd1, f1 = jd2, f2
        if abs(f2) < 1e-6:
            break
    return jd1


class WesternEngine(AstrologyEngine):
    tradition_name = "western"

    def is_applicable(self, context: PredictionContext) -> bool:
        return True

    def calculate(self, context: PredictionContext) -> Dict[str, Any]:
        natal_entity = _shared.natal_chart(context)
        natal = natal_entity.chart
        natal_jd = natal.jd_ut if hasattr(natal, "jd_ut") else _shared.context_jd_ut(context)
        natal_sun_lon = natal.grahas["sun"].tropical_lon_deg
        natal_moon_lon = natal.grahas["moon"].tropical_lon_deg
        natal_asc_lon = natal.ascendant_tropical_deg

        pred_jd = _shared.prediction_date_jd_ut(context)
        age_years_frac = (pred_jd - natal_jd) / 365.25
        age_years_frac = max(age_years_frac, 0.0)

        # 1. Secondary progression: add `age_years_frac` DAYS to the natal JD.
        progressed_jd = natal_jd + age_years_frac
        prog_chart = compute_kundli(progressed_jd, context.latitude, context.longitude)
        prog_moon_lon = prog_chart.grahas["moon"].tropical_lon_deg
        prog_sun_lon = prog_chart.grahas["sun"].tropical_lon_deg

        # 2. Solar return: most recent return at/before the prediction date.
        n_returns = math.floor(age_years_frac)
        sr_jd = _solar_return_jd(natal_sun_lon, natal_jd, n_returns * 365.2422,
                                  context.latitude, context.longitude)
        sr_chart = compute_kundli(sr_jd, context.latitude, context.longitude)

        # 3. Outer-planet transiting aspects to natal Sun/Moon/Ascendant.
        transit = _shared.transit_chart(context)  # sidereal KundliChart; use tropical fields
        aspects_found = []
        natal_points = {"Sun": natal_sun_lon, "Moon": natal_moon_lon, "Ascendant": natal_asc_lon}
        transit_jd = _shared.prediction_date_jd_ut(context)
        for planet in OUTER_PLANETS:
            if planet in ("jupiter", "saturn"):
                t_lon = transit.grahas[planet].tropical_lon_deg
            else:
                t_lon = _outer_planet_tropical_lon(transit_jd, OUTER_PLANET_BODY_IDS[planet])
            for point_name, point_lon in natal_points.items():
                sep = _angular_sep(t_lon, point_lon)
                for aspect_name, (exact_deg, orb) in ASPECTS.items():
                    if abs(sep - exact_deg) <= orb:
                        aspects_found.append({
                            "transiting_planet": planet, "natal_point": point_name,
                            "aspect": aspect_name, "orb_deg": round(abs(sep - exact_deg), 2),
                        })

        return {
            "zodiac_system": "tropical", "calendar_system": "N/A", "coordinate_system": "ecliptic",
            "ayanamsha": "N/A (tropical)", "epoch": context.birth_or_inception_date,
            "age_years_frac": age_years_frac,
            "progressed_moon_sign": _sign_of(prog_moon_lon), "progressed_sun_sign": _sign_of(prog_sun_lon),
            "natal_sun_sign": _sign_of(natal_sun_lon),
            "solar_return_jd": sr_jd, "solar_return_date": _shared.jd_to_iso_date(sr_jd),
            "solar_return_ascendant_sign": _sign_of(sr_chart.ascendant_tropical_deg),
            "outer_planet_aspects": aspects_found,
            "time_accuracy": context.time_accuracy,
        }

    def interpret(self, calculation: Dict[str, Any]) -> Dict[str, Any]:
        themes: List[str] = []
        factors: List[Dict[str, Any]] = []
        rules_used = ["western.secondary_progression", "western.solar_return"]

        themes.append(f"progressed Moon in {calculation['progressed_moon_sign']}")
        factors.append({"name": "Progressed Moon sign", "value": calculation["progressed_moon_sign"],
                        "rule_id": "western.secondary_progression"})
        if calculation["progressed_sun_sign"] != calculation["natal_sun_sign"]:
            themes.append(f"progressed Sun has shifted into {calculation['progressed_sun_sign']} "
                         f"(a decades-scale life-chapter marker)")
            factors.append({"name": "Progressed Sun sign", "value": calculation["progressed_sun_sign"],
                            "rule_id": "western.secondary_progression"})

        themes.append(f"Solar Return Ascendant in {calculation['solar_return_ascendant_sign']}")
        factors.append({"name": "Solar Return date", "value": calculation["solar_return_date"],
                        "rule_id": "western.solar_return"})
        factors.append({"name": "Solar Return Ascendant sign", "value": calculation["solar_return_ascendant_sign"],
                        "rule_id": "western.solar_return"})

        aspects = calculation.get("outer_planet_aspects", [])
        if aspects:
            rules_used.append("western.outer_planet_transit")
            for a in aspects[:5]:
                themes.append(f"transiting {a['transiting_planet']} {a['aspect']} natal {a['natal_point']}")
                factors.append({"name": f"Transit: {a['transiting_planet']} {a['aspect']} natal {a['natal_point']}",
                                "value": f"orb {a['orb_deg']} deg", "rule_id": "western.outer_planet_transit"})

        prediction_text = (
            f"Western (tropical) reading: progressed Moon in {calculation['progressed_moon_sign']}; "
            f"Solar Return Ascendant in {calculation['solar_return_ascendant_sign']} "
            f"(return date {calculation['solar_return_date']})."
            + (f" {len(aspects)} outer-planet transiting aspect(s) to natal Sun/Moon/Ascendant active."
               if aspects else " No major outer-planet transiting aspects to natal Sun/Moon/Ascendant "
                              "within conventional orb at this time.")
        )

        limitations = [
            "Secondary Progressions here compute only the progressed Sun and Moon "
            "positions/signs, not a full progressed-chart house/aspect analysis.",
            "Solar Return is computed at the entity's natal location (non-relocated "
            "convention); relocated Solar Return charts are a documented but distinct "
            "variant not computed here.",
        ]
        if calculation.get("time_accuracy") != "documented":
            limitations.append("Birth/inception time was assumed (midnight) -- the natal "
                              "Ascendant and Solar Return Ascendant carry real extra uncertainty.")

        return {
            "themes": themes, "factors": factors, "rules_used": rules_used,
            "prediction_text": prediction_text, "signal_strength": None,
            "historical_status": HistoricalStatus.DOCUMENTED.value,
            "limitations": limitations, "time_window": None,
        }
