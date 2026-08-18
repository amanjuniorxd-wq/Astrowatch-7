"""
Astrowatch — Rāśi (sidereal zodiac sign) / Nakshatra classification
====================================================================
ARCHITECTURE LAYER: this module sits AFTER the sidereal transformation
(ayanamsha.tropical_to_sidereal_lahiri()) and BEFORE any rule engine. It takes an
already-computed SIDEREAL longitude (degrees, 0-360) and classifies it into a Rāśi
(one of the 12 thirty-degree signs) and a Nakshatra (one of the 27 lunar mansions,
13°20' each). It does not itself know or care how the sidereal longitude was derived
(live Swiss Ephemeris query vs. linear fallback) -- that separation is deliberate, per
the architecture note in ayanamsha.py.

STATUS: written this pass, NOT executed (same sandbox unavailability as everything
else this session -- see ayanamsha.py EXECUTION STATUS). The arithmetic below (integer
division by fixed-width bins) is simple enough that it was hand-traced against the
boundary test cases in tests/test_rashi_nakshatra.py before being committed here.

Rāśi and Nakshatra names/order are standard, uncontroversial reference data (the fixed
12-sign and 27-nakshatra conventions used throughout Vedic astrology, not a disputed or
invented interpretive claim) -- unlike e.g. aspects.py's graha-yuddha thresholds, these
don't need a citation to a specific primary text.
"""

from dataclasses import dataclass


RASHI_NAMES = [
    "Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya",
    "Tula", "Vrischika", "Dhanu", "Makara", "Kumbha", "Meena",
]  # 12 signs, 30 deg each, starting at sidereal 0 deg

NAKSHATRA_NAMES = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]  # 27 nakshatras, 13 deg 20' each, starting at sidereal 0 deg

RASHI_WIDTH_DEG = 30.0
NAKSHATRA_WIDTH_DEG = 360.0 / 27.0  # exactly 13.333... deg = 13 deg 20'
PADA_WIDTH_DEG = NAKSHATRA_WIDTH_DEG / 4.0  # each nakshatra has 4 padas (quarters)

_EPS = 1e-9  # tolerance for boundary snapping, see _normalize_longitude()


@dataclass
class RashiPlacement:
    sidereal_lon_deg: float
    rashi_index: int       # 0-11
    rashi_name: str
    degree_in_rashi: float  # 0.0 (inclusive) - 30.0 (exclusive)


@dataclass
class NakshatraPlacement:
    sidereal_lon_deg: float
    nakshatra_index: int     # 0-26
    nakshatra_name: str
    pada: int                 # 1-4
    degree_in_nakshatra: float  # 0.0 (inclusive) - 13.333... (exclusive)


def _normalize_longitude(lon_deg: float) -> float:
    """
    Wraps any real-valued longitude (including negative values, or values >= 360, both
    of which are legitimate outputs of `tropical - ayanamsha` before wrapping) into
    [0, 360). Uses a small epsilon snap so a value that is mathematically exactly 360.0
    (or numerically indistinguishable from it after floating-point subtraction) lands on
    0.0 rather than on a value like 359.99999999998 that would otherwise be classified
    into the wrong (last) sign/nakshatra by a hair -- this is exactly the kind of
    360->0 wraparound edge case item 10 calls out.
    """
    wrapped = lon_deg % 360.0
    if wrapped > 360.0 - _EPS:
        wrapped = 0.0
    return wrapped


def rashi_for_longitude(sidereal_lon_deg: float) -> RashiPlacement:
    lon = _normalize_longitude(sidereal_lon_deg)
    index = int(lon // RASHI_WIDTH_DEG)
    # Guard against a float `lon` of e.g. 29.999999999999996 (should be sign N, not
    # sign N+1) vs. exactly 30.0 (should be sign N+1) -- integer floor division on a
    # normalized, epsilon-snapped `lon` handles both correctly, but clamp defensively
    # in case of an unexpected floating-point edge (e.g. index == 12 from lon
    # infinitesimally over 360 before snapping caught it).
    index = min(index, 11)
    degree_in_rashi = lon - index * RASHI_WIDTH_DEG
    return RashiPlacement(
        sidereal_lon_deg=sidereal_lon_deg, rashi_index=index,
        rashi_name=RASHI_NAMES[index], degree_in_rashi=degree_in_rashi,
    )


def nakshatra_for_longitude(sidereal_lon_deg: float) -> NakshatraPlacement:
    lon = _normalize_longitude(sidereal_lon_deg)
    index = int(lon // NAKSHATRA_WIDTH_DEG)
    index = min(index, 26)
    degree_in_nakshatra = lon - index * NAKSHATRA_WIDTH_DEG
    pada = min(int(degree_in_nakshatra // PADA_WIDTH_DEG) + 1, 4)
    return NakshatraPlacement(
        sidereal_lon_deg=sidereal_lon_deg, nakshatra_index=index,
        nakshatra_name=NAKSHATRA_NAMES[index], pada=pada,
        degree_in_nakshatra=degree_in_nakshatra,
    )


def classify(sidereal_lon_deg: float):
    """Convenience: returns (RashiPlacement, NakshatraPlacement) together."""
    return rashi_for_longitude(sidereal_lon_deg), nakshatra_for_longitude(sidereal_lon_deg)
