"""
Astrowatch -- cricket match x national-entity Dasha/dignity pattern dataset.
===================================================================
Reads the user-supplied real ODI match-result corpus (1052 international ODI
matches, 2015-01-08 to 2023-08-01, from ESPNcricinfo-sourced result data) and,
for every match where BOTH teams map to a real, sourced national entity this
project can chart (kundli_mass/nations_corpus.py -- a sovereign nation with a
real, documented formation/independence date), computes each team's national
Vimshottari Mahadasha/Antardasha state AS OF the match date via the EXISTING,
already-validated world_astrology.reading_engine.build_chart_bundle() -- no
astronomical calculation is reimplemented here, only orchestrated.

This directly implements the "kundli chart + horoscope for each team on each
match" request: build_chart_bundle(as_of_date=match_date) IS that team's
horoscope reading as of that match.

EXCLUDED (honestly, not silently dropped): Hong Kong, Jersey, Scotland, West
Indies -- none is a sovereign nation with a documented formation/independence
date the way this project's mundane-astrology entity-chart rule requires
(West Indies specifically represents multiple sovereign Caribbean nations, so
no single "West Indies entity chart" is defensible under this project's
existing rule). Matches involving any of these four are excluded from the
dataset and counted/reported separately, never silently treated as if they
had usable data.

Output: kundli_mass/cricket_match_dasha_dataset.csv -- one row per eligible
match with both teams' Mahadasha/Antardasha lord + dignity score as of the
match date, plus the real recorded winner. This is a DESCRIPTIVE/pattern
dataset, not itself a prediction -- see
scripts/analyze_cricket_match_dasha_patterns.py for the actual correlation
analysis computed FROM this file, and prediction/scorer.py's MODEL_CONFIG
docstring for how (if at all) any resulting pattern is used as a real,
disclosed input to the live scoring model.
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from world_astrology import reading_engine
from world_astrology import dignity_tables as dt

INPUT_CSV = "/tmp/cricket_data/Internation Cricket Results.csv"
OUTPUT_CSV = os.path.join(HERE, "kundli_mass", "cricket_match_dasha_dataset.csv")

# CSV team name -> (Astrowatch entity name, entity_type, inception_date, lat, lon, tz)
# Sourced from kundli_mass/nations_corpus.py (already-vetted real formation/
# independence dates+coordinates) -- values copied here (not re-derived) so this
# script has no import-time dependency on nations_corpus's internal _add() list
# structure; if nations_corpus.py's data ever changes, re-sync this table by hand.
TEAM_ENTITY = {
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
EXCLUDED_TEAMS = {"Hong Kong", "Jersey", "Scotland", "West Indies"}


def team_horoscope(team_csv_name: str, as_of_date: str):
    entity_name, inception_date, lat, lon, tz = TEAM_ENTITY[team_csv_name]
    bundle = reading_engine.build_chart_bundle(
        entity_name, "country", inception_date, lat, lon, tz, as_of_date=as_of_date,
    )
    chart = bundle.entity.chart
    ml = bundle.dasha.mahadasha_lord
    ml_placement = chart.grahas.get(ml)
    if ml_placement is not None:
        ml_score, ml_dignity, _ = dt.jyotisha_score(ml, ml_placement.rashi.rashi_name, ml_placement.house)
    else:
        ml_score, ml_dignity = None, "N/A"
    return {
        "mahadasha_lord": ml, "mahadasha_lord_dignity": ml_dignity, "mahadasha_lord_score": ml_score,
        "antardasha_lord": bundle.dasha.antardasha_lord,
        "antardasha_lord_dignity": bundle.agreement.jyotisha_dignity,
        "antardasha_lord_score": bundle.agreement.jyotisha_score,
        "agreement_classification": bundle.agreement.classification,
        "moon_rashi": chart.grahas["moon"].rashi.rashi_name,
        "moon_nakshatra": chart.grahas["moon"].nakshatra.nakshatra_name,
    }


def main():
    with open(INPUT_CSV) as f:
        rows = list(csv.DictReader(f))

    eligible, excluded = [], []
    for r in rows:
        t1, t2 = r["Team 1"], r["Team 2"]
        if t1 in EXCLUDED_TEAMS or t2 in EXCLUDED_TEAMS or t1 not in TEAM_ENTITY or t2 not in TEAM_ENTITY:
            excluded.append(r)
            continue
        eligible.append(r)

    print(f"Total matches in source CSV: {len(rows)}")
    print(f"Eligible (both teams have real, sourced entity data): {len(eligible)}")
    print(f"Excluded (West Indies/Hong Kong/Jersey/Scotland or unmapped): {len(excluded)}")

    out_rows = []
    errors = 0
    for i, r in enumerate(eligible):
        t1, t2, date, winner = r["Team 1"], r["Team 2"], r["Match Date"], r["Winner"]
        try:
            h1 = team_horoscope(t1, date)
            h2 = team_horoscope(t2, date)
        except Exception as e:  # noqa: BLE001 -- record and continue, never silently skip
            errors += 1
            print(f"  [{i}] ERROR computing horoscope for {t1} vs {t2} on {date}: {e}")
            continue
        row = {
            "match_date": date, "team1": t1, "team2": t2, "winner": winner,
            "margin": r["Margin"], "ground": r["Ground"], "scorecard": r["Scorecard"],
        }
        for k, v in h1.items():
            row[f"team1_{k}"] = v
        for k, v in h2.items():
            row[f"team2_{k}"] = v
        out_rows.append(row)
        if (i + 1) % 100 == 0:
            print(f"  ... {i + 1}/{len(eligible)} processed")

    print(f"Successfully computed: {len(out_rows)}; errors: {errors}")

    fieldnames = list(out_rows[0].keys()) if out_rows else []
    with open(OUTPUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(out_rows)
    print(f"Wrote {len(out_rows)} rows to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
