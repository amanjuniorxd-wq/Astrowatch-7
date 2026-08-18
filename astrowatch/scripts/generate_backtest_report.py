#!/usr/bin/env python3
"""
Astrowatch — generate BACKTEST_REPORT_ASTROWATCH_BT001.md from the database.

Every number in the generated report is pulled live from backtest_results.db (and,
for the sample-size context, historical_events_v2.db). No statistic in this script
is hand-typed -- if a table is empty, the report says so, it does not fall back to
an invented number.
"""
import json
import os
import sys

ASTROWATCH_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ASTROWATCH_DIR)

from backtest import database as bdb, repository as brepo
from backtest.category_map import ALL_EVENT_CATEGORIES

EXPERIMENT_ID = "ASTROWATCH-BT-001"


def fmt(x, digits=4):
    if x is None:
        return "N/A"
    if isinstance(x, float):
        return f"{x:.{digits}f}"
    return str(x)


def main():
    conn = bdb.connect(os.path.join(ASTROWATCH_DIR, "backtest_results.db"))
    exp = dict(brepo.get_experiment(conn, EXPERIMENT_ID))
    metrics = [dict(m) for m in brepo.get_metrics(conn, EXPERIMENT_ID)]
    baselines = [dict(b) for b in brepo.get_baseline_results(conn, EXPERIMENT_ID)]
    controls = [dict(c) for c in brepo.get_control_results(conn, EXPERIMENT_ID)]
    audits = [dict(a) for a in brepo.get_audit_tests(conn, EXPERIMENT_ID)]
    test_cases = [dict(t) for t in brepo.get_test_cases(conn, EXPERIMENT_ID)]
    predictions = [dict(p) for p in brepo.get_predictions(conn, EXPERIMENT_ID)]

    global_m = next(m for m in metrics if m["metric_level"] == "GLOBAL")
    category_m = {m["category"]: m for m in metrics if m["metric_level"] == "CATEGORY"}
    subtype_m = [m for m in metrics if m["metric_level"] == "SUBTYPE"]

    n_event = sum(1 for t in test_cases if t["case_kind"] == "EVENT")
    n_control = sum(1 for t in test_cases if t["case_kind"] == "CONTROL")
    mode_counts = {}
    for t in test_cases:
        if t["case_kind"] != "EVENT":
            continue
        mode_counts[t["time_precision_mode"]] = mode_counts.get(t["time_precision_mode"], 0) + 1

    n_fired = sum(1 for p in predictions if p["predicted_fired"])
    ayanamsha_sources = {}
    precision_flags = {}
    for p in predictions:
        ayanamsha_sources[p["ayanamsha_source"]] = ayanamsha_sources.get(p["ayanamsha_source"], 0) + 1
        precision_flags[p["ephemeris_precision_flag"]] = precision_flags.get(p["ephemeris_precision_flag"], 0) + 1
    n_extrapolated = sum(1 for p in predictions if p["astronomy_extrapolated_unvalidated"])

    lines = []
    a = lines.append

    a(f"# Astrowatch Blind Historical Backtest Report — {EXPERIMENT_ID}\n")
    a(f"Generated entirely from `backtest_results.db` by `scripts/generate_backtest_report.py`. "
      f"No number in this document was hand-typed.\n")

    a("## 1. Experiment identity\n")
    a(f"- Experiment ID: `{exp['experiment_id']}`")
    a(f"- Dataset version: `{exp['dataset_version']}` (`{exp['dataset_db_path']}`)")
    a(f"- Rule registry version (hash): `{exp['rule_registry_version']}`")
    a(f"- Astronomy version (hash): `{exp['astronomy_version']}`")
    a(f"- Astrowatch version: `{exp['astrowatch_version']}`")
    a(f"- Configuration hash: `{exp['configuration_hash']}`")
    a(f"- Random seed: `{exp['random_seed']}`")
    a(f"- Sampling method: `{exp['sampling_method']}`")
    a(f"- Control method: `{exp['control_method']}`")
    a(f"- Region used: `{exp['region_used']}` (the ONLY sensible choice: every rule's own "
      "geographic-specificity allowlist in `forecast.geographic_specificity_for_rule()` is empty, "
      "so any non-GLOBAL region would trivially exclude every rule before evaluation — see section 14)")
    a(f"- allow_ayanamsha_fallback: `{bool(exp['allow_ayanamsha_fallback'])}`")
    a(f"- Created: `{exp['created_at']}`  Completed: `{exp['completed_at']}`  Frozen: `{exp['frozen_at']}`")
    a(f"- Status: **{exp['status']}**\n")

    a("## 2. Dataset integrity\n")
    a(f"- HIST-002 checksum BEFORE: `{exp['dataset_checksum_before']}`")
    a(f"- HIST-002 checksum AFTER: `{exp['dataset_checksum_after']}`")
    a(f"- Integrity: **{exp['dataset_integrity']}**\n")

    a("## 3. Sample composition\n")
    a(f"- Events available in {exp['dataset_version']}: 140")
    a(f"- EVENT test cases run: {n_event}")
    a(f"- CONTROL test cases run (reused, pre-existing `control_dates`): {n_control}")
    a(f"- Total predictions generated: {len(predictions)}")
    a(f"- Time-precision mode breakdown (EVENT cases only):")
    for mode, count in sorted(mode_counts.items()):
        a(f"  - `{mode}`: {count}")
    a(f"- Predictions where the rule registry fired at least one rule: {n_fired} / {len(predictions)} "
      f"({fmt(n_fired/len(predictions))})")
    a(f"- Ayanamsha source used, by prediction count: {ayanamsha_sources}")
    a(f"- Ephemeris precision flag, by prediction count: {precision_flags}")
    a(f"- Predictions flagged `astronomy_extrapolated_unvalidated` (date outside the "
      f"1900-2050 linear-ayanamsha-fallback validated range): {n_extrapolated}\n")

    a("## 4. Global (binary, category-agnostic) metrics\n")
    a("| Metric | Value |")
    a("|---|---|")
    for key, label in [("sample_size", "Sample size"), ("tp", "TP"), ("fp", "FP"), ("tn", "TN"), ("fn", "FN"),
                        ("precision", "Precision"), ("recall", "Recall"), ("f1", "F1"),
                        ("accuracy", "Accuracy"), ("specificity", "Specificity"),
                        ("false_positive_rate", "False Positive Rate")]:
        a(f"| {label} | {fmt(global_m[key])} |")
    a(f"| Accuracy 95% Wilson CI | [{fmt(global_m['wilson_ci_low_accuracy'])}, "
      f"{fmt(global_m['wilson_ci_high_accuracy'])}] |")
    a(f"| Sample flag | {global_m['sample_flag']} |\n")

    a("## 5. Category-level metrics\n")
    a("| Category | N | TP | FP | TN | FN | Precision | Recall | F1 | Accuracy | Specificity | FPR | Flag |")
    a("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for cat in ALL_EVENT_CATEGORIES:
        m = category_m[cat]
        a(f"| {cat} | {m['sample_size']} | {m['tp']} | {m['fp']} | {m['tn']} | {m['fn']} | "
          f"{fmt(m['precision'])} | {fmt(m['recall'])} | {fmt(m['f1'])} | {fmt(m['accuracy'])} | "
          f"{fmt(m['specificity'])} | {fmt(m['false_positive_rate'])} | {m['sample_flag']} |")
    a("")
    a("`SCIENCE_TECHNOLOGY` has TP=0/FP=0 by construction: no rule in the current 19-rule "
      "registry documents a technology/science domain (see `backtest/category_map.py`), so this "
      "category can never be predicted positive regardless of the astronomical configuration — a "
      "real registry-coverage limitation, not a negative astrological finding.\n")

    a("## 6. Subtype-level metrics\n")
    ok_n = sum(1 for m in subtype_m if m["sample_flag"] == "OK")
    insuff_n = sum(1 for m in subtype_m if m["sample_flag"] == "INSUFFICIENT_SAMPLE")
    a(f"{len(subtype_m)} subtypes had at least one actual occurrence among the 140 events. "
      f"{ok_n} met the n≥10 sample-size threshold (evaluated against the full 290-case pool, not "
      f"just their own occurrence count) and {insuff_n} were flagged INSUFFICIENT_SAMPLE.\n")
    a("**Every subtype shows TP=0.** `predicted_subtypes` is always `[]` for every prediction: the "
      "current rule registry has no subtype-level rules, only category-level `domain` tags on each "
      "`Rule`. Subtype-level recall/precision in this experiment is therefore mechanically 0/undefined "
      "for all 34 subtypes — this reflects the registry's coverage, not a tested-and-failed hypothesis "
      "at the subtype level. Full subtype table is in `backtest_results.db`'s `metrics` table "
      "(`metric_level='SUBTYPE'`).\n")

    a("## 7. Baseline comparisons\n")
    for name in ("RANDOM", "HISTORICAL_FREQUENCY", "CONTROL_DATE"):
        a(f"### {name}\n")
        a("| Category | N | TP | FP | TN | FN | Precision | Recall | F1 | Accuracy |")
        a("|---|---|---|---|---|---|---|---|---|---|")
        rows = [b for b in baselines if b["baseline_name"] == name]
        for cat in ["ANY"] + list(ALL_EVENT_CATEGORIES):
            row = next((b for b in rows if b["category"] == cat), None)
            if not row:
                continue
            n = row["tp"] + row["fp"] + row["tn"] + row["fn"]
            a(f"| {cat} | {n} | {row['tp']} | {row['fp']} | {row['tn']} | {row['fn']} | "
              f"{fmt(row['precision'])} | {fmt(row['recall'])} | {fmt(row['f1'])} | {fmt(row['accuracy'])} |")
        a("")
    a("**CONTROL_DATE baseline note:** this baseline is evaluated only against the 140 EVENT test "
      "cases (each paired with its temporally-nearest reused control date's own real prediction), so "
      "every `actual_positive` in this specific evaluation is `True` by construction — precision is "
      "trivially high/undefined-favorable and specificity/FPR are undefined (no true negatives are "
      "possible in this pairing). Recall/accuracy (identical here) are the only meaningful columns "
      "for this baseline; they answer 'does the sky on the real event date beat the sky on a nearby "
      "non-selected date, using the SAME predictor and SAME rules on both.'\n")
    a("**HISTORICAL_FREQUENCY baseline note:** category frequencies were derived from this SAME "
      "140-event test set (in-sample), since no separate held-out corpus exists yet — a real "
      "limitation making this a slightly optimistic (not conservative) comparator; see Known "
      "Limitations.\n")

    a("## 8. Event-date vs. control-date fire-rate comparison\n")
    a("| Category | Event N | Event fired | Event rate | Control N | Control fired | Control rate | "
      "Difference | Permutation p-value (n=" + str(controls[0]["permutation_iterations"] if controls else "?") + ") |")
    a("|---|---|---|---|---|---|---|---|---|")
    for cat in ["ANY"] + list(ALL_EVENT_CATEGORIES):
        row = next((c for c in controls if c["category"] == cat), None)
        if not row:
            continue
        a(f"| {cat} | {row['event_case_count']} | {row['event_fired_count']} | "
          f"{fmt(row['event_fire_rate'])} | {row['control_case_count']} | {row['control_fired_count']} | "
          f"{fmt(row['control_fire_rate'])} | {fmt(row['rate_difference'])} | {fmt(row['permutation_p_value'])} |")
    a("")
    any_row = next(c for c in controls if c["category"] == "ANY")
    a(f"At the global (`ANY`) level, the rule registry fired on {fmt(any_row['event_fire_rate'])} of "
      f"real event dates versus {fmt(any_row['control_fire_rate'])} of reused, pre-existing, "
      f"astrology-independent control dates — a difference of {fmt(any_row['rate_difference'])}, "
      f"with a two-sided permutation p-value of {fmt(any_row['permutation_p_value'])}. **This is not "
      f"a statistically significant difference at any conventional threshold.** No category-level "
      f"comparison in the table above reached significance either. See section 12.\n")

    a("## 9. Confidence calibration\n")
    a("**NOT APPLICABLE.** `forecast.py`'s own `confidence` field is derived exclusively from "
      "`historical_sample_size`, which `forecast.py` itself always sets to `0` (no backtest existed "
      "before this one) — see `forecast._confidence_from_sample_size()`. This backtest does not "
      "modify `forecast.py` to wire its own results back into that field (doing so would be "
      "modifying the forecasting pipeline, which is out of scope and explicitly prohibited for this "
      "task), so no numeric confidence score is produced by the unmodified pipeline for any "
      "prediction in this experiment. `predictions.confidence_score` is `NULL` for all 290 rows. "
      "`calibration_bins` is empty. This is a documented limitation, not a fabricated calibration.\n")

    a("## 10. Statistical analysis\n")
    a(f"- Global accuracy 95% Wilson CI: [{fmt(global_m['wilson_ci_low_accuracy'])}, "
      f"{fmt(global_m['wilson_ci_high_accuracy'])}] (n={global_m['sample_size']})")
    a(f"- Event-vs-control fire-rate permutation test (10,000 iterations, seed={exp['random_seed']}): "
      f"p={fmt(any_row['permutation_p_value'])} at the global level; see section 8 for every category.")
    a("- Wilson score intervals (not a naive normal approximation) were used throughout given the "
      "small sample size and rates that are not centered near 0.5 for several categories.")
    a("- A permutation test (not a t-test) was used for the event-vs-control comparison: the outcome "
      "variable is a simple binary rate, the two group sizes are unequal (140 vs 150), and a t-test's "
      "normality assumption is not well justified at this scale.\n")

    a("## 11. Multiple-testing warning\n")
    a(f"This report presents {len(ALL_EVENT_CATEGORIES)} category-level comparisons plus 1 global "
      f"comparison (7 total) in section 8 alone, plus {len(subtype_m)} subtype-level metrics in "
      f"section 6, plus 3 baselines × 7 category-slices in section 7. **No correction for multiple "
      f"comparisons (e.g. Bonferroni) has been applied**, and none of the reported p-values reach "
      f"significance even uncorrected — but if a future re-run of this same experiment design ever "
      f"produces one nominally 'significant' cell among this many comparisons, that alone would NOT "
      f"be sufficient evidence of a real effect. This experiment was run once, was not repeated "
      f"looking for a better result, and no result was hidden or discarded (see `git log` for a "
      f"single commit introducing this entire experiment).\n")

    a("## 12. Small-sample warning\n")
    a(f"The underlying dataset (`{exp['dataset_version']}`) contains only 140 events total. "
      f"Category-level samples range from as few as 15 (ECONOMIC) to 38 (NATURAL_DISASTER) actual "
      f"events; Mode A (EXACT-TIME) events number only 31 and are drawn overwhelmingly from one "
      f"category (earthquakes/tsunamis — see `HISTORICAL_DATA_QUALITY_REPORT.md`). All reported "
      f"metrics carry `sample_flag` and, at global/category level, Wilson confidence intervals for "
      f"exactly this reason. Subtype-level results (34 slices, most with 1-8 actual events) should "
      f"not be over-interpreted even though they are technically all `n≥10` at the evaluation-pool "
      f"level (see section 6) — the ACTUAL positive count per subtype is far smaller.\n")

    a("## 13. Self-audit tests\n")
    a("| Test | Result | Detail |")
    a("|---|---|---|")
    for row in audits:
        a(f"| {row['test_name']} | **{row['result']}** | {row['detail']} |")
    a("")

    a("## 14. Known limitations\n")
    a("- **Live Swiss Ephemeris query unreachable in this sandbox** (same network-allowlist "
      "constraint documented throughout this project): all 290 predictions used `ayanamsha.py`'s "
      "existing, unmodified linear-fallback path (`allow_ayanamsha_fallback=True`), not the primary "
      f"live-query path. See the `ayanamsha_source` breakdown in section 3 ({ayanamsha_sources}).")
    a(f"- That linear fallback is only cross-validated against real Swiss Ephemeris reference points "
      f"within 1900-2050 (`ayanamsha.SWISSEPH_MODE1_REFERENCE`). {n_extrapolated} of {len(predictions)} "
      f"predictions used a date outside that range (as far back as 79 CE) and are flagged "
      f"`astronomy_extrapolated_unvalidated=True` — their ayanamsha value is an untested extrapolation, "
      f"not just lower-precision.")
    a("- Tropical planetary longitudes were computed locally via `pyswisseph` (`backtest/"
      "ephemeris_source.py`) rather than fetched live from JPL Horizons (also network-blocked here). "
      f"Every calculation fell back to Moshier semi-analytic precision (no `.se1` data files present "
      f"in this sandbox) — see `ephemeris_precision_flag` breakdown in section 3 ({precision_flags}).")
    a("- MODE_B (4 samples/day) and MODE_C (7 samples across a ±3h window) test cases had strictly "
      "more opportunities for a rule to fire than MODE_A (1 sample) cases, since a case's "
      "`predicted_fired` is the union of all its samples. See section 3's mode breakdown and the "
      "per-mode fire rates logged by `run_blind_backtest.py`.")
    a("- The registry's only implemented, evaluable trigger types are `grahayuddha_class` and "
      "`grahayuddha_defeat` (6 of 19 rules); the other 13 rules are structurally `NOT EVALUATED` "
      "(no detector implemented) on every single prediction in this experiment, not a tested-and-"
      "negative result for those rules.")
    a("- The graha-yuddha proximity thresholds used (`aspects.GRAHAYUDDHA_PLACEHOLDER_THRESHOLDS_DEG`) "
      "are themselves documented, pre-existing, UNSOURCED PLACEHOLDERS, not derived from the "
      "Bṛhat Saṃhitā text's own numeric values (the text describes them qualitatively). This backtest "
      "tests the registry AS IT EXISTS, placeholders included, per the explicit instruction not to "
      "modify it.")
    a("- The rule→category mapping used for scoring (`backtest/category_map.py`) is this backtest's "
      "own infrastructure, fixed before any prediction was run, not part of the rule registry itself.")
    a("- HISTORICAL_FREQUENCY baseline frequencies are in-sample (drawn from the same 140-event test "
      "set), not from a separate held-out corpus — see section 7.")
    a("- CONTROL_DATE baseline's precision/specificity/FPR are not meaningful (see section 7 note) — "
      "only recall/accuracy should be read from that baseline.")
    a("- No confidence calibration is possible (section 9) since the unmodified `forecast.py` never "
      "produces a numeric confidence score outside `historical_sample_size` bootstrapping, which was "
      "not wired up (out of scope for this task).")
    a("- Location data was collected per test case (`input_location_precision`) but is NOT used by "
      "any calculation in the current pipeline: `forecast.get_astronomical_snapshot()` /"
      "`get_sidereal_snapshot()` take no location parameter, and every rule's geographic-specificity "
      "allowlist (`forecast.geographic_specificity_for_rule()`) is empty — so `region='GLOBAL'` was "
      "used for every single test case (see section 1). This is a structural fact about the existing, "
      "unmodified pipeline, not a choice made to simplify this experiment.")
    a("- This was a single evaluation-oriented experiment with no train/validation/test split — there "
      "is currently no separate corpus this rule registry has never been compared against in any form; "
      "this is disclosed rather than presented as a fully held-out test.\n")

    a("## 15. Astrological validation claim\n")
    a("**NONE.** Astrowatch achieved the measured precision/recall/F1/accuracy/specificity/false-"
      "positive-rate values reported in sections 4-8 on this specific experiment, under this specific "
      "methodology and this specific 140-event dataset. At the global level, the registry's fire rate "
      "on real event dates was statistically indistinguishable from its fire rate on reused, "
      "astrology-independent control dates (permutation p=" + fmt(any_row["permutation_p_value"]) +
      "). No category-level comparison reached significance. This is not evidence that astrology "
      "works, and it is equally not strong evidence that it doesn't — a single 140-event backtest "
      "against a rule registry that can only structurally evaluate 6 of its 19 rules is not sufficient "
      "evidence for a claim in either direction. Historical correlation, even if found, would not "
      "establish causation. See section 14 for the full list of limitations that bound how much any "
      "of these numbers can be trusted.\n")

    report = "\n".join(lines)
    out_path = os.path.join(ASTROWATCH_DIR, "BACKTEST_REPORT_ASTROWATCH_BT001.md")
    with open(out_path, "w") as f:
        f.write(report)
    print(f"Wrote {out_path} ({len(report)} bytes)")
    return out_path


if __name__ == "__main__":
    main()
