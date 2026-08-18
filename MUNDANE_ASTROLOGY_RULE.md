# The Mundane-Astrology Rule

**Stated by the user, this session, in these terms:**

> Everything can be analysed in kundli and mahadasha if inception of that
> particular thing has a date, birth place, and time is available; time not
> available = assume 12 AM. Basically create a pattern and apply it to any
> kundli and mahadasha no matter what entity that kundli belongs to, whether
> it be a stock exchange, sports team, nation, political leader, or anything.

Worked example given by the user: **India** -- formation `15/8/1947`, time
`12:00:00 AM` -> kundli made -> anything can be predicted astrologically
about the nation. Apply the same logic to nations, economies, leaders,
sports teams, everything.

## What this project already had, and what's new

Nothing about `kundli.compute_kundli()` or `mahadasha.compute_dasha_state()`
was ever person-specific -- both already operate on a bare `(jd_ut, latitude,
longitude)` / `(jd_ut, moon_sidereal_lon)` and have been used elsewhere in
this project on **historical events**, not just people (see
`astrowatch/kundli_mass/life_events_dasha_mapping.py`). What's new is making
that fact explicit and giving it one shared, documented entry point:
`astrowatch/mundane/entity_chart.py`'s `compute_entity_chart()`, used
identically for a person, a nation, a company, or anything else with:

1. a real inception **date**,
2. a real inception **place** (for the Ascendant/houses -- required for a
   geographically meaningful chart at all), and
3. an inception **time**, or, if genuinely unknown/nonexistent (most
   nations' independence moments were never recorded to the minute the way
   a hospital birth certificate is), the documented default of **00:00
   local civil time** -- exactly the convention the user specified.

Every `EntityChart` this module produces is tagged
`time_source = "DOCUMENTED"` or `"ASSUMED_MIDNIGHT"` so nothing downstream
can silently forget which charts have a real time behind them.

## Accuracy implications of the 00:00 default (stated honestly, not hidden)

- **Ascendant and all house placements are NOT reliable** when the time is
  assumed. The Ascendant moves about 1 degree every 4 minutes; the true
  founding moment could be off from "00:00" by minutes to hours (or, for
  many entities, may not have a single well-defined instant at all -- when
  exactly does a company or a sports team "begin," to the minute?).
- **Planetary sign (Rashi) placements are effectively time-independent**
  within a single calendar day for every body except the Moon.
- **The Moon's Rashi/Nakshatra -- and therefore the Vimshottari Mahadasha/
  Antardasha lord -- is comparatively low-sensitivity** to a several-hour
  time error (the Moon moves roughly 0.5 degree/hour; a nakshatra is 13.33
  degrees wide, so it would take a ~26-hour time error to likely misplace
  it, and even then only near a nakshatra boundary). This is why this
  project's pattern-mining work leans on Mahadasha-lord correlations far
  more than on house/Ascendant-based claims wherever the underlying time is
  assumed rather than documented.

## Where this rule is applied in the codebase

- `astrowatch/mundane/entity_chart.py` -- the rule's implementation
  (`compute_entity_chart`, `full_lifetime_dasha`).
- `astrowatch/mundane/dasha_timeline.py` -- the full-lifetime Mahadasha/
  Antardasha walker (shared with the person corpus; this was previously
  duplicated inline in `kundli_mass/build_famous_lifetime_dasha.py`, now a
  single source of truth both use).
- `astrowatch/kundli_mass/nations_corpus.py` + `build_nations_kundli.py` +
  `build_nations_lifetime_dasha.py` -- nations, per the user's worked
  example.
- Person charts (`famous_people_corpus.py`) predate this explicit rule and
  use their own documented default (`ASSUMED_NOON`, not midnight) --
  that convention is left as-is for the existing 674-person corpus rather
  than silently changed retroactively, since the existing dataset, patterns,
  and reports were already built and frozen against it. New entity types
  (nations first, more to follow) use the user's midnight-default
  convention going forward, as this module documents.
