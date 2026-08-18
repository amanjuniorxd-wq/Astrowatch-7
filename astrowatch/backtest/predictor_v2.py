"""
Astrowatch backtest — predictor v2 (for BT-002+, NOT used by the already-frozen
ASTROWATCH-BT-001).

Built during the "VALIDATION HARDENING BEFORE BT-002" pass. `predictor.py`
(v1, unchanged) is exactly what BT-001 used and remains importable/runnable so BT-001
stays exactly reproducible; this module is new, additive code that also exercises the
newly-implemented lunar-pass (Ch. XVIII) and eclipse (Ptolemy Book II Ch. VI)
detectors (see rule_matcher.py and aspects.py) alongside the unchanged grahayuddha
detectors (Ch. XVII) that v1 already covered.

BLINDNESS: identical contract to v1 -- predict_v2() takes only a BlindInput (see
models.py) and never references an event field. See blindness.py's
check_predictor_source(), extended in this hardening pass to also scan this file (see
tests/backtest/test_blindness.py).

NOT YET RUN AS A FULL EXPERIMENT. This module exists so BT-002 CAN be executed later
under the pre-registered protocol (BACKTEST_PROTOCOL_BT002.md) -- this pass explicitly
does not run it end-to-end against the dataset (see Phase 19 of the hardening task).
"""

from datetime import datetime, timezone as dt_timezone
from typing import Dict, List, Tuple

from .models import BlindInput, Prediction
from .category_map import rule_domains_to_categories
from . import ephemeris_source
from .predictor import _sample_jd_uts, _is_outside_ayanamsha_validated_range

import forecast          # existing, unmodified
import rule_registry      # existing, unmodified (DATA only -- 19 rules, untouched)
import rule_matcher       # extended this pass (lunar_pass + eclipse now real)

_LUNAR_PASS_TARGET_PLANETS = ("mercury", "venus", "mars", "jupiter", "saturn")


def predict_v2(blind_input: BlindInput, experiment_id: str, prediction_id: str,
               allow_ayanamsha_fallback: bool = True) -> Prediction:
    bi = blind_input
    jd_uts = _sample_jd_uts(bi)

    fired_rule_ids = set()
    fired_categories = set()
    all_raw_evaluations = []
    ayanamsha_sources = set()
    precision_flags = set()
    panchang_snapshots = []
    rashi_nakshatra_snapshots = []
    any_extrapolated = any(_is_outside_ayanamsha_validated_range(jd) for jd in jd_uts)

    for jd_ut in jd_uts:
        full = ephemeris_source.compute_full_positions(jd_ut)
        precision_flags.add(full.precision_flag)

        # --- Unchanged path: grahayuddha (Ch. XVII) via the existing, unmodified
        # forecast.run_forecast() -- identical to v1's predictor.py, longitude only.
        date_label = f"JD{jd_ut:.4f}"
        result = forecast.run_forecast(
            jd_ut=jd_ut, date_label=date_label, forecast_start=bi.date, forecast_end=bi.date,
            tropical_longitudes_deg=full.tropical_longitudes_deg,
            region="GLOBAL", domain="GENERAL", temporal_precision="1-3 days",
            allow_ayanamsha_fallback=allow_ayanamsha_fallback,
        )
        ayanamsha_sources.add(result.sidereal["ayanamsha_source"])
        all_raw_evaluations.append({"jd_ut": jd_ut, "rules_evaluated": result.rules_evaluated,
                                     "source": "forecast.evaluate_rules (grahayuddha)"})
        panchang_snapshots.append(result.panchang)
        rashi_nakshatra_snapshots.append({
            "rashi": result.sidereal["rashi"], "nakshatra": result.sidereal["nakshatra"],
        })
        for ev in result.rules_fired:
            fired_rule_ids.add(ev["rule_id"])
            rule = rule_registry.rule_by_id(ev["rule_id"])
            if rule:
                fired_categories |= rule_domains_to_categories(rule.domain)

        # --- New path: lunar pass (Ch. XVIII), tropical longitude/latitude, no
        # ayanamsha dependency (zodiac_independent -- see rule_registry.py).
        moon_lon = full.tropical_longitudes_deg["moon"]
        moon_lat = full.tropical_latitudes_deg["moon"]
        planet_positions = {
            p: (full.tropical_longitudes_deg[p], full.tropical_latitudes_deg[p])
            for p in _LUNAR_PASS_TARGET_PLANETS
        }
        lunar_matches = rule_matcher.match_lunar_pass_rules(moon_lon, moon_lat, planet_positions)
        all_raw_evaluations.append({
            "jd_ut": jd_ut, "source": "rule_matcher.match_lunar_pass_rules",
            "matches": [m.rule.rule_id for m in lunar_matches],
        })
        for m in lunar_matches:
            fired_rule_ids.add(m.rule.rule_id)
            fired_categories |= rule_domains_to_categories(m.rule.domain)

        # --- New path: eclipse (Ptolemy Book II Ch. VI), tropical, real eclipse-
        # limit geometry.
        sun_lon = full.tropical_longitudes_deg["sun"]
        eclipse_matches = rule_matcher.check_and_match_eclipse(sun_lon, moon_lon, moon_lat)
        all_raw_evaluations.append({
            "jd_ut": jd_ut, "source": "rule_matcher.check_and_match_eclipse",
            "matches": [m.rule.rule_id for m in eclipse_matches],
        })
        for m in eclipse_matches:
            fired_rule_ids.add(m.rule.rule_id)
            fired_categories |= rule_domains_to_categories(m.rule.domain)

    predicted_fired = len(fired_rule_ids) > 0
    ayanamsha_source = (
        "live_swisseph" if ayanamsha_sources == {"live_swisseph"}
        else ("mixed" if len(ayanamsha_sources) > 1 else next(iter(ayanamsha_sources), "unknown"))
    )
    precision_flag = "MOSEPH" if "MOSEPH" in precision_flags else ("SWIEPH" if precision_flags else "unknown")

    return Prediction(
        prediction_id=prediction_id, experiment_id=experiment_id, test_case_id=bi.test_case_id,
        predicted_at=datetime.now(dt_timezone.utc).isoformat(timespec="seconds"),
        predicted_fired=predicted_fired,
        predicted_categories=sorted(fired_categories),
        predicted_subtypes=[],  # still no subtype-level rules in the registry
        rule_matches=sorted(fired_rule_ids),
        confidence_score=None,
        astronomical_inputs_jd_ut=jd_uts,
        ayanamsha_source=ayanamsha_source,
        ephemeris_precision_flag=precision_flag,
        panchang_snapshot={"samples": panchang_snapshots},
        rashi_nakshatra_snapshot={"samples": rashi_nakshatra_snapshots},
        raw_rule_evaluations=all_raw_evaluations,
        astronomy_extrapolated_unvalidated=any_extrapolated,
    )
