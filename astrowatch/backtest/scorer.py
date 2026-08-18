"""
Astrowatch backtest — objective scoring.

Pure functions over already-recorded (predicted, actual) pairs. Nothing here reads
historical_events_v2.db or backtest_results.db directly -- engine.py/repository.py do
the I/O and pass plain data structures in. This keeps the scoring math testable in
isolation (see tests/backtest/test_scoring.py) and impossible to accidentally couple
to database state.

SMALL-SAMPLE THRESHOLD (fixed before any result was seen, per spec item 31): a
category/subtype slice is flagged INSUFFICIENT_SAMPLE if it has fewer than 10 total
cases. This is a round, pre-registered number, not tuned to make any particular
category look adequate or inadequate.
"""

import math
import random
from dataclasses import dataclass
from typing import List, Optional, Tuple

MIN_SAMPLE_SIZE = 10


@dataclass
class ConfusionCounts:
    tp: int
    fp: int
    tn: int
    fn: int

    @property
    def n(self) -> int:
        return self.tp + self.fp + self.tn + self.fn


def confusion_counts(pairs: List[Tuple[bool, bool]]) -> ConfusionCounts:
    tp = sum(1 for p, a in pairs if p and a)
    fp = sum(1 for p, a in pairs if p and not a)
    tn = sum(1 for p, a in pairs if not p and not a)
    fn = sum(1 for p, a in pairs if not p and a)
    return ConfusionCounts(tp=tp, fp=fp, tn=tn, fn=fn)


def _safe_div(numerator: float, denominator: float) -> Optional[float]:
    if denominator == 0:
        return None
    return numerator / denominator


def compute_metrics(c: ConfusionCounts) -> dict:
    precision = _safe_div(c.tp, c.tp + c.fp)
    recall = _safe_div(c.tp, c.tp + c.fn)
    f1 = None
    if precision is not None and recall is not None and (precision + recall) > 0:
        f1 = 2 * precision * recall / (precision + recall)
    accuracy = _safe_div(c.tp + c.tn, c.n)
    specificity = _safe_div(c.tn, c.tn + c.fp)
    fpr = _safe_div(c.fp, c.fp + c.tn)

    ci_low = ci_high = None
    if c.n > 0 and accuracy is not None:
        ci_low, ci_high = wilson_ci(c.tp + c.tn, c.n)

    flag = "OK" if c.n >= MIN_SAMPLE_SIZE else "INSUFFICIENT_SAMPLE"

    return {
        "sample_size": c.n, "tp": c.tp, "fp": c.fp, "tn": c.tn, "fn": c.fn,
        "precision": precision, "recall": recall, "f1": f1, "accuracy": accuracy,
        "specificity": specificity, "false_positive_rate": fpr,
        "wilson_ci_low_accuracy": ci_low, "wilson_ci_high_accuracy": ci_high,
        "sample_flag": flag,
    }


def wilson_ci(successes: int, n: int, z: float = 1.96) -> Tuple[float, float]:
    """Wilson score interval -- appropriate for small/binomial samples, unlike a
    naive normal-approximation interval which can misbehave near 0 or 1 (exactly
    the regime this 140-event dataset lives in). See spec item 29."""
    if n == 0:
        return (0.0, 0.0)
    p_hat = successes / n
    denom = 1 + z ** 2 / n
    center = p_hat + z ** 2 / (2 * n)
    margin = z * math.sqrt((p_hat * (1 - p_hat) + z ** 2 / (4 * n)) / n)
    low = (center - margin) / denom
    high = (center + margin) / denom
    return (max(0.0, low), min(1.0, high))


def permutation_test_fire_rate_difference(
    event_fired: List[bool], control_fired: List[bool], seed: int, iterations: int = 10000,
) -> dict:
    """Two-sided permutation test on the difference in fire-rate between the
    event-date group and the control-date group. Pools both groups' fired/not-fired
    labels, repeatedly reassigns them at random into two groups of the original
    sizes (seeded, reproducible), and asks how often a difference at least as
    extreme as the OBSERVED one would arise by chance alone if group membership
    carried no real information. This is appropriate here specifically because the
    outcome variable is a simple binary rate and the two group sizes are small and
    unequal -- a t-test's normality assumption is not well justified at n=31-150
    with rates that may be close to 0 or 1."""
    n_event = len(event_fired)
    n_control = len(control_fired)
    if n_event == 0 or n_control == 0:
        return {"observed_difference": None, "p_value": None, "iterations": 0}

    observed = (sum(event_fired) / n_event) - (sum(control_fired) / n_control)
    pooled = list(event_fired) + list(control_fired)
    rng = random.Random(seed)
    extreme_count = 0
    for _ in range(iterations):
        rng.shuffle(pooled)
        perm_event = pooled[:n_event]
        perm_control = pooled[n_event:]
        diff = (sum(perm_event) / n_event) - (sum(perm_control) / n_control)
        if abs(diff) >= abs(observed):
            extreme_count += 1
    p_value = extreme_count / iterations
    return {"observed_difference": observed, "p_value": p_value, "iterations": iterations}
