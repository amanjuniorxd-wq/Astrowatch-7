"""
tests/event_backtest/test_event_backtest.py
==============================================
Comprehensive tests for the event_backtest/ + prediction/ historical
backtest engine: schema validation, hindsight/cutoff enforcement, missing
data handling, probability normalization, hand-verified metric math,
calibration binning, reproducibility, model versioning, ablation, CLI, and
report generation.
"""
import json
import math
import os
import subprocess
import sys
import tempfile
import unittest
from dataclasses import replace

ASTROWATCH_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ASTROWATCH_DIR)

from event_backtest.cutoff import (
    HindsightError, DataProvenance, enforce_cutoff, calc_date_within_cutoff,
    validate_event_schema_dates,
)
from event_backtest.models import CandidateRef, HistoricalPredictionEvent, PredictionResult, FeatureBreakdown
from event_backtest import dataset as dataset_module
from event_backtest import engine
from event_backtest.metrics import evaluate_one, aggregate, EvaluatedPrediction
from event_backtest.calibration import compute_calibration_table, calibration_is_claimable
from prediction.predictor import predict
from prediction.scorer import score_candidate, normalize_scores, MODEL_CONFIG, MODEL_VARIANTS
from prediction.features import EntityFeatureSet, extract_entity_features


class CutoffHindsightTests(unittest.TestCase):
    def test_enforce_cutoff_passes_when_data_predates_cutoff(self):
        p = DataProvenance(source="Wikipedia", source_date="2020-01-01", data_type="test")
        enforce_cutoff(p, "2023-01-01")  # should not raise

    def test_enforce_cutoff_raises_when_data_postdates_cutoff(self):
        p = DataProvenance(source="Wikipedia", source_date="2024-06-01", data_type="test")
        with self.assertRaises(HindsightError):
            enforce_cutoff(p, "2023-01-01")

    def test_enforce_cutoff_uses_availability_date_over_source_date(self):
        # source_date is early, but the data wasn't AVAILABLE until later --
        # effective_availability_date() must use availability_date.
        p = DataProvenance(source="X", source_date="2020-01-01", data_type="test",
                            availability_date="2024-01-01")
        with self.assertRaises(HindsightError):
            enforce_cutoff(p, "2023-01-01")

    def test_calc_date_within_cutoff_passes_for_past_date(self):
        calc_date_within_cutoff("2020-01-01", "2023-01-01")  # should not raise

    def test_calc_date_within_cutoff_raises_for_future_date(self):
        with self.assertRaises(HindsightError):
            calc_date_within_cutoff("2024-01-01", "2023-01-01")

    def test_calc_date_within_cutoff_allows_exact_cutoff_instant(self):
        calc_date_within_cutoff("2023-01-01", "2023-01-01")  # should not raise (not strictly after)

    def test_validate_event_schema_dates_passes_for_valid_event(self):
        validate_event_schema_dates("2023-11-19", "2023-01-01")  # should not raise

    def test_validate_event_schema_dates_rejects_cutoff_after_event(self):
        with self.assertRaises(ValueError):
            validate_event_schema_dates("2023-01-01", "2023-11-19")

    def test_validate_event_schema_dates_rejects_equal_dates(self):
        with self.assertRaises(ValueError):
            validate_event_schema_dates("2023-01-01", "2023-01-01")

    def test_future_information_is_rejected_end_to_end(self):
        """Directly proves the spec's requirement: injecting a provenance
        dated AFTER cutoff into the pipeline raises HindsightError, not a
        silently wrong answer."""
        future_provenance = DataProvenance(
            source="A source reporting the tournament's actual result",
            source_date="2023-11-20",  # one day AFTER the final -- clearly future info
            data_type="actual_result_leak",
        )
        with self.assertRaises(HindsightError):
            enforce_cutoff(future_provenance, "2023-01-01")


class ScorerTests(unittest.TestCase):
    def test_model_config_weights_sum_to_one(self):
        self.assertAlmostEqual(sum(MODEL_CONFIG.values()), 1.0, places=9)

    def test_score_candidate_all_features_present(self):
        fs = EntityFeatureSet(
            candidate_id="x", entity_name="X", as_of_date="2023-01-01", time_source="documented",
            mahadasha_lord="jupiter", mahadasha_lord_score=0.9, antardasha_lord_score=0.8,
            transit_strength=0.7, moon_activation=0.6, entity_chart_strength=0.75,
            event_chart_strength=0.5, key_personnel_strength=0.4,
        )
        result = score_candidate(fs, model_variant="complete")
        self.assertIsNotNone(result.raw_score)
        self.assertEqual(result.missing_features, [])
        self.assertAlmostEqual(sum(result.weights_used.values()), 1.0, places=9)

    def test_score_candidate_renormalizes_around_missing_features(self):
        fs = EntityFeatureSet(
            candidate_id="x", entity_name="X", as_of_date="2023-01-01", time_source="documented",
            mahadasha_lord="jupiter", mahadasha_lord_score=0.9, antardasha_lord_score=0.8,
            # transit/moon/entity/event/key_personnel all left as None (missing)
        )
        result = score_candidate(fs, model_variant="complete")
        self.assertIsNotNone(result.raw_score)
        self.assertAlmostEqual(sum(result.weights_used.values()), 1.0, places=9)
        self.assertIn("transit", result.missing_features)

    def test_score_candidate_returns_none_when_everything_missing(self):
        fs = EntityFeatureSet(candidate_id="x", entity_name="X", as_of_date="2023-01-01",
                               time_source="unavailable")
        result = score_candidate(fs, model_variant="complete")
        self.assertIsNone(result.raw_score)

    def test_normalize_scores_sums_to_one(self):
        probs = normalize_scores({"a": 0.6, "b": 0.3, "c": 0.1})
        self.assertAlmostEqual(sum(probs.values()), 1.0, places=9)

    def test_normalize_scores_handles_all_none(self):
        self.assertIsNone(normalize_scores({"a": None, "b": None}))

    def test_normalize_scores_numerical_safeguard_for_zero_total(self):
        probs = normalize_scores({"a": 0.0, "b": 0.0})
        self.assertAlmostEqual(sum(probs.values()), 1.0, places=9)
        self.assertAlmostEqual(probs["a"], 0.5, places=9)

    def test_unknown_model_variant_raises(self):
        fs = EntityFeatureSet(candidate_id="x", entity_name="X", as_of_date="2023-01-01",
                               time_source="documented")
        with self.assertRaises(ValueError):
            score_candidate(fs, model_variant="not-a-real-variant")

    def test_ablation_variants_are_documented_subsets(self):
        for variant, keys in MODEL_VARIANTS.items():
            for k in keys:
                self.assertIn(k, MODEL_CONFIG, f"variant {variant} references unknown key {k}")
        self.assertEqual(set(MODEL_VARIANTS["complete"]), set(MODEL_CONFIG.keys()))


class FeatureExtractionTests(unittest.TestCase):
    def test_extract_entity_features_real_entity(self):
        c = CandidateRef(candidate_id="india", entity_name="India", display_name="India")
        fs = extract_entity_features(c, "2023-01-01")
        self.assertEqual(fs.candidate_id, "india")
        self.assertIsNotNone(fs.mahadasha_lord)
        self.assertIsNotNone(fs.mahadasha_lord_score)
        self.assertGreaterEqual(fs.mahadasha_lord_score, 0.0)
        self.assertLessEqual(fs.mahadasha_lord_score, 1.0)
        self.assertEqual(fs.missing_components, [])

    def test_extract_entity_features_unmapped_entity_reports_missing(self):
        c = CandidateRef(candidate_id="atlantis", entity_name="Atlantis", display_name="Atlantis")
        fs = extract_entity_features(c, "2023-01-01")
        self.assertTrue(len(fs.missing_components) > 0)
        self.assertIsNone(fs.mahadasha_lord)

    def test_feature_scores_are_normalized_0_to_1(self):
        c = CandidateRef(candidate_id="australia", entity_name="Australia", display_name="Australia")
        fs = extract_entity_features(c, "2023-01-01")
        for value in (fs.mahadasha_lord_score, fs.antardasha_lord_score,
                      fs.transit_strength, fs.moon_activation, fs.entity_chart_strength):
            if value is not None:
                self.assertGreaterEqual(value, 0.0)
                self.assertLessEqual(value, 1.0)


class PredictorTests(unittest.TestCase):
    def _sample_event(self):
        return HistoricalPredictionEvent(
            event_id="test_event", event_type="cricket", event_name="Test Event",
            event_date="2023-11-19", prediction_cutoff_date="2023-01-01", location="Test",
            candidates=[
                CandidateRef(candidate_id="india", entity_name="India", display_name="India"),
                CandidateRef(candidate_id="australia", entity_name="Australia", display_name="Australia"),
            ],
            actual_winner="australia",
        )

    def test_predict_never_receives_actual_winner_key(self):
        event = self._sample_event()
        public_fields = event.public_fields()
        self.assertNotIn("actual_winner", public_fields)

    def test_predict_returns_ok_status_with_two_real_candidates(self):
        event = self._sample_event()
        result = predict(event.public_fields())
        self.assertEqual(result.status, "OK")
        self.assertIn(result.predicted_winner, {"india", "australia"})
        self.assertAlmostEqual(sum(result.probabilities.values()), 1.0, places=6)

    def test_predict_probabilities_never_claimed_calibrated(self):
        event = self._sample_event()
        result = predict(event.public_fields())
        self.assertFalse(result.probabilities_are_calibrated)

    def test_predict_with_no_candidates_is_data_unavailable(self):
        event = replace(self._sample_event(), candidates=[])
        result = predict(event.public_fields())
        self.assertEqual(result.status, "DATA_UNAVAILABLE")
        self.assertIsNone(result.predicted_winner)

    def test_predict_with_unmapped_candidates_is_insufficient_data(self):
        event = replace(self._sample_event(), candidates=[
            CandidateRef(candidate_id="a", entity_name="Atlantis", display_name="Atlantis"),
            CandidateRef(candidate_id="b", entity_name="Narnia", display_name="Narnia"),
        ])
        result = predict(event.public_fields())
        self.assertEqual(result.status, "INSUFFICIENT_DATA")

    def test_predict_is_deterministic_reproducible(self):
        event = self._sample_event()
        r1 = predict(event.public_fields())
        r2 = predict(event.public_fields())
        self.assertEqual(r1.predicted_winner, r2.predicted_winner)
        self.assertEqual(r1.scores, r2.scores)
        self.assertEqual(r1.probabilities, r2.probabilities)

    def test_predict_model_version_reflects_variant(self):
        event = self._sample_event()
        result = predict(event.public_fields(), model_variant="vedic-core")
        self.assertIn("vedic-core", result.model_version)

    def test_unknown_model_variant_returns_insufficient_data_not_exception(self):
        event = self._sample_event()
        result = predict(event.public_fields(), model_variant="nonexistent-variant")
        self.assertEqual(result.status, "INSUFFICIENT_DATA")


class MetricsMathTests(unittest.TestCase):
    def _event(self, actual_winner):
        return HistoricalPredictionEvent(
            event_id="e1", event_type="cricket", event_name="E1", event_date="2023-01-02",
            prediction_cutoff_date="2023-01-01", location="X",
            candidates=[
                CandidateRef(candidate_id="a", entity_name="A", display_name="A"),
                CandidateRef(candidate_id="b", entity_name="B", display_name="B"),
            ],
            actual_winner=actual_winner,
        )

    def _result(self, probs, predicted_winner):
        return PredictionResult(
            event_id="e1", cutoff_date="2023-01-01", model_version="test",
            predicted_winner=predicted_winner, scores=probs, probabilities=probs,
            probabilities_are_calibrated=False, feature_breakdown={}, status="OK",
        )

    def test_brier_score_hand_verified_perfect_prediction(self):
        # actual winner 'a' predicted with probability 1.0 -> Brier = 0
        event = self._event("a")
        result = self._result({"a": 1.0, "b": 0.0}, "a")
        ev = evaluate_one(event, result)
        self.assertAlmostEqual(ev.brier, 0.0, places=9)
        self.assertTrue(ev.correct)

    def test_brier_score_hand_verified_worst_prediction(self):
        # actual winner 'a' predicted with probability 0.0 -> Brier = (0-1)^2 + (1-0)^2 = 2.0
        event = self._event("a")
        result = self._result({"a": 0.0, "b": 1.0}, "b")
        ev = evaluate_one(event, result)
        self.assertAlmostEqual(ev.brier, 2.0, places=9)
        self.assertFalse(ev.correct)

    def test_brier_score_hand_verified_even_split(self):
        # 50/50 on a 2-candidate event -> Brier = (0.5-1)^2 + (0.5-0)^2 = 0.5
        event = self._event("a")
        result = self._result({"a": 0.5, "b": 0.5}, "a")
        ev = evaluate_one(event, result)
        self.assertAlmostEqual(ev.brier, 0.5, places=9)

    def test_log_loss_hand_verified(self):
        event = self._event("a")
        result = self._result({"a": 0.25, "b": 0.75}, "b")
        ev = evaluate_one(event, result)
        self.assertAlmostEqual(ev.log_loss, -math.log(0.25), places=9)

    def test_log_loss_numerical_safeguard_for_zero_probability(self):
        event = self._event("a")
        result = self._result({"a": 0.0, "b": 1.0}, "b")
        ev = evaluate_one(event, result)
        self.assertTrue(math.isfinite(ev.log_loss))  # must not be inf or raise

    def test_predicted_rank_of_actual(self):
        event = self._event("b")
        result = self._result({"a": 0.9, "b": 0.1}, "a")
        ev = evaluate_one(event, result)
        self.assertEqual(ev.predicted_rank_of_actual, 2)
        self.assertAlmostEqual(ev.reciprocal_rank, 0.5, places=9)

    def test_insufficient_data_status_excluded_from_metrics(self):
        event = self._event("a")
        result = PredictionResult(
            event_id="e1", cutoff_date="2023-01-01", model_version="test",
            predicted_winner=None, scores={}, probabilities=None,
            probabilities_are_calibrated=False, feature_breakdown={},
            status="INSUFFICIENT_DATA", status_reason="test",
        )
        ev = evaluate_one(event, result)
        self.assertIsNone(ev.correct)
        self.assertIsNone(ev.brier)

    def test_aggregate_excludes_non_ok_from_accuracy(self):
        event = self._event("a")
        ok_result = self._result({"a": 1.0, "b": 0.0}, "a")
        bad_result = PredictionResult(
            event_id="e2", cutoff_date="2023-01-01", model_version="test",
            predicted_winner=None, scores={}, probabilities=None,
            probabilities_are_calibrated=False, feature_breakdown={}, status="DATA_UNAVAILABLE",
        )
        evaluated = [evaluate_one(event, ok_result), evaluate_one(event, bad_result)]
        agg = aggregate(evaluated)
        self.assertEqual(agg.n_total, 2)
        self.assertEqual(agg.n_ok, 1)
        self.assertEqual(agg.n_excluded, 1)
        self.assertAlmostEqual(agg.top1_accuracy, 1.0, places=9)  # only the OK one counts


class CalibrationTests(unittest.TestCase):
    def test_calibration_table_bins_by_confidence(self):
        preds = [
            EvaluatedPrediction(event_id="1", event_type="x", model_version="v", status="OK",
                                 correct=True, predicted_winner="a", actual_winner="a", brier=0.0,
                                 log_loss=0.0, predicted_rank_of_actual=1, reciprocal_rank=1.0,
                                 top_probability=0.9),
            EvaluatedPrediction(event_id="2", event_type="x", model_version="v", status="OK",
                                 correct=False, predicted_winner="b", actual_winner="a", brier=1.0,
                                 log_loss=1.0, predicted_rank_of_actual=2, reciprocal_rank=0.5,
                                 top_probability=0.9),
        ]
        table = compute_calibration_table(preds)
        top_bin = [b for b in table if b.low == 0.8][0]
        self.assertEqual(top_bin.n, 2)
        self.assertAlmostEqual(top_bin.actual_success_rate, 0.5, places=9)

    def test_calibration_not_claimable_on_small_dataset(self):
        preds = [EvaluatedPrediction(event_id="1", event_type="x", model_version="v", status="OK",
                                      correct=True, predicted_winner="a", actual_winner="a", brier=0.0,
                                      log_loss=0.0, predicted_rank_of_actual=1, reciprocal_rank=1.0,
                                      top_probability=0.9)]
        self.assertFalse(calibration_is_claimable(preds))


class DatasetTests(unittest.TestCase):
    def test_no_duplicate_event_ids(self):
        events = dataset_module.list_events(include_excluded=True)
        ids = [e.event_id for e in events]
        self.assertEqual(len(ids), len(set(ids)), "duplicate event_id found in dataset")

    def test_every_event_cutoff_before_event_date(self):
        for event in dataset_module.list_events(include_excluded=True):
            validate_event_schema_dates(event.event_date, event.prediction_cutoff_date)  # must not raise

    def test_every_event_has_at_least_two_candidates(self):
        for event in dataset_module.list_events():
            self.assertGreaterEqual(len(event.candidates), 2)

    def test_actual_winner_is_a_real_candidate_id(self):
        for event in dataset_module.list_events():
            candidate_ids = {c.candidate_id for c in event.candidates}
            self.assertIn(event.actual_winner, candidate_ids)

    def test_public_fields_never_exposes_actual_winner(self):
        for event in dataset_module.list_events():
            self.assertNotIn("actual_winner", event.public_fields())


class EngineIntegrationTests(unittest.TestCase):
    def test_run_all_on_real_dataset_produces_ok_predictions(self):
        events = dataset_module.list_events()
        evaluated = engine.run_all(events, model_variant="complete")
        self.assertEqual(len(evaluated), len(events))
        for e in evaluated:
            self.assertEqual(e.status, "OK")
            self.assertIsNotNone(e.predicted_winner)
            self.assertIsNotNone(e.brier)

    def test_run_all_is_reproducible(self):
        events = dataset_module.list_events()
        r1 = engine.run_all(events, model_variant="complete")
        r2 = engine.run_all(events, model_variant="complete")
        self.assertEqual([e.predicted_winner for e in r1], [e.predicted_winner for e in r2])
        self.assertEqual([e.brier for e in r1], [e.brier for e in r2])

    def test_run_ablation_covers_every_variant(self):
        events = dataset_module.list_events()
        results = engine.run_ablation(events)
        self.assertEqual(set(results.keys()), set(MODEL_VARIANTS.keys()))
        for variant, r in results.items():
            self.assertEqual(r["aggregate"].n_ok, len(events))

    def test_excluded_event_is_reported_not_silently_dropped(self):
        event = replace(dataset_module.list_events()[0], excluded=True,
                         exclusion_reason="test exclusion")
        ev = engine.run_one(event)
        self.assertEqual(ev.status, "DATA_UNAVAILABLE")

    def test_schema_violation_raises_before_prediction(self):
        bad_event = replace(dataset_module.list_events()[0],
                             prediction_cutoff_date="2099-01-01")  # cutoff after event_date
        with self.assertRaises(ValueError):
            engine.run_one(bad_event)


class ReportGenerationTests(unittest.TestCase):
    def test_report_build_and_write_real_files(self):
        from event_backtest import report as report_module
        events = dataset_module.list_events()
        evaluated = engine.run_all(events, model_variant="complete")
        data = report_module.build_report_data(evaluated, events, model_variant="complete")

        self.assertEqual(data["n_total_events_in_dataset"], len(events))
        self.assertIn("metrics", data)
        self.assertFalse(data["calibration"]["claimable"])  # only 6 events -- must not claim calibration

        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = report_module.write_json(data, os.path.join(tmpdir, "s.json"))
            md_path = report_module.write_markdown(data, os.path.join(tmpdir, "s.md"))
            self.assertTrue(os.path.exists(json_path))
            self.assertTrue(os.path.exists(md_path))
            with open(json_path) as f:
                reloaded = json.load(f)
            self.assertEqual(reloaded["n_total_events_in_dataset"], len(events))
            with open(md_path) as f:
                md_content = f.read()
            self.assertIn("Astrowatch Event Backtest Summary", md_content)
            self.assertIn("does NOT prove or disprove astrology", md_content)


class CLITests(unittest.TestCase):
    def test_cli_list_events(self):
        result = subprocess.run(
            [sys.executable, "-m", "event_backtest.runner", "--list-events"],
            cwd=ASTROWATCH_DIR, capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("cricket_wc_2023", result.stdout)

    def test_cli_single_event(self):
        result = subprocess.run(
            [sys.executable, "-m", "event_backtest.runner", "--event", "cricket_wc_2023", "--model", "vedic-core"],
            cwd=ASTROWATCH_DIR, capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("cricket_wc_2023", result.stdout)

    def test_cli_unknown_event_returns_error(self):
        result = subprocess.run(
            [sys.executable, "-m", "event_backtest.runner", "--event", "not_a_real_event"],
            cwd=ASTROWATCH_DIR, capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(result.returncode, 1)

    def test_cli_report_flag_writes_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                [sys.executable, "-m", "event_backtest.runner", "--report"],
                cwd=ASTROWATCH_DIR, capture_output=True, text=True, timeout=60,
            )
            self.assertEqual(result.returncode, 0)
            self.assertIn("backtest_summary.json", result.stdout)
            self.assertIn("backtest_summary.md", result.stdout)


if __name__ == "__main__":
    unittest.main()
