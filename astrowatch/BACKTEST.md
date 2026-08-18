# Astrowatch Formal Historical Backtest Engine

This document describes the `event_backtest/` + `prediction/` system: a
formal, hindsight-protected historical backtesting engine that answers "if
Astrowatch had been run at a particular historical point in time, using
only information available at that time, what prediction would it have
produced, and how accurate was it?"

This is a SEPARATE system from the pre-existing `backtest/` package (the
ASTROWATCH-BT-001 experiment). Both are real, working, intentionally
different tools -- see "Relationship to the existing `backtest/` package"
below.

## Why this exists

Any backtest of a prediction system can be silently contaminated by
hindsight: if the code (even accidentally) has access to the actual outcome
or to information that was only published after the fact, its "prediction"
is not really a prediction at all. This engine's entire design is organized
around preventing that.

## Hindsight protection: two independent layers

1. **Per-datum, runtime provenance checks** (`event_backtest/cutoff.py`).
   Every piece of historical data used by a feature calculation carries a
   `DataProvenance` (source, source_date, availability_date). Before that
   data can be used, `enforce_cutoff()` checks that its effective
   availability date is not after the prediction's cutoff date, raising
   `HindsightError` if it is. A separate function,
   `calc_date_within_cutoff()`, additionally rejects any astronomical
   calculation whose TARGET date is after the cutoff -- a deliberately
   conservative choice (see "Known Limitations" below).

2. **Call-ordering discipline at the orchestration level**
   (`event_backtest/engine.py`). `run_one()` calls
   `prediction.predictor.predict(event.public_fields())` -- and
   `public_fields()` has no `actual_winner` key at all -- and only AFTER
   that call returns does it read `event.actual_winner` to score the
   prediction. There is no code path in this engine that reads
   `actual_winner` before `predict()` is called.

Together these mean: even if a dataset entry had `actual_winner` set (which
it always does, since it's needed for scoring), the predictor genuinely has
no way to see it, and any input data with a too-late availability date is
rejected with an exception rather than silently used.

### Test proving this works

`tests/event_backtest/test_event_backtest.py`'s
`test_future_information_is_rejected_end_to_end` constructs a
`DataProvenance` dated one day after an event's actual final and proves
`enforce_cutoff()` raises `HindsightError`. `test_predict_never_receives_actual_winner_key`
proves `HistoricalPredictionEvent.public_fields()` never contains
`actual_winner`.

## How to run it

```
python -m event_backtest.runner --list-events
python -m event_backtest.runner --event cricket_wc_2023 --model complete
python -m event_backtest.runner --model complete --report
python -m event_backtest.runner --ablation --report
```

`--report` writes `reports/backtest_summary.json` and
`reports/backtest_summary.md`.

## Dataset structure

The primary dataset (`event_backtest/dataset.py`, `DATASET_VERSION =
"cricket-wc-finals-v1"`) is the 6 ICC Men's Cricket World Cup finals,
2003-2023 -- finalists only (2 candidates per event), per the build spec's
explicit instruction to start with cricket rather than build every sport at
once. Every fact (winner, runner-up, captain, captain birth date, final
date, venue) was independently web-verified against Wikipedia/ESPNcricinfo
during this project's research phase, not taken from memory.

Each `HistoricalPredictionEvent` has: `event_id`, `event_type`,
`event_name`, `event_date`, `prediction_cutoff_date`, `location` (+
lat/lon/tz), `candidates` (list of `CandidateRef`), `actual_winner`,
`source_metadata`. `actual_winner` is stored on the dataclass but is never
passed to the predictor -- see hindsight protection above.

A secondary, much larger real dataset (806 real ODI matches, 2015-2023,
`kundli_mass/cricket_match_dasha_dataset.csv`) was built from user-supplied
match-result data and used for an EXPLORATORY, non-hindsight-protected
pattern analysis -- see
`kundli_mass/CRICKET_DASHA_PATTERN_ANALYSIS.md`. It is not wired into this
formal backtest engine (see Known Limitations).

## Model / features

`prediction/features.py` computes, per candidate, per cutoff date: active
Mahadasha lord + dignity score, active Antardasha lord + dignity score,
cross-tradition (Jyotisha/Hellenistic) agreement classification, Moon-based
Gochara transit strength, and Tara Bala (Moon-nakshatra transit
compatibility). All reuse this project's existing, already-validated Swiss
Ephemeris / dasha / dignity engines (`world_astrology.reading_engine`,
`world_astrology.dignity_tables`, `kundli.compute_kundli`) -- no
astronomical primitive is reimplemented.

`prediction/scorer.py`'s `MODEL_CONFIG` weight dict is the exact dict given
in the build spec:

```python
MODEL_CONFIG = {
    "dasha": 0.20, "dasha_lord_strength": 0.15, "antardasha": 0.10,
    "transit": 0.20, "moon_activation": 0.10, "entity_chart": 0.10,
    "event_chart": 0.10, "key_personnel": 0.05,
}
```

**These are initial weights only.** They are not empirically optimized and
not derived from the exploratory pattern analysis (which found no strong
single-feature signal on the 806-match corpus -- see
`kundli_mass/CRICKET_DASHA_PATTERN_ANALYSIS.md`'s closing section for why
that analysis deliberately did NOT feed a number back into this dict).
Missing features are excluded and remaining weights renormalized (not
zeroed), so a candidate with less available data isn't silently penalized.

Model variants for ablation (`prediction.scorer.MODEL_VARIANTS`):
`vedic-core` (dasha/dasha_lord_strength/antardasha only) through `complete`
(all 8 weighted features).

## Metrics

`event_backtest/metrics.py` computes, per prediction: correctness, Brier
score (multiclass one-vs-all form), multiclass log loss (epsilon-clipped
against 0/1 probabilities), predicted rank of the actual winner, and
reciprocal rank. `aggregate()` rolls these up by event type and model
version, explicitly excluding any prediction with `status != "OK"` from
every average (and reporting the excluded count separately, never silently
dropping it).

## Calibration

`event_backtest/calibration.py` bins predictions by the model's own
top-pick confidence and reports the actual success rate in each bin. It
gates any "calibration is demonstrated" claim behind
`MIN_SAMPLE_FOR_CALIBRATION_CLAIM = 30` -- far above this dataset's 6
events. **This project does not claim the model is calibrated.**

## Real results (as of this document, dataset version `cricket-wc-finals-v1`)

Run via `python -m event_backtest.runner --ablation --report`. See
`reports/backtest_summary.json`/`.md` for the full machine-readable output;
headline numbers, `model_variant=complete`:

- Top-1 accuracy: **2/6 = 33.3%** (chance baseline for a 2-candidate
  ranking task is 50%)
- Mean Brier score: **0.641**
- Mean multiclass log loss: **0.838**
- Mean reciprocal rank: **0.667**

Ablation (all real, computed):

| Model variant | Top-1 accuracy | Mean Brier | Mean log loss |
|---|---|---|---|
| vedic-core | 50.0% | 0.734 | 0.945 |
| vedic-transit | 33.3% | 0.671 | 0.871 |
| vedic-entity | 33.3% | 0.641 | 0.838 |
| vedic-event | 33.3% | 0.641 | 0.838 |
| complete | 33.3% | 0.641 | 0.838 |

**Honest reading of these numbers:** on this 6-event dataset, the complete
model performed BELOW a 50% chance baseline for top-1 accuracy on a
2-candidate task, and the simplest variant (`vedic-core`) scored highest.
With only 6 events, none of these differences should be read as a
meaningful finding either way -- n=6 cannot distinguish real predictive
skill from noise. This is reported in full because the build spec requires
never fabricating or improving on real results, not because it is a
favorable outcome for the model.

## Scientific disclaimer

A successful backtest, if this project ever produces one on a larger
dataset, would demonstrate the predictive performance of this project's
SPECIFIC IMPLEMENTED ALGORITHM under its stated assumptions on that
specific historical sample. It would NOT constitute scientific proof that
astrology is predictive of real-world outcomes. This distinction matters
throughout this document and in `reports/backtest_summary.md` (which
repeats it at the top of every generated report): astronomical computation
(verifiably correct, checked against Swiss Ephemeris), astrological
interpretation (a set of documented classical rules and this project's own
weighting choices on top of them), and empirical performance (what this
backtest measures) are three separate things, and only the last one is what
this engine reports on.

## Known Limitations

- **Convention-level, not AST-level, hindsight enforcement at the
  orchestration boundary.** Unlike the older `backtest/blindness.py`
  system (which statically verifies via AST inspection that the predictor
  source code never references certain forbidden field names),
  `event_backtest/engine.py`'s "predict, then reveal" ordering is enforced
  by writing the code in that order, not by a structural check that would
  catch a future refactor breaking it. This is because this system's
  predictor legitimately needs to see candidate names, dates, and
  locations (to compute a chart) -- unlike BT-001's fully blind categorical
  predictor, whose `BlindInput` dataclass structurally cannot carry that
  information. A structural check equivalent to `blindness.py`'s would need
  to allow candidate identity through while still forbidding
  `actual_winner`; this was judged not worth the added complexity for an
  initial version, and is flagged here as a legitimate area for future
  hardening.
- **`calc_date_within_cutoff()` is deliberately conservative about future
  astronomical calculations.** Ephemeris positions for a future date ARE
  in principle deterministically computable in advance (unlike results or
  news), so one could argue computing a transit chart for a known future
  match date shouldn't count as hindsight. This project chose the more
  conservative interpretation -- reject any astronomical calculation
  targeting a post-cutoff date -- to avoid a harder-to-audit judgment call
  about which future-dated calculations are "safe." The practical effect:
  `event_chart_strength` (Section 9's match/final event chart) is always
  `None` for genuine pre-tournament predictions, since the final hasn't
  been played yet relative to the cutoff. This is documented, not a bug.
- **`key_personnel_strength` (captain chart strength) is not computed in
  this initial version.** Computing an Ascendant/house-dependent feature
  for a captain would require a real, sourced birthplace, which this
  project's standing rule (`mundane/entity_chart.py`) forbids fabricating,
  and birthplaces are not reliably available for the captains in this
  dataset. `key_personnel`'s 0.05 weight is therefore always renormalized
  away in practice for this dataset; the feature/weight exists in the
  architecture for a future dataset where birthplace data is available.
- **The 806-match secondary dataset is not wired into this formal
  backtest engine.** It was used only for exploratory pattern analysis
  (`kundli_mass/CRICKET_DASHA_PATTERN_ANALYSIS.md`), which found no strong
  single-feature signal. Running the formal, hindsight-protected engine
  against all 806 matches would require per-match venue/toss/lineup data
  this project doesn't have, and would multiply runtime substantially for
  low expected marginal value given the exploratory pass's null result.
- **n=6 is a very small backtest.** Every number in this document's
  "Real results" section is real and correctly computed, but a 6-event
  sample cannot support any strong claim about the model's true skill,
  positive or negative. Section 15 of the build spec explicitly frames
  cricket as a starting point, not a complete validation.
