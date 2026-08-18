"""
Astrowatch Online -- AI tool surface for the NEW multi-tradition engine layer.
===================================================================
Companion to ai/tools.py (which wraps the ORIGINAL Jyotisha/Hellenistic
reading_engine.py pipeline). This module wraps
world_astrology/engines/*.py + world_astrology/unified_engine.py -- the
computation layer added to make all ten catalogued traditions real,
independently-runnable prediction engines rather than reference-only
knowledge entries.

Same discipline as ai/tools.py: every function here is a thin wrapper. None
of them compute anything themselves; OpenAI (if configured) may CALL these
functions as tools, but the astrological/calendrical math happens entirely
inside world_astrology/engines/*.py before any AI involvement, and AI never
sees or influences the calculation step.

Function list matches this task's own specification (Section 12): run_jyotisha,
run_hellenistic, run_western, run_babylonian, run_persian_islamic, run_chinese,
run_tibetan, run_japanese, run_egyptian, run_mesoamerican, compare_predictions,
generate_unified_prediction.

NOTE ON NAMING: ai/tools.py already exports `run_jyotisha_prediction` (the
OLDER reading_engine.py wrapper, a different and still-fully-functional code
path). The functions here are named exactly per this task's own spec
(`run_jyotisha`, not `run_jyotisha_prediction`) and are intentionally kept in
this separate module so neither pipeline silently shadows the other.
"""

import dataclasses
from typing import Any, Dict, List, Optional

from world_astrology.engine_interface import PredictionContext, TraditionPrediction
from world_astrology.engines.jyotisha_engine import JyotishaEngine
from world_astrology.engines.hellenistic_engine import HellenisticEngine
from world_astrology.engines.western_engine import WesternEngine
from world_astrology.engines.babylonian_engine import BabylonianEngine
from world_astrology.engines.persian_islamic_engine import PersianIslamicEngine
from world_astrology.engines.chinese_engine import ChineseEngine
from world_astrology.engines.tibetan_engine import TibetanEngine
from world_astrology.engines.japanese_engine import JapaneseEngine
from world_astrology.engines.egyptian_engine import EgyptianEngine
from world_astrology.engines.mesoamerican_engine import MesoamericanEngine
from world_astrology.unified_engine import UnifiedAstrologyEngine, ENGINE_REGISTRY


def _build_context(name: str, entity_type: str, date: str, latitude: float, longitude: float,
                    timezone: str, time: Optional[str] = None,
                    prediction_date: Optional[str] = None, prediction_period: Optional[str] = None,
                    geographic_scope: Optional[str] = None, prediction_domain: Optional[str] = None,
                    event_type: Optional[str] = None) -> PredictionContext:
    return PredictionContext(
        entity_name=name, entity_type=entity_type, birth_or_inception_date=date,
        birth_or_inception_time=time, latitude=float(latitude), longitude=float(longitude),
        timezone_name=timezone, time_accuracy="documented" if time else "assumed_midnight",
        prediction_date=prediction_date, prediction_period=prediction_period,
        geographic_scope=geographic_scope, prediction_domain=prediction_domain,
        event_type=event_type,
    )


def _pred_to_dict(pred: TraditionPrediction) -> Dict[str, Any]:
    return dataclasses.asdict(pred)


def _run_one(engine_cls, name, entity_type, date, latitude, longitude, timezone,
             time=None, prediction_date=None, prediction_period=None,
             geographic_scope=None, prediction_domain=None, event_type=None) -> Dict[str, Any]:
    ctx = _build_context(name, entity_type, date, latitude, longitude, timezone, time,
                          prediction_date, prediction_period, geographic_scope,
                          prediction_domain, event_type)
    return _pred_to_dict(engine_cls().predict(ctx))


def run_jyotisha(name, entity_type, date, latitude, longitude, timezone, time=None, **kw) -> Dict[str, Any]:
    return _run_one(JyotishaEngine, name, entity_type, date, latitude, longitude, timezone, time, **kw)


def run_hellenistic(name, entity_type, date, latitude, longitude, timezone, time=None, **kw) -> Dict[str, Any]:
    return _run_one(HellenisticEngine, name, entity_type, date, latitude, longitude, timezone, time, **kw)


def run_western(name, entity_type, date, latitude, longitude, timezone, time=None, **kw) -> Dict[str, Any]:
    return _run_one(WesternEngine, name, entity_type, date, latitude, longitude, timezone, time, **kw)


def run_babylonian(name, entity_type, date, latitude, longitude, timezone, time=None, **kw) -> Dict[str, Any]:
    return _run_one(BabylonianEngine, name, entity_type, date, latitude, longitude, timezone, time, **kw)


def run_persian_islamic(name, entity_type, date, latitude, longitude, timezone, time=None, **kw) -> Dict[str, Any]:
    return _run_one(PersianIslamicEngine, name, entity_type, date, latitude, longitude, timezone, time, **kw)


def run_chinese(name, entity_type, date, latitude, longitude, timezone, time=None, **kw) -> Dict[str, Any]:
    return _run_one(ChineseEngine, name, entity_type, date, latitude, longitude, timezone, time, **kw)


def run_tibetan(name, entity_type, date, latitude, longitude, timezone, time=None, **kw) -> Dict[str, Any]:
    return _run_one(TibetanEngine, name, entity_type, date, latitude, longitude, timezone, time, **kw)


def run_japanese(name, entity_type, date, latitude, longitude, timezone, time=None, **kw) -> Dict[str, Any]:
    return _run_one(JapaneseEngine, name, entity_type, date, latitude, longitude, timezone, time, **kw)


def run_egyptian(name, entity_type, date, latitude, longitude, timezone, time=None, **kw) -> Dict[str, Any]:
    return _run_one(EgyptianEngine, name, entity_type, date, latitude, longitude, timezone, time, **kw)


def run_mesoamerican(name, entity_type, date, latitude, longitude, timezone, time=None, **kw) -> Dict[str, Any]:
    return _run_one(MesoamericanEngine, name, entity_type, date, latitude, longitude, timezone, time, **kw)


def compare_predictions(name, entity_type, date, latitude, longitude, timezone, time=None,
                         traditions: Optional[List[str]] = None, **kw) -> Dict[str, Any]:
    """Runs every requested tradition (default: all 10) independently and
    returns each raw TraditionPrediction, WITHOUT any cross-tradition
    synthesis -- that step is generate_unified_prediction()'s job. Lets the
    AI (or a caller) inspect individual results before/instead of the
    unified reading."""
    ctx = _build_context(name, entity_type, date, latitude, longitude, timezone, time, **kw)
    engine = UnifiedAstrologyEngine(traditions=traditions)
    return {tname: _pred_to_dict(ENGINE_REGISTRY[tname]().predict(ctx)) for tname in engine.traditions}


def generate_unified_prediction(name, entity_type, date, latitude, longitude, timezone, time=None,
                                 traditions: Optional[List[str]] = None, **kw) -> Dict[str, Any]:
    """Runs UnifiedAstrologyEngine's full pipeline: all applicable engines ->
    theme clustering -> agreement/conflict analysis -> transparent categorical
    weighting -> unified prediction text. Reports the mandatory transparency
    counts (traditions evaluated/applicable/calculated/unavailable) -- never
    claims a tradition contributed unless it actually returned status='calculated'."""
    ctx = _build_context(name, entity_type, date, latitude, longitude, timezone, time, **kw)
    engine = UnifiedAstrologyEngine(traditions=traditions)
    unified = engine.generate_unified_prediction(ctx)
    result = dataclasses.asdict(unified)
    return result
