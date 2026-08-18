#!/usr/bin/env python3
"""
Astrowatch -- pattern extraction over life_events_dasha_mapping.db (the 204
real, web-sourced, dated career/life events for 53 highly-documented people,
mapped to their mechanically-computed Mahadasha/Antardasha periods).

Combines this project's own small-sample empirical frequencies with the
classical Vedic graha significations already used throughout the daily-
predictions work (GRAHA_THEME) into a labeled synthesis report. Every
frequency below is a REAL COUNT over this specific 76-event sample -- not
invented -- but the sample is small and non-random (chosen for documentation
quality, not statistical representativeness), so this is explicitly
EXPLORATORY, consistent with ASTROWATCH-BT-001's null result on the much
larger 519-event historical corpus.
"""
import os
import sqlite3
from collections import Counter, defaultdict

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(THIS_DIR, "life_events_dasha_mapping.db")
OUT_MD = os.path.join(THIS_DIR, "GRAHA_MAHADASHA_LIFE_EVENT_SYNTHESIS.md")

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

POSITIVE_TYPES = {"BREAKTHROUGH", "AWARD", "RECORD", "COMEBACK", "MARRIAGE"}
NEGATIVE_TYPES = {"CONTROVERSY", "RETIREMENT", "DIVORCE", "TRAGEDY", "DEATH"}
NEUTRAL_TYPES = {"FINANCIAL"}  # business/financial milestones -- not classified pos/neg
ALL_TYPES_SET = POSITIVE_TYPES | NEGATIVE_TYPES | NEUTRAL_TYPES


def main():
    con = sqlite3.connect(DB)
    cur = con.execute("SELECT name, field, event_date, event_type, description, mahadasha_lord, antardasha_lord FROM life_events_dasha")
    rows = cur.fetchall()

    by_maha = Counter(r[5] for r in rows)
    by_maha_type = defaultdict(Counter)
    for r in rows:
        by_maha_type[r[5]][r[3]] += 1

    total = len(rows)

    lines = []
    lines.append("# Graha / Mahadasha Life-Event Synthesis Report\n")
    lines.append(f"""**Sample**: {total} real, web-sourced, dated career/life milestones across 53
highly-documented public figures (spanning ACTOR, ARTIST_DIRECTOR, ATHLETE, AUTHOR,
BUSINESS, MUSICIAN, SCIENTIST, SCIENTIST/leadership figures), mapped to the Mahadasha/Antardasha
period mechanically computed to be active on each event's real date (birth-progressed
Vimshottari walk, same method used for Trump/Modi/leaders elsewhere in this project).

**What this is NOT**: a validated predictive model. This project's own blind backtest
(ASTROWATCH-BT-001, 519 real historical events) found no statistically significant
predictive edge (permutation p=1.0). {total} events across 53 people, chosen for how
well-documented their timelines are (not randomly sampled), is far too small and too
selectively chosen to establish anything statistically. Treat every frequency below as
a description of THIS SAMPLE, not a law of astrology.

**What this IS**: a transparent, honestly-computed frequency count, combined with the
classical (textually well-established, non-controversial) significations each graha
carries in Vedic astrology -- offered as raw material for further research, not as a
finished predictive claim.

## 1. Event count by Mahadasha lord (this sample)

| Mahadasha lord | Events in this sample | Classical signification |
|---|---|---|
""")
    for lord, _years in [("ketu",7),("venus",20),("sun",6),("moon",10),("mars",7),("rahu",18),("jupiter",16),("saturn",19),("mercury",17)]:
        n = by_maha.get(lord, 0)
        lines.append(f"| {lord} | {n} | {GRAHA_THEME[lord]} |")

    lines.append("\n## 2. Event type breakdown per Mahadasha lord (raw counts, this sample only)\n")
    lines.append("| Mahadasha lord | " + " | ".join(sorted(ALL_TYPES_SET)) + " |")
    lines.append("|---" * (1 + len(ALL_TYPES_SET)) + "|")
    all_types = sorted(ALL_TYPES_SET)
    for lord in sorted(by_maha_type, key=lambda l: -by_maha.get(l, 0)):
        row = [lord] + [str(by_maha_type[lord].get(t, 0)) for t in all_types]
        lines.append("| " + " | ".join(row) + " |")

    pos = sum(1 for r in rows if r[3] in POSITIVE_TYPES)
    neg = sum(1 for r in rows if r[3] in NEGATIVE_TYPES)
    neu = sum(1 for r in rows if r[3] in NEUTRAL_TYPES)
    lines.append(f"\n**Overall in this sample**: {pos}/{total} events tagged as career-positive "
                 f"(breakthrough/award/record/comeback/marriage), {neg}/{total} tagged as "
                 f"career-negative-or-transitional (controversy/retirement/divorce/tragedy/death), "
                 f"{neu}/{total} tagged as neutral financial/business milestones (a deal or sale, "
                 f"not inherently positive or negative). This roughly reflects that these are famous, "
                 f"successful people -- not a claim about any particular graha.\n")

    lines.append("## 3. Per-person timeline (real dates, real sourced events, real computed dasha)\n")
    by_person = defaultdict(list)
    for r in rows:
        by_person[r[0]].append(r)
    for name in sorted(by_person):
        lines.append(f"\n### {name} ({by_person[name][0][1]})\n")
        lines.append("| Date | Event | Mahadasha | Antardasha |")
        lines.append("|---|---|---|---|")
        for r in sorted(by_person[name], key=lambda x: x[2]):
            lines.append(f"| {r[2]} | {r[3]}: {r[4]} | {r[5]} | {r[6]} |")

    lines.append("""

## 4. Honest caveats

1. **Selection bias**: these 53 people were chosen because their career timelines are
   unusually well-documented, not at random. Extremely well-documented lives cluster
   in certain eras/countries/fields, which could itself correlate with dasha patterns
   for reasons that have nothing to do with astrology (e.g. birth-year distribution).
2. **Long Mahadashas dominate short samples**: Venus (20y) and Saturn (19y) mahadashas
   are mechanically more likely to contain *any* given event than Sun (6y) or Mars (7y)
   mahadashas, purely from being longer. Raw event counts by mahadasha lord are NOT
   base-rate-adjusted in the table above -- read them as descriptive, not comparative,
   until normalized by each lord's share of total lifetime-years in this sample.
3. **A single person's whole documented career can fall inside one Mahadasha**: e.g.
   Marilyn Monroe's entire 1953-1962 timeline sits inside one Jupiter Mahadasha, so
   her data only shows Antardasha-level (not Mahadasha-level) variation. This is a
   real, honestly-reported limitation of using famous adults' most-documented years,
   which often cluster inside a single ~15-20 year Mahadasha.
4. This report should be read alongside `FAMOUS_PEOPLE_PATTERN_REPORT.md` (the
   mechanical natal-mahadasha-vs-field frequency count across the full 674-person
   corpus, since expanded from the original 501) and `MASS_KUNDLI_CORRELATION_REPORT.md` (519 real historical events) --
   none of the three found or claim a validated predictive signal.
""")

    with open(OUT_MD, "w") as f:
        f.write("\n".join(lines))
    print("wrote", OUT_MD)


if __name__ == "__main__":
    main()
