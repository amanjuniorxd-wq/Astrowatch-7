#!/usr/bin/env python3
"""
Astrowatch -- forward-looking Mahadasha/Antardasha theme lookup for a named
person already in this project's corpora (famous_people_corpus.py /
leaders_corpus.py) OR for arbitrary supplied birth data.

Given a person, computes their CURRENT and NEXT Mahadasha/Antardasha (via the
correct birth-progressed walk, same method used throughout this project) as
of a target date (default: today, 2026-08-15), and returns a plain-language,
explicitly labeled "astrological calculation only" description grounded in:
  (a) classical Vedic graha significations (GRAHA_THEME, uncontroversial),
  (b) the ACTUAL NATAL KUNDLI CHART -- which house the Mahadasha/Antardasha
      lord occupies at birth, which house(s) it owns (rulership), its
      classical dignity there (exalted/debilitated/own sign/neutral), and
      its classical aspect (drishti) onto other houses. This is the real
      technique for turning a dasha period into a life-area reading in
      Vedic astrology (a dasha lord's period is read through what house(s)
      it occupies/owns/aspects, not just its abstract planetary theme) --
      newly wired into this tool per explicit user request to make sure the
      actual chart, not just the dasha-lord label, drives the reading.
  (c) this project's own small, non-random, exploratory sample frequency
      (life_events_dasha_mapping.db, 76 events / 18 people) where available,
      always clearly marked as anecdotal, not validated.

House significations, exaltation/debilitation signs, own-sign rulerships and
the Mars/Jupiter/Saturn special-aspect rules below are standard, textbook
Vedic astrology reference data (verified via live web research this session
against multiple independent sources: vedicfeed.com, astronidan.com,
jagannathhora.com and others) -- the same "well-established, non-disputed
reference system" status as the Vimshottari sequence itself, not this
project's own interpretation. Rahu/Ketu are deliberately left out of the
dignity/aspect tables below: their exaltation and aspect rules vary by
tradition/text and are NOT settled the way the 7 classical grahas are, so
asserting a specific rule for them here would misrepresent disputed content
as settled fact.

IMPORTANT RELIABILITY CAVEAT: house/Ascendant-based reading is only
meaningful when the birth TIME is actually known (birth_time_source ==
DOCUMENTED). For ASSUMED_NOON entries (the majority of this project's
famous_people_corpus), the Ascendant and house placements are not reliable
-- this tool prints an explicit warning and skips the chart-based section in
that case, falling back to the dasha-lord-theme-only reading.

Does NOT make specific outcome/date claims, does NOT name real ongoing
high-stakes situations, does NOT speculate on death/violence/marriage for
real named individuals -- same safety boundaries held throughout this
project. This is a plain deterministic calculation tool, not a chatbot; it
prints one structured result per invocation.

Usage:
  python3 predict_person_dasha_theme.py --name "Cristiano Ronaldo"
  python3 predict_person_dasha_theme.py --name "Cristiano Ronaldo" --date 2027-06-01
  python3 predict_person_dasha_theme.py --date 1990-05-15 --time 14:30 --tz Asia/Kolkata --lat 28.61 --lon 77.21 --target 2026-08-15
"""
import argparse
import os
import sqlite3
import sys
from datetime import datetime, timezone as dt_timezone
from zoneinfo import ZoneInfo

ASTROWATCH_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ASTROWATCH_DIR)
import coordinates
from kundli import compute_kundli
from mahadasha import (compute_dasha_state, DASHA_SEQUENCE, _lord_index,
                        _compute_antardasha, DashaPeriod, _SIDEREAL_YEAR_DAYS)

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, THIS_DIR)

DISCLAIMER = ("Astrological calculation, not a forecast. Unvalidated pattern-based "
              "reading; Astrowatch's own backtest (BT-001) found no real predictive "
              "edge. Not to be relied on for real decisions.")

GRAHA_THEME = {
    "sun": "authority, visibility and executive action",
    "moon": "public mood, emotional currents and personal/domestic life",
    "mars": "confrontation, assertive moves and sudden action",
    "mercury": "communication, negotiation and information flow",
    "jupiter": "expansion, recognition and institutional validation",
    "venus": "creativity, relationships, wealth and public appeal",
    "saturn": "delay, restriction, endings and structural pressure",
    "rahu": "disruption, ambition and unconventional breakthroughs",
    "ketu": "withdrawal, loose ends and quiet transitions",
}

# --- Real natal-chart reference data (verified via live web research this
# session: vedicfeed.com, astronidan.com, jagannathhora.com, steer.coach,
# omai.app -- standard textbook Vedic astrology, not this project's own
# interpretation). Rahu/Ketu intentionally excluded -- see module docstring. ---

HOUSE_SIGNIFICATIONS = {
    1: "self, body, personality, general vitality",
    2: "wealth, family, speech, accumulated resources",
    3: "courage, siblings, effort, short journeys, communication",
    4: "home, mother, emotional foundation, property",
    5: "creativity, children, intelligence, romance",
    6: "health, obstacles, competition, daily work",
    7: "partnerships, marriage, public dealings, open rivals",
    8: "transformation, longevity, sudden change, shared resources",
    9: "fortune, higher learning, philosophy, father, long journeys",
    10: "career, public standing, authority, actions in the world",
    11: "gains, income, networks, aspirations",
    12: "loss, expenditure, foreign lands, withdrawal, endings",
}

EXALTATION_SIGN = {
    "sun": "Mesha", "moon": "Vrishabha", "mars": "Makara", "mercury": "Kanya",
    "jupiter": "Karka", "venus": "Meena", "saturn": "Tula",
}
DEBILITATION_SIGN = {
    "sun": "Tula", "moon": "Vrischika", "mars": "Karka", "mercury": "Meena",
    "jupiter": "Makara", "venus": "Kanya", "saturn": "Mesha",
}
OWN_SIGNS = {
    "sun": ["Simha"], "moon": ["Karka"], "mars": ["Mesha", "Vrischika"],
    "mercury": ["Mithuna", "Kanya"], "jupiter": ["Dhanu", "Meena"],
    "venus": ["Vrishabha", "Tula"], "saturn": ["Makara", "Kumbha"],
}
# Universal 7th-house aspect for every planet; Mars/Jupiter/Saturn add these extras.
SPECIAL_ASPECT_HOUSES = {"mars": [4, 8], "jupiter": [5, 9], "saturn": [3, 10]}

RASHI_ORDER = ["Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya",
               "Tula", "Vrischika", "Dhanu", "Makara", "Kumbha", "Meena"]

LIFE_EVENTS_DB = os.path.join(THIS_DIR, "life_events_dasha_mapping.db")


def dignity_of(lord, rashi_name):
    """Returns None for rahu/ketu (no settled classical rule -- see docstring)."""
    if lord not in EXALTATION_SIGN:
        return None
    if rashi_name == EXALTATION_SIGN[lord]:
        return "exalted"
    if rashi_name == DEBILITATION_SIGN[lord]:
        return "debilitated"
    if rashi_name in OWN_SIGNS.get(lord, []):
        return "in its own sign"
    return "neutral dignity"


def houses_owned_by(lord, asc_rashi_index):
    """Whole-sign house numbers occupied by each sign this lord rules, given the
    natal Ascendant's sign. Returns [] for rahu/ketu (no sign rulership)."""
    owned = []
    for sign in OWN_SIGNS.get(lord, []):
        sign_idx = RASHI_ORDER.index(sign)
        house = ((sign_idx - asc_rashi_index) % 12) + 1
        owned.append(house)
    return sorted(owned)


def aspected_houses_of(lord, occupied_house):
    """Houses this lord casts its classical aspect (drishti) onto, counting
    from its OCCUPIED house (not its owned houses)."""
    offsets = [7] + SPECIAL_ASPECT_HOUSES.get(lord, [])
    return sorted(set(((occupied_house - 1 + off) % 12) + 1 for off in offsets))


def chart_reading_for_lord(chart, lord, asc_rashi_index):
    placement = chart.grahas[lord]
    occupied_house = placement.house
    occupied_rashi = placement.rashi.rashi_name
    dignity = dignity_of(lord, occupied_rashi)
    owned = houses_owned_by(lord, asc_rashi_index)
    aspected = aspected_houses_of(lord, occupied_house)

    parts = [f"natally placed in house {occupied_house} ({HOUSE_SIGNIFICATIONS[occupied_house]})"
             f" in {occupied_rashi}"]
    if dignity:
        parts.append(f"{dignity} there")
    if owned:
        owned_str = ", ".join(f"house {h} ({HOUSE_SIGNIFICATIONS[h]})" for h in owned)
        parts.append(f"rules {owned_str}")
    if aspected:
        aspected_str = ", ".join(str(h) for h in aspected)
        parts.append(f"casts its classical aspect onto house(s) {aspected_str}")
    return "; ".join(parts) + "."


def jd_for(date_iso, time_hhmm, tz_name):
    y, m, d = (int(x) for x in date_iso.split("-"))
    if time_hhmm:
        hh, mm = (int(x) for x in time_hhmm.split(":"))
    else:
        hh, mm = 12, 0
    local_dt = datetime(y, m, d, hh, mm, tzinfo=ZoneInfo(tz_name))
    utc_dt = local_dt.astimezone(dt_timezone.utc)
    return coordinates.julian_day(utc_dt.year, utc_dt.month, utc_dt.day,
                                   utc_dt.hour + utc_dt.minute / 60.0)


def progress_dasha(birth_jd, natal_moon_lon, target_jd):
    birth_dasha = compute_dasha_state(birth_jd, natal_moon_lon)
    cursor = birth_dasha.mahadasha
    idx = _lord_index(cursor.lord)
    while cursor.end_jd_ut < target_jd:
        idx = (idx + 1) % 9
        lord, years = DASHA_SEQUENCE[idx]
        start = cursor.end_jd_ut
        end = start + years * _SIDEREAL_YEAR_DAYS
        cursor = DashaPeriod(lord=lord, start_jd_ut=start, end_jd_ut=end, level="mahadasha")
    antardasha = _compute_antardasha(target_jd, cursor, idx)
    next_idx = (idx + 1) % 9
    next_lord, next_years = DASHA_SEQUENCE[next_idx]
    return cursor.lord, antardasha.lord, cursor.end_jd_ut, next_lord


def lookup_person(name):
    """Search famous_people_corpus.py then leaders_corpus.py for a matching name."""
    try:
        from famous_people_corpus import PEOPLE
        for p in PEOPLE:
            if p[0].lower() == name.lower():
                nm, date, time_hhmm, tz, country, lat, lon, field, note = p
                return dict(name=nm, date=date, time=time_hhmm, tz=tz, lat=lat, lon=lon, field=field)
    except Exception:
        pass
    try:
        from leaders_corpus import LEADERS
        for l in LEADERS:
            nm = l[0]
            if nm.lower() == name.lower():
                (_, bdate, btime, btz, country, lat, lon, group, *_rest) = l
                return dict(name=nm, date=bdate, time=btime, tz=btz, lat=lat, lon=lon, field=group)
    except Exception:
        pass
    return None


def sample_frequency_note(mahadasha_lord):
    """Optional small-sample cross-reference against life_events_dasha_mapping.db,
    always caveated. Returns None if the db is unavailable."""
    if not os.path.exists(LIFE_EVENTS_DB):
        return None
    con = sqlite3.connect(LIFE_EVENTS_DB)
    cur = con.execute("SELECT event_type FROM life_events_dasha WHERE mahadasha_lord=?", (mahadasha_lord,))
    types = [r[0] for r in cur.fetchall()]
    con.close()
    if not types:
        return None
    pos = {"BREAKTHROUGH", "AWARD", "RECORD", "COMEBACK", "MARRIAGE"}
    n_pos = sum(1 for t in types if t in pos)
    return (f"In this project's own small, non-random 76-event research sample "
            f"(18 highly-documented public figures), {n_pos}/{len(types)} events that fell "
            f"during a {mahadasha_lord} mahadasha were career-positive milestones -- "
            f"anecdotal only, not a validated statistic.")


def describe(name, mahadasha_lord, antardasha_lord, maha_ends_iso, next_lord,
             chart=None, asc_rashi_index=None, time_source=None):
    theme_m = GRAHA_THEME[mahadasha_lord]
    theme_a = GRAHA_THEME[antardasha_lord]
    note = sample_frequency_note(mahadasha_lord)
    lines = []
    lines.append(f"ASTROLOGICAL CALCULATION for {name}")
    lines.append(f"Current Mahadasha: {mahadasha_lord} (classical theme: {theme_m})")
    lines.append(f"Current Antardasha: {antardasha_lord} (classical theme: {theme_a})")
    lines.append(f"This Mahadasha runs until approximately {maha_ends_iso}, after which the "
                 f"{next_lord} Mahadasha begins.")

    if chart is not None and time_source == "DOCUMENTED":
        lines.append("")
        lines.append(f"NATAL CHART READING (Ascendant {chart.ascendant_rashi.rashi_name}, "
                      f"documented birth time -- house placements reliable):")
        lines.append(f"  Mahadasha lord {mahadasha_lord}: "
                      f"{chart_reading_for_lord(chart, mahadasha_lord, asc_rashi_index)}")
        lines.append(f"  Antardasha lord {antardasha_lord}: "
                      f"{chart_reading_for_lord(chart, antardasha_lord, asc_rashi_index)}")
        lines.append("")
        lines.append(f"Combined reading: the {mahadasha_lord} Mahadasha activates the house(s) "
                      f"it occupies and rules in the natal chart above, carrying "
                      f"{theme_m}; the {antardasha_lord} Antardasha inflects that with "
                      f"{theme_a} through its own house placement. This is a genuine "
                      f"chart-based reading (house + dignity + aspect), not just the "
                      f"abstract planetary theme -- but still not a specific outcome or "
                      f"event prediction.")
    else:
        if chart is not None and time_source != "DOCUMENTED":
            lines.append("")
            lines.append("NOTE: birth time for this person is ASSUMED_NOON (not documented), so "
                          "Ascendant and house placements are NOT reliable and are skipped here. "
                          "Only the Moon-nakshatra-derived Mahadasha/Antardasha lords (time-"
                          "insensitive) are used below.")
        lines.append(f"Combined reading: themes of {theme_m}, inflected by {theme_a}, are the "
                     f"astrological backdrop for this period -- not a specific outcome or event "
                     f"prediction.")
    if note:
        lines.append(note)
    lines.append(DISCLAIMER)
    return "\n".join(lines)


def jd_to_iso_date(jd_ut: float) -> str:
    jd = jd_ut + 0.5
    z = int(jd)
    f = jd - z
    if z < 2299161:
        a = z
    else:
        alpha = int((z - 1867216.25) / 36524.25)
        a = z + 1 + alpha - alpha // 4
    b = a + 1524
    c = int((b - 122.1) / 365.25)
    d = int(365.25 * c)
    e = int((b - d) / 30.6001)
    day = int(b - d - int(30.6001 * e) + f)
    month = e - 1 if e < 14 else e - 13
    year = c - 4716 if month > 2 else c - 4715
    return f"{year:04d}-{month:02d}-{day:02d}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", help="Person name, looked up in famous_people_corpus.py / leaders_corpus.py")
    ap.add_argument("--date", help="Birth date YYYY-MM-DD (if not using --name)")
    ap.add_argument("--time", help="Birth time HH:MM (optional; ASSUMED_NOON if omitted)")
    ap.add_argument("--tz", help="IANA timezone name")
    ap.add_argument("--lat", type=float, help="Birth latitude")
    ap.add_argument("--lon", type=float, help="Birth longitude")
    ap.add_argument("--target", default="2026-08-15", help="Target date YYYY-MM-DD (default: today)")
    args = ap.parse_args()

    if args.name:
        person = lookup_person(args.name)
        if not person:
            print(f"'{args.name}' not found in famous_people_corpus.py or leaders_corpus.py. "
                  f"Supply --date/--time/--tz/--lat/--lon instead.")
            sys.exit(1)
        date, time_hhmm, tz, lat, lon = person["date"], person["time"], person["tz"], person["lat"], person["lon"]
        display_name = person["name"]
    else:
        if not (args.date and args.tz and args.lat is not None and args.lon is not None):
            print("Either --name or (--date --tz --lat --lon) is required.")
            sys.exit(1)
        date, time_hhmm, tz, lat, lon = args.date, args.time, args.tz, args.lat, args.lon
        display_name = "supplied birth data"

    birth_jd = jd_for(date, time_hhmm, tz)
    chart = compute_kundli(birth_jd, lat, lon)
    natal_moon_lon = chart.grahas["moon"].sidereal_lon_deg

    target_jd = jd_for(args.target, "12:00", "UTC")
    maha_lord, antar_lord, maha_end_jd, next_lord = progress_dasha(birth_jd, natal_moon_lon, target_jd)
    maha_end_iso = jd_to_iso_date(maha_end_jd)

    time_source = "DOCUMENTED" if time_hhmm else "ASSUMED_NOON"
    asc_rashi_index = chart.ascendant_rashi.rashi_index

    print(describe(display_name, maha_lord, antar_lord, maha_end_iso, next_lord,
                    chart=chart, asc_rashi_index=asc_rashi_index, time_source=time_source))


if __name__ == "__main__":
    main()
