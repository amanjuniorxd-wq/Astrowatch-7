"""
Astrowatch — controlled taxonomy for the historical event database.

Single source of truth for event categories/subtypes and every confidence/quality
enum used across historical/*.py, scripts/*.py, and the seed CSVs. Nothing here
references astrology in any way -- see historical/__init__.py for why that matters.
"""

from typing import Dict, List

# ---------------------------------------------------------------------------
# Top-level event categories and their controlled subtypes
# ---------------------------------------------------------------------------

EVENT_TAXONOMY: Dict[str, List[str]] = {
    "MILITARY": [
        "war_start", "war_end", "battle", "invasion", "ceasefire",
        "peace_treaty", "military_coup", "major_military_crisis",
    ],
    "POLITICAL": [
        "election", "government_change", "leadership_change", "coup",
        "revolution", "independence", "constitutional_change",
        "major_political_crisis", "assassination",
    ],
    "ECONOMIC": [
        "financial_crisis", "market_crash", "sovereign_default",
        "major_currency_event", "banking_crisis", "major_economic_policy",
    ],
    "NATURAL_DISASTER": [
        "earthquake", "volcanic_eruption", "tsunami", "cyclone_hurricane",
        "flood", "wildfire", "major_drought", "major_storm",
    ],
    "SOCIAL_PUBLIC_HEALTH": [
        "pandemic", "epidemic", "major_protest", "civil_unrest",
        "major_social_movement",
    ],
    "SCIENCE_TECHNOLOGY": [
        "major_scientific_discovery", "major_space_event",
        "major_technology_event", "nuclear_event",
    ],
}

EVENT_TYPES = tuple(EVENT_TAXONOMY.keys())

ALL_SUBTYPES = tuple(
    subtype for subtypes in EVENT_TAXONOMY.values() for subtype in subtypes
)


def is_valid_type_subtype(event_type: str, event_subtype: str) -> bool:
    return event_type in EVENT_TAXONOMY and event_subtype in EVENT_TAXONOMY[event_type]


# ---------------------------------------------------------------------------
# Uncertainty enums (Section 7 / 34 of the spec: never fake precision)
# ---------------------------------------------------------------------------

DATE_CONFIDENCE = ("EXACT", "APPROXIMATE", "DATE_RANGE", "DISPUTED", "UNKNOWN")
TIME_CONFIDENCE = ("EXACT", "APPROXIMATE", "UNKNOWN")
LOCATION_CONFIDENCE = ("EXACT", "CITY", "REGION", "COUNTRY", "APPROXIMATE", "UNKNOWN")
LOCATION_PRECISION = LOCATION_CONFIDENCE  # same vocabulary, used on the coordinate fields

# ---------------------------------------------------------------------------
# Source quality tiers (Section 10)
# ---------------------------------------------------------------------------

SOURCE_TIERS: Dict[int, str] = {
    1: "Primary / official source (government record, court filing, official statistics"
       " agency, primary treaty text, official casualty/damage report)",
    2: "Academic / structured dataset (peer-reviewed historical dataset, university"
       " archive, structured conflict/disaster database with documented methodology)",
    3: "High-quality secondary source (established encyclopedia, major news archive"
       " of record, national museum/archive summary)",
    4: "Discovery-only / uncited general reference (used to locate or recall a"
       " candidate event; not independently confirmed against a specific citable"
       " source this session)",
}

# ---------------------------------------------------------------------------
# Verification status -- deliberately stricter than the spec's minimum, because
# this project's whole discipline is "do not claim verification that didn't happen"
# ---------------------------------------------------------------------------

VERIFICATION_STATUS = (
    "UNVERIFIED",             # not checked against any specific citable source this
                               # session; may still be a well-established historical
                               # fact from general reference knowledge -- see notes
    "SINGLE_SOURCE",          # exactly one specific source was actually fetched/read
                               # this session and used to confirm the event record
    "MULTI_SOURCE_CONFIRMED", # two or more independent specific sources were
                               # actually fetched/read this session and agree
    "DISPUTED",                # sources actually checked this session disagree
)

# ---------------------------------------------------------------------------
# Control-date sampling methods (Section 15/16)
# ---------------------------------------------------------------------------

CONTROL_SAMPLING_METHODS = (
    "RANDOM_DATE", "MATCHED_DATE", "CALENDAR_MATCH", "PREDEFINED_CONTROL",
)

# ---------------------------------------------------------------------------
# Event-source link verification status (per-link, distinct from event-level)
# ---------------------------------------------------------------------------

EVENT_SOURCE_LINK_STATUS = ("CONFIRMED", "UNCONFIRMED")
