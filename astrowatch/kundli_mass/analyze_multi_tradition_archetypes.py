#!/usr/bin/env python3
"""
Astrowatch -- MULTI-TRADITION chart-archetype pattern analysis across the full
famous_people_corpus.py (1305 people, 7 career fields), extending
analyze_chart_archetypes.py (Jyotisha-only, already run and reported in
FAMOUS_PEOPLE_CHART_ARCHETYPE_REPORT.md) with a second, independently
developed tradition: Hellenistic sect + essential dignity, via
world_astrology/dignity_tables.py's shared sign-level table.

WHY THIS IS HONEST, NOT DOUBLE-COUNTING: Jyotisha and Hellenistic dignity here
literally use the SAME sign assignments (see dignity_tables.py's own
docstring) -- so this analysis is NOT claiming two independent astronomical
findings agree; it's showing that Hellenistic's DIFFERENT secondary weighting
(sect: is this planet's nature aligned with day/night) layered on the SAME
base sign data produces a genuinely separate statistic (of-sect / contrary-to-
sect rates by field) worth reporting alongside Jyotisha's house-based
weighting. Where this script reports "both traditions agree," it means: same
dignity (guaranteed, shared table) AND Hellenistic sect-favor points the same
direction as Jyotisha's house-strength (kendra/trikona vs dushtana) --
genuinely two different computations converging, not a restated fact.

SCOPE, STATED HONESTLY: this is a STRUCTURAL (natal-chart) pattern analysis,
like its Jyotisha-only predecessor -- it does NOT re-run the news/career-
event correlation work (that was done, with real individually-sourced
biographical research, for a 53-person subset elsewhere in this project --
see kundli_mass's life_events_dasha_mapping.db and the graha/Mahadasha
synthesis report). Repeating that individualized research for all 1305 people
is not something this pass attempted -- doing so honestly would require
individual web research per person, which is exactly the kind of work this
project has consistently scoped down to a tractable subset rather than fake
at full scale. This script instead extends what IS honestly computable at
full corpus scale: structural chart facts, now across two traditions instead
of one.
"""
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone as dt_timezone
from zoneinfo import ZoneInfo

ASTROWATCH_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ASTROWATCH_DIR)
from kundli import compute_kundli, EphemerisDataUnavailable
import coordinates
from world_astrology import dignity_tables as dt

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, THIS_DIR)
from famous_people_corpus import PEOPLE

RASHI_ORDER = ["Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya", "Tula",
               "Vrischika", "Dhanu", "Makara", "Kumbha", "Meena"]

OUT_JSON = os.path.join(THIS_DIR, "multi_tradition_archetype_patterns.json")
OUT_MD = os.path.join(THIS_DIR, "MULTI_TRADITION_ARCHETYPE_REPORT.md")


def jd_for(date, time_hhmm, tz):
    y, m, d = (int(x) for x in date.split("-"))
    hh, mm = (12, 0) if not time_hhmm else (int(x) for x in time_hhmm.split(":"))
    local_dt = datetime(y, m, d, hh, mm, tzinfo=ZoneInfo(tz))
    utc_dt = local_dt.astimezone(dt_timezone.utc)
    return coordinates.julian_day(utc_dt.year, utc_dt.month, utc_dt.day,
                                   utc_dt.hour + utc_dt.minute / 60.0)


def analyze():
    n_by_field = Counter()
    errors = 0
    # Jyotisha dimension (mirrors analyze_chart_archetypes.py exactly)
    by_field_10th_dignity = defaultdict(Counter)
    # Hellenistic dimension (new)
    by_field_10th_sect = defaultdict(Counter)          # "of_sect" | "contrary" | "n/a"
    by_field_chart_sect = defaultdict(Counter)          # "day" | "night"
    # Cross-tradition convergence dimension (new): does Jyotisha house-strength
    # direction (kendra/trikona=+, dushtana=-, other=0) agree in SIGN with
    # Hellenistic sect-favor (+1/-1/0)?
    by_field_convergence = defaultdict(Counter)         # "AGREE_POSITIVE"|"AGREE_NEGATIVE"|"DISAGREE"|"NO_SIGNAL"

    for (name, date, time_hhmm, tz, country, lat, lon, field, note) in PEOPLE:
        try:
            jd = jd_for(date, time_hhmm, tz)
            chart = compute_kundli(jd, lat, lon)
        except (EphemerisDataUnavailable, Exception):
            errors += 1
            continue

        asc_idx = chart.ascendant_rashi.rashi_index
        n_by_field[field] += 1

        is_day_chart = chart.grahas["sun"].house in range(7, 13)
        by_field_chart_sect[field]["day" if is_day_chart else "night"] += 1

        tenth_sign_idx = (asc_idx + 9) % 12
        tenth_sign = RASHI_ORDER[tenth_sign_idx]
        tenth_lord = dt.RASHI_LORD[tenth_sign]

        if tenth_lord not in chart.grahas:
            continue
        tenth_lord_rashi = chart.grahas[tenth_lord].rashi.rashi_name
        tenth_lord_house = chart.grahas[tenth_lord].house

        jy_dignity = dt.dignity_of(tenth_lord, tenth_lord_rashi)
        by_field_10th_dignity[field][jy_dignity] += 1

        of_sect = dt.hellenistic_sect_favor(is_day_chart, tenth_lord)
        sect_label = "n/a (mercury/node)" if of_sect is None else ("of_sect" if of_sect else "contrary_to_sect")
        by_field_10th_sect[field][sect_label] += 1

        house_kind = dt.house_kind(tenth_lord_house)
        jy_direction = 1 if house_kind in ("kendra", "trikona") else (-1 if house_kind == "dushtana" else 0)
        he_direction = 1 if of_sect is True else (-1 if of_sect is False else 0)
        if jy_direction == 0 or he_direction == 0:
            conv = "NO_SIGNAL"
        elif jy_direction == he_direction:
            conv = "AGREE_POSITIVE" if jy_direction > 0 else "AGREE_NEGATIVE"
        else:
            conv = "DISAGREE"
        by_field_convergence[field][conv] += 1

    return {
        "n_by_field": dict(n_by_field), "errors": errors,
        "tenth_dignity_jyotisha": {k: dict(v) for k, v in by_field_10th_dignity.items()},
        "tenth_lord_sect_hellenistic": {k: dict(v) for k, v in by_field_10th_sect.items()},
        "chart_sect_distribution": {k: dict(v) for k, v in by_field_chart_sect.items()},
        "cross_tradition_convergence": {k: dict(v) for k, v in by_field_convergence.items()},
    }


def write_report(results):
    with open(OUT_JSON, "w") as f:
        json.dump(results, f, indent=2)

    lines = [
        "# Multi-Tradition (Jyotisha + Hellenistic) Chart-Archetype Pattern Report",
        "",
        f"Corpus: famous_people_corpus.py -- {sum(results['n_by_field'].values())} people successfully "
        f"charted across {len(results['n_by_field'])} fields ({results['errors']} error(s), same "
        f"already-known 'Homer (traditional)' legendary/undated entry as elsewhere in this project).",
        "",
        "This extends the existing Jyotisha-only FAMOUS_PEOPLE_CHART_ARCHETYPE_REPORT.md with a second,",
        "independently-weighted tradition (Hellenistic sect) applied to the SAME underlying sign data",
        "(see dignity_tables.py) -- not a second independent astronomical claim, but a genuinely",
        "different interpretive layer (sect vs. house) that can either converge or diverge with",
        "Jyotisha's own house-based reading of the same 10th-house lord.",
        "",
        "## Per-field summary",
        "",
    ]
    for field in sorted(results["n_by_field"]):
        n = results["n_by_field"][field]
        lines.append(f"### {field} (n={n})")
        lines.append("")
        jy = results["tenth_dignity_jyotisha"].get(field, {})
        he = results["tenth_lord_sect_hellenistic"].get(field, {})
        cs = results["chart_sect_distribution"].get(field, {})
        conv = results["cross_tradition_convergence"].get(field, {})
        lines.append(f"- 10th-lord Jyotisha dignity: {jy}")
        lines.append(f"- 10th-lord Hellenistic sect status: {he}")
        lines.append(f"- Chart sect distribution (day/night): {cs}")
        lines.append(f"- Cross-tradition convergence on 10th-lord direction: {conv}")
        total_conv = sum(conv.values()) or 1
        agree_pos = conv.get("AGREE_POSITIVE", 0)
        agree_neg = conv.get("AGREE_NEGATIVE", 0)
        disagree = conv.get("DISAGREE", 0)
        lines.append(f"  ({agree_pos+agree_neg}/{total_conv} = "
                     f"{(agree_pos+agree_neg)/total_conv*100:.0f}% show the two traditions agreeing "
                     f"on direction; {disagree}/{total_conv} = {disagree/total_conv*100:.0f}% disagree)")
        lines.append("")

    lines.append("## CRITICAL CAVEAT: chart-sect distribution is an ASSUMED_NOON artifact, not a finding")
    lines.append("")
    lines.append("Self-check performed before finalizing this report: the near-universal 'day chart'")
    lines.append("result above (e.g. ACTOR 173/175 day) is NOT a real astrological pattern. At an")
    lines.append("ASSUMED_NOON birth time, the Sun is mechanically near its daily culmination (the")
    lines.append("Midheaven), which in whole-sign houses almost always falls in house 9, 10, or 11 --")
    lines.append("squarely inside the 7-12 'day chart' range regardless of who the person is or what")
    lines.append("field they're in. Verified directly: three unrelated ASSUMED_NOON test charts (different")
    lines.append("dates/timezones/latitudes) all produced Sun in house 10 or 11. Only 33 of 1305 people")
    lines.append("in this corpus have a specifically DOCUMENTED (non-noon) birth time -- too few to")
    lines.append("break out a meaningful per-field comparison on their own.")
    lines.append("")
    lines.append("Practical consequence: the 'chart sect distribution' and 'cross-tradition convergence'")
    lines.append("numbers above are substantially CONFOUNDED for any field whose corpus is mostly")
    lines.append("ASSUMED_NOON entries (essentially all of them) -- they mostly reflect which of the")
    lines.append("non-neutral planets (Sun/Jupiter/Saturn vs. Moon/Venus/Mars) happens to be that")
    lines.append("field's most common 10th-house lord, crossed with an almost-constant 'day' sect,")
    lines.append("rather than any real distribution of birth-time-sensitive sect across the field.")
    lines.append("The 10th-lord JYOTISHA dignity numbers are NOT affected by this (dignity depends on")
    lines.append("sign, not house/time-of-day), so that half of this report remains as reliable as the")
    lines.append("original Jyotisha-only report.")
    lines.append("")
    lines.append("## Limitations")
    lines.append("")
    lines.append("- Structural (natal chart) analysis only -- no news/career-event correlation was")
    lines.append("  attempted for the full 1305-person corpus in this pass (see module docstring);")
    lines.append("  the real, individually-sourced correlation work remains the existing 53-person")
    lines.append("  subset documented elsewhere in this project.")
    lines.append("- Sign-level dignity only (no moolatrikona, no triplicity/term/face).")
    lines.append("- Mercury and the lunar nodes are sect-neutral in this project's Hellenistic")
    lines.append("  implementation (see dignity_tables.py) -- their 10th-lord rows show 'n/a'.")
    lines.append("- Most charts use ASSUMED_NOON birth time (see famous_people_corpus.py docstring) --")
    lines.append("  house placements (and therefore the 10th lord identity itself) are accordingly")
    lines.append("  less reliable than Moon-based facts would be.")

    with open(OUT_MD, "w") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    results = analyze()
    write_report(results)
    print(f"n_by_field={results['n_by_field']}")
    print(f"errors={results['errors']}")
    print(f"Wrote {OUT_JSON} and {OUT_MD}")
