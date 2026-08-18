# Astrowatch Online — Architecture Report (Phase 0 Audit)

Written before any implementation, per the task's instruction. Covers what exists,
what's authoritative and must not be touched, what's reusable as-is, and what the
new `ai/`, `x/`, and API layers need to add on top.

## 1. What already exists and works

**Astronomical core (authoritative, untouched):**
- `kundli.py` — `compute_kundli(jd_ut, lat, lon)` -> `KundliChart` (9 grahas, Ascendant,
  houses, Rashi/Nakshatra). Real Swiss Ephemeris (`pyswisseph`, file-based `.se1`
  data in `ephemeris/`), Lahiri sidereal, mean-node Rahu/Ketu. Raises
  `EphemerisDataUnavailable` rather than silently approximating -- no fallback path.
- `mahadasha.py` -- `compute_dasha_state(jd_ut, moon_sidereal_lon)` -> Vimshottari
  Mahadasha/Antardasha at any instant. Pure function of Moon longitude, standard
  120-year/9-lord cycle.
- `panchang.py` -- tithi/vara/nakshatra (real); yoga/karana explicitly `None`
  (documented as not implemented, never silently defaulted).
- `rashi_nakshatra.py`, `coordinates.py`, `timeutil.py`, `ayanamsha.py` (legacy,
  superseded by direct `SEFLG_SIDEREAL`, kept for other callers) -- supporting math.

**Mundane/entity layer (authoritative, untouched):**
- `mundane/entity_chart.py` -- `compute_entity_chart(name, entity_type, date, lat,
  lon, tz, time=None)`. THE rule: any entity with a real date+place can be charted;
  missing time defaults to 00:00 local, tagged `time_source=ASSUMED_MIDNIGHT` vs
  `DOCUMENTED`. This is the exact rule the task spec restates in Section 9 --
  already built, reused as-is.
- `mundane/dasha_timeline.py` -- `full_lifetime_sequence()`, multi-cycle Dasha walk
  (nations/orgs can outlive one 120-year cycle; `max_cycles=1` for persons).

**World Astrology knowledge/reading layer (authoritative, untouched):**
- `world_astrology/registry.py` -- `build_registry()`, aggregates 10 traditions
  (Jyotisha, Hellenistic, Western, Babylonian, Persian/Islamic, Chinese, Tibetan,
  Egyptian, Japanese, Mesoamerican). Only 4 have `computed=True` content (Jyotisha,
  Hellenistic, Western, Chinese) -- the other 6 are sourced reference knowledge only.
- `world_astrology/dignity_tables.py` -- shared sign-dignity table, `jyotisha_score()`,
  `hellenistic_score()`.
- `world_astrology/cross_tradition.py` -- 18 curated cross-tradition relationships +
  validator. This IS the cross-tradition engine the task asks for -- already real.
- `world_astrology/reading_engine.py` -- the single most important reuse target:
  - `build_chart_bundle(entity_name, entity_type, inception_date, lat, lon, tz,
    inception_time=None, as_of_date=None)` -> one `ChartBundle` (chart + dasha +
    Jyotisha/Hellenistic agreement classification + Western/Chinese descriptive
    context). One code path, all three reading modes below call it.
  - `generate_short_reading(...)` -- configurable-length priority-ranked sentences.
  - `generate_detailed_reading(...)` -- 15 labeled sections.
  - `generate_world_reading(...)` -- mundane/nation framing, unlimited Dasha cycles.
  - `generate_full_horoscope_narrative(...)` -- flowing-prose long narrative.
  - `classify_agreement()` -- Strong/Moderate/Contradictory/Insufficient/
    Tradition-specific, the exact agreement/disagreement taxonomy the spec asks for.
- `world_astrology/historical_validation.py` -- `record_prediction()`,
  `record_outcome()`, `assess_match()`, `get_prediction()`, `compute_accuracy_summary()`
  against `world_astrology_validation.db`. Append-only by construction (DB trigger
  rejects UPDATE). Narrower schema than the task's spec (agreement-only), so the new
  work adds a broader `predictions.db` rather than overloading this one -- this one
  stays as-is.

**Historical events (authoritative, untouched):**
- `historical/` package -- `database.py`, `repository.py` (`get_events(conn,
  category=, region=, country_code=, start_date=, end_date=, min_source_quality=,
  dataset_version=, ...)`), `models.py`, `versioning.py`, `deduplication.py`,
  `ingestion/*`. Backs `historical_events.db` (frozen `ASTROWATCH-HIST-001`, 136
  events) and `historical_events_v2.db` (`ASTROWATCH-HIST-002`). This is what
  `search_historical_events()` wraps directly -- no reimplementation needed.

**Prediction/rule engines (authoritative, untouched, narrower scope than "AI predict"):**
- `rule_registry.py`, `rule_matcher.py`, `aspects.py`, `forecast.py` -- a
  cited-source (Brhat Samhita/Tetrabiblos) rule-matching engine for
  grahayuddha/eclipse/lunar-pass configurations against fixed named rules. A
  DIFFERENT, narrower prediction mechanism than `world_astrology`'s dignity/dasha
  reading engine -- both stay; the new AI layer's `run_mundane_prediction()` tool
  wraps `forecast.run_forecast()`, not a reimplementation.
- `backtest/` -- a full separate backtest harness that produced the frozen
  `ASTROWATCH-BT-001` experiment. Untouched; not part of the online prediction path.

**`kundli_mass/` (real corpora, reusable as entity-DB seed data):**
- `nations_corpus.py` -- ~193 real UN member states, formation date + capital
  coords + timezone, all `ASSUMED_MIDNIGHT`.
- `famous_people_corpus.py` -- 1,305 real people across 8 fields, birth date/place,
  time where documented else `ASSUMED_NOON` (flagged: the people corpus historically
  used noon as its assumed-time convention, not midnight -- the new Entity DB stores
  whichever `time_accuracy` each source actually used, never overwrites it to look
  more precise than it is).
- `leaders_corpus.py` -- heads of state/government.
- These become the initial seed rows for the new `entities` table -- real,
  already-vetted data, not fabricated to pad the demo.

**API (`api.py`):**
- Stdlib `http.server.ThreadingHTTPServer`, no Flask/FastAPI dependency (deliberate
  project convention). Already reads `PORT` from the environment. Already has a
  `GET /health` (and `/`) returning `{"status": "ok", "engine": ..., "endpoint": ...}`.
  Gap: binds to `127.0.0.1`, not `0.0.0.0` -- unreachable from outside the container
  on Render. Gap: health response shape doesn't match the task's required
  `{"status", "astrowatch", "openai"}`. Otherwise `POST /api/chart` is complete and
  correct; must not be broken.

**Tests:** `tests/` -- 309 passing (`pytest -q`, confirmed this session), covering
astronomy, historical events, world_astrology, backtest. This is the regression
baseline for every phase below.

**Dependencies:** `requirements.txt` (repo root) -- `pyswisseph==2.10.3.2` only.
No web framework, no OpenAI SDK, no HTTP client beyond stdlib. Python 3.10.12 in
this sandbox; task asks to target 3.11 for Render -- new code avoids
version-specific syntax so it runs on both.

## 2. What needs to be added (new, additive, phased)

1. `api.py`: bind `0.0.0.0`, fix `/health` response shape, add new routes
   (`/api/predict`, `/api/agent/run`, `/api/random-prediction`,
   `/api/current-event`, `/api/predictions`, `/api/predictions/{id}`) -- new
   handler branches in the existing `ChartHandler`, not a rewrite.
2. `ai/` package -- OpenAI Responses API client, prompts, entity resolver, event
   scanner, random-prediction selector, synthesis. Orchestrates the existing
   engines above; performs zero astronomical/astrological computation itself.
3. `entities_db.py` -- new SQLite `entities` table per the task's field list,
   seeded from the real `kundli_mass` corpora.
4. `predictions_db.py` -- new SQLite `predictions` table per the task's schema
   (broader than `world_astrology_validation.db`'s narrower agreement-only schema).
5. `ai/tools.py` -- the internal tool-function surface (`get_entity`,
   `search_entities`, `calculate_entity_chart`, `run_jyotisha_prediction`, etc.),
   each a thin wrapper calling the real existing functions listed in section 1.
6. `x/` -- optional X (Twitter) publisher, `X_ENABLED=false` by default.
7. `scheduler.py` -- simple in-process scheduler, `PREDICTIONS_PER_DAY` env var.
8. `.env.example`, `.gitignore` update (add `.env`), `requirements.txt` additions
   (`openai`), `.python-version`.

## 3. Non-negotiable boundaries (carried into every phase)

- OpenAI never computes a planetary position, Dasha, or dignity score. Every
  number the AI synthesis text references must trace back to a `ChartBundle`,
  `EntityChart`, or `historical.repository` row.
- If OpenAI is unconfigured (`OPENAI_API_KEY` missing), `POST /api/chart` and all
  pure-calculation paths keep working; only the AI-synthesis endpoints degrade
  (return a clear `insufficient_data`/`ai_unconfigured` message, never a fake
  reading).
- Assumed-midnight/assumed-noon time is always labeled `time_accuracy`, never
  presented as documented fact.
- Existing files listed above are not modified except `api.py` (additive route
  branches + host/health fix) -- everything else new lives in new files.

## 4. Phased implementation order (this session)

Phase 1 production `api.py` -> Phase 2 `ai/` + OpenAI client -> Phase 2b entity DB +
tool functions -> Phase 3 `/api/predict` -> Phase 4 random predictions -> Phase 5
current-event -> Phase 6 prediction history + agent + scheduler -> Phase 7 X
(optional) -> Phase 8 security/deployment/tests/final report. Full test suite run
after each phase; no regressions carried forward.
