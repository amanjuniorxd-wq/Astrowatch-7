"""
event_backtest/report.py
==========================
Generates reports/backtest_summary.json and reports/backtest_summary.md from
REAL computed EvaluatedPrediction / AggregateMetrics objects -- never from
placeholder or fabricated numbers. If engine.run_all() hasn't been run yet,
there is nothing to report; this module never invents a plausible-looking
number to fill a gap.
"""
import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional

from event_backtest.metrics import EvaluatedPrediction, AggregateMetrics, aggregate
from event_backtest.calibration import compute_calibration_table, calibration_is_claimable, MIN_SAMPLE_FOR_CALIBRATION_CLAIM
from event_backtest.models import HistoricalPredictionEvent
from event_backtest import dataset as dataset_module

REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports")


def _agg_to_dict(agg: AggregateMetrics) -> Dict:
    return {
        "n_total": agg.n_total, "n_ok": agg.n_ok, "n_excluded": agg.n_excluded,
        "top1_accuracy": agg.top1_accuracy, "mean_brier": agg.mean_brier,
        "mean_log_loss": agg.mean_log_loss, "mean_reciprocal_rank": agg.mean_reciprocal_rank,
        "mean_predicted_rank_of_actual": agg.mean_predicted_rank_of_actual,
        "by_event_type": {k: _agg_to_dict(v) for k, v in agg.by_event_type.items()},
        "by_model_version": {k: _agg_to_dict(v) for k, v in agg.by_model_version.items()},
    }


def build_report_data(evaluated: List[EvaluatedPrediction], events: List[HistoricalPredictionEvent],
                       ablation_results: Optional[Dict] = None, model_variant: str = "complete") -> Dict:
    events_by_id = {e.event_id: e for e in events}
    agg = aggregate(evaluated)
    calib_table = compute_calibration_table(evaluated)

    ok = [e for e in evaluated if e.status == "OK"]
    excluded = [e for e in evaluated if e.status != "OK"]
    best = sorted(ok, key=lambda e: (e.brier if e.brier is not None else 999))[:3]
    worst = sorted(ok, key=lambda e: (e.brier if e.brier is not None else -1), reverse=True)[:3]

    data = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_version": dataset_module.DATASET_VERSION,
        "model_variant": model_variant,
        "n_total_events_in_dataset": len(events),
        "n_completed": agg.n_ok,
        "n_excluded": agg.n_excluded,
        "metrics": _agg_to_dict(agg),
        "calibration": {
            "claimable": calibration_is_claimable(evaluated),
            "min_sample_required_for_claim": MIN_SAMPLE_FOR_CALIBRATION_CLAIM,
            "n_ok_predictions": len(ok),
            "bins": [
                {"low": b.low, "high": b.high, "n": b.n,
                 "mean_predicted_confidence": b.mean_predicted_confidence,
                 "actual_success_rate": b.actual_success_rate}
                for b in calib_table
            ],
            "note": ("Calibration is NOT claimed to be demonstrated -- this dataset has only "
                     f"{len(ok)} completed predictions, far below the "
                     f"{MIN_SAMPLE_FOR_CALIBRATION_CLAIM}-sample threshold this project requires "
                     "before making any calibration-quality claim (see build spec Section 12)."),
        },
        "best_predictions": [
            {"event_id": e.event_id, "event_name": events_by_id[e.event_id].event_name,
             "predicted_winner": e.predicted_winner, "actual_winner": e.actual_winner,
             "correct": e.correct, "brier": e.brier}
            for e in best
        ],
        "worst_predictions": [
            {"event_id": e.event_id, "event_name": events_by_id[e.event_id].event_name,
             "predicted_winner": e.predicted_winner, "actual_winner": e.actual_winner,
             "correct": e.correct, "brier": e.brier}
            for e in worst
        ],
        "all_predictions": [
            {"event_id": e.event_id, "event_name": events_by_id[e.event_id].event_name,
             "status": e.status, "predicted_winner": e.predicted_winner, "actual_winner": e.actual_winner,
             "correct": e.correct, "brier": e.brier, "log_loss": e.log_loss,
             "predicted_rank_of_actual": e.predicted_rank_of_actual}
            for e in evaluated
        ],
        "excluded_events": [
            {"event_id": e.event_id, "status": e.status}
            for e in excluded
        ],
        "hindsight_violations": [],  # populated by runner.py if any HindsightError was caught during the run
        "ablation": None,
    }

    if ablation_results:
        data["ablation"] = {
            variant: {"aggregate": _agg_to_dict(r["aggregate"])}
            for variant, r in ablation_results.items()
        }

    return data


def write_json(data: Dict, path: Optional[str] = None) -> str:
    path = path or os.path.join(REPORTS_DIR, "backtest_summary.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    return path


def write_markdown(data: Dict, path: Optional[str] = None) -> str:
    path = path or os.path.join(REPORTS_DIR, "backtest_summary.md")
    os.makedirs(os.path.dirname(path), exist_ok=True)

    m = data["metrics"]
    lines = []
    lines.append("# Astrowatch Event Backtest Summary")
    lines.append("")
    lines.append(f"Generated: {data['generated_at_utc']}  ")
    lines.append(f"Dataset: `{data['dataset_version']}`  ")
    lines.append(f"Model variant: `{data['model_variant']}`")
    lines.append("")
    lines.append("## Scientific status (read first)")
    lines.append("")
    lines.append(
        "This report measures the predictive performance of THIS PROJECT'S IMPLEMENTED "
        "ALGORITHM under its stated assumptions, on a very small (n={}) real historical "
        "dataset. It does NOT prove or disprove astrology scientifically, and no number "
        "below should be read as such -- see BACKTEST.md.".format(data["n_total_events_in_dataset"])
    )
    lines.append("")
    lines.append("## Overview")
    lines.append("")
    lines.append(f"- Total events in dataset: {data['n_total_events_in_dataset']}")
    lines.append(f"- Completed (status=OK): {data['n_completed']}")
    lines.append(f"- Excluded / INSUFFICIENT_DATA / DATA_UNAVAILABLE: {data['n_excluded']}")
    lines.append("")
    lines.append("## Metrics (real, computed)")
    lines.append("")
    lines.append(f"- Top-1 accuracy: {m['top1_accuracy']}")
    lines.append(f"- Mean Brier score: {m['mean_brier']}")
    lines.append(f"- Mean multiclass log loss: {m['mean_log_loss']}")
    lines.append(f"- Mean reciprocal rank: {m['mean_reciprocal_rank']}")
    lines.append(f"- Mean predicted rank of actual winner: {m['mean_predicted_rank_of_actual']}")
    lines.append("")
    lines.append("## Calibration")
    lines.append("")
    lines.append(f"- Claimable: {data['calibration']['claimable']}")
    lines.append(f"- {data['calibration']['note']}")
    lines.append("")
    lines.append("| Confidence bin | n | mean predicted confidence | actual success rate |")
    lines.append("|---|---|---|---|")
    for b in data["calibration"]["bins"]:
        lines.append(f"| {b['low']:.0%}-{b['high']:.0%} | {b['n']} | "
                      f"{b['mean_predicted_confidence']} | {b['actual_success_rate']} |")
    lines.append("")
    lines.append("## All predictions")
    lines.append("")
    lines.append("| Event | Status | Predicted | Actual | Correct | Brier | Log loss | Rank of actual |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for p in data["all_predictions"]:
        lines.append(f"| {p['event_name']} | {p['status']} | {p['predicted_winner']} | "
                      f"{p['actual_winner']} | {p['correct']} | {p['brier']} | {p['log_loss']} | "
                      f"{p['predicted_rank_of_actual']} |")
    lines.append("")

    if data.get("ablation"):
        lines.append("## Ablation (model variant comparison)")
        lines.append("")
        lines.append("**These are REAL computed results on a 6-event dataset -- far too small "
                      "for any variant difference below to be treated as statistically meaningful. "
                      "Reported for transparency, not as a validated conclusion.**")
        lines.append("")
        lines.append("| Model variant | n_ok | Top-1 accuracy | Mean Brier | Mean log loss | MRR |")
        lines.append("|---|---|---|---|---|---|")
        for variant, r in data["ablation"].items():
            a = r["aggregate"]
            lines.append(f"| {variant} | {a['n_ok']} | {a['top1_accuracy']} | {a['mean_brier']} | "
                          f"{a['mean_log_loss']} | {a['mean_reciprocal_rank']} |")
        lines.append("")

    if data["hindsight_violations"]:
        lines.append("## Hindsight violations detected")
        lines.append("")
        for v in data["hindsight_violations"]:
            lines.append(f"- {v}")
        lines.append("")

    with open(path, "w") as f:
        f.write("\n".join(lines))
    return path
