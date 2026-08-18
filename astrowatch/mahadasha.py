"""
Astrowatch — Vimshottari Mahadasha calculator.
==================================================
NEW MODULE. Computes which Mahadasha (and Antardasha sub-period) is running at a given
moment, based on the Moon's sidereal Nakshatra position at that moment (per the
Vimshottari system, "birth" = the reference instant — here, the historical event's own
date/time, not a person's birth, since the point is to characterize the astrological
period an EVENT occurred within).

VIMSHOTTARI SYSTEM — standard reference data, not a disputed/interpretive claim (same
status as rashi_nakshatra.py's Rāśi/Nakshatra names/order): a fixed 120-year cycle
split across 9 planetary lords in a fixed order, each governing a fixed number of
years; each of the 27 Nakshatras is pre-assigned a starting dasha-lord (the sequence
below, repeated 3x across 27 nakshatras = 9 lords x 3). This is the same system used
by essentially every Vedic astrology software package — encoded here directly from
its well-established mathematical definition, not paraphrased from any of this
project's cited primary sources (Bṛhat Saṃhitā / Tetrabiblos do not describe
Vimshottari Dasha; it is a separate, later system).
"""

from dataclasses import dataclass
from typing import List, Optional

import rashi_nakshatra as rn

# Fixed order and year-length of each Mahadasha lord (total = 120 years).
DASHA_SEQUENCE = [
    ("ketu", 7), ("venus", 20), ("sun", 6), ("moon", 10), ("mars", 7),
    ("rahu", 18), ("jupiter", 16), ("saturn", 19), ("mercury", 17),
]
DASHA_TOTAL_YEARS = sum(y for _, y in DASHA_SEQUENCE)  # 120
assert DASHA_TOTAL_YEARS == 120

# Each of the 27 nakshatras' starting dasha-lord, in nakshatra order (index 0 =
# Ashwini .. 26 = Revati). The 9-lord sequence above repeats exactly 3 times.
NAKSHATRA_STARTING_LORD = [DASHA_SEQUENCE[i % 9][0] for i in range(27)]

_SIDEREAL_YEAR_DAYS = 365.25636  # standard sidereal year length, for dasha-duration math


@dataclass
class DashaPeriod:
    lord: str
    start_jd_ut: float
    end_jd_ut: float
    level: str   # "mahadasha" | "antardasha"


@dataclass
class DashaState:
    moon_sidereal_lon_deg: float
    moon_nakshatra: rn.NakshatraPlacement
    mahadasha: DashaPeriod
    antardasha: DashaPeriod
    elapsed_in_mahadasha_years: float
    balance_in_mahadasha_years: float


def _lord_index(lord: str) -> int:
    for i, (name, _) in enumerate(DASHA_SEQUENCE):
        if name == lord:
            return i
    raise ValueError(f"unknown dasha lord {lord!r}")


def compute_dasha_state(jd_ut: float, moon_sidereal_lon_deg: float) -> DashaState:
    """
    jd_ut: the moment to evaluate (e.g. a historical event's date/time, NOT
    necessarily a person's birth — Vimshottari Dasha is a pure function of the Moon's
    sidereal position at any reference instant).
    moon_sidereal_lon_deg: Moon's sidereal longitude at jd_ut (caller supplies this —
    same "caller supplies real, already-computed astronomical input" convention as
    forecast.get_astronomical_snapshot(); this module does not fetch or compute
    planetary positions itself).
    """
    nakshatra = rn.nakshatra_for_longitude(moon_sidereal_lon_deg)
    starting_lord = NAKSHATRA_STARTING_LORD[nakshatra.nakshatra_index]
    start_idx = _lord_index(starting_lord)

    # Fraction of the current nakshatra ALREADY ELAPSED at jd_ut determines how much
    # of the starting lord's Mahadasha has already elapsed (standard Vimshottari
    # balance-of-dasha-at-birth calculation).
    fraction_elapsed = nakshatra.degree_in_nakshatra / rn.NAKSHATRA_WIDTH_DEG
    starting_lord_years = DASHA_SEQUENCE[start_idx][1]
    elapsed_years = fraction_elapsed * starting_lord_years
    balance_years = starting_lord_years - elapsed_years

    mahadasha_start_jd = jd_ut - elapsed_years * _SIDEREAL_YEAR_DAYS
    mahadasha_end_jd = jd_ut + balance_years * _SIDEREAL_YEAR_DAYS
    mahadasha = DashaPeriod(
        lord=starting_lord, start_jd_ut=mahadasha_start_jd, end_jd_ut=mahadasha_end_jd,
        level="mahadasha",
    )

    antardasha = _compute_antardasha(jd_ut, mahadasha, start_idx)

    return DashaState(
        moon_sidereal_lon_deg=moon_sidereal_lon_deg, moon_nakshatra=nakshatra,
        mahadasha=mahadasha, antardasha=antardasha,
        elapsed_in_mahadasha_years=elapsed_years, balance_in_mahadasha_years=balance_years,
    )


def _compute_antardasha(jd_ut: float, mahadasha: DashaPeriod, maha_lord_idx: int) -> DashaPeriod:
    """Antardasha (sub-period) sequence within a Mahadasha starts with the SAME lord
    as the Mahadasha itself, then proceeds through the same 9-lord cyclic order.
    Each antardasha's length is proportional to (antardasha_lord_years *
    mahadasha_lord_years) / 120 — the standard Vimshottari sub-period formula."""
    maha_lord_years = DASHA_SEQUENCE[maha_lord_idx][1]
    cursor_jd = mahadasha.start_jd_ut
    for offset in range(9):
        sub_idx = (maha_lord_idx + offset) % 9
        sub_lord, sub_lord_years = DASHA_SEQUENCE[sub_idx]
        sub_duration_days = (sub_lord_years * maha_lord_years / 120.0) * _SIDEREAL_YEAR_DAYS
        sub_end_jd = cursor_jd + sub_duration_days
        if cursor_jd <= jd_ut < sub_end_jd or offset == 8:
            return DashaPeriod(lord=sub_lord, start_jd_ut=cursor_jd, end_jd_ut=sub_end_jd, level="antardasha")
        cursor_jd = sub_end_jd
    raise RuntimeError("unreachable -- antardasha sequence must cover the full mahadasha span")
