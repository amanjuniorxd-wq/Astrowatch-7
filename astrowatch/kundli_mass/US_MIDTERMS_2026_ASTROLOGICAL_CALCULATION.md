# US Midterms 2026 -- Astrological Calculation (Republican vs. Democrat)

**Astrological calculation only.** Not a real forecast, not backed by any predictive
validation -- this project's own blind backtest (`ASTROWATCH-BT-001`, 519 real
historical events) found no statistically significant edge for this style of
astrology. Treat everything below as a symbolic reading, not a claim about what will
actually happen on November 3, 2026.

## The question and the method

Election day: **November 3, 2026** (all 435 House seats, 35 Senate seats, 39
governorships -- confirmed via live search this session).

Vimshottari Mahadasha has no built-in concept of a "political party" -- there's no
classical technique for "which party wins an election." To give a real, calculated
(not fabricated) answer, this applies the same mundane-astrology rule used for
nations earlier this session (real inception date + place -> real kundli) to the
two parties themselves, using their own real, sourced founding moments:

- **Republican Party**: founded **March 20, 1854**, at a meeting in **Ripon,
  Wisconsin** -- the most commonly cited founding date/place (a Feb 24, 1854
  preliminary meeting also exists; March 20 is the one generally treated as the
  founding).
- **Democratic Party**: founded **January 8, 1828** -- the date of Andrew Jackson's
  campaign speech in **New Orleans, Louisiana** on the 13th anniversary of his
  Battle of New Orleans victory, the moment supporters organized as "the Democracy" /
  Democratic Party (some sources instead mark the party's first national convention
  in 1832 as the "real" founding -- 1828 is used here as the more commonly cited date).

Neither party recorded a founding *time* (unsurprisingly -- no such record exists for
either), so both charts use **00:00 assumed local time**, per this project's own
mundane-astrology rule (`MUNDANE_ASTROLOGY_RULE.md`) -- meaning, as with every
assumed-midnight chart in this project, the Ascendant/houses are not reliable in
detail, but the Moon-based Mahadasha/Antardasha sequence is comparatively robust.

**Scoring convention (my own construction this session, not a classical citation):**
for each party's chart, find the Mahadasha and Antardasha lord actually ruling on
election day (via the same validated, multi-cycle-aware progressed-dasha walker used
for the nations work), then score each lord on 3 factors -- (1) its own dignity in
that party's natal chart (exalted +2 / own-sign +1 / neutral 0 / debilitated -2),
(2) whether it occupies a kendra or trikona ("strong") house, a dushtana ("afflicted")
house, or neither (+1 / -1 / 0), and (3) whether it's a natural benefic or malefic
(+0.5 / -0.5) -- weighted 40% Mahadasha + 60% Antardasha (the more immediate period).
**This weighting and point scheme is a reasonable-but-arbitrary choice, not derived
from any text** -- a different, equally defensible scoring convention could weight
these differently.

## The numbers

### Republican Party (founded 1854-03-20, Ripon, WI)
Ascendant: Vrischika (Scorpio). On 2026-11-03:
- **Mahadasha: MOON** [2022-11-04 -> 2032-11-04] -- natal dignity **DEBILITATED**
  (Moon sits in Vrischika/Scorpio, its classical debilitation sign), house 1 (kendra).
  Score: -0.5
- **Antardasha: JUPITER** [2025-10-05 -> 2027-01-01] -- natal dignity **DEBILITATED**
  (Jupiter sits in Makara/Capricorn, its classical debilitation sign), house 3 (neither
  kendra/trikona/dushtana). Score: -1.5
- **Combined score: -1.10**

Both the ruling Mahadasha lord AND the ruling Antardasha lord are independently
debilitated in the Republican Party's own natal chart -- a real, doubly-afflicted
reading, not a cherry-picked one.

### Democratic Party (founded 1828-01-08, New Orleans, LA)
Ascendant: Kanya (Virgo). On 2026-11-03:
- **Mahadasha: MERCURY** [2021-11-12 -> 2038-11-12] -- natal dignity **NEUTRAL**,
  house 4 (kendra). Score: +1.5
- **Antardasha: VENUS** [2025-04-06 -> 2027-01-01] -- natal dignity **NEUTRAL**,
  house 5 (trikona). Score: +1.5
- **Combined score: +1.50**

Both ruling lords sit in strong (kendra/trikona) houses of the party's own natal
chart, and both are natural benefics.

### Verdict by this methodology: **Democratic Party reads astrologically favored**
(+1.50 vs. -1.10) for the November 2026 midterms.

## Context that complicates a simple "Democrats win" headline

- **The sitting president's OWN chart reads the opposite way.** Donald Trump
  (Republican, incumbent) is running **Jupiter Mahadasha / Venus Antardasha** on
  election day -- both natural benefics, a strong personal-chart reading, in tension
  with his own party's weaker chart above. Astrology doesn't resolve this tension for
  you; a mundane astrologer could reasonably read it either way (does the president's
  personal chart or the party's institutional chart matter more for a midterm?).
- **The US national chart itself (founded 1776-07-04) is in Rahu Mahadasha / Jupiter
  Antardasha** on election day -- Rahu (disruption, unconventional/turbulent shifts)
  as the broader era, Jupiter (expansion, institutional confidence) as the immediate
  sub-period. This reads as a turbulent overall period with a comparatively more
  optimistic near-term flavor -- again, not party-directional by itself.
- **Real, non-astrological context worth knowing alongside this:** in nearly every
  US midterm since World War II, the president's own party has lost House seats --
  a well-documented political-science pattern with no astrology involved at all.
  That pattern alone would point the same direction as this astrological reading
  (away from the president's party, currently Republican) for reasons that have
  nothing to do with planets.
- **A midterm is not one race.** 435 House districts, 35 Senate seats, and 39
  governorships each have their own local dynamics that no single national-level
  chart -- astrological or otherwise -- can resolve. This reading speaks to a
  symbolic national "mood," not a seat count.

## Bottom line

Given the explicit ask for "just an astrological calculation": using each party's own
real founding chart and the same validated dasha methodology this project has used
throughout, **the Democratic Party's ruling planetary period reads meaningfully
stronger than the Republican Party's** for November 3, 2026 (+1.50 vs. -1.10),
driven mainly by both of the Republican Party's currently-ruling planets being
independently debilitated in its own natal chart. Whether that's worth anything is a
separate question this project's own backtest already answered: no.
