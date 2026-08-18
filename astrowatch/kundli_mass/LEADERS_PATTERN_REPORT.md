# Leadership Kundli/Mahadasha Pattern Report (37 leaders, exploratory, UNVALIDATED)

Built from `leaders_kundli.db`: 19 US Presidents, 10 Indian Prime Ministers, 8
current global leaders (see `leaders_corpus.py` for exact birth data and sourcing
notes). Only 11 of 37 have a *documented* (birth-certificate/record-sourced) birth
time; the other 26 use ASSUMED_NOON, per this session's standing instruction. **The
Ascendant (Lagna) is only trustworthy for the 11 DOCUMENTED-time entries** -- an
unknown birth time makes Ascendant/house placement essentially arbitrary. Moon
Rasi/Nakshatra and Mahadasha lord are far less time-sensitive and are the more
usable columns across the full 37.

## Ascendant frequency (DOCUMENTED birth times only, n=11)

Kanya (Virgo): 4, Simha (Leo): 3, Mithuna, Dhanu, Karka, Makara: 1 each.

n=11 is far too small to call this a real distribution -- noted for completeness,
not as a claim.

## Moon Rasi frequency (all 37)

Karka (Cancer): 6, Makara (Capricorn): 5, Kanya (Virgo): 5, Vrischika (Scorpio): 4,
Mesha (Aries): 4, others 1-3 each.

## Office-entry Mahadasha lord frequency (all 37, at the moment each took office)

Mercury: 8, Saturn: 7, Jupiter: 7, Rahu: 5, Ketu: 3, Moon: 3, Sun: 2, Mars: 2.

No lord is dramatically over-represented at this sample size -- roughly proportional
to each lord's share of the 120-year Vimshottari cycle (e.g. Jupiter=16/120=13%,
close to its 7/37=19% share here; within noise for n=37).

## Office-exit Mahadasha/Antardasha, by reason for leaving (27 leaders who have left)

Full per-leader table in `leaders_kundli_records.json`. No dasha lord combination is
exclusive to any single exit reason (term-limit, lost reelection, resigned, died in
office, or assassinated all occur across multiple different lords) -- there is no
usable signal here at n=27 split across 5+ categories, several with only 1-3 cases.

**On the "died in office / assassinated" subset specifically (n=6: Lincoln, FDR,
JFK, Nehru, Shastri, Indira Gandhi):** their exit Mahadasha/Antardasha combinations
are all different from each other (Saturn/Ketu, Ketu/Saturn, Jupiter/Saturn,
Rahu/Jupiter, Ketu/Venus, Saturn/Venus) -- there is no shared astrological signature
among them. This is reported here only for completeness/transparency, exactly as it
came out of the mechanical query, and explicitly NOT used anywhere in this project's
Trump/September-2026 output: six events is nowhere near enough to support any claim
about violence or mortality risk for a real, current public figure, and this project
will not present it that way regardless of any surface-level pattern match a small
sample happens to produce.

## Donald Trump's own record (for reference)

Natal (June 14, 1946, 10:54 AM EDT, Jamaica Queens NY -- DOCUMENTED time):
Ascendant Simha (Leo) / Magha nakshatra, Moon Vrischika (Scorpio) / Jyeshtha, Sun
Mithuna (Gemini), Mars in Simha (1st house, conjunct Ascendant). Office-entry
(Jan 20 2017) Mahadasha/Antardasha: Jupiter/Jupiter. As of September 2026: Jupiter
Mahadasha (2015-12-06 to 2031-12-06) / Sun Antardasha (2026-06-19 to 2027-04-07) --
stable across the full month, no mid-month period change.

## Caveats (identical spirit to every other report in this project)

- n=37 total, with meaningful sub-splits far smaller (11 documented Ascendants, 6
  died-in-office cases, etc.) -- nowhere near enough for any statistically
  defensible claim.
- No held-out set, no significance testing, no multiple-comparison correction.
- ASSUMED_NOON charts (26 of 37) should not be trusted for Ascendant/house-based
  claims at all.
- This is a curiosity-driven pattern extraction exercise, consistent with the
  reduced-rigor standard set earlier in this session, not a validated model of
  political careers.
