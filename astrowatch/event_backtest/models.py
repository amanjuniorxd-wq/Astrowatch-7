"""
Astrowatch event_backtest -- data models.
===================================================================
HistoricalPredictionEvent is the schema for one backtestable historical
event. actual_winner is stored on this dataclass but MUST NEVER be passed to
prediction.predictor.predict() -- engine.py enforces this ordering (see
engine.py's own docstring): predict() is called with only the fields a
predictor is allowed to see (candidates/location/cutoff/entity references),
and actual_winner is read by the ENGINE only, after prediction is complete,
to score it. This is convention-enforced here (unlike backtest/blindness.py's
AST-level enforcement for the other system) -- see BACKTEST.md's "Known
Limitations" section for why, and event_backtest/engine.py's own inline
comments for the specific call-ordering discipline that substitutes for it.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class CandidateRef:
    """One candidate in a HistoricalPredictionEvent. `entity_name` must match
    a real, sourced entity this project can chart (see
    kundli_mass/nations_corpus.py) -- never a fabricated placeholder."""
    candidate_id: str            # short slug, e.g. "australia", "india"
    entity_name: str             # real entity name Astrowatch can chart, e.g. "Australia"
    display_name: str            # human-readable, e.g. "Australia"
    captain_name: Optional[str] = None
    captain_birth_date: Optional[str] = None   # ISO8601, real+sourced, or None if unavailable
    captain_birth_date_source: Optional[str] = None


@dataclass(frozen=True)
class HistoricalPredictionEvent:
    event_id: str
    event_type: str                       # e.g. "cricket_odi_world_cup"
    event_name: str
    event_date: str                       # ISO8601 date of the actual event (e.g. the final)
    prediction_cutoff_date: str            # ISO8601; predictor may use nothing dated after this
    location: str                         # host venue/city, real and sourced
    location_latitude: Optional[float] = None
    location_longitude: Optional[float] = None
    location_timezone: Optional[str] = None
    candidates: List[CandidateRef] = field(default_factory=list)
    # actual_winner is stored SEPARATELY from everything above -- see module
    # docstring. candidate_id, or None/'DATA_UNAVAILABLE' if genuinely unresolved.
    actual_winner: Optional[str] = None
    source_metadata: Dict[str, Any] = field(default_factory=dict)
    model_version: Optional[str] = None    # filled in by the predictor at prediction time, not here
    excluded: bool = False                # True if the dataset curator marked this event
    exclusion_reason: Optional[str] = None  # unusable (insufficient reliable pre-event data)

    def public_fields(self) -> Dict[str, Any]:
        """Everything the predictor is allowed to see: event framing,
        candidates, location, cutoff -- explicitly WITHOUT actual_winner.
        engine.py calls this (not the raw dataclass) when building the
        predictor's input."""
        return {
            "event_id": self.event_id, "event_type": self.event_type,
            "event_name": self.event_name, "prediction_cutoff_date": self.prediction_cutoff_date,
            "location": self.location, "location_latitude": self.location_latitude,
            "location_longitude": self.location_longitude, "location_timezone": self.location_timezone,
            "candidates": list(self.candidates),
        }


@dataclass
class FeatureBreakdown:
    """One candidate's per-component feature scores, before weighting --
    always categorical/numeric with the exact same interpretable scale
    across candidates, never a hidden magic number."""
    candidate_id: str
    dasha_lord: Optional[str] = None
    dasha_lord_strength: Optional[float] = None
    antardasha_lord: Optional[str] = None
    antardasha_strength: Optional[float] = None
    transit_strength: Optional[float] = None
    moon_activation: Optional[float] = None
    entity_chart_strength: Optional[float] = None
    event_chart_strength: Optional[float] = None
    key_personnel_strength: Optional[float] = None
    confidence_notes: List[str] = field(default_factory=list)
    missing_components: List[str] = field(default_factory=list)  # component name -> component excluded, e.g. "event_chart"


@dataclass
class PredictionResult:
    event_id: str
    cutoff_date: str
    model_version: str
    predicted_winner: Optional[str]         # candidate_id, or None if INSUFFICIENT_DATA
    scores: Dict[str, float]                # candidate_id -> raw weighted score
    probabilities: Optional[Dict[str, float]]  # candidate_id -> normalized [0,1] summing to 1, or None
    probabilities_are_calibrated: bool       # always False until real calibration evidence exists (see calibration.py)
    feature_breakdown: Dict[str, FeatureBreakdown]
    status: str                             # "OK" | "INSUFFICIENT_DATA" | "DATA_UNAVAILABLE"
    status_reason: Optional[str] = None
    configuration_hash: Optional[str] = None
