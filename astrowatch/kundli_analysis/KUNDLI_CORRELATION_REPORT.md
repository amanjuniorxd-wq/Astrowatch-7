# Kundli / Mahadasha Correlation Report (exploratory, unvalidated)

Built from `historical_events_v2.db` (ASTROWATCH-HIST-002), read-only. 28 of 140 events had both a known time (EXACT or APPROXIMATE) and known coordinates -- the minimum needed for a real Ascendant/house chart. This is NOT a validated predictor -- see the methodology note in `scripts/build_kundli_correlations.py` and the caveats at the end of this file.

## Sample composition

- NATURAL_DISASTER: 24
- SCIENCE_TECHNOLOGY: 2
- MILITARY: 1
- POLITICAL: 1

**24 of 28 eligible events are NATURAL_DISASTER** (mostly USGS/NOAA earthquakes and tsunamis, the only category with machine-precision timestamps in this dataset). Every correlation below involving another category is based on 1-2 events and should be read as an anecdote, not a pattern.

## Mahadasha lord vs. event category

| Mahadasha lord | event_type: count |
|---|---|
| ketu (n=5) | NATURAL_DISASTER=5 |
| rahu (n=4) | NATURAL_DISASTER=4 |
| moon (n=4) | NATURAL_DISASTER=2, SCIENCE_TECHNOLOGY=1, POLITICAL=1 |
| sun (n=4) | NATURAL_DISASTER=4 |
| saturn (n=3) | NATURAL_DISASTER=2, MILITARY=1 |
| mercury (n=2) | NATURAL_DISASTER=2 |
| jupiter (n=2) | SCIENCE_TECHNOLOGY=1, NATURAL_DISASTER=1 |
| venus (n=2) | NATURAL_DISASTER=2 |
| mars (n=2) | NATURAL_DISASTER=2 |

## Antardasha lord vs. event category

| Antardasha lord | event_type: count |
|---|---|
| mercury (n=7) | NATURAL_DISASTER=4, MILITARY=1, SCIENCE_TECHNOLOGY=1, POLITICAL=1 |
| jupiter (n=6) | NATURAL_DISASTER=6 |
| venus (n=5) | NATURAL_DISASTER=4, SCIENCE_TECHNOLOGY=1 |
| rahu (n=3) | NATURAL_DISASTER=3 |
| sun (n=3) | NATURAL_DISASTER=3 |
| saturn (n=2) | NATURAL_DISASTER=2 |
| mars (n=2) | NATURAL_DISASTER=2 |

## Ascendant Rāśi vs. event category

| Ascendant Rāśi | event_type: count |
|---|---|
| Dhanu (n=6) | NATURAL_DISASTER=5, MILITARY=1 |
| Kanya (n=5) | NATURAL_DISASTER=5 |
| Meena (n=4) | NATURAL_DISASTER=4 |
| Simha (n=3) | NATURAL_DISASTER=2, SCIENCE_TECHNOLOGY=1 |
| Karka (n=3) | NATURAL_DISASTER=3 |
| Vrischika (n=2) | NATURAL_DISASTER=2 |
| Tula (n=1) | NATURAL_DISASTER=1 |
| Mithuna (n=1) | SCIENCE_TECHNOLOGY=1 |
| Makara (n=1) | POLITICAL=1 |
| Vrishabha (n=1) | NATURAL_DISASTER=1 |
| Kumbha (n=1) | NATURAL_DISASTER=1 |

## Moon Rāśi vs. event category

| Moon Rāśi | event_type: count |
|---|---|
| Mithuna (n=4) | NATURAL_DISASTER=3, SCIENCE_TECHNOLOGY=1 |
| Karka (n=4) | NATURAL_DISASTER=3, MILITARY=1 |
| Mesha (n=4) | NATURAL_DISASTER=4 |
| Kanya (n=4) | NATURAL_DISASTER=3, SCIENCE_TECHNOLOGY=1 |
| Tula (n=3) | NATURAL_DISASTER=3 |
| Simha (n=2) | NATURAL_DISASTER=2 |
| Dhanu (n=2) | NATURAL_DISASTER=2 |
| Vrishabha (n=2) | NATURAL_DISASTER=2 |
| Kumbha (n=1) | NATURAL_DISASTER=1 |
| Meena (n=1) | NATURAL_DISASTER=1 |
| Makara (n=1) | POLITICAL=1 |

## Moon Nakshatra vs. event category

| Moon Nakshatra | event_type: count |
|---|---|
| Ashwini (n=3) | NATURAL_DISASTER=3 |
| Hasta (n=3) | NATURAL_DISASTER=2, SCIENCE_TECHNOLOGY=1 |
| Ashlesha (n=2) | NATURAL_DISASTER=2 |
| Pushya (n=2) | MILITARY=1, NATURAL_DISASTER=1 |
| Mrigashira (n=2) | NATURAL_DISASTER=2 |
| Swati (n=2) | NATURAL_DISASTER=2 |
| Uttara Phalguni (n=2) | NATURAL_DISASTER=2 |
| Mula (n=2) | NATURAL_DISASTER=2 |
| Krittika (n=2) | NATURAL_DISASTER=2 |
| Ardra (n=1) | NATURAL_DISASTER=1 |
| Shatabhisha (n=1) | NATURAL_DISASTER=1 |
| Punarvasu (n=1) | SCIENCE_TECHNOLOGY=1 |
| Uttara Bhadrapada (n=1) | NATURAL_DISASTER=1 |
| Purva Phalguni (n=1) | NATURAL_DISASTER=1 |
| Shravana (n=1) | POLITICAL=1 |
| Bharani (n=1) | NATURAL_DISASTER=1 |
| Vishakha (n=1) | NATURAL_DISASTER=1 |

## Caveats (read before using any of the above)

- **No held-out test set.** Every number above is in-sample -- the same 28 events used to find a pattern are the only events available to describe it.
- **No multiple-comparison correction.** 5 feature tables x up to a dozen distinct values each x 6 event categories is a large number of cells; some will look strongly "correlated" by chance alone at this sample size.
- **Category imbalance.** 24/28 events are NATURAL_DISASTER; any apparent association with POLITICAL, MILITARY, or SCIENCE_TECHNOLOGY is 1-2 data points and should not be trusted.
- **This was explicitly requested as a fast, non-rigorous pass** (see the conversation this was built from) -- it has NOT been run through this project's blind-backtest engine (backtest/) the way the rule-registry rules were in ASTROWATCH-BT-001. Treat every line above as a lead to investigate, not a validated claim.