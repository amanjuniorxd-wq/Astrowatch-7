"""
Astrowatch — kundli (Vedic natal-style chart) construction.
================================================================
REWRITTEN this pass to replace an approximate/inconsistent astronomical layer with a
validated, file-based Swiss Ephemeris pipeline. See ARCHITECTURE_SE_MIGRATION.md at
the repo root for the full audit/before-after report. Summary of what changed and why:

1. EPHEMERIS DATA FILES ARE NOW REAL, NOT MOSHIER-APPROXIMATED. `pyswisseph` was
   already an installed dependency, but no module in this project ever called
   `swe.set_ephe_path()`, so every `swe.calc_ut()` call silently ran in Swiss
   Ephemeris's built-in "Moshier" semi-analytic fallback mode (no external files,
   ~1 arcsec-class precision) rather than the full JPL-derived .se1 file-based mode
   sub-milliarcsecond-class precision this library is actually known for. This
   session's sandbox cannot reach astro.com/Dropbox/GitHub-codeload (all return
   HTTP 403 from the outbound proxy — confirmed via direct curl tests) to download
   Astrodienst's own .se1 distribution. However, the open-source `flatlib` package on
   PyPI (reachable — pypi.org/files.pythonhosted.org are allowlisted) bundles the
   real Swiss Ephemeris main-body files (sepl/semo/seas for three 600-year blocks,
   covering roughly 1200-2999 AD) as installed package data. Those files were
   extracted and copied into astrowatch/ephemeris/ (see that directory's own note).
   `swe.set_ephe_path()` now points there, and every calc call in this module was
   verified this session to report `retflag & swe.FLG_SWIEPH` set and
   `retflag & swe.FLG_MOSEPH` NOT set — i.e. genuinely file-based, not Moshier.

2. SIDEREAL POSITIONS ARE NOW COMPUTED DIRECTLY VIA `SEFLG_SIDEREAL`, NOT BY
   MANUALLY SUBTRACTING A SEPARATELY-FETCHED AYANAMSHA VALUE. The previous version
   computed a TROPICAL position via `swe.calc_ut(..., FLG_TRUEPOS|FLG_NOABERR|
   FLG_NOGDEFL|FLG_J2000)` and then subtracted an ayanamsha value obtained from
   ayanamsha.py (a live-HTTP-query-with-linear-fallback module, whose live path is
   blocked in this sandbox, so it silently always used its ~14-64-arcsec-error
   linear fallback). This session, cross-checking BOTH the old flag combination and
   a direct `SEFLG_SIDEREAL` call against a fresh, real, live Swiss Ephemeris
   reference fetched from astro.com's swetest.cgi this session (via the agent's
   web-fetch tool, which — unlike raw outbound curl — IS reachable) found:
     - Direct `FLG_SWIEPH | FLG_SIDEREAL` (SIDM_LAHIRI): matched the live reference
       to within 0.001-0.033 arcsec across Sun/Moon/Mercury/Venus/Mars/Jupiter/Saturn
       at a J2000.0 test instant (see ARCHITECTURE_SE_MIGRATION.md for the full
       numeric table). This is now what this module uses.
     - The OLD flag combination (`TRUEPOS|NOABERR|NOGDEFL`, i.e. a geometric,
       no-light-time-correction position — not what "apparent position" astrology
       conventionally means) was off from the live reference by +20.84 arcsec for
       the Sun at the same instant — the dominant, previously mis-attributed source
       of this project's earlier ~14-21 arcsec ayanamsha/position disagreements.
   ayanamsha.py's live-query/linear-fallback design is no longer used by this
   module. It remains in the repo, now clearly out of the kundli-chart critical
   path (see that file's own updated docstring), since other, unrelated parts of
   the project may still reference it.

3. NO SILENT FALLBACK. If astrowatch/ephemeris/ is missing its required .se1 files
   (or SWEPH_EPHE_PATH points somewhere without them), `_require_ephemeris_files()`
   raises `EphemerisDataUnavailable` at first use — this module will NOT silently
   compute an approximate chart instead.

4. RAHU/KETU NODE CONVENTION: MEAN NODE (`swe.MEAN_NODE`), unchanged from before —
   documented explicitly here (not silently mixed with true-node) per this session's
   audit requirement. Mean node is the convention traditionally used for Vimshottari
   Dasha timing calculations (the dominant use of Rahu/Ketu elsewhere in this
   project); true-node is a legitimate alternative some software uses instead, but
   is NOT used here. See ARCHITECTURE_SE_MIGRATION.md item 4 for the tradeoff note.

5. INTERFACE: `compute_kundli(jd_ut, latitude, longitude)` signature is UNCHANGED
   (the `allow_ayanamsha_fallback` kwarg is still accepted for backward compatibility
   with existing callers but is now a no-op — there is no fallback path to allow or
   disallow anymore; see its own docstring). All ~9 existing callers across
   kundli_mass/*.py continue to work unmodified.

GRAHAS: the classical 9 (Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu).
Rahu/Ketu are the Moon's mean lunar nodes (Rahu = ascending/mean node; Ketu = Rahu +
180 deg exactly, by definition — not independently computed).
"""

import os
from dataclasses import dataclass, field
from typing import Dict

import threading

import swisseph as swe

import rashi_nakshatra as rn

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_EPHEMERIS_PATH = os.path.join(HERE, "ephemeris")

REQUIRED_EPHEMERIS_FILES = ("sepl_18.se1", "semo_18.se1", "seas_18.se1")


class EphemerisDataUnavailable(Exception):
    """Raised when the configured Swiss Ephemeris data directory does not contain
    the required .se1 files. This module never catches this exception internally and
    falls back to an approximation — callers see it directly, per this session's
    explicit "no silent fallback" requirement."""


def _require_ephemeris_files(ephe_path: str) -> None:
    missing = [f for f in REQUIRED_EPHEMERIS_FILES if not os.path.isfile(os.path.join(ephe_path, f))]
    if missing:
        raise EphemerisDataUnavailable(
            f"Swiss Ephemeris data files not found in {ephe_path!r}: missing {missing}. "
            f"Set the SWEPH_EPHE_PATH environment variable to a directory containing "
            f"sepl_*.se1 / semo_*.se1 / seas_*.se1, or restore astrowatch/ephemeris/. "
            f"This module does not compute approximate positions as a fallback."
        )


_EPHE_PATH = os.environ.get("SWEPH_EPHE_PATH", DEFAULT_EPHEMERIS_PATH)
_require_ephemeris_files(_EPHE_PATH)
swe.set_ephe_path(_EPHE_PATH)
swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)

# THREAD-SAFETY FIX (added for the production/online API, which serves each HTTP
# request on its own worker thread via ThreadingHTTPServer): swe.set_ephe_path()/
# set_sid_mode() above run once at module-import time in whichever thread first
# imports this module (normally the main thread). Confirmed by a direct test this
# session: a *different* Python thread that never itself called set_ephe_path()
# can have swe.calc_ut() silently drop into Moshier-approximation mode even though
# the main thread is correctly configured for file-based mode -- pyswisseph's
# ephemeris-file state is apparently not reliably shared across threads. This is
# NOT a change to the calculation methodology or accuracy; it only makes sure
# every thread that calls compute_kundli() re-asserts the identical file-based
# Swiss Ephemeris configuration before its first calc_ut() call, once, cheaply.
_thread_local = threading.local()


def _ensure_thread_ephemeris_configured() -> None:
    if getattr(_thread_local, "configured", False):
        return
    swe.set_ephe_path(_EPHE_PATH)
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    _thread_local.configured = True

GRAHA_BODY_IDS = {
    "sun": swe.SUN, "moon": swe.MOON, "mercury": swe.MERCURY, "venus": swe.VENUS,
    "mars": swe.MARS, "jupiter": swe.JUPITER, "saturn": swe.SATURN,
}
NODE_BODY_ID = swe.MEAN_NODE  # Rahu -- mean node convention, see module docstring item 4.

# Validated this session (see module docstring item 2): plain FLG_SWIEPH (+FLG_SIDEREAL
# for the sidereal call) matches live Swiss Ephemeris to within 0.001-0.033 arcsec.
# Deliberately NOT using FLG_TRUEPOS|FLG_NOABERR|FLG_NOGDEFL|FLG_J2000 (see docstring).
_CALC_FLAGS_TROPICAL = swe.FLG_SWIEPH
_CALC_FLAGS_SIDEREAL = swe.FLG_SWIEPH | swe.FLG_SIDEREAL


@dataclass
class GrahaPlacement:
    graha: str
    tropical_lon_deg: float
    sidereal_lon_deg: float
    latitude_deg: float
    distance_au: float
    speed_lon_deg_per_day: float
    retrograde: bool
    rashi: rn.RashiPlacement
    nakshatra: rn.NakshatraPlacement
    house: int   # 1-12, whole-sign from the Ascendant


@dataclass
class KundliChart:
    jd_ut: float
    latitude: float
    longitude: float
    ayanamsha_deg: float
    ayanamsha_source: str
    ascendant_tropical_deg: float
    ascendant_sidereal_deg: float
    ascendant_rashi: rn.RashiPlacement
    ascendant_nakshatra: rn.NakshatraPlacement
    grahas: Dict[str, GrahaPlacement] = field(default_factory=dict)
    house_system: str = "whole_sign"
    engine: str = "Swiss Ephemeris (pyswisseph, file-based)"
    node_convention: str = "mean_node"


def _house_number(graha_rashi_index: int, asc_rashi_index: int) -> int:
    return ((graha_rashi_index - asc_rashi_index) % 12) + 1


def _placement_from_calc(name: str, body_id: int, jd_ut: float, asc_rashi_index: int) -> GrahaPlacement:
    trop_result, trop_flag = swe.calc_ut(jd_ut, body_id, _CALC_FLAGS_TROPICAL)
    sid_result, sid_flag = swe.calc_ut(jd_ut, body_id, _CALC_FLAGS_SIDEREAL)
    if trop_flag & swe.FLG_MOSEPH or sid_flag & swe.FLG_MOSEPH:
        raise EphemerisDataUnavailable(
            f"swe.calc_ut() for {name} fell back to Moshier approximation mode "
            f"(FLG_MOSEPH set) instead of file-based FLG_SWIEPH -- ephemeris data "
            f"files are misconfigured or missing. Refusing to return an approximate "
            f"position silently."
        )
    tropical_lon = trop_result[0] % 360.0
    sidereal_lon = sid_result[0] % 360.0
    rashi = rn.rashi_for_longitude(sidereal_lon)
    nakshatra = rn.nakshatra_for_longitude(sidereal_lon)
    return GrahaPlacement(
        graha=name, tropical_lon_deg=tropical_lon, sidereal_lon_deg=sidereal_lon,
        latitude_deg=trop_result[1], distance_au=trop_result[2],
        speed_lon_deg_per_day=trop_result[3], retrograde=trop_result[3] < 0.0,
        rashi=rashi, nakshatra=nakshatra,
        house=_house_number(rashi.rashi_index, asc_rashi_index),
    )


def compute_kundli(
    jd_ut: float, latitude: float, longitude: float,
    allow_ayanamsha_fallback: bool = True,  # kept for backward compatibility; no-op, see docstring item 5
) -> KundliChart:
    """
    latitude/longitude: REAL geographic coordinates of the event location (degrees,
    north/east positive) — required for the Ascendant/house calculation. Never pass a
    fabricated or approximate location for a house-sensitive chart; if the event's
    location isn't known precisely, don't call this function for it (see
    scripts/build_kundli_correlations.py's eligibility filter, which enforces this at
    the dataset level rather than leaving it to each caller).
    """
    _ensure_thread_ephemeris_configured()
    _, ascmc = swe.houses_ex(jd_ut, latitude, longitude, b"W", swe.FLG_SIDEREAL)
    asc_sidereal = ascmc[0] % 360.0
    _, ascmc_trop = swe.houses_ex(jd_ut, latitude, longitude, b"W")
    asc_tropical = ascmc_trop[0] % 360.0
    ayanamsha_deg = (asc_tropical - asc_sidereal) % 360.0

    asc_rashi = rn.rashi_for_longitude(asc_sidereal)
    asc_nakshatra = rn.nakshatra_for_longitude(asc_sidereal)

    grahas: Dict[str, GrahaPlacement] = {}
    for name, body_id in GRAHA_BODY_IDS.items():
        grahas[name] = _placement_from_calc(name, body_id, jd_ut, asc_rashi.rashi_index)

    # Rahu (mean node) + Ketu (exactly opposite, by definition -- not independently
    # computed, per this module's own docstring).
    rahu = _placement_from_calc("rahu", NODE_BODY_ID, jd_ut, asc_rashi.rashi_index)
    grahas["rahu"] = rahu
    ketu_tropical = (rahu.tropical_lon_deg + 180.0) % 360.0
    ketu_sidereal = (rahu.sidereal_lon_deg + 180.0) % 360.0
    ketu_rashi = rn.rashi_for_longitude(ketu_sidereal)
    ketu_nakshatra = rn.nakshatra_for_longitude(ketu_sidereal)
    grahas["ketu"] = GrahaPlacement(
        graha="ketu", tropical_lon_deg=ketu_tropical, sidereal_lon_deg=ketu_sidereal,
        latitude_deg=-rahu.latitude_deg, distance_au=rahu.distance_au,
        speed_lon_deg_per_day=rahu.speed_lon_deg_per_day, retrograde=rahu.retrograde,
        rashi=ketu_rashi, nakshatra=ketu_nakshatra,
        house=_house_number(ketu_rashi.rashi_index, asc_rashi.rashi_index),
    )

    return KundliChart(
        jd_ut=jd_ut, latitude=latitude, longitude=longitude,
        ayanamsha_deg=ayanamsha_deg, ayanamsha_source="swisseph_file_based_sidereal",
        ascendant_tropical_deg=asc_tropical, ascendant_sidereal_deg=asc_sidereal,
        ascendant_rashi=asc_rashi, ascendant_nakshatra=asc_nakshatra,
        grahas=grahas,
    )
