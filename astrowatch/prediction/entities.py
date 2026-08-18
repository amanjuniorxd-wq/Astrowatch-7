"""
prediction/entities.py
=======================
Real, sourced national-entity inception data (formation/independence date +
capital-city coordinates + IANA timezone) for the cricket-playing nations
covered by this project's dataset. Sourced originally in
kundli_mass/nations_corpus.py (see that module for citations); duplicated
here in a name-keyed form matching the exact team-name strings used in the
source ODI results CSV (`Internation Cricket Results.csv`), since several
CSV team names ("England", "U.A.E.", "P.N.G.", "U.S.A.") are proxies for the
sovereign nation actually charted (see notes below) rather than exact
nation-corpus names.

This is the SAME mapping originally written directly inside
scripts/build_cricket_match_dasha_dataset.py; factored out here so
prediction/features.py and event_backtest/dataset.py can reuse it instead of
duplicating it a second time.
"""
from typing import Dict, Optional, Tuple

# name (as it appears in the ODI results CSV) -> (charted entity name,
# inception_date "YYYY-MM-DD", capital latitude, capital longitude, IANA tz)
ENTITY_INCEPTION: Dict[str, Tuple[str, str, float, float, str]] = {
    "Afghanistan":   ("Afghanistan", "1919-08-19", 34.53, 69.17, "Asia/Kabul"),
    "Australia":     ("Australia", "1901-01-01", -35.28, 149.13, "Australia/Sydney"),
    "Bangladesh":    ("Bangladesh", "1971-03-26", 23.81, 90.41, "Asia/Dhaka"),
    "Canada":        ("Canada", "1867-07-01", 45.42, -75.70, "America/Toronto"),
    "England":       ("United Kingdom", "1801-01-01", 51.51, -0.13, "Europe/London"),
    "India":         ("India", "1947-08-15", 28.61, 77.21, "Asia/Kolkata"),
    "Ireland":       ("Ireland", "1922-12-06", 53.35, -6.26, "Europe/Dublin"),
    "Namibia":       ("Namibia", "1990-03-21", -22.57, 17.08, "Africa/Windhoek"),
    "Nepal":         ("Nepal", "1768-12-21", 27.72, 85.32, "Asia/Kathmandu"),
    "Netherlands":   ("Netherlands", "1815-03-16", 52.37, 4.90, "Europe/Amsterdam"),
    "New Zealand":   ("New Zealand", "1907-09-26", -41.29, 174.78, "Pacific/Auckland"),
    "Oman":          ("Oman", "1970-07-23", 23.61, 58.59, "Asia/Muscat"),
    "P.N.G.":        ("Papua New Guinea", "1975-09-16", -9.44, 147.18, "Pacific/Port_Moresby"),
    "Pakistan":      ("Pakistan", "1947-08-14", 33.68, 73.05, "Asia/Karachi"),
    "South Africa":  ("South Africa", "1910-05-31", -25.75, 28.19, "Africa/Johannesburg"),
    "Sri Lanka":     ("Sri Lanka", "1948-02-04", 6.93, 79.85, "Asia/Colombo"),
    "U.A.E.":        ("United Arab Emirates", "1971-12-02", 24.47, 54.37, "Asia/Dubai"),
    "U.S.A.":        ("United States", "1776-07-04", 38.91, -77.04, "America/New_York"),
    "Zimbabwe":      ("Zimbabwe", "1980-04-18", -17.83, 31.05, "Africa/Harare"),
}

# Teams present in the source ODI CSV that are deliberately EXCLUDED because
# they are not a single, sourceable sovereign-nation entity under this
# project's entity rule (see mundane/entity_chart.py's docstring):
#   - Hong Kong: not a sovereign nation (SAR of China)
#   - Jersey: not a sovereign nation (Crown Dependency)
#   - Scotland: not a sovereign nation (constituent country of the UK, and
#     the UK slot is already used by "England" above -- charting Scotland
#     separately from the UK's actual 1801 union date would be arbitrary)
#   - West Indies: a multi-nation cricket confederation (Anglophone
#     Caribbean), not a single nation -- no single defensible entity chart
EXCLUDED_ENTITIES = {"Hong Kong", "Jersey", "Scotland", "West Indies"}


def lookup(team_name: str) -> Optional[Tuple[str, str, float, float, str]]:
    """Returns (entity_name, inception_date, lat, lon, tz) or None if this
    team name isn't in the mapping (either excluded or genuinely unmapped)."""
    return ENTITY_INCEPTION.get(team_name)


def is_eligible(team_name: str) -> bool:
    return team_name in ENTITY_INCEPTION and team_name not in EXCLUDED_ENTITIES
