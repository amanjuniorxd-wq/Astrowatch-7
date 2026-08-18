"""
Astrowatch — tradition-specific engines (Phase 5)
===============================================
No single universal astrology engine. The astronomical layer (coordinates.py,
ephemeris_client.py) stays neutral -- it produces a PositionRecord with raw + tropical
+ optional sidereal fields and does not itself decide what matters. Each engine below
sees only its own tradition's rules and its own tradition's configuration-detection
logic, and explicitly refuses to run a rule whose zodiac_requirement is unresolved
rather than silently guessing an ayanamsa.

STATUS: written this session, not executed (see VALIDATION_REPORT.md). Structural/
organizational code -- low computational risk, but "low risk" is not "tested."
"""

from dataclasses import dataclass
from typing import Dict, List

from rule_registry import Rule, rules_for_tradition
from aspects import detect_configuration
from rule_matcher import RuleMatch, format_match_report


class ZodiacUnresolvedError(Exception):
    """Raised instead of silently defaulting to an unjustified ayanamsa."""


@dataclass
class EngineResult:
    tradition: str
    matches: List[RuleMatch]
    skipped_unresolved: List[Rule]


class _BaseEngine:
    tradition_key: str = ""

    def __init__(self):
        self.rules: List[Rule] = rules_for_tradition(self.tradition_key)

    def usable_rules(self, allow_unresolved: bool = False) -> List[Rule]:
        if allow_unresolved:
            return self.rules
        return [r for r in self.rules if r.zodiac_requirement != "sidereal_unresolved"]

    def blocked_rules(self) -> List[Rule]:
        return [r for r in self.rules if r.zodiac_requirement == "sidereal_unresolved"]

    def report_blocked(self) -> str:
        blocked = self.blocked_rules()
        if not blocked:
            return "No rules blocked on unresolved zodiac convention."
        lines = ["Rules blocked -- HISTORICAL COORDINATE CONVENTION UNRESOLVED:"]
        for r in blocked:
            lines.append(f"  {r.rule_id}: {r.zodiac_requirement_note}")
        return "\n".join(lines)


class BrihatSamhitaEngine(_BaseEngine):
    tradition_key = "brihat_samhita"

    def detect(self, positions: Dict[str, float], **kwargs):
        """positions: {body: ecliptic_longitude_deg} -- caller must state, and this
        engine does not itself decide, whether these are tropical or sidereal. For
        rules marked zodiac_independent it doesn't matter (see rule_registry.py
        Phase 4 notes); for rules requiring a resolved sidereal placement, this
        engine will refuse to match them (see usable_rules)."""
        return detect_configuration("brihat_samhita", positions, **kwargs)


class PtolemyEngine(_BaseEngine):
    tradition_key = "ptolemy"

    def detect(self, positions: Dict[str, float], **kwargs):
        """positions MUST be tropical longitudes -- Ptolemy's system is tropical per
        Phase 4. This engine does not check that its caller actually passed tropical
        values; that's on the caller, but every rule here is labeled 'tropical' so at
        least the requirement is explicit and auditable."""
        return detect_configuration("ptolemy", positions, **kwargs)


class GrandConjunctionEngine(_BaseEngine):
    tradition_key = "grand_conjunction"

    def detect(self, *args, **kwargs):
        raise NotImplementedError(
            "No primary Gjamasp text exists in the corpus, and no operative rule was "
            "extracted -- this engine has nothing to run. It exists only to hold the "
            "Level-D historical-report classification, not to generate configurations."
        )


def engine_status_report() -> str:
    bs = BrihatSamhitaEngine()
    pt = PtolemyEngine()
    lines = [
        f"Bṛhat Saṃhitā engine: {len(bs.usable_rules())} usable rules, "
        f"{len(bs.blocked_rules())} blocked on unresolved zodiac convention",
        bs.report_blocked(),
        "",
        f"Ptolemy engine: {len(pt.usable_rules())} usable rules "
        f"(all tropical -- zodiac convention resolved for this tradition)",
        "",
        "Grand-conjunction engine: 0 operative rules (historical report only, by design).",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    print(engine_status_report())
