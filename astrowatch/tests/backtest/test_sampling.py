import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import historical.database as hdb
from backtest import sampler, controls

HIST_DB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                        "historical_events_v2.db")


class SamplingDeterminismTests(unittest.TestCase):
    def setUp(self):
        self.conn = hdb.connect(HIST_DB)

    def tearDown(self):
        self.conn.close()

    def test_full_dataset_returns_all_hist002_events(self):
        cases = sampler.sample_full_dataset(self.conn, "ASTROWATCH-HIST-002", "EXP-X")
        self.assertEqual(len(cases), 140)
        self.assertTrue(all(c.case_kind == "EVENT" for c in cases))
        self.assertTrue(all(c.test_case_id.startswith("TC-EVENT-") for c in cases))

    def test_full_dataset_dataset_version_is_correct(self):
        cases = sampler.sample_full_dataset(self.conn, "ASTROWATCH-HIST-002", "EXP-X")
        ids = {c.source_event_id for c in cases}
        rows = self.conn.execute(
            "SELECT event_id FROM events WHERE dataset_version = 'ASTROWATCH-HIST-002'"
        ).fetchall()
        self.assertEqual(ids, {r["event_id"] for r in rows})

    def test_random_event_sample_reproducible_same_seed(self):
        a = sampler.sample_random_event_sample(self.conn, "ASTROWATCH-HIST-002", "EXP-X", count=20, seed=42)
        b = sampler.sample_random_event_sample(self.conn, "ASTROWATCH-HIST-002", "EXP-X", count=20, seed=42)
        self.assertEqual([c.source_event_id for c in a], [c.source_event_id for c in b])

    def test_random_event_sample_different_seed_differs(self):
        a = sampler.sample_random_event_sample(self.conn, "ASTROWATCH-HIST-002", "EXP-X", count=20, seed=1)
        b = sampler.sample_random_event_sample(self.conn, "ASTROWATCH-HIST-002", "EXP-X", count=20, seed=2)
        self.assertNotEqual([c.source_event_id for c in a], [c.source_event_id for c in b])

    def test_random_date_sample_reproducible(self):
        a = sampler.sample_random_date_sample("1900-01-01", "2020-01-01", 10, seed=7, experiment_id="EXP-X")
        b = sampler.sample_random_date_sample("1900-01-01", "2020-01-01", 10, seed=7, experiment_id="EXP-X")
        self.assertEqual([c.test_date for c in a], [c.test_date for c in b])
        self.assertEqual(len(a), 10)

    def test_time_precision_mode_assignment_matches_taxonomy(self):
        cases = sampler.sample_full_dataset(self.conn, "ASTROWATCH-HIST-002", "EXP-X")
        by_id = {c.source_event_id: c for c in cases}
        exact_row = self.conn.execute(
            "SELECT event_id FROM events WHERE dataset_version='ASTROWATCH-HIST-002' AND time_confidence='EXACT' LIMIT 1"
        ).fetchone()
        self.assertEqual(by_id[exact_row["event_id"]].time_precision_mode, "MODE_A_EXACT_TIME")
        unknown_row = self.conn.execute(
            "SELECT event_id FROM events WHERE dataset_version='ASTROWATCH-HIST-002' AND time_confidence='UNKNOWN' LIMIT 1"
        ).fetchone()
        self.assertEqual(by_id[unknown_row["event_id"]].time_precision_mode, "MODE_B_DATE_ONLY")
        approx_row = self.conn.execute(
            "SELECT event_id FROM events WHERE dataset_version='ASTROWATCH-HIST-002' AND time_confidence='APPROXIMATE' LIMIT 1"
        ).fetchone()
        self.assertEqual(by_id[approx_row["event_id"]].time_precision_mode, "MODE_C_TIME_WINDOW")

    def test_no_write_to_historical_db_during_sampling(self):
        before = os.path.getsize(HIST_DB)
        sampler.sample_full_dataset(self.conn, "ASTROWATCH-HIST-002", "EXP-X")
        controls.sample_existing_control_dates(self.conn, "ASTROWATCH-HIST-002", "EXP-X")
        after = os.path.getsize(HIST_DB)
        self.assertEqual(before, after)


class ControlSamplingTests(unittest.TestCase):
    def setUp(self):
        self.conn = hdb.connect(HIST_DB)

    def tearDown(self):
        self.conn.close()

    def test_existing_control_dates_reused_exactly(self):
        cases = controls.sample_existing_control_dates(self.conn, "ASTROWATCH-HIST-002", "EXP-X")
        self.assertEqual(len(cases), 150)
        self.assertTrue(all(c.case_kind == "CONTROL" for c in cases))
        self.assertTrue(all(c.time_precision_mode == "MODE_B_DATE_ONLY" for c in cases))
        self.assertTrue(all(c.input_time is None for c in cases))


if __name__ == "__main__":
    unittest.main()
