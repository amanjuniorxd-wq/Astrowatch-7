import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from historical import controls, database, deduplication, models, repository, versioning  # noqa: E402


class DeduplicationTests(unittest.TestCase):
    def test_identical_name_same_day_flagged_high(self):
        events = [
            {"event_id": "E1", "event_name": "Battle of X", "event_type": "MILITARY",
             "event_subtype": "battle", "start_date": "1900-01-01", "country_code": "AAA"},
            {"event_id": "E2", "event_name": "Battle of X", "event_type": "MILITARY",
             "event_subtype": "battle", "start_date": "1900-01-02", "country_code": "AAA"},
        ]
        candidates = deduplication.find_duplicate_candidates(events)
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].confidence, "HIGH")

    def test_different_type_never_flagged(self):
        events = [
            {"event_id": "E1", "event_name": "Same Name", "event_type": "MILITARY",
             "event_subtype": "battle", "start_date": "1900-01-01", "country_code": "AAA"},
            {"event_id": "E2", "event_name": "Same Name", "event_type": "ECONOMIC",
             "event_subtype": "market_crash", "start_date": "1900-01-01", "country_code": "AAA"},
        ]
        candidates = deduplication.find_duplicate_candidates(events)
        self.assertEqual(len(candidates), 0)

    def test_clearly_distinct_events_not_flagged(self):
        events = [
            {"event_id": "E1", "event_name": "World War I begins", "event_type": "MILITARY",
             "event_subtype": "war_start", "start_date": "1914-07-28", "country_code": "AUT"},
            {"event_id": "E2", "event_name": "World War II begins", "event_type": "MILITARY",
             "event_subtype": "war_start", "start_date": "1939-09-01", "country_code": "POL"},
        ]
        candidates = deduplication.find_duplicate_candidates(events)
        self.assertEqual(len(candidates), 0)

    def test_no_auto_merge_ever_happens(self):
        # find_duplicate_candidates must never mutate its input or merge anything --
        # it only returns candidates for a human to review.
        events = [
            {"event_id": "E1", "event_name": "X", "event_type": "MILITARY",
             "event_subtype": "battle", "start_date": "1900-01-01", "country_code": "AAA"},
            {"event_id": "E2", "event_name": "X", "event_type": "MILITARY",
             "event_subtype": "battle", "start_date": "1900-01-01", "country_code": "AAA"},
        ]
        before = [dict(e) for e in events]
        deduplication.find_duplicate_candidates(events)
        self.assertEqual(events, before)


class ControlDateTests(unittest.TestCase):
    def test_reproducible_with_same_seed(self):
        a = controls.sample_random_dates("2000-01-01", "2010-01-01", 20, seed=7)
        b = controls.sample_random_dates("2000-01-01", "2010-01-01", 20, seed=7)
        self.assertEqual(a, b)

    def test_different_seed_gives_different_sample(self):
        a = controls.sample_random_dates("2000-01-01", "2010-01-01", 20, seed=7)
        b = controls.sample_random_dates("2000-01-01", "2010-01-01", 20, seed=8)
        self.assertNotEqual(a, b)

    def test_dates_within_window(self):
        dates = controls.sample_random_dates("2000-01-01", "2001-01-01", 50, seed=1)
        self.assertTrue(all("2000" in d or d == "2001-01-01" for d in dates))

    def test_build_random_controls_records_method_and_seed(self):
        cds = controls.build_random_controls(
            "2000-01-01", "2001-01-01", 5, seed=42, region="GLOBAL",
            dataset_version="V1", selection_timestamp="2026-08-14T00:00:00",
        )
        self.assertEqual(len(cds), 5)
        self.assertTrue(all(c.sampling_method == "RANDOM_DATE" for c in cds))
        self.assertTrue(all(c.seed == 42 for c in cds))

    def test_invalid_window_raises(self):
        with self.assertRaises(ValueError):
            controls.sample_random_dates("2010-01-01", "2000-01-01", 5, seed=1)


class VersioningTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        os.remove(self.tmp.name)
        self.conn = database.initialize_db(self.tmp.name)
        repository.create_dataset_version(self.conn, models.DatasetVersion(
            version_id="V1", created_date="2026-08-14"))
        repository.insert_source(self.conn, models.Source(
            "SRC-1", "s", "o", "encyclopedia", 3, "http://x", "2026-08-14", "c", None))
        repository.insert_event(self.conn, models.Event(
            event_id="E1", canonical_event_id="E1", event_name="n", event_type="MILITARY",
            event_subtype="war_start", start_date="1900-01-01", date_confidence="EXACT",
            time_confidence="UNKNOWN", location_confidence="COUNTRY", location_precision="COUNTRY",
            description="d", source_quality_tier=3, verification_status="SINGLE_SOURCE",
            dataset_version="V1", created_at="x", updated_at="x",
        ))
        repository.insert_event_source(self.conn, models.EventSource(
            "E1", "SRC-1", "CONFIRMED", created_at="x"))
        self.conn.commit()

    def tearDown(self):
        self.conn.close()
        if os.path.exists(self.tmp.name):
            os.remove(self.tmp.name)

    def test_freeze_sets_counts_and_checksum(self):
        result = versioning.freeze_dataset_version(self.conn, self.tmp.name, "V1", "test limits")
        self.assertEqual(result["event_count"], 1)
        self.assertEqual(result["source_count"], 1)
        self.assertIsNotNone(result["checksum_sha256"])

    def test_sidecar_checksum_file_matches_actual_file_after_freeze(self):
        # This is the real regression test for the self-reference bug found this
        # pass (see the long comment in historical/versioning.py): the checksum
        # stored INSIDE the db can never equal the file's true final bytes, because
        # writing the checksum changes the file. The sidecar file, computed AFTER
        # all writes finish, is the one that must actually match.
        versioning.freeze_dataset_version(self.conn, self.tmp.name, "V1", "test limits")
        result = versioning.validate_frozen_checksum(self.tmp.name)
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["recorded"], result["current"])

    def test_in_db_checksum_column_deliberately_left_null(self):
        # Documents the design choice directly: a checksum of the file cannot be
        # stored correctly INSIDE that same file (self-reference -- see the long
        # comment in historical/versioning.py). The column stays NULL; the sidecar
        # file (asserted in test_sidecar_checksum_file_matches_actual_file_after_freeze)
        # is the sole authoritative value.
        versioning.freeze_dataset_version(self.conn, self.tmp.name, "V1", "test limits")
        stored = repository.get_dataset_version(self.conn, "V1")["checksum_sha256"]
        self.assertIsNone(stored)

    def test_frozen_flag_set_in_db(self):
        versioning.freeze_dataset_version(self.conn, self.tmp.name, "V1", "test limits")
        row = repository.get_dataset_version(self.conn, "V1")
        self.assertEqual(row["frozen"], 1)

    def test_edit_after_freeze_rejected(self):
        versioning.freeze_dataset_version(self.conn, self.tmp.name, "V1", "test limits")
        with self.assertRaises(Exception):
            self.conn.execute("UPDATE events SET event_name='changed' WHERE event_id='E1'")

    def test_delete_after_freeze_rejected(self):
        versioning.freeze_dataset_version(self.conn, self.tmp.name, "V1", "test limits")
        with self.assertRaises(Exception):
            self.conn.execute("DELETE FROM events WHERE event_id='E1'")

    def test_checksum_changes_if_db_content_differs(self):
        c1 = versioning.compute_db_checksum(self.tmp.name)
        repository.insert_source(self.conn, models.Source(
            "SRC-2", "s2", "o", "encyclopedia", 3, "http://y", "2026-08-14", "c", None))
        self.conn.commit()
        c2 = versioning.compute_db_checksum(self.tmp.name)
        self.assertNotEqual(c1, c2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
