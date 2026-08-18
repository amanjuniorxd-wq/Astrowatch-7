# Astrowatch-2

Astrowatch is a Vedic/mundane-astrology research codebase: real Swiss
Ephemeris-based astronomical calculation (sidereal/Lahiri positions,
Nakshatra/Rashi, Vimshottari Dasha, planetary dignity, transits, aspects,
houses), applied to individual, national/entity, and event charts, plus a
growing set of historical-event and prediction/backtesting tools built on
top of that calculation core. This file gives a short orientation; most
subsystems have their own dedicated docs (see the list of `*.md` files at
the repository root, and each package's module docstrings).

## Historical event backtest engine (`event_backtest/` + `prediction/`)

A formal, hindsight-protected historical backtesting engine: given a real
historical event (so far: ICC Men's Cricket World Cup finals, 2003-2023)
and a prediction cutoff date, it computes what Astrowatch's Vedic-astrology
-based model would have predicted using ONLY information available before
that cutoff, then scores that prediction against the real outcome.

Run it:

```
python -m event_backtest.runner --list-events
python -m event_backtest.runner --model complete --report
python -m event_backtest.runner --ablation --report
```

Full documentation -- hindsight-prevention design, dataset structure,
model/feature definitions, metrics, how to add new events, model versions,
real computed results, known limitations, and the scientific disclaimer --
is in **[BACKTEST.md](BACKTEST.md)**.

This is a separate system from the pre-existing `backtest/` package (the
ASTROWATCH-BT-001 experiment, a different blind categorical rule-firing
backtest) -- see BACKTEST.md's "Relationship to the existing `backtest/`
package" note and `event_backtest/__init__.py`'s docstring for why both
exist.

### Adding a new event

Add a `HistoricalPredictionEvent` to `event_backtest/dataset.py`'s
`_EVENTS` list: `event_id`, `event_type`, `event_name`, `event_date`,
`prediction_cutoff_date`, `location` (+ real lat/lon/tz), `candidates`
(list of `CandidateRef`, each needing a real, sourced `entity_name` this
project can chart -- see `prediction/entities.py`), and `actual_winner`.
Every fact must be real and independently verifiable -- do not add an event
with fabricated or unverified data; if reliable pre-cutoff data isn't
available, mark it `excluded=True` with an `exclusion_reason` instead of
including it.

### Model versions

`prediction/scorer.py`'s `MODEL_VERSION` (currently `vedic-weighted-v1`)
combined with the `--model` variant name (`vedic-core` through `complete`)
forms each prediction's full `model_version` string, e.g.
`vedic-weighted-v1:complete`. Changing `MODEL_CONFIG`'s weights or adding a
new feature should bump `MODEL_VERSION`.

### Limitations and scientific disclaimer

See BACKTEST.md's "Known Limitations" and "Scientific disclaimer"
sections. In short: this engine measures the performance of Astrowatch's
own implemented algorithm on a real but very small (n=6) historical sample.
It does not, and cannot, scientifically validate astrology -- only measure
this specific model's track record under its stated assumptions.

## Other documentation

See the repository root for subsystem-specific docs, including (non-
exhaustive): `HISTORICAL_DATABASE_ARCHITECTURE.md`,
`WORLD_ASTROLOGY_IMPLEMENTATION_REPORT.md`,
`RULE_IMPLEMENTATION_AUDIT.md`, `LOCAL_DEVELOPMENT.md`, and
`kundli_mass/CRICKET_DASHA_PATTERN_ANALYSIS.md` (the exploratory,
non-backtest pattern analysis over a larger real match corpus that fed the
research behind this backtest engine's feature set).
