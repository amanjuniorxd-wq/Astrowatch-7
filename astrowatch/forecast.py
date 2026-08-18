"""
Astrowatch — experimental forecasting mode
=============================================
FORECASTING = EXPERIMENTAL / ENABLED (per explicit user authorization). This is a state
change from the prior hard lock, NOT a claim of validation -- see PRODUCTION_STATUS
below and every ForecastResult's own `validation_status` field, which is UNVALIDATED for
every possible output right now (no historical backtest has ever been run in this
project -- see VALIDATION_REPORT.md's gate table, still unchecked on that item).

PIPELINE (exactly as specified) -----------------------------------------------------
    future date/time
        -> astronomical engine (ephemeris_client.py / JPL Horizons, TROPICAL longitudes)
        -> Lahiri sidereal conversion where applicable (ayanamsha.py, live-SE-primary)
        -> Rāśi / Nakshatra (rashi_nakshatra.py)
        -> Panchang (panchang.py -- PARTIAL: tithi/vara/lunar-nakshatra only; yoga and
           karana are NOT implemented, see panchang.py docstring)
        -> configuration detection (aspects.py, tradition-gated dispatcher)
        -> rule registry lookup (rule_registry.py -- UNMODIFIED, no new rules added here)
        -> geography safeguard (this file's geographic_specificity_for_rule(), a plain
           data lookup against each rule's OWN documented `geography` field -- no LLM
           interpretation, see that function's docstring)
        -> historical evidence lookup (NONE EXISTS in this project yet -- every
           candidate's historical_sample_size is 0 until a real backtest is built and
           run; this file does not fabricate one)
        -> forecast candidate -> confidence/evidence classification -> ForecastResult

HARD SAFEGUARDS (explicit, not to be removed without a genuine validation failure) ---
  1. Only rule_registry.RULES is ever queried -- this file invents nothing.
  2. Rules with zodiac_requirement == "sidereal_unresolved" (BS-19, BS-42, the
     directional component of BS-20) are ALWAYS excluded, unconditionally.
  3. geographic_specificity_for_rule() never manufactures a country mapping a rule's
     own `geography` field doesn't already, explicitly support.
  4. run_forecast(..., allow_ayanamsha_fallback=False) (the default for --live) RAISES
     ProductionCalculationUnavailable if the live Swiss Ephemeris path fails, rather
     than silently substituting the linear fallback. Pass
     allow_ayanamsha_fallback=True (only via --dev-allow-fallback) to opt into the
     fallback explicitly, for development use only.
  5. Confidence is always one of LOW / MODERATE / HIGH / UNVALIDATED, derived only from
     historical_sample_size -- never a manufactured percentage.
  6. Every ForecastResult carries status="EXPERIMENTAL" and an explicit
     validation_status -- never presented as scientifically validated.
  7. BS-19 / BS-42 / BS-20 are never resolved by this file. They appear, if at all, as
     HISTORICALLY UNRESOLVED -- NOT USED.

STATUS: this file's CLI/argparse plumbing and pipeline functions are real Python, not
executed by an interpreter this pass (sandbox unavailable, see VALIDATION_REPORT.md
Phase 10). The PIPELINE LOGIC was exercised BY HAND this pass against real, live-fetched
JPL Horizons + Swiss Ephemeris data for 2026-09-01 -- see FORECAST_RUN_2026_09_USA.md
for that full hand-run and its result. Running `python3 forecast.py ...` will use the
real ephemeris_client.py (which itself has never executed either -- see AUDIT.md) rather
than a hand-computed substitute; until that has actually run, treat this file as
"designed and hand-verified," not "proven."
"""

import argparse
import datetime
import sys
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional

from ayanamsha import (
    lahiri_ayanamsha_deg, LiveSwissEphemerisUnavailable, PARTIALLY_VALIDATED,
)
import rashi_nakshatra as rn
import panchang
from aspects import detect_configuration
from rule_registry import RULES, Rule


ASTROWATCH_VERSION = "0.1.0-experimental"
FORECASTING_STATUS = "EXPERIMENTAL"

VALID_DOMAINS = {"POLITICAL", "MILITARY", "ECONOMIC", "SOCIAL", "ENVIRONMENTAL",
                  "TECHNOLOGY", "GENERAL"}
VALID_TEMPORAL_WINDOWS = {"1-3 days", "7 days", "30 days", "90 days"}


class ProductionCalculationUnavailable(Exception):
    """Raised by run_forecast() in production (--live, no dev fallback opt-in) when the
    live Swiss Ephemeris path is unreachable. Deliberately NOT caught anywhere that
    would let a silent fallback slip through -- see HARD SAFEGUARD #4 above."""


# --- Safeguard 3: geography, data-driven, no interpretation --------------------------

def geographic_specificity_for_rule(rule: Rule) -> str:
    """
    Returns the rule's own documented geography IF AND ONLY IF that field is present in
    a tiny, explicit allowlist mapping to a real modern country/region. As of this pass
    the allowlist is EMPTY: no rule in rule_registry.py documents a mechanism that maps
    to a specific modern nation-state.
      - BS rules: "general" (no mechanism at all) or ancient/extinct peoples
        (Mlecchas, Śūdras, Śaka, Bāhlīka, Sindh, Pahlava, Yavana) that this project does
        not attempt to equate with any modern country.
      - PT-II-3 / PT-II-6 (Ptolemy): a real geographic mechanism exists (triplicity ->
        ancient-world quadrant -> named ancient countries), but that mechanism's known
        world (Europe / southern Asia / northern Asia / Africa-Libya, as understood by
        2nd-century Alexandria) does not include the Americas at all. Mapping it onto
        "USA" would be inventing coverage the source doesn't have.
    Returns "NONE" for every current rule. Do not add an entry here based on an
    inference layered on top of a rule's `geography` field -- only if the field ITSELF,
    as extracted from the source, already names an unambiguous modern country/region.
    """
    _MODERN_MAPPING_ALLOWLIST: Dict[str, str] = {}
    return _MODERN_MAPPING_ALLOWLIST.get(rule.geography, "NONE")


# --- Data classes ----------------------------------------------------------------------

@dataclass
class AstronomicalSnapshot:
    jd_ut: float
    date_label: str
    tropical_longitudes_deg: Dict[str, float]   # J2000-fixed, see caveat in docstring
    frame_caveat: str = (
        "J2000-fixed ecliptic longitudes (no precession-of-date correction applied) -- "
        "consistent with coordinates.ra_dec_to_ecliptic_j2000()'s documented behavior "
        "elsewhere in this project. Differs from true equinox-of-date tropical "
        "longitude by roughly (years since 2000) * 50.29 arcsec -- e.g. ~0.36 deg for "
        "2026. PLANET-TO-PLANET SEPARATIONS are unaffected (a common-mode offset "
        "cancels out), but absolute sign/degree placement carries this small caveat."
    )


@dataclass
class SiderealSnapshot:
    ayanamsha_deg: float
    ayanamsha_source: str    # "live_swisseph" | "linear_fallback"
    sidereal_longitudes_deg: Dict[str, float]
    rashi: Dict[str, rn.RashiPlacement]
    nakshatra: Dict[str, rn.NakshatraPlacement]


@dataclass
class RuleEvaluation:
    rule_id: str
    tradition: str
    source: str
    zodiac_requirement: str
    fired: bool
    reason: str
    geographic_specificity: str


@dataclass
class ForecastResult:
    prediction_id: str
    created_at_utc: str
    forecast_start: str
    forecast_end: str
    region: str
    domain: str
    temporal_precision: str
    status: str = "EXPERIMENTAL"
    validation_status: str = PARTIALLY_VALIDATED  # module-level constant, never upgraded here
    astronomical: Optional[dict] = None
    sidereal: Optional[dict] = None
    panchang: Optional[dict] = None
    rules_evaluated: List[dict] = field(default_factory=list)
    rules_fired: List[dict] = field(default_factory=list)
    historical_sample_size: int = 0
    historical_matches: int = 0
    historical_misses: int = 0
    baseline: Optional[str] = None
    evidence_level: str = "UNVALIDATED"
    confidence: str = "UNVALIDATED"
    prediction_text: str = ""
    no_forecast_reasons: List[str] = field(default_factory=list)


def _confidence_from_sample_size(n: int) -> str:
    """Confidence is derived ONLY from historical_sample_size -- never manufactured.
    Thresholds are a simple, explicit, pre-committed rule, not tuned to any result."""
    if n == 0:
        return "UNVALIDATED"
    if n < 10:
        return "LOW"
    if n < 30:
        return "MODERATE"
    return "HIGH"


def get_astronomical_snapshot(jd_ut: float, date_label: str,
                                tropical_longitudes_deg: Dict[str, float]) -> AstronomicalSnapshot:
    """
    Thin wrapper -- this file does NOT fetch ephemeris data itself. Callers must supply
    real tropical longitudes obtained from ephemeris_client.py (JPL Horizons) or an
    equivalent real source. This function refuses fabricated input the only way it
    practically can: by requiring the caller to have already done the real fetch: it
    does not compute or invent longitudes on its own.
    """
    return AstronomicalSnapshot(jd_ut=jd_ut, date_label=date_label,
                                  tropical_longitudes_deg=dict(tropical_longitudes_deg))


def get_sidereal_snapshot(astro: AstronomicalSnapshot,
                            allow_ayanamsha_fallback: bool) -> SiderealSnapshot:
    """
    HARD SAFEGUARD #4 lives here: if allow_ayanamsha_fallback is False (production
    default) and the live Swiss Ephemeris query fails, this raises
    ProductionCalculationUnavailable instead of silently using the linear model.
    """
    try:
        result = lahiri_ayanamsha_deg(astro.jd_ut, allow_fallback=allow_ayanamsha_fallback)
    except LiveSwissEphemerisUnavailable as e:
        raise ProductionCalculationUnavailable(
            "PRODUCTION CALCULATION UNAVAILABLE -- live Swiss Ephemeris query failed "
            f"and allow_ayanamsha_fallback=False (production mode): {e}"
        ) from e

    sidereal_lons = {
        body: (lon - result.ayanamsha_deg) % 360.0
        for body, lon in astro.tropical_longitudes_deg.items()
    }
    rashi = {body: rn.rashi_for_longitude(lon) for body, lon in sidereal_lons.items()}
    nakshatra = {body: rn.nakshatra_for_longitude(lon) for body, lon in sidereal_lons.items()}
    return SiderealSnapshot(
        ayanamsha_deg=result.ayanamsha_deg, ayanamsha_source=result.source,
        sidereal_longitudes_deg=sidereal_lons, rashi=rashi, nakshatra=nakshatra,
    )


def get_panchang(jd_ut: float, astro: AstronomicalSnapshot,
                   sidereal: SiderealSnapshot) -> Optional[panchang.PanchangPartial]:
    if "sun" not in astro.tropical_longitudes_deg or "moon" not in astro.tropical_longitudes_deg:
        return None
    return panchang.compute_partial_panchang(
        jd_ut=jd_ut,
        sun_tropical_lon_deg=astro.tropical_longitudes_deg["sun"],
        moon_tropical_lon_deg=astro.tropical_longitudes_deg["moon"],
        moon_sidereal_lon_deg=sidereal.sidereal_longitudes_deg["moon"],
    )


def evaluate_rules(astro: AstronomicalSnapshot, region: str) -> List[RuleEvaluation]:
    """
    Queries rule_registry.RULES ONLY (safeguard #1). Excludes sidereal_unresolved rules
    unconditionally (safeguard #2). Applies the geography safeguard (#3): a rule can
    only be considered for a NON-"GLOBAL" region if its OWN geography field maps to that
    region via the explicit allowlist (currently empty).
    """
    evaluations: List[RuleEvaluation] = []

    # Only the classical 5 "graha" (not luminaries) participate in graha-yuddha, per
    # the extracted BS Ch. XVII text and pipeline.py's existing usage convention.
    graha_yuddha_bodies = {
        b: lon for b, lon in astro.tropical_longitudes_deg.items()
        if b in ("mercury", "venus", "mars", "jupiter", "saturn")
    }
    grahayuddha_classes = (
        detect_configuration("brihat_samhita", graha_yuddha_bodies)
        if len(graha_yuddha_bodies) >= 2 else []
    )
    fired_pairs = {(c.body_a, c.body_b): c.conjunction_class for c in grahayuddha_classes}

    for rule in RULES:
        geo_spec = geographic_specificity_for_rule(rule)
        if region.upper() != "GLOBAL" and geo_spec == "NONE":
            evaluations.append(RuleEvaluation(
                rule_id=rule.rule_id, tradition=rule.tradition,
                source=f"{rule.author}, Ch. {rule.chapter}, {rule.citation}",
                zodiac_requirement=rule.zodiac_requirement, fired=False,
                reason=f"No documented geographic mechanism connects this rule to "
                       f"'{region}' -- rule's own geography field is "
                       f"{rule.geography!r}. Not evaluated further for this region "
                       f"(would require inventing a mapping, which is disallowed).",
                geographic_specificity="NONE",
            ))
            continue

        if rule.zodiac_requirement == "sidereal_unresolved":
            evaluations.append(RuleEvaluation(
                rule_id=rule.rule_id, tradition=rule.tradition,
                source=f"{rule.author}, Ch. {rule.chapter}, {rule.citation}",
                zodiac_requirement=rule.zodiac_requirement, fired=False,
                reason="HISTORICALLY UNRESOLVED -- NOT USED. "
                       + (rule.zodiac_requirement_note or ""),
                geographic_specificity=geo_spec,
            ))
            continue

        if rule.trigger_type in ("grahayuddha_class", "grahayuddha_defeat"):
            fired = False
            reason = "No qualifying conjunction found among the classical 5 planets " \
                      "at this configuration (nearest pair still tens of degrees " \
                      "apart)."
            for (a, b), cls in fired_pairs.items():
                if rule.trigger_type == "grahayuddha_class" and cls == rule.trigger_params.get("class"):
                    fired = True
                    reason = (f"{a}-{b} conjunction classified '{cls}' using "
                              f"aspects.GRAHAYUDDHA_PLACEHOLDER_THRESHOLDS_DEG -- those "
                              f"thresholds are UNSOURCED PLACEHOLDERS (see aspects.py), "
                              f"so even a nominal 'fire' here is not presented as a "
                              f"legitimate rule match until real thresholds are sourced.")
                elif rule.trigger_type == "grahayuddha_defeat":
                    want_defeated = rule.trigger_params.get("defeated")
                    want_victor = rule.trigger_params.get("victor")
                    if {a, b} == {want_defeated, want_victor}:
                        fired = True
                        reason = (f"{a}-{b} conjunction found ('{cls}' class, "
                                  f"UNSOURCED placeholder thresholds -- see aspects.py) "
                                  f"-- defeated-body determination (which of the two is "
                                  f"'defeated') is NOT implemented in this project and "
                                  f"was not attempted here.")
            evaluations.append(RuleEvaluation(
                rule_id=rule.rule_id, tradition=rule.tradition,
                source=f"{rule.author}, Ch. {rule.chapter}, {rule.citation}",
                zodiac_requirement=rule.zodiac_requirement, fired=fired, reason=reason,
                geographic_specificity=geo_spec,
            ))
            continue

        # Every other trigger_type (lunar_pass needs ecliptic latitude -- not computed
        # by this project; eclipse -- requires confirming an actual eclipse, not
        # attempted here; multi_planet_shape / named_meeting_type -- no implemented
        # detector exists yet) is honestly marked NOT EVALUATED rather than silently
        # skipped or falsely marked "no match."
        evaluations.append(RuleEvaluation(
            rule_id=rule.rule_id, tradition=rule.tradition,
            source=f"{rule.author}, Ch. {rule.chapter}, {rule.citation}",
            zodiac_requirement=rule.zodiac_requirement, fired=False,
            reason=f"NOT EVALUATED -- no detector implemented for "
                   f"trigger_type={rule.trigger_type!r} in this project yet "
                   f"(see AUDIT.md capability gaps).",
            geographic_specificity=geo_spec,
        ))

    return evaluations


def run_forecast(
    jd_ut: float, date_label: str, forecast_start: str, forecast_end: str,
    tropical_longitudes_deg: Dict[str, float], region: str = "GLOBAL",
    domain: str = "GENERAL", temporal_precision: str = "7 days",
    allow_ayanamsha_fallback: bool = False,
) -> ForecastResult:
    if domain.upper() not in VALID_DOMAINS:
        raise ValueError(f"domain must be one of {sorted(VALID_DOMAINS)}")

    astro = get_astronomical_snapshot(jd_ut, date_label, tropical_longitudes_deg)
    sidereal = get_sidereal_snapshot(astro, allow_ayanamsha_fallback)  # may raise
    panchang_result = get_panchang(jd_ut, astro, sidereal)
    evaluations = evaluate_rules(astro, region)

    fired = [e for e in evaluations if e.fired]
    prediction_id = f"AW-{date_label.replace('-', '').replace(' ', 'T').replace(':', '')}-{region}-{domain}"

    no_forecast_reasons: List[str] = []
    if not fired:
        no_forecast_reasons.append(
            f"No rule in the current registry legitimately fired for region={region!r}, "
            f"domain={domain!r} at this configuration."
        )
        blocked_geo = [e for e in evaluations if e.geographic_specificity == "NONE"
                        and region.upper() != "GLOBAL"]
        if blocked_geo:
            no_forecast_reasons.append(
                f"{len(blocked_geo)} rule(s) were excluded specifically because none of "
                f"them document a geographic mechanism connecting to '{region}' -- see "
                f"HARD SAFEGUARD #3."
            )
        blocked_unresolved = [e for e in evaluations if e.zodiac_requirement == "sidereal_unresolved"]
        if blocked_unresolved:
            no_forecast_reasons.append(
                f"{len(blocked_unresolved)} rule(s) remain HISTORICALLY UNRESOLVED "
                f"(BS-19/BS-42/BS-20) and are never used, regardless of configuration."
            )
        not_evaluated = [e for e in evaluations if "NOT EVALUATED" in e.reason]
        if not_evaluated:
            no_forecast_reasons.append(
                f"{len(not_evaluated)} rule(s) have no implemented detector in this "
                f"project yet (missing capability, not a negative result)."
            )
        no_forecast_reasons.append(
            "historical_sample_size=0 for every candidate -- no backtest has ever been "
            "run in this project, so even a fired rule would carry confidence=UNVALIDATED."
        )

    result = ForecastResult(
        prediction_id=prediction_id,
        created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        forecast_start=forecast_start, forecast_end=forecast_end,
        region=region, domain=domain, temporal_precision=temporal_precision,
        astronomical=asdict(astro),
        sidereal={
            "ayanamsha_deg": sidereal.ayanamsha_deg,
            "ayanamsha_source": sidereal.ayanamsha_source,
            "sidereal_longitudes_deg": sidereal.sidereal_longitudes_deg,
            "rashi": {b: asdict(p) for b, p in sidereal.rashi.items()},
            "nakshatra": {b: asdict(p) for b, p in sidereal.nakshatra.items()},
        },
        panchang=asdict(panchang_result) if panchang_result else None,
        rules_evaluated=[asdict(e) for e in evaluations],
        rules_fired=[asdict(e) for e in fired],
        historical_sample_size=0,
        historical_matches=0,
        historical_misses=0,
        baseline=None,
        evidence_level="UNVALIDATED" if not fired else "LIMITED",
        confidence=_confidence_from_sample_size(0),
        prediction_text=(
            "NO FORECAST." if not fired else
            "Traditional rule(s) matched this configuration; historical evidence is "
            "limited (no backtest has been run). See rules_fired for exact sourced "
            "interpretation text -- this system does not generate free-text "
            "predictions beyond what a matched rule's own interpretation states."
        ),
        no_forecast_reasons=no_forecast_reasons,
    )
    return result


def format_dry_run_report(result: ForecastResult) -> str:
    lines = [
        "FORECAST GENERATED",
        "------------------",
        f"Prediction ID:   {result.prediction_id}",
        f"Created (UTC):   {result.created_at_utc}",
        f"Window:          {result.forecast_start} to {result.forecast_end} "
        f"({result.temporal_precision})",
        f"Region:          {result.region}",
        f"Domain:          {result.domain}",
        f"Status:          {result.status}",
        f"Validation:      {result.validation_status}",
        f"Confidence:      {result.confidence}",
        f"Evidence:        {result.evidence_level}",
        f"Historical N:    {result.historical_sample_size}",
        f"Rules fired:     {len(result.rules_fired)} / {len(result.rules_evaluated)} evaluated",
        f"Interpretation:  {result.prediction_text}",
    ]
    if result.no_forecast_reasons:
        lines.append("Reasons:")
        for r in result.no_forecast_reasons:
            lines.append(f"  - {r}")
    lines.append("")
    lines.append("NO POSTING PERFORMED.")
    return "\n".join(lines)


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Astrowatch experimental forecasting (EXPERIMENTAL, not validated)")
    p.add_argument("--date")
    p.add_argument("--start-date")
    p.add_argument("--end-date")
    p.add_argument("--location")
    p.add_argument("--region", default="GLOBAL")
    p.add_argument("--domain", default="GENERAL")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--live", action="store_true")
    p.add_argument("--dev-allow-fallback", action="store_true",
                    help="DEV ONLY: allow the linear ayanamsha fallback instead of "
                         "requiring the live Swiss Ephemeris path. Never implied by "
                         "--live.")
    return p


def main(argv=None):
    args = build_arg_parser().parse_args(argv)
    if not args.dry_run and not args.live:
        print("Specify --dry-run or --live.", file=sys.stderr)
        return 2
    print(
        "NOTE: this CLI entry point requires a real ephemeris fetch "
        "(ephemeris_client.py / JPL Horizons) that this session's sandbox cannot "
        "execute. See FORECAST_RUN_2026_09_USA.md for a hand-executed run using real, "
        "live-fetched data instead of running this file end-to-end.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
