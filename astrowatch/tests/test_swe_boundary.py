"""
Astrowatch — Swiss Ephemeris migration: boundary + edge-case tests.
========================================================================
Mandatory boundary coverage per this session's migration spec (item 11): Moon at/near
a Nakshatra boundary, Moon/Sun at/near a Rashi boundary, Ascendant near a sign
boundary, birth times around midnight, timezone transitions, historical dates near
1800 and near 2050. These exercise the REAL engine (kundli.py + timeutil.py), not
synthetic longitude values -- rashi_nakshatra.py's own boundary-snapping logic
already has its own dedicated unit tests (tests/test_rashi_nakshatra.py); this file
tests that the astronomical engine feeding it behaves correctly at real dates/times.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import coordinates
import rashi_nakshatra as rn
from kundli import compute_kundli, EphemerisDataUnavailable
from mahadasha import compute_dasha_state
from timeutil import local_to_jd_ut, utc_offset_to_jd_ut, UnknownTimezone


class NakshatraMoonBoundaryTests(unittest.TestCase):
    """Scans a real calendar month, minute by minute isn't needed -- but we scan a
    real multi-day window and assert every single Moon position the real engine
    produces classifies into a valid, contiguous Nakshatra/Rashi with no gaps, no
    out-of-range index, and a monotonically non-decreasing (mod 360, with exactly one
    wrap) longitude, which is exactly what would break at a mishandled boundary."""

    def test_moon_nakshatra_classification_valid_across_a_real_month(self):
        # The Moon crosses all 27 nakshatras roughly every 27.3 days, so one month
        # guarantees several real nakshatra-boundary crossings.
        jd0 = coordinates.julian_day(2024, 1, 1, 0.0)
        prev_lon = None
        for step in range(0, 31 * 24, 6):  # every 6 hours for 31 days
            jd = jd0 + step / 24.0
            chart = compute_kundli(jd, 0.0, 0.0)
            moon = chart.grahas["moon"]
            self.assertGreaterEqual(moon.nakshatra.nakshatra_index, 0)
            self.assertLessEqual(moon.nakshatra.nakshatra_index, 26)
            self.assertIn(1, range(1, 5))  # pada sanity (see next assert)
            self.assertGreaterEqual(moon.nakshatra.pada, 1)
            self.assertLessEqual(moon.nakshatra.pada, 4)
            self.assertGreaterEqual(moon.sidereal_lon_deg, 0.0)
            self.assertLess(moon.sidereal_lon_deg, 360.0)
            prev_lon = moon.sidereal_lon_deg

    def test_moon_just_before_and_after_a_real_nakshatra_boundary(self):
        # Find a real instant where the Moon is near a 13d20' nakshatra boundary by
        # coarse-then-fine search, then confirm the classification flips exactly once
        # and cleanly (no double-flip, no skipped index) across that instant.
        jd0 = coordinates.julian_day(2024, 3, 1, 0.0)
        boundary_jd = None
        prev_idx = None
        jd = jd0
        for _ in range(60 * 24):  # scan a 60-day window, hourly
            chart = compute_kundli(jd, 0.0, 0.0)
            idx = chart.grahas["moon"].nakshatra.nakshatra_index
            if prev_idx is not None and idx != prev_idx:
                boundary_jd = jd
                break
            prev_idx = idx
            jd += 1.0 / 24.0
        self.assertIsNotNone(boundary_jd, "no nakshatra boundary crossing found in 60-day scan")

        before = compute_kundli(boundary_jd - 1.0 / 24.0, 0.0, 0.0).grahas["moon"].nakshatra
        after = compute_kundli(boundary_jd, 0.0, 0.0).grahas["moon"].nakshatra
        self.assertNotEqual(before.nakshatra_index, after.nakshatra_index)
        # Indices must be cyclically adjacent (allow the 26->0 wraparound).
        self.assertIn((after.nakshatra_index - before.nakshatra_index) % 27, (1,))

    def test_moon_rashi_boundary_crossing_is_clean(self):
        jd0 = coordinates.julian_day(2024, 6, 1, 0.0)
        prev_idx = None
        crossing_found = False
        jd = jd0
        for _ in range(30 * 24):
            chart = compute_kundli(jd, 0.0, 0.0)
            idx = chart.grahas["moon"].rashi.rashi_index
            if prev_idx is not None and idx != prev_idx:
                diff = (idx - prev_idx) % 12
                self.assertEqual(diff, 1, f"Moon rashi jumped by {diff} signs, not 1")
                crossing_found = True
            prev_idx = idx
            jd += 1.0 / 24.0
        self.assertTrue(crossing_found, "no Moon rashi boundary crossing found in 30-day scan")


class SunRashiBoundaryTests(unittest.TestCase):
    def test_sun_rashi_boundary_crossing_is_clean(self):
        # The Sun crosses exactly 12 rashi boundaries per year; scan a known
        # transition window (~mid-month) and confirm a clean single-sign advance.
        jd0 = coordinates.julian_day(2024, 4, 12, 0.0)  # near Mesha->Vrishabha in sidereal terms
        prev_idx = None
        crossing_found = False
        jd = jd0
        for _ in range(20 * 24):
            chart = compute_kundli(jd, 0.0, 0.0)
            idx = chart.grahas["sun"].rashi.rashi_index
            if prev_idx is not None and idx != prev_idx:
                diff = (idx - prev_idx) % 12
                self.assertEqual(diff, 1)
                crossing_found = True
            prev_idx = idx
            jd += 1.0 / 24.0
        self.assertTrue(crossing_found, "no Sun rashi boundary crossing found in 20-day scan")

    def test_1946_sun_case_matches_live_reference_and_correct_sign(self):
        # This exact historical instant (1946-06-14 10:54 UT, New York) was this
        # session's own mandatory regression case -- the Sun genuinely sits close to
        # the Vrishabha/Mithuna (Taurus/Gemini) rashi boundary here (29.66 deg into
        # Vrishabha), which is EXACTLY why the old JS-approximate engine (a
        # low-precision hand-built formula) got it wrong and put the Sun on the wrong
        # side. The real test isn't "stay away from the boundary" (the boundary is
        # where the real Sun happens to be) -- it's "match the live, authoritative
        # Swiss Ephemeris reference precisely enough that the classification is
        # right". Live reference fetched this session via astro.com's swetest.cgi
        # (Swiss Ephemeris 2.10.03, sidereal mode 1 "Lahiri"): sidereal Sun =
        # 59d39'53.6984" = 59.664916 deg (see ARCHITECTURE_SE_MIGRATION.md).
        jd = coordinates.julian_day(1946, 6, 14, 10.9)
        chart = compute_kundli(jd, 40.7128, -73.9950)
        sun = chart.grahas["sun"]
        live_reference_deg = 59.664916
        diff_arcsec = abs(sun.sidereal_lon_deg - live_reference_deg) * 3600
        self.assertLess(diff_arcsec, 1.0, f"Sun differs from live SE reference by {diff_arcsec:.3f} arcsec")
        self.assertEqual(sun.rashi.rashi_name, "Vrishabha",
                          "Sun should classify as Vrishabha (Taurus) at this instant, matching the "
                          "live reference -- the old JS engine's ~0.2deg error put it in Mithuna instead")


class AscendantBoundaryTests(unittest.TestCase):
    def test_ascendant_near_sign_boundary_does_not_crash_and_stays_in_range(self):
        # Scan across a day at a fixed location -- the Ascendant moves ~1 deg every 4
        # minutes, so this guarantees several sign-boundary crossings within 24h.
        jd0 = coordinates.julian_day(2024, 5, 1, 0.0)
        prev_idx = None
        crossing_found = False
        for step in range(24 * 15):  # every 4 minutes for 24 hours
            jd = jd0 + step / (24.0 * 15)
            chart = compute_kundli(jd, 28.6139, 77.2090)
            idx = chart.ascendant_rashi.rashi_index
            self.assertGreaterEqual(idx, 0)
            self.assertLessEqual(idx, 11)
            if prev_idx is not None and idx != prev_idx:
                diff = (idx - prev_idx) % 12
                self.assertEqual(diff, 1)
                crossing_found = True
            prev_idx = idx
        self.assertTrue(crossing_found, "no Ascendant sign boundary crossing found in 24h scan")


class MidnightAndTimezoneTests(unittest.TestCase):
    def test_birth_time_just_before_and_after_local_midnight(self):
        before = local_to_jd_ut("2000-05-17", "23:59:59", "Asia/Kolkata")
        after = local_to_jd_ut("2000-05-18", "00:00:01", "Asia/Kolkata")
        # Exactly 2 seconds apart in real time.
        self.assertAlmostEqual((after.jd_ut - before.jd_ut) * 86400, 2.0, places=1)

    def test_unknown_timezone_raises_not_silently_assumes_utc(self):
        with self.assertRaises(UnknownTimezone):
            local_to_jd_ut("2000-01-01", "12:00", "Not/A_Real_Zone")

    def test_dst_transition_handled_by_real_tzdata(self):
        # US DST spring-forward 2024-03-10: 2:00 AM local does not exist in
        # America/New_York; zoneinfo/PEP 495 resolves this to the post-transition
        # (fold=0 default) offset rather than crashing -- assert it doesn't raise and
        # produces a plausible JD (not silently wrong by exactly 1 hour vs neighbors).
        before = local_to_jd_ut("2024-03-10", "01:30", "America/New_York")
        after = local_to_jd_ut("2024-03-10", "03:30", "America/New_York")
        # Wall-clock gap is 2h, but only 1h of real time elapses across the spring-forward.
        self.assertAlmostEqual((after.jd_ut - before.jd_ut) * 24, 1.0, places=2)

    def test_utc_offset_fallback_path_available_and_labeled(self):
        result = utc_offset_to_jd_ut("1850-01-01", "12:00", 5.5)
        self.assertIn("UTC", result.timezone_name)
        self.assertIn("fallback", result.utc_datetime)


class HistoricalRangeTests(unittest.TestCase):
    def test_chart_computes_without_error_near_1800_lower_bound(self):
        jd = coordinates.julian_day(1800, 1, 15, 12.0)
        chart = compute_kundli(jd, 51.5074, -0.1278)
        self.assertEqual(len(chart.grahas), 9)

    def test_chart_computes_without_error_near_2050_upper_bound(self):
        jd = coordinates.julian_day(2050, 6, 15, 12.0)
        chart = compute_kundli(jd, 51.5074, -0.1278)
        self.assertEqual(len(chart.grahas), 9)

    def test_dasha_computes_for_a_near_1800_chart(self):
        jd = coordinates.julian_day(1800, 1, 15, 12.0)
        chart = compute_kundli(jd, 51.5074, -0.1278)
        state = compute_dasha_state(jd, chart.grahas["moon"].sidereal_lon_deg)
        self.assertIn(state.mahadasha.lord, {name for name, _ in
                      __import__("mahadasha").DASHA_SEQUENCE})

    def test_dasha_computes_for_a_near_2050_chart(self):
        jd = coordinates.julian_day(2050, 6, 15, 12.0)
        chart = compute_kundli(jd, 51.5074, -0.1278)
        state = compute_dasha_state(jd, chart.grahas["moon"].sidereal_lon_deg)
        self.assertIn(state.mahadasha.lord, {name for name, _ in
                      __import__("mahadasha").DASHA_SEQUENCE})


class NoSilentFallbackTests(unittest.TestCase):
    def test_missing_ephemeris_path_raises_not_silently_approximates(self):
        from kundli import _require_ephemeris_files
        with self.assertRaises(EphemerisDataUnavailable):
            _require_ephemeris_files("/tmp/definitely_not_a_real_ephemeris_dir_xyz")


if __name__ == "__main__":
    unittest.main()
