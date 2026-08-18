import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import historical.database as hdb
from backtest import reproducibility, sampler, controls, predictor

HIST_DB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                        "historical_events_v2.db")
ASTROWATCH_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class VersionHashTests(unittest.TestCase):
    def test_rule_registry_hash_deterministic(self):
        h1 = reproducibility.rule_registry_version_hash()
        h2 = reproducibility.rule_registry_version_hash()
        self.assertEqual(h1["hash_sha256"], h2["hash_sha256"])
        self.assertEqual(int(h1["rule_count"]), 19)

    def test_astronomy_hash_deterministic(self):
        h1 = reproducibility.astronomy_version_hash(ASTROWATCH_DIR)
        h2 = reproducibility.astronomy_version_hash(ASTROWATCH_DIR)
        self.assertEqual(h1["hash_sha256"], h2["hash_sha256"])
        self.assertEqual(set(h1["per_file_sha256"]), set(reproducibility.ASTRONOMY_METHODOLOGY_MODULES))

    def test_configuration_hash_stable_for_same_dict(self):
        cfg = {"a": 1, "b": [1, 2, 3], "c": "x"}
        self.assertEqual(reproducibility.configuration_hash(cfg), reproducibility.configuration_hash(dict(cfg)))

    def test_configuration_hash_changes_with_content(self):
        cfg1 = {"seed": 1}
        cfg2 = {"seed": 2}
        self.assertNotEqual(reproducibility.configuration_hash(cfg1), reproducibility.configuration_hash(cfg2))


class DeterminismTests(unittest.TestCase):
    """Spec item 26: same dataset version + experiment config + seed + rule/
    astronomy version + sampling methodology -> identical test cases, predictions,
    and scores."""

    def setUp(self):
        self.conn = hdb.connect(HIST_DB)

    def tearDown(self):
        self.conn.close()

    def test_full_pipeline_identical_across_two_runs_same_seed(self):
        cases_a = sampler.sample_full_dataset(self.conn, "ASTROWATCH-HIST-002", "EXP-DET")
        cases_b = sampler.sample_full_dataset(self.conn, "ASTROWATCH-HIST-002", "EXP-DET")
        self.assertEqual([c.test_case_id for c in cases_a], [c.test_case_id for c in cases_b])
        self.assertEqual([c.time_precision_mode for c in cases_a], [c.time_precision_mode for c in cases_b])

        controls_a = controls.sample_existing_control_dates(self.conn, "ASTROWATCH-HIST-002", "EXP-DET")
        controls_b = controls.sample_existing_control_dates(self.conn, "ASTROWATCH-HIST-002", "EXP-DET")
        self.assertEqual([c.test_case_id for c in controls_a], [c.test_case_id for c in controls_b])

        # Predictions for a sample of cases must match exactly, field-for-field.
        for tc in (cases_a[:5] + controls_a[:5]):
            p1 = predictor.predict(tc.to_blind_input(), "EXP-DET", f"PRED-{tc.test_case_id}-1")
            p2 = predictor.predict(tc.to_blind_input(), "EXP-DET", f"PRED-{tc.test_case_id}-2")
            self.assertEqual(p1.predicted_fired, p2.predicted_fired)
            self.assertEqual(p1.predicted_categories, p2.predicted_categories)
            self.assertEqual(p1.rule_matches, p2.rule_matches)
            self.assertEqual(p1.astronomical_inputs_jd_ut, p2.astronomical_inputs_jd_ut)
            self.assertEqual(p1.ayanamsha_source, p2.ayanamsha_source)
            self.assertEqual(p1.ephemeris_precision_flag, p2.ephemeris_precision_flag)


if __name__ == "__main__":
    unittest.main()
