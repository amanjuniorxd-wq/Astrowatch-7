"""Tests for astrowatch/mundane/entity_chart.py -- the universal mundane-astrology
rule (see MUNDANE_ASTROLOGY_RULE.md): any entity with a real inception date/place
(and, per the user's stated rule, an assumed 00:00 time if no real time is known)
can get a kundli + Vimshottari Mahadasha timeline computed."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import coordinates
from mundane.entity_chart import (
    compute_entity_chart, full_lifetime_dasha,
    TIME_SOURCE_ASSUMED_MIDNIGHT, TIME_SOURCE_DOCUMENTED, DEFAULT_TIME,
)


def test_assumed_midnight_default_when_no_time_given():
    ec = compute_entity_chart("India", "nation", "1947-08-15", 28.6139, 77.2090, "Asia/Kolkata")
    assert ec.time_source == TIME_SOURCE_ASSUMED_MIDNIGHT
    assert ec.inception_time == DEFAULT_TIME == "00:00"


def test_documented_time_used_when_given():
    ec = compute_entity_chart("Test Person", "person", "1990-01-15", 28.6139, 77.2090,
                               "Asia/Kolkata", inception_time="08:30")
    assert ec.time_source == TIME_SOURCE_DOCUMENTED
    assert ec.inception_time == "08:30"


def test_entity_chart_matches_kundli_compute_kundli_directly():
    """Same jd/lat/lon fed straight into kundli.compute_kundli() must match
    exactly -- entity_chart.py must not silently alter the underlying math."""
    from kundli import compute_kundli
    ec = compute_entity_chart("India", "nation", "1947-08-15", 28.6139, 77.2090, "Asia/Kolkata")
    direct = compute_kundli(ec.jd_ut, 28.6139, 77.2090)
    assert ec.chart.ayanamsha_deg == direct.ayanamsha_deg
    assert ec.chart.ascendant_sidereal_deg == direct.ascendant_sidereal_deg
    for g in ec.chart.grahas:
        assert ec.chart.grahas[g].sidereal_lon_deg == direct.grahas[g].sidereal_lon_deg


def test_full_lifetime_dasha_covers_multi_century_span_for_old_nations():
    """A nation older than 120 years (one Vimshottari cycle) must still have a
    dasha period covering 'today' -- regression test for the single-cycle cap
    bug found and fixed this session (dasha_timeline.full_lifetime_sequence's
    max_cycles parameter)."""
    ec = compute_entity_chart("United States", "nation", "1776-07-04", 38.9072, -77.0369, "America/New_York")
    today_jd = coordinates.julian_day(2026, 8, 17, 0.0)
    periods = full_lifetime_dasha(ec, today_jd)
    assert len(periods) > 0
    covers_today = any(p[6] <= today_jd <= p[7] for p in periods)
    assert covers_today, "expected a dasha period from a 250-year-old nation's chart to cover today"


def test_default_one_cycle_cap_still_applies_to_dasha_timeline_directly():
    """dasha_timeline.full_lifetime_sequence's OWN default (max_cycles=1) must be
    unchanged, since build_famous_lifetime_dasha.py's already-committed person
    corpus behavior must not silently change."""
    from mundane.dasha_timeline import full_lifetime_sequence
    birth_jd = coordinates.julian_day(1889, 4, 16, 12.0)  # Charlie Chaplin-era date
    from kundli import compute_kundli
    chart = compute_kundli(birth_jd, 51.50, -0.10)
    far_future_jd = birth_jd + 200 * 365.25636  # 200 years later
    periods = list(full_lifetime_sequence(birth_jd, chart.grahas["moon"].sidereal_lon_deg, far_future_jd))
    last_end = max(p[7] for p in periods)
    assert last_end <= birth_jd + 120 * 365.25636 + 1  # capped at ~one cycle, not 200 years
