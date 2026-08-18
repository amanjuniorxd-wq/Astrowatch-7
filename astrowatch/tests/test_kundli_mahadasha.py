"""
Astrowatch — tests for kundli.py and mahadasha.py (new modules, built at explicit
user request to support kundli/Mahadasha pattern extraction over HIST-002).
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import coordinates
import rashi_nakshatra as rn
from kundli import compute_kundli, _house_number
from mahadasha import (
    compute_dasha_state, DASHA_SEQUENCE, DASHA_TOTAL_YEARS, NAKSHATRA_STARTING_LORD,
)


class KundliChartTests(unittest.TestCase):
    def setUp(self):
        # 2011-03-11 Tohoku earthquake, real event coordinates/time from HIST-002.
        self.jd = coordinates.julian_day(2011, 3, 11, 5.77)
        self.chart = compute_kundli(self.jd, 38.297, 142.373)

    def test_all_nine_grahas_present(self):
        expected = {"sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "rahu", "ketu"}
        self.assertEqual(set(self.chart.grahas.keys()), expected)

    def test_ketu_exactly_opposite_rahu(self):
        rahu = self.chart.grahas["rahu"].sidereal_lon_deg
        ketu = self.chart.grahas["ketu"].sidereal_lon_deg
        diff = abs((ketu - rahu) % 360.0 - 180.0)
        self.assertLess(diff, 1e-9)

    def test_all_houses_in_range_1_to_12(self):
        for g in self.chart.grahas.values():
            self.assertGreaterEqual(g.house, 1)
            self.assertLessEqual(g.house, 12)

    def test_ascendant_house_is_house_1_by_construction(self):
        # A graha in the same rashi as the Ascendant must be house 1.
        asc_idx = self.chart.ascendant_rashi.rashi_index
        self.assertEqual(_house_number(asc_idx, asc_idx), 1)

    def test_house_wraps_correctly_across_zodiac_boundary(self):
        # Planet one sign behind the Ascendant sign must be house 12.
        asc_idx = self.chart.ascendant_rashi.rashi_index
        behind_idx = (asc_idx - 1) % 12
        self.assertEqual(_house_number(behind_idx, asc_idx), 12)

    def test_sidereal_lon_in_valid_range(self):
        for g in self.chart.grahas.values():
            self.assertGreaterEqual(g.sidereal_lon_deg, 0.0)
            self.assertLess(g.sidereal_lon_deg, 360.0)

    def test_ayanamsha_consistent_across_all_grahas(self):
        # Every graha's tropical->sidereal conversion must use the SAME ayanamsha
        # value (computed once per chart), not a per-planet-recomputed value.
        for g in self.chart.grahas.values():
            implied = (g.tropical_lon_deg - g.sidereal_lon_deg) % 360.0
            self.assertAlmostEqual(implied, self.chart.ayanamsha_deg % 360.0, places=6)

    def test_deterministic_same_input_same_output(self):
        chart2 = compute_kundli(self.jd, 38.297, 142.373)
        self.assertEqual(self.chart.ascendant_rashi.rashi_name, chart2.ascendant_rashi.rashi_name)
        for name in self.chart.grahas:
            self.assertEqual(self.chart.grahas[name].sidereal_lon_deg,
                              chart2.grahas[name].sidereal_lon_deg)

    def test_different_location_changes_ascendant(self):
        chart_other = compute_kundli(self.jd, -33.87, 151.21)  # Sydney, same instant
        # Same instant, different longitude -> different local sidereal time ->
        # near-certainly a different Ascendant (same planetary positions, though).
        self.assertNotEqual(self.chart.ascendant_tropical_deg, chart_other.ascendant_tropical_deg)
        self.assertEqual(self.chart.grahas["sun"].tropical_lon_deg,
                          chart_other.grahas["sun"].tropical_lon_deg)


class MahadashaTests(unittest.TestCase):
    def test_sequence_totals_120_years(self):
        self.assertEqual(DASHA_TOTAL_YEARS, 120)

    def test_nakshatra_lord_table_has_27_entries(self):
        self.assertEqual(len(NAKSHATRA_STARTING_LORD), 27)

    def test_ashwini_starts_ketu(self):
        self.assertEqual(NAKSHATRA_STARTING_LORD[0], "ketu")

    def test_sequence_repeats_three_times(self):
        lords_only = [l for l, _ in DASHA_SEQUENCE]
        self.assertEqual(NAKSHATRA_STARTING_LORD, lords_only * 3)

    def test_dasha_state_for_start_of_nakshatra(self):
        # Exactly at the start of Krittika (nakshatra index 2 -> Sun, per the fixed
        # sequence) -- elapsed should be ~0, balance ~= full lord duration (6y).
        jd = coordinates.julian_day(2020, 1, 1, 0.0)
        krittika_start_lon = 2 * rn.NAKSHATRA_WIDTH_DEG
        state = compute_dasha_state(jd, krittika_start_lon)
        self.assertEqual(state.mahadasha.lord, "sun")
        self.assertAlmostEqual(state.elapsed_in_mahadasha_years, 0.0, places=4)
        self.assertAlmostEqual(state.balance_in_mahadasha_years, 6.0, places=4)

    def test_dasha_state_at_end_of_nakshatra_near_full_elapsed(self):
        jd = coordinates.julian_day(2020, 1, 1, 0.0)
        krittika_end_lon = 3 * rn.NAKSHATRA_WIDTH_DEG - 0.0001
        state = compute_dasha_state(jd, krittika_end_lon)
        self.assertEqual(state.mahadasha.lord, "sun")
        self.assertAlmostEqual(state.elapsed_in_mahadasha_years, 6.0, places=2)

    def test_antardasha_starts_with_mahadasha_lord(self):
        jd = coordinates.julian_day(2020, 1, 1, 0.0)
        krittika_start_lon = 2 * rn.NAKSHATRA_WIDTH_DEG
        state = compute_dasha_state(jd, krittika_start_lon)
        self.assertEqual(state.mahadasha.lord, state.antardasha.lord)

    def test_antardasha_within_mahadasha_bounds(self):
        jd = coordinates.julian_day(2020, 6, 15, 12.0)
        state = compute_dasha_state(jd, 123.456)
        self.assertGreaterEqual(state.antardasha.start_jd_ut, state.mahadasha.start_jd_ut - 1e-6)
        self.assertLessEqual(state.antardasha.end_jd_ut, state.mahadasha.end_jd_ut + 1e-6)

    def test_deterministic(self):
        jd = coordinates.julian_day(2020, 6, 15, 12.0)
        s1 = compute_dasha_state(jd, 200.5)
        s2 = compute_dasha_state(jd, 200.5)
        self.assertEqual(s1.mahadasha.lord, s2.mahadasha.lord)
        self.assertEqual(s1.antardasha.lord, s2.antardasha.lord)
        self.assertEqual(s1.elapsed_in_mahadasha_years, s2.elapsed_in_mahadasha_years)

    def test_all_27_nakshatras_produce_valid_lord(self):
        valid_lords = {name for name, _ in DASHA_SEQUENCE}
        jd = coordinates.julian_day(2020, 1, 1, 0.0)
        for idx in range(27):
            lon = idx * rn.NAKSHATRA_WIDTH_DEG + 1.0
            state = compute_dasha_state(jd, lon)
            self.assertIn(state.mahadasha.lord, valid_lords)


if __name__ == "__main__":
    unittest.main()
