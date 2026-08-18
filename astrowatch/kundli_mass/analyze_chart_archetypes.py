#!/usr/bin/env python3
"""
Astrowatch -- chart-archetype pattern analysis across the full famous_people_corpus.py
(674 people, 7 career fields). Pure derived computation from already-validated chart
math (kundli.compute_kundli) -- no new web research needed, so this runs at FULL
corpus scale, unlike the (necessarily much smaller, individually-researched) real
dated-event/dasha correlation work elsewhere in this project.

WHAT THIS LOOKS FOR: does a person's career FIELD (actor/athlete/scientist/business/
musician/author/artist-director) correlate with which graha rules their 10th house
(karma/career, whole-sign) or 1st house (self/personality), that graha's dignity
(exalted / debilitated / own-sign / neutral in its OWN sign, sign-level only -- this
project doesn't have degree-level natal data stored for most people, so moolatrikona/
degree-exact dignity is out of scope here), and (for a rough "achievement" proxy)
whether the 10th-lord or 1st-lord is well-dignified. For a rough HEALTH proxy: whether
the 6th/8th/12th houses (classical dushtana / affliction houses) contain a
malefic (Saturn/Mars/Rahu/Ketu) in this sign-level, Ascendant-quality-dependent way
-- flagged with the same "ASSUMED_NOON charts have unreliable house placements"
caveat as everywhere else in this corpus.

DATA HONESTY: dignity/house-lordship tables below are standard classical Vedic
astrology reference data (same status as mahadasha.py's Vimshottari sequence --
sign-level exaltation/debilitation/own-sign points are universally agreed across
traditions; exact degree-level moolatrikona ranges and Rahu/Ketu's disputed
exaltation signs are NOT included here, since this project doesn't have the
precision or traditional-source backing to assert either from this session).
"""
import os
import sys
from collections import Counter, defaultdict

ASTROWATCH_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ASTROWATCH_DIR)
from kundli import compute_kundli, EphemerisDataUnavailable

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, THIS_DIR)
from famous_people_corpus import PEOPLE

from datetime import datetime, timezone as dt_timezone
from zoneinfo import ZoneInfo
import coordinates

RASHI_LORD = {
    "Mesha": "mars", "Vrishabha": "venus", "Mithuna": "mercury", "Karka": "moon",
    "Simha": "sun", "Kanya": "mercury", "Tula": "venus", "Vrischika": "mars",
    "Dhanu": "jupiter", "Makara": "saturn", "Kumbha": "saturn", "Meena": "jupiter",
}
RASHI_ORDER = ["Mesha","Vrishabha","Mithuna","Karka","Simha","Kanya","Tula",
               "Vrischika","Dhanu","Makara","Kumbha","Meena"]
EXALTATION_SIGN = {"sun":"Mesha","moon":"Vrishabha","mars":"Makara","mercury":"Kanya",
                    "jupiter":"Karka","venus":"Meena","saturn":"Tula"}
DEBILITATION_SIGN = {"sun":"Tula","moon":"Vrischika","mars":"Karka","mercury":"Meena",
                      "jupiter":"Makara","venus":"Kanya","saturn":"Mesha"}
OWN_SIGNS = {"sun":{"Simha"},"moon":{"Karka"},"mars":{"Mesha","Vrischika"},
             "mercury":{"Mithuna","Kanya"},"jupiter":{"Dhanu","Meena"},
             "venus":{"Vrishabha","Tula"},"saturn":{"Makara","Kumbha"}}
MALEFICS = {"saturn", "mars", "rahu", "ketu"}
BENEFICS = {"jupiter", "venus", "mercury", "moon"}


def dignity_of(graha, rashi_name):
    if graha not in EXALTATION_SIGN:
        return "N/A"
    if rashi_name == EXALTATION_SIGN[graha]:
        return "EXALTED"
    if rashi_name == DEBILITATION_SIGN[graha]:
        return "DEBILITATED"
    if rashi_name in OWN_SIGNS[graha]:
        return "OWN_SIGN"
    return "NEUTRAL"


def house_of(rashi_idx, asc_idx):
    return ((rashi_idx - asc_idx) % 12) + 1


def jd_for(date, time_hhmm, tz):
    y, m, d = (int(x) for x in date.split("-"))
    hh, mm = (12, 0) if not time_hhmm else (int(x) for x in time_hhmm.split(":"))
    local_dt = datetime(y, m, d, hh, mm, tzinfo=ZoneInfo(tz))
    utc_dt = local_dt.astimezone(dt_timezone.utc)
    return coordinates.julian_day(utc_dt.year, utc_dt.month, utc_dt.day,
                                   utc_dt.hour + utc_dt.minute / 60.0)


def analyze():
    by_field_10th_lord = defaultdict(Counter)
    by_field_10th_dignity = defaultdict(Counter)
    by_field_1st_lord_dignity = defaultdict(Counter)
    by_field_health_affliction = defaultdict(Counter)  # count of malefics in 6/8/12
    n_by_field = Counter()
    errors = 0

    for (name, date, time_hhmm, tz, country, lat, lon, field, note) in PEOPLE:
        try:
            jd = jd_for(date, time_hhmm, tz)
            chart = compute_kundli(jd, lat, lon)
        except (EphemerisDataUnavailable, Exception):
            errors += 1
            continue

        asc_idx = chart.ascendant_rashi.rashi_index
        n_by_field[field] += 1

        # 10th house sign (whole-sign) and its lord
        tenth_sign_idx = (asc_idx + 9) % 12
        tenth_sign = RASHI_ORDER[tenth_sign_idx]
        tenth_lord = RASHI_LORD[tenth_sign]
        by_field_10th_lord[field][tenth_lord] += 1

        # dignity of that 10th-lord graha WHEREVER IT ACTUALLY SITS in this chart
        if tenth_lord in chart.grahas:
            tenth_lord_rashi = chart.grahas[tenth_lord].rashi.rashi_name
            by_field_10th_dignity[field][dignity_of(tenth_lord, tenth_lord_rashi)] += 1

        # 1st-lord (Ascendant lord) dignity -- personality/vitality proxy
        asc_sign = RASHI_ORDER[asc_idx]
        asc_lord = RASHI_LORD[asc_sign]
        if asc_lord in chart.grahas:
            asc_lord_rashi = chart.grahas[asc_lord].rashi.rashi_name
            by_field_1st_lord_dignity[field][dignity_of(asc_lord, asc_lord_rashi)] += 1

        # health proxy: how many malefics (Saturn/Mars/Rahu/Ketu) occupy houses 6/8/12
        malefic_count = 0
        for g in ("saturn", "mars", "rahu", "ketu"):
            h = house_of(chart.grahas[g].rashi.rashi_index, asc_idx)
            if h in (6, 8, 12):
                malefic_count += 1
        by_field_health_affliction[field][malefic_count] += 1

    return {
        "n_by_field": n_by_field, "errors": errors,
        "tenth_lord": by_field_10th_lord, "tenth_dignity": by_field_10th_dignity,
        "first_lord_dignity": by_field_1st_lord_dignity,
        "health_affliction": by_field_health_affliction,
    }


if __name__ == "__main__":
    r = analyze()
    print("n_by_field:", dict(r["n_by_field"]), "errors:", r["errors"])
    for field in sorted(r["n_by_field"]):
        print(f"\n=== {field} (n={r['n_by_field'][field]}) ===")
        print(" 10th-house sign lord (career-house ruler):", r["tenth_lord"][field].most_common())
        print(" 10th-lord dignity:", r["tenth_dignity"][field].most_common())
        print(" Ascendant-lord dignity:", r["first_lord_dignity"][field].most_common())
        print(" malefics in 6/8/12 (0-4):", sorted(r["health_affliction"][field].items()))
