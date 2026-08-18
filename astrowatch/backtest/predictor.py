"""
Astrowatch backtest — the blind predictor.

predict(blind_input: BlindInput) -> Prediction is the ONLY function in this module
that matters for blindness. It takes a BlindInput (date / time-if-known /
timezone-if-known / location-precision-if-known -- see models.py) and returns a
Prediction. It never receives, imports, or references an Event, a canonical_event_id,
a verification_status, a description, or a source. See blindness.py for an automated
AST-based check of this claim (mirrors historical/tests' own AST-based independence
check, same technique).

Internally this function only calls:
  - ephemeris_source.compute_tropical_longitudes()  (this package, real local pyswisseph)
  - forecast.run_forecast()                          (EXISTING, UNMODIFIED)
which in turn calls ayanamsha.py / panchang.py / rashi_nakshatra.py / rule_registry.py
(all EXISTING, UNMODIFIED).

TIME-PRECISION MODES (spec section 9) -- implemented here, not in forecast.py:
  MODE_A_EXACT_TIME:  one sample, at the documented local time converted to UTC.
  MODE_B_DATE_ONLY:   FOUR samples at fixed UTC hours (00, 06, 12, 18) on the given
                      calendar date. This is a deliberate, pre-registered choice: it
                      does NOT claim to know the event's actual time (that is exactly
                      what MODE_B means -- the time is unknown), it instead asks "did
                      any qualifying planetary configuration exist at ANY point during
                      this day," an existential day-level question, not a fabricated
                      instant. The four hours were chosen for even coverage of the
                      24h cycle, fixed BEFORE this experiment ran, identical for every
                      MODE_B case -- never adjusted per-event.
  MODE_C_TIME_WINDOW: for events whose start_time is only APPROXIMATE (a real,
                      sourced value, just not certified exact), sample every hour in
                      a +/-3h window around that documented approximate time (7
                      samples) and again take the union of fired rules. The 3-hour
                      tolerance is a fixed, pre-registered choice, not tuned per case.
A test case's predicted_fired / predicted_categories / rule_matches is the UNION
across all samples taken for that case. This means MODE_B and MODE_C cases have more
chances to trigger a rule than MODE_A cases (a real methodological asymmetry, not
hidden -- see KNOWN_LIMITATIONS in the backtest report and metrics.py's per-mode
breakdown).
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone as dt_timezone
from typing import List, Optional
from zoneinfo import ZoneInfo

from .models import BlindInput, Prediction
from .category_map import rule_domains_to_categories
from . import ephemeris_source

import coordinates          # existing, unmodified
import forecast              # existing, unmodified

# Reference-table bounds of ayanamsha.py's own cross_check() validation (see
# ayanamsha.SWISSEPH_MODE1_REFERENCE) -- outside this window the linear ayanamsha
# fallback (used because the live network path is blocked in this sandbox, see
# ASTRONOMY_METHODOLOGY note in engine.py) is an unvalidated extrapolation.
_AYANAMSHA_VALIDATED_YEAR_MIN = 1900
_AYANAMSHA_VALIDATED_YEAR_MAX = 2050

_MODE_B_UTC_HOURS = [0.0, 6.0, 12.0, 18.0]
_MODE_C_WINDOW_HOURS = [-3, -2, -1, 0, 1, 2, 3]


def _parse_date(date_str: str):
    y, m, d = (int(x) for x in date_str.split("-"))
    return y, m, d


def _local_to_utc_hour(date_str: str, hhmm: str, tzname: Optional[str]) -> float:
    """Returns the fractional UTC hour-of-day for a legitimately-known local time.
    If timezone is unknown, treats the given time AS ALREADY UTC rather than
    fabricating a timezone -- this only happens if input_timezone is genuinely
    absent, which does not occur for any MODE_A/MODE_C case in the current dataset
    (every EXACT/APPROXIMATE-time event carries a timezone -- see HIST-002)."""
    y, m, d = _parse_date(date_str)
    hh, mm = (int(x) for x in hhmm.split(":"))
    if tzname:
        local_dt = datetime(y, m, d, hh, mm, tzinfo=ZoneInfo(tzname))
        utc_dt = local_dt.astimezone(dt_timezone.utc)
    else:
        utc_dt = datetime(y, m, d, hh, mm, tzinfo=dt_timezone.utc)
    return utc_dt.year, utc_dt.month, utc_dt.day, utc_dt.hour + utc_dt.minute / 60.0


def _sample_jd_uts(bi: BlindInput) -> List[float]:
    y, m, d = _parse_date(bi.date)

    if bi.time_precision_mode == "MODE_A_EXACT_TIME":
        if not bi.time_hhmm:
            raise ValueError(f"{bi.test_case_id}: MODE_A_EXACT_TIME requires time_hhmm")
        yy, mm_, dd, hour = _local_to_utc_hour(bi.date, bi.time_hhmm, bi.timezone)
        return [coordinates.julian_day(yy, mm_, dd, hour)]

    if bi.time_precision_mode == "MODE_B_DATE_ONLY":
        # No legitimately known time -- sample fixed UTC hours of the GIVEN calendar
        # date directly (the date itself IS known; only the time-of-day is not).
        return [coordinates.julian_day(y, m, d, h) for h in _MODE_B_UTC_HOURS]

    if bi.time_precision_mode == "MODE_C_TIME_WINDOW":
        if not bi.time_hhmm:
            raise ValueError(f"{bi.test_case_id}: MODE_C_TIME_WINDOW requires time_hhmm")
        yy, mm_, dd, center_hour = _local_to_utc_hour(bi.date, bi.time_hhmm, bi.timezone)
        base = datetime(yy, mm_, dd, tzinfo=dt_timezone.utc) + timedelta(hours=center_hour)
        jds = []
        for offset in _MODE_C_WINDOW_HOURS:
            sample_dt = base + timedelta(hours=offset)
            jds.append(coordinates.julian_day(
                sample_dt.year, sample_dt.month, sample_dt.day,
                sample_dt.hour + sample_dt.minute / 60.0,
            ))
        return jds

    raise ValueError(f"Unknown time_precision_mode: {bi.time_precision_mode!r}")


def _is_outside_ayanamsha_validated_range(jd_ut: float) -> bool:
    # Cheap inverse of coordinates.julian_day: derive the calendar year via the
    # datetime module through a known JD epoch offset is unnecessary here -- we
    # already have the original date string upstream; this helper is kept purely
    # numeric for use directly on jd_ut values collected during sampling.
    # JD 2415020.5 = 1900-01-01 00:00 UT (see ayanamsha.SWISSEPH_MODE1_REFERENCE).
    jd_1900 = 2415020.5
    jd_2050 = 2469807.5
    return not (jd_1900 <= jd_ut <= jd_2050)


def predict(blind_input: BlindInput, experiment_id: str, prediction_id: str,
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
        eph = ephemeris_source.compute_tropical_longitudes(jd_ut)
        precision_flags.add(eph.precision_flag)
        date_label = f"JD{jd_ut:.4f}"
        result = forecast.run_forecast(
            jd_ut=jd_ut,
            date_label=date_label,
            forecast_start=bi.date,
            forecast_end=bi.date,
            tropical_longitudes_deg=eph.tropical_longitudes_deg,
            region="GLOBAL",   # structurally required -- see models.BlindInput docstring
            domain="GENERAL",  # forecast.evaluate_rules() does not filter by this value;
                                # every rule in RULES is evaluated regardless (verified by
                                # reading forecast.py -- domain only labels the result)
            temporal_precision="1-3 days",
            allow_ayanamsha_fallback=allow_ayanamsha_fallback,
        )
        ayanamsha_sources.add(result.sidereal["ayanamsha_source"])
        all_raw_evaluations.append({
            "jd_ut": jd_ut,
            "rules_evaluated": result.rules_evaluated,
        })
        panchang_snapshots.append(result.panchang)
        rashi_nakshatra_snapshots.append({
            "rashi": result.sidereal["rashi"], "nakshatra": result.sidereal["nakshatra"],
        })
        for ev in result.rules_fired:
            fired_rule_ids.add(ev["rule_id"])
            # Recover the rule's own domain list from rule_registry directly (not
            # from historical data) -- ev only carries rule_id/tradition/source/etc,
            # not domain, so look the rule back up in the UNMODIFIED registry.
            import rule_registry
            rule = rule_registry.rule_by_id(ev["rule_id"])
            if rule:
                fired_categories |= rule_domains_to_categories(rule.domain)

    predicted_fired = len(fired_rule_ids) > 0
    ayanamsha_source = (
        "live_swisseph" if ayanamsha_sources == {"live_swisseph"}
        else ("mixed" if len(ayanamsha_sources) > 1 else next(iter(ayanamsha_sources), "unknown"))
    )
    precision_flag = "MOSEPH" if "MOSEPH" in precision_flags else ("SWIEPH" if precision_flags else "unknown")

    return Prediction(
        prediction_id=prediction_id,
        experiment_id=experiment_id,
        test_case_id=bi.test_case_id,
        predicted_at=datetime.now(dt_timezone.utc).isoformat(timespec="seconds"),
        predicted_fired=predicted_fired,
        predicted_categories=sorted(fired_categories),
        predicted_subtypes=[],  # registry has no subtype-level rules -- never fabricated
        rule_matches=sorted(fired_rule_ids),
        confidence_score=None,  # forecast.py's own confidence is derived from
                                  # historical_sample_size which forecast.py itself
                                  # always sets to 0 (no backtest existed before this
                                  # one) -- see forecast._confidence_from_sample_size.
                                  # Recording None here rather than forecast.py's
                                  # UNVALIDATED string keeps this column numeric/NULL
                                  # for calibration code to skip cleanly.
        astronomical_inputs_jd_ut=jd_uts,
        ayanamsha_source=ayanamsha_source,
        ephemeris_precision_flag=precision_flag,
        panchang_snapshot={"samples": panchang_snapshots},
        rashi_nakshatra_snapshot={"samples": rashi_nakshatra_snapshots},
        raw_rule_evaluations=all_raw_evaluations,
        astronomy_extrapolated_unvalidated=any_extrapolated,
    )
