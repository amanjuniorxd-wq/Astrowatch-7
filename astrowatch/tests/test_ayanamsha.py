"""
Astrowatch — tests for ayanamsha.py
===================================
STATUS: written as real, structured unittest code. NOT executed by a Python interpreter
this session -- sandbox and both alternate agent-isolation execution paths remain
unreachable (see ayanamsha.py's EXECUTION STATUS docstring section for the precise,
re-confirmed-this-pass diagnosis). Every expected value below was HAND-VERIFIED against
a live Swiss Ephemeris query fetched this session (astro.com's swetest.cgi, sidereal
mode 1 "Lahiri", Swiss Ephemeris 2.10.03) -- not invented, not carried over from
training-data recall. Run with:

    cd .. && python3 -m unittest tests.test_ayanamsha -v

the moment a Python environment is available.

IMPORTANT DESIGN NOTE: ayanamsha.lahiri_ayanamsha_deg() now tries a LIVE NETWORK QUERY
first (see ayanamsha.py's METHODOLOGY SELECTION / LIVE QUERY IMPLEMENTATION). Unit tests
must not depend on live network availability -- that would make them flaky and
environment-dependent. So:
  - TestFallbackModelAgainstLiveSwissEphemeris tests the deterministic FALLBACK model
    directly (`ayanamsha._lahiri_ayanamsha_deg_linear_fallback`), not the network path.
  - TestLiveQueryParsing tests the regex/parsing logic in
    fetch_live_swisseph_lahiri_ayanamsha_deg() against REAL response text captured live
    this session, via a mocked urlopen -- so it's a real test of the parsing code
    without touching the network.
  - TestFallbackWiring tests that lahiri_ayanamsha_deg() actually falls back (and flags
    that it did) when the live path is unavailable, again via mocking rather than
    relying on the network actually being down.
"""

import os
import re
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import ayanamsha  # noqa: E402


# --- Tolerance notes ------------------------------------------------------------------
# Near either anchor (1956-03-21, 2000-01-01) the linear FALLBACK model agrees with live
# Swiss Ephemeris mode-1 "Lahiri" to within ~1.5 arcsec -- real residual, not zero,
# because the anchors are defined at exact decree/epoch instants while these test dates
# are UT midnights (or noon) that don't always land exactly on those instants. Away from
# both anchors (and even *between* them, e.g. 1950 and 1975) the model has a real,
# expected, quantified drift (see EXPECTED_TOLERANCE per test) from linear-vs-actual-
# precession curvature -- NOT a bug, see ayanamsha.py's WHY NOT A HAND-BUILT PRECESSION
# FORMULA section for why this was left as a documented approximation rather than
# "fixed" with an unvalidated replacement formula.


class TestFallbackModelAgainstLiveSwissEphemeris(unittest.TestCase):
    """Each test compares ayanamsha._lahiri_ayanamsha_deg_linear_fallback(jd) against a
    value fetched live from astro.com/cgi/swetest.cgi this session (sidereal mode 1,
    "Lahiri"). Source query pattern: arg=-bDD.MM.YYYY+-utHH:MM+-p0+-fPZL+-sid1+-n1"""

    def _check(self, jd_ut: float, expected_swisseph_deg: float, tolerance_arcsec: float,
               label: str):
        result = ayanamsha._lahiri_ayanamsha_deg_linear_fallback(jd_ut)
        self.assertEqual(result.source, "linear_fallback")
        diff_arcsec = abs(result.ayanamsha_deg - expected_swisseph_deg) * 3600.0
        self.assertLessEqual(
            diff_arcsec, tolerance_arcsec,
            f"{label}: fallback={result.ayanamsha_deg:.6f} deg, "
            f"swisseph={expected_swisseph_deg:.6f} deg, "
            f"diff={diff_arcsec:.2f} arcsec, tolerance={tolerance_arcsec} arcsec"
        )

    def test_1900_01_01(self):
        self._check(2415020.5, 22.465373, tolerance_arcsec=45.0, label="1900-01-01")

    def test_1950_01_01(self):
        # SwissEph: 23°9'28.1073" = 23.157808 deg. 6 yrs before the 1956 anchor,
        # slightly OUTSIDE the anchor span on the near side -- expect ~24 arcsec drift.
        self._check(2433282.5, 23.157808, tolerance_arcsec=30.0, label="1950-01-01")

    def test_1956_01_01(self):
        self._check(2435473.5, 23.247365, tolerance_arcsec=3.0, label="1956-01-01")

    def test_1956_03_21_anchor_date(self):
        self._check(2435553.5, 23.250221, tolerance_arcsec=2.0, label="1956-03-21 (anchor)")

    def test_1956_06_01(self):
        self._check(2435625.5, 23.252598, tolerance_arcsec=3.0, label="1956-06-01")

    def test_1956_09_22(self):
        self._check(2435738.5, 23.256815, tolerance_arcsec=3.0, label="1956-09-22")

    def test_1956_12_31(self):
        self._check(2435838.5, 23.260637, tolerance_arcsec=3.0, label="1956-12-31")

    def test_1975_01_01(self):
        # SwissEph: 23°30'45.2078" = 23.512558 deg. INSIDE the anchor span (19 yrs after
        # 1956, 25 yrs before 2000) -- still shows ~14 arcsec drift, demonstrating the
        # linear model's curvature error is real even when interpolating, not just when
        # extrapolating beyond the anchors.
        self._check(2442413.5, 23.512558, tolerance_arcsec=20.0, label="1975-01-01")

    def test_2000_01_01_midnight(self):
        self._check(2451544.5, 23.853204, tolerance_arcsec=2.0, label="2000-01-01 00:00")

    def test_2000_01_01_noon_anchor_date(self):
        self._check(2451545.0, 23.853222, tolerance_arcsec=0.01,
                    label="2000-01-01 12:00 (anchor)")

    def test_2026_01_01(self):
        self._check(2461041.5, 24.221810, tolerance_arcsec=45.0, label="2026-01-01")

    def test_2026_08_12(self):
        self._check(2461264.5, 24.231567, tolerance_arcsec=50.0, label="2026-08-12")

    def test_2050_01_01(self):
        self._check(2469807.5, 24.559827, tolerance_arcsec=75.0, label="2050-01-01")


# --- Real captured swetest.cgi response text, fetched live this session --------------
# Used to test the LIVE-QUERY PARSING logic without touching the network. This is the
# actual text returned for arg=-bj2451545.0+-p0+-fPZL+-sid1+-n1 (J2000.0 TT).
_REAL_SWETEST_RESPONSE_J2000 = """
    /ulb/swetest -b -n -s -f -p -bj2451545.0 -p0 -fPZL -sid1 -n1

date (dmy) 1.1.2000 greg.   12:00:00 TT		version 2.10.03
UT:  2451544.999261240     delta t: 63.828914 sec
TT:  2451545.000000000

ayanamsa =   23°51'11.6008 (Lahiri)
Epsilon (m)       23°26'21.4060
Sun             16 sa 30'53.7951  256°30'53.7951
"""

_REAL_SWETEST_RESPONSE_1956 = """
    /ulb/swetest -b -n -s -f -p -b21.3.1956 -ut0:00 -p0 -fPZL -sid1 -n1

date (dmy) 21.3.1956 greg.   0:00:00 UT		version 2.10.03
UT:  2435553.500000000     delta t: 31.411589 sec
TT:  2435553.500363560

ayanamsa =   23°15' 0.7964 (Lahiri)
Epsilon (m)       23°26'41.9120
Sun              7 pi  6'29.3172  337° 6'29.3172
"""


def _make_fake_response(text: str):
    """Minimal stand-in for the object returned by urllib.request.urlopen() used as a
    context manager -- just needs .read() and to support `with ... as resp`."""
    class _Fake:
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return False
        def read(self):
            return text.encode("utf-8")
    return _Fake()


class TestLiveQueryParsing(unittest.TestCase):
    """Tests fetch_live_swisseph_lahiri_ayanamsha_deg()'s HTTP-response parsing against
    REAL text captured live this session -- via a mocked urlopen, so no network call
    actually happens, but the regex/parsing code under test is exercised for real."""

    def setUp(self):
        ayanamsha._LIVE_QUERY_CACHE.clear()

    def test_parses_j2000_response_correctly(self):
        with mock.patch("ayanamsha.urllib.request.urlopen",
                         return_value=_make_fake_response(_REAL_SWETEST_RESPONSE_J2000)):
            value = ayanamsha.fetch_live_swisseph_lahiri_ayanamsha_deg(2451545.0)
        self.assertAlmostEqual(value, 23.853222, places=5)

    def test_parses_1956_response_correctly(self):
        with mock.patch("ayanamsha.urllib.request.urlopen",
                         return_value=_make_fake_response(_REAL_SWETEST_RESPONSE_1956)):
            value = ayanamsha.fetch_live_swisseph_lahiri_ayanamsha_deg(2435553.5)
        self.assertAlmostEqual(value, 23.250221, places=5)

    def test_result_is_cached(self):
        with mock.patch("ayanamsha.urllib.request.urlopen",
                         return_value=_make_fake_response(_REAL_SWETEST_RESPONSE_J2000)) as m:
            ayanamsha.fetch_live_swisseph_lahiri_ayanamsha_deg(2451545.0)
            ayanamsha.fetch_live_swisseph_lahiri_ayanamsha_deg(2451545.0)
        self.assertEqual(m.call_count, 1, "second call with the same JD should hit the "
                                            "in-memory cache, not the network again")

    def test_unparseable_response_raises_unavailable(self):
        with mock.patch("ayanamsha.urllib.request.urlopen",
                         return_value=_make_fake_response("garbage, no ayanamsa line here")):
            with self.assertRaises(ayanamsha.LiveSwissEphemerisUnavailable):
                ayanamsha.fetch_live_swisseph_lahiri_ayanamsha_deg(2451545.0)


class TestFallbackWiring(unittest.TestCase):
    """Tests that lahiri_ayanamsha_deg() actually falls back -- and FLAGS that it did,
    via the `source` field -- when the live path is unavailable, and that it does NOT
    silently fall back when allow_fallback=False."""

    def test_falls_back_and_flags_source_on_live_failure(self):
        with mock.patch("ayanamsha.fetch_live_swisseph_lahiri_ayanamsha_deg",
                         side_effect=ayanamsha.LiveSwissEphemerisUnavailable("simulated")):
            result = ayanamsha.lahiri_ayanamsha_deg(2451545.0)
        self.assertEqual(result.source, "linear_fallback")

    def test_uses_live_source_when_available(self):
        with mock.patch("ayanamsha.fetch_live_swisseph_lahiri_ayanamsha_deg",
                         return_value=23.853222):
            result = ayanamsha.lahiri_ayanamsha_deg(2451545.0)
        self.assertEqual(result.source, "live_swisseph")
        self.assertAlmostEqual(result.ayanamsha_deg, 23.853222, places=6)

    def test_raises_when_fallback_disallowed_and_live_fails(self):
        with mock.patch("ayanamsha.fetch_live_swisseph_lahiri_ayanamsha_deg",
                         side_effect=ayanamsha.LiveSwissEphemerisUnavailable("simulated")):
            with self.assertRaises(ayanamsha.LiveSwissEphemerisUnavailable):
                ayanamsha.lahiri_ayanamsha_deg(2451545.0, allow_fallback=False)


class TestCrossCheckSelfConsistency(unittest.TestCase):
    """Sanity checks on the module's own cross_check()/methodology_status() machinery."""

    def test_cross_check_covers_all_reference_points(self):
        rows = ayanamsha.cross_check()
        self.assertEqual(len(rows), len(ayanamsha.SWISSEPH_MODE1_REFERENCE))
        self.assertEqual(len(rows), 13)  # 11 from the prior pass + 1950 + 1975 this pass

    def test_anchor_rows_classified_as_rounding_or_expected(self):
        rows = {r.label: r for r in ayanamsha.cross_check()}
        j2000_row = rows["2000-01-01 12:00 UT (our anchor -- J2000.0)"]
        self.assertLess(abs(j2000_row.diff_arcsec), 0.01)

    def test_methodology_status_is_not_overclaimed(self):
        status = ayanamsha.methodology_status()
        self.assertEqual(status["status"], ayanamsha.PARTIALLY_VALIDATED)
        self.assertNotEqual(status["status"], ayanamsha.VALIDATED)


class TestRegressionNoHardcodedSinglePointConstantInCoordinates(unittest.TestCase):
    """
    Guards against exactly the regression this project called out: nobody should be able
    to silently revert coordinates.py back to a hardcoded single-anchor ayanamsha guess
    (the original pre-this-project behavior: `23.85 + (year - 2000.0) * (50.29/3600.0)`,
    sourced to nothing). The source of truth must stay ayanamsha.py.

    SOURCE-INSPECTION test (reads coordinates.py's text), deliberately -- needs to catch
    a regression even in an environment where nobody re-derives the "correct" answer.
    """

    def setUp(self):
        coords_path = os.path.join(os.path.dirname(__file__), "..", "coordinates.py")
        with open(coords_path, "r", encoding="utf-8") as f:
            self.source = f.read()

    def test_coordinates_imports_from_ayanamsha_module(self):
        self.assertIn(
            "from ayanamsha import", self.source,
            "coordinates.py no longer imports from ayanamsha.py -- if it computes its "
            "own ayanamsha value independently, that's exactly the regression this test "
            "exists to catch."
        )

    def test_approximate_lahiri_function_delegates_not_hardcodes(self):
        # NOTE (fixed after first real execution of this suite): the original pattern
        # was r"def approximate_lahiri_ayanamsa_deg\(.*?\):(.*?)(?:\ndef |\Z)". It
        # assumed the signature ends "...):" immediately, but the real signature is
        # "def approximate_lahiri_ayanamsa_deg(year: float) -> float:" -- a return-type
        # annotation sits between ")" and ":". Because re.DOTALL lets ".*?" cross
        # newlines, the old pattern silently skipped past the real signature and
        # anchored on the next unrelated "):" it could find (self_test()'s empty-arg
        # "():" at the end of the file), capturing everything up to EOF as "body" and
        # making the test fail even though coordinates.py correctly delegates (verified
        # by direct inspection: line 222 is
        # "return lahiri_ayanamsha_deg_for_year(year).ayanamsha_deg"). This is a test
        # bug, not a source regression -- fixed here to tolerate an optional "-> Type"
        # return annotation before the colon.
        match = re.search(
            r"def approximate_lahiri_ayanamsa_deg\([^)]*\)(?:\s*->\s*[^:]+)?:(.*?)(?:\ndef |\Z)",
            self.source, re.DOTALL,
        )
        self.assertIsNotNone(match, "approximate_lahiri_ayanamsa_deg() not found at all "
                                     "-- if it was removed, confirm nothing else in the "
                                     "codebase reintroduced a hardcoded constant instead.")
        body = match.group(1)
        self.assertIn(
            "lahiri_ayanamsha_deg_for_year", body,
            "approximate_lahiri_ayanamsa_deg() no longer delegates to "
            "ayanamsha.lahiri_ayanamsha_deg_for_year() -- looks like a hardcoded "
            "constant/rate may have been reintroduced directly in coordinates.py."
        )
        self.assertNotRegex(
            body, r"23\.85\s*\+",
            "Looks like the old hardcoded '23.85 + ...' single-anchor formula is back "
            "in coordinates.py -- this must live only in ayanamsha.py's sourced anchors."
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
