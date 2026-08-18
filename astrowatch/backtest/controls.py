"""
Astrowatch backtest — control-case generation, reusing EXISTING infrastructure.

Spec item 12: "Use the existing control-date infrastructure... Controls must be
selected independently of astrology... determined before seeing test results."

historical_events_v2.db already contains 150 control_dates rows for
dataset_version='ASTROWATCH-HIST-002' (sampling_method='RANDOM_DATE', seed=20260814,
window='1900-01-01..2026-08-14', generated via historical.controls.build_random_controls()
during the HIST-002 build -- BEFORE this backtest engine existed, and therefore
unambiguously independent of any astrological result). This module reads that
pre-existing, frozen table (read-only) and turns it into backtest TestCase rows. It
does not call historical.controls.sample_random_dates() itself for the primary
control set -- there is no need to generate anything new, and generating something
new would mean a second, backtest-time-chosen seed, which is a weaker independence
story than reusing dates that were literally selected before this experiment was
conceived.
"""

from datetime import datetime, timezone as dt_timezone
from typing import List

import historical.repository as hrepo

from .models import TestCase


def sample_existing_control_dates(conn, dataset_version: str, experiment_id: str) -> List[TestCase]:
    rows = hrepo.get_control_dates(conn, dataset_version=dataset_version)
    generated_at = datetime.now(dt_timezone.utc).isoformat(timespec="seconds")
    out = []
    for r in rows:
        out.append(TestCase(
            test_case_id=f"TC-{r['control_id']}",
            experiment_id=experiment_id,
            case_kind="CONTROL",
            source_event_id=None,
            source_control_id=r["control_id"],
            test_date=r["date"],
            time_precision_mode="MODE_B_DATE_ONLY",  # control dates carry no time -- never fabricated
            input_time=None,
            input_timezone=None,
            input_location_precision="UNKNOWN",  # control_dates.region is 'GLOBAL', not a real location
            sample_hours_utc=[],
            generated_at=generated_at,
        ))
    return out
