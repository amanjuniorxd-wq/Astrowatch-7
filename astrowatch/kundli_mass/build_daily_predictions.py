#!/usr/bin/env python3
"""
Astrowatch -- generates a precomputed table of "daily astrological calculation"
content for a private (not published) web-app artifact, per explicit user request
for "a web app or bot that gives out 2 random predictions everyday."

SCOPE / SAFETY NOTES (read before extending this):
- This is NOT a public-posting bot. Output is a static JSON file consumed by a
  self-contained HTML artifact the user opens themselves -- nothing here posts to
  any public platform, automatically or otherwise.
- 5 categories, each grounded in REAL computed chart data (no fabricated numbers):
  1. US politics    -- Donald Trump's birth-progressed Mahadasha/Antardasha
  2. Indian politics -- Narendra Modi's birth-progressed Mahadasha/Antardasha
  3. Global politics -- location-independent (Moon/Sun/dasha-only, no Ascendant)
     resonance against the 519-event kundli_mass POLITICAL table
  4. Global economy  -- same mechanism, ECONOMIC table. Deliberately NOT a market-
     direction call (no "will rise/fall") -- themes only, per this project's
     standing avoidance of unqualified financial-advice-style output.
  5. Sports          -- rotates through athlete natal charts (famous_people_kundli),
     entertainment framing only, no odds/percentages/betting language.
- Every entry carries the same disclaimer used throughout kundli_mass/: astrological
  calculation, not a forecast, not validated (BT-001 found no predictive edge).
- Window: today through +400 days. Mahadasha/Antardasha segments and weekly
  resonance snapshots are cheap to compute at this range; re-run this script to
  extend the window later if needed.
"""
import json
import os
import sys
import sqlite3
from datetime import datetime, timedelta, timezone as dt_timezone
from collections import defaultdict

ASTROWATCH_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ASTROWATCH_DIR)
import coordinates
from kundli import compute_kundli
from mahadasha import (compute_dasha_state, DASHA_SEQUENCE, _lord_index,
                        _compute_antardasha, DashaPeriod, _SIDEREAL_YEAR_DAYS)

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, THIS_DIR)
from leaders_corpus import LEADERS
from famous_people_corpus import PEOPLE
from nations_corpus import NATIONS

OUT_PATH = os.path.join(THIS_DIR, "daily_predictions_data.json")

# --- Extension (added this pass): 5 more fields, feeding the new nations +
# chart-archetype data built this session into the same prediction mechanism. ---
WORLD_LEADER_NAMES = [
    "Vladimir Putin", "Xi Jinping", "Emmanuel Macron", "Andy Burnham",
    "Friedrich Merz", "Benjamin Netanyahu", "Volodymyr Zelenskyy",
    "Luiz Inacio Lula da Silva",
]
NATION_POOL_NAMES = [
    "United States", "India", "China", "Russia", "United Kingdom", "France",
    "Germany", "Japan", "Brazil", "South Africa", "Nigeria", "Egypt", "Israel",
    "Ukraine", "Pakistan", "Indonesia", "Mexico", "Canada", "Australia", "South Korea",
]

DISCLAIMER = ("Astrological calculation, not a forecast. Unvalidated pattern-based "
              "reading; Astrowatch's own backtest (BT-001) found no real predictive "
              "edge. Not to be relied on for real decisions.")

GRAHA_THEME = {
    "sun": "authority, visibility and executive action",
    "moon": "public mood and emotional currents",
    "mars": "conflict, assertiveness and sudden action",
    "mercury": "communication, negotiation and information flow",
    "jupiter": "law, expansion and institutional matters",
    "venus": "diplomacy, trade and alliances",
    "saturn": "delay, restriction and structural pressure",
    "rahu": "disruption, ambition and unconventional moves",
    "ketu": "withdrawal, loose ends and quiet transitions",
}

WINDOW_DAYS = 400
TODAY = datetime.now(dt_timezone.utc).date()


def _birth_jd_and_moon(name, date, time, tz):
    from zoneinfo import ZoneInfo
    y, m, d = (int(x) for x in date.split("-"))
    hh, mm = (int(x) for x in time.split(":")) if time else (12, 0)
    local_dt = datetime(y, m, d, hh, mm, tzinfo=ZoneInfo(tz))
    utc_dt = local_dt.astimezone(dt_timezone.utc)
    jd = coordinates.julian_day(utc_dt.year, utc_dt.month, utc_dt.day,
                                 utc_dt.hour + utc_dt.minute / 60.0)
    return jd


def _leader_lookup(name):
    for L in LEADERS:
        if L[0] == name:
            return L
    raise KeyError(name)


def leader_dasha_segments(name, lat, lon, window_start_jd, window_end_jd):
    """Real birth-progressed Mahadasha walk (same method as build_leaders_kundli.py),
    returning the Mahadasha/Antardasha segment(s) overlapping the window."""
    L = _leader_lookup(name)
    _, bdate, btime, btz, country, blat, blon, group, tstart, tyears, reel, reason = L
    birth_jd = _birth_jd_and_moon(name, bdate, btime, btz)
    chart = compute_kundli(birth_jd, blat, blon)
    natal_moon_lon = chart.grahas["moon"].sidereal_lon_deg
    birth_dasha = compute_dasha_state(birth_jd, natal_moon_lon)

    cursor = birth_dasha.mahadasha
    idx = _lord_index(cursor.lord)
    segments = []
    # advance to at least window_start
    while cursor.end_jd_ut < window_start_jd:
        idx = (idx + 1) % 9
        lord, years = DASHA_SEQUENCE[idx]
        start = cursor.end_jd_ut
        end = start + years * _SIDEREAL_YEAR_DAYS
        cursor = DashaPeriod(lord=lord, start_jd_ut=start, end_jd_ut=end, level="mahadasha")
    while cursor.start_jd_ut < window_end_jd:
        # walk antardasha sub-segments within this mahadasha for the window
        maha_lord_years = DASHA_SEQUENCE[idx][1]
        sub_cursor = cursor.start_jd_ut
        for offset in range(9):
            sub_idx = (idx + offset) % 9
            sub_lord, sub_lord_years = DASHA_SEQUENCE[sub_idx]
            sub_dur = (sub_lord_years * maha_lord_years / 120.0) * _SIDEREAL_YEAR_DAYS
            sub_end = sub_cursor + sub_dur
            if sub_end > window_start_jd and sub_cursor < window_end_jd:
                segments.append({
                    "start_jd": max(sub_cursor, window_start_jd),
                    "end_jd": min(sub_end, window_end_jd),
                    "mahadasha_lord": cursor.lord, "antardasha_lord": sub_lord,
                })
            sub_cursor = sub_end
            if sub_cursor >= window_end_jd:
                break
        idx = (idx + 1) % 9
        lord, years = DASHA_SEQUENCE[idx]
        start = cursor.end_jd_ut
        end = start + years * _SIDEREAL_YEAR_DAYS
        cursor = DashaPeriod(lord=lord, start_jd_ut=start, end_jd_ut=end, level="mahadasha")
    return segments


def jd_for_date(dt_date):
    return coordinates.julian_day(dt_date.year, dt_date.month, dt_date.day, 12.0)


def load_mass_correlate_tables():
    conn = sqlite3.connect(os.path.join(THIS_DIR, "kundli_mass.db"))
    conn.row_factory = sqlite3.Row
    rows = [dict(r) for r in conn.execute(
        "SELECT category, mahadasha_lord, antardasha_lord, moon_rashi, moon_nakshatra, "
        "sun_rashi FROM mass_events WHERE status='COMPUTED'")]
    conn.close()
    tables = {}
    for fk in ("mahadasha_lord", "antardasha_lord", "moon_rashi", "moon_nakshatra", "sun_rashi"):
        t = defaultdict(lambda: defaultdict(int))
        for r in rows:
            t[r[fk]][r["category"]] += 1
        tables[fk] = t
    return tables


def global_resonance_for_day(dt_date, tables, category):
    """Location-independent (no Ascendant) resonance -- uses a fixed neutral
    reference point ONLY for the astronomical calc's longitude parameter (which
    doesn't affect Moon/Sun/dasha, only would affect Ascendant, which we don't use
    here) -- 0,0 is fine since we discard house/ascendant output entirely."""
    jd = jd_for_date(dt_date)
    chart = compute_kundli(jd, 0.0, 0.0)
    dasha = compute_dasha_state(jd, chart.grahas["moon"].sidereal_lon_deg)
    features = {
        "mahadasha_lord": dasha.mahadasha.lord, "antardasha_lord": dasha.antardasha.lord,
        "moon_rashi": chart.grahas["moon"].rashi.rashi_name,
        "moon_nakshatra": chart.grahas["moon"].nakshatra.nakshatra_name,
        "sun_rashi": chart.grahas["sun"].rashi.rashi_name,
    }
    score = 0
    for fk, val in features.items():
        score += tables[fk].get(val, {}).get(category, 0)
    return features, score


def nation_segments_from_db(name, window_start_date, window_end_date):
    """Reads pre-computed segments straight from nations_lifetime_dasha.db (built
    this session by build_nations_lifetime_dasha.py) rather than recomputing --
    avoids re-deriving the multi-cycle-aware walk here."""
    conn = sqlite3.connect(os.path.join(THIS_DIR, "nations_lifetime_dasha.db"))
    rows = conn.execute(
        "SELECT antar_start_date, antar_end_date, mahadasha_lord, antardasha_lord "
        "FROM lifetime_dasha WHERE name=? AND antar_end_date>=? AND antar_start_date<=? "
        "ORDER BY mahadasha_index, antardasha_index",
        (name, window_start_date, window_end_date),
    ).fetchall()
    conn.close()
    return [{"start": r[0], "end": r[1], "mahadasha_lord": r[2], "antardasha_lord": r[3]} for r in rows]


def nations_pattern_ratios():
    """Base-rate-normalized Mahadasha-lord ratios from the real 74-event/27-nation
    sample this session built (NATIONS_MAHADASHA_PATTERN_REPORT.md) -- computed
    fresh from the mapping database, not hardcoded, so it stays in sync if that
    database is ever regenerated with more events."""
    BASE_YEARS = {"ketu": 7, "venus": 20, "sun": 6, "moon": 10, "mars": 7,
                  "rahu": 18, "jupiter": 16, "saturn": 19, "mercury": 17}
    total = sum(BASE_YEARS.values())
    conn = sqlite3.connect(os.path.join(THIS_DIR, "nations_events_dasha_mapping.db"))
    rows = conn.execute("SELECT mahadasha_lord FROM nations_events_dasha").fetchall()
    conn.close()
    n = len(rows)
    counts = defaultdict(int)
    for (lord,) in rows:
        counts[lord] += 1
    ratios = {}
    for lord, base_years in BASE_YEARS.items():
        obs_pct = counts.get(lord, 0) / n * 100 if n else 0
        base_pct = base_years / total * 100
        ratios[lord] = round(obs_pct / base_pct, 2) if base_pct else None
    return ratios


def archetype_ratios_by_field():
    """Base-rate-normalized natal-Mahadasha-lord ratios per career field, from
    FAMOUS_PEOPLE_CHART_ARCHETYPE_REPORT.md's method, computed fresh from
    famous_people_kundli.db (all 673 computed people)."""
    BASE_YEARS = {"ketu": 7, "venus": 20, "sun": 6, "moon": 10, "mars": 7,
                  "rahu": 18, "jupiter": 16, "saturn": 19, "mercury": 17}
    total = sum(BASE_YEARS.values())
    conn = sqlite3.connect(os.path.join(THIS_DIR, "famous_people_kundli.db"))
    rows = conn.execute(
        "SELECT field, natal_mahadasha_lord FROM famous_people WHERE status='COMPUTED'"
    ).fetchall()
    conn.close()
    by_field = defaultdict(lambda: defaultdict(int))
    n_by_field = defaultdict(int)
    for field, lord in rows:
        by_field[field][lord] += 1
        n_by_field[field] += 1
    out = {}
    for field, counts in by_field.items():
        n = n_by_field[field]
        out[field] = {}
        for lord, base_years in BASE_YEARS.items():
            obs_pct = counts.get(lord, 0) / n * 100 if n else 0
            base_pct = base_years / total * 100
            out[field][lord] = round(obs_pct / base_pct, 2) if base_pct else None
    return out


def field_pool(field_name):
    conn = sqlite3.connect(os.path.join(THIS_DIR, "famous_people_kundli.db"))
    rows = conn.execute(
        "SELECT name, natal_mahadasha_lord FROM famous_people WHERE field=? AND status='COMPUTED'",
        (field_name,),
    ).fetchall()
    conn.close()
    return [{"name": r[0], "natal_mahadasha_lord": r[1], "field": field_name} for r in rows]


def build():
    window_start_jd = jd_for_date(TODAY)
    window_end_jd = jd_for_date(TODAY + timedelta(days=WINDOW_DAYS))

    print("Computing Trump segments...")
    trump_segs = leader_dasha_segments("Donald Trump", 40.70, -73.79, window_start_jd, window_end_jd)
    print("Computing Modi segments...")
    modi_segs = leader_dasha_segments("Narendra Modi", 23.78, 72.64, window_start_jd, window_end_jd)

    print("Loading mass correlation tables...")
    tables = load_mass_correlate_tables()

    print("Computing weekly global resonance (political/economic)...")
    weekly = []
    d = TODAY
    while d <= TODAY + timedelta(days=WINDOW_DAYS):
        pol_feat, pol_score = global_resonance_for_day(d, tables, "POLITICAL")
        econ_feat, econ_score = global_resonance_for_day(d, tables, "ECONOMIC")
        weekly.append({
            "date": d.isoformat(),
            "political": {"features": pol_feat, "score": pol_score},
            "economic": {"features": econ_feat, "score": econ_score},
        })
        d += timedelta(days=7)

    athletes = [p for p in PEOPLE if p[7] == "ATHLETE"]
    _athlete_maha = {}
    _conn = sqlite3.connect(os.path.join(THIS_DIR, "famous_people_kundli.db"))
    for _name, _lord in _conn.execute(
        "SELECT name, natal_mahadasha_lord FROM famous_people WHERE field='ATHLETE' AND status='COMPUTED'"
    ):
        _athlete_maha[_name] = _lord
    _conn.close()

    def jd_to_date(jd):
        import swisseph as swe
        y, m, dd, h = swe.revjul(jd)
        return datetime(y, m, dd).date().isoformat()

    print("Computing world-leader segments (8 current leaders)...")
    world_leader_segments = {}
    for name in WORLD_LEADER_NAMES:
        L = _leader_lookup(name)
        _, bdate, btime, btz, country, blat, blon, group, tstart, tyears, reel, reason = L
        segs = leader_dasha_segments(name, blat, blon, window_start_jd, window_end_jd)
        world_leader_segments[name] = [
            {"start": jd_to_date(s["start_jd"]), "end": jd_to_date(s["end_jd"]),
             "mahadasha_lord": s["mahadasha_lord"], "antardasha_lord": s["antardasha_lord"]}
            for s in segs
        ]

    print("Reading nation segments from nations_lifetime_dasha.db...")
    window_start_date_str = TODAY.isoformat()
    window_end_date_str = (TODAY + timedelta(days=WINDOW_DAYS)).isoformat()
    nation_segments = {
        name: nation_segments_from_db(name, window_start_date_str, window_end_date_str)
        for name in NATION_POOL_NAMES
    }

    print("Computing nations pattern ratios (from real 74-event mapping)...")
    nat_ratios = nations_pattern_ratios()

    print("Computing archetype ratios by field (from full 673-person corpus)...")
    arch_ratios = archetype_ratios_by_field()

    print("Building business/science/entertainment pools...")
    business_pool = field_pool("BUSINESS")
    science_pool = field_pool("SCIENTIST")
    entertainment_pool = (field_pool("ACTOR") + field_pool("MUSICIAN")
                           + field_pool("ARTIST_DIRECTOR"))

    data = {
        "generated_for_window_start": TODAY.isoformat(),
        "generated_for_window_end": (TODAY + timedelta(days=WINDOW_DAYS)).isoformat(),
        "disclaimer": DISCLAIMER,
        "graha_theme": GRAHA_THEME,
        "trump_segments": [
            {"start": jd_to_date(s["start_jd"]), "end": jd_to_date(s["end_jd"]),
             "mahadasha_lord": s["mahadasha_lord"], "antardasha_lord": s["antardasha_lord"]}
            for s in trump_segs
        ],
        "modi_segments": [
            {"start": jd_to_date(s["start_jd"]), "end": jd_to_date(s["end_jd"]),
             "mahadasha_lord": s["mahadasha_lord"], "antardasha_lord": s["antardasha_lord"]}
            for s in modi_segs
        ],
        "weekly_global_resonance": weekly,
        "athlete_pool": [{"name": a[0], "sport": a[8], "natal_mahadasha_lord": _athlete_maha.get(a[0])} for a in athletes if a[0] in _athlete_maha],
        "world_leader_segments": world_leader_segments,
        "nation_segments": nation_segments,
        "nations_pattern_ratios": nat_ratios,
        "archetype_ratios_by_field": arch_ratios,
        "business_pool": business_pool,
        "science_pool": science_pool,
        "entertainment_pool": entertainment_pool,
    }
    with open(OUT_PATH, "w") as f:
        json.dump(data, f, indent=1)
    print(f"Wrote {OUT_PATH}")
    print(f"trump segments: {len(trump_segs)}, modi segments: {len(modi_segs)}, "
          f"weekly points: {len(weekly)}, athlete pool: {len(athletes)}, "
          f"world leaders: {len(world_leader_segments)}, nations: {len(nation_segments)}, "
          f"business_pool: {len(business_pool)}, science_pool: {len(science_pool)}, "
          f"entertainment_pool: {len(entertainment_pool)}")


if __name__ == "__main__":
    build()
