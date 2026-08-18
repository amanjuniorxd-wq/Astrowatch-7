import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from backtest import baselines, scorer
from backtest.category_map import ALL_EVENT_CATEGORIES


def _actuals(fired, categories):
    return {"fired": fired, "categories": set(categories)}


class RandomBaselineTests(unittest.TestCase):
    def test_reproducible_same_seed(self):
        events = {f"E{i}": _actuals(i % 2 == 0, ["MILITARY"] if i % 2 == 0 else []) for i in range(10)}
        controls = {f"C{i}": _actuals(False, []) for i in range(5)}
        a = baselines.random_baseline_pairs(events, controls, seed=1)
        b = baselines.random_baseline_pairs(events, controls, seed=1)
        self.assertEqual(a["ANY"], b["ANY"])

    def test_different_seed_can_differ(self):
        events = {f"E{i}": _actuals(True, ["MILITARY"]) for i in range(20)}
        controls = {f"C{i}": _actuals(False, []) for i in range(20)}
        a = baselines.random_baseline_pairs(events, controls, seed=1)
        b = baselines.random_baseline_pairs(events, controls, seed=2)
        self.assertNotEqual(a["ANY"], b["ANY"])

    def test_produces_entry_for_every_category(self):
        events = {"E1": _actuals(True, ["MILITARY"])}
        controls = {}
        out = baselines.random_baseline_pairs(events, controls, seed=1)
        for cat in ALL_EVENT_CATEGORIES:
            self.assertIn(cat, out)


class HistoricalFrequencyBaselineTests(unittest.TestCase):
    def test_reproducible_same_seed(self):
        events = {f"E{i}": _actuals(True, ["NATURAL_DISASTER"]) for i in range(10)}
        controls = {f"C{i}": _actuals(False, []) for i in range(10)}
        a = baselines.historical_frequency_baseline_pairs(events, controls, seed=5)
        b = baselines.historical_frequency_baseline_pairs(events, controls, seed=5)
        self.assertEqual(a["NATURAL_DISASTER"], b["NATURAL_DISASTER"])

    def test_all_same_category_yields_prob_one_for_that_category(self):
        # With category_prob=1.0 for NATURAL_DISASTER, every draw must predict positive.
        events = {f"E{i}": _actuals(True, ["NATURAL_DISASTER"]) for i in range(30)}
        controls = {}
        out = baselines.historical_frequency_baseline_pairs(events, controls, seed=1)
        predicted = [p for p, a in out["NATURAL_DISASTER"]]
        self.assertTrue(all(predicted))


class ControlDateBaselineTests(unittest.TestCase):
    def test_matches_nearest_control_date(self):
        event_dates = {"TC-E1": "2000-06-15"}
        event_actuals = {"TC-E1": _actuals(True, ["MILITARY"])}
        control_dates = {"TC-C1": "2000-06-10", "TC-C2": "2000-01-01"}
        control_predictions = {
            "TC-C1": {"fired": True, "categories": {"MILITARY"}},
            "TC-C2": {"fired": False, "categories": set()},
        }
        out = baselines.control_date_baseline_pairs(event_dates, event_actuals, control_dates, control_predictions)
        # TC-C1 (5 days away) should be chosen over TC-C2 (166 days away)
        self.assertEqual(out["ANY"], [(True, True)])

    def test_empty_controls_returns_empty(self):
        out = baselines.control_date_baseline_pairs({"E1": "2000-01-01"}, {"E1": _actuals(True, [])}, {}, {})
        self.assertEqual(out["ANY"], [])


class BaselinesScoredWithSameMetricsTests(unittest.TestCase):
    def test_baseline_output_feeds_scorer_cleanly(self):
        events = {f"E{i}": _actuals(i % 3 == 0, ["MILITARY"] if i % 3 == 0 else []) for i in range(15)}
        controls = {f"C{i}": _actuals(False, []) for i in range(15)}
        pairs = baselines.random_baseline_pairs(events, controls, seed=1)
        m = scorer.compute_metrics(scorer.confusion_counts(pairs["ANY"]))
        self.assertEqual(m["sample_size"], 30)


if __name__ == "__main__":
    unittest.main()
