#!/usr/bin/env python3
"""
Astrowatch -- US Midterms 2026 astrological calculation (Republican vs. Democrat).
See US_MIDTERMS_2026_ASTROLOGICAL_CALCULATION.md for the full write-up, sourcing,
and caveats. This script reproduces every number in that report.

Applies the mundane-astrology rule (MUNDANE_ASTROLOGY_RULE.md) to the two parties'
own real, sourced founding dates/places, computes which Mahadasha/Antardasha rules
each on election day (2026-11-03, confirmed via live search) using the same
validated, multi-cycle-aware progressed-dasha walker used for the nations work, and
scores each ruling lord on natal dignity + house strength + benefic/malefic nature
-- a scoring convention built for this analysis, not a classical citation.
"""
import os
import sys

ASTROWATCH_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ASTROWATCH_DIR)
import coordinates
from mundane.entity_chart import compute_entity_chart, full_lifetime_dasha
from mundane.dasha_timeline import jd_to_iso_date

ELECTION_DATE = "2026-11-03"

EXALTATION_SIGN = {"sun": "Mesha", "moon": "Vrishabha", "mars": "Makara", "mercury": "Kanya",
                    "jupiter": "Karka", "venus": "Meena", "saturn": "Tula"}
DEBILITATION_SIGN = {"sun": "Tula", "moon": "Vrischika", "mars": "Karka", "mercury": "Meena",
                      "jupiter": "Makara", "venus": "Kanya", "saturn": "Mesha"}
OWN_SIGNS = {"sun": {"Simha"}, "moon": {"Karka"}, "mars": {"Mesha", "Vrischika"},
             "mercury": {"Mithuna", "Kanya"}, "jupiter": {"Dhanu", "Meena"},
             "venus": {"Vrishabha", "Tula"}, "saturn": {"Makara", "Kumbha"}}
BENEFICS = {"jupiter", "venus", "mercury", "moon"}
KENDRA = {1, 4, 7, 10}
TRIKONA = {1, 5, 9}
DUSHTANA = {6, 8, 12}


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


def score_lord(chart, asc_idx, lord):
    if lord not in chart.grahas:
        return 0.0, "N/A", None, "node"
    r = chart.grahas[lord].rashi.rashi_name
    d = dignity_of(lord, r)
    h = house_of(chart.grahas[lord].rashi.rashi_index, asc_idx)
    kind = "kendra" if h in KENDRA else ("trikona" if h in TRIKONA else ("dushtana" if h in DUSHTANA else "other"))
    dign_pts = {"EXALTED": 2, "OWN_SIGN": 1, "NEUTRAL": 0, "DEBILITATED": -2, "N/A": 0}[d]
    house_pts = {"kendra": 1, "trikona": 1, "dushtana": -1, "other": 0}[kind]
    nature_pts = 0.5 if lord in BENEFICS else -0.5
    return dign_pts + house_pts + nature_pts, d, h, kind


def analyze_party(name, date, lat, lon, tz):
    ec = compute_entity_chart(name, "political_party", date, lat, lon, tz)
    chart = ec.chart
    asc_idx = chart.ascendant_rashi.rashi_index
    end_jd = coordinates.julian_day(2027, 1, 1, 0)
    periods = full_lifetime_dasha(ec, end_jd)
    for p in periods:
        maha_i, ml, ms, me, ant_i, al, as_, ae = p
        if jd_to_iso_date(as_) <= ELECTION_DATE < jd_to_iso_date(ae):
            maha_score, maha_d, maha_h, maha_kind = score_lord(chart, asc_idx, ml)
            antar_score, antar_d, antar_h, antar_kind = score_lord(chart, asc_idx, al)
            combined = maha_score * 0.4 + antar_score * 0.6
            print(f"\n=== {name} (founded {date}, {lat},{lon}, {tz}) ===")
            print(f"Ascendant: {chart.ascendant_rashi.rashi_name}")
            print(f"  Mahadasha={ml.upper()} [{jd_to_iso_date(ms)}->{jd_to_iso_date(me)}] "
                  f"dignity={maha_d} house={maha_h}({maha_kind}) score={maha_score:+.1f}")
            print(f"  Antardasha={al.upper()} [{jd_to_iso_date(as_)}->{jd_to_iso_date(ae)}] "
                  f"dignity={antar_d} house={antar_h}({antar_kind}) score={antar_score:+.1f}")
            print(f"  Combined score = {combined:+.2f}")
            return combined
    raise RuntimeError(f"no dasha period found covering {ELECTION_DATE} for {name}")


if __name__ == "__main__":
    rep = analyze_party("Republican Party", "1854-03-20", 43.84, -88.84, "America/Chicago")
    dem = analyze_party("Democratic Party", "1828-01-08", 29.95, -90.07, "America/Chicago")

    usa = compute_entity_chart("United States", "nation", "1776-07-04", 38.91, -77.04, "America/New_York")
    end_jd = coordinates.julian_day(2027, 1, 1, 0)
    for p in full_lifetime_dasha(usa, end_jd):
        maha_i, ml, ms, me, ant_i, al, as_, ae = p
        if jd_to_iso_date(as_) <= ELECTION_DATE < jd_to_iso_date(ae):
            print(f"\n=== USA national chart context ===")
            print(f"On {ELECTION_DATE}: Mahadasha={ml.upper()} Antardasha={al.upper()}")
            break

    print(f"\n>>> Republican combined score: {rep:+.2f}")
    print(f">>> Democratic combined score: {dem:+.2f}")
    print(f">>> Favored by this methodology: "
          f"{'DEMOCRATIC' if dem > rep else ('REPUBLICAN' if rep > dem else 'TIE')}")
