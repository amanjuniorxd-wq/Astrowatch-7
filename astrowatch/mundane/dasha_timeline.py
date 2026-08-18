"""
Astrowatch -- shared full-lifetime Vimshottari Mahadasha/Antardasha timeline walker.

Extracted (unchanged logic) from kundli_mass/build_famous_lifetime_dasha.py so both
the person corpus and the new mundane/entity corpus (nations, leaders, sports teams,
markets, or anything else with a real inception moment) use the exact same,
single-source-of-truth implementation rather than two copies that could drift.
build_famous_lifetime_dasha.py now imports this instead of defining it locally --
its own row-for-row behavior (and therefore famous_people_lifetime_dasha.db) is
unchanged.
"""
import os
import sys

ASTROWATCH_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ASTROWATCH_DIR not in sys.path:
    sys.path.insert(0, ASTROWATCH_DIR)

from mahadasha import compute_dasha_state, DASHA_SEQUENCE, _lord_index, DashaPeriod, _SIDEREAL_YEAR_DAYS


def jd_to_iso_date(jd_ut: float) -> str:
    jd = jd_ut + 0.5
    z = int(jd)
    f = jd - z
    if z < 2299161:
        a = z
    else:
        alpha = int((z - 1867216.25) / 36524.25)
        a = z + 1 + alpha - alpha // 4
    b = a + 1524
    c = int((b - 122.1) / 365.25)
    d = int(365.25 * c)
    e = int((b - d) / 30.6001)
    day = b - d - int(30.6001 * e) + f
    month = e - 1 if e < 14 else e - 13
    year = c - 4716 if month > 2 else c - 4715
    day_int = int(day)
    return f"{year:04d}-{month:02d}-{day_int:02d}"


def full_lifetime_sequence(birth_jd, natal_moon_lon, end_jd, max_cycles=1):
    """
    Yields (mahadasha_index, mahadasha_lord, maha_start_jd, maha_end_jd,
            antardasha_index, antardasha_lord, antar_start_jd, antar_end_jd)
    tuples from birth_jd forward through the Vimshottari sequence, capped at
    min(end_jd, birth_jd + max_cycles * one 120-year cycle).

    "birth_jd" here means whatever reference instant the entity's chart is anchored
    to -- a person's actual birth, or (per the mundane-astrology rule this project
    now applies uniformly) a nation's independence moment, a company's incorporation
    moment, a sports team's founding moment, etc. Vimshottari Dasha is a pure
    function of the Moon's sidereal longitude at that instant; it has no concept of
    "person" built into it.

    max_cycles: how many full 120-year Vimshottari cycles to walk through before
    stopping (the sequence genuinely repeats -- after Mercury Mahadasha ends, it
    returns to whichever lord started the first cycle, indefinitely). Default 1
    matches this function's original behavior (correct for a person -- no one
    outlives one 120-year cycle in this project's existing person-corpus use, so
    this default is unchanged and famous_people_lifetime_dasha.db is unaffected).
    Callers charting long-lived entities that CAN outlive 120 years (nations
    especially -- the United States' chart is 250 years old) must pass a larger
    max_cycles (or None for "as many cycles as needed to reach end_jd").
    """
    birth_dasha = compute_dasha_state(birth_jd, natal_moon_lon)
    cursor = birth_dasha.mahadasha
    idx = _lord_index(cursor.lord)
    if max_cycles is None:
        hard_end_jd = end_jd
    else:
        cycle_end_jd = birth_jd + max_cycles * 120 * _SIDEREAL_YEAR_DAYS
        hard_end_jd = min(end_jd, cycle_end_jd)

    maha_i = 0
    while cursor.start_jd_ut < hard_end_jd:
        maha_lord_years = DASHA_SEQUENCE[idx][1]
        sub_cursor_jd = cursor.start_jd_ut
        for offset in range(9):
            sub_idx = (idx + offset) % 9
            sub_lord, sub_lord_years = DASHA_SEQUENCE[sub_idx]
            sub_duration_days = (sub_lord_years * maha_lord_years / 120.0) * _SIDEREAL_YEAR_DAYS
            sub_end_jd = sub_cursor_jd + sub_duration_days
            if sub_cursor_jd >= hard_end_jd:
                break
            yield (maha_i, cursor.lord, cursor.start_jd_ut, cursor.end_jd_ut,
                   offset, sub_lord, sub_cursor_jd, min(sub_end_jd, hard_end_jd))
            sub_cursor_jd = sub_end_jd
        idx = (idx + 1) % 9
        lord, years = DASHA_SEQUENCE[idx]
        start = cursor.end_jd_ut
        end = start + years * _SIDEREAL_YEAR_DAYS
        cursor = DashaPeriod(lord=lord, start_jd_ut=start, end_jd_ut=end, level="mahadasha")
        maha_i += 1
