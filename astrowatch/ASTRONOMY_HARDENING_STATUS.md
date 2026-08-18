# Astronomy Calculation Hardening — Phase 5 findings

Written during the "VALIDATION HARDENING BEFORE BT-002" pass. Investigates exactly
why BT-001 reported "every prediction used ayanamsha.py's existing linear fallback,"
and what is/isn't fixable about that in this specific sandboxed environment.

## 1. What's installed

- `pyswisseph` 2.10.3.2 (`pip show pyswisseph`), the official Python binding to the
  Swiss Ephemeris C library.
- No `.se1` data files anywhere on the filesystem (`find / -iname "*.se1"` returns
  nothing). Without them, `swe.calc_ut()` silently falls back to its bundled Moshier
  semi-analytic ephemeris (confirmed via the `FLG_MOSEPH` bit on every returned
  `retflag`, both for modern and ancient dates — see `backtest/ephemeris_source.py`).

## 2. Can real `.se1` files be obtained in this sandbox? (tested, not assumed)

| Attempt | Result |
|---|---|
| `pip download swisseph-data` (hypothetical bundled-data package) | No such PyPI package exists. |
| `curl https://www.astro.com/ftp/swisseph/ephe/` (bash) | Blocked (`000`, same proxy-allowlist as every other non-github/pypi host documented throughout this project). |
| `mcp__workspace__web_fetch` to the same astro.com page | **Succeeded** — confirms `web_fetch` has broader domain reach than the bash sandbox (consistent with prior findings in this project). Page states real files live at `github.com/aloistr/swisseph/tree/master/ephe` or a Dropbox folder (11-29 GB for full asteroid coverage). |
| `git clone https://github.com/aloistr/swisseph.git` (bash) | `fetch-pack: unexpected disconnect while reading sideband packet` — connection drops mid-transfer. |
| `web_fetch` to `github.com/aloistr/swisseph/tree/master/ephe` | Empty response — GitHub's file browser is JavaScript-rendered; a non-JS fetch gets nothing usable. |
| `web_fetch` to `raw.githubusercontent.com/aloistr/swisseph/master/ephe/seleapsec.txt` | Empty response — `raw.githubusercontent.com` is blocked even via the broader-reach tool. |

**Conclusion: real `.se1` files are not obtainable through any tool available to this
session in this sandbox.** They were NOT approximated, synthesized, or faked as a
substitute — that would make the whole Moshier-vs-file-based distinction meaningless.

## 3. What was built instead: a clean, non-fabricating configuration mechanism

`backtest/ephemeris_source.configure_ephemeris_path()`:
- Checks the `ASTROWATCH_EPHE_PATH` environment variable, then a local `backtest/ephe/`
  directory, for `.se1` files.
- If found: calls `swe.set_ephe_path()` so every subsequent calculation in this
  project automatically upgrades to full file-based precision — zero other code
  changes needed.
- If not found (the case in this sandbox, confirmed by running it — see below):
  returns a structured "not configured, here's why" result, and every calculation
  continues to honestly report `ephemeris_precision_flag='MOSEPH'`, exactly as BT-001
  already did.

Run in this sandbox just now:
```json
{
  "configured": false,
  "path_checked": ".../astrowatch/backtest/ephe",
  "source": "default_local_dir",
  "se1_files_found": 0,
  "reason": "no directory found -- ... none were obtainable here"
}
```

Anyone running this project on a machine where they've legitimately obtained real
`.se1` files (from the sources above) can set `ASTROWATCH_EPHE_PATH` and get full
Swiss-Ephemeris-file precision with no code change — this is the "dependency/
configuration mechanism" requested by the hardening spec.

## 4. Supported / unsupported date ranges

- **Ecliptic longitude/latitude (pyswisseph, Moshier mode):** the Moshier analytical
  model is valid across a very wide historical range (roughly 3000 BCE - 3000 CE per
  its own documentation) and produced plausible output for every date tested in this
  project, including 79 CE (see the original BT-001 feasibility test).
- **Lahiri ayanamsha (the OFFSET between tropical and sidereal, a SEPARATE
  calculation from planetary longitude — see `ayanamsha.py`):** BT-001's linear
  fallback model is cross-validated (`ayanamsha.cross_check()`) only against
  reference points spanning **1900-2050** (`ayanamsha.SWISSEPH_MODE1_REFERENCE`).
  Outside that window the fallback is an untested extrapolation — BT-001 already
  flagged the 9/290 predictions this affected (`astronomy_extrapolated_unvalidated`).
  This is unchanged by this hardening pass (see Phase 6 below for how BT-002 will
  handle this rather than silently including it).
- **Rules that don't need the ayanamsha at all:** the newly-implemented Ch. XVIII
  lunar-pass and Ch. XVII graha-yuddha rules are `zodiac_independent` (a constant
  offset cancels out of a longitude *difference*, and doesn't affect latitude at
  all — see `rule_registry.py`), so they are NOT subject to this validated-range
  caveat. Only rules whose interpretation depends on an absolute sidereal placement
  are affected.

## 5. Moshier fallback behavior — confirmed, not assumed

Every `swe.calc_ut()` call in this sandbox returns a `retflag` with the `FLG_MOSEPH`
bit set, for both a modern date (2004-12-26) and an ancient one (79 CE) — re-verified
in this pass via `backtest/ephemeris_source.py`'s own `self_test()` and the new
`compute_full_positions()` function. This is silent-by-design in `pyswisseph` itself
(it does not raise or warn); this project's own code is what surfaces it
(`ephemeris_precision_flag` on every `Prediction` row).

## 6. Lahiri calculation — unchanged, already documented

`ayanamsha.py` was not modified this pass. Its primary path (live query to
`astro.com/cgi/swetest.cgi`) is network-blocked here for the same proxy-allowlist
reason as everything else in section 2; its fallback path (linear two-anchor model)
is what BT-001 used and remains what BT-002 will use unless a future pass adds a
genuinely different, textually-justified mechanism. See `ayanamsha.py`'s own
docstring for the full accuracy characterization — nothing here supersedes it.

## 7. Panchang — unchanged

`panchang.py` was not modified. It remains PARTIAL (tithi/vara/lunar-nakshatra only;
yoga and karana are not implemented), as documented in that file's own docstring.

## 8. Timezone conversion — verified working correctly, historical dates included

`backtest/predictor.py`'s existing `_local_to_utc_hour()` uses Python's `zoneinfo`
with the `tzdata` package (IANA database version **2026b**, confirmed installed).
Spot-checked in this pass against 4 real historical events already in HIST-002,
including two with non-trivial historical UTC offsets:

| Event | Local time | IANA zone | Correct UTC offset applied |
|---|---|---|---|
| WWI declaration | 1914-07-28 11:10 | `Europe/Vienna` | +1:00 |
| Pearl Harbor | 1941-12-07 07:55 | `Pacific/Honolulu` | **-10:30** (Hawaii's pre-1947 offset, correctly NOT -10:00) |
| Tangshan earthquake | 1976-07-28 03:42 | `Asia/Shanghai` | +8:00 |
| Haiti earthquake | 2010-01-12 21:53 | `America/Port-au-Prince` | -5:00 |

The Pearl Harbor case is the meaningful one: `zoneinfo`/`tzdata` correctly applies
Hawaii's actual **historical** (pre-standardization) UTC offset rather than today's,
confirming this isn't silently using a modern offset for a historical date.

## 9. Determinism / reproducibility

Both the Moshier ephemeris calculation and the linear ayanamsha fallback are pure,
seed-free deterministic functions of `(jd_ut, body)` — confirmed by
`tests/backtest/test_reproducibility.py`'s existing determinism tests (re-run in
Phase 18 below, still passing). No change to this in Phase 5.

## Summary

**ASTRONOMY STATUS:** Moshier-precision (no local `.se1` files obtainable in this
sandbox), deterministic, reproducible, wide historical date range for raw planetary
positions; ayanamsha offset accuracy remains validated only for 1900-2050 (unchanged
limitation, now explicitly separated into PRIMARY vs. SECONDARY test sets — see Phase
6 / `BACKTEST_EVALUATION_METHODOLOGY.md`).

**EPHEMERIS STATUS:** pyswisseph 2.10.3.2 installed; 0 `.se1` files present; a clean,
tested, non-fabricating configuration mechanism (`configure_ephemeris_path()`) now
exists for any environment where real files ARE available.
