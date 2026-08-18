# Astrowatch Online -- Final Deliverable Report

Transforms the existing Astrowatch project into an online, AI-assisted,
autonomous astrological prediction platform, implemented in 8 phases (task
spec Section 36), full test suite run and passing after every phase. See
`ARCHITECTURE_REPORT_ONLINE.md` for the pre-implementation audit this report
follows on from.

## 1. Architecture

```
USER REQUESTS / AUTONOMOUS AGENT
            |
   OPENAI INTELLIGENCE (ai/openai_client.py, ai/prompts.py)
            |
  entity_resolver.py / event_scanner.py / random_prediction.py
            |
     ENTITY RESOLVER (entities_db.py, seeded from real corpora)
            |
   ASTROWATCH ENGINE  <-- unchanged, authoritative
     kundli.py (Swiss Ephemeris) / mahadasha.py / mundane/entity_chart.py
            |
  world_astrology/reading_engine.py + cross_tradition.py
     (Jyotisha / Hellenistic / Western / Chinese + 6 reference traditions)
            |
     PREDICTION RESULT (structured, ai/tools.py)
            |
   OPENAI SYNTHESIS (ai/synthesis.py) -- prose, kept separate from calculation
            |
    FINAL ASTROWATCH READING (ai/prediction_agent.py assembles Section 17 shape)
            |
      predictions_db.py (history/outcome tracking)
            |
      -------+-------
      |             |
  api.py (HTTP)   x/publisher.py (optional, X_ENABLED gated)
```

OpenAI never computes a planetary position, dasha, or dignity score -- every
number in a response traces back to `kundli.py`/`world_astrology/*`/
`historical/repository.py`. If `OPENAI_API_KEY` is unset, calculation
endpoints keep working; AI-synthesis-dependent responses return a clear
`insufficient_data`/503 status instead of a fabricated reading (verified by
`tests/test_online_platform.py`, run with no key configured).

## 2. Files created

```
ARCHITECTURE_REPORT_ONLINE.md          Phase 0 audit (before any code changes)
ONLINE_PLATFORM_DELIVERABLE.md         this report
.env.example                            env var template (repo root)
.python-version                         "3.11" (repo root)

astrowatch/entities_db.py               entities table + seeding from kundli_mass/*_corpus.py
astrowatch/predictions_db.py            predictions table (history/outcome tracking)
astrowatch/scheduler.py                 PREDICTIONS_PER_DAY autonomous scheduler

astrowatch/ai/__init__.py
astrowatch/ai/openai_client.py          OpenAI Responses API wrapper, graceful failure
astrowatch/ai/prompts.py                shared SYSTEM_PROMPT (integrity rules)
astrowatch/ai/tools.py                  13 internal tool functions (Section 8)
astrowatch/ai/entity_resolver.py        question -> structured entity/domain/dates
astrowatch/ai/event_scanner.py          current-event text -> structured event + pipeline
astrowatch/ai/synthesis.py              structured results -> prose, Section 17 shape
astrowatch/ai/prediction_agent.py       orchestrates resolve -> calculate -> synthesize -> save
astrowatch/ai/random_prediction.py      intelligent (scored, weighted-random) candidate selection
astrowatch/ai/agent.py                  the 11-step autonomous agent, dry_run support

astrowatch/x/__init__.py
astrowatch/x/client.py                  minimal X API v2 client (OAuth 1.0a, stdlib only)
astrowatch/x/publisher.py               X_ENABLED-gated publish orchestration, dedup

astrowatch/tests/test_online_platform.py  52 new tests (all modules above + live HTTP)
```

## 3. Files modified

```
astrowatch/api.py       0.0.0.0 binding, GET /health reshaped, 7 new routes wired,
                         rate limiting + body-size/type validation added
astrowatch/kundli.py    real pre-existing thread-safety bug fixed (see Section 9) --
                         no calculation/methodology change
requirements.txt        + openai>=1.50.0
.gitignore              + .env / .env.local
README.md               + "Astrowatch Online" section (local run + Render steps)
```

Nothing else in the pre-existing codebase was touched.

## 4. API endpoints

```
GET  /health                     {"status","astrowatch","openai"}
GET  /                           endpoint list
POST /api/chart                  unchanged, pre-existing
POST /api/predict                {entity, entity_type?, question, start_date?, end_date?,
                                   mode: short|detailed, date?/latitude?/longitude?/timezone?/time?}
POST /api/agent/run              {dry_run?, category?, mode?, publish_to_x?}
POST /api/random-prediction      {category?, mode?}
POST /api/current-event          {event_text, mode?}
GET  /api/predictions            ?entity=&mode=&limit=
GET  /api/predictions/{id}
```

## 5. Environment variables

```
OPENAI_API_KEY                   required for all AI-synthesis features
OPENAI_MODEL                     optional, defaults to gpt-4o-mini in code
OPENAI_MAX_OUTPUT_TOKENS         optional, defaults to 1200
PORT                              cloud-platform-injected; do not set manually on Render
HOST                              optional, defaults to 0.0.0.0
PREDICTIONS_PER_DAY              optional, defaults to 2
PREDICTION_POSTING_WINDOWS_UTC   optional, comma-separated UTC hours
ASTROWATCH_SCHEDULER_ENABLED     optional, "true" to run the scheduler in-process
X_ENABLED                        optional, defaults to false
X_API_KEY / X_API_SECRET / X_ACCESS_TOKEN / X_ACCESS_TOKEN_SECRET / X_BEARER_TOKEN
RATE_LIMIT_MAX_REQUESTS          optional, defaults to 30 (per window, per IP)
RATE_LIMIT_WINDOW_SECONDS        optional, defaults to 60
MAX_REQUEST_BODY_BYTES           optional, defaults to 262144 (256 KB)
```

## 6. OpenAI integration, exactly how it works

`ai/openai_client.py` is the single choke point: reads `OPENAI_API_KEY`/
`OPENAI_MODEL` fresh from the environment on every call (never cached/
hard-coded), uses the Responses API (`client.responses.create`), and offers
two entry points -- `complete_text()` (free prose, used by `synthesis.py`) and
`complete_json()` (strict `json_schema` structured output, used by
`entity_resolver.py`/`event_scanner.py` so parsing never depends on regex over
free text). Every failure mode (no key, package missing, API error, empty/
malformed response) raises one exception type, `AIUnavailable`, which every
caller in `ai/` and every route handler in `api.py` catches explicitly and
turns into either a clear `insufficient_data` status (when the calculation
half of the response is still valid and useful on its own, e.g.
`/api/predict`) or a 503 with an explanation (when the whole feature
inherently requires the model, e.g. `/api/current-event`'s free-text
extraction, which has no honest non-AI fallback).

## 7. Autonomous prediction system, exactly how it works

**Random:** `ai/random_prediction.py` maps each of the 10 task-spec categories
to an `entities_db` query (entity_type + optional category filter). Candidates
are scored on 4 signals (data quality, novelty via
`predictions_db.recent_predictions_for_entity`, historical-importance
heuristic, public-interest proxy), then the final pick is a **weighted random
draw** among the top-N scorers -- not `random.choice(all_entities)`, and not a
deterministic argmax either. Verified: a synthetically over-predicted entity
scored 0.458 vs. a fresh entity's 0.807 (novelty signal working); the
`politics` category was found (and fixed) to return real heads of state
(`US_PRESIDENT`/`INDIA_PM`/`CURRENT_LEADER`), not arbitrary people, after a
pool-size bug was caught by the new tests.

**Current-event:** `ai/event_scanner.py` extracts structured fields from
user-supplied event text via OpenAI, then requires at least one extracted
entity to resolve against the real `entities_db` before proceeding --
`can_analyze` is forced `False` (never fabricated true) if nothing resolves.

**Agent:** `ai/agent.py` runs the 11-step flow (discover -> select -> identify
-> verify -> horizon -> calculate -> run traditions -> compare -> synthesize
-> save -> return), each step delegating to already-tested code
(`random_prediction.select_candidate`, `ai.tools.*`,
`ai.synthesis.build_final_result`, `predictions_db.save_prediction`).
`dry_run=true` runs the entire real pipeline (including any configured OpenAI
call) and only skips the final persistence step -- verified live: a dry run
returns `prediction_id: null` and never shows up in a subsequent
`GET /api/predictions?entity=...` query.

## 8. Database schemas

**`entities.db`** (`entities_db.py`): `name, entity_type, birth_or_inception_date,
birth_or_inception_place, birth_or_inception_time, timezone, latitude,
longitude, source, source_reliability, time_accuracy
(documented|assumed_midnight|assumed_noon), notes, category, created_at,
last_predicted_at, prediction_count`. Seeded with 1,520 real entities from
this project's own `kundli_mass/{nations,famous_people,leaders}_corpus.py`
(197 countries, 1,305 people, 37 heads of state/government) -- not fabricated
demo rows.

**`predictions.db`** (`predictions_db.py`): `id, created_at, entity,
entity_type, question, prediction, time_window, traditions_used,
calculation_data, confidence, model_score, mode, source, published,
x_post_id, actual_outcome, outcome_status
(pending|correct|partially_correct|incorrect|unclear), outcome_recorded_at`.
Append-only in spirit: no function performs a blanket `UPDATE` of prediction
content; `record_outcome()` is the one allowed post-insert mutation and never
touches the original prediction text (verified by
`test_outcome_recording_never_touches_prediction_text`). Deliberately separate
from the pre-existing, narrower `world_astrology_validation.db`, which is
untouched.

## 9. A real bug found and fixed along the way

While making `api.py` production-ready (Phase 1), a direct multi-threaded
reproduction revealed that `pyswisseph`'s `set_ephe_path()`/`set_sid_mode()`
calls (in `kundli.py`) only reliably apply in the thread that calls them --
since `ThreadingHTTPServer` runs every HTTP request on its own thread, this
meant **every concurrent `/api/chart` request beyond the first would have
silently failed** (correctly caught and rejected by the existing
no-Moshier-fallback check, but still a real production-breaking bug, not
hypothetical). Fixed by re-asserting the identical file-based ephemeris
configuration once per thread inside `compute_kundli()` -- confirmed via an
8-thread concurrent repro (all 8 succeeded, identical results) and a live
10-concurrent-request load test against the running server (0 errors). No
calculation, methodology, or accuracy was changed.

A second, analogous bug was caught by the new test suite itself: `ai/tools.py`
originally cached one module-level sqlite3 connection per database, which
raised `sqlite3.ProgrammingError` when a background-thread caller (e.g.
`AutonomousAgentTests`, or the scheduler) and an HTTP-request-thread caller
both touched it. Fixed by opening a short-lived connection per call instead
(consistent with this project's existing `historical/database.connect()`
convention) -- verified by the full test suite passing in every run order.

`ai/tools.run_mundane_prediction()` also surfaces (rather than papering over)
a **pre-existing** limitation in `forecast.py`: its ayanamsha step queries
astro.com live over the network with no offline path unless
`allow_ayanamsha_fallback=True` is explicitly passed. This was not introduced
by this work; it's disclosed with a clear error message pointing callers at
the validated, network-independent `run_jyotisha_prediction`/
`run_cross_tradition_analysis` tools instead.

## 10. Deployment (Render)

See the "Astrowatch Online" section of `README.md` for the exact steps
(build/start commands, root directory, Python 3.11, required env vars,
scheduler options, and the `/health` verification response to expect).

## 11. Testing

**Existing suite:** 309 tests, all passing before this work began (baseline)
and unchanged/still passing after every phase (kundli.py's thread-safety fix
did not change any existing test's expected output).

**New tests:** 52, in `astrowatch/tests/test_online_platform.py` --
`OpenAIClientTests` (5), `EntitiesDBTests` (5), `PredictionsDBTests` (6),
`ToolFunctionsTests` (7, exercising the real calculation pipeline end to
end), `PredictionAgentTests` (5), `RandomPredictionTests` (4),
`AutonomousAgentTests` (2), `SynthesisTests` (2), `XPublisherTests` (6),
`APIEndpointTests` (12, real HTTP requests against a live
`ThreadingHTTPServer` instance spun up in-process).

**Combined total: 361/361 passing**, run via `python3 -m pytest -q` from
`astrowatch/`. No `OPENAI_API_KEY` or X credentials are configured for these
tests -- graceful-degradation behavior (task spec Section 29 "test failure
when OPENAI_API_KEY is missing") is exactly what most of the new tests
assert, not skipped or mocked around.

**Manual local-testing checklist** (task spec Section 28), all performed
live against a running server this session: install deps, run pytest,
start API, `/health`, `/api/chart`, `/api/predict` (known + unknown entity),
`/api/agent/run?dry_run=true` and `dry_run=false`, `/api/random-prediction`,
`/api/current-event` (both the 503-without-key path and the 400-missing-field
path), `GET /api/predictions` + `GET /api/predictions/{id}` round-trip,
concurrent-load chart requests (10 parallel, 0 errors), and the
OPENAI_API_KEY-missing failure path.

**Remaining/known issues, disclosed honestly:**
- No live OpenAI or X API call has been made this session (no real API keys
  available in this sandbox) -- the integration code is complete and its
  error/success branches are exercised via the graceful-degradation and
  credential-missing paths, but a live end-to-end synthesis/publish call has
  not been observed. Recommend running one real `/api/predict` call with a
  real `OPENAI_API_KEY` before considering the AI-synthesis path fully proven
  in production.
- `run_mundane_prediction()`'s live-network ayanamsha dependency (pre-existing,
  in `forecast.py`) will also fail in most sandboxed/firewalled production
  environments unless `allow_ayanamsha_fallback=True` is passed or that
  environment's egress allows astro.com.
- The in-memory rate limiter and scheduler state are per-process; a
  multi-instance Render deployment (if ever scaled beyond one instance) would
  need a shared store for both -- noted, not implemented, since the task
  explicitly asked not to overengineer the first version.

## 12. Cost optimization

- `ai/tools.py`'s 13 functions never call OpenAI -- every calculation Astrowatch
  already does locally stays local; OpenAI is invoked only for the
  entity/event-text understanding and final-prose steps.
- `ai/random_prediction.py`'s candidate selection is template + scoring based,
  zero OpenAI calls, even though it produces a different, non-repetitive
  result each time.
- `complete_json()` uses strict JSON-schema structured output (short,
  bounded, reliably parseable) instead of free-form "reply in JSON" prompting.
- `OPENAI_MAX_OUTPUT_TOKENS` (default 1200) and a hard 200-token ceiling on
  `mode="short"` synthesis calls bound worst-case per-call spend; both are
  configurable via environment, not hard-coded.
- `predictions_db.question_already_asked()` / `recent_predictions_for_entity()`
  exist specifically so a future scheduler/agent iteration can skip
  regenerating a near-duplicate prediction (wired into the scoring function
  today; a stricter hard-skip is a natural, easy follow-on, not implemented
  this pass to avoid overengineering the first version).
- Rate limiting (`RATE_LIMIT_MAX_REQUESTS`/`RATE_LIMIT_WINDOW_SECONDS`) caps
  worst-case request volume from any single client, which directly bounds
  worst-case OpenAI/X spend from abuse.
