# Astrowatch — Historical Data Quality Report

Generated directly from `historical_events.db` (dataset_version: ASTROWATCH-HIST-001) by
`scripts/generate_historical_quality_report.py`. Every figure below is a live
query result against the actual database as it exists right now -- none of it is
typed by hand or estimated.

## Headline numbers

- Total events: **136**
- Verified events (SINGLE_SOURCE or MULTI_SOURCE_CONFIRMED): **19**
- Unverified events: **117**
- Disputed events (verification_status=DISPUTED, i.e. sources actually checked this
  session disagreed): **0**
- Events with DISPUTED date_confidence specifically (a source WAS found, but the
  exact date it gives conflicts with another real source -- see "Date confidence"
  below and manual_review.csv): **3**
- Total distinct sources: **5**
- Manual review queue entries: **3** (of which 0 are
  duplicate-candidate flags; see `manual_review.csv`)

**Still far below the 500-2,000 event target from the original spec, and now
explicitly NOT chasing that number** -- the operating principle for this pass was
"verified 100 events > unverified 1,000 events." Quality/evidence over quantity.

## Verification status distribution

- UNVERIFIED: 117
- SINGLE_SOURCE: 17
- MULTI_SOURCE_CONFIRMED: 2

## Events by category

- NATURAL_DISASTER: 34
- MILITARY: 25
- POLITICAL: 24
- SCIENCE_TECHNOLOGY: 20
- SOCIAL_PUBLIC_HEALTH: 18
- ECONOMIC: 15

## Events by subtype

- earthquake: 19
- invasion: 8
- assassination: 7
- war_start: 6
- nuclear_event: 6
- war_end: 5
- volcanic_eruption: 5
- civil_unrest: 5
- major_space_event: 5
- major_scientific_discovery: 5
- revolution: 4
- major_political_crisis: 4
- major_economic_policy: 4
- major_currency_event: 4
- cyclone_hurricane: 4
- epidemic: 4
- major_technology_event: 4
- major_military_crisis: 3
- independence: 3
- financial_crisis: 3
- pandemic: 3
- major_protest: 3
- major_social_movement: 3
- battle: 2
- constitutional_change: 2
- election: 2
- government_change: 2
- market_crash: 2
- tsunami: 2
- flood: 2
- wildfire: 2
- ceasefire: 1
- sovereign_default: 1
- banking_crisis: 1

## Events by region

- Asia: 30
- North America: 29
- Europe: 28
- (unspecified): 16
- Middle East: 12
- Africa: 7
- Southeast Asia: 5
- Caribbean: 4
- South America: 3
- Oceania: 1
- Extraterrestrial: 1

## Events by country code

- USA: 31
- (unspecified): 16
- CHN: 10
- GBR: 6
- JPN: 5
- DEU: 4
- FRA: 3
- ISR: 3
- BGD: 3
- UKR: 3
- EGY: 3
- ZAF: 3
- IDN: 3
- KAZ: 3
- AUT: 2
- POL: 2
- KWT: 2
- IRQ: 2
- RUS: 2
- CUB: 2
- IND: 2
- HKG: 2
- ITA: 2
- CHE: 2
- KOR: 1
- PRK: 1
- VNM: 1
- RWA: 1
- SRB: 1
- IRN: 1
- TUN: 1
- THA: 1
- GRC: 1
- ARG: 1
- SAU: 1
- VEN: 1
- ZWE: 1
- PHL: 1
- MMR: 1
- PAK: 1
- AUS: 1
- HTI: 1
- GIN: 1
- CZE: 1

## Events by decade

- 2010s: 22
- 2000s: 16
- 1990s: 15
- 1970s: 14
- 1940s: 13
- 1980s: 12
- 1960s: 11
- 1950s: 7
- 2020s: 6
- 1910s: 4
- 1900s: 3
- 1930s: 3
- 1920s: 3
- 1780s: 1
- 1770s: 1
- 1860s: 1
- 1880s: 1
- 1810s: 1
- 70s: 1
- 1340s: 1

## Events by century

- 20th century: 85
- 21st century: 44
- 19th century: 3
- 18th century: 2
- 1st century: 1
- 14th century: 1

## Events by broad historical period

- 20th century: 85
- 21st century: 44
- 19th century: 3
- Early modern (1500-1799): 2
- Ancient (pre-500 CE): 1
- Medieval (500-1499): 1

## Source-quality tier distribution

- Tier 1 (primary/official): **16**
- Tier 2 (academic/structured): **0**
- Tier 3 (high-quality secondary): **3**
- Tier 4 (discovery-only/uncited): **117**

## Date confidence

- EXACT: **123**
- APPROXIMATE: **9**
- DATE_RANGE: **1**
- DISPUTED: **3**
- UNKNOWN: **0**

## Time confidence

- EXACT: **25**
- APPROXIMATE: **8**
- UNKNOWN: **103**

## Location confidence

- EXACT: **18**
- APPROXIMATE: **0**
- (full breakdown: {'EXACT': 18, 'COUNTRY': 40, 'REGION': 23, 'CITY': 55})

## Source count per event

- Single-source events: **134**
- Multi-source events (2+ sources actually linked): **2**
- Zero-source events: **0** (should always be 0 -- `validate_historical_db.py`'s
  `missing_provenance` check fails the whole run otherwise)

## Duplicate candidates

**0** flagged by `historical/deduplication.py`'s scan this pass
(broader signal set than the original pass — see that module's docstring: normalized
name, fuzzy name similarity, source_record_id, country/region/location, subtype,
date proximity/range overlap, description overlap).

## Known limitations (stated plainly)

1. **Scale**: 136 events, not 500-2,000 -- an explicit, instructed trade-off
   favoring verification quality over raw count this pass.
2. **117 events remain UNVERIFIED** (86%):
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
