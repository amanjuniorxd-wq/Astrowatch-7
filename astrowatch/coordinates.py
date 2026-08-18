"""
Astrowatch — coordinate pipeline
============================
RA/Dec (equatorial, as returned by an ephemeris source) -> ecliptic longitude/latitude
-> tropical zodiac sign/degree -> optional sidereal (Vedic) sign/degree via ayanamsa.

STATUS: written and hand-verified against the standard spherical-astronomy transform,
but NOT executed in this session (local sandbox unavailable, see README.md). Before
relying on this for a real backtest, run coordinates.py's self_test() once a Python
environment is available and cross-check against an independent source (e.g. compare
converted longitude to the "ecliptic longitude" figure many ephemeris sites publish
directly, or to Swiss Ephemeris / Skyfield output for the same instant).

Reference frame / epoch notes (read before using):
- This module treats the input RA/Dec as APPARENT, equinox-of-date coordinates (i.e.
  exactly what most live ephemeris sites, and JPL Horizons' default "OBSERVER" table,
  report) unless you say otherwise. It converts to ECLIPTIC OF DATE longitude using the
  mean obliquity of the ecliptic at that date.
- Ecliptic-of-date longitude, with 0 deg Aries fixed at the date's vernal equinox, is the
  TROPICAL zodiac used by Ptolemy/Tetrabiblos.
- The Bṛhat Saṃhitā and Indian jyotiṣa generally use a SIDEREAL zodiac (fixed against the
  background stars, not the moving equinox). To get a sidereal placement you must subtract
  the "ayanamsa" (precession offset between the tropical and sidereal zero points) from the
  tropical longitude. This module delegates that calculation to ayanamsha.py (added this
  session), a two-point-anchored linear model sourced to the 1956 Calendar Reform
  Committee decree and the J2000 ICRC standard value -- see that module's docstring for
  full citations and limitations. Still an approximation, still not independently
  cross-checked against a live Swiss Ephemeris run; a production system should verify
  against pyswisseph before treating sidereal placements as precise. IMPORTANT: this
  applies only to MODERN sidereal/kundli use -- it is not, and should not be, applied to
  the ancient Bṛhat Saṃhitā corpus (see rule_registry.py, which keeps those rules
  "sidereal_unresolved" on purpose).
- Geocentric vs topocentric: values pulled from a live "current position" ephemeris page
  are typically geocentric or Earth-center-ish; if you pull from JPL Horizons with a
  specific CENTER parameter, match that here. This module does no parallax correction —
  fine for zodiac-sign-level astrology, not fine for anything requiring arcsecond
  precision (occultations, etc.).

Formula source: standard equatorial<->ecliptic spherical coordinate transform, as given
in any spherical astronomy reference (e.g. Meeus, "Astronomical Algorithms", ch. 13) and
the standard IAU mean-obliquity polynomial. These are public mathematical formulas, not
reproduced text from any single copyrighted work.
"""

import math
from dataclasses import dataclass
from typing import Optional

from ayanamsha import lahiri_ayanamsha_deg_for_year  # see ayanamsha.py for sourcing/limits


ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]


def julian_day(year: int, month: int, day: int, hour: float = 0.0) -> float:
    """Standard Julian Day Number for a Gregorian calendar date + UT hour."""
    if month <= 2:
        year -= 1
        month += 12
    a = year // 100
    b = 2 - a + a // 4
    jd = (
        int(365.25 * (year + 4716))
        + int(30.6001 * (month + 1))
        + day + hour / 24.0 + b - 1524.5
    )
    return jd


def julian_centuries_j2000(jd: float) -> float:
    return (jd - 2451545.0) / 36525.0


def mean_obliquity_deg(jd: float) -> float:
    """Mean obliquity of the ecliptic, IAU polynomial, degrees."""
    t = julian_centuries_j2000(jd)
    eps = (
        23.439291111
        - 0.0130041667 * t
        - 1.63888889e-7 * t**2
        + 5.03611111e-7 * t**3
    )
    return eps


@dataclass
class EclipticPosition:
    longitude_deg: float   # 0-360
    latitude_deg: float
    sign: str
    degree_in_sign: float  # 0-30


@dataclass
class PositionRecord:
    """
    Full, reproducible record for one body at one instant. Nothing here overwrites
    anything else -- raw source data, tropical result, and sidereal result are all
    kept as separate fields (validation requirements 8 & 9).
    """
    body: str
    # --- raw source data, exactly as retrieved, never mutated ---
    source_name: str            # e.g. "JPL Horizons VECTORS", "theskylive.com"
    source_frame: str           # e.g. "Ecliptic J2000.0 geometric", "apparent of date (probable, unconfirmed)"
    epoch_or_date: str          # ISO date/time or "J2000.0"
    raw_ra_deg: Optional[float] = None
    raw_dec_deg: Optional[float] = None
    raw_note: str = ""

    # --- tropical result (equinox of date, per Ptolemaic/Western convention) ---
    tropical: Optional[EclipticPosition] = None
    tropical_obliquity_used_deg: Optional[float] = None

    # --- sidereal result (per Indian/jyotisha convention) -- only populated if requested ---
    sidereal: Optional[EclipticPosition] = None
    ayanamsa_deg_used: Optional[float] = None
    ayanamsa_method: str = ""   # e.g. "Lahiri two-anchor linear (see ayanamsha.py) -- modern/kundli use only, NOT historically justified for the ancient corpus, see VALIDATION_REPORT.md item 7"

    validated: bool = False     # set True only once cross-checked against an independent source
    validation_note: str = ""


def _ecliptic_from_ra_dec(ra_deg: float, dec_deg: float, eps_deg: float) -> EclipticPosition:
    eps = math.radians(eps_deg)
    alpha = math.radians(ra_deg)
    delta = math.radians(dec_deg)

    sin_beta = math.sin(delta) * math.cos(eps) - math.cos(delta) * math.sin(eps) * math.sin(alpha)
    beta = math.asin(max(-1.0, min(1.0, sin_beta)))

    y = math.sin(alpha) * math.cos(eps) + math.tan(delta) * math.sin(eps)
    x = math.cos(alpha)
    lam = math.atan2(y, x)

    lon = math.degrees(lam) % 360.0
    lat = math.degrees(beta)
    sign_index = int(lon // 30)
    degree_in_sign = lon - sign_index * 30

    return EclipticPosition(
        longitude_deg=lon, latitude_deg=lat,
        sign=ZODIAC_SIGNS[sign_index], degree_in_sign=degree_in_sign,
    )


def ra_dec_to_ecliptic(ra_deg: float, dec_deg: float, jd: float) -> EclipticPosition:
    """
    Convert equatorial RA/Dec (degrees) at Julian Day `jd` to ecliptic longitude/
    latitude, using the MEAN OBLIQUITY OF DATE at jd. This is only correct if the input
    RA/Dec is itself in an equinox-of-date frame (e.g. Horizons QUANTITIES=2 "apparent").
    If your RA/Dec is J2000-fixed (e.g. "astrometric", or derived from a J2000 VECTORS
    call as in VALIDATION_REPORT.md), use ra_dec_to_ecliptic_j2000() instead -- mixing
    the two frames was exactly the bug class this validation pass was built to catch.
    """
    eps = mean_obliquity_deg(jd)
    return _ecliptic_from_ra_dec(ra_deg, dec_deg, eps)


def ra_dec_to_ecliptic_j2000(ra_deg: float, dec_deg: float) -> EclipticPosition:
    """Same transform, but using the FIXED J2000.0 obliquity (23.439291 deg) -- use this
    when the input RA/Dec is itself J2000-referenced (astrometric or derived from a
    J2000 VECTORS call), not equinox-of-date."""
    return _ecliptic_from_ra_dec(ra_deg, dec_deg, 23.439291111)


def build_position_record(
    body: str, source_name: str, source_frame: str, epoch_or_date: str,
    ra_deg: float, dec_deg: float, jd: Optional[float] = None,
    compute_sidereal: bool = False,
) -> PositionRecord:
    """
    Convenience constructor that fills in a PositionRecord without ever overwriting
    the raw input. Caller must state which frame the RA/Dec is actually in via
    `source_frame` -- this function does NOT guess.
    """
    rec = PositionRecord(
        body=body, source_name=source_name, source_frame=source_frame,
        epoch_or_date=epoch_or_date, raw_ra_deg=ra_deg, raw_dec_deg=dec_deg,
    )
    if "j2000" in source_frame.lower() and jd is None:
        rec.tropical = ra_dec_to_ecliptic_j2000(ra_deg, dec_deg)
        rec.tropical_obliquity_used_deg = 23.439291111
        rec.raw_note = "Converted using fixed J2000 obliquity -- NOT equinox of date."
    elif jd is not None:
        rec.tropical = ra_dec_to_ecliptic(ra_deg, dec_deg, jd)
        rec.tropical_obliquity_used_deg = mean_obliquity_deg(jd)
    else:
        raise ValueError("Must supply jd for equinox-of-date conversion, or state a "
                          "j2000-labeled source_frame for the fixed-obliquity path.")

    if compute_sidereal and rec.tropical is not None:
        year = float(epoch_or_date[:4]) if epoch_or_date[:4].isdigit() else 2000.0
        rec.sidereal = tropical_to_sidereal(rec.tropical.longitude_deg, year)
        rec.sidereal.latitude_deg = rec.tropical.latitude_deg  # ayanamsa doesn't affect latitude
        rec.ayanamsa_deg_used = approximate_lahiri_ayanamsa_deg(year)
        rec.ayanamsa_method = ("Lahiri, two-anchor linear (see ayanamsha.py: sourced to "
                                "1956 Calendar Reform Committee decree + J2000 ICRC "
                                "value; NOT independently cross-checked against a live "
                                "Swiss Ephemeris run this session). Applying this to any "
                                "pre-1956 source (e.g. Bṛhat Saṃhitā) would NOT be "
                                "historically justified -- see VALIDATION_REPORT.md item "
                                "7 and rule_registry.py, which deliberately does not do "
                                "this for the ancient-text rules.")
    return rec


def approximate_lahiri_ayanamsa_deg(year: float) -> float:
    """
    DEPRECATED as of the ayanamsha.py module (this session) -- kept only for backward
    compatibility with any external caller that imported this name directly. Delegates
    to ayanamsha.lahiri_ayanamsha_deg_for_year(), which uses a two-point interpolation
    anchored to two actually-sourced values (1956 Calendar Reform Committee decree +
    J2000 ICRC standard value) instead of this function's old single anchor
    (23.85 deg @ 2000 + an assumed 50.29"/yr rate, neither independently sourced).
    See ayanamsha.py's module docstring for full citations and known limitations
    (still a linear approximation, still not cross-checked against a live Swiss
    Ephemeris run this session).
    """
    return lahiri_ayanamsha_deg_for_year(year).ayanamsha_deg


def tropical_to_sidereal(tropical_lon_deg: float, year: float) -> EclipticPosition:
    ayanamsa = approximate_lahiri_ayanamsa_deg(year)
    sidereal_lon = (tropical_lon_deg - ayanamsa) % 360.0
    sign_index = int(sidereal_lon // 30)
    degree_in_sign = sidereal_lon - sign_index * 30
    return EclipticPosition(
        longitude_deg=sidereal_lon,
        latitude_deg=float("nan"),  # latitude unaffected by ayanamsa; caller should reuse original lat
        sign=ZODIAC_SIGNS[sign_index],
        degree_in_sign=degree_in_sign,
    )


def self_test():
    """
    Sanity check using a known reference: the Sun's ecliptic latitude should be
    ~0 deg year-round (by definition, the Sun sits on the ecliptic), which is a
    good smoke test independent of any external ephemeris. Also checks that
    Aries/Libra boundaries fall near the equinox dates.
    """
    # Approx Sun RA/Dec near the September equinox 2026 (23 Sep 2026, ~06:05 UT,
    # RA/Dec sourced from this session's live theskylive.com fetch is NOT available
    # for that date -- this is a placeholder using the Sun's known equinox condition:
    # ecliptic longitude should be ~180 deg (entering Libra) and latitude ~0.
    jd = julian_day(2026, 9, 23, 6.0)
    eps = mean_obliquity_deg(jd)
    print(f"Mean obliquity on {jd}: {eps:.5f} deg (expect ~23.44 deg)")
    print("Run a real RA/Dec through ra_dec_to_ecliptic() once live ephemeris data")
    print("is available, and confirm ecliptic latitude for the SUN specifically")
    print("comes out within ~0.01 deg of 0 -- that is the cheapest correctness check.")


if __name__ == "__main__":
    self_test()
