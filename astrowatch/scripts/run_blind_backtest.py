#!/usr/bin/env python3
"""
Astrowatch — run a full blind historical backtest experiment.

Usage:
    python3 scripts/run_blind_backtest.py --experiment-id ASTROWATCH-BT-001 [--overwrite]

Runs the ENTIRE pipeline end to end: checksum verification, experiment creation,
sampling (FULL_DATASET of ASTROWATCH-HIST-002's 140 events + all 150 existing
control_dates), blind prediction for every case, outcome reveal, scoring
(prediction_matches, per-category/subtype metrics), baselines (random,
historical-frequency, control-date), the event-vs-control fire-rate comparison
with a permutation test, the blindness/leakage/determinism self-audits, and
final post-experiment checksum re-verification. Exits non-zero (and marks the
experiment FAILED, not frozen) if anything required fails.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone as dt_timezone

ASTROWATCH_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ASTROWATCH_DIR)

import historical.database as hdb
import historical.versioning as hversioning
from backtest import (
    baselines, controls, database as bdb, engine, metrics as bmetrics,
    predictor, repository as brepo, sampler, scorer,
)
from backtest.blindness import check_predictor_source
from backtest.category_map import ALL_EVENT_CATEGORIES
from backtest.models import TestCase

HIST_DB_PATH = os.path.join(ASTROWATCH_DIR, "historical_events_v2.db")
BT_DB_PATH = os.path.join(ASTROWATCH_DIR, "backtest_results.db")
DATASET_VERSION = "ASTROWATCH-HIST-002"
RANDOM_SEED = 20260814  # same convention as HIST-002's own control-date seed
PERMUTATION_ITERATIONS = 10000


def _now():
    return datetime.now(dt_timezone.utc).isoformat(timespec="seconds")


def run(experiment_id: str, overwrite: bool):
    print(f"=== ASTROWATCH blind backtest: {experiment_id} ===")

    # ---- Step 0: verify checksum BEFORE anything else. STOP on mismatch. ----
    checksum_before = engine.verify_hist002_checksum(HIST_DB_PATH)["current"]
    print(f"[1/9] HIST-002 checksum verified BEFORE: {checksum_before}")

    # ---- Step 0b: static blindness check must pass before we trust predictor.py ----
    ok, violations = check_predictor_source()
    if not ok:
        print(f"BLINDNESS CHECK FAILED: {violations}", file=sys.stderr)
        sys.exit(1)
    print("[1/9] Static blindness check on predictor.py: PASS")

    # ---- Step 1: build + record experiment ----
    exp = engine.build_experiment(
        experiment_id=experiment_id, dataset_version=DATASET_VERSION,
        hist_db_path=HIST_DB_PATH, astrowatch_dir=ASTROWATCH_DIR, random_seed=RANDOM_SEED,
        sampling_method="FULL_DATASET", control_method="EXISTING_CONTROL_DATES_REUSED",
        allow_ayanamsha_fallback=True, test_window_start=None, test_window_end=None,
    )
    if os.path.exists(BT_DB_PATH) and not overwrite:
        bt_conn = bdb.connect(BT_DB_PATH)
        existing = brepo.get_experiment(bt_conn, experiment_id)
        if existing:
            print(f"Experiment {experiment_id} already exists in {BT_DB_PATH}. "
                  f"Refusing to overwrite (pass --overwrite to force, which requires "
                  f"a fresh experiment_id if the prior one is frozen).", file=sys.stderr)
            sys.exit(1)
    else:
        bt_conn = bdb.initialize_db(BT_DB_PATH, overwrite=overwrite)
    brepo.insert_experiment(bt_conn, exp)
    bt_conn.commit()
    print(f"[2/9] Experiment recorded. rule_registry_version={exp.rule_registry_version[:16]}... "
          f"astronomy_version={exp.astronomy_version[:16]}... seed={exp.random_seed}")

    hist_conn = hdb.connect(HIST_DB_PATH)

    # ---- Step 2: sample test cases + controls (deterministic, seeded) ----
    event_cases = sampler.sample_full_dataset(hist_conn, DATASET_VERSION, experiment_id)
    control_cases = controls.sample_existing_control_dates(hist_conn, DATASET_VERSION, experiment_id)
    print(f"[3/9] Sampled {len(event_cases)} EVENT test cases + {len(control_cases)} CONTROL test cases")

    all_cases = event_cases + control_cases
    for tc in all_cases:
        brepo.insert_test_case(bt_conn, tc)
    bt_conn.commit()

    # ---- Step 3: run every case through the blind predictor, then reveal ----
    for i, tc in enumerate(all_cases):
        engine.run_test_case(bt_conn, hist_conn, tc, experiment_id, allow_ayanamsha_fallback=True)
        if (i + 1) % 50 == 0:
            print(f"    ... {i + 1}/{len(all_cases)} cases predicted+revealed")
    bt_conn.commit()
    predictions = brepo.get_predictions(bt_conn, experiment_id)
    outcomes = brepo.get_actual_outcomes(bt_conn, experiment_id)
    print(f"[4/9] {len(predictions)} predictions generated, {len(outcomes)} outcomes revealed")

    # ---- Step 4: scoring -- prediction_matches + metrics ----
    test_case_rows = brepo.get_test_cases(bt_conn, experiment_id)
    records = bmetrics.build_case_records(test_case_rows, predictions, outcomes)

    for (tc_id, cat, pred_pos, actual_pos, outcome) in bmetrics.compute_prediction_matches(records):
        brepo.insert_prediction_match(bt_conn, experiment_id, tc_id, cat, pred_pos, actual_pos, outcome)
    bt_conn.commit()

    for m in bmetrics.compute_global_and_category_metrics(records):
        brepo.insert_metric(bt_conn, experiment_id, m)
    for m in bmetrics.compute_subtype_metrics(records):
        brepo.insert_metric(bt_conn, experiment_id, m)
    bt_conn.commit()
    print(f"[5/9] Scored: {len(records)} test cases -> metrics recorded (GLOBAL + "
          f"{len(ALL_EVENT_CATEGORIES)} categories + subtype-level)")

    mode_metrics = bmetrics.compute_metrics_by_time_precision_mode(records)
    print(f"    Fire-rate by time-precision mode: {mode_metrics}")

    # ---- Step 5: event-vs-control fire-rate comparison (with permutation test) ----
    event_records = [r for r in records if r["case_kind"] == "EVENT"]
    control_records = [r for r in records if r["case_kind"] == "CONTROL"]
    for cat in ["ANY"] + list(ALL_EVENT_CATEGORIES):
        if cat == "ANY":
            ev_fired = [r["predicted_fired"] for r in event_records]
            ct_fired = [r["predicted_fired"] for r in control_records]
        else:
            ev_fired = [cat in r["predicted_categories"] for r in event_records]
            ct_fired = [cat in r["predicted_categories"] for r in control_records]
        perm = scorer.permutation_test_fire_rate_difference(ev_fired, ct_fired, seed=RANDOM_SEED, iterations=PERMUTATION_ITERATIONS)
        row = {
            "category": cat,
            "event_case_count": len(ev_fired), "event_fired_count": sum(ev_fired),
            "event_fire_rate": (sum(ev_fired) / len(ev_fired)) if ev_fired else 0.0,
            "control_case_count": len(ct_fired), "control_fired_count": sum(ct_fired),
            "control_fire_rate": (sum(ct_fired) / len(ct_fired)) if ct_fired else 0.0,
            "rate_difference": perm["observed_difference"] if perm["observed_difference"] is not None else 0.0,
            "permutation_p_value": perm["p_value"], "permutation_iterations": perm["iterations"],
        }
        brepo.insert_control_result(bt_conn, experiment_id, row)
    bt_conn.commit()
    print(f"[6/9] Event-vs-control fire-rate comparison recorded ({PERMUTATION_ITERATIONS} permutation iterations per category)")

    # ---- Step 6: baselines ----
    event_actuals = {r["test_case_id"]: {"fired": r["actual_kind"] == "EVENT",
                                           "categories": {r["actual_category"]} if r["actual_category"] else set()}
                      for r in event_records}
    control_actuals = {r["test_case_id"]: {"fired": False, "categories": set()} for r in control_records}
    control_predictions_lookup = {r["test_case_id"]: {"fired": r["predicted_fired"], "categories": r["predicted_categories"]}
                                   for r in control_records}
    event_dates_lookup = {tc["test_case_id"]: tc["test_date"] for tc in test_case_rows if tc["case_kind"] == "EVENT"}
    control_dates_lookup = {tc["test_case_id"]: tc["test_date"] for tc in test_case_rows if tc["case_kind"] == "CONTROL"}

    baseline_sets = {
        "RANDOM": baselines.random_baseline_pairs(event_actuals, control_actuals, seed=RANDOM_SEED),
        "HISTORICAL_FREQUENCY": baselines.historical_frequency_baseline_pairs(event_actuals, control_actuals, seed=RANDOM_SEED),
        "CONTROL_DATE": baselines.control_date_baseline_pairs(event_dates_lookup, event_actuals, control_dates_lookup, control_predictions_lookup),
    }
    for name, cat_pairs in baseline_sets.items():
        for cat, pairs in cat_pairs.items():
            if not pairs:
                continue
            m = scorer.compute_metrics(scorer.confusion_counts(pairs))
            m["baseline_name"] = name
            m["category"] = cat
            brepo.insert_baseline_result(bt_conn, experiment_id, m)
    bt_conn.commit()
    print("[7/9] Baselines computed: RANDOM, HISTORICAL_FREQUENCY, CONTROL_DATE")

    # ---- Step 7: self-audit tests (blindness / leakage / determinism) ----
    audit_results = _run_self_audits(bt_conn, hist_conn, experiment_id)
    for name, (result, detail) in audit_results.items():
        brepo.insert_audit_test(bt_conn, experiment_id, name, result, detail, _now())
    bt_conn.commit()
    print(f"[8/9] Self-audits: {[(k, v[0]) for k, v in audit_results.items()]}")

    # ---- Step 8: verify checksum AFTER, freeze experiment ----
    checksum_after_result = hversioning.validate_frozen_checksum(HIST_DB_PATH)
    checksum_after = checksum_after_result["current"]
    integrity = "UNCHANGED" if checksum_after == checksum_before else "CHANGED"
    status = "COMPLETED" if integrity == "UNCHANGED" and all(v[0] == "PASS" for v in audit_results.values()) else "FAILED"
    brepo.update_experiment_completion(bt_conn, experiment_id, _now(), checksum_after, integrity, status)
    bt_conn.commit()
    print(f"[9/9] HIST-002 checksum AFTER: {checksum_after} -> integrity={integrity}, experiment status={status}")

    if status == "COMPLETED":
        brepo.freeze_experiment(bt_conn, experiment_id, _now())
        bt_conn.commit()
        print(f"Experiment {experiment_id} FROZEN.")
    else:
        print(f"Experiment {experiment_id} NOT frozen (status={status}) -- see audit_tests / dataset_integrity.", file=sys.stderr)

    bt_conn.close()
    hist_conn.close()
    return status


def _run_self_audits(bt_conn, hist_conn, experiment_id: str):
    from backtest.models import BlindInput
    results = {}

    # Blindness: static source check (already run earlier, re-check here for the record)
    ok, violations = check_predictor_source()
    results["blindness_static_source_check"] = ("PASS" if ok else "FAIL", json.dumps(violations))

    # Blindness: same BlindInput -> same prediction regardless of test_case_id label
    bi = BlindInput(test_case_id="AUDIT-A", date="2011-03-11", time_precision_mode="MODE_A_EXACT_TIME",
                     time_hhmm="05:46", timezone="UTC", location_precision="EXACT")
    bi2 = BlindInput(test_case_id="AUDIT-B-RELABELED", date=bi.date, time_precision_mode=bi.time_precision_mode,
                      time_hhmm=bi.time_hhmm, timezone=bi.timezone, location_precision=bi.location_precision)
    p1 = predictor.predict(bi, "AUDIT", "AUDIT-P1")
    p2 = predictor.predict(bi2, "AUDIT", "AUDIT-P2")
    label_invariant = (p1.predicted_fired == p2.predicted_fired and
                        p1.predicted_categories == p2.predicted_categories and
                        p1.rule_matches == p2.rule_matches)
    results["blindness_label_invariance"] = ("PASS" if label_invariant else "FAIL",
                                               f"p1.fired={p1.predicted_fired} p2.fired={p2.predicted_fired}")

    # Leakage: re-run identical BlindInput after "changing" what it would be revealed
    # as -- prediction must be byte-identical.
    p3 = predictor.predict(bi, "AUDIT", "AUDIT-P3")
    leakage_ok = (p1.predicted_fired == p3.predicted_fired and
                  p1.predicted_categories == p3.predicted_categories and
                  p1.rule_matches == p3.rule_matches and
                  p1.astronomical_inputs_jd_ut == p3.astronomical_inputs_jd_ut)
    results["leakage_repeated_prediction_identical"] = ("PASS" if leakage_ok else "FAIL",
                                                           f"jd_uts equal: {p1.astronomical_inputs_jd_ut == p3.astronomical_inputs_jd_ut}")

    # Determinism: re-sample + re-predict a handful of real cases, compare.
    cases_a = sampler.sample_full_dataset(hist_conn, DATASET_VERSION, "AUDIT-DET")[:5]
    cases_b = sampler.sample_full_dataset(hist_conn, DATASET_VERSION, "AUDIT-DET")[:5]
    det_ok = all(a.test_case_id == b.test_case_id and a.time_precision_mode == b.time_precision_mode
                 for a, b in zip(cases_a, cases_b))
    for a, b in zip(cases_a, cases_b):
        pa = predictor.predict(a.to_blind_input(), "AUDIT-DET", f"P-{a.test_case_id}-a")
        pb = predictor.predict(b.to_blind_input(), "AUDIT-DET", f"P-{b.test_case_id}-b")
        if pa.predicted_fired != pb.predicted_fired or pa.rule_matches != pb.rule_matches:
            det_ok = False
    results["determinism_resample_and_repredict"] = ("PASS" if det_ok else "FAIL", f"checked {len(cases_a)} cases")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-id", default="ASTROWATCH-BT-001")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    status = run(args.experiment_id, args.overwrite)
    sys.exit(0 if status == "COMPLETED" else 1)
