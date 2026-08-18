# Astrowatch-2

Astrowatch correlates astrological configurations (Bṛhat Saṃhitā, Ptolemy's
Tetrabiblos, modern Lahiri/Vedic astrology) with real historical events, for
eventual blind backtesting. All code lives under `astrowatch/`.

**Status:** astronomy/astrology engine is PARTIALLY_VALIDATED (see
`astrowatch/docs/ASTRONOMY_VALIDATION_REPORT.md`). Historical event database is a
136-event pilot, frozen as `ASTROWATCH-HIST-001` (see
`astrowatch/HISTORICAL_DATA_QUALITY_REPORT.md` and `astrowatch/DATASET_FREEZE.md`).
No backtest engine exists yet — this repo does not claim to validate astrology.

## Setup

```bash
cd astrowatch
pip install -r requirements.txt --break-system-packages   # stdlib only; pyswisseph is optional, see requirements.txt
```

Everything below assumes you're inside the `astrowatch/` directory.

## Astronomy / astrology engine

Run the full test suite (astronomy + historical, from `astrowatch/`):

```bash
python3 -m unittest discover -s tests -t . -v
```

**Use `-t .`** — without it, `tests/historical/`'s package name collides with the
top-level `historical/` package and imports resolve to the wrong module (a real
issue hit and diagnosed this session, not hypothetical).

See `docs/ASTRONOMY_VALIDATION_REPORT.md` for the full validation history,
including exactly what executes cleanly in a given sandbox versus what depends on
live network access (astro.com / JPL Horizons — see that document's Phase 11 for
how to diagnose a proxy-allowlist-restricted environment versus a real code bug).

## Historical event database

```bash
python3 scripts/ingest_historical_data.py          # builds historical_events.db from scratch
python3 scripts/generate_control_dates.py           # adds reproducible control dates
python3 scripts/validate_historical_db.py            # flags issues, never silently repairs; exit code 1 on any FATAL
python3 scripts/generate_historical_quality_report.py # regenerates HISTORICAL_DATA_QUALITY_REPORT.md from the live DB
python3 scripts/freeze_historical_dataset.py          # freezes ASTROWATCH-HIST-001 (only do this once per version)
```

A quality-improvement successor, `ASTROWATCH-HIST-002`, was built in a separate
database file (`historical_events_v2.db`) via `scripts/ingest_historical_data_v2.py`
— it adds real WebSearch-verified corrections and real NOAA tsunami data without
touching `historical_events.db`'s frozen `ASTROWATCH-HIST-001`. See
`DATASET_FREEZE.md` for both versions' exact numbers and checksums.

Read-only access for any future backtest code:

```python
from historical import database, repository
conn = database.connect("historical_events.db")
events = repository.get_events(conn, category="NATURAL_DISASTER", min_source_quality=2)
```

### Dataset versioning

Once a `dataset_version` is frozen (see `historical_events_schema.sql`'s triggers),
its `events`/`control_dates` rows cannot be silently edited or deleted — any real
change requires creating a new version (`ASTROWATCH-HIST-002`, etc.), never editing
`001` in place. See `DATASET_FREEZE.md`.

### Source provenance principles

Every event links to at least one row in `sources` via `event_sources` (enforced —
`validate_historical_db.py` fails on any event with zero linked sources). Every
source is tiered 1 (primary/official) through 4 (discovery-only/uncited), and every
event's `verification_status` honestly reflects what was actually checked THIS
session, not what's presumed true — see `data_dictionary.md`'s "Verification
status, precisely" section, and `HISTORICAL_DATA_QUALITY_REPORT.md` for the real
breakdown (86% of this pilot's events are `UNVERIFIED` in this specific sense).

### Historical/astrological separation

`historical/` never imports astrology code, and astrology code never imports
`historical/` — mechanically enforced by
`tests/historical/test_astrological_independence.py`. Event selection for this
pilot never used any astrological criterion (no searching for events near a
particular planetary configuration). See `astrowatch/historical/__init__.py` and
`HISTORICAL_DATABASE_ARCHITECTURE.md` for the full boundary and data-flow diagram.

## Astrowatch Online -- AI-assisted prediction platform

Built on top of (not replacing) everything above. See
`ARCHITECTURE_REPORT_ONLINE.md` for the full architecture audit/design, and
`ONLINE_PLATFORM_DELIVERABLE.md` for the complete final deliverable report
(files, endpoints, env vars, database schemas, testing results, cost
optimization). Short version:

- The Swiss Ephemeris / Jyotisha / Hellenistic / Western / Chinese /
  cross-tradition engine above remains 100% authoritative for every number.
- `astrowatch/ai/` is a new, additive intelligence/orchestration/synthesis
  layer (OpenAI) that calls into the existing engine via a fixed tool surface
  (`ai/tools.py`) -- it never computes astronomy/astrology itself.
- `astrowatch/entities_db.py` / `predictions_db.py` are new SQLite stores
  (entity database seeded from the project's own real corpora; prediction
  history/outcome tracking).
- `astrowatch/x/` is an optional, disabled-by-default X (Twitter) publisher.
- `astrowatch/scheduler.py` runs the autonomous agent automatically.

### Running locally

```bash
cd astrowatch
pip install -r requirements.txt --break-system-packages
cp ../.env.example ../.env   # then fill in OPENAI_API_KEY if you want the AI layer
python3 api.py                # binds 0.0.0.0:8420 by default
curl http://127.0.0.1:8420/health
```

### Deploying to Render

1. Push this repo to GitHub/GitLab (Render deploys from a git remote).
2. In Render: **New -> Web Service**, connect the repo.
3. **Root Directory:** `astrowatch` (or leave blank and use `cd astrowatch &&`
   in the build/start commands below).
4. **Build Command:**
   ```
   pip install -r ../requirements.txt
   ```
5. **Start Command:**
   ```
   python astrowatch/api.py
   ```
   (adjust paths if you set Root Directory to `astrowatch` -- then it's just
   `pip install -r requirements.txt` and `python api.py`.)
6. **Runtime:** Python 3.11 (see `.python-version` at the repo root).
7. **Environment variables** (Render dashboard -> Environment): see
   `.env.example` at the repo root for the full list. At minimum for the AI
   layer to work:
   - `OPENAI_API_KEY`
   - `OPENAI_MODEL` (optional -- defaults to `gpt-4o-mini` in code)
   - Render sets `PORT` automatically; api.py reads it automatically. Do not
     set `PORT` manually on Render.
   - `X_ENABLED` -- leave `false` (or unset) unless you also set all four
     `X_*` credential variables.
   - `PREDICTIONS_PER_DAY` -- optional, defaults to `2`.
   - `ASTROWATCH_SCHEDULER_ENABLED=true` -- set this if you want the
     autonomous scheduler to run inside the same web-service process (simplest
     setup for a single Render instance; for a separate worker, run
     `python scheduler.py` as its own Render Background Worker instead and
     leave this unset on the web service).
8. Deploy. Verify with `GET https://<your-service>.onrender.com/health` --
   expect `{"status":"ok","astrowatch":"online","openai":"configured"}`.

### Testing before deployment

```bash
cd astrowatch
python3 -m pytest -q                       # full suite, expect 361 passed
python3 api.py &                            # start locally
curl http://127.0.0.1:8420/health
curl -X POST http://127.0.0.1:8420/api/chart -d '{"date":"2000-05-17","time":"14:30:00","timezone":"Asia/Kolkata","latitude":28.6139,"longitude":77.2090}'
curl -X POST http://127.0.0.1:8420/api/predict -d '{"entity":"India","entity_type":"country","question":"q?","mode":"short"}'
curl -X POST http://127.0.0.1:8420/api/agent/run -d '{"dry_run":true}'
```
