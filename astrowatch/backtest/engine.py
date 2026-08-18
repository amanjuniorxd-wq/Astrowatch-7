"""
Astrowatch backtest — orchestration engine.

Enforces the exact ordering required by the spec's CORE PRINCIPLE:

  FROZEN DATASET -> SELECT TEST DATE -> HIDE LABEL -> ASTRONOMICAL CALC -> ... ->
  PREDICTION -> ONLY THEN REVEAL -> COMPARE -> STATISTICAL EVALUATION

run_test_case() is the load-bearing function: it calls predictor.predict() (which
receives only a BlindInput) and WRITES the resulting Prediction to
backtest_results.db BEFORE it ever looks at the source event's actual category/
outcome. Only after the prediction row exists does it construct and store an
ActualOutcome. repository.insert_actual_outcome() itself refuses to insert an
outcome row if no prediction row exists yet for that test_case_id -- a second,
independent enforcement of the ordering, not just caller discipline.
"""

import os
from datetime import datetime, timezone as dt_timezone
from typing import List, Optional

import historical.database as hdb
import historical.repository as hrepo
import historical.versioning as hversioning

from . import database as bdb
from . import repository as brepo
from . import sampler, controls, predictor, reproducibility
from .models import ActualOutcome, Experiment, Prediction, TestCase


class ChecksumMismatchError(Exception):
    pass


def verify_hist002_checksum(hist_db_path: str) -> dict:
    result = hversioning.validate_frozen_checksum(hist_db_path)
    if not result["ok"]:
        raise ChecksumMismatchError(
            f"HIST-002 checksum mismatch at {hist_db_path}: recorded="
            f"{result.get('recorded')!r} current={result.get('current')!r}. "
            f"STOPPING per spec item 7/32 -- do not proceed."
        )
    return result


def _reveal_event_outcome(hist_conn, test_case: TestCase, experiment_id: str) -> ActualOutcome:
    row = hrepo.get_event(hist_conn, test_case.source_event_id)
    return ActualOutcome(
        test_case_id=test_case.test_case_id,
        experiment_id=experiment_id,
        revealed_at=datetime.now(dt_timezone.utc).isoformat(timespec="seconds"),
        actual_kind="EVENT",
        actual_event_id=row["event_id"],
        actual_category=row["event_type"],
        actual_subtype=row["event_subtype"],
        actual_event_name=row["event_name"],
    )


def _reveal_control_outcome(test_case: TestCase, experiment_id: str) -> ActualOutcome:
    return ActualOutcome(
        test_case_id=test_case.test_case_id,
        experiment_id=experiment_id,
        revealed_at=datetime.now(dt_timezone.utc).isoformat(timespec="seconds"),
        actual_kind="PRESUMED_NO_EVENT",
    )


def run_test_case(bt_conn, hist_conn, test_case: TestCase, experiment_id: str,
                   allow_ayanamsha_fallback: bool) -> None:
    # 1. HIDE LABEL / PREDICT -- predictor receives ONLY the blinded input.
    blind_input = test_case.to_blind_input()
    prediction = predictor.predict(
        blind_input, experiment_id=experiment_id,
        prediction_id=f"PRED-{test_case.test_case_id}",
        allow_ayanamsha_fallback=allow_ayanamsha_fallback,
    )
    brepo.insert_prediction(bt_conn, prediction)  # written BEFORE any reveal

    # 2. REVEAL -- only now do we look at the actual event/control outcome.
    if test_case.case_kind == "EVENT":
        outcome = _reveal_event_outcome(hist_conn, test_case, experiment_id)
    else:
        outcome = _reveal_control_outcome(test_case, experiment_id)
    brepo.insert_actual_outcome(bt_conn, outcome)  # repository enforces prediction-first


def build_experiment(
    experiment_id: str, dataset_version: str, hist_db_path: str,
    astrowatch_dir: str, random_seed: int, sampling_method: str,
    control_method: str, allow_ayanamsha_fallback: bool,
    test_window_start: Optional[str], test_window_end: Optional[str],
) -> Experiment:
    checksum_result = verify_hist002_checksum(hist_db_path)
    rule_hash = reproducibility.rule_registry_version_hash()
    astro_hash = reproducibility.astronomy_version_hash(astrowatch_dir)

    import forecast  # existing, unmodified -- for ASTROWATCH_VERSION only
    config = {
        "dataset_version": dataset_version, "random_seed": random_seed,
        "sampling_method": sampling_method, "control_method": control_method,
        "allow_ayanamsha_fallback": allow_ayanamsha_fallback,
        "region_used": "GLOBAL", "rule_registry_hash": rule_hash["hash_sha256"],
        "astronomy_hash": astro_hash["hash_sha256"],
    }
    return Experiment(
        experiment_id=experiment_id,
        dataset_version=dataset_version,
        dataset_db_path=hist_db_path,
        dataset_checksum_before=checksum_result["current"],
        rule_registry_version=rule_hash["hash_sha256"],
        astronomy_version=astro_hash["hash_sha256"],
        astrowatch_version=forecast.ASTROWATCH_VERSION,
        random_seed=random_seed,
        sampling_method=sampling_method,
        control_method=control_method,
        configuration_hash=reproducibility.configuration_hash(config),
        created_at=datetime.now(dt_timezone.utc).isoformat(timespec="seconds"),
        region_used="GLOBAL",
        allow_ayanamsha_fallback=allow_ayanamsha_fallback,
        test_window_start=test_window_start,
        test_window_end=test_window_end,
    )
