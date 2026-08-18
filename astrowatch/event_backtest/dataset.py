"""
event_backtest/dataset.py
==========================
PRIMARY dataset: the 6 ICC Men's Cricket World Cup finals, 2003-2023
(2023, 2019, 2015, 2011, 2007, 2003), per the build spec's explicit
instruction to "start with cricket... investigate 2003/2007/2011/2015/2019/
2023" and "don't build every sport/election at once."

Every fact below (winner, runner-up, captain, captain birth date, final
date, venue) was independently web-verified against Wikipedia/ESPNcricinfo
during this project's research phase (see this module's SOURCES comments
per event) rather than taken from memory alone, per the build spec's
"VERY IMPORTANT: DO NOT FAKE THE RESULTS" requirement.

SCOPE NOTE -- finalists only, 2 candidates per event: semifinalist lists for
the earlier tournaments (2003, 2007) were not reliably re-confirmable to
this project's verification standard during research, so this dataset
deliberately narrows to a 2-candidate (finalist-only) ranking task rather
than risk an unverified semifinalist inclusion. This is a documented scope
choice, not a limitation discovered after the fact.

SECONDARY / EXPLORATORY dataset: a much larger, real 806-match ODI corpus
(2015-2023, from user-supplied match-result data) was separately used for
an observational (non-hindsight-protected, non-backtest) pattern analysis --
see kundli_mass/cricket_match_dasha_dataset.csv and
kundli_mass/CRICKET_DASHA_PATTERN_ANALYSIS.md. That corpus is NOT wired into
this formal backtest engine yet (future work item, see BACKTEST.md's "Known
Limitations" -- it would require per-match venue/toss/lineup data this
project does not have, and would multiply runtime ~800x for comparatively
low marginal value versus the headline World Cup-final backtest).

CUTOFF DATE CONVENTION: each event's prediction_cutoff_date is set to
January 1 of the tournament's year, mirroring the exact convention used in
the build spec's own worked example ("2023 Cricket World Cup, prediction
cutoff 2023-01-01").
"""
from typing import Dict, List, Optional

from event_backtest.models import CandidateRef, HistoricalPredictionEvent

DATASET_VERSION = "cricket-wc-finals-v1"

_EVENTS: List[HistoricalPredictionEvent] = [
    HistoricalPredictionEvent(
        event_id="cricket_wc_2003", event_type="cricket_odi_world_cup",
        event_name="2003 ICC Cricket World Cup", event_date="2003-03-23",
        prediction_cutoff_date="2003-01-01", location="Wanderers Stadium, Johannesburg",
        location_latitude=-26.20, location_longitude=28.05, location_timezone="Africa/Johannesburg",
        candidates=[
            CandidateRef(candidate_id="australia", entity_name="Australia", display_name="Australia",
                         captain_name="Ricky Ponting", captain_birth_date="1974-12-19",
                         captain_birth_date_source="Wikipedia: Ricky Ponting"),
            CandidateRef(candidate_id="india", entity_name="India", display_name="India",
                         captain_name="Sourav Ganguly", captain_birth_date="1972-07-08",
                         captain_birth_date_source="Wikipedia: Sourav Ganguly"),
        ],
        actual_winner="australia",
        source_metadata={"source": "Wikipedia: 2003 Cricket World Cup Final", "verified_during": "research phase"},
    ),
    HistoricalPredictionEvent(
        event_id="cricket_wc_2007", event_type="cricket_odi_world_cup",
        event_name="2007 ICC Cricket World Cup", event_date="2007-04-28",
        prediction_cutoff_date="2007-01-01", location="Kensington Oval, Bridgetown, Barbados",
        location_latitude=13.10, location_longitude=-59.62, location_timezone="America/Barbados",
        candidates=[
            CandidateRef(candidate_id="australia", entity_name="Australia", display_name="Australia",
                         captain_name="Ricky Ponting", captain_birth_date="1974-12-19",
                         captain_birth_date_source="Wikipedia: Ricky Ponting"),
            CandidateRef(candidate_id="sri_lanka", entity_name="Sri Lanka", display_name="Sri Lanka",
                         captain_name="Mahela Jayawardene", captain_birth_date="1977-05-27",
                         captain_birth_date_source="Wikipedia: Mahela Jayawardene"),
        ],
        actual_winner="australia",
        source_metadata={"source": "Wikipedia: 2007 Cricket World Cup Final", "verified_during": "research phase"},
    ),
    HistoricalPredictionEvent(
        event_id="cricket_wc_2011", event_type="cricket_odi_world_cup",
        event_name="2011 ICC Cricket World Cup", event_date="2011-04-02",
        prediction_cutoff_date="2011-01-01", location="Wankhede Stadium, Mumbai",
        location_latitude=19.08, location_longitude=72.88, location_timezone="Asia/Kolkata",
        candidates=[
            CandidateRef(candidate_id="india", entity_name="India", display_name="India",
                         captain_name="MS Dhoni", captain_birth_date="1981-07-07",
                         captain_birth_date_source="Wikipedia: MS Dhoni"),
            CandidateRef(candidate_id="sri_lanka", entity_name="Sri Lanka", display_name="Sri Lanka",
                         captain_name="Kumar Sangakkara", captain_birth_date="1977-10-27",
                         captain_birth_date_source="Wikipedia: Kumar Sangakkara"),
        ],
        actual_winner="india",
        source_metadata={"source": "Wikipedia: 2011 Cricket World Cup Final", "verified_during": "research phase"},
    ),
    HistoricalPredictionEvent(
        event_id="cricket_wc_2015", event_type="cricket_odi_world_cup",
        event_name="2015 ICC Cricket World Cup", event_date="2015-03-29",
        prediction_cutoff_date="2015-01-01", location="Melbourne Cricket Ground, Melbourne",
        location_latitude=-37.81, location_longitude=144.96, location_timezone="Australia/Melbourne",
        candidates=[
            CandidateRef(candidate_id="australia", entity_name="Australia", display_name="Australia",
                         captain_name="Michael Clarke", captain_birth_date="1981-04-02",
                         captain_birth_date_source="Wikipedia: Michael Clarke (cricketer)"),
            CandidateRef(candidate_id="new_zealand", entity_name="New Zealand", display_name="New Zealand",
                         captain_name="Brendon McCullum", captain_birth_date="1981-09-27",
                         captain_birth_date_source="Wikipedia: Brendon McCullum"),
        ],
        actual_winner="australia",
        source_metadata={"source": "Wikipedia: 2015 Cricket World Cup Final", "verified_during": "research phase"},
    ),
    HistoricalPredictionEvent(
        event_id="cricket_wc_2019", event_type="cricket_odi_world_cup",
        event_name="2019 ICC Cricket World Cup", event_date="2019-07-14",
        prediction_cutoff_date="2019-01-01", location="Lord's, London",
        location_latitude=51.53, location_longitude=-0.17, location_timezone="Europe/London",
        candidates=[
            CandidateRef(candidate_id="england", entity_name="England", display_name="England",
                         captain_name="Eoin Morgan", captain_birth_date="1986-09-10",
                         captain_birth_date_source="Wikipedia: Eoin Morgan"),
            CandidateRef(candidate_id="new_zealand", entity_name="New Zealand", display_name="New Zealand",
                         captain_name="Kane Williamson", captain_birth_date="1990-08-08",
                         captain_birth_date_source="Wikipedia: Kane Williamson"),
        ],
        actual_winner="england",
        source_metadata={"source": "Wikipedia: 2019 Cricket World Cup Final", "verified_during": "research phase"},
    ),
    HistoricalPredictionEvent(
        event_id="cricket_wc_2023", event_type="cricket_odi_world_cup",
        event_name="2023 ICC Cricket World Cup", event_date="2023-11-19",
        prediction_cutoff_date="2023-01-01", location="Narendra Modi Stadium, Ahmedabad",
        location_latitude=23.03, location_longitude=72.58, location_timezone="Asia/Kolkata",
        candidates=[
            CandidateRef(candidate_id="australia", entity_name="Australia", display_name="Australia",
                         captain_name="Pat Cummins", captain_birth_date="1993-05-08",
                         captain_birth_date_source="Wikipedia: Pat Cummins"),
            CandidateRef(candidate_id="india", entity_name="India", display_name="India",
                         captain_name="Rohit Sharma", captain_birth_date="1987-04-30",
                         captain_birth_date_source="Wikipedia: Rohit Sharma"),
        ],
        actual_winner="australia",
        source_metadata={"source": "Wikipedia: 2023 Cricket World Cup Final", "verified_during": "research phase"},
    ),
]

_EVENTS_BY_ID: Dict[str, HistoricalPredictionEvent] = {e.event_id: e for e in _EVENTS}


def list_events(include_excluded: bool = False) -> List[HistoricalPredictionEvent]:
    if include_excluded:
        return list(_EVENTS)
    return [e for e in _EVENTS if not e.excluded]


def get_event(event_id: str) -> Optional[HistoricalPredictionEvent]:
    return _EVENTS_BY_ID.get(event_id)
