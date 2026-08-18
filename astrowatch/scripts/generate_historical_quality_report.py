#!/usr/bin/env python3
"""Astrowatch — generate HISTORICAL_DATA_QUALITY_REPORT.md from the actual database.
Every number below is a live query result -- nothing here is typed by hand."""
import argparse
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from historical import database  # noqa: E402


def decade(year: int) -> str:
    return f"{(year // 10) * 10}s"


def _ordinal(n: int) -> str:
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def century(year: int) -> str:
    # real bug found by test_century_bucketing on first execution: the original
    # f"{c}th century" hardcoded "th" for every century, giving "21th century"
    # instead of "21st century" -- fixed with a proper ordinal-suffix helper.
    c = year // 100 + 1
    return f"{_ordinal(c)} century" if year >= 0 else "pre-1st century"


def period_bucket(year: int) -> str:
    if year < 500:
        return "Ancient (pre-500 CE)"
    if year < 1500:
        return "Medieval (500-1499)"
    if year < 1800:
        return "Early modern (1500-1799)"
    if year < 1900:
        return "19th century"
    if year < 2000:
        return "20th century"
    return "21st century"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--db", default="historical_events.db")
    p.add_argument("--out", default="HISTORICAL_DATA_QUALITY_REPORT.md")
    p.add_argument("--dataset-version", default=None)
    args = p.parse_args()

    conn = database.connect(args.db)
    events = [dict(r) for r in conn.execute("SELECT * FROM events").fetchall()]
    if args.dataset_version:
        events = [e for e in events if e["dataset_version"] == args.dataset_version]
    total = len(events)

    by_type = Counter(e["event_type"] for e in events)
    by_subtype = Counter(e["event_subtype"] for e in events)
    by_region = Counter(e["region"] or "(unspecified)" for e in events)
    by_country = Counter(e["country_code"] or "(unspecified)" for e in events)
    by_decade = Counter(decade(int(e["start_date"][:4])) for e in events)
    by_century = Counter(century(int(e["start_date"][:4])) for e in events)
    by_period = Counter(period_bucket(int(e["start_date"][:4])) for e in events)
    by_tier = Counter(e["source_quality_tier"] for e in events)
    by_verification = Counter(e["verification_status"] for e in events)
    by_date_conf = Counter(e["date_confidence"] for e in events)
    by_time_conf = Counter(e["time_confidence"] for e in events)
    by_loc_conf = Counter(e["location_confidence"] for e in events)

    verified_statuses = {"SINGLE_SOURCE", "MULTI_SOURCE_CONFIRMED"}
    verified = sum(1 for e in events if e["verification_status"] in verified_statuses)
    unverified = by_verification.get("UNVERIFIED", 0)
    disputed = by_verification.get("DISPUTED", 0)

    exact_dates = by_date_conf.get("EXACT", 0)
    approx_dates = by_date_conf.get("APPROXIMATE", 0)
    disputed_dates = by_date_conf.get("DISPUTED", 0)
    range_dates = by_date_conf.get("DATE_RANGE", 0)
    unknown_dates = by_date_conf.get("UNKNOWN", 0)

    unknown_time = by_time_conf.get("UNKNOWN", 0)
    exact_time = by_time_conf.get("EXACT", 0)
    approx_time = by_time_conf.get("APPROXIMATE", 0)

    exact_loc = by_loc_conf.get("EXACT", 0)
    approx_loc = by_loc_conf.get("APPROXIMATE", 0)

    source_counts = {}
    for e in events:
        n = conn.execute(
            "SELECT COUNT(*) FROM event_sources WHERE event_id = ?", (e["event_id"],)
        ).fetchone()[0]
        source_counts[e["event_id"]] = n
    single_source = sum(1 for n in source_counts.values() if n == 1)
    multi_source = sum(1 for n in source_counts.values() if n >= 2)
    zero_source = sum(1 for n in source_counts.values() if n == 0)

    n_sources_total = conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
    n_manual_review = 0
    n_duplicate_candidates = 0
    if os.path.exists("manual_review.csv"):
        with open("manual_review.csv") as f:
            rows = list(f)[1:]
            n_manual_review = len(rows)
            n_duplicate_candidates = sum(1 for r in rows if "possible duplicate" in r)

    conn.close()

    def fmt_counter(c: Counter) -> str:
        return "\n".join(f"- {k}: {v}" for k, v in sorted(c.items(), key=lambda x: -x[1]))

    version_label = args.dataset_version or "(all versions in this database)"

    report = f"""# Astrowatch — Historical Data Quality Report

Generated directly from `{args.db}` (dataset_version: {version_label}) by
`scripts/generate_historical_quality_report.py`. Every figure below is a live
query result against the actual database as it exists right now -- none of it is
typed by hand or estimated.

## Headline numbers

- Total events: **{total}**
- Verified events (SINGLE_SOURCE or MULTI_SOURCE_CONFIRMED): **{verified}**
- Unverified events: **{unverified}**
- Disputed events (verification_status=DISPUTED, i.e. sources actually checked this
  session disagreed): **{disputed}**
- Events with DISPUTED date_confidence specifically (a source WAS found, but the
  exact date it gives conflicts with another real source -- see "Date confidence"
  below and manual_review.csv): **{disputed_dates}**
- Total distinct sources: **{n_sources_total}**
- Manual review queue entries: **{n_manual_review}** (of which {n_duplicate_candidates} are
  duplicate-candidate flags; see `manual_review.csv`)

**Still far below the 500-2,000 event target from the original spec, and now
explicitly NOT chasing that number** -- the operating principle for this pass was
"verified 100 events > unverified 1,000 events." Quality/evidence over quantity.

## Verification status distribution

{fmt_counter(by_verification)}

## Events by category

{fmt_counter(by_type)}

## Events by subtype

{fmt_counter(by_subtype)}

## Events by region

{fmt_counter(by_region)}

## Events by country code

{fmt_counter(by_country)}

## Events by decade

{fmt_counter(by_decade)}

## Events by century

{fmt_counter(by_century)}

## Events by broad historical period

{fmt_counter(by_period)}

## Source-quality tier distribution

- Tier 1 (primary/official): **{by_tier.get(1, 0)}**
- Tier 2 (academic/structured): **{by_tier.get(2, 0)}**
- Tier 3 (high-quality secondary): **{by_tier.get(3, 0)}**
- Tier 4 (discovery-only/uncited): **{by_tier.get(4, 0)}**

## Date confidence

- EXACT: **{exact_dates}**
- APPROXIMATE: **{approx_dates}**
- DATE_RANGE: **{range_dates}**
- DISPUTED: **{disputed_dates}**
- UNKNOWN: **{unknown_dates}**

## Time confidence

- EXACT: **{exact_time}**
- APPROXIMATE: **{approx_time}**
- UNKNOWN: **{unknown_time}**

## Location confidence

- EXACT: **{exact_loc}**
- APPROXIMATE: **{approx_loc}**
- (full breakdown: {dict(by_loc_conf)})

## Source count per event

- Single-source events: **{single_source}**
- Multi-source events (2+ sources actually linked): **{multi_source}**
- Zero-source events: **{zero_source}** (should always be 0 -- `validate_historical_db.py`'s
  `missing_provenance` check fails the whole run otherwise)

## Duplicate candidates

**{n_duplicate_candidates}** flagged by `historical/deduplication.py`'s scan this pass
(broader signal set than the original pass — see that module's docstring: normalized
name, fuzzy name similarity, source_record_id, country/region/location, subtype,
date proximity/range overlap, description overlap).

## Known limitations (stated plainly)

1. **Scale**: {total} events, not 500-2,000 -- an explicit, instructed trade-off
   favoring verification quality over raw count this pass.
2. **{unverified} events remain UNVERIFIED** ({round(100*unverified/total) if total else 0}%):
   general historical reference knowledge, not independently re-checked against a
   specific live source. See `data/curated_events.py` and, for this pass's
   upgrades, `data/verification_updates.py`.
3. **Geographic/temporal concentration** persists despite deliberate effort toward
   Asia, Africa, Latin America, and the Middle East.
4. **Real machine-precision date/time/location** exists only for USGS earthquake
   and NOAA tsunami events (Tier 1). Nearly everything else has time_confidence
   UNKNOWN/APPROXIMATE and no coordinates, by design (never fabricated).
5. **UCDP and ACLED remain unreachable/inaccessible this pass** (network-blocked
   and API-key-gated respectively); NOAA (tsunamis + significant earthquakes),
   World Bank, and WHO GHO APIs were newly confirmed reachable via `web_fetch`
   this pass, but only NOAA's tsunami data was actually integrated as discrete
   historical events -- World Bank/WHO are indicator time series, not
   event-structured, and were not force-fit into this schema.
6. **Deduplication is heuristic, not exhaustive.**
"""

    with open(args.out, "w") as f:
        f.write(report)
    print(f"wrote {args.out} ({len(report)} chars) from {total} real events in {args.db} "
          f"(dataset_version={version_label})")


if __name__ == "__main__":
    main()
