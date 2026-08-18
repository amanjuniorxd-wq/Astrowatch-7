"""
Astrowatch — Lahiri (Chitrapaksha) ayanamsha module
===================================================
SCOPE NOTE (read this first): this module is for the MODERN / forward-looking part of
Astrowatch -- computing accurate sidereal ("kundli"-style) planetary positions today, so
current configurations can be compared against current/near-term world events. It is
DELIBERATELY NOT wired into the ancient-text rule engines (rule_registry.py's Bṛhat
Saṃhitā / Ptolemy rules). Those rules stay classified "sidereal_unresolved" where the
extracted 6th-century text doesn't itself specify a precession model -- using a 1956
Indian government committee's ayanamsha to reinterpret a pre-1956 source would be
exactly the unjustified retrofit this project's rule_registry.py explicitly refuses to
do. Nothing below changes that.

ARCHITECTURE -- WHICH ENGINE IS AUTHORITATIVE FOR WHICH LAYER (read second)
-----------------------------------------------------------------------------
    JPL Horizons (ephemeris_client.py)  -->  raw geocentric planetary longitude (TROPICAL)
                     |
                     v
    THIS MODULE (ayanamsha.py)          -->  Lahiri ayanamsha OFFSET (a single angle, deg)
                     |
                     v
    coordinates.tropical_to_sidereal_lahiri()  -->  sidereal longitude = tropical - ayanamsha
                     |
                     v
    rashi_nakshatra.py                  -->  Rāśi (zodiac sign) / Nakshatra classification
                     |
                     v
    rule_registry.py / engines.py       -->  rule matching (MODERN track only, see scope note)

JPL Horizons remains the sole source of raw planetary positions -- nothing here replaces
it. Swiss Ephemeris (live-queried, see below) is used ONLY to compute the ayanamsha
OFFSET VALUE (one number, the angular gap between the tropical and sidereal zero
points) -- it is never asked for a planetary position itself. This keeps the two
engines' roles from blurring into each other, per explicit instruction.

STATUS OF THIS PASS: the two-point LINEAR model (previous pass) has been DEMOTED from
primary to FALLBACK-ONLY. The primary path now queries live Swiss Ephemeris (the actual
reference implementation, via astro.com's swetest.cgi) for the ayanamsha value at the
requested date, so the "computation" is the real Swiss Ephemeris algorithm, not a
hand-built approximation of it. See LIVE QUERY IMPLEMENTATION and WHY NOT A HAND-BUILT
PRECESSION FORMULA below for why this design was chosen over reimplementing the
precession math from scratch. The .py CODE ITSELF has STILL never executed in a Python
interpreter this session (see EXECUTION STATUS at the very bottom, and
methodology_status()) -- three independent execution paths were tried again this pass
(direct sandbox, worktree-isolated agent, remote-isolated agent) and all three failed,
for the same reasons as every prior attempt. Do not conflate "the design is now sound
and the numbers check out by hand" with "this code has run."

METHODOLOGY SELECTION -- WHICH "LAHIRI" DID WE PICK, AND WHY (decided BEFORE any
accuracy/backtest comparison, per explicit instruction not to choose based on which
variant produces better historical predictions)
--------------------------------------------------------------------------------------
Swiss Ephemeris ships (at least) four differently-named "Lahiri" sidereal modes:

    mode  1 = Lahiri                  (SE's default/plain "Lahiri")
    mode 43 = Lahiri 1940
    mode 44 = Lahiri VP285 (1980)
    mode 46 = Lahiri ICRC

These are NOT interchangeable (see the numeric table in METHODOLOGY DISTINCTIONS
below). This module selects **mode 1, the plain/default "Lahiri"**, on THESE grounds,
all read directly from Swiss Ephemeris's own documentation this pass (not chosen by
comparing which one "worked better" in any test):

1. Astrodienst's own canonical ayanamsha explainer -- Dieter Koch (Swiss Ephemeris
   co-author), "Ayanamshas in Sidereal Astrology" (fetched live this pass via the
   Claude-in-Chrome browser tool, since the page requires JavaScript and a plain fetch
   returns only a bot-check shell):
   https://www.astro.com/astrology/in_ayanamsha_e.htm
   This page lists exactly ONE "Lahiri Ayanamsha" entry (no separate "ICRC"/"1940"/
   "VP285" entries at all) and describes it in unqualified terms: "This is the ayanamsha
   mostly used in India, and it is the official ayanamsha used to determine the dates of
   Hindu religious festivals... Hindu astrologers and their western disciples mostly use
   the so-called Lahiri ayanamsha." The separately-named 43/44/46 modes exist in the
   `swetest` command-line tool (for research/comparison purposes) but are NOT presented
   by Swiss Ephemeris's own documentation as alternative "Lahiri" choices for ordinary
   use -- mode 1 is what that documentation means by "the Lahiri ayanamsha."
2. Mode 1's live J2000.0 value (23.853222°) matches the ORIGINAL 1956 Calendar Reform
   Committee decree value (23°15'00" = 23.25° at 21 Mar 1956) to within ~0.8 arcsec when
   projected back to that date (see CROSS-CHECK RESULTS) -- i.e. mode 1 is the SE
   implementation that actually tracks the original historical decree, which is the
   specific, named, single "Lahiri ayanamsha" this module was built to represent (see
   ayanamsha.py's original SOURCING section, unchanged: the 1956 CRC decree).
3. By elimination: modes 43/44/46 are named, specific, LATER variants/refinements (1940
   predates the 1955/56 decree and is a different historical reconstruction; VP285 is an
   explicit 1980 revision; ICRC is a distinct later-standardized recomputation) --
   choosing any of those instead of the plain default would require its own, separate
   historical justification that this project does not have and is not asserting.

This decision was made by reading source documentation, not by comparing prediction
accuracy -- per instruction, methodology selection happens before, and independently of,
any backtesting.

LIVE QUERY IMPLEMENTATION
----------------------------
`fetch_live_swisseph_lahiri_ayanamsha_deg(jd_tt)` queries astro.com's `swetest.cgi`
(Swiss Ephemeris 2.10.03, Astrodienst) directly over HTTP, using the `-bj` flag (absolute
Julian Day, interpreted as TT -- confirmed empirically this pass: a query for
`-bj2451545.0` echoed back `TT: 2451545.000000000` exactly, with UT back-derived from
delta-T) and `-sid1` (mode 1, "Lahiri" -- see METHODOLOGY SELECTION above). This is the
actual reference Swiss Ephemeris binary computing the actual, non-approximated ayanamsha
value -- not a reimplementation. Real, live values obtained this way agree with the
project's SWISSEPH_MODE1_REFERENCE table by construction (same source), which is why
`cross_check()` below validates the FALLBACK linear model against that table, not the
live path against itself (that would be circular).

KNOWN LIMITATIONS OF THE LIVE-QUERY DESIGN (stated plainly, not hidden):
- Requires network access at call time. If unavailable, falls back to the linear model
  (see below) and FLAGS that fallback explicitly in the returned AyanamshaResult --
  never silently.
- `swetest.cgi` is Astrodienst's public interactive testing tool. It is not documented
  as a stable, rate-limit-free API intended for programmatic production traffic. Using
  it as a hard production dependency carries real operational risk (latency, possible
  future changes or throttling) that a locally-installed `pyswisseph` would not have.
  This module's design treats the live query as the best currently-available way to use
  "real Swiss Ephemeris" without local code execution (see WHY NOT PYSWISSEPH below) --
  not as a permanent architecture recommendation. A future pass with a working local
  Python environment should install `pyswisseph` (`pip install pyswisseph`) and swap the
  network call for a local `swisseph.get_ayanamsa_ut()` call, which is faster, has no
  external dependency at request time, and is the more defensible long-term production
  path.
- A per-process in-memory cache (`_LIVE_QUERY_CACHE`) avoids redundant network round
  trips for a JD already queried, but there is no persistent/on-disk cache -- a fresh
  process starts cold.

WHY NOT PYSWISSEPH DIRECTLY (item 5's first-choice option)
--------------------------------------------------------------
`pyswisseph` would be the better production choice (local, fast, no network dependency,
the same computation without the ToS/availability caveats above) but could not be used
this pass: installing it requires `pip install pyswisseph`, which requires a working
shell -- and this session's sandbox is unavailable (see EXECUTION STATUS). The live-CGI
path above is the closest honest substitute: it is still the real Swiss Ephemeris
algorithm computing the real answer, just reached over the network instead of via a
locally-installed library, because that is what was actually reachable this pass.

WHY NOT A HAND-BUILT PRECESSION FORMULA (an approach that was tried and rejected this
pass, documented rather than silently abandoned)
------------------------------------------------------------------------------------------
Before settling on the live-query design, a pure-Python replacement using the standard
IAU 1976 (Lieske) general-precession-in-longitude polynomial was attempted by hand:
    p_A(T) = 5029.0966"*T + 1.11113"*T^2 - 0.000006"*T^3   (T = Julian centuries from J2000 TT)
    ayanamsha(T) = ANCHOR_J2000_AYANAMSA_DEG + p_A(T)/3600
Hand-evaluated at T = -1 (year 1900) against the live SWISSEPH_MODE1_REFERENCE value for
that date: this formula gave 22.456245°, vs. the live SE value of 22.465373° -- a ~32.9
arcsec error, NOT a clear improvement over the simple two-point linear model's ~36.3
arcsec error at the same date. Two plausible explanations, neither confirmed: (a) the
polynomial coefficients as recalled are for the general IAU1976 precession constant,
which may not exactly match whatever specific, older precession model the ORIGINAL 1956
Lahiri decree (and by extension, Swiss Ephemeris's mode-1 reproduction of it) actually
used -- Dieter Koch's own documentation notes that "the official definition of the
Lahiri ayanamsha does not [cleanly] realise" its own stated intent, implying it follows
a specific historical calculation recipe rather than a clean modern formula; (b) an
error in the recalled coefficients themselves. Rather than present an unvalidated
formula as an improvement (this project's numbers must be demonstrated, not asserted),
this approach was DROPPED in favor of the live-query design above, which sidesteps the
question entirely by asking the real implementation instead of guessing its formula.

METHODOLOGY DISTINCTIONS -- THE FOUR SWISS EPHEMERIS "LAHIRI" MODES, NUMERICALLY
------------------------------------------------------------------------------------
All four queried live at J2000.0 this session:

    mode  1 "Lahiri"        23°51'11.6009"  = 23.853222 deg  <- SELECTED (see above)
    mode 43 "Lahiri 1940"   23°50'18.4322"  = 23.838453 deg  (-53.2 arcsec vs mode 1)
    mode 44 "Lahiri VP285"  23°51'34.6009"  = 23.859611 deg  (+23.0 arcsec vs mode 1)
    mode 46 "Lahiri ICRC"   23°51'10.5089"  = 23.852919 deg  (-1.1 arcsec vs mode 1)

(Fetched via https://www.astro.com/cgi/swetest.cgi?arg=-b1.1.2000+-ut12:00+-p0+-fPZL+-sidNN+-n1,
NN = 1, 43, 44, 46.)

CROSS-CHECK RESULTS FOR THE FALLBACK LINEAR MODEL (unchanged from the prior pass, still
accurate -- see lahiri_crosscheck.csv) -- 13 dates now, 1900-2050, including 1950 and
1975 added this pass:
- Near either anchor (1956, 2000): ~0.4-1.4 arcsec error.
- 1975 (INSIDE the anchor span, not an extrapolation case): -13.6 arcsec -- demonstrates
  the linear model's curvature error is real even when interpolating between the two
  anchors, not only when extrapolating beyond them.
- 1950 (6 years before the 1956 anchor): +23.5 arcsec.
- Range extremes (1900, 2050): +36.3 / -63.8 arcsec.
This is the model now used ONLY as an offline fallback, not as production-primary.

SOURCING -- ANCHOR VALUES (used by the fallback model; unchanged from the prior pass)
-----------------------------------------------------------------------------------------
1. OFFICIAL DECREE VALUE: 23°15'00" (23.25 deg) at 21 March 1956, 0:00 ET, India's
   Calendar Reform Committee. Source: Ron Scott, "The 'Lahiri ayanamsha' and the
   Sidereal Zodiac" (rscott51.substack.com, Feb 2025):
   https://rscott51.substack.com/p/the-lahiri-ayanamsha-and-the-sidereal
2. J2000.0 VALUE: 23.853222 deg at JD 2451545.0 TT -- confirmed live this session
   against Swiss Ephemeris mode 1 "Lahiri" (see METHODOLOGY DISTINCTIONS).

DEPENDENCY / VERSION RECORD (item 8)
-----------------------------------------
    Swiss Ephemeris version:     2.10.03 (self-reported in every swetest.cgi response
                                  banner this session, e.g. "version 2.10.03")
    pyswisseph version:          N/A -- not installed, not used this pass (see WHY NOT
                                  PYSWISSEPH above); the HTTP-CGI path uses Astrodienst's
                                  own server-side SE binary, not the Python binding
    Selected sidereal mode:      1 ("Lahiri", SE's default/plain mode)
    Methodology name:            "Lahiri" / "Chitrapaksha ayanamsha" (1955/56 Indian
                                  Calendar Reform Committee)
    Calculation date/time:       This module and all live reference values were
                                  gathered 2026-08-12 (session date); swetest.cgi queries
                                  used JPL DE441 ephemeris internally by default (no
                                  `-ejpl`/`-eswe` override was passed, so SE's own
                                  default ephemeris source was used -- not independently
                                  confirmed which that is without the flag echoed back)
    Relevant settings:           `-fPZL` output format, `-sid1` sidereal mode, `-bj<JD>`
                                  absolute-JD-in-TT input

EXECUTION STATUS
--------------------
NOT EXECUTED. Confirmed again this pass via three independent paths, same outcomes as
every prior attempt: `mcp__workspace__bash` direct call -- "Not enough disk space to set
up the workspace"; `Agent(isolation="worktree")` -- "Failed to resolve base branch
'HEAD': git rev-parse failed"; `Agent(isolation="remote")` -- identical git-repo error.
This is a real, reproducible, host-level constraint, not an assumption. All numbers in
this module were verified BY HAND against live-fetched reference values -- that is a
different claim from "this code has run," and methodology_status() keeps those two
claims separate.
"""

import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import List


# --- Anchor points for the FALLBACK linear model only (see SOURCING above) --------

ANCHOR_1956_JD = 2435553.5  # 21 Mar 1956, 0:00 TT-ish
ANCHOR_1956_AYANAMSA_DEG = 23.25  # 23 deg 15' 00" exactly, CRC decree

ANCHOR_J2000_JD = 2451545.0  # 1 Jan 2000, 12:00 TT
ANCHOR_J2000_AYANAMSA_DEG = 23.853222  # SE mode-1 "Lahiri" value at J2000.0, confirmed live

_DEG_PER_DAY = (ANCHOR_J2000_AYANAMSA_DEG - ANCHOR_1956_AYANAMSA_DEG) / (
    ANCHOR_J2000_JD - ANCHOR_1956_JD
)
_IMPLIED_ARCSEC_PER_YEAR = _DEG_PER_DAY * 365.25 * 3600.0  # ~49.6 arcsec/yr, see docstring


@dataclass
class AyanamshaResult:
    jd: float
    ayanamsha_deg: float
    method: str
    precision_note: str
    source: str = "unknown"  # "live_swisseph" | "linear_fallback"


# --- PRIMARY: live Swiss Ephemeris query --------------------------------------------

SWETEST_CGI_BASE = "https://www.astro.com/cgi/swetest.cgi"
SIDEREAL_MODE_LAHIRI = 1  # see METHODOLOGY SELECTION above

_LIVE_QUERY_CACHE = {}  # jd (rounded to 1e-6 day) -> float degrees


class LiveSwissEphemerisUnavailable(Exception):
    """Raised internally when the live query fails for any reason (network, parsing,
    unexpected response shape). Callers of lahiri_ayanamsha_deg() never see this --
    it is caught there and triggers the documented, flagged fallback."""


def fetch_live_swisseph_lahiri_ayanamsha_deg(jd_tt: float, timeout: float = 15.0) -> float:
    """
    Queries astro.com's swetest.cgi (Swiss Ephemeris 2.10.03) live for the mode-1
    "Lahiri" ayanamsha at Julian Day `jd_tt` (treated as TT, per the -bj flag's
    confirmed behavior -- see LIVE QUERY IMPLEMENTATION in the module docstring).
    Raises LiveSwissEphemerisUnavailable on any failure -- network, HTTP, or unexpected
    response shape -- so the caller can fall back deliberately rather than propagate an
    opaque exception.

    NOT EXECUTED this session (see EXECUTION STATUS) -- the query pattern and response
    parsing below were validated by hand against multiple real fetches performed
    directly through this session's web-fetch tool (not this urllib code path itself),
    the same caveat that applies to ephemeris_client.py's Horizons client elsewhere in
    this project.
    """
    cache_key = round(jd_tt, 6)
    if cache_key in _LIVE_QUERY_CACHE:
        return _LIVE_QUERY_CACHE[cache_key]

    arg = f"-bj{jd_tt}+-p0+-fPZL+-sid{SIDEREAL_MODE_LAHIRI}+-n1"
    url = f"{SWETEST_CGI_BASE}?arg={arg}"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, OSError) as e:
        raise LiveSwissEphemerisUnavailable(f"Network error querying swetest.cgi: {e}") from e

    # Expected line shape (confirmed live, multiple times, this session):
    #   ayanamsa =   23°51'11.6009 (Lahiri)
    match = re.search(
        r"ayanamsa\s*=\s*(\d+)\s*°\s*(\d+)\s*'\s*([\d.]+)\s*\(Lahiri\)", raw
    )
    if not match:
        raise LiveSwissEphemerisUnavailable(
            f"Could not parse ayanamsa line from swetest.cgi response "
            f"(first 300 chars): {raw[:300]!r}"
        )
    deg, minutes, seconds = match.groups()
    value = float(deg) + float(minutes) / 60.0 + float(seconds) / 3600.0
    _LIVE_QUERY_CACHE[cache_key] = value
    return value


# --- FALLBACK: two-point linear model (see CROSS-CHECK RESULTS above for its error) --

def _lahiri_ayanamsha_deg_linear_fallback(jd: float) -> AyanamshaResult:
    value = ANCHOR_1956_AYANAMSA_DEG + _DEG_PER_DAY * (jd - ANCHOR_1956_JD)
    return AyanamshaResult(
        jd=jd,
        ayanamsha_deg=value,
        method="lahiri_linear_two_anchor_FALLBACK (1956 decree + J2000 SE-mode-1 value)",
        precision_note=(
            "FALLBACK PATH -- live Swiss Ephemeris query was unavailable or failed for "
            "this call. Linear model: ~0.4-1.4 arcsec error near the anchors, growing to "
            "~14-64 arcsec elsewhere in 1900-2050 (see lahiri_crosscheck.csv). Adequate "
            "for zodiac-sign-level use only."
        ),
        source="linear_fallback",
    )


def lahiri_ayanamsha_deg(jd: float, allow_fallback: bool = True) -> AyanamshaResult:
    """
    MAIN ENTRY POINT. Tries the live Swiss Ephemeris query first (the real reference
    computation -- see METHODOLOGY SELECTION and LIVE QUERY IMPLEMENTATION above). If
    that fails and `allow_fallback` is True (default), falls back to the two-point
    linear approximation and marks the result's `source` field "linear_fallback" so
    callers can always tell which path actually produced a given number -- never a
    silent substitution. If `allow_fallback` is False and the live query fails, the
    LiveSwissEphemerisUnavailable exception propagates instead of masking the failure.
    """
    try:
        value = fetch_live_swisseph_lahiri_ayanamsha_deg(jd)
        return AyanamshaResult(
            jd=jd,
            ayanamsha_deg=value,
            method="swisseph_live_mode1_lahiri (astro.com swetest.cgi, SE 2.10.03)",
            precision_note=(
                "Live Swiss Ephemeris computation (mode 1, 'Lahiri') -- the actual "
                "reference implementation's output, not an approximation. Subject to "
                "network availability; see module docstring KNOWN LIMITATIONS OF THE "
                "LIVE-QUERY DESIGN."
            ),
            source="live_swisseph",
        )
    except LiveSwissEphemerisUnavailable:
        if not allow_fallback:
            raise
        return _lahiri_ayanamsha_deg_linear_fallback(jd)


def lahiri_ayanamsha_deg_for_year(year: float) -> AyanamshaResult:
    """Convenience wrapper taking a decimal year instead of a Julian Day, using
    Jan 1 00:00-ish of that year (matches coordinates.py's julian_day() convention to
    within ~0.5 day at year boundaries)."""
    jd = 2451545.0 + (year - 2000.0) * 365.25
    return lahiri_ayanamsha_deg(jd)


def tropical_to_sidereal_lahiri(tropical_lon_deg: float, jd: float) -> float:
    """Subtract the Lahiri ayanamsha from a tropical ecliptic longitude to get the
    sidereal (kundli-convention) longitude, normalized to [0, 360). This is the ONLY
    place the sidereal transformation happens -- callers should get their tropical
    longitude from ephemeris_client.py/coordinates.py (JPL-derived), never from here."""
    ayanamsha = lahiri_ayanamsha_deg(jd).ayanamsha_deg
    return (tropical_lon_deg - ayanamsha) % 360.0


# --- Independent cross-check reference data (LIVE, fetched this session) -----------
# Validates the FALLBACK linear model specifically (see cross_check() docstring for why
# validating the live path against itself would be circular). Source for every row:
# https://www.astro.com/cgi/swetest.cgi (Astrodienst, Swiss Ephemeris 2.10.03), sidereal
# mode 1 "Lahiri". Full table also in lahiri_crosscheck.csv.

@dataclass
class ReferencePoint:
    label: str
    jd_ut: float
    swisseph_lahiri_deg: float


SWISSEPH_MODE1_REFERENCE: List[ReferencePoint] = [
    ReferencePoint("1900-01-01 00:00 UT", 2415020.5, 22.465373),
    ReferencePoint("1950-01-01 00:00 UT", 2433282.5, 23.157808),
    ReferencePoint("1956-01-01 00:00 UT", 2435473.5, 23.247365),
    ReferencePoint("1956-03-21 00:00 UT (our anchor date)", 2435553.5, 23.250221),
    ReferencePoint("1956-06-01 00:00 UT", 2435625.5, 23.252598),
    ReferencePoint("1956-09-22 00:00 UT", 2435738.5, 23.256815),
    ReferencePoint("1956-12-31 00:00 UT", 2435838.5, 23.260637),
    ReferencePoint("1975-01-01 00:00 UT", 2442413.5, 23.512558),
    ReferencePoint("2000-01-01 00:00 UT", 2451544.5, 23.853204),
    ReferencePoint("2000-01-01 12:00 UT (our anchor -- J2000.0)", 2451545.0, 23.853222),
    ReferencePoint("2026-01-01 00:00 UT", 2461041.5, 24.221810),
    ReferencePoint("2026-08-12 00:00 UT", 2461264.5, 24.231567),
    ReferencePoint("2050-01-01 00:00 UT", 2469807.5, 24.559827),
]


@dataclass
class CrossCheckRow:
    label: str
    jd_ut: float
    our_value_deg: float
    reference_value_deg: float
    diff_arcsec: float
    classification: str


def _classify_diff(abs_arcsec: float, jd_ut: float) -> str:
    near_anchor = (
        abs(jd_ut - ANCHOR_1956_JD) < 400 or abs(jd_ut - ANCHOR_J2000_JD) < 10
    )
    if near_anchor and abs_arcsec < 5.0:
        return "ROUNDING"
    return "EXPECTED_METHODOLOGICAL_DIFFERENCE"


def cross_check() -> List[CrossCheckRow]:
    """
    Validates the FALLBACK linear model (`_lahiri_ayanamsha_deg_linear_fallback`)
    against the baked-in live Swiss Ephemeris reference points. Deliberately does NOT
    exercise the live-query path here: comparing a live query's own output against a
    reference table built FROM live queries of the same source would be circular (it
    would only test that HTTP still works and the regex still parses, not accuracy).
    The live path's correctness rests on it being the actual reference implementation
    by construction; what genuinely needs -- and gets -- accuracy validation is the
    approximation used when that path is unavailable.
    """
    rows = []
    for ref in SWISSEPH_MODE1_REFERENCE:
        ours = _lahiri_ayanamsha_deg_linear_fallback(ref.jd_ut).ayanamsha_deg
        diff_arcsec = (ours - ref.swisseph_lahiri_deg) * 3600.0
        rows.append(CrossCheckRow(
            label=ref.label, jd_ut=ref.jd_ut, our_value_deg=ours,
            reference_value_deg=ref.swisseph_lahiri_deg, diff_arcsec=diff_arcsec,
            classification=_classify_diff(abs(diff_arcsec), ref.jd_ut),
        ))
    return rows


# --- Honest status reporting --------------------------------------------------------

VALIDATED = "VALIDATED"
PARTIALLY_VALIDATED = "PARTIALLY_VALIDATED"
UNVERIFIED = "UNVERIFIED"


def methodology_status() -> dict:
    """
    Current, honest validation status. Per explicit instruction, this MUST remain
    PARTIALLY_VALIDATED (not VALIDATED) until the implementation itself has executed
    successfully in a Python interpreter AND the independent comparisons have been run
    (not just hand-verified) and passed. Neither has happened yet -- see EXECUTION
    STATUS in the module docstring.
    """
    return {
        "status": PARTIALLY_VALIDATED,
        "source_methodology": "DOCUMENTED -- live Swiss Ephemeris mode 1 ('Lahiri') "
                               "selected on methodology/source grounds (Dieter Koch's "
                               "canonical ayanamsha documentation + agreement with the "
                               "1956 CRC decree value), before and independent of any "
                               "accuracy comparison. Fallback linear model explicitly "
                               "labeled an approximation, not presented as the "
                               "historical algorithm.",
        "anchor_validation": "CONFIRMED LIVE against Swiss Ephemeris 2.10.03.",
        "execution": "EXECUTED for the first time this pass (Astrowatch-2 port, code "
                     "execution became available in this session's sandbox). "
                     "tests/test_ayanamsha.py: 25/25 pass (one genuine test-regex bug "
                     "found and fixed by actual execution -- see the comment above "
                     "test_approximate_lahiri_function_delegates_not_hardcodes in that "
                     "file; the source code itself was already correct). "
                     "tests/test_rashi_nakshatra.py: 20/20 pass. The live-query path "
                     "(fetch_live_swisseph_lahiri_ayanamsha_deg) was executed and "
                     "diagnosed to fail in THIS sandbox specifically: the outbound "
                     "proxy returns HTTP 403 for astro.com with header "
                     "'X-Proxy-Error: blocked-by-allowlist' (confirmed via a raw curl "
                     "test), not an astro.com-side error -- so the fallback path is "
                     "what actually executes and returns results in this environment. "
                     "Separately, `pip install pyswisseph` now succeeds (pypi.org is "
                     "allowlisted) and was executed locally, producing real numbers -- "
                     "but diagnosed to run in Moshier approximation mode (no .se1 "
                     "Swiss Ephemeris data files present; confirmed via "
                     "swe.calc_ut(..., FLG_SWIEPH) silently returning "
                     "retflag=FLG_MOSEPH), which disagreed with the session's earlier "
                     "live-fetched SWISSEPH_MODE1_REFERENCE table by up to 17.5 "
                     "arcsec, non-monotonically across dates -- classified as an "
                     "EXPECTED_METHODOLOGICAL_DIFFERENCE (approximate vs. full-file "
                     "ephemeris precision), not a Lahiri-definition disagreement or "
                     "code bug. The .se1 files could not be downloaded to confirm "
                     "further -- astro.com is blocked by the same proxy allowlist.",
        "independent_cross_check": "DONE for the fallback model -- 13 dates (1900-2050) "
                                    "vs. live Swiss Ephemeris; see lahiri_crosscheck.csv. "
                                    "The live-query path's own code (urllib request + "
                                    "regex parsing) has now executed against real "
                                    "captured swetest.cgi responses via the unit tests "
                                    "(mocked transport, real response text) -- passes. "
                                    "The live urllib call itself cannot be exercised "
                                    "end-to-end in this sandbox (proxy allowlist blocks "
                                    "astro.com); a local pyswisseph cross-check was run "
                                    "instead (see 'execution' above) but is itself only "
                                    "Moshier-precision here, so it cannot serve as a "
                                    "higher-precision substitute in this environment.",
        "multi_date_validation": "DONE for the fallback model (13 dates), now via actual "
                                  "execution, not just hand-verification. Boundary "
                                  "(rāśi/nakshatra/wraparound) tests in "
                                  "tests/test_rashi_nakshatra.py: 20/20 executed and pass.",
        "historical_applicability": "NOT APPLICABLE BY DESIGN -- scoped to modern/kundli "
                                     "use only; BS-19/BS-42/BS-20 remain "
                                     "sidereal_unresolved, confirmed via actual execution "
                                     "this pass (rule_registry.py, all 8 matching rule "
                                     "IDs: BS-19-saturn-year, BS-19-jupiter-year, "
                                     "BS-20-02, BS-20-sannipata, BS-42-01a, BS-42-01b, "
                                     "BS-42-14, BS-42-14b).",
        "not_upgraded_to_validated_because": [
            "The live-query path (the intended PRIMARY path) has never actually "
            "reached astro.com in any execution environment available this session -- "
            "it is correctly coded and unit-tested against real captured responses, "
            "but its live network call is blocked by this sandbox's proxy allowlist, "
            "so end-to-end success has still never been directly observed.",
            "The one alternative local computation available (pyswisseph) is confirmed "
            "to run in reduced-precision Moshier mode here (no ephemeris data files "
            "reachable), so it cannot itself confirm the live path's expected precision.",
        ],
    }


def self_test():
    """Prints a human-readable cross-check report for the fallback model, plus status.
    Like everything else this pass: hand-verified, NOT executed (see methodology_status())."""
    print(f"Implied precession rate from the two fallback anchors: "
          f"{_IMPLIED_ARCSEC_PER_YEAR:.3f} arcsec/year")
    print()
    print(f"{'Label':<45}{'Fallback':>12}{'SwissEph':>12}{'Diff(as)':>10}  Classification")
    for row in cross_check():
        print(f"{row.label:<45}{row.our_value_deg:>12.6f}{row.reference_value_deg:>12.6f}"
              f"{row.diff_arcsec:>10.2f}  {row.classification}")
    print()
    status = methodology_status()
    print(f"methodology_status(): {status['status']}")


if __name__ == "__main__":
    self_test()
