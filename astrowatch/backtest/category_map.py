"""
Astrowatch backtest — rule-domain-to-event-category mapping.

rule_registry.Rule.domain uses a lowercase, free-text vocabulary
(military/political/economic/environmental/geological/social/diplomatic) extracted
directly from each rule's own source text. historical/taxonomy.py's EVENT_TAXONOMY
uses a different, controlled, uppercase vocabulary
(MILITARY/POLITICAL/ECONOMIC/NATURAL_DISASTER/SOCIAL_PUBLIC_HEALTH/SCIENCE_TECHNOLOGY).
Scoring predictions against real events requires SOME mapping between the two.

This mapping was fixed by plain-English semantic correspondence BEFORE this
experiment was run, and is never adjusted based on backtest results (per the explicit
instruction: "Do NOT optimize existing rules based on backtest results" -- this
mapping is not a rule, but it is scored-outcome-adjacent infrastructure and is held to
the same no-tuning standard). If it is later found to misrepresent a rule's domain,
that is a documented limitation of this experiment, not something to silently patch
and re-run.

Rationale, recorded once:
  military     -> MILITARY                (direct match)
  political     -> POLITICAL                (direct match)
  economic      -> ECONOMIC                 (direct match)
  diplomatic     -> POLITICAL                (diplomacy is a form of interstate political
                                           relations in this taxonomy; no separate
                                           DIPLOMATIC category exists)
  environmental   -> NATURAL_DISASTER          (the rules using this word describe drought,
                                           weapons+disease+hunger, and similar physical/
                                           subsistence effects -- closest existing category)
  geological     -> NATURAL_DISASTER          (direct semantic match)
  social       -> SOCIAL_PUBLIC_HEALTH        (closest existing category; the rule text
                                           describes unrest/allegiance shifts, not public
                                           health specifically, but SOCIAL_PUBLIC_HEALTH
                                           is the only category with "social" in it)

No rule in the current registry documents a "technology" or "science" domain, so
SCIENCE_TECHNOLOGY can never be predicted by this rule set -- a real limitation of the
registry's current coverage (see rule_registry.COVERAGE), not a mapping gap.
"""

from typing import List, Set

RULE_DOMAIN_TO_EVENT_CATEGORY = {
    "military": "MILITARY",
    "political": "POLITICAL",
    "economic": "ECONOMIC",
    "diplomatic": "POLITICAL",
    "environmental": "NATURAL_DISASTER",
    "geological": "NATURAL_DISASTER",
    "social": "SOCIAL_PUBLIC_HEALTH",
}

ALL_EVENT_CATEGORIES = (
    "MILITARY", "POLITICAL", "ECONOMIC", "NATURAL_DISASTER",
    "SOCIAL_PUBLIC_HEALTH", "SCIENCE_TECHNOLOGY",
)


def rule_domains_to_categories(domains: List[str]) -> Set[str]:
    out = set()
    for d in domains:
        mapped = RULE_DOMAIN_TO_EVENT_CATEGORY.get(d.lower())
        if mapped:
            out.add(mapped)
    return out
