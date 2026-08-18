# National Mahadasha Pattern Report

**Method:** for 27 nations in `nations_corpus.py` (real formation/independence dates,
capital-city location, `00:00` assumed local civil time per `MUNDANE_ASTROLOGY_RULE.md`),
74 real, widely-documented major national events (wars, revolutions/coups, economic
crises/booms, reunifications, regime changes, one disaster) were looked up against
that nation's mechanically-computed Vimshottari Mahadasha/Antardasha timeline
(`nations_lifetime_dasha.db`) to find which planetary Mahadasha was running when each
event happened. Source data: `nations_events_corpus.py` / `nations_events_dasha_mapping.db`.

**This is exploratory, not a validated finding.** n=74 events across 9 possible
Mahadasha lords is a small sample (about 8 events per lord on average); this report
does not run a significance test, and this project's own much larger blind backtest
(`ASTROWATCH-BT-001`, 519 real historical events, permutation p=1.0) found no
statistically significant predictive edge for this style of astrology at scale. Any
pattern below should be read as "worth a closer look with more data," not as a
demonstrated effect.

**Why base rate matters here:** each Mahadasha lord governs a different, fixed number
of years out of the 120-year Vimshottari cycle (Venus 20, Saturn 19, Mercury 17, Rahu
18, Jupiter 16, Moon 10, Ketu 7, Mars 7, Sun 6). A lord with more years simply covers
more calendar time across any nation's history and will rack up more events by pure
chance, even under a true null. All numbers below are shown both as raw counts and
as a ratio against that lord's base-rate share of the 120-year cycle -- a ratio near
1.0x means "about what you'd expect from chance alone given how much time that lord
covers"; higher or lower suggests (not proves) something worth a closer look.

## Overall distribution (all 74 events)

| Lord | Events | Observed % | Base-rate % | Ratio |
|---|---|---|---|---|
| Mercury | 14 | 18.9% | 14.2% | **1.34x** |
| Venus | 14 | 18.9% | 16.7% | 1.14x |
| Jupiter | 11 | 14.9% | 13.3% | 1.11x |
| Ketu | 5 | 6.8% | 5.8% | 1.16x |
| Sun | 4 | 5.4% | 5.0% | 1.08x |
| Rahu | 10 | 13.5% | 15.0% | 0.90x |
| Saturn | 9 | 12.2% | 15.8% | 0.77x |
| Mars | 3 | 4.1% | 5.8% | 0.69x |
| Moon | 4 | 5.4% | 8.3% | 0.65x |

Mercury is the most over-represented lord overall in this small sample. No lord is
dramatically over- or under-represented at this scale -- all ratios are within roughly
+/-35% of 1.0x, which is well within what a sample this size could produce by chance.

## By event type (only categories with n >= 9 shown; smaller categories are in the
raw database but too small to say anything about)

### WAR (n=18)
| Lord | Events | Observed % | Base-rate % | Ratio |
|---|---|---|---|---|
| Saturn | 4 | 22.2% | 15.8% | 1.40x |
| Sun | 3 | 16.7% | 5.0% | **3.33x** |
| Mercury | 3 | 16.7% | 14.2% | 1.18x |
| Rahu | 1 | 5.6% | 15.0% | 0.37x |

Saturn and Sun are over-represented among wars in this sample. Saturn-with-conflict
is a long-standing traditional mundane-astrology association (Saturn = hardship,
loss, restriction); Sun's 3.33x ratio is the single largest ratio anywhere in this
report, but rests on just 3 events (US Civil War 1861, Israel Six-Day War 1967,
Egypt 1952 coup) -- a genuinely small number to draw any conclusion from.

### REVOLUTION / COUP (n=13)
| Lord | Events | Observed % | Base-rate % | Ratio |
|---|---|---|---|---|
| Rahu | 4 | 30.8% | 15.0% | **2.05x** |
| Mercury | 4 | 30.8% | 14.2% | **2.17x** |
| Venus | 1 | 7.7% | 16.7% | 0.46x |

Rahu-with-upheaval is, like Saturn-with-war above, a long-standing traditional
association (Rahu = disruption, sudden/unconventional change) -- and it does show
the second-largest ratio in this whole report. Mercury is equally elevated here,
with no obvious traditional-astrology story behind it; that "no traditional
narrative, but the numbers still moved" combination is exactly the kind of pattern
that most needs a bigger sample before trusting it.

### ECONOMIC CRISIS (n=9)
| Lord | Events | Observed % | Base-rate % | Ratio |
|---|---|---|---|---|
| Jupiter | 2 | 22.2% | 13.3% | 1.67x |
| Ketu | 1 | 11.1% | 5.8% | 1.90x |
| Mars | 1 | 11.1% | 5.8% | 1.90x |
| Saturn | 2 | 22.2% | 15.8% | 1.40x |

n=9 is too small to read anything into individual ratios here (each event moves the
percentage by more than 10 points); listed for completeness only.

## Honest bottom line

The two largest, most traditionally-consistent signals in this pass -- Saturn
elevated for wars, Rahu elevated for revolutions -- are also the two with the
clearest pre-existing astrological narrative behind them, which is exactly the
situation where confirmation bias in event selection is hardest to rule out (even
though this sample was chosen for documentation quality, not to fit an outcome, per
`nations_events_corpus.py`'s own docstring). Mercury's broad, category-spanning
over-representation has no such narrative and is the more surprising of the two
patterns, for whatever that's worth at n=74. Scaling this analysis (more nations,
more events per nation, ideally drawn from a pre-registered event list rather than
"most historically famous events I could name," and run through the same
permutation-test methodology `ASTROWATCH-BT-001` used) would be the honest next
step before treating any of this as more than a starting hypothesis.
