"""
Astrowatch backtest — baseline comparisons.

Spec item 18: "A prediction is meaningless without comparison." Three baselines,
each scored with the IDENTICAL scorer.compute_metrics() function used for the real
predictor, so the numbers are directly comparable.

Baseline 1 -- RANDOM: an unbiased (p=0.5 "fired" coin, seeded) prediction, with a
  seeded uniform-random nonempty subset of the 6 categories chosen when it "fires."
  Fixed probability chosen BEFORE seeing any result; not tuned to Astrowatch's own
  observed fire rate (which would make the comparison meaningless).

Baseline 2 -- HISTORICAL_FREQUENCY: predicts category C as positive for a test case
  with probability equal to category C's prevalence AMONG THE 140-EVENT TEST SET
  ITSELF (seeded per-test-case draw). LIMITATION, disclosed here and in the report:
  this is an in-sample frequency (there is currently no separate held-out corpus to
  derive frequencies from -- see spec item 20, "prefer a purely evaluation-oriented
  experiment" for this first backtest). This makes Baseline 2 a slightly optimistic
  comparator, not a conservative one -- Astrowatch beating it is a lower bar than
  beating a true out-of-sample frequency baseline would be.

Baseline 3 -- CONTROL_DATE: for each EVENT test case, find the temporally-nearest
  already-predicted CONTROL test case (from the pre-existing, reused control_dates
  pool) and use THAT control's real Astrowatch prediction as the "guess" for the
  event's actual outcome. This asks: does knowing the sky on the real event date
  carry information beyond knowing the sky on a nearby, non-selected date? No new
  predictions are generated for this baseline -- it reuses predictions already
  computed for the two real test-case groups.
"""

import random
from datetime import date as _date
from typing import Dict, List, Tuple

from .category_map import ALL_EVENT_CATEGORIES


def _days_since_epoch(date_str: str) -> int:
    y, m, d = (int(x) for x in date_str.split("-"))
    return _date(y, m, d).toordinal()


def random_baseline_pairs(
    event_actuals: Dict[str, dict],   # test_case_id -> {'fired': bool, 'categories': set}
    control_actuals: Dict[str, dict],
    seed: int,
) -> Dict[str, List[Tuple[bool, bool]]]:
    rng = random.Random(seed)
    all_cases = list(event_actuals.items()) + list(control_actuals.items())
    all_cases.sort(key=lambda kv: kv[0])  # deterministic iteration order before drawing
    out = {"ANY": []}
    for cat in ALL_EVENT_CATEGORIES:
        out[cat] = []
    for tc_id, actual in all_cases:
        fired = rng.random() < 0.5
        cats = set()
        if fired:
            k = rng.randint(1, len(ALL_EVENT_CATEGORIES))
            cats = set(rng.sample(ALL_EVENT_CATEGORIES, k))
        out["ANY"].append((fired, actual["fired"]))
        for cat in ALL_EVENT_CATEGORIES:
            out[cat].append((cat in cats, cat in actual["categories"]))
    return out


def historical_frequency_baseline_pairs(
    event_actuals: Dict[str, dict],
    control_actuals: Dict[str, dict],
    seed: int,
) -> Dict[str, List[Tuple[bool, bool]]]:
    total_events = len(event_actuals) or 1
    category_prevalence = {cat: 0 for cat in ALL_EVENT_CATEGORIES}
    for actual in event_actuals.values():
        for cat in actual["categories"]:
            category_prevalence[cat] += 1
    category_prob = {cat: n / total_events for cat, n in category_prevalence.items()}
    fired_prevalence = sum(1 for a in event_actuals.values() if a["fired"]) / total_events

    rng = random.Random(seed)
    all_cases = list(event_actuals.items()) + list(control_actuals.items())
    all_cases.sort(key=lambda kv: kv[0])
    out = {"ANY": []}
    for cat in ALL_EVENT_CATEGORIES:
        out[cat] = []
    for tc_id, actual in all_cases:
        fired = rng.random() < fired_prevalence
        out["ANY"].append((fired, actual["fired"]))
        for cat in ALL_EVENT_CATEGORIES:
            predicted = rng.random() < category_prob[cat]
            out[cat].append((predicted, cat in actual["categories"]))
    return out


def control_date_baseline_pairs(
    event_dates: Dict[str, str],          # event test_case_id -> date
    event_actuals: Dict[str, dict],       # event test_case_id -> actual
    control_dates: Dict[str, str],        # control test_case_id -> date
    control_predictions: Dict[str, dict], # control test_case_id -> {'fired':bool,'categories':set}
) -> Dict[str, List[Tuple[bool, bool]]]:
    out = {"ANY": []}
    for cat in ALL_EVENT_CATEGORIES:
        out[cat] = []
    if not control_dates:
        return out
    control_days = {tc_id: _days_since_epoch(d) for tc_id, d in control_dates.items()}
    for event_tc_id, event_date in event_dates.items():
        try:
            event_day = _days_since_epoch(event_date)
        except ValueError:
            continue  # pre-year-1 dates unrepresentable by datetime.date -- excluded, documented
        best_tc, best_dist = None, None
        for control_tc_id, control_day in control_days.items():
            dist = abs(control_day - event_day)
            if best_dist is None or dist < best_dist or (dist == best_dist and control_tc_id < best_tc):
                best_tc, best_dist = control_tc_id, dist
        if best_tc is None:
            continue
        stand_in = control_predictions[best_tc]
        actual = event_actuals[event_tc_id]
        out["ANY"].append((stand_in["fired"], actual["fired"]))
        for cat in ALL_EVENT_CATEGORIES:
            out[cat].append((cat in stand_in["categories"], cat in actual["categories"]))
    return out
