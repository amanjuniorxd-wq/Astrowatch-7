"""
Astrowatch backtest — turns recorded predictions + revealed outcomes into
prediction_matches rows and GLOBAL/CATEGORY/SUBTYPE metrics rows.

Runs strictly AFTER both predictions and actual_events already exist in
backtest_results.db for the experiment -- this module never calls predictor.predict()
itself and never reads historical_events_v2.db.
"""

import json
from typing import Dict, List, Tuple

from .category_map import ALL_EVENT_CATEGORIES
from . import scorer


def build_case_records(test_cases, predictions, actual_outcomes) -> List[dict]:
    """Joins the three already-recorded row sets (from backtest_results.db) into
    one record per test case: {test_case_id, case_kind, time_precision_mode,
    predicted_fired, predicted_categories, actual_kind, actual_category}."""
    pred_by_case = {p["test_case_id"]: p for p in predictions}
    outcome_by_case = {o["test_case_id"]: o for o in actual_outcomes}
    out = []
    for tc in test_cases:
        p = pred_by_case[tc["test_case_id"]]
        o = outcome_by_case[tc["test_case_id"]]
        out.append({
            "test_case_id": tc["test_case_id"],
            "case_kind": tc["case_kind"],
            "time_precision_mode": tc["time_precision_mode"],
            "predicted_fired": bool(p["predicted_fired"]),
            "predicted_categories": set(json.loads(p["predicted_categories"])),
            "predicted_subtypes": set(json.loads(p["predicted_subtypes"])),
            "actual_kind": o["actual_kind"],
            "actual_category": o["actual_category"],
            "actual_subtype": o["actual_subtype"],
        })
    return out


def compute_prediction_matches(records: List[dict]) -> List[Tuple[str, str, bool, bool, str]]:
    """Returns (test_case_id, category, predicted_positive, actual_positive, outcome)
    rows for category='ANY' plus every one of the 6 controlled categories."""
    rows = []
    for r in records:
        actual_positive_any = r["actual_kind"] == "EVENT"
        predicted_positive_any = r["predicted_fired"]
        rows.append((r["test_case_id"], "ANY", predicted_positive_any, actual_positive_any,
                     _outcome(predicted_positive_any, actual_positive_any)))
        for cat in ALL_EVENT_CATEGORIES:
            actual_positive = (r["actual_category"] == cat)
            predicted_positive = cat in r["predicted_categories"]
            rows.append((r["test_case_id"], cat, predicted_positive, actual_positive,
                         _outcome(predicted_positive, actual_positive)))
    return rows


def _outcome(predicted: bool, actual: bool) -> str:
    if predicted and actual:
        return "TP"
    if predicted and not actual:
        return "FP"
    if not predicted and not actual:
        return "TN"
    return "FN"


def compute_global_and_category_metrics(records: List[dict]) -> List[dict]:
    out = []
    any_pairs = [(r["predicted_fired"], r["actual_kind"] == "EVENT") for r in records]
    m = scorer.compute_metrics(scorer.confusion_counts(any_pairs))
    m["metric_level"] = "GLOBAL"
    m["category"] = None
    m["subtype"] = None
    out.append(m)

    for cat in ALL_EVENT_CATEGORIES:
        pairs = [(cat in r["predicted_categories"], r["actual_category"] == cat) for r in records]
        m = scorer.compute_metrics(scorer.confusion_counts(pairs))
        m["metric_level"] = "CATEGORY"
        m["category"] = cat
        m["subtype"] = None
        out.append(m)
    return out


def compute_subtype_metrics(records: List[dict]) -> List[dict]:
    subtypes_present = sorted({r["actual_subtype"] for r in records if r["actual_subtype"]})
    out = []
    for subtype in subtypes_present:
        pairs = [(subtype in r["predicted_subtypes"], r["actual_subtype"] == subtype) for r in records]
        m = scorer.compute_metrics(scorer.confusion_counts(pairs))
        m["metric_level"] = "SUBTYPE"
        m["category"] = None
        m["subtype"] = subtype
        m["notes"] = (
            "predicted_subtypes is always empty -- the current rule registry has no "
            "subtype-level rules (only category-level domain tags exist on each Rule); "
            "recall/precision at this level will trivially reflect that registry gap, "
            "not a genuine negative astrological result."
        )
        out.append(m)
    return out


def compute_metrics_by_time_precision_mode(records: List[dict]) -> Dict[str, dict]:
    """Not written to the DB schema directly (no dedicated table), but computed and
    surfaced in the report -- MODE_B/MODE_C cases get MORE sampling chances to fire
    than MODE_A cases (see predictor.py docstring), a real asymmetry worth
    reporting transparently rather than silently averaging over."""
    out = {}
    for mode in ("MODE_A_EXACT_TIME", "MODE_B_DATE_ONLY", "MODE_C_TIME_WINDOW"):
        subset = [r for r in records if r["time_precision_mode"] == mode and r["case_kind"] == "EVENT"]
        if not subset:
            out[mode] = {"sample_size": 0, "fire_rate": None}
            continue
        fired = sum(1 for r in subset if r["predicted_fired"])
        out[mode] = {"sample_size": len(subset), "fire_rate": fired / len(subset), "fired_count": fired}
    return out
