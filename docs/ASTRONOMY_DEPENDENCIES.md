# Astrowatch — Dependency / Version Record

Kept as a standalone file for visibility (same information is also embedded in
`ayanamsha.py`'s module docstring, "DEPENDENCY / VERSION RECORD" section).

| Item | Value |
|---|---|
| Swiss Ephemeris version | **2.10.03** — self-reported in every `swetest.cgi` response banner this session (e.g. `version 2.10.03`), not assumed |
| pyswisseph version | **N/A** — not installed, not used. Installing it requires `pip install pyswisseph`, which requires a working shell; this session's sandbox is unavailable (see `VALIDATION_REPORT.md`). The live-CGI path uses Astrodienst's own server-side SE binary directly over HTTP, not the Python binding |
| Selected sidereal mode | **1** — SE's default/plain "Lahiri" (see `ayanamsha.py`'s METHODOLOGY SELECTION section for the sourced justification; explicitly NOT modes 43 "Lahiri 1940", 44 "Lahiri VP285", or 46 "Lahiri ICRC") |
| Methodology name | "Lahiri" / "Chitrapaksha ayanamsha", 1955/56 Indian Calendar Reform Committee (N.C. Lahiri, Secretary) |
| Calculation / data-gathering date | 2026-08-12 (session date) |
| Query mechanism | HTTP GET to `https://www.astro.com/cgi/swetest.cgi`, raw-flag passthrough via `arg=`, e.g. `arg=-bj2451545.0+-p0+-fPZL+-sid1+-n1` |
| Relevant settings | `-fPZL` (output format incl. longitude), `-sid1` (sidereal mode 1), `-bj<JD>` (absolute Julian Day, confirmed empirically to be interpreted as **TT**, not UT) |
| Underlying planetary ephemeris (JPL vs. Moshier vs. SE's own) | **Not confirmed** — no `-ejpl`/`-eswe`/`-emos` override flag was passed in any query this session, so whichever Astrodienst's server defaults to was used; this was not independently determined and should not be assumed |
| Python execution of any of the above | **Not executed** — see `VALIDATION_REPORT.md` Phase 8/9 for the three independently-attempted, independently-failed execution paths this session |

## What is and isn't "Swiss Ephemeris" in this project

- **Astronomical layer (raw planetary positions):** `ephemeris_client.py`, backed by **JPL Horizons** (`ssd.jpl.nasa.gov`). Swiss Ephemeris is never asked for a planetary position in this project.
- **Sidereal transformation layer (ayanamsha offset only):** `ayanamsha.py`, backed by a **live query to Swiss Ephemeris 2.10.03** (primary path) with a two-point linear model as an explicitly-flagged offline fallback.
- These two layers are kept deliberately separate — see `ayanamsha.py`'s ARCHITECTURE section.
