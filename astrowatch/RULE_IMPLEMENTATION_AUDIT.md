# Rule Implementation Audit — all 19 rules in `rule_registry.RULES`

Written during the "VALIDATION HARDENING BEFORE BT-002" pass. Covers every rule
exactly as it exists in `rule_registry.py` (unmodified — no rule was added, removed,
reworded, or re-thresholded to produce this audit). "Detector" means the code that
decides `fired=True/False` for a rule given an astronomical configuration; a rule can
have correct *data* (citation, domain, interpretation) while having no detector, a
partial detector, or (for 8 rules) being structurally excluded before any detector
would even run, because of its `zodiac_requirement` classification.

Four detector-implementation statuses are used below:
- **IMPLEMENTED** — detector exists, evaluates the rule's actual trigger condition
  correctly and completely against real astronomical input.
- **PARTIALLY_IMPLEMENTED** — detector exists and fires, but on a condition that is
  looser than the rule's true trigger (documented per-rule below).
- **NOT_IMPLEMENTED** — no detector exists yet, but one is plausible with more work
  and no missing source information.
- **NOT_IMPLEMENTABLE_WITH_CURRENT_DATA** — cannot be correctly implemented without
  either (a) information this project's own principles forbid guessing (an
  unspecified precession/ayanamsha model) or (b) input data that isn't derivable from
  astronomical calculation at all (an observed terrestrial/atmospheric omen).

## Summary

| Status | Count |
|---|---|
| IMPLEMENTED | 8 |
| PARTIALLY_IMPLEMENTED | 2 |
| NOT_IMPLEMENTED | 1 |
| NOT_IMPLEMENTABLE_WITH_CURRENT_DATA | 8 |
| **Total** | **19** |

Before this pass: 6 IMPLEMENTED (4 fully + 2 that were, on closer inspection during
this audit, actually PARTIALLY_IMPLEMENTED — see BS-17-25/BS-17-16 below; this was not
previously stated explicitly), 13 with no detector at all. This pass added real
detectors for the 3 Ch. XVIII lunar-pass rules and the 1 Ptolemy eclipse rule (4 rules:
NOT_IMPLEMENTED → IMPLEMENTED), and re-classified the 8 `sidereal_unresolved` rules
from an undifferentiated "no detector" bucket into the more precise
NOT_IMPLEMENTABLE_WITH_CURRENT_DATA status, with the specific missing information
named for each. PT-II-3-general is a lookup table with no independent trigger
condition of its own (see its row) — counted under NOT_IMPLEMENTED with that caveat
rather than forced into one of the other three boxes.

## Full table

| rule_id | rule_name (short) | definition_source | detector_status | thresholds | threshold_source | inputs_required | outputs | tests | known_limitations |
|---|---|---|---|---|---|---|---|---|---|
| BS-17-04 | graha-yuddha "bheda" | Iyer 1884, BS Ch.XVII Sl.4 | IMPLEMENTED | 0.5° (bheda class) | `aspects.GRAHAYUDDHA_PLACEHOLDER_THRESHOLDS_DEG` — UNSOURCED PLACEHOLDER | 2 planet longitudes | fired bool, category(ies) | `tests/test_ayanamsha.py`-adjacent + `tests/backtest/*` (indirect, via `forecast.evaluate_rules`) | Threshold not textually sourced (qualitative "one disc eclipsed" in source, no numeric degree given). |
| BS-17-04b | graha-yuddha "ullekha" | Iyer 1884, Sl.4 | IMPLEMENTED | 0.5–1.0° | same placeholder table | 2 planet longitudes | fired bool, category | same | same threshold caveat |
| BS-17-05 | graha-yuddha "amsumardana" | Iyer 1884, Sl.5 | IMPLEMENTED | 1.0–3.0° | same placeholder table | 2 planet longitudes | fired bool, category | same | same |
| BS-17-05b | graha-yuddha "asavya_apasavya" | Iyer 1884, Sl.5 | IMPLEMENTED | 3.0–8.0° | same placeholder table | 2 planet longitudes | fired bool, category | same | same |
| BS-17-25 | Saturn defeated by Venus | Iyer 1884, Sl.25 | **PARTIALLY_IMPLEMENTED** | 8.0° (any conjunction class) | same placeholder table | Saturn+Venus longitude | fired bool, category | same | Fires whenever Saturn and Venus are in ANY conjunction class, regardless of which is actually "defeated" — `forecast.py`'s own inline comment already documented this: defeat determination (Ch.XVII Sl.9, disc brightness/size/steadiness) is NOT implemented. Not fixed this pass — implementing it would need Sl.9's specific criteria extracted into `rule_registry.py`'s `trigger_params` (not currently there) before any magnitude/diameter calculation (technically available via `swe_pheno_ut`) could be applied without guessing. See Manual Review item MR-1. |
| BS-17-16 | Mercury defeated by Jupiter | Iyer 1884, Sl.16 | **PARTIALLY_IMPLEMENTED** | 8.0° (any class) | same placeholder table | Mercury+Jupiter longitude | fired bool, category | same | Same limitation as BS-17-25. See Manual Review item MR-1. |
| BS-18-02 | Moon north of Mars | Iyer 1884, Ch.XVIII Sl.2 | **IMPLEMENTED (this pass)** | 8.0° conjunction orb (reused from graha-yuddha's widest class) | `aspects.LUNAR_PASS_PLACEHOLDER_ORB_DEG` — UNSOURCED PLACEHOLDER, explicitly documented as reused-not-independently-derived | Moon lon+lat, Mars lon+lat | fired bool, category | `tests/backtest/test_rule_detectors.py` | Orb is a placeholder; N/S comparison itself (ecliptic latitude) is exact, not a placeholder. |
| BS-18-06 | Moon north of Saturn | Iyer 1884, Sl.6 | **IMPLEMENTED (this pass)** | same 8.0° placeholder | same | Moon lon+lat, Saturn lon+lat | fired bool, category | same | same |
| BS-18-general | general N/S rule, any planet | Iyer 1884, Sl.1,7-8 | **IMPLEMENTED (this pass)** | same 8.0° placeholder | same | Moon lon+lat vs. mercury/venus/mars/jupiter/saturn lon+lat | fired bool, category | same | Checked against the classical 5 (mercury/venus/mars/jupiter/saturn) only, per this project's existing convention (`forecast.py`'s own `graha_yuddha_bodies` filter) — outer planets and fixed stars/asterisms (also named in the source as valid targets) are out of scope. |
| BS-19-saturn-year | Saturn as year-lord | Iyer 1884, Ch.XIX | NOT_IMPLEMENTABLE_WITH_CURRENT_DATA | n/a | n/a | Caitra-month new-moon weekday + a precession model | fired bool, category | n/a | Two compounding gaps: (1) `zodiac_requirement=sidereal_unresolved` — the extracted text specifies no precession/ayanamsha model for this pre-1956 calendrical convention, and this project's own principle (documented in `rule_registry.py`) refuses to default to Lahiri; (2) even if resolved, the year-lord-from-weekday calendar algorithm itself has no detector. See Manual Review item MR-2. |
| BS-19-jupiter-year | Jupiter as year-lord | Iyer 1884, Ch.XIX | NOT_IMPLEMENTABLE_WITH_CURRENT_DATA | n/a | n/a | same | fired bool, category | n/a | Same as BS-19-saturn-year. |
| BS-20-02 | multi-planet geometric shapes | Iyer 1884, Ch.XX Sl.2 | NOT_IMPLEMENTABLE_WITH_CURRENT_DATA | n/a | n/a | ≥3 planet longitudes + a geography table | fired bool, category | n/a | `zodiac_requirement=sidereal_unresolved` at the CHAPTER level (the shape-geometry part is actually zodiac-independent per `rule_registry.py`'s own note, but the geography component's zodiacal basis isn't established, and the whole rule is blocked as a unit). Implementing shape-detection alone would have zero effect on any prediction unless the zodiac classification changes — not attempted, to avoid dead code. See Manual Review item MR-3. |
| BS-20-sannipata | "sannipāta"-class meeting | Iyer 1884, Ch.XX Sl.5-9 | NOT_IMPLEMENTABLE_WITH_CURRENT_DATA | n/a | n/a | multi-planet configuration + definition of "sannipāta" | fired bool, category | n/a | Same chapter-level `sidereal_unresolved` block as BS-20-02, PLUS "sannipāta" itself has no sub-criteria encoded in `trigger_params` (what geometric/temporal pattern qualifies) — doubly underspecified. See Manual Review item MR-3. |
| BS-42-01a | omen on new/full moon day | Iyer 1884, Ch.XLII Sl.1 | NOT_IMPLEMENTABLE_WITH_CURRENT_DATA | n/a | n/a | observed heavy rain / meteor / halo / parhelion / danda-formation on a given day | fired bool, category | n/a | Two independent blockers: (1) `sidereal_unresolved` (Sun's zodiac sign needed, no pre-1956 ayanamsha specified); (2) the trigger phenomena themselves (heavy rain, meteors, halos, parhelia) are OBSERVED atmospheric/terrestrial events, not derivable from planetary ephemeris data at all — this is not a "missing detector," it is data this project structurally cannot compute from a date alone. See Manual Review item MR-4. |
| BS-42-01b | same omens, other days | Iyer 1884, Sl.1 | NOT_IMPLEMENTABLE_WITH_CURRENT_DATA | n/a | n/a | same | fired bool, category | n/a | Same as BS-42-01a. |
| BS-42-14 | new/full moon + benefic aspect | Iyer 1884, Sl.14 | NOT_IMPLEMENTABLE_WITH_CURRENT_DATA | n/a | n/a (aspect detection itself exists — `aspects.detect_aspects` — but zodiac-blocked) | Sun/Moon + "benefic" planet longitudes, a precession model | fired bool, category | n/a | `sidereal_unresolved`. The aspect-detection MECHANISM already exists (`aspects.detect_aspects`) and a classical benefic/malefic planet list could be stated, but the rule cannot fire regardless while zodiac-blocked — not implemented, to avoid dead code that can never execute. See Manual Review item MR-5. |
| BS-42-14b | new/full moon + malefic aspect | Iyer 1884, Sl.14 | NOT_IMPLEMENTABLE_WITH_CURRENT_DATA | n/a | n/a | same | fired bool, category | n/a | Same as BS-42-14. |
| PT-II-3-general | triplicity/quadrant lookup table | Ashmand tr., Book II Ch.III | NOT_IMPLEMENTED (infrastructure, no independent trigger) | n/a (pure data table) | table copied verbatim from `trigger_params` | tropical longitude | `{sign, triplicity, quadrant}` (always defined — every sign belongs to exactly one triplicity) | `tests/backtest/test_rule_detectors.py` (tests the lookup helper `aspects.triplicity_for_tropical_longitude`) | This "rule" has no trigger CONDITION distinct from "some sign is always active" — asking whether it independently `fired=True/False` on a given date is not a meaningful question. Implemented as a reusable lookup function (`aspects.triplicity_for_tropical_longitude`) consumed by PT-II-6-01 below, rather than forced into a fired/not-fired shape it doesn't have. |
| PT-II-6-01 | eclipse locality | Ashmand tr., Book II Ch.VI | **IMPLEMENTED (this pass)** | eclipse-limit angle 1.6° (latitude), syzygy orb 1.0° (longitude) | Standard positional-astronomy eclipse-limit criteria (e.g. Meeus, *Astronomical Algorithms* ch.54) — NOT a project-specific interpretive placeholder, applied identically to every date | Sun lon, Moon lon+lat | fired bool, category, ancient quadrant/triplicity (via PT-II-3-general) | `tests/backtest/test_rule_detectors.py`, verified against the real 2020-06-21 annular solar eclipse (see commit) | Modern-country mapping for the ancient quadrant table still doesn't exist (documented as `unsatisfied_conditions` in every match) — only the ancient quadrant/triplicity is reported, not a present-day country. |

## Manual review items

- **MR-1** (BS-17-25, BS-17-16): extract Ch. XVII Sl.9's actual defeat criteria
  (disc brightness/size/steadiness) from the Iyer 1884 translation into a new,
  explicit `trigger_params` sub-field before attempting any magnitude/diameter-based
  defeat detector. `pyswisseph`'s `swe_pheno_ut()` can supply apparent magnitude and
  angular diameter once the textual criterion is known — do not guess the mapping
  from magnitude to "defeated" without the source text in hand.
- **MR-2** (BS-19-*): would require (a) sourcing which precession model, if any, 6th-
  century Caitra-month year-lord calculations are meant to use (this project's
  existing principle is to refuse to default to Lahiri without textual justification),
  and (b) implementing the Caitra-new-moon-weekday-to-year-lord calendar algorithm
  itself, which does not exist anywhere in this codebase yet.
- **MR-3** (BS-20-02, BS-20-sannipata): would require sourcing the zodiacal basis (if
  any) of Ch. XX's compass-sector geography table, and, for BS-20-sannipata
  specifically, the verse-level sub-criteria defining a "sannipāta" configuration
  (currently just a label in `trigger_params`, not a computable definition).
- **MR-4** (BS-42-01a, BS-42-01b): these rules are keyed to OBSERVED atmospheric/
  terrestrial omens (rain, meteors, halos), not computable astronomical positions.
  They could only become "implementable" if this project ever ingested a real
  historical weather/meteor-observation dataset as a second input alongside
  ephemeris data — a data-acquisition problem, not a code problem.
- **MR-5** (BS-42-14, BS-42-14b): blocked purely by `sidereal_unresolved`; would
  become implementable immediately if MR-2's precession-model question were ever
  resolved for Ch. XLII specifically (a DIFFERENT chapter, so resolving it for Ch.
  XIX would not automatically resolve it here).

## What changed vs. what didn't

**Changed this pass (additive only, verified via `git diff`):**
- `aspects.py`: added `classify_lunar_pass()`, `check_for_eclipse()`,
  `triplicity_for_tropical_longitude()`, and 3 new documented-placeholder/
  standard-astronomy constants. Every existing function/constant is byte-identical.
- `rule_matcher.py`: `match_lunar_pass_rules()` now has a real implementation
  (previously `raise NotImplementedError`); `match_eclipse_geography()` was replaced
  by `check_and_match_eclipse()` (the old function now raises `RuntimeError` pointing
  callers at the new one, rather than silently keeping incorrect always-matches
  behavior). `match_grahayuddha_rules()` and `format_match_report()` unchanged.
- `backtest/ephemeris_source.py`: added `compute_full_positions()` (latitude + lunar
  node). `compute_tropical_longitudes()` (what BT-001 used) is byte-identical.
- `backtest/predictor_v2.py`: new file. `backtest/predictor.py` (what BT-001 used) is
  byte-identical.
- `backtest/reproducibility.py`: added `ASTRONOMY_METHODOLOGY_MODULES_V2`,
  `backtest_code_version_hash()`, and an optional `modules=` parameter on
  `astronomy_version_hash()` (defaults to the original list, so a call with no
  arguments still reproduces BT-001's exact hashing behavior).

**Not changed, verified via `git diff` returning empty for these paths:**
`rule_registry.py`, `historical/`, `coordinates.py`, `ayanamsha.py`, `panchang.py`,
`rashi_nakshatra.py`, `forecast.py`, `historical_events.db`, `historical_events_v2.db`,
`backtest_results.db`, `BACKTEST_REPORT_ASTROWATCH_BT001.md`.
