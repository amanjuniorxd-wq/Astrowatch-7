"""
Astrowatch event_backtest -- strict cutoff / hindsight-protection system.
===================================================================
Every piece of information the predictor uses must carry PROVENANCE (source,
source_date, data_version, availability_date). This module enforces, at the
point of use, that provenance's source_date/availability_date never exceeds
the prediction's cutoff date -- raising HindsightError immediately if it does,
rather than silently proceeding with a leaked future fact.

This is a runtime/data-provenance check, distinct from (and a deliberate
complement to) backtest/blindness.py's AST-level static check on the OTHER
(categorical rule-firing) backtest system -- that system structurally cannot
reference forbidden fields at all; this system's predictor CAN receive
candidate names/dates/locations (it must, to compute a chart), so the
safeguard here is explicit provenance-dated data plus a real date comparison
against the cutoff, checked at construction time.
"""

from dataclasses import dataclass
from datetime import date
from typing import Optional


class HindsightError(Exception):
    """Raised when a DataProvenance record's source_date (or availability_date,
    if given) is strictly after the prediction_cutoff_date it is being used
    for. This is the load-bearing safeguard of the whole package -- every
    caller that constructs a DataProvenance and every caller of
    enforce_cutoff() relies on this being raised immediately, not logged and
    ignored."""


@dataclass(frozen=True)
class DataProvenance:
    """Describes where a single piece of information used by the predictor
    came from and when it became known. Required on every historical/factual
    input the predictor touches (candidate identity, entity inception date,
    captain birth date, etc.) -- NOT required on the deterministic
    astronomical calculations themselves (planetary positions are a pure
    function of a date/time/place, not a 'sourced fact' with a publication
    date; their only relevant date is the calculation TARGET date, which
    enforce_cutoff() also checks separately, see calc_date_within_cutoff())."""
    source: str                       # e.g. "Wikipedia: 2023 Cricket World Cup final", "ESPNcricinfo player profile"
    source_date: str                  # ISO8601 date this fact was published/recorded, e.g. "2023-01-15"
    data_type: str                    # e.g. "entity_inception_date", "captain_birth_date", "candidate_list"
    availability_date: Optional[str] = None  # if the fact became publicly known later than source_date; defaults to source_date
    confidence: str = "high"          # "high" | "moderate" | "low" -- never a fabricated numeric confidence

    def effective_availability_date(self) -> str:
        return self.availability_date or self.source_date


def _parse_date(d: str) -> date:
    y, m, day = (int(x) for x in d.split("-"))
    return date(y, m, day)


def enforce_cutoff(provenance: DataProvenance, cutoff_date: str) -> None:
    """Raises HindsightError if provenance's effective availability date is
    strictly after cutoff_date. Called by every code path in prediction/
    that consumes a DataProvenance-tagged fact."""
    avail = _parse_date(provenance.effective_availability_date())
    cutoff = _parse_date(cutoff_date)
    if avail > cutoff:
        raise HindsightError(
            f"HindsightError: data item of type {provenance.data_type!r} from "
            f"source {provenance.source!r} has availability_date "
            f"{provenance.effective_availability_date()!r}, which is AFTER the "
            f"prediction cutoff date {cutoff_date!r}. This data item would not "
            f"have been available at prediction time and has been rejected."
        )


def calc_date_within_cutoff(calc_target_date: str, cutoff_date: str) -> None:
    """A distinct, complementary check: the astronomical/calendrical
    calculation TARGET date itself (e.g. 'what were the planetary positions
    on this date') must never be later than the cutoff either -- a backtest
    predicting a 2023 event as of a 2023-01-01 cutoff must not be handed
    'transiting positions as of 2023-11-19' (the day of the actual final) as
    if that were legitimately known in advance. Deterministic astronomical
    calculation is not itself a 'sourced fact' (no publication date), so this
    is checked separately from enforce_cutoff()/DataProvenance."""
    calc_dt = _parse_date(calc_target_date)
    cutoff_dt = _parse_date(cutoff_date)
    if calc_dt > cutoff_dt:
        raise HindsightError(
            f"HindsightError: an astronomical/calendrical calculation was requested "
            f"for target date {calc_target_date!r}, which is AFTER the prediction "
            f"cutoff date {cutoff_date!r}. Refusing to compute a chart for a moment "
            f"that would not have existed yet relative to the prediction."
        )


def validate_event_schema_dates(event_date: str, prediction_cutoff_date: str) -> None:
    """Sanity check applied once per event at load time (see dataset.py):
    the cutoff must genuinely precede the event itself, and both must be
    valid ISO8601 dates. Does not by itself guarantee no hindsight leak --
    that is enforced per-datum via enforce_cutoff()/calc_date_within_cutoff()
    -- this only rejects an obviously malformed event record."""
    ed = _parse_date(event_date)
    cd = _parse_date(prediction_cutoff_date)
    if cd >= ed:
        raise ValueError(
            f"Invalid event schema: prediction_cutoff_date {prediction_cutoff_date!r} "
            f"must be strictly before event_date {event_date!r} (a cutoff on or after "
            f"the event date would trivially leak the outcome)."
        )
