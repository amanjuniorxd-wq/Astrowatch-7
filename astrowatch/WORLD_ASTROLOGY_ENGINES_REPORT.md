# Astrowatch World Astrology Engines — Implementation Report

**Scope of this report:** the task of turning all ten catalogued astrological traditions
into real, independently-runnable computational prediction engines, rather than leaving
six of them as reference-only knowledge entries. This report documents exactly what was
built, what was deliberately left unimplemented (and why), and how the whole system
enforces its own "no fabrication" rule end to end.

---

## 1. Starting point (audit)

Before writing any code, `world_astrology.registry.build_registry()` was used to check
which of the ten catalogued traditions had *any* `computed=True` knowledge entries:

| Tradition | Computed entries (before this work) |
|---|---|
| Jyotisha | 10 / 20 |
| Hellenistic | 3 / 9 |
| Western | 2 / 11 |
| Chinese | 2 / 10 (sexagenary-year math only) |
| Babylonian | 0 / 6 |
| Persian/Islamic | 0 / 8 |
| Tibetan | 0 / 5 |
| Japanese | 0 / 4 |
| Egyptian | 0 / 4 |
| Mesoamerican | 0 / 5 |

Six traditions had zero computational engines — pure reference material. This confirmed
the task's premise and set the baseline this work fills in.

## 2. Architecture: two layers, kept separate

- **Knowledge layer** (`world_astrology/schema.py`, `world_astrology/traditions/*.py`,
  `world_astrology/registry.py`) — the pre-existing catalogued reference content. **Untouched.**
- **Computation layer (new, additive)** — `world_astrology/engine_interface.py` +
  `world_astrology/engines/*.py` + `world_astrology/unified_engine.py`. A parallel system
  that actually runs testable astronomical/calendrical calculations.

The pre-existing `reading_engine.py` (Jyotisha/Hellenistic reading pipeline) and
`cross_tradition.py` (curated 18-relationship table) are also **untouched** and remain
fully functional — the new `UnifiedAstrologyEngine` sits alongside them, not in place of
them. Nothing in this task removed, replaced, or weakened any pre-existing Astrowatch
functionality; `pytest` confirms 389/389 tests pass (361 pre-existing + 28 new), zero
regressions.

### The common engine contract (`engine_interface.py`)

Every tradition implements `AstrologyEngine`: `is_applicable(context)`, `calculate(context)`
(raw astronomical/calendrical math only), `interpret(calculation)` (rule-based reading),
and inherits a default `predict(context)` pipeline that:

- Returns `status="not_applicable"` if the tradition doesn't historically address this
  entity type/domain (e.g. Babylonian omen astrology for a private individual).
- Returns `status="insufficient_methodology"` if `calculate()` raises `NotImplementedError`
  — the engine's own honest "I looked at this and cannot reconstruct it" signal.
- Returns `status="error"` for a genuine bug, always surfaced in `limitations`, never hidden.
- Returns `status="calculated"` with a real `TraditionPrediction` otherwise.

Every `PredictiveRule` carries `historical_status` from a fixed, documented vocabulary:
`documented / reconstructed / scholarly_disputed / traditional / modern / speculative`.
Confidence is always **categorical** (`low`/`moderate`/`high`/`unvalidated`) — no engine
in this codebase invents a numerical accuracy value.

## 3. What was actually implemented, per tradition

### Jyotisha (extended, not replaced)
Implemented: Navamsa (D9 varga, hand-verified against the classical modality-based
counting rule), four BPHS-attested Yogas (Gajakesari, Chandra-Mangala, Budhaditya,
Kemadruma — without the full Kemadruma cancellation rules, disclosed as a limitation),
Jupiter/Saturn Gochara from natal Moon (marked `traditional`, not `documented` — no single
primary-source citation for the exact favorable-house table was independently verified
this session).
**Not implemented** (honestly, with individual reasons): Jaimini, Nadi (no computational
algorithm exists for leaf-matching), Tajika, Prashna, Muhurta.

### Hellenistic (extended)
Implemented: Annual Profections + Lord of the Year, Lot of Fortune + Lot of Spirit
(sect-dependent), Zodiacal Releasing from Fortune (L1 major periods only — hand-verified
against a documented year-length table).
**Not implemented:** horary, electional, ZR sub-periods (L2–L4) / "loosing of the bond".

### Western (extended)
Implemented: Secondary Progressions (day-for-a-year; verified the progressed Sun lands in
the astronomically correct sign for a 79-year-old chart), Solar Return (numeric root-find
against real Swiss Ephemeris Sun longitude — verified the return date sits within hours of
the astronomically true crossing, correctly offset from the calendar birthday by the real
tropical-year drift), transiting outer-planet (Jupiter/Saturn/Uranus/Neptune/Pluto) aspects
to natal Sun/Moon/Ascendant.
**Not implemented:** synastry, lunar returns, eclipse-based mundane technique, horary, electional.

### Babylonian (new)
Implemented: real Swiss-Ephemeris eclipse search (lunar globally, solar for the entity's
location), Venus visibility phase (elongation-based), planetary conjunctions among the five
classical planets. **Cross-checked against real 2026 eclipse data**: the engine correctly
found the Aug 28 2026 partial lunar eclipse for a Sept 2026 prediction date.
Deliberately reports only the **general documented omen category** for each phenomenon
(e.g. "lunar eclipses concern the king/state") — never a specific invented apodosis, since
Enuma Anu Enlil's ~7000 individual omens are not comprehensively sourced in this project.
`is_applicable()` returns `False` for person/company/sports_team entities — Babylonian
celestial-omen astrology was fundamentally mundane/royal, not personal natal astrology.

### Persian/Islamic (new)
Implemented: Great Conjunction detection (Jupiter-Saturn, real numeric search) + triplicity
mutation. **Verified against the real, famous Dec 21 2020 "Great Mutation" conjunction**
(0° Aquarius, air triplicity) — the engine found this exact date and sign independently.
Annual Revolution explicitly **reuses** `HellenisticEngine`'s profection/Lots output rather
than duplicating the math, per the task's own instruction.
**Not implemented:** additional named Arabic Lots beyond Fortune/Spirit, horary, electional,
the larger ~960-year "mutation of mutations" cycle.

### Chinese — BaZi (new)
Implemented: Year Pillar (Gan-Zhi) and Month Pillar, using real solar-longitude search for
the Lichun/solar-term year and month boundaries (not a fixed calendar-date approximation).
**Independently verified against three well-known facts**: 1984 = Jiazi/Rat, 1999
(post-Lichun) = Ji-Mao/Rabbit, 2000 (post-Lichun) = Geng-Chen/Dragon — all three matched.
**Day Pillar and Hour Pillar are deliberately NOT implemented**: this project could not
independently verify a sexagenary day-count epoch anchor with enough confidence to trust
the offset constant, and a wrong epoch would silently mis-date every reading — marked
`not_implemented` rather than guessed. Da Yun (Luck Cycle), Zi Wei Dou Shu, Qi Men Dun Jia,
and Tai Yi are also not implemented.

### Tibetan (new)
Implemented: the Elemental Year (Rabjung 60-year cycle), computed by **reusing** the
already-verified Chinese Year Pillar (the Tibetan calendar shares the identical
year-to-cycle-position correspondence with the Chinese sexagenary system since 1027 CE —
a documented synchronization) and relabeling with Element/Polarity/Animal names.
Verified: 1984 → "Male Wood Rat Year", matching the well-known Chinese/Tibetan label for
that year. **Not implemented:** Phugpa/Tsurphu true-longitude astronomy, Tibetan lunar
month/day calculation (both require specialized tables this project does not have).

### Japanese — Nine Star Ki (new)
Implemented: the digital-root year formula → 1–9 star number, mapped to a Wu-Xing element.
Marked `historical_status="traditional"` (not `"documented"`) — the formula is consistently
published in modern reference works but this session could not trace it to a single
pre-modern primary source. **Not implemented:** monthly/daily star cycles, Onmyodo
directional-timing ritual.

### Egyptian (new)
Implemented: the (Greco-Egyptian, post-500 BCE) 36-decan system — which of the 36
zodiacal decans the Sun currently occupies. Explicitly **not a natal system**:
`is_applicable()` returns `False` when `prediction_domain="natal"`, per the task's own
explicit instruction not to invent an Egyptian natal-horoscope tradition that never
historically existed. **Not implemented:** heliacal-rising-based decan timing (the
*original* native-Egyptian method), Sirius/Sopdet heliacal rising — both require a
fixed-star ephemeris with atmospheric-visibility modeling this project doesn't have.

### Mesoamerican — Maya (new)
Implemented: Tzolk'in (260-day), Haab' (365-day vague year), Long Count — real Julian-Day
arithmetic anchored to the GMT correlation constant (584283). **Verified against the
famous Dec 21 2012 "end of Baktun 13" date**: the engine independently computed
`13.0.0.0.0`, `4 Ajaw`, `3 Kankin` — all three match the well-documented historical
designation for that date. The GMT correlation constant itself has *real, disclosed*
scholarly disagreement (584283 vs. 584285); this is reported transparently, not hidden,
via `historical_status="scholarly_disputed"` and an explicit alternate-reading factor.
**Not implemented:** day-sign omens/meanings (source-dependent, not independently
verified), Dresden Codex Venus Table correlation, Aztec tonalpohualli (a separate,
deliberately unconflated tradition).

## 4. UnifiedAstrologyEngine — the cross-tradition pipeline

`world_astrology/unified_engine.py` runs every applicable engine independently, then:

1. **Theme clustering** — a disclosed keyword-heuristic (not real NLP) groups each
   tradition's free-text themes into macro-categories. The trivially-common
   "timing_marker" category (any mention of a date/period) is explicitly **excluded**
   from agreement scoring, since almost every tradition mentions *some* date and treating
   that as "agreement" would overclaim consensus.
2. **Agreement classification** — `exact_agreement` / `strong_thematic_agreement` /
   `partial_agreement` / `weak_agreement` / `no_agreement` / `contradiction` — scored by
   how many **independent lineage groups** concur, not raw tradition count. This directly
   implements the "not simple majority voting" requirement.
3. **Dependency grouping** (`INDEPENDENCE_GROUPS`) — traditions that directly reuse
   another's computed numbers are grouped so their agreement isn't double-counted:
   `{hellenistic, persian_islamic, western}` (Persian directly reuses Hellenistic's code;
   Western's Solar Return is doctrinally continuous with Hellenistic's annual revolution),
   `{chinese, tibetan, japanese}` (Tibetan/Japanese both reuse the Chinese solar year).
4. **Conflict detection** — if `favorable_growth` and `instability_conflict` themes both
   appear, the engine explicitly reports "Mixed/conflicting signals" — never hidden or averaged away.
5. **Weighting** — entirely categorical: applicability, data quality, rule strength,
   historical documentation, independence group, backtest performance. `empirical_weight`
   is **always** `"unavailable"` until real backtest data exists — no invented numbers.
6. **Mandatory transparency** — every reading reports "Traditions evaluated / applicable /
   calculated / unavailable" and never claims a tradition contributed unless it actually
   returned `status="calculated"`.

## 5. Backtesting scaffold

`world_astrology/backtesting.py` — a new, separate SQLite ledger
(`world_astrology_backtest.db`, distinct from the older `backtest_results.db` mundane-rule
system) for recording tradition-engine predictions against real outcomes. **Ships empty —
no historical results were seeded or fabricated.** Performance aggregation refuses to
report a rate below 5 samples (`MIN_SAMPLE_SIZE_FOR_RATE`), returning raw counts and an
explicit `"insufficient_sample_size"` flag instead.

## 6. API / AI tool wiring

- `ai/world_engine_tools.py` — `run_jyotisha`, `run_hellenistic`, `run_western`,
  `run_babylonian`, `run_persian_islamic`, `run_chinese`, `run_tibetan`, `run_japanese`,
  `run_egyptian`, `run_mesoamerican`, `compare_predictions()`, `generate_unified_prediction()`
  — the exact function list the task specified, each a thin wrapper with no calculation
  logic of its own.
- `ai/world_prediction_agent.py` — orchestrates `POST /api/world-prediction`, reusing
  `ai.prediction_agent._resolve_entity` (the same entity-resolution logic `/api/predict`
  uses) rather than duplicating it. Supports `mode` (`short`/`detailed`) and a `traditions`
  filter (default: all 10, "All Applicable"). Fully functional without OpenAI configured —
  AI stays orchestration/NLG-only, never the calculation, per the project's standing rule.
- New endpoint `POST /api/world-prediction`, verified end-to-end over real HTTP (server
  started, request sent, response validated, prediction persisted to `predictions_db` and
  read back).

## 7. Tests

`tests/test_world_astrology_engines.py` — 28 new tests: one per tradition engine (each
checking real computed output, not just "doesn't crash"), engine-interface contract tests
(`NotImplementedError` → `insufficient_methodology`, real exceptions → `error`, never
hidden), `test_missing_data`, `test_assumed_midnight`, `test_historical_status`,
`test_cross_tradition_agreement`, `test_cross_tradition_conflict`,
`test_dependency_weighting`, `test_unified_prediction`, and three backtesting-scaffold
tests. **Full suite: 389/389 passed** (361 pre-existing + 28 new), zero regressions.

## 8. Final capability test: "Will Republicans win the 2028 U.S. presidential election?"

Ran the exact scenario the task specifies. `Republican Party` (founded Ripon, WI, March 20
1854 — web-verified) and `Democratic Party` (conventionally dated Jan 8 1828 — web-verified,
with the genuine date-uncertainty disclosed in the entity's own notes field, since unlike
the Republicans there is no single documented founding *meeting*) were added to
`entities_db` with real, sourced data; `United States` (July 4 1776) was already present.

For all three entities, `run_world_prediction()` (the same code path `POST
/api/world-prediction` uses) was run for prediction date 2028-11-07 (the actual, calculated
2028 U.S. Election Day):

- **Traditions evaluated: 10 / applicable: 10 / calculated: 10 / unavailable: 0** for every entity.
- Each of the ten traditions' own prediction is individually shown and traceable.
- The system correctly identified real **contradiction** (mixed favorable/growth vs.
  instability/conflict signals) for all three entities on this date, and reported it
  explicitly rather than forcing a false consensus.
- **The system never outputs a fabricated "Republicans win" / "Democrats win" claim.** No
  engine in this codebase computes anything about vote counts, polling, or electoral
  outcomes — that would be fabrication. What it genuinely produces is a transparent,
  per-tradition thematic reading (growth/instability/timing signals) plus an honest
  cross-tradition agreement/conflict analysis, exactly matching the task's own repeated
  instruction that astrology be presented as astrology, not disguised political forecasting.

## 9. Summary: implemented vs. not, by the numbers

| Tradition | New rules implemented | Techniques explicitly marked not-implemented |
|---|---:|---:|
| Jyotisha | 6 | 5 |
| Hellenistic | 4 | 3 |
| Western | 3 | 5 |
| Babylonian | 3 | 3 |
| Persian/Islamic | 2 | 4 |
| Chinese | 2 | 6 |
| Tibetan | 1 | 3 |
| Japanese | 1 | 3 |
| Egyptian | 1 | 3 |
| Mesoamerican | 3 | 4 |
| **Total** | **26** | **39** |

Every one of the 39 not-implemented techniques has an individually-reasoned explanation in
its engine's `NOT_IMPLEMENTED_TECHNIQUES` dict — none are silent omissions, and none were
faked to appear complete. This project's objective, per its own governing instruction, was
"all available genuine astrological knowledge, not fake completeness" — this report is the
accounting of exactly where that line was drawn and why.
