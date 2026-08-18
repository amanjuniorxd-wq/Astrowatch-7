"""
Astrowatch — blind historical backtesting engine.
====================================================
Tests the EXISTING, UNMODIFIED rule registry (rule_registry.py) and EXISTING,
UNMODIFIED astronomical pipeline (ayanamsha.py / panchang.py / rashi_nakshatra.py /
forecast.py) against the EXISTING, UNMODIFIED, FROZEN historical dataset
(ASTROWATCH-HIST-002 in historical_events_v2.db).

This package does not add astrological rules, does not change thresholds/weights, does
not change Lahiri/Panchang/Rāśi-Nakshatra methodology, and never writes to
historical_events.db / historical_events_v2.db. It only READS from the historical
database (via historical.repository's existing read-only functions) and WRITES to its
own, separate backtest_results.db.

Architecture (see BACKTEST_REPORT_ASTROWATCH_BT001.md for the full write-up):

    FROZEN historical_events_v2.db (ASTROWATCH-HIST-002)
            |  (read-only; checksum verified before AND after)
            v
    sampler.py       -- deterministic test-case selection, seeded
            |
            v
    predictor.py      -- BLIND: receives only date/time-if-known/location-if-known,
            |             never event name/type/description/source/verification/outcome
            v          -- internally calls, UNMODIFIED: ephemeris_source.py (real
    (existing)            local pyswisseph tropical longitudes) -> forecast.run_forecast()
    forecast.py           -> ayanamsha.py -> panchang.py -> rashi_nakshatra.py ->
    rule_registry.py      rule_registry.RULES
            |
            v
    scorer.py + baselines.py + controls.py   -- ONLY AFTER prediction is recorded,
            |                                    actual_events revealed and compared
            v
    backtest_results.db (separate, own schema, frozen once complete)

No module in this package imports historical.models.Event fields for anything other
than test-case *generation* (sampler.py, controls.py) and post-prediction *reveal*
(engine.py, after predictor.py has already returned). predictor.py itself takes a
BlindInput dataclass (see models.py) that structurally cannot carry event-identifying
fields -- see blindness.py for the automated check of this claim.
"""

import os as _os
import sys as _sys

_ASTROWATCH_DIR = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _ASTROWATCH_DIR not in _sys.path:
    _sys.path.insert(0, _ASTROWATCH_DIR)
# The astrowatch/ directory must be on sys.path for this package's modules to reach
# the existing, UNMODIFIED top-level modules (forecast.py, rule_registry.py,
# ayanamsha.py, coordinates.py, panchang.py, rashi_nakshatra.py, aspects.py) via the
# same flat (non-package-qualified) imports those modules already use internally
# (e.g. forecast.py does `from ayanamsha import ...`, not a relative/package import).
# This mirrors exactly how historical/ was already usable from astrowatch/ as cwd.
