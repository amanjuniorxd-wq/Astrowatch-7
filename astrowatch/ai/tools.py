"""
Astrowatch Online -- internal tool surface for the AI agent.
================================================================
Every function here is a THIN WRAPPER around a real, pre-existing Astrowatch
function. None of them compute anything themselves -- they translate between
the AI layer's simple keyword-argument calling convention and this project's
already-built, already-tested engine modules:

    kundli.compute_kundli                  <- calculate_transits()/calculate_entity_chart()
    mundane.entity_chart.compute_entity_chart <- calculate_entity_chart()
    world_astrology.reading_engine.*       <- run_jyotisha_prediction(), etc.
    world_astrology.cross_tradition.*      <- run_cross_tradition_analysis()
    world_astrology.registry.build_registry <- run_world_astrology()
    forecast.run_forecast                  <- run_mundane_prediction()
    historical.repository.get_events       <- search_historical_events()
    entities_db.*                          <- get_entity() / search_entities()
    predictions_db.*                       <- save_prediction() / get_prediction_history()

This is the exact function list from the task spec's Section 8, each backed by
real project code -- no calculation is duplicated or reimplemented here.
"""

import os
import sys
from typing import Any, Dict, List, Optional

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # astrowatch/
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import coordinates
import entities_db
import predictions_db
from kundli import compute_kundli, EphemerisDataUnavailable
from mundane.entity_chart import compute_entity_chart
from timeutil import local_to_jd_ut
from historical import database as hist_database, repository as hist_repository
from world_astrology import reading_engine, cross_tradition, registry as wa_registry
import forecast as forecast_mod

HISTORICAL_DB_PATH = os.path.join(HERE, "historical_events.db")

# THREAD-SAFETY: api.py serves each HTTP request on its own thread
# (ThreadingHTTPServer), and sqlite3 connections are NOT safe to share across
# threads by default (confirmed this session -- a single cached module-level
# connection created in one thread raised sqlite3.ProgrammingError when a
# later request from a different thread tried to reuse it, the same class of
# cross-thread bug already found and fixed in kundli.py's ephemeris state).
# Rather than pass check_same_thread=False (which just papers over concurrent-
# write risk instead of fixing it), each call opens its own short-lived
# connection -- consistent with this project's existing convention elsewhere
# (historical/database.connect(), backtest/database.py) of "open per call/
# short-lived script," not a new pattern invented for this module.
def _entities_connection():
    return entities_db.get_connection()


def _predictions_connection():
    return predictions_db.get_connection()


class ToolError(Exception):
    """Raised by any tool function for a caller-facing, non-fabricated error
    (entity not found, ephemeris unavailable, invalid input, etc). Distinct
    from ai.openai_client.AIUnavailable, which is specifically about the AI
    call layer -- these tool functions never call OpenAI themselves."""


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------

def get_entity(entity_id: int) -> Dict[str, Any]:
    e = entities_db.get_entity(_entities_connection(), entity_id)
    if e is None:
        raise ToolError(f"No entity with id={entity_id}")
    return e.__dict__


def search_entities(query: Optional[str] = None, entity_type: Optional[str] = None,
                     category: Optional[str] = None, limit: int = 25) -> List[Dict[str, Any]]:
    rows = entities_db.search_entities(_entities_connection(), query=query,
                                        entity_type=entity_type, category=category, limit=limit)
    return [r.__dict__ for r in rows]


# ---------------------------------------------------------------------------
# Chart calculation
# ---------------------------------------------------------------------------

def calculate_entity_chart(name: str, entity_type: str, date: str, latitude: float,
                            longitude: float, timezone: str,
                            time: Optional[str] = None) -> Dict[str, Any]:
    """Wraps mundane.entity_chart.compute_entity_chart -- THE mundane-astrology
    rule (real date+place -> chart; missing time -> assumed 00:00, honestly
    labeled). Returns a JSON-safe dict, never a raw dataclass with Python
    objects the AI layer can't serialize."""
    try:
        entity = compute_entity_chart(name, entity_type, date, latitude, longitude,
                                       timezone, inception_time=time)
    except Exception as e:  # noqa: BLE001 -- surfaced as ToolError, not a crash
        raise ToolError(f"calculate_entity_chart failed: {e}") from e
    chart = entity.chart
    return {
        "entity_name": entity.entity_name,
        "entity_type": entity.entity_type,
        "inception_date": entity.inception_date,
        "inception_time": entity.inception_time,
        "time_accuracy": ("documented" if entity.time_source == "DOCUMENTED"
                           else "assumed_midnight"),
        "ascendant": {"sign": chart.ascendant_rashi.rashi_name,
                      "degree_in_sign": round(chart.ascendant_rashi.degree_in_rashi, 4)},
        "planets": {
            g: {"sign": p.rashi.rashi_name, "nakshatra": p.nakshatra.nakshatra_name,
                "house": p.house, "retrograde": p.retrograde,
                "tropical_longitude": round(p.tropical_lon_deg, 4),
                "sidereal_longitude": round(p.sidereal_lon_deg, 4)}
            for g, p in chart.grahas.items()
        },
        "natal_mahadasha": {"lord": entity.natal_dasha.mahadasha.lord},
        "natal_antardasha": {"lord": entity.natal_dasha.antardasha.lord},
        "engine": chart.engine,
    }


def calculate_transits(date: str, latitude: float, longitude: float,
                        timezone: str, time: str = "12:00") -> Dict[str, Any]:
    """Current/target-date planetary positions at a location -- wraps
    kundli.compute_kundli directly (no natal-chart framing, just "where are the
    planets on this date")."""
    try:
        time_result = local_to_jd_ut(date, time, timezone)
        chart = compute_kundli(time_result.jd_ut, latitude, longitude)
    except EphemerisDataUnavailable as e:
        raise ToolError(f"Ephemeris data unavailable: {e}") from e
    except Exception as e:  # noqa: BLE001
        raise ToolError(f"calculate_transits failed: {e}") from e
    return {
        "date": date, "time": time, "timezone": timezone,
        "planets": {g: {"sign": p.rashi.rashi_name, "house": p.house,
                        "tropical_longitude": round(p.tropical_lon_deg, 4)}
                    for g, p in chart.grahas.items()},
        "ascendant": {"sign": chart.ascendant_rashi.rashi_name},
    }


# ---------------------------------------------------------------------------
# World-astrology reading engine (Jyotisha / Hellenistic / Western / Chinese +
# cross-tradition agreement) -- all backed by world_astrology/reading_engine.py
# ---------------------------------------------------------------------------

def run_jyotisha_prediction(name: str, entity_type: str, date: str, latitude: float,
                             longitude: float, timezone: str,
                             time: Optional[str] = None,
                             as_of_date: Optional[str] = None) -> Dict[str, Any]:
    b = reading_engine.build_chart_bundle(name, entity_type, date, latitude, longitude,
                                           timezone, inception_time=time, as_of_date=as_of_date)
    return {
        "ascendant": b.entity.chart.ascendant_rashi.rashi_name,
        "moon_sign": b.entity.chart.grahas["moon"].rashi.rashi_name,
        "moon_nakshatra": b.entity.chart.grahas["moon"].nakshatra.nakshatra_name,
        "as_of_date": b.as_of_date,
        "mahadasha_lord": b.dasha.mahadasha_lord, "mahadasha_start": b.dasha.mahadasha_start,
        "mahadasha_end": b.dasha.mahadasha_end, "antardasha_lord": b.dasha.antardasha_lord,
        "antardasha_end": b.dasha.antardasha_end,
        "jyotisha_dignity": b.agreement.jyotisha_dignity, "jyotisha_score": b.agreement.jyotisha_score,
        "time_accuracy": ("documented" if b.entity.time_source == "DOCUMENTED"
                           else "assumed_midnight"),
        "computed": True,
    }


def run_cross_tradition_analysis(name: str, entity_type: str, date: str, latitude: float,
                                  longitude: float, timezone: str,
                                  time: Optional[str] = None,
                                  as_of_date: Optional[str] = None) -> Dict[str, Any]:
    """Wraps build_chart_bundle's Jyotisha-vs-Hellenistic classify_agreement()
    output (the project's real cross-tradition engine) plus the descriptive
    Western/Chinese context build_chart_bundle already computes."""
    b = reading_engine.build_chart_bundle(name, entity_type, date, latitude, longitude,
                                           timezone, inception_time=time, as_of_date=as_of_date)
    return {
        "agreement_classification": b.agreement.classification,
        "reasoning": b.agreement.reasoning,
        "jyotisha_dignity": b.agreement.jyotisha_dignity, "jyotisha_score": b.agreement.jyotisha_score,
        "hellenistic_dignity": b.agreement.hellenistic_dignity, "hellenistic_score": b.agreement.hellenistic_score,
        "is_day_chart": b.is_day_chart,
        "western_sun_sign": b.western_signs.get("sun"),
        "chinese_birth_year": list(b.chinese_birth_year),
        "chinese_as_of_year": list(b.chinese_as_of_year),
        "computed_traditions": wa_registry.build_registry().computed_traditions(),
        "all_cataloged_traditions": wa_registry.build_registry().traditions(),
    }


def run_world_astrology(name: str, entity_type: str, date: str, latitude: float,
                         longitude: float, timezone: str, time: Optional[str] = None,
                         as_of_date: Optional[str] = None) -> Dict[str, Any]:
    """Wraps generate_world_reading -- the mundane/collective-entity reading mode."""
    text = reading_engine.generate_world_reading(name, date, latitude, longitude, timezone,
                                                   entity_type=entity_type, inception_time=time,
                                                   as_of_date=as_of_date)
    return {"world_reading_text": text}


def run_mundane_prediction(name: str, entity_type: str, date: str, latitude: float,
                            longitude: float, timezone: str, time: Optional[str] = None,
                            region: str = "GLOBAL", domain: str = "GENERAL",
                            allow_ayanamsha_fallback: bool = False) -> Dict[str, Any]:
    """Wraps forecast.run_forecast -- the project's separate, cited-source
    (Brhat Samhita/Tetrabiblos) rule-matching engine. Computes the entity's
    chart first (for real tropical longitudes -- forecast.run_forecast never
    computes positions itself, it only evaluates rules against caller-supplied
    ones) then evaluates the fixed rule registry against it.

    KNOWN PRE-EXISTING LIMITATION (not introduced by this tool, see
    ARCHITECTURE_REPORT_ONLINE.md): forecast.py's own sidereal/ayanamsha step
    (separate from kundli.py's validated file-based Swiss Ephemeris pipeline)
    queries astro.com's swetest.cgi live over the network by default, and
    raises rather than silently degrading if that network call fails or is
    blocked (e.g. by a restrictive outbound proxy/firewall in some deployment
    environments) -- same no-silent-fallback philosophy as the rest of this
    project. allow_ayanamsha_fallback=True opts into forecast.py's own
    documented lower-precision linear ayanamsha approximation (~14-64 arcsec
    error) instead of failing outright; this tool does NOT default to that
    silently -- the caller (AI agent or end user) must explicitly request it."""
    try:
        entity = compute_entity_chart(name, entity_type, date, latitude, longitude,
                                       timezone, inception_time=time)
    except Exception as e:  # noqa: BLE001
        raise ToolError(f"run_mundane_prediction chart step failed: {e}") from e
    tropical = {g: p.tropical_lon_deg for g, p in entity.chart.grahas.items()
                if g not in ("rahu", "ketu")}
    try:
        result = forecast_mod.run_forecast(
            entity.jd_ut, date, forecast_start=date, forecast_end=date,
            tropical_longitudes_deg=tropical, region=region, domain=domain,
            allow_ayanamsha_fallback=allow_ayanamsha_fallback,
        )
    except forecast_mod.ProductionCalculationUnavailable as e:
        raise ToolError(
            f"run_mundane_prediction: forecast.py's live ayanamsha network query "
            f"failed (this deployment's network egress likely blocks astro.com) "
            f"and allow_ayanamsha_fallback=False, so no result was produced -- no "
            f"approximate calculation was silently substituted. Retry with "
            f"allow_ayanamsha_fallback=True to accept forecast.py's documented "
            f"lower-precision fallback instead, or use run_jyotisha_prediction / "
            f"run_cross_tradition_analysis, which use the validated file-based "
            f"Swiss Ephemeris pipeline and do not depend on network access. "
            f"Underlying error: {e}"
        ) from e
    except Exception as e:  # noqa: BLE001
        raise ToolError(f"run_mundane_prediction rule evaluation failed: {e}") from e
    return {
        "prediction_id": result.prediction_id, "prediction_text": result.prediction_text,
        "rules_fired": result.rules_fired, "evidence_level": result.evidence_level,
        "confidence": result.confidence, "no_forecast_reasons": result.no_forecast_reasons,
    }


def generate_short_reading(name: str, entity_type: str, date: str, latitude: float,
                            longitude: float, timezone: str, time: Optional[str] = None,
                            as_of_date: Optional[str] = None, max_sentences: int = 5) -> Dict[str, Any]:
    text = reading_engine.generate_short_reading(name, entity_type, date, latitude, longitude,
                                                   timezone, inception_time=time,
                                                   as_of_date=as_of_date, max_sentences=max_sentences)
    return {"short_reading_text": text}


def generate_detailed_reading(name: str, entity_type: str, date: str, latitude: float,
                               longitude: float, timezone: str, time: Optional[str] = None,
                               as_of_date: Optional[str] = None) -> Dict[str, Any]:
    text = reading_engine.generate_detailed_reading(name, entity_type, date, latitude, longitude,
                                                       timezone, inception_time=time,
                                                       as_of_date=as_of_date)
    return {"detailed_reading_text": text}


# ---------------------------------------------------------------------------
# Historical events
# ---------------------------------------------------------------------------

def search_historical_events(category: Optional[str] = None, region: Optional[str] = None,
                              country_code: Optional[str] = None, start_date: Optional[str] = None,
                              end_date: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
    if not os.path.isfile(HISTORICAL_DB_PATH):
        raise ToolError(f"historical_events.db not found at {HISTORICAL_DB_PATH}")
    conn = hist_database.connect(HISTORICAL_DB_PATH)
    try:
        rows = hist_repository.get_events(conn, category=category, region=region,
                                           country_code=country_code, start_date=start_date,
                                           end_date=end_date)
    finally:
        conn.close()
    out = [dict(r) for r in rows[:limit]]
    return out


# ---------------------------------------------------------------------------
# Prediction persistence
# ---------------------------------------------------------------------------

def save_prediction(entity: str, question: str, prediction: str,
                     calculation_data: Dict[str, Any], **kwargs) -> str:
    return predictions_db.save_prediction(_predictions_connection(), entity=entity,
                                           question=question, prediction=prediction,
                                           calculation_data=calculation_data, **kwargs)


def get_prediction_history(entity: Optional[str] = None, mode: Optional[str] = None,
                            limit: int = 50) -> List[Dict[str, Any]]:
    rows = predictions_db.get_prediction_history(_predictions_connection(), entity=entity,
                                                  mode=mode, limit=limit)
    return [r.__dict__ for r in rows]
