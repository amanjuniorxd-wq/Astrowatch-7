"""
event_backtest/calibration.py
================================
Confidence-bin vs actual-success-rate calibration table.

DO NOT claim the model is calibrated until historical data demonstrates it
(build spec Section 12). This module only ever COMPUTES the table from real
evaluated predictions -- it never asserts a conclusion about calibration
quality. Any prose claim about calibration belongs in report.py/BACKTEST.md
and must explicitly cite the sample size behind it (a 6-event dataset is far
too small to responsibly claim anything about calibration -- report.py must
say so).
"""
from dataclasses import dataclass
from typing import List, Optional

from event_backtest.metrics import EvaluatedPrediction

# Standard 5-bin calibration table (0-20%, 20-40%, ..., 80-100%).
DEFAULT_BIN_EDGES = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]


@dataclass
class CalibrationBin:
    low: float
    high: float
    n: int
    mean_predicted_confidence: Optional[float]
    actual_success_rate: Optional[float]


def compute_calibration_table(evaluated: List[EvaluatedPrediction],
                               bin_edges: List[float] = None) -> List[CalibrationBin]:
    """Bins by the predictor's OWN top-pick confidence (top_probability),
    and reports the ACTUAL fraction of those top picks that were correct.
    Perfect calibration = mean_predicted_confidence ~= actual_success_rate
    within each bin."""
    edges = bin_edges or DEFAULT_BIN_EDGES
    ok = [e for e in evaluated if e.status == "OK" and e.top_probability is not None]

    bins = []
    for i in range(len(edges) - 1):
        low, high = edges[i], edges[i + 1]
        in_bin = [e for e in ok if low <= e.top_probability < high or (high == 1.0 and e.top_probability == 1.0)]
        n = len(in_bin)
        mean_conf = sum(e.top_probability for e in in_bin) / n if n else None
        success_rate = sum(1.0 for e in in_bin if e.correct) / n if n else None
        bins.append(CalibrationBin(low=low, high=high, n=n,
                                    mean_predicted_confidence=mean_conf, actual_success_rate=success_rate))
    return bins


MIN_SAMPLE_FOR_CALIBRATION_CLAIM = 30  # far above this dataset's 6 events -- see module docstring


def calibration_is_claimable(evaluated: List[EvaluatedPrediction]) -> bool:
    """Returns False (almost always, for this dataset) -- gate used by
    report.py to decide whether ANY calibration-quality prose is allowed in
    the generated report at all."""
    n_ok = len([e for e in evaluated if e.status == "OK"])
    return n_ok >= MIN_SAMPLE_FOR_CALIBRATION_CLAIM
