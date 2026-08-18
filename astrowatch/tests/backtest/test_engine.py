import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import historical.database as hdb
from backtest import engine, sampler, controls, database as bdb, repository as brepo

ASTROWATCH_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HIST_DB = os.path.join(ASTROWATCH_DIR, "historical_events_v2.db")


class EngineIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        os.remove(self.tmp.name)
        self.bt_conn = bdb.initialize_db(self.tmp.name)
        self.hist_conn = hdb.connect(HIST_DB)

    def tearDown(self):
        self.bt_conn.close()
        self.hist_conn.close()
        if os.path.exists(self.tmp.name):
            os.remove(self.tmp.name)

    def test_build_experiment_and_run_mixed_cases(self):
        exp = engine.build_experiment(
            experiment_id="EXP-ENGINE-TEST", dataset_version="ASTROWATCH-HIST-002",
            hist_db_path=HIST_DB, astrowatch_dir=ASTROWATCH_DIR, random_seed=123,
            sampling_method="FULL_DATASET", control_method="EXISTING_CONTROL_DATES",
            allow_ayanamsha_fallback=True, test_window_start=None, test_window_end=None,
        )
        brepo.insert_experiment(self.bt_conn, exp)
        self.bt_conn.commit()

        event_cases = sampler.sample_full_dataset(self.hist_conn, "ASTROWATCH-HIST-002", exp.experiment_id)
        control_cases = controls.sample_existing_control_dates(self.hist_conn, "ASTROWATCH-HIST-002", exp.experiment_id)

        sample = event_cases[:4] + control_cases[:4]
        for tc in sample:
            brepo.insert_test_case(self.bt_conn, tc)
            engine.run_test_case(self.bt_conn, self.hist_conn, tc, exp.experiment_id, allow_ayanamsha_fallback=True)
        self.bt_conn.commit()

        preds = brepo.get_predictions(self.bt_conn, exp.experiment_id)
        outcomes = brepo.get_actual_outcomes(self.bt_conn, exp.experiment_id)
        self.assertEqual(len(preds), 8)
        self.assertEqual(len(outcomes), 8)

        outcome_by_case = {o["test_case_id"]: o for o in outcomes}
        for tc in event_cases[:4]:
            self.assertEqual(outcome_by_case[tc.test_case_id]["actual_kind"], "EVENT")
            self.assertIsNotNone(outcome_by_case[tc.test_case_id]["actual_category"])
        for tc in control_cases[:4]:
            self.assertEqual(outcome_by_case[tc.test_case_id]["actual_kind"], "PRESUMED_NO_EVENT")
            self.assertIsNone(outcome_by_case[tc.test_case_id]["actual_category"])

    def test_checksum_mismatch_stops_experiment_build(self):
        # Point at a db path with no sidecar file at all -- validate_frozen_checksum()
        # returns ok=False in that case too (see historical/versioning.py), which
        # build_experiment() must treat identically to a real mismatch: STOP.
        with self.assertRaises(engine.ChecksumMismatchError):
            engine.build_experiment(
                experiment_id="EXP-SHOULD-FAIL", dataset_version="ASTROWATCH-HIST-002",
                hist_db_path=os.path.join(ASTROWATCH_DIR, "backtest_results_schema.sql"),
                astrowatch_dir=ASTROWATCH_DIR, random_seed=1, sampling_method="FULL_DATASET",
                control_method="EXISTING_CONTROL_DATES", allow_ayanamsha_fallback=True,
                test_window_start=None, test_window_end=None,
            )


if __name__ == "__main__":
    unittest.main()
