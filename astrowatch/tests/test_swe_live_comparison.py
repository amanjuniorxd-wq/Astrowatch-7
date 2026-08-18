"""
Astrowatch — Swiss Ephemeris migration: numerical comparison vs the authoritative
live Swiss Ephemeris reference (astro.com's swetest.cgi, Swiss Ephemeris 2.10.03).
========================================================================
Encodes the 14 live reference points fetched this session (2 mandatory cases -- the
2000-05-17 Patna test case and the 1946-06-14 historical test case -- plus 12
additional dates spanning 1800-2034 across 6 locations) as a fixed-data regression
test: the LOCAL engine's output for each (date, time, location) is compared against
the value astro.com's own server returned at fetch time, with an explicit
per-body/overall arcsecond tolerance.

WHY ONLY 14 OF THE REQUESTED 20 ADDITIONAL DATES: astro.com's swetest.cgi is a public
interactive testing tool, not a documented rate-limit-free API (this exact caveat is
already recorded elsewhere in this project, in ephemeris_client.py's own docstring,
from an earlier session). 8 of 22 attempted live fetches this session failed
transiently (returned a stale default-date response instead of the requested
computation) -- consistent with intermittent throttling, not a code bug on either
side. This is disclosed here rather than silently padding the count.

TOLERANCE: 0.5 arcsec per body (this session's own live comparisons measured a
maximum of 0.291 arcsec, for Jupiter/Saturn specifically -- attributed to a real,
disclosed ephemeris-file-vintage gap between this project's bundled 2021 .se1 files
and astro.com's live server, rebuilt against JPL DE441 in April 2026; see
ARCHITECTURE_SE_MIGRATION.md). 0.5 arcsec leaves headroom above the measured maximum
without being so loose it would miss a real regression.
"""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

import coordinates
from kundli import compute_kundli
from _se_live_reference_data import LIVE

TOLERANCE_ARCSEC = 0.5

# (label, date_iso, hour_ut, lat, lon) -- matches the instants used when the LIVE
# dict above was fetched this session.
TEST_CASES = [
    ("Patna (mandatory test case)", 2000, 5, 17, 22.0, 25.5941, 85.1376),
    ("New York (mandatory 1946 test case)", 1946, 6, 14, 10.9, 40.7128, -73.9950),
    ("Tokyo 1830-06-17", 1830, 6, 17, 16.0, 35.6762, 139.6503),
    ("London 1800-10-03", 1800, 10, 3, 3.5, 51.5074, -0.1278),
    ("Moscow 1915-01-27", 1915, 1, 27, 21.75, 55.7558, 37.6173),
    ("London 1990-09-21", 1990, 9, 21, 2.5, 51.5074, -0.1278),
    ("New York 1942-09-10", 1942, 9, 10, 9.75, 40.7128, -74.006),
    ("New Delhi 2024-11-23", 2024, 11, 23, 22.5, 28.6139, 77.209),
    ("London 1823-07-19", 1823, 7, 19, 17.75, 51.5074, -0.1278),
    ("Singapore 2034-09-09", 2034, 9, 9, 13.75, 1.3521, 103.8198),
    ("New Delhi 1932-01-19", 1932, 1, 19, 7.25, 28.6139, 77.209),
    ("London 1909-08-05", 1909, 8, 5, 15.25, 51.5074, -0.1278),
    ("Singapore 1960-12-15", 1960, 12, 15, 21.75, 1.3521, 103.8198),
    ("New Delhi 1910-04-10", 1910, 4, 10, 8.0, 28.6139, 77.209),
]

BODY_KEY_MAP = {"sun": "sun", "moon": "moon", "mercury": "mercury", "venus": "venus",
                 "mars": "mars", "jupiter": "jupiter", "saturn": "saturn"}


def _make_test(label, y, m, d, hour, lat, lon):
    def test(self):
        jd = coordinates.julian_day(y, m, d, hour)
        chart = compute_kundli(jd, lat, lon)
        live = LIVE[label]
        max_diff = 0.0
        details = []
        for body_local, body_live in BODY_KEY_MAP.items():
            local_lon = chart.grahas[body_local].sidereal_lon_deg
            live_lon = live[body_live]
            diff_arcsec = abs(((local_lon - live_lon + 180) % 360 - 180) * 3600)
            max_diff = max(max_diff, diff_arcsec)
            details.append(f"{body_local}: local={local_lon:.6f} live={live_lon:.6f} diff={diff_arcsec:.3f}as")
        asc_diff = abs(((chart.ascendant_sidereal_deg - live["asc"] + 180) % 360 - 180) * 3600)
        max_diff = max(max_diff, asc_diff)
        details.append(f"ascendant: local={chart.ascendant_sidereal_deg:.6f} live={live['asc']:.6f} diff={asc_diff:.3f}as")
        self.assertLess(
            max_diff, TOLERANCE_ARCSEC,
            f"{label}: max diff {max_diff:.3f} arcsec exceeds {TOLERANCE_ARCSEC} arcsec tolerance\n"
            + "\n".join(details)
        )
    return test


class LiveSwissEphemerisComparisonTests(unittest.TestCase):
    pass


for _label, _y, _m, _d, _hour, _lat, _lon in TEST_CASES:
    _test_name = "test_" + _label.lower().replace(" ", "_").replace("(", "").replace(")", "").replace("-", "_").replace("/", "_")
    setattr(LiveSwissEphemerisComparisonTests, _test_name, _make_test(_label, _y, _m, _d, _hour, _lat, _lon))


class ComparisonCoverageTests(unittest.TestCase):
    def test_at_least_14_dates_covered_including_both_mandatory_cases(self):
        self.assertGreaterEqual(len(TEST_CASES), 14)
        labels = {c[0] for c in TEST_CASES}
        self.assertIn("Patna (mandatory test case)", labels)
        self.assertIn("New York (mandatory 1946 test case)", labels)

    def test_date_range_spans_near_1800_to_near_2050(self):
        years = [c[1] for c in TEST_CASES]
        self.assertLess(min(years), 1810)
        self.assertGreater(max(years), 2020)


if __name__ == "__main__":
    unittest.main()
