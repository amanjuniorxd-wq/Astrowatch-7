"""
Astrowatch World Astrology -- Jyotisha (Parashari Vedic) computational engine.
=================================================================================
Extends (does not replace) this project's existing Jyotisha computation
(kundli.py Swiss-Ephemeris sidereal chart, mahadasha.py Vimshottari Dasha,
world_astrology/reading_engine.py's dignity/agreement logic) with three
further, historically documented Parashari techniques not previously
computed anywhere in this project:

  1. Navamsa (D9 varga) -- BPHS's 9-fold sign division, using the standard
     shortcut formula navamsa_sign = (sign_index*9 + navamsa_number) % 12,
     verified against the modality-based counting rule it's derived from
     (movable signs count from themselves, fixed from the 9th, dual from the
     5th) for Aries/Taurus/Gemini as worked examples in this module's tests.
  2. A small set of classical, name-attested Yogas (planetary combinations)
     from Brihat Parashara Hora Shastra: Gajakesari, Chandra-Mangala,
     Budhaditya, Kemadruma.
  3. Gochara (transit) analysis -- the widely-practiced Rashi Gochara
     technique of reading Jupiter/Saturn transits relative to the natal Moon
     sign. Marked historical_status="traditional" (ubiquitous in living
     practice, but this module does not independently verify a single
     canonical textual source for the exact house-favorability table used --
     see the rule metadata's own note).

Jaimini, Nadi, and Tajika are NOT implemented here -- see this module's
NOT_IMPLEMENTED_TECHNIQUES list and the reasons given, per the task's
explicit "do not fabricate" requirement.
"""

from typing import Any, Dict, List

from ..engine_interface import (
    AstrologyEngine, PredictionContext, TraditionStatus, HistoricalStatus, PredictiveRule,
)
from ..dignity_tables import RASHI_LORD, jyotisha_score
from . import _shared

RASHI_NAMES = ["Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya",
               "Tula", "Vrischika", "Dhanu", "Makara", "Kumbha", "Meena"]
MODALITY = {  # 0=movable(chara), 1=fixed(sthira), 2=dual(dwiswabhava) -- BPHS classification
    "Mesha": 0, "Karka": 0, "Tula": 0, "Makara": 0,
    "Vrishabha": 1, "Simha": 1, "Vrischika": 1, "Kumbha": 1,
    "Mithuna": 2, "Kanya": 2, "Dhanu": 2, "Meena": 2,
}

NOT_IMPLEMENTED_TECHNIQUES = {
    "jaimini": "Jaimini's Chara Karaka/Char Dasha system requires a distinct karaka-assignment "
               "algorithm and rasi-dasha timing model this project has not built or validated "
               "against a primary/secondary source this session.",
    "nadi": "Nadi astrology (e.g. Bhrigu/Chandra Nadi) traditionally relies on pre-written leaf "
            "matching against an individual's thumbprint/specific birth details from a physical "
            "archive -- there is no general computational algorithm to reconstruct; genuinely "
            "not implementable as a prediction engine.",
    "tajika": "Tajika (annual-chart Vedic astrology, Persian-influenced) requires its own "
              "Varshaphal/Muntha/Sahams calculation set, distinct from Parashari natal technique "
              "-- not built this session.",
    "prashna": "Prashna (horary) requires a query-moment chart with its own house-signification "
               "rule set distinct from natal/mundane technique -- not built this session.",
    "muhurta": "Muhurta (electional timing) requires searching a date range against multiple "
               "concurrent panchanga/tarabala/chandrabala constraints -- not built this session.",
}

RULES: Dict[str, PredictiveRule] = {
    "jyotisha.navamsa": PredictiveRule(
        rule_id="jyotisha.navamsa", tradition="jyotisha", school="Parashari",
        name="Navamsa (D9) sign placement",
        description="Each 30-degree Rashi is divided into 9 navamsas of 3d20'; the navamsa "
                    "sign is derived by the standard shortcut (sign_index*9 + navamsa_number) "
                    "mod 12, equivalent to the modality-based counting rule (movable signs "
                    "count from themselves, fixed from the 9th, dual from the 5th).",
        historical_source="Brihat Parashara Hora Shastra, Ch. on Shodasavarga (16 divisional charts)",
        calculation="navamsa_sign = (rashi_index*9 + floor(degree_in_rashi / 3.3333)) mod 12",
        interpretation="A planet's navamsa placement is read as its 'inner strength' -- exalted/"
                       "own-sign navamsa placement reinforces the natal (D1) dignity reading.",
        prediction_domain=["natal", "marriage", "general_strength"],
        historical_status=HistoricalStatus.DOCUMENTED.value, confidence="moderate",
    ),
    "jyotisha.yoga.gajakesari": PredictiveRule(
        rule_id="jyotisha.yoga.gajakesari", tradition="jyotisha", school="Parashari",
        name="Gajakesari Yoga",
        description="Moon and Jupiter in mutual kendra (1st/4th/7th/10th houses from each other).",
        historical_source="Brihat Parashara Hora Shastra, Yoga chapters",
        calculation="abs(house(Moon) - house(Jupiter)) mod 12 in {0,3,6,9}",
        interpretation="Classically indicates fame, wisdom, and public respect.",
        prediction_domain=["natal", "reputation"],
        historical_status=HistoricalStatus.DOCUMENTED.value, confidence="low",
    ),
    "jyotisha.yoga.chandra_mangala": PredictiveRule(
        rule_id="jyotisha.yoga.chandra_mangala", tradition="jyotisha", school="Parashari",
        name="Chandra-Mangala Yoga",
        description="Moon and Mars conjunct in the same Rashi.",
        historical_source="Brihat Parashara Hora Shastra, Yoga chapters",
        calculation="rashi(Moon) == rashi(Mars)",
        interpretation="Classically indicates business acumen and material drive; also cited as "
                       "a potential source of emotional volatility.",
        prediction_domain=["natal", "business", "finance"],
        historical_status=HistoricalStatus.DOCUMENTED.value, confidence="low",
    ),
    "jyotisha.yoga.budhaditya": PredictiveRule(
        rule_id="jyotisha.yoga.budhaditya", tradition="jyotisha", school="Parashari",
        name="Budhaditya Yoga",
        description="Sun and Mercury conjunct in the same Rashi.",
        historical_source="Brihat Parashara Hora Shastra, Yoga chapters",
        calculation="rashi(Sun) == rashi(Mercury)",
        interpretation="Classically indicates intelligence and communicative/analytical skill.",
        prediction_domain=["natal", "intellect", "communication"],
        historical_status=HistoricalStatus.DOCUMENTED.value, confidence="low",
    ),
    "jyotisha.yoga.kemadruma": PredictiveRule(
        rule_id="jyotisha.yoga.kemadruma", tradition="jyotisha", school="Parashari",
        name="Kemadruma Yoga (dosha)",
        description="No planet (other than the Sun) in the 2nd or 12th house from the Moon, "
                    "and no planet conjunct the Moon.",
        historical_source="Brihat Parashara Hora Shastra, Yoga chapters",
        calculation="planets_in_house(moon_house-1) union planets_in_house(moon_house+1) union "
                    "planets_conjunct_moon, excluding Sun, is empty",
        interpretation="Classically read as isolation/struggle unless cancelled by other factors "
                       "-- this engine reports the raw combination only, not cancellation rules "
                       "(a real, documented, but more elaborate sub-topic not implemented here).",
        prediction_domain=["natal", "general_hardship"],
        historical_status=HistoricalStatus.DOCUMENTED.value, confidence="low",
    ),
    "jyotisha.gochara.jupiter_saturn": PredictiveRule(
        rule_id="jyotisha.gochara.jupiter_saturn", tradition="jyotisha", school="Parashari (popular practice)",
        name="Rashi Gochara (Jupiter/Saturn transit from natal Moon)",
        description="Jupiter transiting the 2nd/5th/7th/9th/11th house from natal Moon, and "
                    "Saturn transiting the 3rd/6th/11th house from natal Moon, are read as "
                    "generally favorable transit windows; Saturn in the 12th/1st/2nd from natal "
                    "Moon is the well-known 'Sade Sati' period.",
        historical_source="Ubiquitous in contemporary Panchanga-based predictive practice; this "
                          "engine does not independently verify one single canonical primary-"
                          "source citation for the exact favorable-house list used, hence "
                          "historical_status=traditional rather than documented.",
        calculation="house(transiting Jupiter/Saturn, counted from natal Moon's Rashi)",
        interpretation="See description.",
        prediction_domain=["natal", "mundane", "timing"],
        historical_status=HistoricalStatus.TRADITIONAL.value, confidence="low",
    ),
}

_GOCHARA_JUPITER_FAVORABLE = {2, 5, 7, 9, 11}
_GOCHARA_SATURN_FAVORABLE = {3, 6, 11}
_SADE_SATI_HOUSES = {12, 1, 2}


def _house_from(target_sign_idx: int, from_sign_idx: int) -> int:
    return ((target_sign_idx - from_sign_idx) % 12) + 1


class JyotishaEngine(AstrologyEngine):
    tradition_name = "jyotisha"

    def is_applicable(self, context: PredictionContext) -> bool:
        # Parashari technique applies to any entity with real date+place (the
        # project's mundane-astrology rule) -- natal for persons, mundane
        # framing for collective entities, both already handled upstream by
        # mundane/entity_chart.py's identical computation path.
        return True

    def calculate(self, context: PredictionContext) -> Dict[str, Any]:
        natal = _shared.natal_chart(context)
        transit = _shared.transit_chart(context)
        asc_idx = natal.chart.ascendant_rashi.rashi_index
        grahas = natal.chart.grahas

        navamsa = {}
        for name, g in grahas.items():
            sign_idx = g.rashi.rashi_index
            deg_in_sign = g.rashi.degree_in_rashi
            navamsa_num = int(deg_in_sign // (30.0 / 9.0))
            navamsa_sign_idx = (sign_idx * 9 + navamsa_num) % 12
            navamsa[name] = {"sign": RASHI_NAMES[navamsa_sign_idx], "navamsa_number": navamsa_num + 1}

        moon_house = grahas["moon"].house
        jupiter_house = grahas.get("jupiter").house if "jupiter" in grahas else None
        mars_house = grahas.get("mars").house if "mars" in grahas else None
        sun_house = grahas.get("sun").house if "sun" in grahas else None
        mercury_house = grahas.get("mercury").house if "mercury" in grahas else None

        houses_occupied: Dict[int, List[str]] = {}
        for name, g in grahas.items():
            houses_occupied.setdefault(g.house, []).append(name)

        moon_sign_idx = grahas["moon"].rashi.rashi_index
        transit_jupiter_sign_idx = transit.grahas["jupiter"].rashi.rashi_index
        transit_saturn_sign_idx = transit.grahas["saturn"].rashi.rashi_index
        gochara_jupiter_house = _house_from(transit_jupiter_sign_idx, moon_sign_idx)
        gochara_saturn_house = _house_from(transit_saturn_sign_idx, moon_sign_idx)

        return {
            "zodiac_system": "sidereal", "calendar_system": "N/A",
            "coordinate_system": "ecliptic", "ayanamsha": "Lahiri",
            "epoch": context.birth_or_inception_date,
            "navamsa": navamsa, "moon_house": moon_house, "jupiter_house": jupiter_house,
            "mars_house": mars_house, "sun_house": sun_house, "mercury_house": mercury_house,
            "houses_occupied": houses_occupied,
            "moon_rashi": grahas["moon"].rashi.rashi_name,
            "gochara_jupiter_house_from_moon": gochara_jupiter_house,
            "gochara_saturn_house_from_moon": gochara_saturn_house,
            "time_accuracy": context.time_accuracy,
        }

    def interpret(self, calculation: Dict[str, Any]) -> Dict[str, Any]:
        themes: List[str] = []
        factors: List[Dict[str, Any]] = []
        rules_used: List[str] = []
        limitations: List[str] = []

        # Yogas
        moon_h, jup_h = calculation.get("moon_house"), calculation.get("jupiter_house")
        if jup_h is not None:
            diff = abs(moon_h - jup_h) % 12
            if diff in (0, 3, 6, 9):
                themes.append("reputation and public standing")
                factors.append({"name": "Gajakesari Yoga", "value": True, "rule_id": "jyotisha.yoga.gajakesari"})
                rules_used.append("jyotisha.yoga.gajakesari")

        houses_occ = calculation.get("houses_occupied", {})
        moon_house_planets = houses_occ.get(moon_h, [])
        if "mars" in moon_house_planets:
            themes.append("business drive and material ambition")
            factors.append({"name": "Chandra-Mangala Yoga", "value": True, "rule_id": "jyotisha.yoga.chandra_mangala"})
            rules_used.append("jyotisha.yoga.chandra_mangala")

        sun_h, merc_h = calculation.get("sun_house"), calculation.get("mercury_house")
        if sun_h is not None and merc_h is not None and sun_h == merc_h:
            themes.append("intellect and communication")
            factors.append({"name": "Budhaditya Yoga", "value": True, "rule_id": "jyotisha.yoga.budhaditya"})
            rules_used.append("jyotisha.yoga.budhaditya")

        adjacent = set()
        for h in ((moon_h % 12) + 1, ((moon_h - 2) % 12) + 1):
            adjacent.update(houses_occ.get(h, []))
        adjacent.update(moon_house_planets)
        adjacent.discard("moon")
        adjacent.discard("sun")
        if not adjacent:
            themes.append("isolation or unsupported effort (Kemadruma)")
            factors.append({"name": "Kemadruma Yoga (raw combination, cancellations not checked)",
                            "value": True, "rule_id": "jyotisha.yoga.kemadruma"})
            rules_used.append("jyotisha.yoga.kemadruma")
            limitations.append("Kemadruma cancellation rules (Yoga-bhanga) are documented but "
                              "not implemented -- this raw combination may be cancelled in the "
                              "full classical reading.")

        # Gochara
        gj = calculation.get("gochara_jupiter_house_from_moon")
        gs = calculation.get("gochara_saturn_house_from_moon")
        if gj in _GOCHARA_JUPITER_FAVORABLE:
            themes.append("expansion and growth (favorable Jupiter transit)")
            factors.append({"name": "Jupiter gochara house from Moon", "value": gj,
                            "rule_id": "jyotisha.gochara.jupiter_saturn", "weight_hint": "supportive"})
        else:
            factors.append({"name": "Jupiter gochara house from Moon", "value": gj,
                            "rule_id": "jyotisha.gochara.jupiter_saturn", "weight_hint": "neutral"})
        if gs in _SADE_SATI_HOUSES:
            themes.append("restriction and testing (Sade Sati)")
            factors.append({"name": "Saturn gochara (Sade Sati)", "value": gs,
                            "rule_id": "jyotisha.gochara.jupiter_saturn", "weight_hint": "opposing"})
        elif gs in _GOCHARA_SATURN_FAVORABLE:
            themes.append("disciplined, structural gains (favorable Saturn transit)")
            factors.append({"name": "Saturn gochara house from Moon", "value": gs,
                            "rule_id": "jyotisha.gochara.jupiter_saturn", "weight_hint": "supportive"})
        rules_used.append("jyotisha.gochara.jupiter_saturn")

        if not themes:
            themes.append("no strong classical yoga or favorable transit combination detected")

        prediction_text = (
            "Parashari Jyotisha reading: " + "; ".join(themes) + ". "
            f"(Moon Rashi: {calculation.get('moon_rashi')}; Navamsa placements computed for all grahas.)"
        )

        return {
            "themes": themes, "factors": factors, "rules_used": rules_used,
            "prediction_text": prediction_text,
            "signal_strength": None,  # no defensible numeric basis -- see task Section 13
            "historical_status": HistoricalStatus.DOCUMENTED.value,
            "limitations": limitations + (
                ["Birth/inception time was assumed (midnight) -- house-based yogas and Gochara "
                 "house counts carry real extra uncertainty."]
                if calculation.get("time_accuracy") != "documented" else []
            ),
            "time_window": None,
        }
