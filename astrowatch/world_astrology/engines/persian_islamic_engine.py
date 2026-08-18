"""
Astrowatch World Astrology -- Persian/Islamic (medieval Arabic) computational engine.
===================================================================
Implements two real, documented techniques from the medieval Perso-Arabic
astrological tradition (8th-13th century CE, building on Hellenistic and
Sassanid-Persian sources), per Kennedy & Pingree's "The Astrological History
of Masha'allah" (1971) and Abu Ma'shar's "Kitab al-Qiranat" (Book of
Religions and Dynasties / Great Conjunctions) as summarized in Yamamoto &
Burnett's critical edition, and Chris Brennan's "Hellenistic Astrology"
(2017) ch. 17 on the technique's transmission:

  1. Great Conjunctions (Jupiter-Saturn) and triplicity mutation -- Abu
     Ma'shar's method of tracking successive ~20-year Jupiter-Saturn
     conjunctions through the four zodiacal triplicities (fire/earth/air/
     water), used for large-scale political/dynastic/religious-history
     forecasting. Real numeric search against Swiss Ephemeris.
  2. Annual Revolution (Tasyir) -- this tradition inherited the Hellenistic
     profection/Lord-of-the-Year and Lots (Sahm, Arabic "Parts") techniques
     largely intact via Sassanid Persian transmission (Brennan 2017 ch. 17;
     Masha'allah's own natal/mundane works use profections extensively).
     Rather than reimplementing this identical math, this engine explicitly
     REUSES world_astrology.engines.hellenistic_engine.HellenisticEngine's
     calculate() output for the profection/Lord-of-Year and Lot-of-Fortune/
     Spirit figures, per this task's explicit instruction to reuse rather
     than duplicate.

NOT implemented: the broader catalog of additional named Arabic Lots (Sahm
al-Mulk "Lot of Kingship" etc.) beyond Fortune/Spirit -- their exact
classical formulas are not reliably in this project's sourced knowledge this
session; natal/horary/electional application beyond the annual-revolution
reuse above -- see NOT_IMPLEMENTED_TECHNIQUES.
"""

from typing import Any, Dict, List

from ..engine_interface import AstrologyEngine, PredictionContext, HistoricalStatus, PredictiveRule
from . import _shared
from .hellenistic_engine import HellenisticEngine
from kundli import compute_kundli

# Zodiacal triplicity groupings (fire/earth/air/water), keyed by this
# project's RASHI_NAMES convention (see hellenistic_engine.py).
TRIPLICITY = {
    "Mesha": "fire", "Simha": "fire", "Dhanu": "fire",
    "Vrishabha": "earth", "Kanya": "earth", "Makara": "earth",
    "Mithuna": "air", "Tula": "air", "Kumbha": "air",
    "Karka": "water", "Vrischika": "water", "Meena": "water",
}
RASHI_NAMES = ["Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya",
               "Tula", "Vrischika", "Dhanu", "Makara", "Kumbha", "Meena"]

NOT_IMPLEMENTED_TECHNIQUES = {
    "additional_arabic_lots": "Beyond Fortune and Spirit (reused from the Hellenistic engine), "
        "the medieval catalog includes many more named Sahms (e.g. Sahm al-Mulk 'Lot of "
        "Kingship', used for mundane/political astrology) whose exact classical formulas are "
        "not reliably sourced in this project this session -- not built, to avoid guessing a "
        "formula and mislabeling it as documented.",
    "horary": "Requires a query-moment chart with its own house-signification rule set -- not built this session.",
    "electional": "Requires searching a date range against multiple concurrent constraints -- not built this session.",
    "full_dynastic_history_synthesis": "Abu Ma'shar's system also included larger ~960-year "
        "'mutation of mutations' cycles and specific historical/religious correlations; only "
        "the ~20-year conjunction and triplicity-mutation layer is implemented here.",
}

RULES: Dict[str, PredictiveRule] = {
    "persian_islamic.great_conjunction": PredictiveRule(
        rule_id="persian_islamic.great_conjunction", tradition="persian_islamic", school="Abu Ma'shar (Kitab al-Qiranat)",
        name="Great Conjunction / Triplicity Mutation",
        description="The most recent Jupiter-Saturn conjunction (mean synodic period ~19.86 "
                    "years) before the prediction date, and which zodiacal triplicity "
                    "(fire/earth/air/water) it fell in -- successive conjunctions normally stay "
                    "within one triplicity for ~200 years before 'mutating' to the next.",
        historical_source="Abu Ma'shar, Kitab al-Qiranat (Book of Religions and Dynasties); "
                          "Kennedy & Pingree, The Astrological History of Masha'allah (1971).",
        calculation="Numeric root-find on (Jupiter_tropical_lon - Saturn_tropical_lon) mod 360 "
                    "== 0, searched backward from the prediction date in ~20-year steps.",
        interpretation="Great Conjunctions were used for large-scale political, dynastic, and "
                       "religious-history forecasting; a triplicity mutation (change of "
                       "element) was read as marking a major historical turning point.",
        prediction_domain=["mundane", "political", "long_range_timing"],
        historical_status=HistoricalStatus.DOCUMENTED.value, confidence="moderate",
    ),
    "persian_islamic.annual_revolution": PredictiveRule(
        rule_id="persian_islamic.annual_revolution", tradition="persian_islamic", school="Sassanid-Persian / Hellenistic transmission",
        name="Annual Revolution (Tasyir) -- reuses Hellenistic profection/Lots",
        description="This tradition inherited the Hellenistic profection (Lord of the Year) "
                    "and Lot of Fortune/Spirit techniques via Sassanid Persian transmission "
                    "largely unchanged; this rule explicitly reuses "
                    "hellenistic_engine.HellenisticEngine's output rather than reimplementing "
                    "identical math.",
        historical_source="Masha'allah's natal/mundane works; Brennan, Hellenistic Astrology "
                          "(2017) ch. 17 on the technique's transmission to the Persian/Arabic tradition.",
        calculation="See hellenistic_engine.py's hellenistic.profection / "
                    "hellenistic.lot_of_fortune / hellenistic.lot_of_spirit rules.",
        interpretation="Same as the corresponding Hellenistic rules.",
        prediction_domain=["natal", "mundane", "annual_timing"],
        historical_status=HistoricalStatus.DOCUMENTED.value, confidence="moderate",
    ),
}


def _jupiter_saturn_diff(jd: float) -> float:
    ch = compute_kundli(jd, 0.0, 0.0)
    j = ch.grahas["jupiter"].tropical_lon_deg
    s = ch.grahas["saturn"].tropical_lon_deg
    return (j - s + 180.0) % 360.0 - 180.0


def _find_most_recent_conjunction(before_jd: float) -> float:
    """Backward search: step in 200-day increments looking for a sign change
    in (Jupiter-Saturn) longitude difference, then bisect to the root."""
    step = 200.0
    jd_hi = before_jd
    f_hi = _jupiter_saturn_diff(jd_hi)
    jd_lo = jd_hi - step
    for _ in range(200):  # generous cap; synodic period ~7255 days / 200-day step ~ 37 steps needed
        f_lo = _jupiter_saturn_diff(jd_lo)
        if f_lo == 0.0:
            return jd_lo
        if (f_lo > 0) != (f_hi > 0):
            break
        jd_hi, f_hi = jd_lo, f_lo
        jd_lo -= step
    else:
        return jd_hi  # fallback, shouldn't happen within cap
    # Bisect between jd_lo and jd_hi.
    for _ in range(60):
        jd_mid = (jd_lo + jd_hi) / 2.0
        f_mid = _jupiter_saturn_diff(jd_mid)
        if (f_mid > 0) == (f_lo > 0):
            jd_lo, f_lo = jd_mid, f_mid
        else:
            jd_hi, f_hi = jd_mid, f_mid
    return (jd_lo + jd_hi) / 2.0


class PersianIslamicEngine(AstrologyEngine):
    tradition_name = "persian_islamic"

    def is_applicable(self, context: PredictionContext) -> bool:
        return True

    def calculate(self, context: PredictionContext) -> Dict[str, Any]:
        pred_jd = _shared.prediction_date_jd_ut(context)
        conj_jd = _find_most_recent_conjunction(pred_jd)
        conj_chart = compute_kundli(conj_jd, 0.0, 0.0)
        conj_lon = conj_chart.grahas["jupiter"].tropical_lon_deg
        sign_idx = int(conj_lon // 30) % 12
        conj_sign = RASHI_NAMES[sign_idx]
        triplicity = TRIPLICITY[conj_sign]
        years_since = (pred_jd - conj_jd) / 365.2422

        # Reuse the Hellenistic engine for annual-revolution figures.
        hellenistic = HellenisticEngine()
        hel_prediction = hellenistic.predict(context)

        return {
            "zodiac_system": "tropical", "calendar_system": "N/A", "coordinate_system": "ecliptic",
            "ayanamsha": "N/A (tropical)", "epoch": context.prediction_date or "today",
            "great_conjunction_jd": conj_jd,
            "great_conjunction_date": _shared.jd_to_iso_date(conj_jd),
            "great_conjunction_sign": conj_sign, "great_conjunction_triplicity": triplicity,
            "years_since_conjunction": round(years_since, 2),
            "hellenistic_reused_status": hel_prediction.status,
            "hellenistic_prediction_text": hel_prediction.prediction,
            "hellenistic_factors": hel_prediction.factors,
            "time_accuracy": context.time_accuracy,
        }

    def interpret(self, calculation: Dict[str, Any]) -> Dict[str, Any]:
        themes: List[str] = []
        factors: List[Dict[str, Any]] = []
        rules_used = ["persian_islamic.great_conjunction"]

        themes.append(f"most recent Great Conjunction in {calculation['great_conjunction_sign']} "
                     f"({calculation['great_conjunction_triplicity']} triplicity)")
        factors.append({"name": "Great Conjunction date", "value": calculation["great_conjunction_date"],
                        "rule_id": "persian_islamic.great_conjunction"})
        factors.append({"name": "Great Conjunction sign/triplicity",
                        "value": f"{calculation['great_conjunction_sign']} ({calculation['great_conjunction_triplicity']})",
                        "rule_id": "persian_islamic.great_conjunction"})
        factors.append({"name": "Years since Great Conjunction", "value": calculation["years_since_conjunction"],
                        "rule_id": "persian_islamic.great_conjunction"})

        prediction_text = (
            f"Persian/Islamic reading: the era's Great Conjunction fell in "
            f"{calculation['great_conjunction_sign']} ({calculation['great_conjunction_triplicity']} "
            f"triplicity) on {calculation['great_conjunction_date']}, "
            f"{calculation['years_since_conjunction']:.1f} years before the prediction date."
        )
        if calculation.get("hellenistic_reused_status") == "calculated":
            rules_used.append("persian_islamic.annual_revolution")
            themes.append("annual revolution (reused Hellenistic profection/Lots)")
            for f in calculation.get("hellenistic_factors", []):
                factors.append({**f, "rule_id": "persian_islamic.annual_revolution"})
            prediction_text += " " + (calculation.get("hellenistic_prediction_text") or "")

        limitations = [
            "Only the ~20-year Great-Conjunction/triplicity layer is implemented, not Abu "
            "Ma'shar's larger ~960-year 'mutation of mutations' cycle.",
            "Additional named Arabic Lots beyond Fortune/Spirit (e.g. Sahm al-Mulk) are not "
            "implemented -- see NOT_IMPLEMENTED_TECHNIQUES.",
        ]
        return {
            "themes": themes, "factors": factors, "rules_used": rules_used,
            "prediction_text": prediction_text, "signal_strength": None,
            "historical_status": HistoricalStatus.DOCUMENTED.value,
            "limitations": limitations, "time_window": None,
        }
