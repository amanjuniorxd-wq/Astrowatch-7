"""
Astrowatch World Astrology -- common tradition-engine interface.
====================================================================
This is the "computation layer" contract every tradition-specific engine
under world_astrology/engines/*.py implements. It is ADDITIVE: nothing here
replaces or modifies schema.py's KnowledgeEntry/TraditionRegistry (the
"knowledge layer", used for reference/catalogued content), reading_engine.py
(the existing Jyotisha/Hellenistic reading pipeline), or cross_tradition.py
(the existing curated relationship table). Those stay exactly as they are;
UnifiedAstrologyEngine (unified_engine.py) sits ALONGSIDE them and calls into
kundli.py/mundane/entity_chart.py for astronomical data exactly like
reading_engine.py already does.

DESIGN PRINCIPLE (task requirement, repeated here for every engine author to
see): do not build one generic Western-style algorithm and relabel it for
each tradition. Every engine module under engines/ implements its own real,
historically-sourced calculation. If a tradition's technique cannot be
reconstructed with defensible confidence from documented sources, the engine
must return status="not_implemented" or "insufficient_methodology" for that
technique -- never a fabricated result dressed up to look computed.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class HistoricalStatus(str, Enum):
    """How well-grounded a specific RULE (not a whole tradition) is in
    documented historical sources. Assigned per-rule, mirrors
    schema.EvidenceLevel's spirit but named per this task's exact vocabulary."""
    DOCUMENTED = "documented"                # directly attested calculation/rule in a primary source
    RECONSTRUCTED = "reconstructed"          # assembled from multiple documented fragments; a defensible reading, not a verbatim source
    SCHOLARLY_DISPUTED = "scholarly_disputed"  # real scholarly disagreement about the method/meaning
    TRADITIONAL = "traditional"              # claimed within the living tradition, not independently source-verified this session
    MODERN = "modern"                        # post-traditional/20th-century-or-later reinterpretation
    SPECULATIVE = "speculative"              # explicitly flagged low-confidence extrapolation -- used sparingly, never for a headline prediction alone


class TraditionStatus(str, Enum):
    """Whole-tradition (or whole-technique-within-a-tradition) implementation
    status -- this is what UnifiedAstrologyEngine's transparency counts
    (task spec Section 25) are built from."""
    CALCULATED = "calculated"                          # ran successfully, real output
    NOT_APPLICABLE = "not_applicable"                   # tradition doesn't historically address this domain/entity type (e.g. Egyptian natal astrology)
    NOT_IMPLEMENTED = "not_implemented"                 # engine/technique doesn't exist in this codebase yet
    INSUFFICIENT_METHODOLOGY = "insufficient_methodology"  # cannot be reconstructed with defensible confidence -- by design, not a gap to fill later
    INSUFFICIENT_DATA = "insufficient_data"             # entity/context data is missing (e.g. no location)
    ERROR = "error"                                     # a real calculation error (bug, bad input) -- distinct from the above, always logged


@dataclass
class PredictionContext:
    """Shared input structure every engine receives (task spec Section 5)."""
    entity_name: str
    entity_type: str  # person | country | government | political_party | company | organization | sports_team | institution | city | event | other
    birth_or_inception_date: str  # YYYY-MM-DD
    latitude: float
    longitude: float
    timezone_name: str
    birth_or_inception_time: Optional[str] = None  # HH:MM, None -> assumed midnight
    time_accuracy: str = "assumed_midnight"  # "documented" | "assumed_midnight"
    prediction_date: Optional[str] = None    # as-of / evaluation date, YYYY-MM-DD; defaults to today if None
    prediction_period: Optional[str] = None  # e.g. "2028-11-01..2028-11-30"
    geographic_scope: Optional[str] = None   # e.g. "USA", "GLOBAL"
    prediction_domain: Optional[str] = None  # politics | economy | sports | ...
    event_type: Optional[str] = None
    astronomical_data: Dict[str, Any] = field(default_factory=dict)  # engines may cache shared chart data here
    historical_context: Optional[str] = None


@dataclass
class PredictiveRule:
    """Metadata for one predictive rule (task spec Section 7). Every
    TraditionPrediction.rules_used entry should resolve to one of these via
    rule_id, so a caller can always answer 'where did this specific finding
    come from.'"""
    rule_id: str
    tradition: str
    school: str
    name: str
    description: str
    historical_source: str
    calculation: str
    interpretation: str
    prediction_domain: List[str]
    historical_status: str  # HistoricalStatus value
    confidence: str  # categorical: "low" | "moderate" | "high" | "unvalidated" -- NEVER a fabricated number


@dataclass
class TraditionFactor:
    """One concrete computed factor feeding a prediction (e.g. 'Jupiter in
    house 10, exalted')."""
    name: str
    value: Any
    rule_id: Optional[str] = None
    weight_hint: Optional[str] = None  # "supportive" | "opposing" | "neutral" | "contextual"


@dataclass
class TraditionPrediction:
    """The structured, independent output every engine produces (task spec
    Section 8) -- always returned, even when status != CALCULATED, so callers
    have one uniform shape to handle."""
    tradition: str
    applicable: bool
    status: str  # TraditionStatus value
    prediction: Optional[str] = None
    themes: List[str] = field(default_factory=list)
    time_window: Optional[Dict[str, str]] = None
    factors: List[Dict[str, Any]] = field(default_factory=list)
    rules_used: List[str] = field(default_factory=list)
    signal_strength: Optional[float] = None  # only set when the engine has a real, documented basis for it; else None
    historical_status: str = HistoricalStatus.DOCUMENTED.value
    limitations: List[str] = field(default_factory=list)
    zodiac_system: Optional[str] = None
    calendar_system: Optional[str] = None
    coordinate_system: Optional[str] = None
    epoch: Optional[str] = None
    ayanamsha: Optional[str] = None
    engine: Optional[str] = None  # e.g. "astrowatch.world_astrology.engines.babylonian_engine"


class AstrologyEngine(ABC):
    """Every tradition-specific engine subclasses this. NOTE: is_applicable/
    calculate/interpret are intentionally separate steps (not folded into one
    predict() body) so a caller can introspect a tradition's raw calculation
    independent of its interpretation -- exactly the calculation/interpretation
    separation the task spec insists on everywhere else in this project."""

    tradition_name: str = "unknown"

    @abstractmethod
    def is_applicable(self, context: PredictionContext) -> bool:
        """Whether this tradition historically addresses this context's
        entity_type/prediction_domain at all (e.g. Egyptian has no natal
        astrology; Babylonian mundane omens don't address a sports team)."""

    @abstractmethod
    def calculate(self, context: PredictionContext) -> Dict[str, Any]:
        """Raw astronomical/calendrical calculation only -- no interpretation.
        Must raise nothing for missing methodology; instead the caller
        (predict()) should catch and translate to a TraditionStatus."""

    @abstractmethod
    def interpret(self, calculation: Dict[str, Any]) -> Dict[str, Any]:
        """Rule-based interpretation of an already-computed calculation.
        Returns {"themes": [...], "factors": [...], "rules_used": [...],
        "prediction_text": str, "limitations": [...]}."""

    def predict(self, context: PredictionContext) -> TraditionPrediction:
        """Default full pipeline: is_applicable -> calculate -> interpret ->
        TraditionPrediction. Engines may override for tradition-specific
        control flow (e.g. multiple techniques with independent
        applicability), but most should just implement the three methods
        above and use this default."""
        if not self.is_applicable(context):
            return TraditionPrediction(
                tradition=self.tradition_name, applicable=False,
                status=TraditionStatus.NOT_APPLICABLE.value,
                limitations=[f"{self.tradition_name} does not historically address this "
                             f"entity_type/prediction_domain combination."],
            )
        try:
            calc = self.calculate(context)
        except NotImplementedError as e:
            return TraditionPrediction(
                tradition=self.tradition_name, applicable=True,
                status=TraditionStatus.INSUFFICIENT_METHODOLOGY.value,
                limitations=[str(e)],
            )
        except Exception as e:  # noqa: BLE001 -- surfaced honestly, not hidden
            return TraditionPrediction(
                tradition=self.tradition_name, applicable=True,
                status=TraditionStatus.ERROR.value,
                limitations=[f"Calculation error: {e}"],
            )
        interp = self.interpret(calc)
        return TraditionPrediction(
            tradition=self.tradition_name, applicable=True,
            status=TraditionStatus.CALCULATED.value,
            prediction=interp.get("prediction_text"),
            themes=interp.get("themes", []),
            time_window=interp.get("time_window"),
            factors=interp.get("factors", []),
            rules_used=interp.get("rules_used", []),
            signal_strength=interp.get("signal_strength"),
            historical_status=interp.get("historical_status", HistoricalStatus.DOCUMENTED.value),
            limitations=interp.get("limitations", []),
            zodiac_system=calc.get("zodiac_system"),
            calendar_system=calc.get("calendar_system"),
            coordinate_system=calc.get("coordinate_system"),
            epoch=calc.get("epoch"),
            ayanamsha=calc.get("ayanamsha"),
            engine=f"{self.__class__.__module__}.{self.__class__.__name__}",
        )

    def explain(self, result: TraditionPrediction) -> str:
        """Human-readable trace of how `result` was produced -- default
        implementation walks factors/rules_used; engines may override for
        richer explanations."""
        lines = [f"{self.tradition_name} -- status: {result.status}"]
        if result.factors:
            lines.append("Factors:")
            for f in result.factors:
                lines.append(f"  - {f.get('name')}: {f.get('value')}")
        if result.rules_used:
            lines.append(f"Rules applied: {', '.join(result.rules_used)}")
        if result.limitations:
            lines.append("Limitations:")
            for lim in result.limitations:
                lines.append(f"  - {lim}")
        return "\n".join(lines)
