# Astrowatch — local development setup (Swiss Ephemeris backend)

This covers running the Swiss-Ephemeris-backed chart engine added in this session's
migration (see `ARCHITECTURE_SE_MIGRATION.md` for the full audit/before-after report).
Everything below is run from inside the `astrowatch/` directory unless noted.

## 1. Python version

Python 3.9+ is required (the timezone module, `timeutil.py`, uses the standard-library
`zoneinfo`, added in 3.9). This project was built and tested against **Python 3.10.12**.

## 2. Dependencies

One required third-party dependency: `pyswisseph` (the Python binding for the actual
Swiss Ephemeris C library). Everything else in the project — including the new
`api.py`, `timeutil.py`, `kundli.py`, `mahadasha.py`, `rashi_nakshatra.py` — uses only
the Python standard library (no Flask/FastAPI/etc.; see `api.py`'s own docstring for
why a web framework was deliberately not added).

```
pyswisseph==2.10.3.2
```

See `requirements.txt` at the repo root.

## 3. Installation

```bash
pip install -r ../requirements.txt --break-system-packages
```

(`--break-system-packages` is only needed on systems with an externally-managed Python;
drop it if you're using a virtualenv, which is the normal recommendation for a real
deployment — a venv wasn't used in this session's sandbox for practical reasons, but
there's nothing venv-incompatible about this project.)

Verify the install:

```bash
python3 -c "import swisseph as swe; print(swe.version)"
# should print: 2.10.03
```

## 4. Swiss Ephemeris data installation

`kundli.py` needs real `.se1` Swiss Ephemeris data files on disk — it refuses to run in
Swiss Ephemeris's built-in "Moshier" approximation mode (see
`ARCHITECTURE_SE_MIGRATION.md` item 1 for why that distinction matters: Moshier mode
needs no files but is much lower precision than the file-based mode this project
validated against a live reference this session).

**They're already included in this repo** at `astrowatch/ephemeris/` (`sepl_18.se1`,
`semo_18.se1`, `seas_18.se1`, plus the `_12`/`_24` 600-year-block neighbors — see
`astrowatch/ephemeris/README.md` for exactly where these came from and their known
precision caveats). Nothing further to download for normal use.

To point at a different/newer file set instead (e.g. if you can reach Astrodienst's own
distribution directly — this session's sandbox couldn't, see that same README):

```bash
export SWEPH_EPHE_PATH=/path/to/your/ephemeris/directory
```

`kundli.py` reads `SWEPH_EPHE_PATH` at import time and raises
`EphemerisDataUnavailable` immediately, with a clear message, if the required files
aren't found there — it does not fall back silently.

## 5. Environment variables

| Variable          | Required? | Default                              | Purpose                                   |
|--------------------|-----------|---------------------------------------|--------------------------------------------|
| `SWEPH_EPHE_PATH`  | No        | `astrowatch/ephemeris/` (relative to `kundli.py`) | Directory containing the `.se1` files |
| `PORT`             | No        | `8420`                                | Port `api.py`'s HTTP server binds to      |

## 6. Starting the backend

```bash
cd astrowatch
python3 api.py
```

This starts a stdlib `http.server`-based API at `http://127.0.0.1:8420`, exposing:

- `GET /health` — liveness check, returns `{"status": "ok", ...}`
- `POST /api/chart` — the chart calculation endpoint (see `api.py`'s docstring for the
  full request/response shape)

Quick smoke test in a second terminal:

```bash
curl -X POST http://127.0.0.1:8420/api/chart \
  -H "Content-Type: application/json" \
  -d '{"date":"2000-05-17","time":"22:00:00","timezone":"Asia/Kolkata","latitude":25.5941,"longitude":85.1376}'
```

## 7. Starting the frontend

The kundli web app (`astrowatch/kundli_mass/astrowatch_kundli_life_report.html`) is a
static file — no build step. With the backend running (step 6), open the HTML file
directly in a browser, or serve it locally:

```bash
cd astrowatch/kundli_mass
python3 -m http.server 8000
# then open http://127.0.0.1:8000/astrowatch_kundli_life_report.html
```

The other two static apps in the same directory
(`astrowatch_daily_predictions.html`, `astrowatch_4_predictions.html`,
`astrowatch_tarot_reading.html`) are unrelated to the chart API — they read
precomputed/embedded data and don't need the backend running.

## 8. Running tests

Full suite, from `astrowatch/`:

```bash
python3 -m pytest -q
```

Just the Swiss Ephemeris migration's own tests:

```bash
python3 -m pytest tests/test_kundli_mahadasha.py tests/test_swe_boundary.py tests/test_swe_live_comparison.py -v
```

`test_swe_live_comparison.py` is a **fixed-data regression test** — it compares the
local engine's output against 14 real reference values fetched live from astro.com's
Swiss Ephemeris server *this session* (recorded in
`tests/_se_live_reference_data.py`), not a live network call at test time. It will pass
offline and won't flake if astro.com is unreachable later; it just won't catch a *new*
divergence from Astrodienst's own server going forward. See
`ARCHITECTURE_SE_MIGRATION.md` for the full methodology and measured numbers.
