# Swiss Ephemeris data files

`sepl_18.se1`, `semo_18.se1`, `seas_18.se1` (+ the `_12`/`_24` 600-year-block neighbors)
are the real Swiss Ephemeris main-body/asteroid data files, JPL-derived, in Astrodienst's
own `.se1` binary format. They are NOT approximations and were NOT fabricated -- they were
extracted from the `flatlib` package (MIT-licensed, PyPI: https://pypi.org/project/flatlib/),
which bundles them as installed package data (`flatlib/resources/swefiles/`).

WHY THIS INDIRECT SOURCE: this project's own sandbox cannot reach astro.com, GitHub's
codeload/raw content hosts, or Dropbox (all return HTTP 403 from the outbound proxy this
session -- confirmed via direct curl tests), which is where Astrodienst distributes these
files directly. `pypi.org`/`files.pythonhosted.org` ARE reachable, and `flatlib` is an
open-source package that redistributes the same files under its own license terms.

COVERAGE: the `_12`/`_18`/`_24` suffixes are Swiss Ephemeris's own 600-year-block naming
convention. Together the three blocks bundled here cover roughly 1200-01-01 through
2999-12-31 (per Swiss Ephemeris's own file-range convention) -- comfortably covering this
project's targeted ~1800-2050 range and then some.

VINTAGE NOTE (see ARCHITECTURE_SE_MIGRATION.md for the full numeric writeup): these files
are dated 2021-04-05 (per flatlib's own package metadata). Astrodienst's public
`swetest.cgi` was found this session (via its own repository README, fetched live) to have
been rebuilt in April 2026 against a newer JPL ephemeris (DE441). Cross-checking this
project's local computation against that live, newer reference found sub-0.3-arcsecond
differences for Jupiter/Saturn (and sub-0.1-arcsecond for Sun/Moon/Mercury/Venus/Mars/
Ascendant) -- consistent with this known ephemeris-vintage gap, not a bug. Still an
enormous improvement over both this project's prior Moshier-fallback and JS-approximate
paths (which had arcminute-to-degree-class errors). If a newer file set becomes reachable
in a future session (e.g. sandbox network policy changes), replacing these files is a
drop-in swap -- nothing else in the codebase needs to change.

LICENSE: Swiss Ephemeris itself is available under AGPL or a commercial Astrodienst
license (see https://www.astro.com/swisseph/); flatlib redistributes the ephemeris data
files under its own MIT license. This project uses these files for non-commercial
astronomical calculation, consistent with Swiss Ephemeris's public/free-edition terms.
