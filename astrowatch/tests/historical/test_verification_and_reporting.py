import json
import os
import sys
import tempfile
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO_ROOT)

from historical import database, models, repository  # noqa: E402
from historical.ingestion.usgs import USGSEarthquakeAdapter  # noqa: E402
from historical.ingestion.noaa import NOAATsunamiAdapter  # noqa: E402

sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
import generate_historical_quality_report as report_mod  # noqa: E402


# ---------------------------------------------------------------------------
# Raw-source normalization tests -- using small inline fixtures, not network,
# so these run deterministically regardless of live source availability.
# ---------------------------------------------------------------------------

class USGSAdapterNormalizationTests(unittest.TestCase):
    FIXTURE = {
        "features": [{
            "type": "Feature",
            "properties": {"mag": 9.1, "place": "Test Place, Testland", "time": 1104022733450,
                            "tsunami": 1, "magType": "mw"},
            "geometry": {"type": "Point", "coordinates": [95.982, 3.295, 30]},
            "id": "test123",
        }]
    }

    def test_parse_extracts_features(self):
        a = USGSEarthquakeAdapter()
        records = a.parse(json.dumps(self.FIXTURE))
        self.assertEqual(len(records), 1)

    def test_normalize_produces_exact_confidence_fields(self):
        a = USGSEarthquakeAdapter()
        records = a.normalize(a.parse(json.dumps(self.FIXTURE)))
        rec = records[0]
        self.assertEqual(rec.date_confidence, "EXACT")
        self.assertEqual(rec.time_confidence, "EXACT")
        self.assertEqual(rec.location_confidence, "EXACT")
        self.assertEqual(rec.source_quality_tier, 1)
        self.assertEqual(rec.start_date, "2004-12-26")  # real conversion from the epoch ms above
        self.assertAlmostEqual(rec.latitude, 3.295)
        self.assertAlmostEqual(rec.longitude, 95.982)
        self.assertEqual(rec.source_record_id, "test123")

    def test_retrieve_raises_documented_error_not_silent_failure(self):
        a = USGSEarthquakeAdapter()
        with self.assertRaises(RuntimeError):
            a.retrieve()


class NOAAAdapterNormalizationTests(unittest.TestCase):
    FIXTURE = {"items": [{
        "id": 9999, "year": 1883, "month": 8, "day": 27, "hour": 2, "minute": 59,
        "country": "INDONESIA", "locationName": "KRAKATAU", "latitude": -6.102,
        "longitude": 105.423, "maxWaterHeight": 41, "deathsTotal": 36417,
        "oceanicTsunami": True,
    }]}

    def test_normalize_produces_real_death_toll_in_description(self):
        a = NOAATsunamiAdapter()
        records = a.normalize(a.parse(json.dumps(self.FIXTURE)))
        rec = records[0]
        self.assertIn("36,417", rec.description)
        self.assertEqual(rec.event_subtype, "tsunami")
        self.assertEqual(rec.start_date, "1883-08-27")
        self.assertEqual(rec.start_time, "02:59")

    def test_missing_time_falls_back_to_unknown_not_fabricated(self):
        fixture = {"items": [{
            "id": 1, "year": 1900, "month": 1, "day": 1, "country": "X",
            "locationName": "Y", "latitude": 0.0, "longitude": 0.0,
            "maxWaterHeight": 1, "deathsTotal": 1,
        }]}
        a = NOAATsunamiAdapter()
        rec = a.normalize(a.parse(json.dumps(fixture)))[0]
        self.assertIsNone(rec.start_time)
        self.assertEqual(rec.time_confidence, "UNKNOWN")


# ---------------------------------------------------------------------------
# Verification workflow / source-tier / multi-source-independence tests
# ---------------------------------------------------------------------------

class VerificationWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        os.remove(self.tmp.name)
        self.conn = database.initialize_db(self.tmp.name)
        repository.create_dataset_version(self.conn, models.DatasetVersion(
            version_id="V1", created_date="2026-08-14"))
        repository.insert_source(self.conn, models.Source(
            "SRC-A", "Source A", "Org A", "encyclopedia", 3, "http://a", "2026-08-14", "c", None))
        repository.insert_source(self.conn, models.Source(
            "SRC-B", "Source B", "Org B", "encyclopedia", 3, "http://b", "2026-08-14", "c", None))
        self.conn.commit()

    def tearDown(self):
        self.conn.close()
        if os.path.exists(self.tmp.name):
            os.remove(self.tmp.name)

    def _base_event(self, **overrides):
        base = dict(
            event_id="E1", canonical_event_id="E1", event_name="n", event_type="MILITARY",
            event_subtype="war_start", start_date="1900-01-01", date_confidence="EXACT",
            time_confidence="UNKNOWN", location_confidence="COUNTRY", location_precision="COUNTRY",
            description="d", source_quality_tier=3, verification_status="MULTI_SOURCE_CONFIRMED",
            dataset_version="V1", created_at="x", updated_at="x", verification_count=2,
        )
        base.update(overrides)
        return models.Event(**base)

    def test_multi_source_independence_requires_two_distinct_source_ids(self):
        repository.insert_event(self.conn, self._base_event())
        repository.insert_event_source(self.conn, models.EventSource("E1", "SRC-A", "CONFIRMED", created_at="x"))
        repository.insert_event_source(self.conn, models.EventSource("E1", "SRC-B", "CONFIRMED", created_at="x"))
        self.conn.commit()
        links = repository.get_event_sources(self.conn, "E1")
        distinct_orgs = {l["organization"] for l in links}
        self.assertEqual(len(links), 2)
        self.assertEqual(len(distinct_orgs), 2, "two links to the same organization would not be independent")

    def test_duplicate_source_link_rejected_by_unique_constraint(self):
        repository.insert_event(self.conn, self._base_event())
        repository.insert_event_source(self.conn, models.EventSource("E1", "SRC-A", "CONFIRMED", created_at="x"))
        self.conn.commit()
        with self.assertRaises(Exception):
            repository.insert_event_source(self.conn, models.EventSource("E1", "SRC-A", "CONFIRMED", created_at="x"))

    def test_all_four_source_tiers_accepted(self):
        for i, tier in enumerate((1, 2, 3, 4)):
            repository.insert_source(self.conn, models.Source(
                f"SRC-TIER-{tier}", f"s{tier}", "o", "type", tier, None, None, None, None))
        self.conn.commit()  # should not raise

    def test_invalid_tier_rejected(self):
        with self.assertRaises(Exception):
            repository.insert_source(self.conn, models.Source(
                "SRC-BAD-TIER", "s", "o", "type", 5, None, None, None, None))
            self.conn.commit()


# ---------------------------------------------------------------------------
# Geographic / temporal reporting tests -- the quality-report generator's own
# bucketing logic, exercised directly (not just "did the script run").
# ---------------------------------------------------------------------------

class ReportingBucketTests(unittest.TestCase):
    def test_decade_bucketing(self):
        self.assertEqual(report_mod.decade(1914), "1910s")
        self.assertEqual(report_mod.decade(2004), "2000s")

    def test_century_bucketing(self):
        self.assertEqual(report_mod.century(1914), "20th century")
        self.assertEqual(report_mod.century(2004), "21st century")

    def test_period_bucketing_covers_ancient_to_modern(self):
        self.assertEqual(report_mod.period_bucket(79), "Ancient (pre-500 CE)")
        self.assertEqual(report_mod.period_bucket(1347), "Medieval (500-1499)")
        self.assertEqual(report_mod.period_bucket(1700), "Early modern (1500-1799)")
        self.assertEqual(report_mod.period_bucket(1850), "19th century")
        self.assertEqual(report_mod.period_bucket(1950), "20th century")
        self.assertEqual(report_mod.period_bucket(2020), "21st century")


# ---------------------------------------------------------------------------
# manual_review.csv format / reproducibility tests
# ---------------------------------------------------------------------------

class ManualReviewFormatTests(unittest.TestCase):
    def test_manual_review_csv_has_expected_header_if_present(self):
        path = os.path.join(REPO_ROOT, "manual_review.csv")
        if not os.path.exists(path):
            self.skipTest("manual_review.csv not generated yet in this environment")
        with open(path) as f:
            header = f.readline().strip().split(",")
        self.assertEqual(
            header,
            ["event_id", "reason", "current_value", "recommended_action", "source", "status"],
        )

    def test_dedup_scan_is_deterministic_across_repeated_calls(self):
        from historical import deduplication
        events = [
            {"event_id": "E1", "event_name": "Battle of X", "event_type": "MILITARY",
             "event_subtype": "battle", "start_date": "1900-01-01", "country_code": "AAA",
             "region": "R", "location_name": "L", "description": "a battle happened"},
            {"event_id": "E2", "event_name": "Battle of X", "event_type": "MILITARY",
             "event_subtype": "battle", "start_date": "1900-01-02", "country_code": "AAA",
             "region": "R", "location_name": "L", "description": "a battle happened here too"},
        ]
        r1 = deduplication.find_duplicate_candidates(events)
        r2 = deduplication.find_duplicate_candidates(events)
        self.assertEqual([(c.event_id_a, c.event_id_b, c.confidence) for c in r1],
                          [(c.event_id_a, c.event_id_b, c.confidence) for c in r2])


if __name__ == "__main__":
    unittest.main(verbosity=2)
