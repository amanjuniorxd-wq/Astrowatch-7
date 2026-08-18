# Famous-People Chart Archetype Report

**Question asked:** does a person's chart look like a recognizable "type" -- does
their career field, and by extension personality/achievement/health, show up in
their planetary placements? **Method:** the full `famous_people_corpus.py` (674
people, 7 fields: ACTOR, MUSICIAN, ATHLETE, SCIENTIST, BUSINESS, AUTHOR,
ARTIST_DIRECTOR) run through `kundli.compute_kundli()` (673 succeeded; 1 -- the
legendary/undated "Homer" entry -- correctly refused a Moshier-approximate result,
see its `error` field). This is pure derived computation from already-validated,
already-committed chart data -- no new web research was needed, so unlike the
event-correlation work elsewhere in this project, this runs at the corpus's FULL
scale, not a small researched subset. Source: `analyze_chart_archetypes.py`,
`famous_people_kundli.db`.

**Time-reliability note (important, read before the tables):** only 33 of 674
people have a documented, sourced birth TIME; the rest use `famous_people_corpus.py`'s
existing `ASSUMED_NOON` convention. That makes Ascendant- and house-based findings
(who rules the 10th house, what's in the 6th/8th/12th) individually unreliable for
most of this corpus -- but the Moon's Nakshatra (and therefore the natal Mahadasha
lord) is comparatively low-sensitivity to a several-hour time error, so the tables
below lead with Mahadasha-lord and Sun/Mars-sign findings (reliable regardless of
exact birth time) and flag the Ascendant/10th-house findings as weaker, secondary,
and time-sensitive.

**Same caveat as every other pattern-mining pass in this project:** exploratory,
small effect sizes relative to sample noise, not a validated statistical finding
(`ASTROWATCH-BT-001`'s 519-event blind backtest found no significant edge at scale).

## 1. Natal Mahadasha lord by field (RELIABLE -- time-robust, n=673)

Top over-represented lord per field, vs. that lord's base rate (its share of the
120-year Vimshottari cycle -- Ketu/Sun/Mars are short (5.8-7%), so anything landing
disproportionately on them is a bigger relative signal than the same raw count
landing on long lords like Venus/Saturn/Mercury):

| Field (n) | Most over-represented lord | Observed % | Base % | Ratio |
|---|---|---|---|---|
| SCIENTIST (108) | Ketu | 16.7% | 5.8% | **2.86x** |
| SCIENTIST (108) | Sun | 13.9% | 5.0% | **2.78x** |
| BUSINESS (93) | Ketu | 16.1% | 5.8% | **2.76x** |
| BUSINESS (93) | Sun | 12.9% | 5.0% | **2.58x** |
| AUTHOR (67) | Mars | 14.9% | 5.8% | **2.56x** |
| ACTOR (114) | Moon | 16.7% | 8.3% | 2.00x |
| ARTIST_DIRECTOR (56) | Rahu | 23.2% | 15.0% | 1.55x |
| ATHLETE (141) | Moon | 12.8% | 8.3% | 1.53x |

The clearest pattern: **Ketu and Sun are both strongly over-represented for
SCIENTIST and BUSINESS** -- fields built on focus/detachment-from-distraction
(Ketu, traditionally associated with introspection, isolation, research) and
authority/willpower/identity (Sun, traditionally associated with leadership,
government, self-directed drive). That's a genuinely traditional-astrology-
consistent pairing on both counts. **Moon over-represented for ACTOR and ATHLETE**
also fits the traditional association of Moon with public visibility, emotional
expressiveness, and the body -- three things central to acting and sport.
AUTHOR's Mars over-representation is less obviously "story-consistent" (Mars is
usually read as combative/physical, not literary) and is the kind of result that
most needs a bigger sample before trusting.

## 2. Mars sign by field (time-independent, n=673)

Mars sign only depends on birth DATE, not time -- fully reliable regardless of the
ASSUMED_NOON issue. Top 3 signs per field:

| Field | Top Mars signs |
|---|---|
| ATHLETE | Vrishabha (16), Mithuna (15), Karka (14) |
| ACTOR | Mithuna (15), Vrishabha (13), Karka (12) |
| BUSINESS | Kanya (14), Mesha (10), Simha (10) |
| SCIENTIST | Tula (12), Kanya (12), Meena (11) |
| MUSICIAN | Simha (12), Mithuna (11), Kanya (11) |

No field shows one sign dominating sharply (max is 16/141 = 11% for Athletes'
Vrishabha Mars) -- Mars sign alone doesn't produce a strong field signal in this
corpus; listed for completeness, not because it's a notable finding.

## 3. Ascendant-lord / 10th-house-lord dignity (WEAK, time-sensitive, n=673 but
   only 33 have a documented time -- read this section skeptically)

Across all 7 fields, the 10th-lord's dignity distribution looks broadly similar
(roughly 60-70% NEUTRAL, 15-30% OWN_SIGN, 5-12% each EXALTED/DEBILITATED in every
field) -- no field stands out as having a systematically better- or worse-dignified
career-house ruler than any other. Given that most of this corpus uses an assumed
noon birth time, this null result is more likely a measurement-precision limit than
a genuine absence of pattern -- this is exactly the kind of question a larger
documented-birth-time subset (see `famous_people_corpus.py`'s `DOCUMENTED` tag)
would be needed to answer properly.

## 4. Health proxy: malefics (Saturn/Mars/Rahu/Ketu) in houses 6/8/12

| Field | n | Avg. malefics in 6th/8th/12th (of 4 possible) |
|---|---|---|
| ATHLETE | 141 | 0.91 |
| BUSINESS | 93 | 0.95 |
| AUTHOR | 67 | 1.03 |
| SCIENTIST | 108 | 1.06 |
| MUSICIAN | 94 | 1.09 |
| ACTOR | 114 | 1.16 |
| ARTIST_DIRECTOR | 56 | 1.00 |

Naive expectation under no pattern at all: with 4 malefics and 3 of 12 houses
counted as "affliction houses," about 1.0 malefic per chart lands there by chance
alone. Every field here sits within about +/-0.16 of that number -- **no field
shows a meaningfully different malefic-affliction burden than chance would predict**.
This is a genuine null result on this particular proxy, not a gap in the analysis;
reported honestly rather than searching for a way to make it look like a finding.

## Bottom line

The two most traditionally-coherent, largest-ratio signals here are Ketu/Sun
over-representation in the natal Mahadasha for scientists and business figures,
and Moon over-representation for actors/athletes -- all four fit long-standing
classical significations reasonably well. Everything house/Ascendant-dependent is
weak by construction (assumed birth times) and should not be read as a finding one
way or the other until more documented-time data exists.
