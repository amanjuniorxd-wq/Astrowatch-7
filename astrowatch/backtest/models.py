"""
Astrowatch backtest — data models.

BlindInput is the load-bearing structural safeguard for this whole package: it is the
ONLY type predictor.py's core function accepts, and it has no field capable of
carrying an event name, type, subtype, description, source, verification status, or
outcome. See blindness.py for an automated AST check that predictor.py never imports
or references any historical.models.Event field other than through a BlindInput that
was already constructed by sampler.py/controls.py/engine.py -- never inside
predictor.py itself.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass(frozen=True)
class BlindInput:
    """Everything (and ONLY everything) that would legitimately be available at
    prediction time, before any outcome is known. No event_id, event_name,
    event_type, description, source, or verification_status field exists on this
    class -- this is enforced structurally (there is nowhere to put them), not just
    by convention."""
    test_case_id: str
    date: str                                  # ISO8601 date, e.g. '1964-03-28'
    time_precision_mode: str                    # 'MODE_A_EXACT_TIME' | 'MODE_B_DATE_ONLY' | 'MODE_C_TIME_WINDOW'
    time_hhmm: Optional[str] = None              # legitimately known local time, Mode A/C center
    timezone: Optional[str] = None               # IANA tz name, legitimately known
    location_precision: Optional[str] = None       # from location_confidence / 'UNKNOWN' for controls
    # location itself is NOT included: the existing, unmodified astronomical pipeline
    # (forecast.get_astronomical_snapshot / get_sidereal_snapshot) takes no location
    # parameter at all -- see forecast.py's AstronomicalSnapshot (jd_ut + tropical
    # longitudes only) and evaluate_rules()'s own hard safeguard #3 (geographic
    # allowlist is empty, so no rule can be geographically targeted regardless of
    # what location string is supplied). Passing a fabricated or even a real
    # location into a pipeline that structurally cannot use it would only create the
    # appearance of location-awareness that does not exist. See KNOWN_LIMITATIONS in
    # the backtest report.


@dataclass
class Prediction:
    prediction_id: str
    experiment_id: str
    test_case_id: str
    predicted_at: str
    predicted_fired: bool
    predicted_categories: List[str]
    predicted_subtypes: List[str]
    rule_matches: List[str]
    confidence_score: Optional[float]
    astronomical_inputs_jd_ut: List[float]
    ayanamsha_source: str
    ephemeris_precision_flag: str
    panchang_snapshot: Optional[dict]
    rashi_nakshatra_snapshot: Optional[dict]
    raw_rule_evaluations: List[dict]
    astronomy_extrapolated_unvalidated: bool = False


@dataclass
class ActualOutcome:
    """Constructed ONLY after a Prediction already exists for the same test_case_id.
    engine.py enforces the ordering; see engine.run_test_case()."""
    test_case_id: str
    experiment_id: str
    revealed_at: str
    actual_kind: str                 # 'EVENT' | 'PRESUMED_NO_EVENT'
    actual_event_id: Optional[str] = None
    actual_category: Optional[str] = None
    actual_subtype: Optional[str] = None
    actual_event_name: Optional[str] = None


@dataclass
class TestCase:
    test_case_id: str
    experiment_id: str
    case_kind: str                  # 'EVENT' | 'CONTROL'
    source_event_id: Optional[str]
    source_control_id: Optional[str]
    test_date: str
    time_precision_mode: str
    input_time: Optional[str]
    input_timezone: Optional[str]
    input_location_precision: Optional[str]
    sample_hours_utc: List[float]
    generated_at: str

    def to_blind_input(self) -> BlindInput:
        return BlindInput(
            test_case_id=self.test_case_id,
            date=self.test_date,
            time_precision_mode=self.time_precision_mode,
            time_hhmm=self.input_time,
            timezone=self.input_timezone,
            location_precision=self.input_location_precision,
        )


@dataclass
class Experiment:
    experiment_id: str
    dataset_version: str
    dataset_db_path: str
    dataset_checksum_before: str
    rule_registry_version: str
    astronomy_version: str
    astrowatch_version: str
    random_seed: int
    sampling_method: str
    control_method: str
    configuration_hash: str
    created_at: str
    region_used: str = "GLOBAL"
    allow_ayanamsha_fallback: bool = True
    test_window_start: Optional[str] = None
    test_window_end: Optional[str] = None
    dataset_checksum_after: Optional[str] = None
    dataset_integrity: Optional[str] = None
    completed_at: Optional[str] = None
    status: str = "RUNNING"
    frozen: bool = False
    frozen_at: Optional[str] = None
    notes: Optional[str] = None
