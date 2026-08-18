"""
Astrowatch backtest — real, local, non-fabricated ephemeris data source.

WHY THIS FILE EXISTS (read before touching anything else in this package)
---------------------------------------------------------------------------
forecast.get_astronomical_snapshot(jd_ut, date_label, tropical_longitudes_deg) is,
BY ITS OWN DOCSTRING, "a thin wrapper -- this file does NOT fetch ephemeris data
itself. Callers must supply real tropical longitudes obtained from
ephemeris_client.py (JPL Horizons) or an equivalent real source." That is an
explicit, pre-existing extension point in the UNMODIFIED forecast.py -- this module
fills exactly that documented contract for the backtest, without editing
forecast.py, ephemeris_client.py, ayanamsha.py, coordinates.py, panchang.py, or
rashi_nakshatra.py in any way.

ephemeris_client.py's own JPL Horizons path is network-blocked in this sandbox (the
same proxy-allowlist constraint documented throughout this project -- see
ASTRONOMY_VALIDATION_REPORT.md Phase 11). Running ~140 events x up to 7 planets x up
to 7 time-samples each would also require several hundred individual live network
round-trips even if reachable. pyswisseph (already installed and confirmed working
across the full historical date range this project needs, including 79 CE) is used
instead: it is the SAME underlying Swiss Ephemeris library that astro.com's
swetest.cgi (ayanamsha.py's own live-query primary path) exposes over HTTP -- a real,
deterministic, locally-computed source, not a fabrication.

HONEST PRECISION CAVEAT (do not omit from any report using this module's output):
this sandbox has no Swiss Ephemeris .se1 data files installed (same absence that
affects ayanamsha.py's own cross-check work), so pyswisseph silently falls back to
its bundled Moshier semi-analytic approximation for every calculation (confirmed
below via the FLG_MOSEPH bit on every returned retflag, both for a modern date and
for 79 CE). The earlier phase of this project measured up to ~17.5 arcsec disagreement
between Moshier-mode ayanamsha values and live Swiss-Ephemeris-file reference values
in the 1900-2050 range; degree-level planetary longitude error from Moshier mode is
generally much smaller than that (arcsecond-to-sub-arcminute for the inner planets
across recorded history), but no live comparison has been possible in this sandbox to
directly confirm the exact magnitude for arbitrary ancient dates. Every prediction
row this module contributes to records ephemeris_precision_flag='MOSEPH' so this is
traceable per-case, not asserted once and forgotten.

FRAME: uses FLG_J2000 (fixed J2000.0 equinox, no precession-of-date correction) to
match ephemeris_client.py's own documented JPL Horizons convention (REF_PLANE=ECLIPTIC,
"Ecliptic of J2000.0") -- see forecast.AstronomicalSnapshot's own frame_caveat, which
already documents this convention for the whole project; this module does not
introduce a new convention. Uses FLG_TRUEPOS + FLG_NOABERR + FLG_NOGDEFL to request
geometric (no light-time/aberration/gravitational-deflection correction) positions --
matching JPL Horizons VECTORS output's own documented "geometric" behavior
(ephemeris_client.py's fetch_ecliptic_vectors() docstring).
"""

from dataclasses import dataclass
from typing import Dict, Tuple

import swisseph as swe

# ---------------------------------------------------------------------------------
# Local ephemeris FILE configuration (Phase 5 of the "VALIDATION HARDENING BEFORE
# BT-002" pass). Investigated during this pass, with real (not assumed) evidence:
#
#   1. `pip show pyswisseph` confirms 2.10.3.2 installed; `find / -iname "*.se1"`
#      finds NONE anywhere on this sandbox's filesystem.
#   2. `pip download swisseph-data` (a hypothetical bundled-data package): no such
#      package exists on PyPI.
#   3. astro.com's own download page (fetched successfully via this session's
#      broader-reach web-fetch tool, confirming the page itself IS reachable) states
#      the real files are hosted at github.com/aloistr/swisseph/tree/master/ephe or
#      a Dropbox folder (11-29 GB for full asteroid coverage; the core planetary
#      files needed here are much smaller, but still real binary astronomical data
#      files, not something to approximate).
#   4. `git clone https://github.com/aloistr/swisseph.git` from this sandbox's own
#      shell: connection disconnects mid-transfer (same proxy-allowlist class of
#      failure documented throughout this project for non-github.com/pypi.org
#      hosts -- large GitHub LFS/blob transfers appear to hit the same wall).
#   5. `raw.githubusercontent.com` (needed for any direct file fetch): unreachable
#      via both this sandbox's shell AND the broader-reach web-fetch tool (empty
#      response) -- consistent with this project's standing, previously-documented
#      network constraint (github.com's HTML pages are reachable; raw content and
#      api.github.com are not).
#   6. GitHub's own repository file browser is JavaScript-rendered and returns no
#      usable content to a non-JS-executing fetch.
#
# CONCLUSION: real .se1 Swiss Ephemeris data files are NOT obtainable in this
# specific sandboxed environment through any tool available to this session. They
# are NOT fabricated, approximated, or synthesized as a substitute -- doing so would
# make the Moshier-vs-file-based precision distinction meaningless and dishonest.
#
# CONFIGURATION MECHANISM (for environments where real files ARE available, e.g. a
# developer's own machine): set the ASTROWATCH_EPHE_PATH environment variable to a
# directory containing real .se1 files (obtained legitimately from astro.com/GitHub/
# Dropbox as above), or place them in ./ephe/ relative to this file. If found,
# configure_ephemeris_path() below points pyswisseph at them via swe.set_ephe_path()
# and every subsequent swe.calc_ut() call automatically uses full file-based
# precision (FLG_SWIEPH without silently falling back to FLG_MOSEPH) instead of
# Moshier -- no other code in this project needs to change. If not found, pyswisseph
# continues to fall back to Moshier exactly as it does today, and
# ephemeris_precision_flag continues to honestly report 'MOSEPH' per-prediction.
# ---------------------------------------------------------------------------------

import os as _os

ASTROWATCH_EPHE_PATH_ENV_VAR = "ASTROWATCH_EPHE_PATH"
_DEFAULT_LOCAL_EPHE_DIR = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "ephe")


def configure_ephemeris_path() -> dict:
    """Idempotent. Returns a dict describing what was found/configured -- callers
    (scripts, tests) should log this once at startup so it's clear which precision
    mode a given run actually used, rather than discovering it implicitly per-call
    via ephemeris_precision_flag alone."""
    candidate = _os.environ.get(ASTROWATCH_EPHE_PATH_ENV_VAR)
    source = "env:" + ASTROWATCH_EPHE_PATH_ENV_VAR
    if not candidate:
        candidate = _DEFAULT_LOCAL_EPHE_DIR
        source = "default_local_dir"

    if not candidate or not _os.path.isdir(candidate):
        return {
            "configured": False, "path_checked": candidate, "source": source,
            "se1_files_found": 0,
            "reason": "no directory found -- see module docstring for how to obtain "
                       "real files and where this project looked for them in this "
                       "sandbox (none were obtainable here)",
        }
    se1_files = [f for f in _os.listdir(candidate) if f.lower().endswith(".se1")]
    if not se1_files:
        return {
            "configured": False, "path_checked": candidate, "source": source,
            "se1_files_found": 0, "reason": "directory exists but contains no .se1 files",
        }
    swe.set_ephe_path(candidate)
    return {
        "configured": True, "path_checked": candidate, "source": source,
        "se1_files_found": len(se1_files), "files": sorted(se1_files),
    }


CLASSICAL_BODY_IDS = {
    "sun": swe.SUN,
    "moon": swe.MOON,
    "mercury": swe.MERCURY,
    "venus": swe.VENUS,
    "mars": swe.MARS,
    "jupiter": swe.JUPITER,
    "saturn": swe.SATURN,
}

_CALC_FLAGS = (
    swe.FLG_SWIEPH | swe.FLG_J2000 | swe.FLG_TRUEPOS | swe.FLG_NOABERR | swe.FLG_NOGDEFL
)


class EphemerisComputationError(Exception):
    """Raised if pyswisseph itself reports an error (negative return flag)."""


@dataclass
class EphemerisSnapshot:
    jd_ut: float
    tropical_longitudes_deg: Dict[str, float]
    precision_flag: str          # 'SWIEPH' | 'MOSEPH'
    per_body_retflag: Dict[str, int]


def compute_tropical_longitudes(jd_ut: float) -> EphemerisSnapshot:
    """Real, local, deterministic computation -- the 7 classical bodies only (the
    ones with any rule coverage in this corpus, matching
    ephemeris_client.fetch_all_classical_bodies()'s own scope decision)."""
    longitudes: Dict[str, float] = {}
    retflags: Dict[str, int] = {}
    any_moseph = False
    for body, body_id in CLASSICAL_BODY_IDS.items():
        result, retflag = swe.calc_ut(jd_ut, body_id, _CALC_FLAGS)
        if retflag < 0:
            raise EphemerisComputationError(
                f"swe.calc_ut failed for body={body!r} at jd_ut={jd_ut}: retflag={retflag}"
            )
        longitudes[body] = result[0] % 360.0
        retflags[body] = retflag
        if retflag & swe.FLG_MOSEPH:
            any_moseph = True
    return EphemerisSnapshot(
        jd_ut=jd_ut,
        tropical_longitudes_deg=longitudes,
        precision_flag="MOSEPH" if any_moseph else "SWIEPH",
        per_body_retflag=retflags,
    )


# ---------------------------------------------------------------------------------
# Extended output (added during the "VALIDATION HARDENING BEFORE BT-002" pass) --
# compute_tropical_longitudes() above is UNCHANGED (still used exactly as BT-001 used
# it, for full reproducibility of that frozen experiment). The functions below are
# ADDITIVE: they expose ecliptic LATITUDE (needed for Ch. XVIII lunar-pass detection,
# see aspects.classify_lunar_pass) and the Moon's node longitude (needed for eclipse
# detection, see aspects.check_for_eclipse), neither of which BT-001's predictor used.
# ---------------------------------------------------------------------------------

NODE_BODY_IDS = {
    "mean_node": swe.MEAN_NODE,
    "true_node": swe.TRUE_NODE,
}


@dataclass
class FullPositionSnapshot:
    jd_ut: float
    tropical_longitudes_deg: Dict[str, float]
    tropical_latitudes_deg: Dict[str, float]
    node_longitudes_deg: Dict[str, float]   # 'mean_node', 'true_node'
    precision_flag: str
    per_body_retflag: Dict[str, int]


def compute_full_positions(jd_ut: float) -> FullPositionSnapshot:
    """Like compute_tropical_longitudes(), but also returns ecliptic latitude per
    body and the lunar node longitude(s). Same flags, same precision caveats (see
    module docstring) -- this is not a different methodology, just more of the same
    already-computed pyswisseph output (result[1] is latitude; calc_ut already
    returns it, compute_tropical_longitudes() simply discarded it)."""
    longitudes: Dict[str, float] = {}
    latitudes: Dict[str, float] = {}
    retflags: Dict[str, int] = {}
    any_moseph = False

    for body, body_id in CLASSICAL_BODY_IDS.items():
        result, retflag = swe.calc_ut(jd_ut, body_id, _CALC_FLAGS)
        if retflag < 0:
            raise EphemerisComputationError(
                f"swe.calc_ut failed for body={body!r} at jd_ut={jd_ut}: retflag={retflag}"
            )
        longitudes[body] = result[0] % 360.0
        latitudes[body] = result[1]
        retflags[body] = retflag
        if retflag & swe.FLG_MOSEPH:
            any_moseph = True

    node_longitudes: Dict[str, float] = {}
    for name, node_id in NODE_BODY_IDS.items():
        result, retflag = swe.calc_ut(jd_ut, node_id, _CALC_FLAGS)
        if retflag < 0:
            raise EphemerisComputationError(
                f"swe.calc_ut failed for node={name!r} at jd_ut={jd_ut}: retflag={retflag}"
            )
        node_longitudes[name] = result[0] % 360.0
        retflags[name] = retflag
        if retflag & swe.FLG_MOSEPH:
            any_moseph = True

    return FullPositionSnapshot(
        jd_ut=jd_ut, tropical_longitudes_deg=longitudes, tropical_latitudes_deg=latitudes,
        node_longitudes_deg=node_longitudes,
        precision_flag="MOSEPH" if any_moseph else "SWIEPH", per_body_retflag=retflags,
    )


def self_test() -> Tuple[bool, str]:
    """Sanity check this module still produces real, plausible output. Not a
    correctness proof (no live reference is reachable in this sandbox) -- just a
    guard against silent breakage (e.g. a future pyswisseph upgrade changing the
    flag/return contract)."""
    import coordinates  # existing, unmodified module -- date-independent utility
    jd = coordinates.julian_day(2004, 12, 26, 0.9666666)
    snap = compute_tropical_longitudes(jd)
    if set(snap.tropical_longitudes_deg) != set(CLASSICAL_BODY_IDS):
        return False, "missing bodies in output"
    for body, lon in snap.tropical_longitudes_deg.items():
        if not (0.0 <= lon < 360.0):
            return False, f"{body} longitude out of range: {lon}"
    return True, f"OK, precision_flag={snap.precision_flag}"


if __name__ == "__main__":
    ok, msg = self_test()
    print(("PASS" if ok else "FAIL") + ": " + msg)
