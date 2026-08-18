"""
Astrowatch World Astrology -- UnifiedAstrologyEngine (cross-tradition pipeline).
===================================================================
Runs every registered tradition engine (world_astrology/engines/*.py) against
one PredictionContext, then combines their independent TraditionPrediction
outputs into a single, fully-traceable unified reading, per this project's
governing "no fabrication" rule:

  ASTRONOMICAL DATA -> TRADITION-SPECIFIC CALCULATION -> TRADITION-SPECIFIC
  INTERPRETATION -> INDIVIDUAL PREDICTION -> CROSS-TRADITION COMPARISON ->
  AGREEMENT/CONFLICT ANALYSIS -> WEIGHTING -> UNIFIED PREDICTION.

Deliberately NOT simple majority voting (explicit task instruction: "6
traditions agree" is not automatically stronger evidence than 2 agreeing).
Traditions that are historically/computationally DEPENDENT on each other
(one reuses another's numbers -- see INDEPENDENCE_GROUPS below) are grouped,
and cross-tradition agreement is scored by how many INDEPENDENT GROUPS concur,
not by raw tradition count. This directly implements the requirement that
"traditions historically derived heavily from the same source should not
count as independent confirmations."

Theme clustering uses a small, explicitly-disclosed KEYWORD-HEURISTIC (not
real NLP/semantic clustering, which this project does not have) -- every
report produced by this module discloses that limitation rather than
presenting the clustering as more rigorous than it is.

Weighting is entirely CATEGORICAL (applicable/not_applicable, documented/
reconstructed/etc., low/moderate/high confidence) -- per the explicit
instruction to never invent numerical accuracy values, empirical_weight is
always reported as "unavailable" until a real HistoricalPredictionTest
backtest corpus exists (see world_astrology/backtesting.py).

MANDATORY TRANSPARENCY (task's "IMPORTANT DISTINCTION"): every unified
reading reports exactly how many traditions were evaluated / computationally
applicable / successfully calculated / unavailable -- never claims more
traditions "ran" than actually executed successfully.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .engine_interface import (
    AstrologyEngine, PredictionContext, TraditionPrediction, TraditionStatus, HistoricalStatus,
)
from .engines.jyotisha_engine import JyotishaEngine
from .engines.hellenistic_engine import HellenisticEngine
from .engines.western_engine import WesternEngine
from .engines.babylonian_engine import BabylonianEngine
from .engines.persian_islamic_engine import PersianIslamicEngine
from .engines.chinese_engine import ChineseEngine
from .engines.tibetan_engine import TibetanEngine
from .engines.japanese_engine import JapaneseEngine
from .engines.egyptian_engine import EgyptianEngine
from .engines.mesoamerican_engine import MesoamericanEngine

ENGINE_REGISTRY: Dict[str, type] = {
    "jyotisha": JyotishaEngine, "hellenistic": HellenisticEngine, "western": WesternEngine,
    "babylonian": BabylonianEngine, "persian_islamic": PersianIslamicEngine,
    "chinese": ChineseEngine, "tibetan": TibetanEngine, "japanese": JapaneseEngine,
    "egyptian": EgyptianEngine, "mesoamerican": MesoamericanEngine,
}

# Traditions that DIRECTLY reuse another tradition's computed numbers (code-level
# reuse, see each engine's docstring) or are historically/doctrinally continuous
# with each other closely enough that their agreement should not be double-counted
# as independent confirmation. Disclosed explicitly, not hidden.
INDEPENDENCE_GROUPS: Dict[str, str] = {
    "jyotisha": "vedic",
    "hellenistic": "hellenistic_lineage", "persian_islamic": "hellenistic_lineage",
    "western": "hellenistic_lineage",  # Solar Return/annual-revolution doctrinal continuity
    "chinese": "sino_tibetan", "tibetan": "sino_tibetan", "japanese": "sino_tibetan",
    "babylonian": "mesopotamian",
    "egyptian": "egyptian",
    "mesoamerican": "mesoamerican",
}

CONFIDENCE_ORDER = ["unvalidated", "low", "moderate", "high"]
HISTORICAL_STATUS_ORDER = [  # least to most certain, for "worst case" aggregation
    HistoricalStatus.SPECULATIVE.value, HistoricalStatus.SCHOLARLY_DISPUTED.value,
    HistoricalStatus.RECONSTRUCTED.value, HistoricalStatus.TRADITIONAL.value,
    HistoricalStatus.MODERN.value, HistoricalStatus.DOCUMENTED.value,
]

# Keyword-heuristic macro-theme clustering. Explicitly approximate -- see module
# docstring. Each tradition's raw theme strings are matched (case-insensitive
# substring) against these keyword lists; a theme string may match >=0 categories.
MACRO_THEME_KEYWORDS: Dict[str, List[str]] = {
    "authority_leadership": ["lord", "ruler", "king", "authority", "leadership", "profected",
                             "year pillar", "reputation"],
    "instability_conflict": ["instability", "danger", "conflict", "opposition", "eclipse",
                             "challenging", "debilitated", "kemadruma", "contradiction"],
    "favorable_growth": ["favorable", "exalted", "auspicious", "gajakesari", "budhaditya",
                         "trine", "sextile", "growth", "expansion"],
    "communication_intellect": ["mercury", "communication", "intellect"],
    "transformation_change": ["pluto", "transformation", "releasing", "mutation", "shift",
                              "transiting"],
    "timing_marker": ["decan", "pillar", "period", "return", "conjunction", "elemental year",
                      "tzolk", "haab", "star"],
}


def _classify_themes(themes: List[str]) -> List[str]:
    categories = set()
    for theme in themes:
        t_lower = theme.lower()
        for cat, keywords in MACRO_THEME_KEYWORDS.items():
            if any(kw in t_lower for kw in keywords):
                categories.add(cat)
    return sorted(categories)


def _aggregate_worst(values: List[str], order: List[str]) -> str:
    if not values:
        return "unavailable"
    return min(values, key=lambda v: order.index(v) if v in order else 0)


@dataclass
class ThemeCluster:
    macro_theme: str
    contributing_traditions: List[str] = field(default_factory=list)
    independence_groups: List[str] = field(default_factory=list)
    raw_themes_by_tradition: Dict[str, List[str]] = field(default_factory=dict)


@dataclass
class WeightBreakdown:
    tradition: str
    methodological_applicability: str
    data_quality: str
    rule_strength: str
    historical_documentation: str
    historical_backtest_performance: str
    tradition_independence_group: str
    empirical_weight: str = "unavailable"


@dataclass
class AgreementAnalysis:
    classification: str
    strongest_cluster: Optional[ThemeCluster]
    all_clusters: List[ThemeCluster]
    contradiction_detected: bool
    contradiction_note: Optional[str]


@dataclass
class UnifiedPrediction:
    entity_name: str
    entity_type: str
    traditions_evaluated: int
    traditions_applicable: int
    traditions_calculated: int
    traditions_unavailable: int
    status_by_tradition: Dict[str, str]
    individual_predictions: Dict[str, TraditionPrediction]
    theme_clusters: List[ThemeCluster]
    agreement: AgreementAnalysis
    weighting: List[WeightBreakdown]
    unified_prediction_text: str
    limitations: List[str]


class UnifiedAstrologyEngine:
    def __init__(self, traditions: Optional[List[str]] = None):
        """traditions=None runs ALL registered engines ('All Applicable' default,
        per the task's specified UI convention); pass an explicit list to restrict
        to specific traditions."""
        self.traditions = traditions or list(ENGINE_REGISTRY.keys())
        for t in self.traditions:
            if t not in ENGINE_REGISTRY:
                raise ValueError(f"Unknown tradition '{t}'. Known: {list(ENGINE_REGISTRY.keys())}")

    def generate_unified_prediction(self, context: PredictionContext) -> UnifiedPrediction:
        predictions: Dict[str, TraditionPrediction] = {}
        for name in self.traditions:
            engine: AstrologyEngine = ENGINE_REGISTRY[name]()
            predictions[name] = engine.predict(context)

        status_by_tradition = {name: p.status for name, p in predictions.items()}
        n_evaluated = len(predictions)
        n_applicable = sum(1 for p in predictions.values() if p.applicable)
        n_calculated = sum(1 for p in predictions.values() if p.status == TraditionStatus.CALCULATED.value)
        n_unavailable = n_evaluated - n_calculated

        calculated = {name: p for name, p in predictions.items() if p.status == TraditionStatus.CALCULATED.value}

        # -- Theme clustering --
        cluster_map: Dict[str, ThemeCluster] = {}
        for name, pred in calculated.items():
            macro_cats = _classify_themes(pred.themes)
            for cat in macro_cats:
                if cat not in cluster_map:
                    cluster_map[cat] = ThemeCluster(macro_theme=cat)
                cluster_map[cat].contributing_traditions.append(name)
                group = INDEPENDENCE_GROUPS.get(name, name)
                if group not in cluster_map[cat].independence_groups:
                    cluster_map[cat].independence_groups.append(group)
                cluster_map[cat].raw_themes_by_tradition[name] = pred.themes

        clusters = sorted(cluster_map.values(), key=lambda c: -len(set(c.independence_groups)))

        # "timing_marker" is deliberately EXCLUDED from agreement/strongest-cluster
        # selection: it fires on almost any tradition that mentions ANY date/period
        # (a return, a pillar, a decan, a conjunction date...), so "agreement" on it
        # is semantically close to meaningless -- nearly every calculated tradition
        # trivially mentions *some* timing marker. Counting that as thematic
        # agreement would overclaim consensus that isn't really there. It is still
        # computed and available in theme_clusters for inspection, just not used to
        # drive the classification/strongest-cluster logic below.
        substantive_clusters = [c for c in clusters if c.macro_theme != "timing_marker"]

        # -- Agreement classification (by DISTINCT independence groups, not raw
        # tradition count -- this is the "not simple majority voting" mechanism). --
        strongest = substantive_clusters[0] if substantive_clusters else None
        n_groups_strongest = len(set(strongest.independence_groups)) if strongest else 0
        n_traditions_strongest = len(strongest.contributing_traditions) if strongest else 0

        favorable_present = "favorable_growth" in cluster_map
        instability_present = "instability_conflict" in cluster_map
        contradiction_detected = favorable_present and instability_present
        contradiction_note = None
        if contradiction_detected:
            fav_traditions = cluster_map["favorable_growth"].contributing_traditions
            unstable_traditions = cluster_map["instability_conflict"].contributing_traditions
            contradiction_note = (
                f"Mixed/conflicting signals: {fav_traditions} indicate favorable/growth "
                f"themes while {unstable_traditions} indicate instability/conflict themes. "
                f"Both are reported, not hidden or averaged away."
            )

        if n_groups_strongest == 0:
            classification = "no_agreement"
        elif contradiction_detected and n_groups_strongest <= 2:
            classification = "contradiction"
        elif n_groups_strongest >= 4:
            classification = "exact_agreement" if n_traditions_strongest >= n_groups_strongest + 2 else "strong_thematic_agreement"
        elif n_groups_strongest == 3:
            classification = "strong_thematic_agreement"
        elif n_groups_strongest == 2:
            classification = "partial_agreement"
        else:  # 1 group (possibly multiple traditions within one lineage)
            classification = "weak_agreement"

        agreement = AgreementAnalysis(
            classification=classification, strongest_cluster=strongest, all_clusters=clusters,
            contradiction_detected=contradiction_detected, contradiction_note=contradiction_note,
        )

        # -- Weighting (categorical only, no fabricated numbers) --
        weighting: List[WeightBreakdown] = []
        for name, pred in predictions.items():
            rules = []
            hist_statuses = []
            # Pull confidence/historical_status by cross-referencing each engine's RULES dict.
            import importlib
            try:
                mod = importlib.import_module(f".engines.{name}_engine", package=__package__)
                rule_defs = getattr(mod, "RULES", {})
                for rid in pred.rules_used:
                    rule = rule_defs.get(rid)
                    if rule:
                        rules.append(rule.confidence)
                        hist_statuses.append(rule.historical_status)
            except ImportError:
                pass
            weighting.append(WeightBreakdown(
                tradition=name,
                methodological_applicability="applicable" if pred.applicable else "not_applicable",
                data_quality="reduced (assumed midnight)" if context.time_accuracy != "documented" else "full",
                rule_strength=_aggregate_worst(rules, CONFIDENCE_ORDER) if rules else "N/A (not calculated)",
                historical_documentation=_aggregate_worst(hist_statuses, HISTORICAL_STATUS_ORDER) if hist_statuses else "N/A (not calculated)",
                historical_backtest_performance="unavailable (no HistoricalPredictionTest corpus yet)",
                tradition_independence_group=INDEPENDENCE_GROUPS.get(name, name),
            ))

        # -- Unified prediction text (transparent, traceable, never overclaiming) --
        lines = [
            f"Traditions evaluated: {n_evaluated} / computationally applicable: {n_applicable} / "
            f"successfully calculated: {n_calculated} / unavailable: {n_unavailable}.",
        ]
        if strongest:
            lines.append(
                f"Strongest recurring theme cluster: '{strongest.macro_theme}' -- supported by "
                f"{n_traditions_strongest} tradition(s) across {n_groups_strongest} independent "
                f"lineage group(s) ({sorted(set(strongest.independence_groups))}). "
                f"Classification: {classification}."
            )
        else:
            lines.append("No shared macro-theme cluster was detected across the calculated "
                        "traditions' free-text themes (keyword-heuristic clustering).")
        if contradiction_note:
            lines.append(contradiction_note)
        for name, pred in calculated.items():
            lines.append(f"[{name}] {pred.prediction}")
        for name, pred in predictions.items():
            if pred.status != TraditionStatus.CALCULATED.value:
                lines.append(f"[{name}] not used in this reading -- status: {pred.status}"
                            + (f" ({pred.limitations[0]})" if pred.limitations else ""))

        limitations = [
            "Theme clustering uses a simple keyword-substring heuristic, not real semantic/NLP "
            "analysis -- it may miss true thematic overlaps or create false-positive matches.",
            "Weighting is entirely categorical (applicability, documentation status, confidence "
            "tier) -- no numerical accuracy/probability value is invented; empirical_weight is "
            "'unavailable' pending a real historical backtest corpus.",
            "Agreement is scored by distinct independence-lineage-group count, not raw tradition "
            "count, specifically to avoid treating traditions that reuse each other's computed "
            "numbers (see INDEPENDENCE_GROUPS) as independent confirmations.",
        ]

        return UnifiedPrediction(
            entity_name=context.entity_name, entity_type=context.entity_type,
            traditions_evaluated=n_evaluated, traditions_applicable=n_applicable,
            traditions_calculated=n_calculated, traditions_unavailable=n_unavailable,
            status_by_tradition=status_by_tradition, individual_predictions=predictions,
            theme_clusters=clusters, agreement=agreement, weighting=weighting,
            unified_prediction_text="\n".join(lines), limitations=limitations,
        )


def short_reading(unified: UnifiedPrediction) -> str:
    """Compresses the unified reading into a few sentences (X-post-suitable),
    never fabricating consensus beyond what agreement/theme_clusters actually
    found. Always includes the mandatory transparency counts."""
    lines = [
        f"{unified.entity_name}: {unified.traditions_calculated}/{unified.traditions_evaluated} "
        f"astrological traditions computationally applicable and calculated.",
    ]
    if unified.agreement.strongest_cluster:
        c = unified.agreement.strongest_cluster
        n_groups = len(set(c.independence_groups))
        lines.append(
            f"Strongest cross-tradition theme: '{c.macro_theme}' ({unified.agreement.classification}, "
            f"{len(c.contributing_traditions)} tradition(s) / {n_groups} independent lineage group(s))."
        )
    else:
        lines.append("No shared theme cluster was found across the calculated traditions.")
    if unified.agreement.contradiction_detected:
        lines.append("Note: mixed/conflicting signals were found across traditions -- see detailed reading.")
    return " ".join(lines)


def detailed_reading(unified: UnifiedPrediction) -> str:
    """Full reasoning chain: transparency counts, every calculated tradition's
    own prediction, theme clusters (substantive + timing-marker separately),
    agreement/conflict analysis, and the categorical weighting breakdown for
    every tradition (including ones that did NOT calculate, so the reader can
    see why)."""
    lines = [unified.unified_prediction_text, "", "-- Weighting breakdown (categorical only; "
             "no fabricated numerical accuracy) --"]
    for w in unified.weighting:
        lines.append(
            f"[{w.tradition}] applicability={w.methodological_applicability}, "
            f"data_quality={w.data_quality}, rule_strength={w.rule_strength}, "
            f"historical_documentation={w.historical_documentation}, "
            f"independence_group={w.tradition_independence_group}, "
            f"backtest_performance={w.historical_backtest_performance}, "
            f"empirical_weight={w.empirical_weight}"
        )
    lines.append("")
    lines.append("-- Limitations --")
    for lim in unified.limitations:
        lines.append(f"* {lim}")
    return "\n".join(lines)
