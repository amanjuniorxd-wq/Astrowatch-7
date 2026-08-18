"""
Astrowatch backtest — backtest_results.db repository layer.

All raw SQL for the backtest results database lives here, same convention as
historical/repository.py. This module's write functions ONLY ever target
backtest_results.db. Anywhere this module needs to READ from the historical
database, it takes an already-open sqlite3.Connection from the caller (engine.py),
which itself only ever opens historical_events_v2.db via historical.database.connect()
-- a connection this module never writes through.
"""

import json
import sqlite3
from typing import List, Optional

from .models import ActualOutcome, Experiment, Prediction, TestCase


def insert_experiment(conn: sqlite3.Connection, e: Experiment) -> None:
    conn.execute(
        """INSERT INTO experiments
           (experiment_id, dataset_version, dataset_db_path, dataset_checksum_before,
            dataset_checksum_after, dataset_integrity, rule_registry_version,
            astronomy_version, astrowatch_version, random_seed, sampling_method,
            test_window_start, test_window_end, control_method, region_used,
            allow_ayanamsha_fallback, configuration_hash, created_at, completed_at,
            status, frozen, frozen_at, notes)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (e.experiment_id, e.dataset_version, e.dataset_db_path,
         e.dataset_checksum_before, e.dataset_checksum_after, e.dataset_integrity,
         e.rule_registry_version, e.astronomy_version, e.astrowatch_version,
         e.random_seed, e.sampling_method, e.test_window_start, e.test_window_end,
         e.control_method, e.region_used, int(e.allow_ayanamsha_fallback),
         e.configuration_hash, e.created_at, e.completed_at, e.status,
         int(e.frozen), e.frozen_at, e.notes),
    )


def update_experiment_completion(
    conn: sqlite3.Connection, experiment_id: str, completed_at: str,
    dataset_checksum_after: str, dataset_integrity: str, status: str,
) -> None:
    conn.execute(
        """UPDATE experiments
           SET completed_at = ?, dataset_checksum_after = ?, dataset_integrity = ?, status = ?
           WHERE experiment_id = ?""",
        (completed_at, dataset_checksum_after, dataset_integrity, status, experiment_id),
    )


def freeze_experiment(conn: sqlite3.Connection, experiment_id: str, frozen_at: str) -> None:
    conn.execute(
        "UPDATE experiments SET frozen = 1, frozen_at = ? WHERE experiment_id = ?",
        (frozen_at, experiment_id),
    )


def get_experiment(conn: sqlite3.Connection, experiment_id: str) -> Optional[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM experiments WHERE experiment_id = ?", (experiment_id,)
    ).fetchone()


def insert_test_case(conn: sqlite3.Connection, tc: TestCase) -> None:
    conn.execute(
        """INSERT INTO test_cases
           (test_case_id, experiment_id, case_kind, source_event_id, source_control_id,
            test_date, time_precision_mode, input_time, input_timezone,
            input_location_precision, sample_hours_utc, generated_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        (tc.test_case_id, tc.experiment_id, tc.case_kind, tc.source_event_id,
         tc.source_control_id, tc.test_date, tc.time_precision_mode, tc.input_time,
         tc.input_timezone, tc.input_location_precision,
         json.dumps(tc.sample_hours_utc), tc.generated_at),
    )


def get_test_cases(conn: sqlite3.Connection, experiment_id: str) -> List[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM test_cases WHERE experiment_id = ? ORDER BY test_case_id",
        (experiment_id,),
    ).fetchall()


def insert_prediction(conn: sqlite3.Connection, p: Prediction) -> None:
    conn.execute(
        """INSERT INTO predictions
           (prediction_id, experiment_id, test_case_id, predicted_at, predicted_fired,
            predicted_categories, predicted_subtypes, rule_matches, confidence_score,
            astronomical_inputs_jd_ut, ayanamsha_source, ephemeris_precision_flag,
            panchang_snapshot, rashi_nakshatra_snapshot, raw_rule_evaluations,
            astronomy_extrapolated_unvalidated)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (p.prediction_id, p.experiment_id, p.test_case_id, p.predicted_at,
         int(p.predicted_fired), json.dumps(p.predicted_categories),
         json.dumps(p.predicted_subtypes), json.dumps(p.rule_matches),
         p.confidence_score, json.dumps(p.astronomical_inputs_jd_ut),
         p.ayanamsha_source, p.ephemeris_precision_flag,
         json.dumps(p.panchang_snapshot), json.dumps(p.rashi_nakshatra_snapshot),
         json.dumps(p.raw_rule_evaluations), int(p.astronomy_extrapolated_unvalidated)),
    )


def get_prediction_for_test_case(conn: sqlite3.Connection, experiment_id: str, test_case_id: str) -> Optional[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM predictions WHERE experiment_id = ? AND test_case_id = ?",
        (experiment_id, test_case_id),
    ).fetchone()


def get_predictions(conn: sqlite3.Connection, experiment_id: str) -> List[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM predictions WHERE experiment_id = ? ORDER BY test_case_id",
        (experiment_id,),
    ).fetchall()


def insert_actual_outcome(conn: sqlite3.Connection, a: ActualOutcome) -> None:
    # Enforce prediction-before-reveal at the repository layer, not just by caller
    # discipline: refuse to insert an outcome for a test_case_id with no prediction row.
    existing = conn.execute(
        "SELECT 1 FROM predictions WHERE experiment_id = ? AND test_case_id = ?",
        (a.experiment_id, a.test_case_id),
    ).fetchone()
    if not existing:
        raise RuntimeError(
            f"Refusing to insert actual_events for test_case_id={a.test_case_id!r}: "
            f"no predictions row exists yet for experiment {a.experiment_id!r}. "
            f"Outcomes may only be revealed AFTER a prediction is recorded."
        )
    conn.execute(
        """INSERT INTO actual_events
           (test_case_id, experiment_id, revealed_at, actual_kind, actual_event_id,
            actual_category, actual_subtype, actual_event_name)
           VALUES (?,?,?,?,?,?,?,?)""",
        (a.test_case_id, a.experiment_id, a.revealed_at, a.actual_kind,
         a.actual_event_id, a.actual_category, a.actual_subtype, a.actual_event_name),
    )


def get_actual_outcomes(conn: sqlite3.Connection, experiment_id: str) -> List[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM actual_events WHERE experiment_id = ? ORDER BY test_case_id",
        (experiment_id,),
    ).fetchall()


def insert_prediction_match(
    conn: sqlite3.Connection, experiment_id: str, test_case_id: str, category: str,
    predicted_positive: bool, actual_positive: bool, outcome: str,
) -> None:
    conn.execute(
        """INSERT INTO prediction_matches
           (experiment_id, test_case_id, category, predicted_positive, actual_positive, outcome)
           VALUES (?,?,?,?,?,?)""",
        (experiment_id, test_case_id, category, int(predicted_positive),
         int(actual_positive), outcome),
    )


def get_prediction_matches(conn: sqlite3.Connection, experiment_id: str, category: Optional[str] = None) -> List[sqlite3.Row]:
    if category:
        return conn.execute(
            "SELECT * FROM prediction_matches WHERE experiment_id = ? AND category = ?",
            (experiment_id, category),
        ).fetchall()
    return conn.execute(
        "SELECT * FROM prediction_matches WHERE experiment_id = ?", (experiment_id,)
    ).fetchall()


def insert_metric(conn: sqlite3.Connection, experiment_id: str, row: dict) -> None:
    conn.execute(
        """INSERT INTO metrics
           (experiment_id, metric_level, category, subtype, sample_size, tp, fp, tn, fn,
            precision, recall, f1, accuracy, specificity, false_positive_rate,
            wilson_ci_low_accuracy, wilson_ci_high_accuracy, sample_flag, notes)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (experiment_id, row["metric_level"], row.get("category"), row.get("subtype"),
         row["sample_size"], row["tp"], row["fp"], row["tn"], row["fn"],
         row.get("precision"), row.get("recall"), row.get("f1"), row.get("accuracy"),
         row.get("specificity"), row.get("false_positive_rate"),
         row.get("wilson_ci_low_accuracy"), row.get("wilson_ci_high_accuracy"),
         row.get("sample_flag", "OK"), row.get("notes")),
    )


def get_metrics(conn: sqlite3.Connection, experiment_id: str) -> List[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM metrics WHERE experiment_id = ?", (experiment_id,)
    ).fetchall()


def insert_baseline_result(conn: sqlite3.Connection, experiment_id: str, row: dict) -> None:
    conn.execute(
        """INSERT INTO baseline_results
           (experiment_id, baseline_name, category, tp, fp, tn, fn, precision, recall,
            f1, accuracy, specificity, false_positive_rate, sample_flag)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (experiment_id, row["baseline_name"], row["category"], row["tp"], row["fp"],
         row["tn"], row["fn"], row.get("precision"), row.get("recall"), row.get("f1"),
         row.get("accuracy"), row.get("specificity"), row.get("false_positive_rate"),
         row.get("sample_flag", "OK")),
    )


def get_baseline_results(conn: sqlite3.Connection, experiment_id: str) -> List[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM baseline_results WHERE experiment_id = ?", (experiment_id,)
    ).fetchall()


def insert_control_result(conn: sqlite3.Connection, experiment_id: str, row: dict) -> None:
    conn.execute(
        """INSERT INTO control_results
           (experiment_id, category, event_case_count, event_fired_count,
            event_fire_rate, control_case_count, control_fired_count,
            control_fire_rate, rate_difference, permutation_p_value, permutation_iterations)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (experiment_id, row["category"], row["event_case_count"], row["event_fired_count"],
         row["event_fire_rate"], row["control_case_count"], row["control_fired_count"],
         row["control_fire_rate"], row["rate_difference"], row.get("permutation_p_value"),
         row.get("permutation_iterations")),
    )


def get_control_results(conn: sqlite3.Connection, experiment_id: str) -> List[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM control_results WHERE experiment_id = ?", (experiment_id,)
    ).fetchall()


def insert_calibration_bin(conn: sqlite3.Connection, experiment_id: str, row: dict) -> None:
    conn.execute(
        """INSERT INTO calibration_bins
           (experiment_id, bin_label, predicted_confidence_mid, case_count, actual_success_rate)
           VALUES (?,?,?,?,?)""",
        (experiment_id, row["bin_label"], row.get("predicted_confidence_mid"),
         row["case_count"], row.get("actual_success_rate")),
    )


def insert_audit_test(conn: sqlite3.Connection, experiment_id: str, test_name: str, result: str, detail: str, run_at: str) -> None:
    conn.execute(
        """INSERT INTO audit_tests (experiment_id, test_name, result, detail, run_at)
           VALUES (?,?,?,?,?)""",
        (experiment_id, test_name, result, detail, run_at),
    )


def get_audit_tests(conn: sqlite3.Connection, experiment_id: str) -> List[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM audit_tests WHERE experiment_id = ?", (experiment_id,)
    ).fetchall()
