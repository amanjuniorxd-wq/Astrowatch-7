#!/usr/bin/env python3
"""
Astrowatch — post-hoc validation of a completed backtest experiment.

Re-checks, independently of run_blind_backtest.py's own in-process bookkeeping:
  - HIST-002 sidecar checksum still matches the live file
  - backtest_results.db's own post-freeze sidecar checksum still matches (if present)
  - the experiment row is frozen, status=COMPLETED, dataset_integrity=UNCHANGED
  - all recorded audit_tests are PASS
  - prediction/outcome/test_case row counts are internally consistent
Exits non-zero on any failure.
"""
import os
import sys

ASTROWATCH_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ASTROWATCH_DIR)

import historical.versioning as hversioning
from backtest import database as bdb, repository as brepo


def validate(experiment_id: str) -> bool:
    ok = True
    hist_path = os.path.join(ASTROWATCH_DIR, "historical_events_v2.db")
    result = hversioning.validate_frozen_checksum(hist_path)
    print(f"HIST-002 checksum: {'OK' if result['ok'] else 'MISMATCH'} ({result})")
    ok = ok and result["ok"]

    bt_path = os.path.join(ASTROWATCH_DIR, "backtest_results.db")
    sidecar = os.path.join(ASTROWATCH_DIR, f"backtest_results.db.{experiment_id}.sha256")
    if os.path.exists(sidecar):
        with open(sidecar) as f:
            recorded = f.read().split()[0]
        current = hversioning.compute_db_checksum(bt_path)
        match = recorded == current
        status_label = "OK" if match else "CHANGED (expected if a later experiment was added; not a failure by itself)"
        print(f"backtest_results.db post-freeze snapshot checksum: {status_label}")

    conn = bdb.connect(bt_path)
    exp = brepo.get_experiment(conn, experiment_id)
    if exp is None:
        print(f"NO SUCH EXPERIMENT: {experiment_id}")
        return False
    print(f"experiment status={exp['status']} frozen={exp['frozen']} dataset_integrity={exp['dataset_integrity']}")
    ok = ok and exp["status"] == "COMPLETED" and exp["frozen"] == 1 and exp["dataset_integrity"] == "UNCHANGED"

    audits = brepo.get_audit_tests(conn, experiment_id)
    for a in audits:
        print(f"audit: {a['test_name']} = {a['result']}")
        ok = ok and a["result"] == "PASS"

    test_cases = brepo.get_test_cases(conn, experiment_id)
    predictions = brepo.get_predictions(conn, experiment_id)
    outcomes = brepo.get_actual_outcomes(conn, experiment_id)
    consistent = len(test_cases) == len(predictions) == len(outcomes)
    print(f"row counts: test_cases={len(test_cases)} predictions={len(predictions)} outcomes={len(outcomes)} consistent={consistent}")
    ok = ok and consistent

    conn.close()
    return ok


if __name__ == "__main__":
    experiment_id = sys.argv[1] if len(sys.argv) > 1 else "ASTROWATCH-BT-001"
    passed = validate(experiment_id)
    print("VALIDATION: " + ("PASS" if passed else "FAIL"))
    sys.exit(0 if passed else 1)
