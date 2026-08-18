#!/usr/bin/env python3
"""
Astrowatch -- pattern report for famous_people_kundli.db (459 charts, 7 fields).
Same exploratory/unvalidated methodology and caveat style as every other pattern
report in this project.
"""
import os
import sqlite3
from collections import defaultdict, Counter

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(THIS_DIR, "famous_people_kundli.db")
OUT_PATH = os.path.join(THIS_DIR, "FAMOUS_PEOPLE_PATTERN_REPORT.md")


def load():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM famous_people WHERE status='COMPUTED'").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def correlate(rows, feature_key):
    table = defaultdict(lambda: defaultdict(int))
    for r in rows:
        table[r[feature_key]][r["field"]] += 1
    return table


def main():
    rows = load()
    doc = [r for r in rows if r["birth_time_source"] == "DOCUMENTED"]
    lines = [
        "# Famous People Kundli/Mahadasha Pattern Report (459 charts, exploratory, UNVALIDATED)",
        "",
        f"Built from `famous_people_kundli.db`. {len(rows)} charted across 7 fields. "
        f"Only {len(doc)} of {len(rows)} have a DOCUMENTED (credibly-sourced) birth "
        f"time -- the rest use ASSUMED_NOON. **Ascendant/house results below should "
        f"only be trusted for the DOCUMENTED subset; Moon Rasi/Nakshatra and "
        f"Mahadasha lord are usable across the full set.**",
        "",
        "## Sample composition",
        "",
    ]
    base = Counter(r["field"] for r in rows)
    for field, n in base.most_common():
        lines.append(f"- {field}: {n}")
    lines.append("")

    lines.append("## Ascendant Rasi frequency by field (DOCUMENTED birth times only, n=" + str(len(doc)) + ")")
    lines.append("")
    table = correlate(doc, "ascendant_rashi")
    lines.append("| Ascendant | n | " + " | ".join(sorted(base.keys())) + " |")
    lines.append("|---|---|" + "---|" * len(base))
    for value, counts in sorted(table.items(), key=lambda kv: -sum(kv[1].values())):
        total = sum(counts.values())
        cells = " | ".join(str(counts.get(f, 0)) for f in sorted(base.keys()))
        lines.append(f"| {value} | {total} | {cells} |")
    lines.append("")

    lines.append("## Moon Rasi frequency by field (all 459)")
    lines.append("")
    table = correlate(rows, "moon_rashi")
    lines.append("| Moon Rasi | n | " + " | ".join(sorted(base.keys())) + " |")
    lines.append("|---|---|" + "---|" * len(base))
    for value, counts in sorted(table.items(), key=lambda kv: -sum(kv[1].values())):
        total = sum(counts.values())
        cells = " | ".join(str(counts.get(f, 0)) for f in sorted(base.keys()))
        lines.append(f"| {value} | {total} | {cells} |")
    lines.append("")

    lines.append("## Natal Mahadasha lord frequency by field (all 459)")
    lines.append("")
    table = correlate(rows, "natal_mahadasha_lord")
    lines.append("| Mahadasha lord | n | " + " | ".join(sorted(base.keys())) + " |")
    lines.append("|---|---|" + "---|" * len(base))
    for value, counts in sorted(table.items(), key=lambda kv: -sum(kv[1].values())):
        total = sum(counts.values())
        cells = " | ".join(str(counts.get(f, 0)) for f in sorted(base.keys()))
        lines.append(f"| {value} | {total} | {cells} |")
    lines.append("")

    # Field with highest share of each mahadasha lord, as a simple "headline" scan
    lines.append("## Simple headline reads (still unvalidated -- see caveats)")
    lines.append("")
    for field in sorted(base.keys()):
        field_rows = [r for r in rows if r["field"] == field]
        top_moon = Counter(r["moon_rashi"] for r in field_rows).most_common(1)[0]
        top_maha = Counter(r["natal_mahadasha_lord"] for r in field_rows).most_common(1)[0]
        lines.append(f"- **{field}** (n={len(field_rows)}): most common Moon Rasi = "
                      f"{top_moon[0]} ({top_moon[1]}/{len(field_rows)}); most common "
                      f"natal Mahadasha lord = {top_maha[0]} ({top_maha[1]}/{len(field_rows)})")
    lines.append("")

    lines.append("## Caveats")
    lines.append("")
    lines.append(
        "- Sample is curated from general biographical knowledge, not individually "
        "re-verified live at this volume (a couple of very recent honorees were "
        "spot-checked live this session)."
    )
    lines.append(
        "- 447 of 459 (97%) use ASSUMED_NOON -- Ascendant/house results are only "
        "meaningful for the small DOCUMENTED subset."
    )
    lines.append(
        "- No held-out set, no significance testing, no multiple-comparison "
        "correction -- consistent with every other exploratory report in this "
        "project. With 7 fields x a dozen+ Rasi/lord values, many cells will look "
        "'notable' by chance alone at this sample size."
    )
    lines.append(
        "- Fields are unevenly sampled (Athletes and Scientists are larger than "
        "Artists/Directors, for instance) -- frequency differences may just reflect "
        "sample size, not any real astrological effect."
    )

    with open(OUT_PATH, "w") as f:
        f.write("\n".join(lines))
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
