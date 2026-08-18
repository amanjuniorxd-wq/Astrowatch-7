"""
Astrowatch — POST /api/chart backend
========================================
Stdlib-only HTTP server (http.server) exposing the single authoritative chart
calculation endpoint this session's migration spec calls for. No third-party web
framework dependency, consistent with this project's existing "no required
third-party dependencies beyond what's strictly needed" stance (see requirements.txt)
-- pyswisseph is the one real, load-bearing exception, already required by kundli.py.

ENDPOINT
--------
POST /api/chart
Request body (JSON):
    {
      "date": "2000-05-17",
      "time": "14:30:00",
      "timezone": "Asia/Kolkata",     // IANA zone name (preferred)
      "latitude": 28.6139,
      "longitude": 77.2090
    }
  OR, if a real timezone name isn't available:
    { ..., "utc_offset_hours": 5.5 }  // instead of "timezone" -- see timeutil.py's
                                       // own caveats about this fallback path.

Response (JSON): input echo, Julian Day, ayanamsha, all 9 graha placements, Ascendant,
houses (whole-sign), Rashi/Nakshatra/Pada, Mahadasha + Antardasha, and engine/version
metadata. See build_chart_response() below for the exact shape.

NO SILENT FALLBACK: if Swiss Ephemeris data is unavailable (kundli.EphemerisDataUnavailable)
or the request is otherwise malformed, this returns a clear 4xx/5xx JSON error body --
it never substitutes an approximate calculation.

RUNNING: `python3 astrowatch/api.py` (see README.md's Local Development section for
the full setup). Binds to 0.0.0.0:$PORT (default 8420) -- 0.0.0.0 so the server is
reachable from outside its container on a cloud platform (Render etc.); set HOST=127.0.0.1
explicitly for a localhost-only dev setup. GET /health added for platform health checks.
"""

import json
import os
import threading
import time
from collections import defaultdict, deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import coordinates
from kundli import compute_kundli, EphemerisDataUnavailable
from mahadasha import compute_dasha_state, DASHA_SEQUENCE
from timeutil import local_to_jd_ut, utc_offset_to_jd_ut, UnknownTimezone

# --- Basic rate limiting (security/cost control, task spec Section 25) -----
# Simple in-memory sliding-window limiter, per client IP, applied to every
# POST endpoint (the AI-calling ones in particular -- this directly bounds
# worst-case OpenAI/X API spend from a single abusive client). Intentionally
# simple (no external dependency, no Redis) -- adequate for a single-process
# deployment; a multi-instance production deployment would need a shared
# store instead, noted here rather than silently pretended away.
_RATE_LIMIT_MAX_REQUESTS = int(os.environ.get("RATE_LIMIT_MAX_REQUESTS", "30"))
_RATE_LIMIT_WINDOW_SECONDS = int(os.environ.get("RATE_LIMIT_WINDOW_SECONDS", "60"))
_rate_limit_lock = threading.Lock()
_rate_limit_hits = defaultdict(deque)


def _rate_limited(client_ip: str) -> bool:
    now = time.time()
    with _rate_limit_lock:
        hits = _rate_limit_hits[client_ip]
        while hits and now - hits[0] > _RATE_LIMIT_WINDOW_SECONDS:
            hits.popleft()
        if len(hits) >= _RATE_LIMIT_MAX_REQUESTS:
            return True
        hits.append(now)
        return False


# --- Max request body size (security, prevents unbounded-memory JSON bodies) --
_MAX_BODY_BYTES = int(os.environ.get("MAX_REQUEST_BODY_BYTES", str(256 * 1024)))  # 256 KB

ENGINE_NAME = "Swiss Ephemeris"
ENGINE_LIBRARY = "pyswisseph (file-based, SEFLG_SWIEPH + SEFLG_SIDEREAL)"
AYANAMSHA_NAME = "Lahiri"


def _graha_to_dict(g) -> dict:
    return {
        "planet": g.graha,
        "longitude": round(g.sidereal_lon_deg, 6),
        "tropical_longitude": round(g.tropical_lon_deg, 6),
        "latitude": round(g.latitude_deg, 6),
        "distance_au": round(g.distance_au, 6),
        "speed_deg_per_day": round(g.speed_lon_deg_per_day, 6),
        "retrograde": g.retrograde,
        "sign": g.rashi.rashi_name,
        "degree_in_sign": round(g.rashi.degree_in_rashi, 6),
        "nakshatra": g.nakshatra.nakshatra_name,
        "nakshatra_index": g.nakshatra.nakshatra_index,
        "pada": g.nakshatra.pada,
        "degrees_into_nakshatra": round(g.nakshatra.degree_in_nakshatra, 6),
        "remaining_degrees_in_nakshatra": round(
            (13 + 1 / 3) - g.nakshatra.degree_in_nakshatra, 6),
        "house": g.house,
    }


def _dasha_to_dict(d) -> dict:
    return {
        "lord": d.lord,
        "start": coordinates.julian_day and _jd_to_iso(d.start_jd_ut),
        "end": _jd_to_iso(d.end_jd_ut),
        "level": d.level,
    }


def _jd_to_iso(jd_ut: float) -> str:
    # Fliegel & Van Flandern JD -> Gregorian calendar conversion (standard algorithm).
    jd = jd_ut + 0.5
    z = int(jd)
    f = jd - z
    if z < 2299161:
        a = z
    else:
        alpha = int((z - 1867216.25) / 36524.25)
        a = z + 1 + alpha - alpha // 4
    b = a + 1524
    c = int((b - 122.1) / 365.25)
    d_ = int(365.25 * c)
    e = int((b - d_) / 30.6001)
    day = b - d_ - int(30.6001 * e) + f
    month = e - 1 if e < 14 else e - 13
    year = c - 4716 if month > 2 else c - 4715
    day_int = int(day)
    hour_frac = (day - day_int) * 24
    hh = int(hour_frac)
    mm = int((hour_frac - hh) * 60)
    return f"{year:04d}-{month:02d}-{day_int:02d}T{hh:02d}:{mm:02d}:00Z"


class ChartRequestError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.message = message
        self.status = status


def build_chart_response(payload: dict) -> dict:
    date_str = payload.get("date")
    time_str = payload.get("time")
    latitude = payload.get("latitude")
    longitude = payload.get("longitude")
    timezone_name = payload.get("timezone")
    utc_offset_hours = payload.get("utc_offset_hours")

    if not date_str or not time_str:
        raise ChartRequestError("Both 'date' (YYYY-MM-DD) and 'time' (HH:MM[:SS]) are required.")
    if latitude is None or longitude is None:
        raise ChartRequestError("Both 'latitude' and 'longitude' (numeric degrees) are required.")
    if not timezone_name and utc_offset_hours is None:
        raise ChartRequestError("Provide either 'timezone' (IANA zone name, preferred) or 'utc_offset_hours'.")

    try:
        if timezone_name:
            time_result = local_to_jd_ut(date_str, time_str, timezone_name)
        else:
            time_result = utc_offset_to_jd_ut(date_str, time_str, float(utc_offset_hours))
    except UnknownTimezone as e:
        raise ChartRequestError(str(e)) from e
    except ValueError as e:
        raise ChartRequestError(f"Could not parse date/time: {e}") from e

    try:
        chart = compute_kundli(time_result.jd_ut, float(latitude), float(longitude))
    except EphemerisDataUnavailable as e:
        raise ChartRequestError(f"Calculation error: {e}", status=503) from e

    dasha_state = compute_dasha_state(time_result.jd_ut, chart.grahas["moon"].sidereal_lon_deg)

    return {
        "input": {
            "date": date_str, "time": time_str,
            "timezone": timezone_name, "utc_offset_hours": utc_offset_hours,
            "latitude": latitude, "longitude": longitude,
        },
        "time_debug": {
            "input_local_datetime": time_result.input_local_datetime,
            "timezone": time_result.timezone_name,
            "utc_datetime": time_result.utc_datetime,
            "julian_day_ut": time_result.jd_ut,
        },
        "engine": ENGINE_NAME,
        "engine_library": ENGINE_LIBRARY,
        "ayanamsha_name": AYANAMSHA_NAME,
        "ayanamsha_degrees": round(chart.ayanamsha_deg, 6),
        "sidereal": True,
        "node_convention": chart.node_convention,
        "house_system": chart.house_system,
        "ascendant": {
            "longitude": round(chart.ascendant_sidereal_deg, 6),
            "tropical_longitude": round(chart.ascendant_tropical_deg, 6),
            "sign": chart.ascendant_rashi.rashi_name,
            "degree_in_sign": round(chart.ascendant_rashi.degree_in_rashi, 6),
            "nakshatra": chart.ascendant_nakshatra.nakshatra_name,
            "pada": chart.ascendant_nakshatra.pada,
        },
        "planets": {name: _graha_to_dict(g) for name, g in chart.grahas.items()},
        "mahadasha": {
            "lord": dasha_state.mahadasha.lord,
            "start": _jd_to_iso(dasha_state.mahadasha.start_jd_ut),
            "end": _jd_to_iso(dasha_state.mahadasha.end_jd_ut),
        },
        "antardasha": {
            "lord": dasha_state.antardasha.lord,
            "start": _jd_to_iso(dasha_state.antardasha.start_jd_ut),
            "end": _jd_to_iso(dasha_state.antardasha.end_jd_ut),
        },
        "vimshottari_sequence": [{"lord": l, "years": y} for l, y in DASHA_SEQUENCE],
    }


class ChartHandler(BaseHTTPRequestHandler):
    def _send_json(self, status: int, body: dict):
        data = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _read_json_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        if length > _MAX_BODY_BYTES:
            raise ValueError(f"Request body too large ({length} bytes, max {_MAX_BODY_BYTES}).")
        raw = self.rfile.read(length) if length else b""
        return json.loads(raw) if raw else {}

    def do_POST(self):
        path = self.path.split("?", 1)[0]

        client_ip = self.client_address[0] if self.client_address else "unknown"
        if _rate_limited(client_ip):
            self._send_json(429, {
                "error": f"Rate limit exceeded: max {_RATE_LIMIT_MAX_REQUESTS} requests per "
                         f"{_RATE_LIMIT_WINDOW_SECONDS}s per client. Try again shortly.",
            })
            return

        try:
            payload = self._read_json_body()
        except json.JSONDecodeError:
            self._send_json(400, {"error": "Request body is not valid JSON."})
            return
        except ValueError as e:
            self._send_json(413, {"error": str(e)})
            return
        if not isinstance(payload, dict):
            self._send_json(400, {"error": "Request body must be a JSON object."})
            return

        if path == "/api/chart":
            try:
                response = build_chart_response(payload)
                self._send_json(200, response)
            except ChartRequestError as e:
                self._send_json(e.status, {"error": e.message})
            except Exception as e:  # noqa: BLE001 -- last-resort catch, still returns clear JSON, no fallback calc
                self._send_json(500, {"error": f"Unexpected server error: {e}"})
            return

        if path == "/api/predict":
            self._handle_predict(payload)
            return

        if path == "/api/random-prediction":
            self._handle_random_prediction(payload)
            return

        if path == "/api/current-event":
            self._handle_current_event(payload)
            return

        if path == "/api/agent/run":
            self._handle_agent_run(payload)
            return

        if path == "/api/world-prediction":
            self._handle_world_prediction(payload)
            return

        self._send_json(404, {"error": f"Unknown endpoint {path!r}. See GET / for the endpoint list."})

    def _handle_predict(self, payload: dict):
        from ai.prediction_agent import run_prediction, PredictionInputError
        try:
            result = run_prediction(payload)
            self._send_json(200, result)
        except PredictionInputError as e:
            self._send_json(400, {"error": str(e)})
        except Exception as e:  # noqa: BLE001 -- never a silent/fabricated reading, always a clear JSON error
            self._send_json(500, {"error": f"Unexpected server error in /api/predict: {e}"})

    def _handle_random_prediction(self, payload: dict):
        from ai.random_prediction import generate_random_prediction
        category = payload.get("category")
        mode = payload.get("mode", "short")
        try:
            result = generate_random_prediction(category=category, mode=mode)
            self._send_json(200, result)
        except ValueError as e:
            self._send_json(400, {"error": str(e)})
        except Exception as e:  # noqa: BLE001
            self._send_json(500, {"error": f"Unexpected server error in /api/random-prediction: {e}"})

    def _handle_agent_run(self, payload: dict):
        from ai.agent import run as run_agent
        dry_run = bool(payload.get("dry_run", False))
        category = payload.get("category")
        mode = payload.get("mode", "detailed")
        try:
            result = run_agent(dry_run=dry_run, category=category, mode=mode)
            if not dry_run and payload.get("publish_to_x") and result.get("prediction_id"):
                from x.publisher import publish_prediction
                result["x_publish"] = publish_prediction(result["prediction_id"])
            self._send_json(200, result)
        except ValueError as e:
            self._send_json(400, {"error": str(e)})
        except Exception as e:  # noqa: BLE001
            self._send_json(500, {"error": f"Unexpected server error in /api/agent/run: {e}"})

    def _handle_world_prediction(self, payload: dict):
        from ai.world_prediction_agent import run_world_prediction
        from ai.prediction_agent import PredictionInputError
        try:
            result = run_world_prediction(payload)
            self._send_json(200, result)
        except PredictionInputError as e:
            self._send_json(400, {"error": str(e)})
        except Exception as e:  # noqa: BLE001 -- never a silent/fabricated reading, always a clear JSON error
            self._send_json(500, {"error": f"Unexpected server error in /api/world-prediction: {e}"})

    def _handle_current_event(self, payload: dict):
        from ai.event_scanner import analyze_current_event
        from ai.openai_client import AIUnavailable
        event_text = payload.get("event_text") or payload.get("text")
        if not event_text:
            self._send_json(400, {"error": "'event_text' (the news headline/summary to analyze) is required."})
            return
        mode = payload.get("mode", "detailed")
        try:
            result = analyze_current_event(event_text, mode=mode)
            self._send_json(200, result)
        except AIUnavailable as e:
            self._send_json(503, {
                "error": "AI-driven current-event extraction requires OPENAI_API_KEY "
                         "to be configured (no rule-based fallback exists for free-text "
                         "event understanding -- this project never fabricates that "
                         "analysis). Astrowatch's calculation endpoints (POST /api/chart, "
                         "POST /api/predict with a known entity) work without it.",
                "detail": str(e),
            })
        except Exception as e:  # noqa: BLE001
            self._send_json(500, {"error": f"Unexpected server error in /api/current-event: {e}"})

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/health":
            self._send_json(200, {
                "status": "ok",
                "astrowatch": "online",
                "openai": "configured" if os.environ.get("OPENAI_API_KEY") else "not_configured",
            })
        elif path == "/":
            self._send_json(200, {
                "status": "ok", "engine": ENGINE_NAME,
                "endpoints": [
                    "GET /health", "POST /api/chart", "POST /api/predict",
                    "POST /api/agent/run", "POST /api/random-prediction",
                    "POST /api/current-event", "POST /api/world-prediction",
                    "GET /api/predictions", "GET /api/predictions/{id}",
                ],
            })
        elif path == "/api/predictions":
            self._handle_list_predictions()
        elif path.startswith("/api/predictions/"):
            self._handle_get_prediction(path[len("/api/predictions/"):])
        else:
            self._send_json(404, {"error": "Not found. See GET / for the endpoint list."})

    def _handle_list_predictions(self):
        from urllib.parse import urlparse, parse_qs
        import predictions_db
        qs = parse_qs(urlparse(self.path).query)
        entity = qs.get("entity", [None])[0]
        mode = qs.get("mode", [None])[0]
        try:
            limit = int(qs.get("limit", ["50"])[0])
        except ValueError:
            limit = 50
        conn = predictions_db.get_connection()
        rows = predictions_db.get_prediction_history(conn, entity=entity, mode=mode, limit=limit)
        self._send_json(200, {"count": len(rows), "predictions": [r.__dict__ for r in rows]})

    def _handle_get_prediction(self, prediction_id: str):
        import predictions_db
        conn = predictions_db.get_connection()
        row = predictions_db.get_prediction(conn, prediction_id)
        if row is None:
            self._send_json(404, {"error": f"No prediction with id={prediction_id!r}."})
            return
        self._send_json(200, row.__dict__)

    def log_message(self, format, *args):  # noqa: A002 -- quiet default stdout logging
        pass


def run(port: int = None, host: str = None):
    """Production-ready entry point. Binds 0.0.0.0 by default (required to be
    reachable inside a container on Render/any cloud platform) and reads the
    listening port from the PORT environment variable, per platform convention
    (the platform assigns PORT at runtime; do not hard-code it). Local
    development is unaffected -- PORT defaults to 8420 exactly as before, and
    passing host="127.0.0.1" explicitly still works for anyone who wants to
    restrict to localhost only."""
    host = host or os.environ.get("HOST", "0.0.0.0")
    port = port or int(os.environ.get("PORT", "8420"))

    if os.environ.get("ASTROWATCH_SCHEDULER_ENABLED", "").lower() in ("1", "true", "yes"):
        import scheduler
        scheduler.start_background_thread()
        print("Astrowatch autonomous scheduler started "
              f"(PREDICTIONS_PER_DAY={os.environ.get('PREDICTIONS_PER_DAY', '2')}).")

    server = ThreadingHTTPServer((host, port), ChartHandler)
    print(f"Astrowatch API listening on http://{host}:{port}  "
          f"(POST /api/chart, POST /api/predict, POST /api/agent/run, GET /health, ...)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    run()
