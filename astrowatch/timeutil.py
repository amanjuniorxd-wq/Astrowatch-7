"""
Astrowatch — local datetime + timezone -> Julian Day (UT) conversion.
========================================================================
NEW MODULE, built as part of the Swiss Ephemeris migration (see
ARCHITECTURE_SE_MIGRATION.md). Purpose: take user-facing input (a local date, a local
time, and an IANA timezone name) and produce the UT Julian Day that kundli.py actually
needs, WITHOUT ever letting the browser's/server's own local timezone silently leak
into the calculation (item 12 of this session's migration spec).

Uses only the Python standard library `zoneinfo` (3.9+) -- no extra dependency, no
network access, and (unlike a fixed UTC-offset input) correctly handles historical
DST rules and pre-standard-time-zone civil offsets for any IANA zone the platform's
tzdata database knows about.

Deliberately does NOT accept a bare UTC-offset-in-hours as an alternative primary
input path (a common source of longitude/timezone confusion — item 12 again): a
numeric offset is only accepted as an explicit, clearly-labeled fallback for the rare
case where the caller doesn't have or can't determine an IANA zone name (e.g. very
old dates predating a location's modern zone database entry).
"""

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from coordinates import julian_day


class UnknownTimezone(Exception):
    """Raised when the given IANA timezone name isn't found in the platform's tzdata."""


@dataclass
class TimeConversionResult:
    input_local_datetime: str   # ISO-ish string, exactly as given
    timezone_name: str
    utc_datetime: str           # ISO 8601, UTC
    jd_ut: float


def local_to_jd_ut(date_str: str, time_str: str, timezone_name: str) -> TimeConversionResult:
    """
    date_str: "YYYY-MM-DD"
    time_str: "HH:MM" or "HH:MM:SS"
    timezone_name: IANA zone name, e.g. "Asia/Kolkata", "America/New_York", "UTC"

    Returns the UT Julian Day plus the full input/UTC datetime trail, for debugging
    (per item 12's "expose input local datetime / timezone / UTC datetime / Julian Day"
    requirement) -- callers building an API response can surface all of these fields
    directly rather than only the final JD.
    """
    if len(time_str.split(":")) == 2:
        time_str = time_str + ":00"
    try:
        tz = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as e:
        raise UnknownTimezone(
            f"Unknown IANA timezone {timezone_name!r}. Use a name from the IANA tz "
            f"database (e.g. 'Asia/Kolkata', 'America/New_York', 'UTC'), not a raw "
            f"UTC offset or an abbreviation like 'IST'/'EST' (those are ambiguous)."
        ) from e

    local_dt_str = f"{date_str}T{time_str}"
    naive = datetime.fromisoformat(local_dt_str)
    aware_local = naive.replace(tzinfo=tz)
    utc_dt = aware_local.astimezone(ZoneInfo("UTC"))

    hour_ut = utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0
    jd = julian_day(utc_dt.year, utc_dt.month, utc_dt.day, hour_ut)

    return TimeConversionResult(
        input_local_datetime=local_dt_str,
        timezone_name=timezone_name,
        utc_datetime=utc_dt.isoformat(),
        jd_ut=jd,
    )


def utc_offset_to_jd_ut(date_str: str, time_str: str, utc_offset_hours: float) -> TimeConversionResult:
    """
    FALLBACK PATH ONLY (see module docstring) -- use local_to_jd_ut() with a real IANA
    zone name whenever possible. This treats `utc_offset_hours` as a FIXED offset with
    no DST/historical-rule awareness, which is a real precision risk for any location/
    date where the civil clock offset actually changed (this happened almost
    everywhere at some point in history) -- callers should prefer a real zone name.
    """
    if len(time_str.split(":")) == 2:
        time_str = time_str + ":00"
    naive = datetime.fromisoformat(f"{date_str}T{time_str}")
    hour_local = naive.hour + naive.minute / 60.0 + naive.second / 3600.0
    hour_ut = hour_local - utc_offset_hours
    # Julian day arithmetic handles hour_ut outside [0,24) correctly (fractional day),
    # so no manual day-rollover is needed here.
    jd = julian_day(naive.year, naive.month, naive.day, hour_ut)
    return TimeConversionResult(
        input_local_datetime=f"{date_str}T{time_str}",
        timezone_name=f"UTC{utc_offset_hours:+.2f}",
        utc_datetime="(fixed-offset fallback -- no calendar-accurate UTC datetime computed)",
        jd_ut=jd,
    )
