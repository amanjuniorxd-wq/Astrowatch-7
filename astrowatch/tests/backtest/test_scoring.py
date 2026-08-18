import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from backtest import scorer


class ConfusionCountsTests(unittest.TestCase):
    def test_basic_counts(self):
        pairs = [(True, True), (True, False), (False, False), (False, True), (True, True)]
        c = scorer.confusion_counts(pairs)
        self.assertEqual((c.tp, c.fp, c.tn, c.fn), (2, 1, 1, 1))
        self.assertEqual(c.n, 5)

    def test_all_true_negative(self):
        pairs = [(False, False)] * 10
        c = scorer.confusion_counts(pairs)
        self.assertEqual((c.tp, c.fp, c.tn, c.fn), (0, 0, 10, 0))


class MetricComputationTests(unittest.TestCase):
    def test_perfect_predictor(self):
        pairs = [(True, True)] * 5 + [(False, False)] * 5
        c = scorer.confusion_counts(pairs)
        m = scorer.compute_metrics(c)
        self.assertAlmostEqual(m["precision"], 1.0)
        self.assertAlmostEqual(m["recall"], 1.0)
        self.assertAlmostEqual(m["f1"], 1.0)
        self.assertAlmostEqual(m["accuracy"], 1.0)
        self.assertAlmostEqual(m["specificity"], 1.0)
        self.assertAlmostEqual(m["false_positive_rate"], 0.0)

    def test_worst_case_predictor(self):
        pairs = [(True, False)] * 5 + [(False, True)] * 5
        c = scorer.confusion_counts(pairs)
        m = scorer.compute_metrics(c)
        self.assertAlmostEqual(m["precision"], 0.0)
        self.assertAlmostEqual(m["recall"], 0.0)
        self.assertAlmostEqual(m["accuracy"], 0.0)

    def test_undefined_precision_when_no_positive_predictions(self):
        pairs = [(False, True), (False, False)]
        c = scorer.confusion_counts(pairs)
        m = scorer.compute_metrics(c)
        self.assertIsNone(m["precision"])  # 0/0, correctly None not fabricated as 0 or 1

    def test_small_sample_flagged(self):
        pairs = [(True, True), (False, False)]  # n=2 < MIN_SAMPLE_SIZE
        c = scorer.confusion_counts(pairs)
        m = scorer.compute_metrics(c)
        self.assertEqual(m["sample_flag"], "INSUFFICIENT_SAMPLE")

    def test_adequate_sample_not_flagged(self):
        pairs = [(True, True)] * 6 + [(False, False)] * 6  # n=12 >= 10
        c = scorer.confusion_counts(pairs)
        m = scorer.compute_metrics(c)
        self.assertEqual(m["sample_flag"], "OK")


class WilsonCITests(unittest.TestCase):
    def test_ci_contains_point_estimate(self):
        low, high = scorer.wilson_ci(50, 100)
        self.assertLess(low, 0.5)
        self.assertGreater(high, 0.5)

    def test_ci_widens_with_smaller_n(self):
        low_big, high_big = scorer.wilson_ci(50, 100)
        low_small, high_small = scorer.wilson_ci(5, 10)
        self.assertLess(low_small, low_big)
        self.assertGreater(high_small, high_big)

    def test_ci_zero_n(self):
        self.assertEqual(scorer.wilson_ci(0, 0), (0.0, 0.0))


class PermutationTestTests(unittest.TestCase):
    def test_identical_groups_high_p_value(self):
        event_fired = [True, False, True, False, True, False, True, False, True, False]
        control_fired = [True, False, True, False, True, False, True, False, True, False]
        result = scorer.permutation_test_fire_rate_difference(event_fired, control_fired, seed=1, iterations=2000)
        self.assertAlmostEqual(result["observed_difference"], 0.0)
        self.assertGreater(result["p_value"], 0.5)

    def test_maximally_different_groups_low_p_value(self):
        event_fired = [True] * 20
        control_fired = [False] * 20
        result = scorer.permutation_test_fire_rate_difference(event_fired, control_fired, seed=1, iterations=2000)
        self.assertAlmostEqual(result["observed_difference"], 1.0)
        self.assertLess(result["p_value"], 0.05)

    def test_reproducible_with_same_seed(self):
        event_fired = [True, False, True, True, False]
        control_fired = [False, False, True, False, False]
        r1 = scorer.permutation_test_fire_rate_difference(event_fired, control_fired, seed=99, iterations=500)
        r2 = scorer.permutation_test_fire_rate_difference(event_fired, control_fired, seed=99, iterations=500)
        self.assertEqual(r1["p_value"], r2["p_value"])

    def test_empty_group_returns_none(self):
        result = scorer.permutation_test_fire_rate_difference([], [True], seed=1)
        self.assertIsNone(result["p_value"])


if __name__ == "__main__":
    unittest.main()
