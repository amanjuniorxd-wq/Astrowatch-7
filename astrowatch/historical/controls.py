"""
Astrowatch — reproducible control-date sampling.

Controls exist so a future backtest can compare "rule fired near a real event" rates
against "rule fired near an arbitrary date" rates. The whole point is falsifiability,
so the sampling method must be fixed and reproducible BEFORE looking at any
astrological result -- never cherry-picked afterward (spec item 15/16).
"""

import random
from dataclasses import dataclass
from datetime import date, timedelta
from typing import List

from .models import ControlDate


def sample_random_dates(
    start_date: str, end_date: str, count: int, seed: int
) -> List[str]:
    """Deterministic: same start_date/end_date/count/seed always produces the same
    dates. This is the entire reproducibility contract -- store the seed, and
    anyone can regenerate the identical sample."""
    y1, m1, d1 = (int(x) for x in start_date.split("-"))
    y2, m2, d2 = (int(x) for x in end_date.split("-"))
    span_start, span_end = date(y1, m1, d1), date(y2, m2, d2)
    total_days = (span_end - span_start).days
    if total_days <= 0:
        raise ValueError("end_date must be after start_date")
    rng = random.Random(seed)
    offsets = rng.sample(range(total_days + 1), min(count, total_days + 1))
    return sorted((span_start + timedelta(days=o)).isoformat() for o in offsets)


def build_random_controls(
    start_date: str, end_date: str, count: int, seed: int,
    region: str, dataset_version: str, selection_timestamp: str,
    id_prefix: str = "CTRL",
) -> List[ControlDate]:
    dates = sample_random_dates(start_date, end_date, count, seed)
    return [
        ControlDate(
            control_id=f"{id_prefix}-{i+1:04d}",
            date=d,
            region=region,
            sampling_method="RANDOM_DATE",
            seed=seed,
            selection_timestamp=selection_timestamp,
            source_window=f"{start_date}..{end_date}",
            dataset_version=dataset_version,
            notes=f"Reproducible via random.Random({seed}).sample(range(total_days+1), {count}) "
                  f"over the window {start_date}..{end_date}.",
        )
        for i, d in enumerate(dates)
    ]
