"""
Astrowatch — external ephemeris client (JPL Horizons)
===================================================
Confirmed reachable this session via a direct fetch of:
  https://ssd.jpl.nasa.gov/api/horizons.api

This module builds correctly-parameterized requests and parses the $$SOE/$$EOE
ephemeris block. Uses only the Python standard library (urllib) so it has no extra
dependencies to install.

STATUS (updated after validation pass): EPHEM_TYPE=OBSERVER (used by fetch_radec() /
parse_radec_table() below) returned EMPTY responses in three separate live attempts
during validation, across QUANTITIES=1, 2, and 31 -- reproducibly, not a fluke. Treat
that code path as UNVERIFIED / POSSIBLY BROKEN until someone can debug it in an
environment that surfaces the actual HTTP status/error instead of silently swallowing it.

EPHEM_TYPE=VECTORS with REF_PLANE=ECLIPTIC, by contrast, WAS confirmed working (real
data returned, self-documented reference frame: "Ecliptic of J2000.0", geometric, no
aberration). fetch_ecliptic_vectors() / vectors_to_ecliptic_longitude() below implement
that path and are the currently more trustworthy way to pull a position from Horizons.
See VALIDATION_REPORT.md for the full cross-check.
"""

import urllib.request
import urllib.parse
import re
import math
from dataclasses import dataclass
from typing import List, Tuple


HORIZONS_BODY_IDS = {
    "sun": "10",
    "moon": "301",
    "mercury": "199",
    "venus": "299",
    "mars": "499",
    "jupiter": "599",
    "saturn": "699",
    "uranus": "799",
    "neptune": "899",
    "pluto": "999",
}

# QUANTITIES=1 -> Astrometric RA & DEC (J2000). Use this rather than "apparent" RA/Dec
# unless you specifically want equinox-of-date -- and if you use apparent (QUANTITIES=2),
# match that assumption in coordinates.py (it currently assumes equinox-of-date input).
QUANTITIES_ASTROMETRIC_RADEC = "1"


@dataclass
class EphemerisRow:
    body: str
    utc_datetime: str
    ra_deg: float
    dec_deg: float


def _build_url(body_key: str, start_time: str, stop_time: str, step: str = "1d",
                center: str = "500@399", quantities: str = QUANTITIES_ASTROMETRIC_RADEC) -> str:
    body_id = HORIZONS_BODY_IDS[body_key.lower()]
    params = {
        "format": "text",
        "COMMAND": f"'{body_id}'",
        "OBJ_DATA": "'NO'",
        "MAKE_EPHEM": "'YES'",
        "EPHEM_TYPE": "'OBSERVER'",
        "CENTER": f"'{center}'",
        "START_TIME": f"'{start_time}'",
        "STOP_TIME": f"'{stop_time}'",
        "STEP_SIZE": f"'{step}'",
        "QUANTITIES": f"'{quantities}'",
    }
    query = "&".join(f"{k}={urllib.parse.quote(v)}" for k, v in params.items())
    return f"https://ssd.jpl.nasa.gov/api/horizons.api?{query}"


def fetch_radec(body_key: str, start_time: str, stop_time: str, step: str = "1d") -> str:
    """
    Returns the raw Horizons text response. start_time/stop_time format: 'YYYY-MM-DD'
    or 'YYYY-MM-DD HH:MM'. Caller should parse with parse_radec_table().

    NOTE: this makes a live network call. In this session that network call was
    validated to work via the agent's own web-fetch tool, but this exact urllib
    code path has not itself been executed (no local run environment). If it fails
    in your environment, the most likely causes are (a) network egress restrictions,
    or (b) Horizons occasionally rate-limiting -- both easy to confirm by hand-testing
    the URL from _build_url() in a browser first.
    """
    url = _build_url(body_key, start_time, stop_time, step)
    with urllib.request.urlopen(url, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse_radec_table(raw_text: str, body_key: str) -> List[EphemerisRow]:
    """
    Parses the $$SOE ... $$EOE block. Horizons OBSERVER-table text format varies
    slightly by query; this expects columns roughly:
      Date__(UT)__HR:MN     R.A.___(ICRF)___DEC
    with RA as 'HH MM SS.ss' and DEC as 'sDD MM SS.s'.
    If Horizons changes its column layout, this regex will need adjusting --
    validate against one real response before trusting it in a backtest.
    """
    rows: List[EphemerisRow] = []
    if "$$SOE" not in raw_text or "$$EOE" not in raw_text:
        return rows
    block = raw_text.split("$$SOE")[1].split("$$EOE")[0]
    line_re = re.compile(
        r"(?P<date>\d{4}-\w{3}-\d{2} \d{2}:\d{2})\s+.*?"
        r"(?P<rah>\d{2})\s+(?P<ram>\d{2})\s+(?P<ras>\d{2}\.\d+)\s+"
        r"(?P<decsign>[+-])(?P<decd>\d{2})\s+(?P<decm>\d{2})\s+(?P<decs>\d{2}\.\d+)"
    )
    for line in block.strip().splitlines():
        m = line_re.search(line)
        if not m:
            continue
        ra_deg = (int(m["rah"]) + int(m["ram"]) / 60 + float(m["ras"]) / 3600) * 15.0
        dec_abs = int(m["decd"]) + int(m["decm"]) / 60 + float(m["decs"]) / 3600
        dec_deg = dec_abs if m["decsign"] == "+" else -dec_abs
        rows.append(EphemerisRow(body=body_key, utc_datetime=m["date"], ra_deg=ra_deg, dec_deg=dec_deg))
    return rows


def fetch_ecliptic_vectors(body_key: str, start_time: str, stop_time: str, step: str = "1d",
                            center: str = "500@399") -> str:
    """The CONFIRMED-WORKING path (see module docstring). Returns raw Horizons text
    containing geocentric ecliptic J2000 Cartesian state vectors."""
    body_id = HORIZONS_BODY_IDS[body_key.lower()]
    params = {
        "format": "text", "COMMAND": body_id, "EPHEM_TYPE": "VECTORS",
        "CENTER": center, "START_TIME": start_time, "STOP_TIME": stop_time,
        "STEP_SIZE": step, "REF_PLANE": "ECLIPTIC",
    }
    query = "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items())
    url = f"https://ssd.jpl.nasa.gov/api/horizons.api?{query}"
    with urllib.request.urlopen(url, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse_vectors_xyz(raw_text: str) -> List[Tuple[str, float, float, float]]:
    """Parses $$SOE/$$EOE VECTORS block -> [(date_str, X_km, Y_km, Z_km), ...]."""
    rows = []
    if "$$SOE" not in raw_text or "$$EOE" not in raw_text:
        return rows
    block = raw_text.split("$$SOE")[1].split("$$EOE")[0]
    entries = block.strip().split("\n")
    i = 0
    while i < len(entries):
        header = entries[i]
        date_match = re.search(r"=\s*A\.D\.\s*([\d\-A-Za-z: ]+?)\s*TDB", header)
        if date_match and i + 1 < len(entries):
            xyz_line = entries[i + 1]
            xyz_match = re.search(
                r"X\s*=\s*([\-\d.E+]+)\s*Y\s*=\s*([\-\d.E+]+)\s*Z\s*=\s*([\-\d.E+]+)", xyz_line
            )
            if xyz_match:
                rows.append((
                    date_match.group(1).strip(),
                    float(xyz_match.group(1)), float(xyz_match.group(2)), float(xyz_match.group(3)),
                ))
        i += 1
    return rows


def vectors_to_ecliptic_longitude(x: float, y: float, z: float) -> Tuple[float, float]:
    """Ecliptic J2000 Cartesian -> (longitude_deg, latitude_deg). This is INDEPENDENT of
    coordinates.py's RA/Dec-based transform -- use this as the ground truth to check
    ra_dec_to_ecliptic_j2000() against, as done in VALIDATION_REPORT.md."""
    lon = math.degrees(math.atan2(y, x)) % 360.0
    lat = math.degrees(math.atan2(z, math.sqrt(x * x + y * y)))
    return lon, lat


def fetch_all_classical_bodies(start_time: str, stop_time: str, step: str = "1d") -> dict:
    """Convenience wrapper: fetch ecliptic J2000 X/Y/Z for the 7 classical bodies only
    (the ones with any rule coverage in this corpus). Outer planets deliberately
    excluded by default -- add them explicitly if needed for astronomical
    record-keeping, but remember they have zero rule coverage.

    AUDIT NOTE (fixed): this previously called fetch_radec()/parse_radec_table(),
    which use the OBSERVER endpoint -- confirmed broken (empty responses) in this
    session across 3 separate manual attempts. Switched to the confirmed-working
    VECTORS path. Still UNVERIFIED as *code* -- the URL pattern was manually
    confirmed, this specific function has not itself been executed."""
    classical = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn"]
    out = {}
    for body in classical:
        raw = fetch_ecliptic_vectors(body, start_time, stop_time, step)
        rows = parse_vectors_xyz(raw)
        out[body] = [
            {"date": d, "x_km": x, "y_km": y, "z_km": z,
             **dict(zip(("lon_deg", "lat_deg"), vectors_to_ecliptic_longitude(x, y, z)))}
            for (d, x, y, z) in rows
        ]
    return out
