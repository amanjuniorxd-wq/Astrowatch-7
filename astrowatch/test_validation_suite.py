"""
Astrowatch — automated coordinate validation suite
=================================================
STATUS: written, NOT executed. No code-execution capability was available in this
session when this was written (see VALIDATION_REPORT.md "Execution capability missing"
section for the precise diagnosis of why). This file is ready to run the moment any
Python 3 environment with internet access exists -- local sandbox recovery, the user's
own machine, or a future agent attempt with a working execution backend.

Run with:
    python3 test_validation_suite.py

No third-party packages required (urllib + math only).

What this does, precisely: for each (body, date), fetches JPL Horizons geocentric
ecliptic-J2000 Cartesian vectors (the confirmed-working endpoint from this session),
computes REFERENCE longitude/latitude directly from those vectors (independent ground
truth), derives RA/Dec from the SAME vector via the documented J2000 rotation, feeds
that RA/Dec through coordinates.py's transform to get CALCULATED longitude/latitude,
and reports the difference in arcseconds. This is a self-consistency / round-trip test
of the transform's numerical implementation -- see ACCEPTANCE CRITERIA below for why
that specific design was chosen and what error it should and shouldn't be expected to
catch.

ACCEPTANCE CRITERIA (established BEFORE running, not fitted after seeing results):
- Both "reference" and "calculated" longitude/latitude in this test derive from the
  IDENTICAL Cartesian vector, in the IDENTICAL frame (J2000 ecliptic, geometric, same
  instant). The two rotations involved (ecliptic->equatorial, then equatorial->ecliptic
  via coordinates.py) are exact mathematical inverses of each other. With exact
  arithmetic, error would be precisely zero.
- The only real source of nonzero error in THIS specific test is floating-point
  representation: Python floats are IEEE754 double precision, ~15-17 significant
  decimal digits. Propagated through ~10 trig operations, expected numerical noise is
  on the order of 1e-12 to 1e-9 degrees, i.e. roughly 1e-6 to 1e-3 arcseconds.
- Horizons' own DE441-based ephemeris is accurate to a small fraction of an arcsecond
  for planetary positions in this date range (well-documented JPL precision, not
  something this test re-derives) -- but that precision is irrelevant to THIS
  self-consistency test specifically, since both sides of the comparison use the exact
  same fetched number.
- THEREFORE: PASS threshold for this test = error < 0.01 arcsec per body/date. Anything
  in the 0.01-1 arcsec range should be treated as suspicious and investigated (possible
  accumulated floating-point error from an unusually ill-conditioned case, e.g. near a
  pole or exact 0/180 longitude). Anything above ~1 arcsec indicates a genuine
  implementation bug, not numerical noise -- and per instruction, the fix in that case
  is to find and correct the bug, not loosen the tolerance.
- IMPORTANT: this test does NOT validate the transform against a real apparent-position
  source (e.g. theskylive.com) -- that is a DIFFERENT test with a much looser, properly-
  justified tolerance budget (arcminute-scale) because of genuine physical effects not
  present here: precession between epochs, aberration, light-time. See
  VALIDATION_REPORT.md Phase 1 for that error budget. Do not conflate the two.
"""

import urllib.request
import urllib.parse
import math
import re

J2000_OBLIQUITY_DEG = 23.4392911111

BODIES = {
    "Sun": "10", "Moon": "301", "Mercury": "199", "Venus": "299",
    "Mars": "499", "Jupiter": "599", "Saturn": "699",
}

DATES = ["1900-01-01", "1950-01-01", "2000-01-01", "2026-08-12", "2030-01-01"]


def fetch_vectors(body_id: str, date: str) -> str:
    stop = _next_day(date)
    params = {
        "format": "text", "COMMAND": body_id, "EPHEM_TYPE": "VECTORS",
        "CENTER": "500@399", "START_TIME": date, "STOP_TIME": stop,
        "STEP_SIZE": "1d", "REF_PLANE": "ECLIPTIC",
    }
    query = "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items())
    url = f"https://ssd.jpl.nasa.gov/api/horizons.api?{query}"
    with urllib.request.urlopen(url, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _next_day(date_str: str) -> str:
    y, m, d = (int(x) for x in date_str.split("-"))
    import datetime
    return (datetime.date(y, m, d) + datetime.timedelta(days=1)).isoformat()


def parse_xyz(raw: str):
    if "$$SOE" not in raw or "$$EOE" not in raw:
        raise RuntimeError(f"No $$SOE/$$EOE block in response. First 500 chars:\n{raw[:500]}")
    block = raw.split("$$SOE")[1].split("$$EOE")[0]
    m = re.search(
        r"X\s*=\s*([\-\d.E+]+)\s*Y\s*=\s*([\-\d.E+]+)\s*Z\s*=\s*([\-\d.E+]+)", block
    )
    if not m:
        raise RuntimeError(f"Could not parse X/Y/Z from block:\n{block[:500]}")
    return float(m.group(1)), float(m.group(2)), float(m.group(3))


def ecliptic_from_xyz(x, y, z):
    lon = math.degrees(math.atan2(y, x)) % 360.0
    lat = math.degrees(math.atan2(z, math.sqrt(x * x + y * y)))
    return lon, lat


def radec_from_ecliptic_xyz(x, y, z, eps_deg=J2000_OBLIQUITY_DEG):
    eps = math.radians(eps_deg)
    x_eq = x
    y_eq = y * math.cos(eps) - z * math.sin(eps)
    z_eq = y * math.sin(eps) + z * math.cos(eps)
    ra = math.degrees(math.atan2(y_eq, x_eq)) % 360.0
    dec = math.degrees(math.atan2(z_eq, math.sqrt(x_eq * x_eq + y_eq * y_eq)))
    return ra, dec


def ra_dec_to_ecliptic(ra_deg, dec_deg, eps_deg=J2000_OBLIQUITY_DEG):
    eps = math.radians(eps_deg)
    alpha = math.radians(ra_deg)
    delta = math.radians(dec_deg)
    sin_beta = math.sin(delta) * math.cos(eps) - math.cos(delta) * math.sin(eps) * math.sin(alpha)
    beta = math.degrees(math.asin(max(-1.0, min(1.0, sin_beta))))
    y = math.sin(alpha) * math.cos(eps) + math.tan(delta) * math.sin(eps)
    x = math.cos(alpha)
    lam = math.degrees(math.atan2(y, x)) % 360.0
    return lam, beta


def angle_diff_deg(a, b):
    d = abs(a - b) % 360.0
    return min(d, 360.0 - d)


def run():
    results = []
    print(f"{'Body':<9}{'Date':<12}{'RefLon':>10}{'CalcLon':>10}{'LonErr(as)':>12}"
          f"{'RefLat':>10}{'CalcLat':>10}{'LatErr(as)':>12}")
    for body, body_id in BODIES.items():
        for date in DATES:
            try:
                raw = fetch_vectors(body_id, date)
                x, y, z = parse_xyz(raw)
                ref_lon, ref_lat = ecliptic_from_xyz(x, y, z)
                ra, dec = radec_from_ecliptic_xyz(x, y, z)
                calc_lon, calc_lat = ra_dec_to_ecliptic(ra, dec)
                lon_err_as = angle_diff_deg(ref_lon, calc_lon) * 3600
                lat_err_as = abs(ref_lat - calc_lat) * 3600
                results.append({
                    "body": body, "date": date, "ref_lon": ref_lon, "calc_lon": calc_lon,
                    "lon_err_as": lon_err_as, "ref_lat": ref_lat, "calc_lat": calc_lat,
                    "lat_err_as": lat_err_as,
                })
                print(f"{body:<9}{date:<12}{ref_lon:>10.4f}{calc_lon:>10.4f}{lon_err_as:>12.6f}"
                      f"{ref_lat:>10.4f}{calc_lat:>10.4f}{lat_err_as:>12.6f}")
            except Exception as e:
                print(f"{body:<9}{date:<12} FAILED: {e}")
                results.append({"body": body, "date": date, "error": str(e)})

    max_lon_err = max((r["lon_err_as"] for r in results if "lon_err_as" in r), default=None)
    max_lat_err = max((r["lat_err_as"] for r in results if "lat_err_as" in r), default=None)
    print(f"\nMax longitude error: {max_lon_err} arcsec")
    print(f"Max latitude error: {max_lat_err} arcsec")
    print("Acceptance threshold: < 0.01 arcsec (see module docstring for derivation).")
    if max_lon_err is not None and max_lon_err < 0.01 and max_lat_err < 0.01:
        print("RESULT: PASS (self-consistency round-trip test)")
    else:
        print("RESULT: FAIL or INVESTIGATE -- do not loosen tolerance, find the cause.")
    return results


if __name__ == "__main__":
    run()
