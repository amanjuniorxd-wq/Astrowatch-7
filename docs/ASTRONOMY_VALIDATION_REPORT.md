# Astrowatch Coordinate Module — Validation Report (Revision 2)

**Status: PARTIAL. Coordinate module remains NOT production-ready.
Prospective forecasting stays LOCKED.**

Revision 2 adds: a proper source-by-source coordinate-definition table (Phase 1), a
redone Phase 2 comparison carried to higher hand-precision specifically to diagnose
*why* the original 3.5′ discrepancy existed (not to tune it away), and an explicit
per-rule zodiac-convention classification (Phase 4). Automated multi-body/multi-date
testing (Phase 3) is still not done — that requires actual code execution and is not
being simulated by hand.

---

## PHASE 1 — COORDINATE DEFINITIONS PER SOURCE

| Property | theskylive.com (live snapshot, used earlier in session) | JPL Horizons `EPHEM_TYPE=OBSERVER` | JPL Horizons `EPHEM_TYPE=VECTORS`, `REF_PLANE=ECLIPTIC` (confirmed working) |
|---|---|---|---|
| Coordinate type | R.A./Dec. | R.A./Dec. | Cartesian X/Y/Z |
| Reference frame | Not documented on the page. Inferred (see Phase 2) to be close to true-equator-and-equinox of date. | ICRF-aligned per Horizons documentation; exact epoch depends on QUANTITIES code chosen | Explicitly stated by the response itself: **"Ecliptic of J2000.0"** |
| Epoch | Unstated | Unstated in this session (endpoint did not return data) | **J2000.0**, explicitly stated |
| Equinox | Unstated; behavior in Phase 2 is consistent with equinox-of-date but this is inference, not documentation | QUANTITIES=1 = astrometric (J2000-ish, minimal corrections); QUANTITIES=2 = apparent (equinox of date) — **neither could be confirmed this session, endpoint returned empty both times** | J2000.0 fixed (not of-date) |
| Apparent vs. astrometric | Unstated | Selectable, but untested | N/A (Cartesian state vector, not an apparent-position quantity) |
| Geocentric vs. topocentric | Unstated, presumed geocentric (no observer location given on the page) | Set via CENTER parameter; `500@399` = Earth body center = geocentric | `CENTER=500@399` = **geocentric** (used this session) |
| Aberration treatment | Unstated | Depends on QUANTITIES/APPARENT settings, untested | Explicitly stated: **"Geometric state vectors have NO corrections or aberrations applied"** |
| Light-time treatment | Unstated | Untested | Geometric — **no light-time correction** (this matters: the Sun's *apparent* position is offset from its *geometric* position by ~8.3 light-minutes of orbital motion, on the order of tens of arcseconds — this alone is a plausible contributor to any residual discrepancy against an apparent-position source like theskylive.com) |
| Precession/nutation | Unstated | Untested | Fixed J2000 frame — by construction, **no** precession/nutation applied (that's what "J2000.0" fixed means) |
| Units | Sexagesimal RA/Dec | Sexagesimal RA/Dec (intended) | **Kilometers**, Cartesian |
| Time scale | Unstated | Unstated (untested) | **TDB** (Barycentric Dynamical Time), explicitly stated |

**Conclusion of Phase 1: these three sources are NOT directly interchangeable**, and I
am not treating them as such. In particular, comparing a **geometric, no-light-time,
J2000-fixed** vector (Horizons VECTORS) against an **apparent, of-date** position
(theskylive.com, presumptively) has at least two known, real, non-error sources of
difference baked in: (a) ~26 years of precession between J2000 and 2026, and (b) the
light-time/aberration offset neither corrected for. Any comparison between them has to
be read with that in mind, not treated as a clean apples-to-apples check.

---

This report addresses each of the 10 validation requirements directly, with what was
actually done, real numbers obtained this session, and what remains outstanding.

---

## 1. Reference frame of external sources — investigated, partially resolved

- **JPL Horizons `EPHEM_TYPE=OBSERVER`** (which `ephemeris_client.py` was written to use):
  failed to return any ephemeris data in this session regardless of `QUANTITIES` value
  tried (1, 2, and 31 all returned empty bodies from three separate live attempts — see
  raw evidence below). This is a genuine, reproducible failure in this environment, not
  a one-off. **`ephemeris_client.py`'s OBSERVER-table path must be treated as unverified
  and possibly broken** until someone can run it in an environment where the failure
  mode is visible (right now the tool used to fetch these URLs returns no error and no
  body — I can't tell if Horizons itself rejected the request or something is being
  swallowed in transit).

- **JPL Horizons `EPHEM_TYPE=VECTORS`, `REF_PLANE=ECLIPTIC`**: this **did work**, and
  returned a fully self-documenting response: *"Reference frame: Ecliptic of J2000.0"*,
  geometric (explicitly stated: *"NO corrections or aberrations applied"*), center =
  Earth body center, time system TDB. This is now the more trustworthy data path and
  `ephemeris_client.py` has been updated accordingly (see below).

- **theskylive.com** (used earlier in the session for a live Sun/Moon/planets snapshot):
  **no explicit frame documentation found on the page itself.** I did not simply assume
  "apparent equinox-of-date" this time — I cross-checked it (see Section 2). The
  cross-check result is *consistent with* apparent/of-date coordinates, but is not a
  certified confirmation from their own documentation. Treat theskylive.com's exact
  frame as **probable, not confirmed**.

## PHASE 2 — VECTORS AS GROUND TRUTH, REDONE AT HIGHER PRECISION TO DIAGNOSE THE ERROR

Same source, same instant as the first pass (Sun, 2026-Aug-12 00:00 TDB, Horizons
VECTORS geocentric ecliptic J2000): **no constants were changed.** The only thing
changed between this pass and the original is arithmetic precision — every trig value
carried to 6-7 significant figures via careful interpolation instead of the coarser
lookups used the first time. The point is diagnostic: if the original gap was rounding
error, carrying more precision through the *same* formula should shrink it substantially.
If it didn't shrink, that would point to an actual formula bug instead.

| Quantity | Independent (Horizons vectors, direct atan2) | Recovered via formula — Pass 1 (coarse) | Recovered via formula — Pass 2 (refined precision) |
|---|---|---|---|
| Ecliptic longitude | 138.959° | 138.901° (Δ ≈ 209″) | **138.9614° (Δ ≈ 8.6″)** |
| Ecliptic latitude | −0.00195° (−7″) | −0.012° (Δ ≈ 36″) | **−0.00023° (Δ ≈ 6″)** |

**Diagnosis: the original discrepancy was accumulated hand-rounding error, not a
formula defect.** This is expected on independent mathematical grounds, not just an
empirical coincidence: the round trip (ecliptic→equatorial via +ε, then
equatorial→ecliptic via my formula, which is mathematically the inverse rotation, −ε)
is an identity operation if executed with exact arithmetic — it *must* return the
original longitude/latitude exactly. Any nonzero result is therefore, by construction,
entirely attributable to the finite precision of whatever is doing the arithmetic. Going
from ~6-figure coarse interpolation to more careful ~7-figure interpolation cut the
longitude error by a factor of ~24 (209″ → 8.6″) and the latitude error by a factor of ~6
(36″ → 6″) — consistent with a rounding-error explanation, not consistent with a
structural bug (a structural bug would not shrink like that just from carrying more
decimal places through the identical formula).

**What this does and doesn't establish:**
- It supports, fairly strongly, that `_ecliptic_from_ra_dec()`'s formula is
  mathematically correct.
- It does **not** establish arcsecond-level certified accuracy, because this is still
  one hand-executed calculation, for one body, at one instant, done by a human carrying
  decimal approximations — not code running IEEE double-precision floats. The residual
  ~6-9″ is plausibly further rounding, but I can't rule out a residual systematic term
  without running the actual code.
- It does **not** replace Phase 3's automated multi-body/multi-date suite, which is a
  different and necessary test (this only checked the transform formula's internal
  consistency on a round trip; it did not check, e.g., the mean-obliquity-of-date
  polynomial against an independent obliquity source, or exercise the code path at all
  since none of this was actually executed as code).

**Net Phase 2 verdict: PARTIAL, upgraded from Phase 1.** The formula is now well-supported
rather than merely "plausible," but this is still not the certified pass Phase 3 requires.

## PHASE 3 — AUTOMATED TEST SUITE

**NOT DONE. Execution capability missing — precise diagnosis below, not a vague "sandbox down."**

Two independent code-execution paths were tried this pass:

1. **Local sandbox** (`mcp__workspace__bash`): still fails with the same error as every
   prior attempt this session — *"Not enough disk space to set up the workspace."* This
   is a host-side provisioning failure, not something retryable from in-conversation.
2. **Remote-isolated subagent** (an alternative execution path, tried specifically to
   route around #1): failed immediately with *"Failed to resolve base branch 'HEAD':
   git rev-parse failed."* This isolation mode expects a git repository to attach a
   worktree/branch to; this workspace isn't one. Different failure mode from #1 — not a
   capacity problem, a structural mismatch between what that tool expects and what this
   environment is.
3. **Worktree-isolated subagent** (tried in a follow-up pass, as a distinct isolation
   mode from #2, in case it behaved differently): failed identically — *"Failed to
   resolve base branch 'HEAD': git rev-parse failed."* Same root cause as #2: both
   isolation modes require a git repository to attach to, and this Cowork workspace
   (a scratchpad output folder) is not one. This confirms the git-repo requirement is
   the actual blocker for both isolation modes, not a fluke of one of them.

**Net: I have now tried every code-execution path available to me in this session (1
direct sandbox call + 2 distinct agent-isolation modes), and all three are unreachable,
for two identifiable and different underlying reasons (disk space on the direct sandbox;
missing git repository for both agent-isolation modes). No further retry of any of these
three paths is expected to produce a different result without an external fix (freeing
sandbox disk space, or initializing this workspace as a git repository) that is outside
what I can do from within this conversation.** Per your instruction, I did not fall back to more manual
arithmetic to compensate. Instead:

- `test_validation_suite.py` has been written — real, complete, ready-to-run code
  implementing exactly the body x date matrix below (Sun/Moon/Mercury/Venus/Mars/
  Jupiter/Saturn x 1900/1950/2000/2026/2030), plus the acceptance-criteria analysis
  (next section) baked into its own docstring so the threshold is committed *before*
  anyone runs it and sees numbers. It has NOT been executed. Running it requires either
  this session's sandbox recovering, or someone running `python3 test_validation_suite.py`
  themselves (stdlib only, no dependencies) in any working Python 3 environment.
- The table below stays empty, honestly, rather than populated with anything I didn't
  actually compute:

| Date | Body | Reference longitude | Calculated longitude | Error |
|------|------|---------------------|----------------------|-------|
| *(pending real execution — see test_validation_suite.py)* | | | | |

### Acceptance criteria, established before any numbers exist (not fitted afterward)

`test_validation_suite.py`'s design is a **self-consistency round trip**: reference and
calculated longitude/latitude both derive from the *same* fetched Cartesian vector, in
the *same* frame, at the *same* instant — the two rotations involved are exact
mathematical inverses. Working through each precision source that could contribute
error in that specific design:

- **Source (Horizons/DE441) precision**: sub-arcsecond for planetary positions in this
  date range — but irrelevant here, since both sides of the comparison use the identical
  fetched number, not two independently-sourced ones.
- **Input coordinate precision**: Horizons prints X/Y/Z to ~16 significant figures —
  far more than needed.
- **Floating-point precision**: Python floats are IEEE754 double (~15-17 significant
  decimal digits); propagated through ~10 trig calls, expected numerical noise is
  roughly 1e-12 to 1e-9 degrees ≈ 1e-6 to 1e-3 arcsec.
- **Transformation assumptions**: none introduce error here specifically, because both
  legs of the round trip use the identical, matched J2000 frame — this design was
  chosen precisely to eliminate the frame-mismatch issue that explained the earlier
  8.6″/6″ figures.
- **Reference-frame differences**: deliberately eliminated by construction in this test
  (see above) — they matter for a *different* test (comparing against an apparent-
  position source like theskylive.com), not this one.

**Committed threshold: < 0.01 arcsec = PASS for this round-trip test.** 0.01–1 arcsec =
investigate as a possible edge-case numerical issue. **>1 arcsec = genuine bug, to be
found and fixed, not tolerated by loosening the threshold** — consistent with your
explicit instruction not to fit the math to agreement after the fact.

This round-trip design deliberately does **not** re-validate against a real apparent-
position source the way the Phase 1/2 hand-check did — that remains a separate,
loosely-toleranced (arcminute-scale, due to real precession/aberration/light-time
effects) test, not to be conflated with this one.

| Date | Body | Reference longitude | Calculated longitude | Error |
|------|------|---------------------|----------------------|-------|
| *(pending — 1900, 1950, 2000, 2026, future)* | *(pending — Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn)* | *(pending — from JPL Horizons VECTORS, computed automatically)* | *(pending — from `coordinates.py`, run as code)* | *(pending)* |

Also not done, same reason: sign-boundary cases (near 0°/30°/etc.), near-station
(retrograde-turn) cases, and high-ecliptic-latitude objects. All require running loops
of real code against real dates, which is not available this session.

## Prior single-point validation (superseded above, kept for record) — done for ONE body, ONE date, BY HAND; not yet automated or scaled

**What ground truth I used:** Horizons VECTORS gave the Sun's geocentric ecliptic
Cartesian position (J2000.0 ecliptic, geometric) for 2026-Aug-12 00:00 TDB:

```
X = -1.143459250545978E+08 km
Y =  9.954430758214843E+07 km
Z = -5.154432458586991E+03 km
```

From these I independently derived (by direct `atan2`, not via my RA/Dec code path):

- **Ecliptic longitude (independent) = 138.959°** (Leo 18.96°)
- **Ecliptic latitude (independent) = -0.00195° (-7 arcsec)** — correctly ~0, as it must
  be for the Sun by definition.

**Cross-check path:** I then rotated that same Cartesian vector from ecliptic into
equatorial J2000 (using the standard rotation by the J2000 obliquity, 23.439291°, the
same constant Horizons itself reports: 84381.448 arcsec) to get an independently-derived
RA/Dec, **then fed that RA/Dec through `coordinates.ra_dec_to_ecliptic()`'s formula (by
hand)** and compared the recovered longitude/latitude back against the 138.959°/-0.00195°
above.

**Result:**

| Quantity | Independent (Horizons vectors) | Recovered via my RA/Dec formula (hand-computed) | Difference |
|---|---|---|---|
| Ecliptic longitude | 138.959° | 138.901° | **≈ 0.058° ≈ 3.5 arcmin ≈ 209 arcsec** |
| Ecliptic latitude | -0.00195° (-7″) | -0.012° (-43″) | **≈ 0.010° ≈ 36 arcsec** |

**Interpretation — read this carefully:** a few arcminutes of discrepancy from an
**entirely hand-executed** trig calculation (multiple sine/cosine lookups and
multiplications carried to ~5-6 significant figures, no calculator or code execution)
is fully consistent with **accumulated manual rounding error**, not necessarily a bug in
the transform itself. The formula matches the standard published spherical-astronomy
transform (same one used in essentially every ephemeris library), and the result is
correct in sign, quadrant, and order of magnitude (latitude correctly near-zero;
longitude correct to better than a tenth of a degree). But **I cannot certify
arcsecond-level accuracy by hand** — that requires the code to actually run with
double-precision floats, which the sandbox outage still prevents. This is a **PARTIAL
pass at best**: the transform's correctness is well-supported but not proven to the
precision you asked for.

**Separately, as a sanity signal on the external-source frame question (Section 1):**
comparing the RA/Dec I derived here (J2000 astrometric, from Horizons' own geometric
vector) against the RA/Dec theskylive.com displayed earlier this session for the same
date:

| | RA | Dec |
|---|---|---|
| theskylive.com (live snapshot) | 09h 26m 35s | +15° 03′ 07″ |
| Derived from Horizons J2000 vectors (this check) | 09h 25m 34s | +15° 08′ 26″ |
| Difference | ≈ 61s of time ≈ 15.3′ | ≈ 5.3′ |

A ~15-20 arcminute-scale difference is the right order of magnitude for 26 years of
precession (J2000 → 2026) plus aberration/nutation — which is what you'd expect if
theskylive.com is giving apparent-of-date coordinates rather than fixed J2000 ones.
That's supportive of the assumption `coordinates.py` documents, but again: supportive,
not a certified confirmation, and not itself free of the same hand-arithmetic caveat above.

**Not done: requirement 3 in full ("test Sun, Moon, Mars, Jupiter, Saturn across
multiple historical dates").** I validated one body (Sun) at one date, by hand. Testing
5 bodies across multiple dates needs a real test harness running actual code in a loop
— not something to fake by doing five more manual trig derivations. This stays
outstanding until the sandbox (or any Python execution environment) is available.

Sign-boundary testing, retrograde verification: still NOT DONE, same reason (Phase 3).

## PHASE 4 — HISTORICAL ZODIAC PROBLEM: PER-RULE CLASSIFICATION

Lahiri ayanamsa is now explicitly marked in code and here as:

> **NOT VALIDATED AS VARĀHAMIHIRA'S ORIGINAL AYANAMSA.** It is a 20th-century Indian
> government standard (1950s calendar-reform committee, Chitra-paksha convention),
> roughly 1,400 years later than the Bṛhat Saṃhitā. It is used in this codebase only
> as a labeled, flagged approximation — never as a default applied silently.

Every extracted rule has been reviewed and classified by what kind of zodiac/coordinate
convention it actually requires, rather than assuming Vedic = "modern sidereal with
Lahiri ayanamsa" by default:

| Rule(s) | Requires | Reasoning |
|---|---|---|
| BS-17-* (all graha-yuddha rules) | **Planetary relationship independent of zodiac** | Conjunction closeness is the angular separation between two planets. A constant ayanamsa offset cancels out when comparing two bodies to each other — irrelevant whether tropical or sidereal. |
| BS-18-* (Moon north/south of a planet) | **Planetary relationship independent of zodiac** | This is an ecliptic-*latitude* comparison (north/south of the ecliptic), not a longitude/sign placement. Ayanamsa is a longitude shift and doesn't touch latitude. |
| BS-16 (planetary rulership of countries) | **Planetary relationship independent of zodiac** | A fixed signification table ("Mars rules region X"), not a transiting-sign-position rule. No date-dependent zodiac calculation involved at all. |
| BS-20 (planetary triangle/meeting shapes) | **Mostly independent; directional component unresolved** | The geometric-shape and defeat logic is planet-to-planet, but the "which compass sector suffers" step involves a geographic/directional mapping whose zodiacal basis (if any) is not established in the extracted text. **HISTORICAL COORDINATE CONVENTION UNRESOLVED** for that sub-component specifically. |
| BS-19 (planetary year-lord, keyed to weekday of Caitra new moon) | **Sidereal zodiac (calendrical), exact ayanamsa unresolved** | "Caitra" is a named lunisolar calendar month, which in the Hindu calendar tradition is conventionally tied to sidereal solar position — but the extracted chapter doesn't itself specify a precession model. **HISTORICAL COORDINATE CONVENTION UNRESOLVED.** |
| BS-42 (price fluctuation by solar month/sign) | **Sidereal zodiac, exact ayanamsa unresolved** | The rule explicitly keys effects to which zodiac sign the Sun occupies (e.g., a phenomenon "while the Sun is in [sign]"). This unambiguously requires a zodiac-sign determination, and the source is 6th-century, predating any named ayanamsa standard. **HISTORICAL COORDINATE CONVENTION UNRESOLVED** — do not silently apply Lahiri. |
| PT-II-3, PT-II-6 (Ptolemy geography/eclipse locality) | **Tropical zodiac** | Hellenistic astrology's equinox/solstice-anchored triplicity system is unambiguously tropical — this is well-established in the scholarship on the tradition itself, not something the extracted text leaves ambiguous. |
| Gjamasp/grand-conjunction material | **N/A** | Historical report only, no operative calculation in the corpus to classify. |

**Practical consequence:** BS-42 and BS-19 currently cannot be run against a real date
in good conscience, because doing so requires picking *some* ayanamsa, and none is
textually justified. `rule_registry.py` now carries a `zodiac_requirement` field per
rule reflecting this table, and `engines.py` (new) refuses to silently default to
Lahiri for rules marked unresolved — it raises rather than guesses.

## PHASE 5 — TRADITION-SPECIFIC ENGINES

Added `engines.py`: three thin, separate engine objects (`BrihatSamhitaEngine`,
`PtolemyEngine`, `GrandConjunctionEngine`), each only able to see its own tradition's
rules and its own tradition's configuration-detection function (via the Phase-10
`detect_configuration()` dispatcher already in `aspects.py`). The astronomical layer
(`coordinates.py`, `ephemeris_client.py`) stays neutral — it outputs a `PositionRecord`
with raw + tropical + (optional) sidereal fields, and does not itself decide which
fields matter. Each engine then decides what it needs, and refuses rules whose
`zodiac_requirement` is unresolved rather than guessing.

## PHASE 7 — LAHIRI AYANAMSHA MODULE (MODERN/KUNDLI TRACK, SEPARATE FROM PHASE 4)

Added `ayanamsha.py` this pass, in response to a direct request for a better-sourced
planetary-position pipeline for modern sidereal ("kundli") use — this is a DIFFERENT
track from Phase 4's ancient-corpus zodiac question, and does not change any Phase 4
classification. `rule_registry.py`'s BS-19/BS-42/BS-20-directional stay
`sidereal_unresolved`; this module is not applied to them.

**What changed:** `coordinates.py`'s old `approximate_lahiri_ayanamsa_deg()` used a
single anchor (23.85° @ 2000) plus an assumed 50.29″/yr precession rate, neither of
which was independently sourced this session (or any prior one) — it was a plausible-
sounding constant, not a cited one. Replaced with a two-point linear model anchored to
two values actually fetched and read this session:

| Anchor | Value | Source |
|---|---|---|
| 21 Mar 1956, 0:00 TT | 23°15′00″ (23.25°) | India's Calendar Reform Committee decree, via Ron Scott, "The 'Lahiri ayanamsha' and the Sidereal Zodiac" (rscott51.substack.com, Feb 2025) — fetched directly |
| J2000.0 (1 Jan 2000, 12:00 TT) | 23.853222° | "ICRC-compliant" Lahiri value / Swiss Ephemeris `SE_SIDM_LAHIRI` — via WebSearch synthesis of astro.com/Swiss Ephemeris documentation |

Cross-check: the implied rate between the two anchors is ~50.28″/yr (computed in-code,
see `_IMPLIED_ARCSEC_PER_YEAR` in `ayanamsha.py`) — consistent with the commonly-cited
general precession rate, which is a good sign the two sourced points aren't
contradictory, though it doesn't make them independently *proven*.

**What was tried and did NOT work:** attempted to get a live third-party cross-check via
astro.com's own `swetest.cgi` calculator (which does support a Lahiri sidereal mode per
its documentation). Multiple query-parameter guesses for the sidereal-mode flag
(`sid1=`, `sid1=on`, `sid=1`) were all silently dropped by the CGI — confirmed by
inspecting the echoed command line in each response, which never included `-sid1`. The
correct field name for that specific web form was not discovered this session. This
module is therefore sourced to two independent secondary/tertiary citations that agree
with each other, but is **not** independently verified against a live Swiss Ephemeris
calculation. `ayanamsha.py`'s `self_test_placeholder()` documents exactly what that
verification should do once `pyswisseph` or a working `swetest.cgi` query is available.

**Precision honestly stated:** this is a two-point *linear* model. Real precession has a
small secular (non-linear) term that Swiss Ephemeris's actual Lahiri implementation
captures via the full Lieske 1976 precession theory (plus Wahr 1980 nutation for the
"true"/1985-revised variant) — neither is implemented here. Expected error from
linearity alone is on the order of arcseconds to tens of arcseconds across the
1900–2100 range this model is meant for — fine for identifying which zodiac sign a
planet is in, not fine for sub-arcminute work (exact aspect degrees, house cusps).

**Status: PARTIAL, same as everything else in this project.** Better-sourced than what
it replaced, internally consistent, not independently executed or cross-checked against
a primary calculator.

## PHASE 8 — LIVE INDEPENDENT CROSS-CHECK OF THE LAHIRI MODULE (this pass)

Direct continuation of Phase 7. Three things changed this pass, in order:

**1. Environment re-diagnosed, not just re-declared blocked.** Per instruction, tried
three distinct execution paths before treating this as unfixable:
- `mcp__workspace__bash` direct call: same "Not enough disk space to set up the
  workspace" error as every prior attempt.
- `Agent` with `isolation: "worktree"`: failed immediately with `Failed to resolve base
  branch "HEAD": git rev-parse failed` — this workspace is a Cowork scratchpad folder,
  not a git repository, so this isolation mode cannot attach to it.
- `Agent` with `isolation: "remote"`: failed with the identical git-repo error.
Conclusion, unchanged from Revision 2: no code-execution path reachable from inside this
conversation. This is a real, reproducible, host-level constraint — not a stand-in for
"didn't try." `ayanamsha.py` and `tests/test_ayanamsha.py` remain unexecuted by an
actual Python interpreter.

**2. The astro.com `swetest.cgi` blocker from Phase 7 was resolved.** The correct
mechanism turned out to be a raw-flag passthrough parameter (`arg=`, discovered by
fetching the CGI's own `-h` help text via `arg=-h&p=0` — a real primary-source
documentation fetch, not a guess) rather than the named-field guesses tried previously
(`sid1=`, `sid=1`, etc.), which were all silently dropped. Once found, this gave direct,
live access to Astrodienst's reference Swiss Ephemeris implementation (version 2.10.03)
for the exact test-vector dates originally requested.

**3. 11 live queries executed against Swiss Ephemeris, sidereal mode 1 ("Lahiri"),
covering 1900–2050 (see `lahiri_crosscheck.csv` for the full table with sources):**

| Date | JD (UT) | Our linear model | Swiss Ephemeris (live) | Diff (arcsec) | Classification |
|---|---|---|---|---|---|
| 1900-01-01 00:00 | 2415020.5 | 22.475466° | 22.465373° | +36.3″ | EXPECTED_METHODOLOGICAL_DIFFERENCE |
| 1956-01-01 00:00 | 2435473.5 | 23.246982° | 23.247365° | −1.4″ | ROUNDING |
| 1956-03-21 00:00 (our anchor date) | 2435553.5 | 23.250000° | 23.250221° | −0.8″ | EXPECTED_METHODOLOGICAL_DIFFERENCE (decree instant vs. UT midnight) |
| 1956-06-01 00:00 | 2435625.5 | 23.252716° | 23.252598° | +0.4″ | ROUNDING |
| 1956-09-22 00:00 | 2435738.5 | 23.256978° | 23.256815° | +0.6″ | ROUNDING |
| 1956-12-31 00:00 | 2435838.5 | 23.260751° | 23.260637° | +0.4″ | ROUNDING |
| 2000-01-01 00:00 | 2451544.5 | 23.853205° | 23.853204° | +0.0″ | ROUNDING |
| 2000-01-01 12:00 (our anchor date — J2000.0) | 2451545.0 | 23.853222° | 23.853222° | 0.0″ | exact by construction, confirmed live |
| 2026-01-01 00:00 | 2461041.5 | 24.211442° | 24.221810° | −37.3″ | EXPECTED_METHODOLOGICAL_DIFFERENCE |
| 2026-08-12 00:00 | 2461264.5 | 24.219860° | 24.231567° | −42.1″ | EXPECTED_METHODOLOGICAL_DIFFERENCE |
| 2050-01-01 00:00 | 2469807.5 | 24.542111° | 24.559827° | −63.8″ | EXPECTED_METHODOLOGICAL_DIFFERENCE |

**Diagnosis of the pattern (per instruction: understand before touching the
implementation):** error is near-zero at both anchors and grows outward monotonically
in both directions. This is the signature of a LINEAR chord fit to a curve with a real
secular (non-linear, slowly-increasing) precession term — Swiss Ephemeris's Lahiri mode
uses the full Lieske 1976 (IAU 1976) precession theory, which captures that curvature; a
straight line between two points on that curve is exact at the two points and diverges
elsewhere, by construction. This is classified **EXPECTED_METHODOLOGICAL_DIFFERENCE**,
not IMPLEMENTATION_ERROR, ROUNDING, or SOURCE_DISCREPANCY — the code is doing exactly
what a linear model does; the model's simplicity (not a defect in executing it) is the
limitation. **No formula bug was found or fixed.** The implementation was not modified
based on this result, per instruction not to change the code until the discrepancy is
understood.

**Practical reading:** as of today (2026-08-12), the linear model is already ~42 arcsec
(~0.7 arcmin) off from Swiss Ephemeris's Lahiri — irrelevant for identifying which
30-degree zodiac sign a planet occupies (this project's actual use case for the modern/
kundli track), not adequate for sub-arcminute work.

**4. Methodology distinction discovered and corrected.** Swiss Ephemeris's own `-h` help
text (fetched directly — primary source) shows it has *multiple* named "Lahiri" sidereal
modes, not one: mode 1 "Lahiri" (default), mode 43 "Lahiri 1940", mode 44 "Lahiri VP285
(1980)", mode 46 "Lahiri ICRC". Querying all four live at J2000.0 (this pass):

| SE mode | Label | Value | vs. mode 1 |
|---|---|---|---|
| 1 | Lahiri (default) | 23°51'11.6009″ = 23.853222° | — (reference) |
| 43 | Lahiri 1940 | 23°50'18.4322″ = 23.838453° | −53.2″ |
| 44 | Lahiri VP285 (1980) | 23°51'34.6009″ = 23.859611° | +23.0″ |
| 46 | Lahiri ICRC | 23°51'10.5089″ = 23.852919° | −1.1″ |

Phase 7's original write-up had labeled the 23.853222° anchor "the ICRC-compliant
value" based on a WebSearch synthesis. **That label was imprecise and has been
corrected in `ayanamsha.py`:** the value actually matches SE's *default* mode-1
"Lahiri" almost exactly, not its distinctly-numbered "Lahiri ICRC" mode (which differs
by ~1.1 arcsec). The numeric anchor itself is unaffected and is now *better* sourced
(confirmed live against the SE reference implementation) — only the methodological
label was wrong, and this is now documented rather than silently carried forward.

**5. Deliverables added this pass:**
- `lahiri_crosscheck.csv` — the full 11-row table above in machine-readable form.
- `ayanamsha.py` — updated with the corrected methodology labeling, the baked-in
  `SWISSEPH_MODE1_REFERENCE` dataset, a `cross_check()` function that reproduces the
  table above from the live-fetched constants, and `methodology_status()` (see below).
- `tests/test_ayanamsha.py` — real `unittest` code, one test per requested date, each
  asserting against the live-fetched Swiss Ephemeris value with a tolerance matching
  the *measured, understood* error at that date (tight near the anchors, wider at the
  range extremes) — not executed (see point 1), but every expected value and every
  tolerance was hand-checked against the arithmetic above before being committed to the
  file. Also includes a regression test (`TestRegressionNoHardcodedSinglePointConstantInCoordinates`)
  that reads `coordinates.py`'s source and fails if it ever stops delegating to
  `ayanamsha.py` or reintroduces a hardcoded single-point constant.

**6. `methodology_status()` added to `ayanamsha.py`,** returning `PARTIALLY_VALIDATED`
(not `VALIDATED` — the code has never executed, and the model has a measured,
non-negligible systematic error away from its anchors; not `UNVERIFIED` either — real
independent reference data now exists and the model's behavior against it is fully
characterized).

**7. Historical-rule safeguard reconfirmed untouched:** `rule_registry.py`'s BS-19,
BS-42, and BS-20 remain `sidereal_unresolved`. Nothing in this pass applied Lahiri (in
any of its four SE variants) to the ancient Bṛhat Saṃhitā corpus.

```
LAHIRI IMPLEMENTATION
---------------------
Source methodology:      DOCUMENTED — two-point linear model, explicitly labeled as an
                          approximation, not presented as Varāhamihira's or any single
                          historical algorithm; SE mode-1 "Lahiri" identified as the
                          specific target convention (distinct from SE modes 43/44/46).
Anchor validation:       CONFIRMED LIVE — both anchors (1956 decree, J2000.0) verified
                          this pass against a live Swiss Ephemeris query, not just
                          secondary sources.
Execution:               NOT EXECUTED — sandbox and two alternate agent-isolation paths
                          all unreachable this session (see point 1 above); every number
                          in this report was hand-computed and cross-checked, not
                          produced by running the .py files.
Independent cross-check: DONE — 11 dates (1900-2050) checked against live Swiss
                          Ephemeris 2.10.03, sidereal mode 1 "Lahiri"; see
                          lahiri_crosscheck.csv.
Multi-date validation:   DONE — near-anchor error 0.4-1.4″; range-extreme error 36-64″,
                          fully explained as expected linear-model curvature error, not
                          a bug (see diagnosis above).
Historical applicability: NOT APPLICABLE BY DESIGN — this module is scoped to modern/
                          kundli use only; BS-19/BS-42/BS-20 remain sidereal_unresolved.

PRODUCTION STATUS:
NOT READY — mathematically implemented and now independently, live cross-checked, but
the code itself has never executed, and the linear model carries a measured ~36-64
arcsec systematic error away from its anchors (fine for zodiac-sign-level use, not for
sub-arcminute precision work).
```

## PHASE 9 — REPLACING THE LINEAR MODEL AS PRODUCTION-PRIMARY

Direct response to explicit instruction: the linear approximation must not remain the
production Lahiri engine. What changed this pass:

**1. Environment re-checked again, honestly, before anything else.** Three paths tried:
direct `mcp__workspace__bash` (same disk-space provisioning error as every prior
attempt), `Agent(isolation="worktree")` (same "no git repository" error), `Agent(isolation="remote")`
(same). No new outcome. This is stated again rather than assumed, per instruction —
nothing below claims execution that didn't happen.

**2. Methodology selection, decided from source documentation BEFORE any accuracy
comparison (per explicit instruction not to pick a variant based on prediction
performance).** Fetched Dieter Koch's (Swiss Ephemeris co-author) canonical ayanamsha
explainer live via the Claude-in-Chrome browser tool (the page requires JavaScript; a
plain fetch returns only a bot-check shell) —
https://www.astro.com/astrology/in_ayanamsha_e.htm. That page lists exactly ONE "Lahiri
Ayanamsha" (no separate ICRC/1940/VP285 entries) and describes it as what "Hindu
astrologers and their western disciples mostly use." Combined with the numeric fact
(Phase 8) that SE's plain mode-1 "Lahiri" — not mode 46 "ICRC" — is the one matching the
original 1956 Calendar Reform Committee decree value to <1 arcsec, this project selects
**Swiss Ephemeris sidereal mode 1 ("Lahiri", the default)** as its methodology. Modes 43
("Lahiri 1940"), 44 ("Lahiri VP285"), and 46 ("Lahiri ICRC") remain explicitly
distinguished and unused, documented with their numeric offsets from mode 1 in
`ayanamsha.py`.

**3. Architecture: astronomical and sidereal layers kept explicitly separate**, per
instruction not to let Swiss Ephemeris creep into the planetary-position role:

```
JPL Horizons (ephemeris_client.py)  ->  raw TROPICAL planetary longitude
Swiss Ephemeris (ayanamsha.py)      ->  ayanamsha OFFSET value only (one angle, never a planetary position)
coordinates.tropical_to_sidereal_lahiri()  ->  sidereal longitude = tropical - ayanamsha
rashi_nakshatra.py (new)            ->  Rāśi / Nakshatra classification
```

JPL Horizons was not touched and remains the sole source of planetary positions.

**4. Linear model demoted to fallback-only; live Swiss Ephemeris query is now the
primary path.** `ayanamsha.lahiri_ayanamsha_deg()` now tries a live HTTP query to
`swetest.cgi` (mode 1, "Lahiri") first — the actual reference implementation computing
the actual answer, not an approximation of it — and only falls back to the two-point
linear model if that fails, FLAGGING which path produced a given result via the new
`source` field (`"live_swisseph"` vs. `"linear_fallback"`) rather than silently
substituting. The `-bj<JD>` input flag (absolute Julian Day, confirmed empirically to be
interpreted as TT) is used to avoid a separate calendar-conversion function.

**5. A hand-built precession-polynomial replacement was attempted and explicitly
rejected, not silently dropped.** Before choosing the live-query design, the standard
IAU 1976 (Lieske) general-precession-in-longitude polynomial was hand-evaluated against
the live 1900 reference point: it produced a ~32.9 arcsec error, not a clear improvement
over the simple linear model's ~36.3 arcsec error at the same date. Rather than present
an unvalidated formula as a fix, this was abandoned in favor of querying the real
implementation directly — see `ayanamsha.py`'s "WHY NOT A HAND-BUILT PRECESSION
FORMULA" section for the full reasoning, including the plausible explanation (per Koch's
own documentation) that Lahiri's official definition doesn't cleanly follow a clean
modern precession formula in the first place.

**6. `pyswisseph` (the first-choice option per instruction) could not be used.**
Installing it requires `pip install pyswisseph`, which requires a working shell — this
session's sandbox is unavailable. The live-CGI path is the closest honest substitute:
still the real Swiss Ephemeris algorithm, reached over HTTP instead of a local library
because that's what was actually reachable. `DEPENDENCIES.md` records this plainly and
recommends `pyswisseph` as the correct long-term production path once local execution is
available.

**7. Cross-validation extended to the full requested date list.** 1950 and 1975 added
this pass (live-fetched) to the existing 1900/1956/2000/2026/2050 set — 13 points total,
covering every year explicitly requested. Notably, 1975 sits INSIDE the two anchors
(1956–2000), not beyond them, and still shows a real ~13.6 arcsec error — demonstrating
the linear model's curvature error is not purely an extrapolation artifact.

| Date | Fallback model | Swiss Ephemeris (live) | Diff (arcsec) | Classification |
|---|---|---|---|---|
| 1950-01-01 00:00 | 23.164334° | 23.157808° | +23.5″ | EXPECTED_METHODOLOGICAL_DIFFERENCE |
| 1975-01-01 00:00 | 23.508770° | 23.512558° | −13.6″ | EXPECTED_METHODOLOGICAL_DIFFERENCE |

(Full 13-row table, all sources: `lahiri_crosscheck.csv`.)

**8. Boundary conditions tested (item 10).** New module `rashi_nakshatra.py` (Rāśi +
Nakshatra classification layer) with `tests/test_rashi_nakshatra.py` covering: exact
0°/30° Rāśi boundaries, exact Nakshatra-width boundaries, pada boundaries, 360°→0°
wraparound (including negative longitudes and floating-point noise just under 360° that
must snap to 0° rather than misclassify into the last sign by a hair), and end-to-end
integration tests placing a simulated tropical longitude exactly on/near a sidereal
boundary. All hand-traced against the fixed-width-bin arithmetic; not executed (same
blocker as everything else).

**9. Regression test preserved and extended** (item 11) —
`TestRegressionNoHardcodedSinglePointConstantInCoordinates` in `tests/test_ayanamsha.py`
is unchanged and still guards `coordinates.py` against reverting to a hardcoded ayanamsha
constant. New tests this pass (`TestLiveQueryParsing`, `TestFallbackWiring`) exercise the
live-query parsing logic against REAL captured `swetest.cgi` response text via mocked
`urlopen` — a real test of the parsing code, without depending on live network access
inside the test suite itself (unit tests should not require network availability to be
deterministic).

**10. Historical-rule safeguard reconfirmed untouched (item 15).** `rule_registry.py`'s
BS-19, BS-42, BS-20 remain `sidereal_unresolved`. Nothing in this pass applied any Lahiri
variant to the ancient Bṛhat Saṃhitā corpus.

**11. `methodology_status()` updated but deliberately still returns
`PARTIALLY_VALIDATED`**, per explicit instruction that it must remain so until the
implementation has actually executed and the independent comparisons have actually been
run (not just hand-verified) and passed. Neither has happened.

### FINAL ACCEPTANCE CRITERIA (user's exact checklist, honestly marked)

```
[x] Linear approximation removed from production path
    -- demoted to fallback-only; live Swiss Ephemeris query is now primary.
[~] Computational Lahiri implementation installed
    -- "installed" in the sense of a live query to the real SE binary; pyswisseph
       itself could not be installed (no shell). See DEPENDENCIES.md.
[x] Exact Lahiri variant documented
    -- mode 1 "Lahiri", selected on source-documentation grounds, distinguished from
       modes 43/44/46 with numeric offsets recorded.
[x] Swiss Ephemeris cross-check performed
    -- 13 live queries this session + all prior pass's queries.
[x] Multiple historical dates cross-checked
    -- 1900, 1950, 1956 (x4), 1975, 2000 (x2), 2026 (x2), 2050.
[~] Boundary tests pass
    -- written and hand-traced correct; NOT executed (see below).
[ ] Python implementation actually executes
    -- NOT DONE. Sandbox + 2 agent-isolation paths all unreachable this pass, same as
       every prior pass. This is the single biggest gap between current status and
       "production ready."
[~] Regression tests pass
    -- written, hand-verified against actual file contents; NOT executed.
[x] Astronomical and sidereal layers remain separate
    -- JPL Horizons untouched; Swiss Ephemeris used only for the ayanamsha offset.
[x] Historical BS rules remain unresolved
    -- BS-19/BS-42/BS-20 untouched.
[x] No methodology was selected based on prediction performance
    -- mode 1 selected from Koch's documentation + decree-value agreement, before any
       accuracy comparison; the precession-polynomial alternative was rejected on
       validation grounds, not on "which gives better history."
```

`[~]` = designed and believed correct, hand-verified where verification without
execution is possible, but NOT proven by actual execution — the honest middle state
between done and not-done that this checklist needs, since several items literally
cannot be marked `[x]` without a working Python interpreter.

```
LAHIRI IMPLEMENTATION
---------------------
Source methodology:      DOCUMENTED AND SELECTED ON METHODOLOGICAL GROUNDS — SE mode 1
                          "Lahiri", chosen from Dieter Koch's canonical documentation and
                          agreement with the 1956 CRC decree value, before any backtest.
Anchor validation:       CONFIRMED LIVE against Swiss Ephemeris 2.10.03.
Execution:               NOT EXECUTED — sandbox and two alternate agent-isolation paths
                          all unreachable this pass, identical to every prior attempt.
Independent cross-check: DONE for the fallback model — 13 dates (1900-2050) vs. live
                          Swiss Ephemeris; NOT DONE for the live-query path's own code
                          (parsing logic hand-verified against real captured responses,
                          not executed).
Multi-date validation:   DONE (13 dates) for the fallback model's accuracy; boundary
                          tests written and hand-traced, not executed.
Historical applicability: NOT APPLICABLE BY DESIGN — BS-19/BS-42/BS-20 remain
                          sidereal_unresolved, untouched.

PRODUCTION STATUS:
NOT READY — the architecture and methodology are now sound and source-justified (live
Swiss Ephemeris as primary, linear model as an explicitly-flagged fallback, JPL and SE
layers kept separate), but no code in this project — this module or any other — has
executed in a Python interpreter this session. That remains the single blocking gap.
```

## PHASE 10 — EXPERIMENTAL FORECASTING UNLOCKED (explicit user authorization)

`forecast.py` (+ `panchang.py`, `predictions_schema.sql`, `evaluate_forecasts.py`)
added: FORECASTING moves from LOCKED to **EXPERIMENTAL**, per explicit instruction, with
every listed safeguard implemented as real code (rule-registry-only lookups, hard
exclusion of `sidereal_unresolved` rules, an empty, data-driven geography allowlist that
cannot manufacture a country mapping, production mode that raises
`ProductionCalculationUnavailable` rather than silently using the linear ayanamsha
fallback, confidence derived only from `historical_sample_size`, immutable prediction
records with a DB-level trigger rejecting UPDATEs).

Environment re-checked again before any of this: direct sandbox (same disk-space
error), worktree-isolated agent (same missing-git-repo error), remote-isolated agent
(same). No change. `forecast.py` itself has not executed.

**A real test run WAS hand-executed against live data** (not fabricated, not run as
code) — see `FORECAST_RUN_2026_09_USA.md`: live JPL Horizons positions for 2026-09-01,
live Swiss Ephemeris ayanamsha, real Rāśi/Nakshatra/partial-Panchang classification, and
a full rule evaluation. Result: **NO FORECAST**, for both USA (blocked by the empty
geography allowlist — no rule in the registry documents any mechanism connecting to a
modern country) and GLOBAL scope (the real planetary configuration's closest pairing,
Mercury-Jupiter, is 29° apart — nowhere near any conjunction-class threshold, and every
other candidate rule is either `sidereal_unresolved` or has no implemented detector).
This is treated as a genuine, useful result, not a failure to produce output — it
demonstrates the safeguards functioning as designed on real data.

## PHASE 6 — VALIDATION GATE

- [x] coordinate reference frames documented (Phase 1)
- [ ] automated multi-body testing complete
- [ ] multi-date testing complete
- [ ] sign-boundary testing complete
- [ ] retrograde verification complete
- [x] independent-source comparison complete *for one body/date, hand-executed —
      strengthened this pass, but not the automated version Phase 3 still requires*
- [x] historical zodiac convention documented per rule (Phase 4)
- [ ] rule engine successfully matches at least one historical configuration
- [ ] first blind historical backtest completed

**5 of 9 gate items still open. Prospective forecasting remains LOCKED — not "close,"
genuinely blocked on code execution that hasn't happened.**

---

## VALIDATION GATE TABLE (Step 12 format)

| Validation Gate | Status | Evidence |
|---|---|---|
| Coordinate transformation | NOT TESTED | Formula hand-diagnosed as rounding-error-consistent (8.6″/6″ after precision increase, down from 3.5′), which is supportive but explicitly not a code-execution result. `test_validation_suite.py` written, not run. |
| Multi-body | NOT TESTED | No execution environment reachable (see three failed attempts above). |
| Multi-date | NOT TESTED | Same. |
| Sign boundaries | NOT TESTED | No automated boundary test has been run; code path (`int(lon // 30)`) inspected but not exercised. |
| Retrograde | NOT TESTED | `aspects.is_retrograde()` exists, never run against real data. |
| Reference-frame audit | PARTIAL | Horizons VECTORS fully self-documented (J2000 ecliptic, geometric, TDB, geocentric). Horizons OBSERVER and theskylive.com frames could not be confirmed — OBSERVER returned empty on 3 attempts across two report revisions; theskylive.com frame inferred only, marked UNRESOLVED in Phase 1 table. |
| Historical zodiac conventions | PARTIALLY UNRESOLVED | Per-rule classification done (Phase 4): BS-16/17/18 zodiac-independent; BS-19/42/part-of-20 explicitly HISTORICALLY_UNRESOLVED and blocked; Ptolemy tropical by established convention. No Lahiri default introduced. |
| Rule-engine execution | NOT TESTED | Gated on astronomical validation per Step 11 of your instructions — correctly not attempted yet. |
| Historical backtest | NOT TESTED | Same gating; zero cases run. |

# FINAL STATUS

**ASTRONOMICAL ENGINE:** NOT READY (VECTORS path works and is documented; OBSERVER path
unverified/likely broken; no code has actually executed this session)

**COORDINATE VALIDATION:** PARTIAL (formula strongly supported by a diagnosed,
precision-shrinking hand round-trip test; automated multi-body/multi-date/boundary/
retrograde suite not run)

**HISTORICAL ZODIAC MODEL:** UNRESOLVED for BS-19, BS-42, and the directional component
of BS-20 (explicitly, per rule); VALIDATED-BY-CONVENTION for Ptolemy (tropical, well-
established); N/A for grand-conjunction material; not applicable to the
zodiac-independent Bṛhat Saṃhitā rules (BS-16, 17, 18) since they don't need one

**BṚHAT SAṂHITĀ ENGINE:** NOT READY (registry populated for 6 chapters, but 3 of those
rules can't run without resolving an ayanamsa question that has no textual answer yet)

**PTOLEMY ENGINE:** NOT READY (registry populated for Book II Ch. III/VI only;
zodiac convention resolved, but no automated coordinate validation yet)

**BACKTEST ENGINE:** NOT READY (design exists; zero historical cases actually run)

**PROSPECTIVE FORECAST: LOCKED**

**Every remaining uncertainty, explicitly:**
1. Whether `coordinates.py`'s transform holds to arcsecond precision across bodies/dates
   — only one body, one date, hand-checked.
2. theskylive.com's actual reference frame — inferred, not documented by the source.
3. Whether the JPL Horizons OBSERVER endpoint is fixable or has to be abandoned in favor
   of VECTORS-only — unknown, the failure mode wasn't visible from this environment.
4. Sign-boundary behavior — untested.
5. Retrograde detection — untested.
6. The exact ayanamsa (if any) implied by Varāhamihira's own text — unresolved, and may
   remain unresolved without independent Indological/history-of-astronomy scholarship
   beyond what the extracted chapters state.
7. Whether BS-20's directional/geographic component has any zodiacal basis at all, or is
   a purely compass-geographic rule — unresolved.
8. Light-time/aberration-scale effects on any future apparent-position comparisons —
   identified as a real factor in Phase 1, not yet quantified for any specific case.
9. RESOLVED (Phase 8): `ayanamsha.py`'s two anchor values are now confirmed live against
   Swiss Ephemeris (`swetest.cgi`, mode 1 "Lahiri") — the query-parameter blocker from
   Phase 7 was found and fixed. What remains open is narrower: the linear MODEL's known
   ~36-64 arcsec error away from its anchors (quantified, understood, not fixed — see
   Phase 8), and the fact that `ayanamsha.py`'s own code has still never executed in a
   Python interpreter.

---

## Phase 11 — Astrowatch-2 port: first real code execution (this pass)

Context: this pass ported the gmare/ codebase into the `Astrowatch-2` GitHub repository
(`astrowatch/` subdirectory) as a prerequisite for building the historical event
database. Code execution, which was unreachable in every prior pass (disk-space
provisioning error, confirmed repeatedly), is available in this session's sandbox.
Every module below was actually run for the first time in this project's history.

**Test suites (actually executed):**
- `python3 -m unittest tests.test_ayanamsha` — 25/25 pass.
  - One real bug found by execution: `test_approximate_lahiri_function_delegates_not_hardcodes`
    failed on first run. Diagnosis (not assumption): the regex
    `r"def approximate_lahiri_ayanamsa_deg\(.*?\):(.*?)(?:\ndef |\Z)"` didn't
    account for the function's `-> float` return-type annotation between `)` and `:`,
    so `.*?` (DOTALL) skipped past the real signature and anchored on the next
    unrelated `():` it could find (`self_test()` at EOF), capturing the wrong body.
    Confirmed via direct inspection that `coordinates.py` line 222 correctly reads
    `return lahiri_ayanamsha_deg_for_year(year).ayanamsha_deg` — this was a test bug,
    not a source regression. Fixed the regex to tolerate an optional `-> Type`
    annotation; documented the fix in a comment in the test file itself.
- `python3 -m unittest tests.test_rashi_nakshatra` — 20/20 pass, no code changes needed.
- `python3 test_validation_suite.py` — ran; all JPL Horizons calls failed cleanly with
  `Tunnel connection failed: 403 Forbidden` (see network diagnosis below). Script
  correctly reported FAIL/INVESTIGATE and did not fabricate results.

**Network diagnosis (this sandbox specifically):**
`curl -v https://api.github.com` (and astro.com, ssd.jpl.nasa.gov, raw.githubusercontent.com)
returns `HTTP 403` from a local proxy (`localhost:3128`) with response header
`X-Proxy-Error: blocked-by-allowlist` — this is the sandbox's own egress policy, not a
failure on astro.com's or JPL's side. `github.com` and `pypi.org` ARE allowlisted
(confirmed: `git clone`/`git ls-remote` and `pip install` both succeed). Practical
effect: `ayanamsha.fetch_live_swisseph_lahiri_ayanamsha_deg()` and every
`ephemeris_client.py` function that calls Horizons will deterministically fail in this
specific sandboxed environment and fall through to the documented fallback/error paths
— this is an environment constraint, not a newly discovered code defect.

**`pyswisseph` installed and run locally for the first time** (`pip install pyswisseph`
succeeded — version 2.10.3.2, pypi.org being allowlisted). Cross-checked against the
13-point `SWISSEPH_MODE1_REFERENCE` table already baked into `ayanamsha.py` (itself
live-fetched from astro.com in an earlier pass): disagreement up to **17.5 arcsec**,
non-monotonic across dates (not a simple constant offset or TT/UT drift pattern).
Diagnosed cause: no local `.se1` Swiss Ephemeris data files are present, and
`swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH)` silently returns `retflag == swe.FLG_MOSEPH`
— i.e. pyswisseph is silently running in the lower-precision Moshier analytical-ephemeris
mode, not the full file-based Swiss Ephemeris the live astro.com tool almost certainly
uses. The `.se1` files themselves could not be downloaded to close this gap — astro.com
is blocked by the same proxy allowlist described above. Classified:
**EXPECTED_METHODOLOGICAL_DIFFERENCE** (ephemeris backend precision), not a Lahiri
sidereal-mode disagreement and not a code bug. `ayanamsha.py`'s `methodology_status()`
has been updated to describe this precisely instead of the stale "NOT EXECUTED" claim.

**Other modules executed, all produced correct real output, no code changes needed:**
`rashi_nakshatra.py` (`rashi_for_longitude`, `nakshatra_for_longitude`), `panchang.py`
(`compute_partial_panchang`), `aspects.py` (`classify_grahayuddha`, `detect_configuration`),
`rule_registry.py` (19 rules total; confirmed via execution, not just inspection, that
all 8 BS-19/BS-20/BS-42 rule IDs still carry `zodiac_requirement = "sidereal_unresolved"`),
`engines.py` (imports cleanly), `pipeline.py` (`demo_with_sample_positions()` runs
end-to-end and produces real rule matches from its labeled-as-illustrative sample data),
`predictions_schema.sql` (applies cleanly via `sqlite3` stdlib module),
`evaluate_forecasts.py` (`summarize` runs correctly against a freshly-initialized empty
predictions DB, returns `{}`).

**One AUDIT.md item found stale, not a new bug:** `ephemeris_client.fetch_all_classical_bodies()`
was flagged CRITICAL in `AUDIT.md` for using the broken OBSERVER endpoint. Direct
inspection of the ported file shows this was already fixed in a prior pass (it calls
`fetch_ecliptic_vectors()`, the confirmed-working VECTORS path) — the audit table
itself was just never updated to reflect that fix. Corrected in `docs/ASTRONOMY_AUDIT.md`.

**`forecast.py`'s CLI (`main()`) still correctly refuses full end-to-end execution** —
it depends on `ephemeris_client.py`, which cannot reach JPL Horizons in this specific
sandbox (proxy allowlist, as above), so its refusal remains accurate, not overly
conservative, in this environment.

Net effect on validation status: still **PARTIALLY_VALIDATED**, not VALIDATED — but the
reasons have changed from "nothing has ever executed" to "the intended primary live-data
path is blocked by this specific sandbox's network policy, and the one available local
alternative (pyswisseph) only reaches reduced Moshier precision here." Everything that
CAN run in this environment (all unit tests, all pure-computation modules, the schema)
has now actually run, for the first time, and passed.
