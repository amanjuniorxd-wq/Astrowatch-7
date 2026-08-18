import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from backtest.blindness import check_predictor_source
from backtest.models import BlindInput
from backtest.predictor import predict


class StaticBlindnessTests(unittest.TestCase):
    def test_predictor_source_has_no_forbidden_references(self):
        ok, violations = check_predictor_source()
        self.assertTrue(ok, msg=f"predictor.py references forbidden fields: {violations}")

    def test_predictor_module_does_not_import_historical_package(self):
        # AST-based, not text-search-based -- a naive substring search on "from
        # historical" false-positives on this very module's own docstring (which
        # legitimately mentions "historical/tests' own AST-based independence
        # check" in prose). This is the exact class of bug this project has hit
        # before (see historical/tests/test_astrological_independence.py's own
        # history) -- caught here by actually running this test, not assumed.
        import ast
        import backtest.predictor as pred_mod
        with open(pred_mod.__file__) as f:
            tree = ast.parse(f.read())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertFalse(alias.name.startswith("historical"))
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                self.assertFalse(mod.startswith("historical"))


class FunctionalBlindnessTests(unittest.TestCase):
    """Randomizing the (never-passed-in) outcome label cannot possibly affect
    predict() since BlindInput has no outcome field at all -- this test instead
    demonstrates the OTHER direction: the SAME BlindInput always yields the SAME
    prediction regardless of what a caller does with any DIFFERENT test_case_id or
    label bookkeeping around it (i.e. prediction generation is a pure function of
    BlindInput, nothing else)."""

    def test_same_blind_input_same_prediction_regardless_of_surrounding_labels(self):
        bi = BlindInput(test_case_id="TC-A", date="2011-03-11",
                         time_precision_mode="MODE_A_EXACT_TIME", time_hhmm="05:46",
                         timezone="UTC", location_precision="EXACT")
        p1 = predict(bi, experiment_id="EXP-1", prediction_id="PRED-1")
        # Relabel test_case_id (simulating a randomized/shuffled outcome-label
        # scenario elsewhere in the pipeline) -- the ASTRONOMICAL content of the
        # prediction must be identical; only the bookkeeping id differs.
        bi_relabeled = BlindInput(test_case_id="TC-SHUFFLED-999", date=bi.date,
                                   time_precision_mode=bi.time_precision_mode,
                                   time_hhmm=bi.time_hhmm, timezone=bi.timezone,
                                   location_precision=bi.location_precision)
        p2 = predict(bi_relabeled, experiment_id="EXP-1", prediction_id="PRED-2")
        self.assertEqual(p1.predicted_fired, p2.predicted_fired)
        self.assertEqual(p1.predicted_categories, p2.predicted_categories)
        self.assertEqual(p1.rule_matches, p2.rule_matches)

    def test_blind_input_has_no_outcome_carrying_fields(self):
        import dataclasses
        field_names = {f.name for f in dataclasses.fields(BlindInput)}
        forbidden = {
            "event_name", "event_type", "event_subtype", "description",
            "verification_status", "canonical_event_id", "actual_category",
            "source", "actual_outcome",
        }
        self.assertEqual(field_names & forbidden, set())


if __name__ == "__main__":
    unittest.main()
