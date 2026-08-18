# Astrowatch Blind Historical Backtest Report — ASTROWATCH-BT-001

Generated entirely from `backtest_results.db` by `scripts/generate_backtest_report.py`. No number in this document was hand-typed.

## 1. Experiment identity

- Experiment ID: `ASTROWATCH-BT-001`
- Dataset version: `ASTROWATCH-HIST-002` (`/sessions/beautiful-vibrant-fermat/work/Astrowatch-2/astrowatch/historical_events_v2.db`)
- Rule registry version (hash): `94dc2ebb02b1928fb44950f6a2464404bc730bef3e960908b48d38a43b2c59a7`
- Astronomy version (hash): `6ee2e17f6dfaf579527c59f3133418f96f9ab9f5d4ce30528f3329f8933db6c2`
- Astrowatch version: `0.1.0-experimental`
- Configuration hash: `bca4be94cf19eff054619fef7ab3f6040521150c62ad221ec7d62ae5a0a834f3`
- Random seed: `20260814`
- Sampling method: `FULL_DATASET`
- Control method: `EXISTING_CONTROL_DATES_REUSED`
- Region used: `GLOBAL` (the ONLY sensible choice: every rule's own geographic-specificity allowlist in `forecast.geographic_specificity_for_rule()` is empty, so any non-GLOBAL region would trivially exclude every rule before evaluation — see section 14)
- allow_ayanamsha_fallback: `True`
- Created: `2026-08-14T16:47:02+00:00`  Completed: `2026-08-14T16:47:10+00:00`  Frozen: `2026-08-14T16:47:10+00:00`
- Status: **COMPLETED**

## 2. Dataset integrity

- HIST-002 checksum BEFORE: `e5cabbe5115c7d115eb0ec56ae18083db028e2579b6f4b7daf2680a143dc30fa`
- HIST-002 checksum AFTER: `e5cabbe5115c7d115eb0ec56ae18083db028e2579b6f4b7daf2680a143dc30fa`
- Integrity: **UNCHANGED**

## 3. Sample composition

- Events available in ASTROWATCH-HIST-002: 140
- EVENT test cases run: 140
- CONTROL test cases run (reused, pre-existing `control_dates`): 150
- Total predictions generated: 290
- Time-precision mode breakdown (EVENT cases only):
  - `MODE_A_EXACT_TIME`: 31
  - `MODE_B_DATE_ONLY`: 100
  - `MODE_C_TIME_WINDOW`: 9
- Predictions where the rule registry fired at least one rule: 154 / 290 (0.5310)
- Ayanamsha source used, by prediction count: {'linear_fallback': 290}
- Ephemeris precision flag, by prediction count: {'MOSEPH': 290}
- Predictions flagged `astronomy_extrapolated_unvalidated` (date outside the 1900-2050 linear-ayanamsha-fallback validated range): 9

## 4. Global (binary, category-agnostic) metrics

| Metric | Value |
|---|---|
| Sample size | 290 |
| TP | 74 |
| FP | 80 |
| TN | 70 |
| FN | 66 |
| Precision | 0.4805 |
| Recall | 0.5286 |
| F1 | 0.5034 |
| Accuracy | 0.4966 |
| Specificity | 0.4667 |
| False Positive Rate | 0.5333 |
| Accuracy 95% Wilson CI | [0.4394, 0.5538] |
| Sample flag | OK |

## 5. Category-level metrics

| Category | N | TP | FP | TN | FN | Precision | Recall | F1 | Accuracy | Specificity | FPR | Flag |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| MILITARY | 290 | 3 | 64 | 201 | 22 | 0.0448 | 0.1200 | 0.0652 | 0.7034 | 0.7585 | 0.2415 | OK |
| POLITICAL | 290 | 8 | 95 | 171 | 16 | 0.0777 | 0.3333 | 0.1260 | 0.6172 | 0.6429 | 0.3571 | OK |
| ECONOMIC | 290 | 2 | 59 | 216 | 13 | 0.0328 | 0.1333 | 0.0526 | 0.7517 | 0.7855 | 0.2145 | OK |
| NATURAL_DISASTER | 290 | 17 | 60 | 192 | 21 | 0.2208 | 0.4474 | 0.2957 | 0.7207 | 0.7619 | 0.2381 | OK |
| SOCIAL_PUBLIC_HEALTH | 290 | 1 | 29 | 243 | 17 | 0.0333 | 0.0556 | 0.0417 | 0.8414 | 0.8934 | 0.1066 | OK |
| SCIENCE_TECHNOLOGY | 290 | 0 | 0 | 270 | 20 | N/A | 0.0000 | N/A | 0.9310 | 1.0000 | 0.0000 | OK |

`SCIENCE_TECHNOLOGY` has TP=0/FP=0 by construction: no rule in the current 19-rule registry documents a technology/science domain (see `backtest/category_map.py`), so this category can never be predicted positive regardless of the astronomical configuration — a real registry-coverage limitation, not a negative astrological finding.

## 6. Subtype-level metrics

34 subtypes had at least one actual occurrence among the 140 events. 34 met the n≥10 sample-size threshold (evaluated against the full 290-case pool, not just their own occurrence count) and 0 were flagged INSUFFICIENT_SAMPLE.

**Every subtype shows TP=0.** `predicted_subtypes` is always `[]` for every prediction: the current rule registry has no subtype-level rules, only category-level `domain` tags on each `Rule`. Subtype-level recall/precision in this experiment is therefore mechanically 0/undefined for all 34 subtypes — this reflects the registry's coverage, not a tested-and-failed hypothesis at the subtype level. Full subtype table is in `backtest_results.db`'s `metrics` table (`metric_level='SUBTYPE'`).

## 7. Baseline comparisons

### RANDOM

| Category | N | TP | FP | TN | FN | Precision | Recall | F1 | Accuracy |
|---|---|---|---|---|---|---|---|---|---|
| ANY | 290 | 73 | 67 | 83 | 67 | 0.5214 | 0.5214 | 0.5214 | 0.5379 |
| MILITARY | 290 | 12 | 68 | 197 | 13 | 0.1500 | 0.4800 | 0.2286 | 0.7207 |
| POLITICAL | 290 | 6 | 74 | 192 | 18 | 0.0750 | 0.2500 | 0.1154 | 0.6828 |
| ECONOMIC | 290 | 6 | 81 | 194 | 9 | 0.0690 | 0.4000 | 0.1176 | 0.6897 |
| NATURAL_DISASTER | 290 | 8 | 74 | 178 | 30 | 0.0976 | 0.2105 | 0.1333 | 0.6414 |
| SOCIAL_PUBLIC_HEALTH | 290 | 8 | 78 | 194 | 10 | 0.0930 | 0.4444 | 0.1538 | 0.6966 |
| SCIENCE_TECHNOLOGY | 290 | 10 | 74 | 196 | 10 | 0.1190 | 0.5000 | 0.1923 | 0.7103 |

### HISTORICAL_FREQUENCY

| Category | N | TP | FP | TN | FN | Precision | Recall | F1 | Accuracy |
|---|---|---|---|---|---|---|---|---|---|
| ANY | 290 | 140 | 150 | 0 | 0 | 0.4828 | 1.0000 | 0.6512 | 0.4828 |
| MILITARY | 290 | 7 | 53 | 212 | 18 | 0.1167 | 0.2800 | 0.1647 | 0.7552 |
| POLITICAL | 290 | 1 | 42 | 224 | 23 | 0.0233 | 0.0417 | 0.0299 | 0.7759 |
| ECONOMIC | 290 | 0 | 38 | 237 | 15 | 0.0000 | 0.0000 | N/A | 0.8172 |
| NATURAL_DISASTER | 290 | 7 | 68 | 184 | 31 | 0.0933 | 0.1842 | 0.1239 | 0.6586 |
| SOCIAL_PUBLIC_HEALTH | 290 | 1 | 24 | 248 | 17 | 0.0400 | 0.0556 | 0.0465 | 0.8586 |
| SCIENCE_TECHNOLOGY | 290 | 3 | 53 | 217 | 17 | 0.0536 | 0.1500 | 0.0789 | 0.7586 |

### CONTROL_DATE

| Category | N | TP | FP | TN | FN | Precision | Recall | F1 | Accuracy |
|---|---|---|---|---|---|---|---|---|---|
| ANY | 140 | 81 | 0 | 0 | 59 | 1.0000 | 0.5786 | 0.7330 | 0.5786 |
| MILITARY | 140 | 4 | 21 | 94 | 21 | 0.1600 | 0.1600 | 0.1600 | 0.7000 |
| POLITICAL | 140 | 16 | 44 | 72 | 8 | 0.2667 | 0.6667 | 0.3810 | 0.6286 |
| ECONOMIC | 140 | 1 | 19 | 106 | 14 | 0.0500 | 0.0667 | 0.0571 | 0.7643 |
| NATURAL_DISASTER | 140 | 6 | 22 | 80 | 32 | 0.2143 | 0.1579 | 0.1818 | 0.6143 |
| SOCIAL_PUBLIC_HEALTH | 140 | 2 | 10 | 112 | 16 | 0.1667 | 0.1111 | 0.1333 | 0.8143 |
| SCIENCE_TECHNOLOGY | 140 | 0 | 0 | 120 | 20 | N/A | 0.0000 | N/A | 0.8571 |

**CONTROL_DATE baseline note:** this baseline is evaluated only against the 140 EVENT test cases (each paired with its temporally-nearest reused control date's own real prediction), so every `actual_positive` in this specific evaluation is `True` by construction — precision is trivially high/undefined-favorable and specificity/FPR are undefined (no true negatives are possible in this pairing). Recall/accuracy (identical here) are the only meaningful columns for this baseline; they answer 'does the sky on the real event date beat the sky on a nearby non-selected date, using the SAME predictor and SAME rules on both.'

**HISTORICAL_FREQUENCY baseline note:** category frequencies were derived from this SAME 140-event test set (in-sample), since no separate held-out corpus exists yet — a real limitation making this a slightly optimistic (not conservative) comparator; see Known Limitations.

## 8. Event-date vs. control-date fire-rate comparison

| Category | Event N | Event fired | Event rate | Control N | Control fired | Control rate | Difference | Permutation p-value (n=10000) |
|---|---|---|---|---|---|---|---|---|
| ANY | 140 | 74 | 0.5286 | 150 | 80 | 0.5333 | -0.0048 | 1.0000 |
| MILITARY | 140 | 32 | 0.2286 | 150 | 35 | 0.2333 | -0.0048 | 1.0000 |
| POLITICAL | 140 | 49 | 0.3500 | 150 | 54 | 0.3600 | -0.0100 | 0.9000 |
| ECONOMIC | 140 | 30 | 0.2143 | 150 | 31 | 0.2067 | 0.0076 | 0.8883 |
| NATURAL_DISASTER | 140 | 38 | 0.2714 | 150 | 39 | 0.2600 | 0.0114 | 0.8937 |
| SOCIAL_PUBLIC_HEALTH | 140 | 16 | 0.1143 | 150 | 14 | 0.0933 | 0.0210 | 0.5744 |
| SCIENCE_TECHNOLOGY | 140 | 0 | 0.0000 | 150 | 0 | 0.0000 | 0.0000 | 1.0000 |

At the global (`ANY`) level, the rule registry fired on 0.5286 of real event dates versus 0.5333 of reused, pre-existing, astrology-independent control dates — a difference of -0.0048, with a two-sided permutation p-value of 1.0000. **This is not a statistically significant difference at any conventional threshold.** No category-level comparison in the table above reached significance either. See section 12.

## 9. Confidence calibration

**NOT APPLICABLE.** `forecast.py`'s own `confidence` field is derived exclusively from `historical_sample_size`, which `forecast.py` itself always sets to `0` (no backtest existed before this one) — see `forecast._confidence_from_sample_size()`. This backtest does not modify `forecast.py` to wire its own results back into that field (doing so would be modifying the forecasting pipeline, which is out of scope and explicitly prohibited for this task), so no numeric confidence score is produced by the unmodified pipeline for any prediction in this experiment. `predictions.confidence_score` is `NULL` for all 290 rows. `calibration_bins` is empty. This is a documented limitation, not a fabricated calibration.

## 10. Statistical analysis

- Global accuracy 95% Wilson CI: [0.4394, 0.5538] (n=290)
- Event-vs-control fire-rate permutation test (10,000 iterations, seed=20260814): p=1.0000 at the global level; see section 8 for every category.
- Wilson score intervals (not a naive normal approximation) were used throughout given the small sample size and rates that are not centered near 0.5 for several categories.
- A permutation test (not a t-test) was used for the event-vs-control comparison: the outcome variable is a simple binary rate, the two group sizes are unequal (140 vs 150), and a t-test's normality assumption is not well justified at this scale.

## 11. Multiple-testing warning

This report presents 6 category-level comparisons plus 1 global comparison (7 total) in section 8 alone, plus 34 subtype-level metrics in section 6, plus 3 baselines × 7 category-slices in section 7. **No correction for multiple comparisons (e.g. Bonferroni) has been applied**, and none of the reported p-values reach significance even uncorrected — but if a future re-run of this same experiment design ever produces one nominally 'significant' cell among this many comparisons, that alone would NOT be sufficient evidence of a real effect. This experiment was run once, was not repeated looking for a better result, and no result was hidden or discarded (see `git log` for a single commit introducing this entire experiment).

## 12. Small-sample warning

The underlying dataset (`ASTROWATCH-HIST-002`) contains only 140 events total. Category-level samples range from as few as 15 (ECONOMIC) to 38 (NATURAL_DISASTER) actual events; Mode A (EXACT-TIME) events number only 31 and are drawn overwhelmingly from one category (earthquakes/tsunamis — see `HISTORICAL_DATA_QUALITY_REPORT.md`). All reported metrics carry `sample_flag` and, at global/category level, Wilson confidence intervals for exactly this reason. Subtype-level results (34 slices, most with 1-8 actual events) should not be over-interpreted even though they are technically all `n≥10` at the evaluation-pool level (see section 6) — the ACTUAL positive count per subtype is far smaller.

## 13. Self-audit tests

| Test | Result | Detail |
|---|---|---|
| blindness_label_invariance | **PASS** | p1.fired=True p2.fired=True |
| blindness_static_source_check | **PASS** | [] |
| determinism_resample_and_repredict | **PASS** | checked 5 cases |
| leakage_repeated_prediction_identical | **PASS** | jd_uts equal: True |

## 14. Known limitations

- **Live Swiss Ephemeris query unreachable in this sandbox** (same network-allowlist constraint documented throughout this project): all 290 predictions used `ayanamsha.py`'s existing, unmodified linear-fallback path (`allow_ayanamsha_fallback=True`), not the primary live-query path. See the `ayanamsha_source` breakdown in section 3 ({'linear_fallback': 290}).
- That linear fallback is only cross-validated against real Swiss Ephemeris reference points within 1900-2050 (`ayanamsha.SWISSEPH_MODE1_REFERENCE`). 9 of 290 predictions used a date outside that range (as far back as 79 CE) and are flagged `astronomy_extrapolated_unvalidated=True` — their ayanamsha value is an untested extrapolation, not just lower-precision.
- Tropical planetary longitudes were computed locally via `pyswisseph` (`backtest/ephemeris_source.py`) rather than fetched live from JPL Horizons (also network-blocked here). Every calculation fell back to Moshier semi-analytic precision (no `.se1` data files present in this sandbox) — see `ephemeris_precision_flag` breakdown in section 3 ({'MOSEPH': 290}).
- MODE_B (4 samples/day) and MODE_C (7 samples across a ±3h window) test cases had strictly more opportunities for a rule to fire than MODE_A (1 sample) cases, since a case's `predicted_fired` is the union of all its samples. See section 3's mode breakdown and the per-mode fire rates logged by `run_blind_backtest.py`.
- The registry's only implemented, evaluable trigger types are `grahayuddha_class` and `grahayuddha_defeat` (6 of 19 rules); the other 13 rules are structurally `NOT EVALUATED` (no detector implemented) on every single prediction in this experiment, not a tested-and-negative result for those rules.
- The graha-yuddha proximity thresholds used (`aspects.GRAHAYUDDHA_PLACEHOLDER_THRESHOLDS_DEG`) are themselves documented, pre-existing, UNSOURCED PLACEHOLDERS, not derived from the Bṛhat Saṃhitā text's own numeric values (the text describes them qualitatively). This backtest tests the registry AS IT EXISTS, placeholders included, per the explicit instruction not to modify it.
- The rule→category mapping used for scoring (`backtest/category_map.py`) is this backtest's own infrastructure, fixed before any prediction was run, not part of the rule registry itself.
- HISTORICAL_FREQUENCY baseline frequencies are in-sample (drawn from the same 140-event test set), not from a separate held-out corpus — see section 7.
- CONTROL_DATE baseline's precision/specificity/FPR are not meaningful (see section 7 note) — only recall/accuracy should be read from that baseline.
- No confidence calibration is possible (section 9) since the unmodified `forecast.py` never produces a numeric confidence score outside `historical_sample_size` bootstrapping, which was not wired up (out of scope for this task).
- Location data was collected per test case (`input_location_precision`) but is NOT used by any calculation in the current pipeline: `forecast.get_astronomical_snapshot()` /`get_sidereal_snapshot()` take no location parameter, and every rule's geographic-specificity allowlist (`forecast.geographic_specificity_for_rule()`) is empty — so `region='GLOBAL'` was used for every single test case (see section 1). This is a structural fact about the existing, unmodified pipeline, not a choice made to simplify this experiment.
- This was a single evaluation-oriented experiment with no train/validation/test split — there is currently no separate corpus this rule registry has never been compared against in any form; this is disclosed rather than presented as a fully held-out test.

## 15. Astrological validation claim

**NONE.** Astrowatch achieved the measured precision/recall/F1/accuracy/specificity/false-positive-rate values reported in sections 4-8 on this specific experiment, under this specific methodology and this specific 140-event dataset. At the global level, the registry's fire rate on real event dates was statistically indistinguishable from its fire rate on reused, astrology-independent control dates (permutation p=1.0000). No category-level comparison reached significance. This is not evidence that astrology works, and it is equally not strong evidence that it doesn't — a single 140-event backtest against a rule registry that can only structurally evaluate 6 of its 19 rules is not sufficient evidence for a claim in either direction. Historical correlation, even if found, would not establish causation. See section 14 for the full list of limitations that bound how much any of these numbers can be trusted.
