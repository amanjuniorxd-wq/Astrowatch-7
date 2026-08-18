"""
Astrowatch World Astrology engines -- shared helpers.
=========================================================
Thin, reusable wrappers around the project's EXISTING astronomical primitives
(kundli.py, mundane/entity_chart.py, coordinates.py, timeutil.py) so every
tradition engine gets identical, already-validated astronomical input rather
than each re-deriving Julian Day / planetary longitude logic itself. No
engine module should call swisseph directly -- always go through here (or
through kundli.py/mundane.entity_chart.py directly for the two things this
module doesn't wrap, like full natal Ascendant/house computation).
"""

import os
import sys
from datetime import date as _date
from typing import Dict, Optional

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # astrowatch/
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import coordinates
from kundli import compute_kundli, KundliChart
from mundane.entity_chart import compute_entity_chart, EntityChart
from timeutil import local_to_jd_ut


def context_jd_ut(context) -> float:
    """Julian Day (UT) for the context's birth/inception moment."""
    time_str = context.birth_or_inception_time or "00:00"
    y, m, d = (int(x) for x in context.birth_or_inception_date.split("-"))
    from datetime import datetime, timezone as dt_timezone
    from zoneinfo import ZoneInfo
    hh, mm = (int(x) for x in time_str.split(":")[:2])
    local_dt = datetime(y, m, d, hh, mm, tzinfo=ZoneInfo(context.timezone_name))
    utc_dt = local_dt.astimezone(dt_timezone.utc)
    return coordinates.julian_day(utc_dt.year, utc_dt.month, utc_dt.day,
                                   utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0)


def prediction_date_jd_ut(context) -> float:
    """Julian Day (UT, noon) for context.prediction_date, defaulting to
    today if unset -- used by every engine's transit/timing-relevant step."""
    ds = context.prediction_date or _date.today().isoformat()
    y, m, d = (int(x) for x in ds.split("-"))
    return coordinates.julian_day(y, m, d, 12.0)


def natal_chart(context) -> EntityChart:
    """Full natal/inception EntityChart (Ascendant, houses, Rashi/Nakshatra,
    Mahadasha) via the project's existing, validated mundane-astrology rule
    implementation. Cached on context.astronomical_data so multiple engines
    sharing one context don't recompute it."""
    cache_key = "_natal_chart"
    cached = context.astronomical_data.get(cache_key)
    if cached is not None:
        return cached
    chart = compute_entity_chart(
        context.entity_name, context.entity_type, context.birth_or_inception_date,
        context.latitude, context.longitude, context.timezone_name,
        inception_time=context.birth_or_inception_time,
    )
    context.astronomical_data[cache_key] = chart
    return chart


def transit_chart(context) -> KundliChart:
    """Planetary positions at context.prediction_date (noon, at the entity's
    own location -- consistent with how this project's existing Gochara-style
    reasoning elsewhere treats transits). Cached per prediction_date."""
    cache_key = f"_transit_chart_{context.prediction_date}"
    cached = context.astronomical_data.get(cache_key)
    if cached is not None:
        return cached
    jd = prediction_date_jd_ut(context)
    chart = compute_kundli(jd, context.latitude, context.longitude)
    context.astronomical_data[cache_key] = chart
    return chart


SIDEREAL_YEAR_DAYS = 365.25636
TROPICAL_YEAR_DAYS = 365.24219
SYNODIC_MONTH_DAYS = 29.530589  # mean lunar synodic month


def jd_to_iso_date(jd_ut: float) -> str:
    from mundane.dasha_timeline import jd_to_iso_date as _f
    return _f(jd_ut)
