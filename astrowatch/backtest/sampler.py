"""
Astrowatch backtest — deterministic test-case generation.

Reads events ONLY through historical.repository.get_events() (the existing,
unmodified, read-only interface) -- never writes to historical_events_v2.db. Every
sampling method here is deterministic given (dataset_version, seed, method-specific
parameters); the seed is always recorded on the Experiment row so any test case list
can be regenerated exactly.
"""

import random
from datetime import datetime, timezone as dt_timezone
from typing import List, Optional

import historical.repository as hrepo

from .models import TestCase

SAMPLING_METHODS = (
    "FULL_DATASET", "RANDOM_EVENT_SAMPLE", "RANDOM_DATE_SAMPLE",
    "PREDEFINED_SAMPLE", "MATCHED_CONTROL_SAMPLE",
)


def _time_precision_mode_for_event(row) -> str:
    tc = row["time_confidence"]
    if tc == "EXACT" and row["start_time"]:
        return "MODE_A_EXACT_TIME"
    if tc == "APPROXIMATE" and row["start_time"]:
        return "MODE_C_TIME_WINDOW"
    return "MODE_B_DATE_ONLY"


def _event_row_to_test_case(row, experiment_id: str, generated_at: str) -> TestCase:
    mode = _time_precision_mode_for_event(row)
    return TestCase(
        test_case_id=f"TC-{row['event_id']}",
        experiment_id=experiment_id,
        case_kind="EVENT",
        source_event_id=row["event_id"],
        source_control_id=None,
        test_date=row["start_date"],
        time_precision_mode=mode,
        input_time=row["start_time"] if mode in ("MODE_A_EXACT_TIME", "MODE_C_TIME_WINDOW") else None,
        input_timezone=row["timezone"] if mode in ("MODE_A_EXACT_TIME", "MODE_C_TIME_WINDOW") else None,
        input_location_precision=row["location_confidence"],
        sample_hours_utc=[],  # filled in by predictor at prediction time, not here
        generated_at=generated_at,
    )


def sample_full_dataset(conn, dataset_version: str, experiment_id: str) -> List[TestCase]:
    """Every event in the frozen dataset version. Chosen as the PRIMARY method for
    ASTROWATCH-BT-001: the dataset is already small (140 events), so subsampling it
    would only reduce statistical power for no benefit -- see run_blind_backtest.py."""
    rows = hrepo.get_events(conn, dataset_version=dataset_version)
    generated_at = datetime.now(dt_timezone.utc).isoformat(timespec="seconds")
    return [_event_row_to_test_case(r, experiment_id, generated_at) for r in rows]


def sample_random_event_sample(conn, dataset_version: str, experiment_id: str, count: int, seed: int) -> List[TestCase]:
    rows = list(hrepo.get_events(conn, dataset_version=dataset_version))
    rng = random.Random(seed)
    chosen = rng.sample(rows, min(count, len(rows)))
    chosen.sort(key=lambda r: r["event_id"])  # deterministic output order
    generated_at = datetime.now(dt_timezone.utc).isoformat(timespec="seconds")
    return [_event_row_to_test_case(r, experiment_id, generated_at) for r in chosen]


def sample_random_date_sample(start_date: str, end_date: str, count: int, seed: int, experiment_id: str) -> List[TestCase]:
    """Test cases anchored on ARBITRARY dates (not necessarily event dates) --
    reuses historical.controls.sample_random_dates(), the EXISTING unmodified
    reproducible sampler, for the date-selection itself. These become MODE_B
    (no legitimate time is knowable for an arbitrary date) EVENT-kind... no --
    these are not tied to any specific event, so they are generated as their own
    case_kind='CONTROL'-shaped test cases with no source_event_id -- callers that
    want to know 'did anything happen on this date' should cross-reference
    historical.repository.get_events() themselves post-hoc during reveal, exactly
    like engine.py does for true CONTROL cases."""
    import historical.controls as hcontrols
    dates = hcontrols.sample_random_dates(start_date, end_date, count, seed)
    generated_at = datetime.now(dt_timezone.utc).isoformat(timespec="seconds")
    out = []
    for i, d in enumerate(dates):
        out.append(TestCase(
            test_case_id=f"TC-RDS-{seed}-{i+1:04d}",
            experiment_id=experiment_id, case_kind="CONTROL",
            source_event_id=None, source_control_id=f"RDS-{seed}-{i+1:04d}",
            test_date=d, time_precision_mode="MODE_B_DATE_ONLY",
            input_time=None, input_timezone=None, input_location_precision="UNKNOWN",
            sample_hours_utc=[], generated_at=generated_at,
        ))
    return out


def sample_predefined(conn, dataset_version: str, experiment_id: str, event_ids: List[str]) -> List[TestCase]:
    generated_at = datetime.now(dt_timezone.utc).isoformat(timespec="seconds")
    out = []
    for eid in event_ids:
        row = hrepo.get_event(conn, eid)
        if row is None:
            raise ValueError(f"event_id {eid!r} not found in dataset")
        out.append(_event_row_to_test_case(row, experiment_id, generated_at))
    return out


def sample_matched_control(conn, dataset_version: str, experiment_id: str, seed: int) -> List[TestCase]:
    """One CONTROL test case per EVENT test case, matched to the temporally-nearest
    pre-existing control_date in historical_events_v2.db's control_dates table for
    that dataset_version (read-only). Ties broken deterministically (lowest
    control_id) rather than randomly, so this method needs no seed for the matching
    itself -- seed is accepted/recorded for interface consistency with the other
    methods and to fix iteration order if ever needed."""
    event_rows = list(hrepo.get_events(conn, dataset_version=dataset_version))
    control_rows = list(hrepo.get_control_dates(conn, dataset_version=dataset_version))
    generated_at = datetime.now(dt_timezone.utc).isoformat(timespec="seconds")

    def days_since_epoch(date_str: str) -> int:
        y, m, d = (int(x) for x in date_str.split("-"))
        return datetime(y, m, d).toordinal()

    out = []
    for er in event_rows:
        try:
            ed = days_since_epoch(er["start_date"])
        except ValueError:
            continue  # dates before year 1 not representable by datetime.date -- skip matching, event still usable via FULL_DATASET
        best = None
        best_dist = None
        for cr in control_rows:
            try:
                cd = days_since_epoch(cr["date"])
            except ValueError:
                continue
            dist = abs(cd - ed)
            if best is None or dist < best_dist or (dist == best_dist and cr["control_id"] < best["control_id"]):
                best, best_dist = cr, dist
        if best is None:
            continue
        out.append(TestCase(
            test_case_id=f"TC-MATCH-{best['control_id']}",
            experiment_id=experiment_id, case_kind="CONTROL",
            source_event_id=None, source_control_id=best["control_id"],
            test_date=best["date"], time_precision_mode="MODE_B_DATE_ONLY",
            input_time=None, input_timezone=None, input_location_precision="UNKNOWN",
            sample_hours_utc=[], generated_at=generated_at,
        ))
    return out
