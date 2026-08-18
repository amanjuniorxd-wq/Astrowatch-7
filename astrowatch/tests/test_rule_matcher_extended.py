"""
Astrowatch — tests for the lunar-pass / eclipse / triplicity detectors added during
the "VALIDATION HARDENING BEFORE BT-002" pass (aspects.py additions + rule_matcher.py
real implementations). See RULE_IMPLEMENTATION_AUDIT.md.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import aspects
import rule_matcher as rm
import rule_registry


class LunarPassClassificationTests(unittest.TestCase):
    def test_north_when_moon_latitude_greater(self):
        r = aspects.classify_lunar_pass(10.0, 2.0, "mars", 12.0, -1.0)
        self.assertTrue(r.in_conjunction_range)
        self.assertEqual(r.side, "north")

    def test_south_when_moon_latitude_lesser(self):
        r = aspects.classify_lunar_pass(10.0, -2.0, "mars", 12.0, 1.0)
        self.assertEqual(r.side, "south")

    def test_not_in_range_outside_orb(self):
        r = aspects.classify_lunar_pass(10.0, 2.0, "mars", 30.0, -1.0)
        self.assertFalse(r.in_conjunction_range)
        self.assertEqual(r.side, "not_in_range")

    def test_equal_latitude_is_not_in_range_not_a_side(self):
        r = aspects.classify_lunar_pass(10.0, 1.0, "mars", 12.0, 1.0)
        self.assertEqual(r.side, "not_in_range")

    def test_orb_boundary_inclusive(self):
        r = aspects.classify_lunar_pass(0.0, 2.0, "mars", 8.0, -1.0, orb_deg=8.0)
        self.assertTrue(r.in_conjunction_range)

    def test_placeholder_orb_matches_grahayuddha_widest_class(self):
        self.assertEqual(aspects.LUNAR_PASS_PLACEHOLDER_ORB_DEG,
                          aspects.GRAHAYUDDHA_PLACEHOLDER_THRESHOLDS_DEG["asavya_apasavya"])


class MatchLunarPassRulesTests(unittest.TestCase):
    def test_matches_bs_18_02_for_mars_north(self):
        matches = rm.match_lunar_pass_rules(10.0, 2.0, {"mars": (12.0, -1.0)})
        ids = {m.rule.rule_id for m in matches}
        self.assertIn("BS-18-02", ids)
        self.assertIn("BS-18-general", ids)

    def test_matches_bs_18_06_for_saturn_north(self):
        matches = rm.match_lunar_pass_rules(10.0, 2.0, {"saturn": (11.0, -1.0)})
        ids = {m.rule.rule_id for m in matches}
        self.assertIn("BS-18-06", ids)

    def test_no_match_when_out_of_range(self):
        matches = rm.match_lunar_pass_rules(10.0, 2.0, {"mars": (200.0, -1.0)})
        self.assertEqual(matches, [])

    def test_wrong_side_planet_specific_rule_does_not_match(self):
        # BS-18-02 requires side="north" specifically for mars.
        matches = rm.match_lunar_pass_rules(10.0, -2.0, {"mars": (12.0, 1.0)})  # moon south
        ids = {m.rule.rule_id for m in matches}
        self.assertNotIn("BS-18-02", ids)
        self.assertIn("BS-18-general", ids)  # general rule matches either side

    def test_multiple_planets_independent(self):
        matches = rm.match_lunar_pass_rules(10.0, 2.0, {
            "mars": (12.0, -1.0), "saturn": (11.0, -1.0), "venus": (200.0, 0.0),
        })
        ids = {m.rule.rule_id for m in matches}
        self.assertIn("BS-18-02", ids)
        self.assertIn("BS-18-06", ids)


class TriplicityLookupTests(unittest.TestCase):
    def test_fire_sign(self):
        info = aspects.triplicity_for_tropical_longitude(15.0)  # Aries
        self.assertEqual(info["sign"], "Aries")
        self.assertEqual(info["triplicity"], "fire")
        self.assertEqual(info["quadrant"], "NW=Europe")

    def test_every_sign_covered(self):
        for lon in range(0, 360, 30):
            info = aspects.triplicity_for_tropical_longitude(float(lon) + 1.0)
            self.assertIn(info["triplicity"], ("fire", "earth", "air", "water"))

    def test_wraps_at_360(self):
        info = aspects.triplicity_for_tropical_longitude(360.5)
        self.assertEqual(info["sign"], "Aries")


class EclipseDetectionTests(unittest.TestCase):
    def test_solar_eclipse_conjunction_low_latitude(self):
        result = aspects.check_for_eclipse(90.0, 90.3, 0.1)
        self.assertEqual(result.kind, "solar")

    def test_lunar_eclipse_opposition_low_latitude(self):
        result = aspects.check_for_eclipse(90.0, 270.2, 0.1)
        self.assertEqual(result.kind, "lunar")

    def test_no_eclipse_high_latitude(self):
        result = aspects.check_for_eclipse(90.0, 90.1, 3.0)
        self.assertEqual(result.kind, "none")

    def test_no_eclipse_far_from_syzygy(self):
        result = aspects.check_for_eclipse(90.0, 150.0, 0.1)
        self.assertEqual(result.kind, "none")

    def test_real_2020_06_21_solar_eclipse_fires(self):
        # Real, documented annular solar eclipse. Verified via backtest/ephemeris_source
        # (see git history / RULE_IMPLEMENTATION_AUDIT.md) that these are the actual
        # locally-computed positions at 2020-06-21 06:00 UTC (near maximum eclipse).
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        import coordinates
        from backtest import ephemeris_source as es
        jd = coordinates.julian_day(2020, 6, 21, 6.0)
        full = es.compute_full_positions(jd)
        result = aspects.check_for_eclipse(
            full.tropical_longitudes_deg["sun"], full.tropical_longitudes_deg["moon"],
            full.tropical_latitudes_deg["moon"],
        )
        self.assertEqual(result.kind, "solar")

    def test_check_and_match_eclipse_returns_pt_ii_6_01(self):
        matches = rm.check_and_match_eclipse(90.0, 90.3, 0.1)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].rule.rule_id, "PT-II-6-01")

    def test_check_and_match_eclipse_empty_when_no_eclipse(self):
        matches = rm.check_and_match_eclipse(90.0, 150.0, 0.1)
        self.assertEqual(matches, [])

    def test_old_match_eclipse_geography_raises(self):
        with self.assertRaises(RuntimeError):
            rm.match_eclipse_geography(1.0)


class RuleRegistryUnmodifiedTests(unittest.TestCase):
    """Confirms this hardening pass did not touch rule_registry.py's DATA."""

    def test_still_19_rules(self):
        self.assertEqual(len(rule_registry.RULES), 19)

    def test_expected_rule_ids_present(self):
        ids = {r.rule_id for r in rule_registry.RULES}
        expected = {
            "BS-17-04", "BS-17-04b", "BS-17-05", "BS-17-05b", "BS-17-25", "BS-17-16",
            "BS-18-02", "BS-18-06", "BS-18-general",
            "BS-19-saturn-year", "BS-19-jupiter-year",
            "BS-20-02", "BS-20-sannipata",
            "BS-42-01a", "BS-42-01b", "BS-42-14", "BS-42-14b",
            "PT-II-3-general", "PT-II-6-01",
        }
        self.assertEqual(ids, expected)


if __name__ == "__main__":
    unittest.main()
