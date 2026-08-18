"""
Astrowatch — boundary tests for rashi_nakshatra.py (item 10: boundary conditions)
==================================================================================
STATUS: written as real unittest code, NOT executed this session (same sandbox/agent-
isolation unavailability as everything else -- see ayanamsha.py EXECUTION STATUS).
Every expected value below was hand-traced against the fixed-width-bin arithmetic in
rashi_nakshatra.py before being committed.

Covers, per instruction: 0/30-degree Rāśi boundaries, Nakshatra boundaries, 360->0
wraparound, and planetary positions near boundaries (via integration with
ayanamsha.tropical_to_sidereal_lahiri()).
"""

import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import ayanamsha  # noqa: E402
import rashi_nakshatra as rn  # noqa: E402


class TestRashiBoundaries(unittest.TestCase):
    def test_zero_degrees_is_start_of_mesha(self):
        p = rn.rashi_for_longitude(0.0)
        self.assertEqual(p.rashi_name, "Mesha")
        self.assertEqual(p.rashi_index, 0)
        self.assertAlmostEqual(p.degree_in_rashi, 0.0)

    def test_just_under_thirty_stays_in_mesha(self):
        p = rn.rashi_for_longitude(29.999999999)
        self.assertEqual(p.rashi_name, "Mesha")
        self.assertAlmostEqual(p.degree_in_rashi, 29.999999999, places=6)

    def test_exactly_thirty_rolls_to_vrishabha(self):
        p = rn.rashi_for_longitude(30.0)
        self.assertEqual(p.rashi_name, "Vrishabha")
        self.assertEqual(p.rashi_index, 1)
        self.assertAlmostEqual(p.degree_in_rashi, 0.0)

    def test_last_sign_boundary_meena(self):
        # 330 deg = start of the 12th sign, Meena (Pisces)
        p = rn.rashi_for_longitude(330.0)
        self.assertEqual(p.rashi_name, "Meena")
        self.assertEqual(p.rashi_index, 11)

    def test_all_twelve_signs_reachable_and_correctly_ordered(self):
        expected = rn.RASHI_NAMES
        for i, name in enumerate(expected):
            p = rn.rashi_for_longitude(i * 30.0 + 1.0)  # 1 deg into each sign
            self.assertEqual(p.rashi_name, name, f"sign index {i} should be {name}")


class TestNakshatraBoundaries(unittest.TestCase):
    def test_zero_degrees_is_start_of_ashwini(self):
        p = rn.nakshatra_for_longitude(0.0)
        self.assertEqual(p.nakshatra_name, "Ashwini")
        self.assertEqual(p.nakshatra_index, 0)
        self.assertEqual(p.pada, 1)

    def test_just_under_one_nakshatra_width_stays_in_ashwini(self):
        p = rn.nakshatra_for_longitude(13.333332)
        self.assertEqual(p.nakshatra_name, "Ashwini")

    def test_exactly_one_nakshatra_width_rolls_to_bharani(self):
        p = rn.nakshatra_for_longitude(rn.NAKSHATRA_WIDTH_DEG)
        self.assertEqual(p.nakshatra_name, "Bharani")
        self.assertEqual(p.nakshatra_index, 1)
        self.assertAlmostEqual(p.degree_in_nakshatra, 0.0, places=9)

    def test_all_27_nakshatras_reachable_and_correctly_ordered(self):
        for i, name in enumerate(rn.NAKSHATRA_NAMES):
            lon = i * rn.NAKSHATRA_WIDTH_DEG + 0.5  # half a degree into each
            p = rn.nakshatra_for_longitude(lon)
            self.assertEqual(p.nakshatra_name, name, f"nakshatra index {i} should be {name}")

    def test_pada_boundaries_within_a_nakshatra(self):
        # First nakshatra (Ashwini), width 13.3333..., 4 padas of 3.3333... each.
        # Uses points well INSIDE each pada bin (not exact multiplied boundaries --
        # 360/27 is not exactly representable in binary floating point, so asserting
        # behavior at a compounded-multiplication exact tie would test float rounding
        # behavior rather than the classification logic itself). The one true boundary
        # asserted directly (PADA_WIDTH_DEG itself, not a multiple of it) is safe since
        # it's the same stored constant used internally by the comparison.
        self.assertEqual(rn.nakshatra_for_longitude(0.0).pada, 1)
        self.assertEqual(rn.nakshatra_for_longitude(1.5).pada, 1)
        self.assertEqual(rn.nakshatra_for_longitude(rn.PADA_WIDTH_DEG).pada, 2)
        self.assertEqual(rn.nakshatra_for_longitude(5.0).pada, 2)
        self.assertEqual(rn.nakshatra_for_longitude(8.0).pada, 3)
        self.assertEqual(rn.nakshatra_for_longitude(11.0).pada, 4)
        # Just before the nakshatra ends -- still pada 4, not rolled into next nakshatra
        just_before_next = rn.NAKSHATRA_WIDTH_DEG - 0.001
        p = rn.nakshatra_for_longitude(just_before_next)
        self.assertEqual(p.nakshatra_name, "Ashwini")
        self.assertEqual(p.pada, 4)

    def test_mula_nakshatra_index_18_matches_bs17_16_earthquake_rule_region(self):
        # Sanity check only -- confirms the reference table's ordering is the standard
        # one (Mula = 19th nakshatra, index 18), not asserting anything about
        # rule_registry.py's BS-17-16, which stays untouched.
        self.assertEqual(rn.NAKSHATRA_NAMES[18], "Mula")


class TestWraparound(unittest.TestCase):
    def test_exactly_360_wraps_to_zero(self):
        p = rn.rashi_for_longitude(360.0)
        self.assertEqual(p.rashi_name, "Mesha")
        self.assertAlmostEqual(p.degree_in_rashi, 0.0)

    def test_value_above_360_wraps_correctly(self):
        p = rn.rashi_for_longitude(370.0)
        self.assertEqual(p.rashi_name, "Mesha")
        self.assertAlmostEqual(p.degree_in_rashi, 10.0)

    def test_small_negative_value_wraps_to_end_of_meena(self):
        p = rn.rashi_for_longitude(-0.0001)
        self.assertEqual(p.rashi_name, "Meena")
        self.assertAlmostEqual(p.degree_in_rashi, 29.9999, places=4)

    def test_large_negative_value_wraps_correctly(self):
        # -30 deg should land exactly on the Meena/Mesha boundary from below, i.e. at
        # the START of the last sign (330 deg), not somewhere else.
        p = rn.rashi_for_longitude(-30.0)
        self.assertEqual(p.rashi_name, "Meena")
        self.assertAlmostEqual(p.degree_in_rashi, 0.0)

    def test_float_noise_just_under_360_snaps_to_zero(self):
        # Simulates the kind of near-360 float noise real subtraction can produce
        # (e.g. 383.853222 - 23.853222 computed with floating point rounding).
        noisy = 360.0 - 1e-13
        p = rn.rashi_for_longitude(noisy)
        self.assertEqual(p.rashi_name, "Mesha",
                          "float noise infinitesimally under 360 should snap to 0, not "
                          "be misclassified as the last few billionths of a degree of "
                          "the last sign")

    def test_nakshatra_wraparound_consistent_with_rashi_wraparound(self):
        p = rn.nakshatra_for_longitude(360.0)
        self.assertEqual(p.nakshatra_name, "Ashwini")
        p2 = rn.nakshatra_for_longitude(-0.0001)
        self.assertEqual(p2.nakshatra_name, "Revati")  # last of the 27


class TestIntegrationNearBoundaryWithSiderealTransform(unittest.TestCase):
    """End-to-end: tropical longitude -> ayanamsha subtraction -> rashi/nakshatra
    classification, specifically constructed to land ON or NEAR a boundary.

    IMPORTANT: ayanamsha.tropical_to_sidereal_lahiri() calls the network-first
    lahiri_ayanamsha_deg() internally. A unit test must not depend on live network
    access (flaky, slow, won't work offline) -- so every test here forces the
    deterministic fallback path via mock, exactly like TestFallbackWiring in
    test_ayanamsha.py, rather than letting it hit the real network."""

    def setUp(self):
        self._patcher = mock.patch(
            "ayanamsha.fetch_live_swisseph_lahiri_ayanamsha_deg",
            side_effect=ayanamsha.LiveSwissEphemerisUnavailable("forced for test determinism"),
        )
        self._patcher.start()
        self.addCleanup(self._patcher.stop)

        self.ayanamsha_j2000 = ayanamsha._lahiri_ayanamsha_deg_linear_fallback(
            ayanamsha.ANCHOR_J2000_JD
        ).ayanamsha_deg
        self.assertAlmostEqual(self.ayanamsha_j2000, 23.853222, places=6)

    def test_tropical_longitude_equal_to_ayanamsha_lands_on_mesha_zero(self):
        # tropical - ayanamsha = 0 exactly -> sidereal 0 deg -> start of Mesha/Ashwini
        tropical_lon = self.ayanamsha_j2000
        sidereal_lon = ayanamsha.tropical_to_sidereal_lahiri(
            tropical_lon, ayanamsha.ANCHOR_J2000_JD
        )
        self.assertAlmostEqual(sidereal_lon, 0.0, places=6)
        rashi = rn.rashi_for_longitude(sidereal_lon)
        nakshatra = rn.nakshatra_for_longitude(sidereal_lon)
        self.assertEqual(rashi.rashi_name, "Mesha")
        self.assertEqual(nakshatra.nakshatra_name, "Ashwini")

    def test_tropical_longitude_just_under_ayanamsha_wraps_to_meena(self):
        # tropical slightly LESS than ayanamsha -> sidereal goes negative before
        # wrapping -> should land at the very end of Meena/Revati, not error out.
        tropical_lon = self.ayanamsha_j2000 - 0.0001
        sidereal_lon = ayanamsha.tropical_to_sidereal_lahiri(
            tropical_lon, ayanamsha.ANCHOR_J2000_JD
        )
        self.assertGreater(sidereal_lon, 359.9)
        rashi = rn.rashi_for_longitude(sidereal_lon)
        self.assertEqual(rashi.rashi_name, "Meena")

    def test_tropical_longitude_at_ayanamsha_plus_30_lands_on_vrishabha_zero(self):
        tropical_lon = self.ayanamsha_j2000 + 30.0
        sidereal_lon = ayanamsha.tropical_to_sidereal_lahiri(
            tropical_lon, ayanamsha.ANCHOR_J2000_JD
        )
        self.assertAlmostEqual(sidereal_lon, 30.0, places=6)
        rashi = rn.rashi_for_longitude(sidereal_lon)
        self.assertEqual(rashi.rashi_name, "Vrishabha")


if __name__ == "__main__":
    unittest.main(verbosity=2)
