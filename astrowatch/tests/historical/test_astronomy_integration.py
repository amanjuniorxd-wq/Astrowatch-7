"""
Astrowatch — integration test: historical_events.db -> existing astronomy pipeline.

Proves the READ pathway (spec item 28) actually works: pull an event's date from
historical_events.db via historical.repository.get_events(), feed ONLY its
date/time/location into the pre-existing (unmodified) astronomy modules
(ayanamsha.py, rashi_nakshatra.py, panchang.py, rule_registry.py), and confirm it
produces real output -- without ever importing astrology code INTO historical/,
and without modifying any astronomical methodology to make this pass (spec item 3/28).

Uses the deterministic ayanamsha fallback path (allow_fallback=True, the default)
rather than the live Swiss Ephemeris query, since this sandbox cannot reach
astro.com (see docs/ASTRONOMY_VALIDATION_REPORT.md Phase 11) -- this keeps the test
itself deterministic and network-independent, which is what you want in a test suite
regardless of the network situation.
"""
import os
import sys
import tempfile
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO_ROOT)

from historical import database, models, repository  # noqa: E402
import ayanamsha  # noqa: E402
import coordinates  # noqa: E402
import rashi_nakshatra  # noqa: E402
import rule_registry  # noqa: E402


class HistoricalToAstronomyIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        os.remove(self.tmp.name)
        self.conn = database.initialize_db(self.tmp.name)
        repository.create_dataset_version(self.conn, models.DatasetVersion(
            version_id="V1", created_date="2026-08-14"))
        repository.insert_source(self.conn, models.Source(
            "SRC-1", "s", "o", "encyclopedia", 3, "http://x", "2026-08-14", "c", None))
        # A real historical event, with a real date -- Hiroshima, as in the actual
        # pilot dataset (see data/curated_events.py).
        repository.insert_event(self.conn, models.Event(
            event_id="EVENT-1945-HIROSHIMA", canonical_event_id="EVENT-1945-HIROSHIMA",
            event_name="Atomic bombing of Hiroshima", event_type="SCIENCE_TECHNOLOGY",
            event_subtype="nuclear_event", start_date="1945-08-06",
            date_confidence="EXACT", time_confidence="EXACT", start_time="08:15",
            timezone="Asia/Tokyo", location_confidence="EXACT", location_precision="EXACT",
            latitude=34.3853, longitude=132.4553, location_name="Hiroshima",
            country="Japan", country_code="JPN", region="Asia",
            description="d", source_quality_tier=3, verification_status="UNVERIFIED",
            dataset_version="V1", created_at="x", updated_at="x",
        ))
        repository.insert_event_source(self.conn, models.EventSource(
            "EVENT-1945-HIROSHIMA", "SRC-1", "CONFIRMED", created_at="x"))
        self.conn.commit()

    def tearDown(self):
        self.conn.close()
        if os.path.exists(self.tmp.name):
            os.remove(self.tmp.name)

    def test_event_date_flows_into_ayanamsha_engine(self):
        rows = repository.get_events(self.conn, category="SCIENCE_TECHNOLOGY")
        self.assertEqual(len(rows), 1)
        event = rows[0]
        year, month, day = (int(x) for x in event["start_date"].split("-"))

        # historical_events.db never computes this -- it only supplies the date.
        jd = coordinates.julian_day(year, month, day, hour=12.0)
        result = ayanamsha.lahiri_ayanamsha_deg(jd)  # real call into the unmodified engine
        self.assertIsInstance(result.ayanamsha_deg, float)
        self.assertGreater(result.ayanamsha_deg, 0.0)
        self.assertLess(result.ayanamsha_deg, 30.0)

    def test_event_date_flows_into_rashi_nakshatra_classification(self):
        rows = repository.get_events(self.conn, category="SCIENCE_TECHNOLOGY")
        event = rows[0]
        year, month, day = (int(x) for x in event["start_date"].split("-"))
        jd = coordinates.julian_day(year, month, day, hour=12.0)
        ayanamsha_result = ayanamsha.lahiri_ayanamsha_deg(jd)
        # arbitrary tropical longitude for this smoke test -- the point is that the
        # PIPELINE (historical date -> ayanamsha -> rashi/nakshatra) executes, not
        # that this specific longitude is astronomically meaningful here.
        sidereal_lon = ayanamsha.tropical_to_sidereal_lahiri(100.0, jd)
        rashi = rashi_nakshatra.rashi_for_longitude(sidereal_lon)
        nak = rashi_nakshatra.nakshatra_for_longitude(sidereal_lon)
        self.assertIn(rashi.rashi_name, rashi_nakshatra.RASHI_NAMES)
        self.assertIn(nak.nakshatra_name, rashi_nakshatra.NAKSHATRA_NAMES)

    def test_rule_registry_still_untouched_and_functional(self):
        # confirm the rule registry (never modified by this pass) still loads
        # correctly and the historically-unresolved safeguard is still intact,
        # exercised from within a test that also touches historical_events.db --
        # proving the two systems coexist without interfering with each other.
        self.assertGreater(len(rule_registry.RULES), 0)
        unresolved_ids = [r.rule_id for r in rule_registry.RULES if r.zodiac_requirement == "sidereal_unresolved"]
        self.assertIn("BS-19-saturn-year", unresolved_ids)
        self.assertIn("BS-20-02", unresolved_ids)
        self.assertIn("BS-42-01a", unresolved_ids)

    def test_historical_repository_never_mutates_on_get_events(self):
        before = repository.get_events(self.conn)
        _ = ayanamsha.lahiri_ayanamsha_deg(2451545.0)  # exercise the astronomy side
        after = repository.get_events(self.conn)
        self.assertEqual(
            [dict(r) for r in before], [dict(r) for r in after],
            "get_events() must be read-only regardless of what the astronomy side does",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
