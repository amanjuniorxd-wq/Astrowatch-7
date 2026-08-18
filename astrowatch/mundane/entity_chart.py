"""
Astrowatch -- universal "entity chart" (the mundane-astrology rule).

THE RULE (as stated by the user, verbatim intent preserved):
    Anything can be analysed via kundli + Mahadasha if the inception of that
    thing has a real date, place, and (optionally) time. If time is not
    available, assume 00:00 (midnight) local civil time. This applies no
    matter what kind of entity the "kundli" belongs to -- a person, a nation,
    a company, a stock exchange, a sports team, a political leader's term,
    or anything else with one identifiable founding/starting moment and a
    real location.

This module is the one place that rule is implemented. Everything downstream
(kundli.compute_kundli for the planetary positions, mahadasha.compute_dasha_state
+ mundane.dasha_timeline.full_lifetime_sequence for the Vimshottari timeline) is
UNCHANGED, general-purpose machinery this project already built and validated for
people and historical events -- there is nothing person-specific in that machinery
to begin with. What's new here is just: (1) a single, explicit, honestly-documented
default-time convention for entities whose exact founding time isn't known or
doesn't meaningfully exist, and (2) one shared entry point so every entity type
(nations, leaders, teams, markets, ...) goes through identical code, rather than
each getting its own slightly-different one-off script.

IMPORTANT CAVEAT, stated up front and repeated in every report this module's output
feeds: using an assumed 00:00 birth/founding time means the Ascendant and all
house placements for that chart are NOT reliable (the Ascendant moves roughly
1 degree every 4 minutes; a wrong assumed time can put it in the wrong sign
entirely). What DOES remain reasonably meaningful at an assumed time: the Moon's
Rashi/Nakshatra and therefore the Vimshottari Mahadasha/Antardasha lord sequence
(low sensitivity to a few hours' time error -- see this project's own measured
Moon-position accuracy notes elsewhere), and all non-Moon planets' sign placements
(essentially time-independent within a single day). Any pattern this project draws
from entity charts should weight accordingly: Mahadasha-lord correlations are on
much firmer ground than house/Ascendant-based claims for anything using the 00:00
default.
"""

import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone as dt_timezone
from typing import Dict, List, Optional
from zoneinfo import ZoneInfo

ASTROWATCH_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ASTROWATCH_DIR not in sys.path:
    sys.path.insert(0, ASTROWATCH_DIR)

import coordinates
from kundli import compute_kundli, KundliChart
from mahadasha import compute_dasha_state, DashaState
from mundane.dasha_timeline import full_lifetime_sequence, jd_to_iso_date

DEFAULT_TIME = "00:00"  # the rule's stated default when no real inception time is known
TIME_SOURCE_DOCUMENTED = "DOCUMENTED"   # a real, sourced founding/birth time was used
TIME_SOURCE_ASSUMED_MIDNIGHT = "ASSUMED_MIDNIGHT"  # this module's default per the rule


@dataclass
class EntityChart:
    entity_name: str
    entity_type: str            # "nation" | "person" | "company" | "sports_team" | ...
    inception_date: str         # "YYYY-MM-DD"
    inception_time: str         # "HH:MM", real or the ASSUMED_MIDNIGHT default
    time_source: str            # TIME_SOURCE_DOCUMENTED | TIME_SOURCE_ASSUMED_MIDNIGHT
    timezone_name: str
    latitude: float
    longitude: float
    jd_ut: float
    chart: KundliChart
    natal_dasha: DashaState


def _jd_ut_for(date_str: str, time_str: str, tz_name: str) -> float:
    y, m, d = (int(x) for x in date_str.split("-"))
    hh, mm = (int(x) for x in time_str.split(":")[:2])
    local_dt = datetime(y, m, d, hh, mm, tzinfo=ZoneInfo(tz_name))
    utc_dt = local_dt.astimezone(dt_timezone.utc)
    return coordinates.julian_day(utc_dt.year, utc_dt.month, utc_dt.day,
                                   utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0)


def compute_entity_chart(
    entity_name: str,
    entity_type: str,
    inception_date: str,
    latitude: float,
    longitude: float,
    timezone_name: str,
    inception_time: Optional[str] = None,
) -> EntityChart:
    """
    inception_date: "YYYY-MM-DD" -- the entity's real founding/inception date
        (a nation's independence/formation date, a company's incorporation date,
        a sports team's founding date, a person's birth date, etc).
    latitude/longitude: REAL geographic coordinates of where the inception took
        place (capital city for a nation, headquarters city for a company, etc).
        Never fabricate a location -- if it isn't known, don't chart this entity.
    timezone_name: IANA zone name valid for that place at that date (handles
        historical offset/DST changes correctly, same convention as timeutil.py).
    inception_time: "HH:MM" if a real, specific inception time is known and
        sourced (rare for nations/companies; common for people). If None, this
        function applies the rule's stated default -- 00:00 local civil time --
        and tags the result TIME_SOURCE_ASSUMED_MIDNIGHT so every downstream
        consumer can see, honestly, which charts are time-reliable and which
        are not.
    """
    if inception_time:
        time_str = inception_time
        time_source = TIME_SOURCE_DOCUMENTED
    else:
        time_str = DEFAULT_TIME
        time_source = TIME_SOURCE_ASSUMED_MIDNIGHT

    jd_ut = _jd_ut_for(inception_date, time_str, timezone_name)
    chart = compute_kundli(jd_ut, latitude, longitude)
    natal_dasha = compute_dasha_state(jd_ut, chart.grahas["moon"].sidereal_lon_deg)

    return EntityChart(
        entity_name=entity_name, entity_type=entity_type,
        inception_date=inception_date, inception_time=time_str, time_source=time_source,
        timezone_name=timezone_name, latitude=latitude, longitude=longitude,
        jd_ut=jd_ut, chart=chart, natal_dasha=natal_dasha,
    )


def full_lifetime_dasha(entity: EntityChart, end_jd_ut: float, max_cycles=None) -> List[tuple]:
    """Returns the full list of (mahadasha_index, mahadasha_lord, maha_start_jd,
    maha_end_jd, antardasha_index, antardasha_lord, antar_start_jd, antar_end_jd)
    tuples from inception through end_jd_ut -- e.g. pass today's JD to get "every
    period from founding to now". max_cycles=None (the default here, deliberately
    different from dasha_timeline.full_lifetime_sequence's own default of 1) walks
    as many full 120-year Vimshottari cycles as needed to reach end_jd_ut -- correct
    for entities that can outlive a person's lifespan, e.g. most nations."""
    natal_moon_lon = entity.chart.grahas["moon"].sidereal_lon_deg
    return list(full_lifetime_sequence(entity.jd_ut, natal_moon_lon, end_jd_ut, max_cycles=max_cycles))
