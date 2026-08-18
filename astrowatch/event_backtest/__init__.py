"""
Astrowatch -- event_backtest package.
===================================================================
A formal historical backtesting engine that answers: "If Astrowatch had been
run at a given historical point in time, using ONLY information available at
that time, what prediction would it have produced, and how accurate was it?"

NAMING NOTE (read before extending this package): this project already has a
top-level `backtest/` package (backtest/engine.py, backtest/models.py,
backtest/metrics.py, backtest/scorer.py, backtest/predictor.py, etc.) that
implements a STRUCTURALLY DIFFERENT system -- a blind categorical rule-firing
test (did mundane-astrology rule category X fire on date Y?) against
historical_events_v2.db, with AST-enforced hindsight protection
(backtest/blindness.py) via a BlindInput type that has no field capable of
carrying an outcome. That system (ASTROWATCH-BT-001) is untouched by this
work and remains fully functional.

This package (event_backtest/) implements a DIFFERENT prediction shape:
multi-candidate ranking/outcome prediction for discrete events (e.g. "who
wins the 2023 Cricket World Cup: India, Australia, ...") with calibrated
scores/probabilities, Brier score, log loss, calibration analysis, and
ablation testing across model variants -- a genuinely new capability, not a
duplicate of the existing backtest/ package. It was given a new top-level
name specifically to avoid colliding with (and never silently overwriting)
that pre-existing, working system. See BACKTEST.md for the full comparison
and rationale.

This package still reuses the same hindsight-protection PRINCIPLE as
backtest/blindness.py (structural inability to see the future), implemented
here via cutoff.py's HindsightError + explicit source-date provenance
checking, since a ranking predictor's evidence (per-candidate feature
values from prediction/features.py) doesn't fit the BlindInput dataclass
shape that backtest/models.py uses.
"""
