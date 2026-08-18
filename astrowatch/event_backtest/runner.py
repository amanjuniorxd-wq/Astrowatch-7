"""
event_backtest/runner.py
==========================
CLI entry point.

    python -m event_backtest.runner --list-events
    python -m event_backtest.runner --event cricket_wc_2023 --model complete
    python -m event_backtest.runner --dataset cricket-wc-finals --model complete --report
    python -m event_backtest.runner --ablation --report

REPRODUCIBILITY: every run prints the dataset version, model version(s), and
(if --report is given) writes that same information into
reports/backtest_summary.json's "dataset_version"/"model_variant" fields --
running the identical command again against unchanged code/data produces
identical output (no random seeds are used anywhere in this deterministic,
rule-based pipeline).
"""
import argparse
import sys

from event_backtest import dataset as dataset_module
from event_backtest import engine
from event_backtest import report as report_module
from event_backtest.cutoff import HindsightError
from prediction.scorer import MODEL_VARIANTS


def main(argv=None):
    parser = argparse.ArgumentParser(description="Astrowatch historical event backtest runner")
    parser.add_argument("--list-events", action="store_true", help="List all events in the dataset and exit.")
    parser.add_argument("--event", type=str, default=None, help="Run a single event by event_id.")
    parser.add_argument("--cutoff", type=str, default=None,
                         help="Override the cutoff date for --event (ISO8601). Defaults to the dataset's own cutoff.")
    parser.add_argument("--dataset", type=str, default=dataset_module.DATASET_VERSION,
                         help="Dataset identifier (currently only the cricket World Cup finals dataset exists).")
    parser.add_argument("--model", type=str, default="complete", choices=list(MODEL_VARIANTS.keys()),
                         help="Model variant to run.")
    parser.add_argument("--ablation", action="store_true", help="Run every model variant and compare.")
    parser.add_argument("--report", action="store_true", help="Write reports/backtest_summary.{json,md}.")
    args = parser.parse_args(argv)

    if args.list_events:
        for e in dataset_module.list_events(include_excluded=True):
            flag = " [EXCLUDED]" if e.excluded else ""
            print(f"{e.event_id}  cutoff={e.prediction_cutoff_date}  event_date={e.event_date}  "
                  f"candidates={[c.candidate_id for c in e.candidates]}{flag}")
        return 0

    if args.event:
        event = dataset_module.get_event(args.event)
        if event is None:
            print(f"Unknown event_id: {args.event!r}. Run --list-events to see valid ids.", file=sys.stderr)
            return 1
        if args.cutoff:
            from dataclasses import replace
            event = replace(event, prediction_cutoff_date=args.cutoff)
        events = [event]
    else:
        events = dataset_module.list_events()

    print(f"Dataset: {args.dataset}  Events: {len(events)}  Model: {args.model}")

    hindsight_violations = []
    try:
        evaluated = engine.run_all(events, model_variant=args.model)
    except HindsightError as exc:
        print(f"HindsightError: {exc}", file=sys.stderr)
        hindsight_violations.append(str(exc))
        return 1

    for e in evaluated:
        print(f"  {e.event_id}: status={e.status} predicted={e.predicted_winner} "
              f"actual={e.actual_winner} correct={e.correct} brier={e.brier}")

    ablation_results = None
    if args.ablation:
        print("\nRunning ablation across all model variants...")
        ablation_results = engine.run_ablation(events)
        for variant, r in ablation_results.items():
            a = r["aggregate"]
            print(f"  {variant:20s} n_ok={a.n_ok} top1_acc={a.top1_accuracy} "
                  f"brier={a.mean_brier} log_loss={a.mean_log_loss}")

    if args.report:
        data = report_module.build_report_data(evaluated, events, ablation_results=ablation_results,
                                                 model_variant=args.model)
        data["hindsight_violations"] = hindsight_violations
        json_path = report_module.write_json(data)
        md_path = report_module.write_markdown(data)
        print(f"\nWrote {json_path}")
        print(f"Wrote {md_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
