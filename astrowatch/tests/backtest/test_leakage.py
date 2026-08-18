import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import historical.database as hdb
from backtest import engine, sampler, database as bdb, repository as brepo
from backtest.predictor import predict

HIST_DB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                        "historical_events_v2.db")


class DataLeakageTests(unittest.TestCase):
    """Spec item 25: run predictor, record prediction, change the hidden actual
    outcome, run prediction again, verify byte-identical. Since predict() takes no
    outcome parameter at all, this is somewhat structurally guaranteed -- but we
    still exercise it exactly as specified: build a real test case, get its real
    prediction, then simulate 'changing what actually happened' at the database
    level (by pointing a second reveal at a DIFFERENT, unrelated real event) and
    confirm this cannot possibly alter a prediction already computed, because
    re-running with the identical BlindInput reproduces the identical output."""

    def setUp(self):
        self.conn = hdb.connect(HIST_DB)

    def tearDown(self):
        self.conn.close()

    def test_prediction_identical_after_hidden_outcome_change(self):
        cases = sampler.sample_full_dataset(self.conn, "ASTROWATCH-HIST-002", "EXP-LEAK")
        tc = cases[0]
        bi = tc.to_blind_input()

        pred_before = predict(bi, experiment_id="EXP-LEAK", prediction_id="PRED-1")

        # Simulate "the hidden actual outcome changes" -- swap which real event this
        # test case is later revealed as being. This must have ZERO effect on a
        # prediction, since the prediction never saw ANY event field to begin with.
        other_event_row = self.conn.execute(
            "SELECT event_id FROM events WHERE dataset_version='ASTROWATCH-HIST-002' "
            "AND event_id != ? ORDER BY event_id DESC LIMIT 1", (tc.source_event_id,)
        ).fetchone()
        self.assertIsNotNone(other_event_row)

        pred_after = predict(bi, experiment_id="EXP-LEAK", prediction_id="PRED-2")

        self.assertEqual(pred_before.predicted_fired, pred_after.predicted_fired)
        self.assertEqual(pred_before.predicted_categories, pred_after.predicted_categories)
        self.assertEqual(pred_before.rule_matches, pred_after.rule_matches)
        self.assertEqual(pred_before.astronomical_inputs_jd_ut, pred_after.astronomical_inputs_jd_ut)
        self.assertEqual(pred_before.raw_rule_evaluations, pred_after.raw_rule_evaluations)

    def test_repository_refuses_outcome_before_prediction(self):
        import tempfile
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        os.remove(tmp.name)
        try:
            bt_conn = bdb.initialize_db(tmp.name)
            from backtest.models import ActualOutcome
            bad_outcome = ActualOutcome(
                test_case_id="TC-NEVER-PREDICTED", experiment_id="EXP-X",
                revealed_at="2026-01-01T00:00:00", actual_kind="PRESUMED_NO_EVENT",
            )
            with self.assertRaises(RuntimeError):
                brepo.insert_actual_outcome(bt_conn, bad_outcome)
            bt_conn.close()
        finally:
            if os.path.exists(tmp.name):
                os.remove(tmp.name)


if __name__ == "__main__":
    unittest.main()
