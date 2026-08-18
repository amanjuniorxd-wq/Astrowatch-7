"""
Astrowatch — rule-matching engine
==============================
ASTRONOMICAL POSITIONS -> CONFIGURATION DETECTION -> RULE REGISTRY SEARCH -> MATCHES

Deliberately conservative: this only emits a match when a rule's trigger_params are
satisfied by the detected configuration. It does not infer, extrapolate, or fill gaps
with unlisted rules. If nothing matches, it says so -- it does not fall back to general
astrology knowledge.

STATUS: written this session, not run against live data yet (see README.md).
"""

from dataclasses import dataclass
from typing import Dict, List, Optional

from aspects import (
    DetectedAspect, GrahaYuddhaClass, classify_lunar_pass, LunarPassResult,
    check_for_eclipse, EclipseCheckResult, triplicity_for_tropical_longitude,
    ECLIPSE_LATITUDE_LIMIT_DEG,
)
from rule_registry import Rule, RULES


@dataclass
class RuleMatch:
    rule: Rule
    satisfied_conditions: List[str]
    unsatisfied_conditions: List[str]
    trigger_evidence: str


def match_grahayuddha_rules(
    classes: List[GrahaYuddhaClass],
    defeated_body: Optional[Dict[str, str]] = None,  # {"body_a_vs_body_b": "loser_name"}
) -> List[RuleMatch]:
    """
    classes: output of aspects.classify_grahayuddha()
    defeated_body: optional externally-determined winner/loser per pair (brightness/size
        comparison is not automated here -- Ch. XVII's defeat criteria, Sl. 9, require
        disc brightness/size/steadiness judgments not derivable from longitude alone).
    """
    matches: List[RuleMatch] = []
    for c in classes:
        for rule in RULES:
            if rule.trigger_type == "grahayuddha_class" and rule.trigger_params.get("class") == c.conjunction_class:
                matches.append(RuleMatch(
                    rule=rule,
                    satisfied_conditions=[f"{c.body_a}-{c.body_b} conjunction classified as '{c.conjunction_class}'"],
                    unsatisfied_conditions=[],
                    trigger_evidence=f"separation={c.separation_deg:.3f} deg ({c.note})",
                ))
            if rule.trigger_type == "grahayuddha_defeat" and defeated_body:
                pair_key = f"{c.body_a}_vs_{c.body_b}"
                pair_key_rev = f"{c.body_b}_vs_{c.body_a}"
                loser = defeated_body.get(pair_key) or defeated_body.get(pair_key_rev)
                if loser and loser == rule.trigger_params.get("defeated"):
                    winner_expected = rule.trigger_params.get("victor")
                    winner_actual = c.body_b if loser == c.body_a else c.body_a
                    if winner_actual == winner_expected:
                        matches.append(RuleMatch(
                            rule=rule,
                            satisfied_conditions=[f"{loser} defeated by {winner_actual} (externally judged)"],
                            unsatisfied_conditions=[],
                            trigger_evidence=f"separation={c.separation_deg:.3f} deg, class={c.conjunction_class}",
                        ))
    return matches


def match_lunar_pass_rules(
    moon_lon: float, moon_lat: float,
    planet_positions: Dict[str, tuple],  # {planet_name: (lon_deg, lat_deg)}
) -> List[RuleMatch]:
    """
    IMPLEMENTED during the "VALIDATION HARDENING BEFORE BT-002" pass (previously
    raised NotImplementedError -- see git history for the original stub and its
    stated reason). Uses aspects.classify_lunar_pass() for each planet the Moon is
    given a position for for, and matches against every 'lunar_pass' /
    'lunar_pass_general' rule in RULES whose trigger_params are satisfied.

    trigger_params shapes handled:
      lunar_pass:          {"planet": <name>, "side": "north"|"south"}
      lunar_pass_general:  {"rule": "north=prosperity, south=misery, ..."} -- matches
                            ANY planet the Moon passes, either side (the text states a
                            general principle, not a specific planet/side pair).

    See aspects.py's THRESHOLD NOTE for the conjunction-orb caveat (unsourced
    placeholder, reused from graha-yuddha for consistency, not tuned to any result).
    """
    matches: List[RuleMatch] = []
    pass_results: Dict[str, LunarPassResult] = {}
    for planet, (p_lon, p_lat) in planet_positions.items():
        result = classify_lunar_pass(moon_lon, moon_lat, planet, p_lon, p_lat)
        pass_results[planet] = result
        if not result.in_conjunction_range:
            continue
        for rule in RULES:
            if rule.trigger_type == "lunar_pass":
                if rule.trigger_params.get("planet") == planet and rule.trigger_params.get("side") == result.side:
                    matches.append(RuleMatch(
                        rule=rule,
                        satisfied_conditions=[f"Moon passes {result.side} of {planet} "
                                               f"(sep={result.longitude_separation_deg:.3f} deg, "
                                               f"orb={result.orb_used_deg} deg PLACEHOLDER)"],
                        unsatisfied_conditions=[],
                        trigger_evidence=f"moon_lat={moon_lat:.4f} {planet}_lat={p_lat:.4f}",
                    ))
            elif rule.trigger_type == "lunar_pass_general" and result.side in ("north", "south"):
                matches.append(RuleMatch(
                    rule=rule,
                    satisfied_conditions=[f"Moon passes {result.side} of {planet} "
                                           f"(general Ch. XVIII principle, sep="
                                           f"{result.longitude_separation_deg:.3f} deg, "
                                           f"orb={result.orb_used_deg} deg PLACEHOLDER)"],
                    unsatisfied_conditions=[],
                    trigger_evidence=f"moon_lat={moon_lat:.4f} {planet}_lat={p_lat:.4f}",
                ))
    return matches


def check_and_match_eclipse(sun_lon: float, moon_lon: float, moon_lat: float) -> List[RuleMatch]:
    """
    IMPLEMENTED during the "VALIDATION HARDENING BEFORE BT-002" pass. Actually
    detects whether an eclipse is geometrically occurring (aspects.check_for_eclipse
    -- real eclipse-limit astronomy, not a placeholder) before matching PT-II-6-01,
    replacing the old match_eclipse_geography() which unconditionally matched
    regardless of whether any eclipse was actually happening (it took an
    'eclipse_ecliptic_lon' as a GIVEN, never checking that one existed). Returns []
    if no eclipse is occurring -- this is the correct behavior for a rule whose
    trigger condition (an eclipse) is not met, not a bug.
    """
    check: EclipseCheckResult = check_for_eclipse(sun_lon, moon_lon, moon_lat)
    if check.kind == "none":
        return []
    rule = next(r for r in RULES if r.rule_id == "PT-II-6-01")
    triplicity_info = triplicity_for_tropical_longitude(check.eclipse_ecliptic_lon_deg)
    return [RuleMatch(
        rule=rule,
        satisfied_conditions=[
            f"{check.kind} eclipse geometrically possible at ecliptic longitude "
            f"{check.eclipse_ecliptic_lon_deg:.2f} deg (syzygy separation="
            f"{check.syzygy_separation_deg:.3f} deg, moon_lat={moon_lat:.3f} deg, "
            f"within the {ECLIPSE_LATITUDE_LIMIT_DEG} deg eclipse-limit bound)",
        ],
        unsatisfied_conditions=[
            "named-country modern-mapping layer for the PT-II-3 quadrant table does "
            "not exist yet -- geography reported as ancient quadrant/triplicity only "
            "(see triplicity_info), not a modern country/region",
        ],
        trigger_evidence=(
            f"triplicity={triplicity_info['triplicity']} sign={triplicity_info['sign']} "
            f"quadrant={triplicity_info['quadrant']} (via rule PT-II-3-general's table)"
        ),
    )]


# Backward-compatible alias retained so any external caller of the OLD (always-
# matches, no real eclipse check) function fails loudly instead of silently keeping
# the old, incorrect behavior.
def match_eclipse_geography(*args, **kwargs):
    raise RuntimeError(
        "match_eclipse_geography() was replaced by check_and_match_eclipse(sun_lon, "
        "moon_lon, moon_lat), which actually checks whether an eclipse is occurring "
        "instead of assuming one. Update the caller."
    )


def format_match_report(matches: List[RuleMatch]) -> str:
    if not matches:
        return "NO MATCHING RULES in current registry for the given configuration. " \
               "This does not mean nothing is happening astrologically -- it means the " \
               "extracted rule set (Astrowatch MVP-1) does not cover it yet."
    lines = []
    for m in matches:
        r = m.rule
        lines.append(
            f"Rule ID: {r.rule_id}\n"
            f"Source: {r.author} ({r.tradition})\n"
            f"Chapter: {r.chapter} ({r.citation})\n"
            f"Configuration: {r.trigger_type} {r.trigger_params}\n"
            f"Satisfied conditions: {m.satisfied_conditions}\n"
            f"Unsatisfied conditions: {m.unsatisfied_conditions}\n"
            f"Traditional interpretation: {r.interpretation}\n"
            f"Domain: {r.domain}\n"
            f"Geography: {r.geography}\n"
            f"Timing: {r.timing}\n"
            f"Source confidence: {r.source_confidence}\n"
            f"Evidence: {m.trigger_evidence}\n"
            + "-" * 60
        )
    return "\n".join(lines)
