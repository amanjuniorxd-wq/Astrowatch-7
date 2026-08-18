"""
Astrowatch Online -- autonomous scheduler.
=============================================
Simple in-process scheduler (no external cron/task-queue dependency, matching
this project's stdlib-first convention) that runs ai.agent.run() automatically
PREDICTIONS_PER_DAY times per day (default 2), spread across configurable
posting windows.

CONFIGURATION (env vars, never hard-coded):
    PREDICTIONS_PER_DAY              default 2
    PREDICTION_POSTING_WINDOWS_UTC   comma-separated 24h UTC hours, e.g. "09,18".
                                      If unset, windows are spread evenly across
                                      the day starting at 00:00 UTC.

This module does not publish to X itself (see x/publisher.py, Phase 7,
X_ENABLED gated) -- it only runs the agent and lets the resulting prediction
sit in predictions_db; publishing is a separate, explicitly-opted-into step.

Run standalone with `python3 scheduler.py` for a long-running foreground
scheduler process, or import `run_due_predictions_if_needed()` / start_thread()
to embed it inside api.py's process (see api.py's optional
AUTOWATCH_SCHEDULER_ENABLED wiring).
"""

import datetime
import os
import threading
import time as _time
from typing import List, Optional

_STOP = threading.Event()


def _configured_windows() -> List[int]:
    raw = os.environ.get("PREDICTION_POSTING_WINDOWS_UTC", "").strip()
    n = int(os.environ.get("PREDICTIONS_PER_DAY", "2") or "2")
    if raw:
        hours = sorted(int(h) for h in raw.split(",") if h.strip() != "")
        if hours:
            return hours[:n] if len(hours) >= n else hours
    if n <= 0:
        return []
    step = 24.0 / n
    return sorted(int(round(i * step)) % 24 for i in range(n))


def _today_key() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")


def run_due_predictions_if_needed(state: Optional[dict] = None) -> List[dict]:
    """Checks whether the current UTC hour matches a configured posting window
    and, if so and it hasn't already run this hour today, runs one autonomous
    prediction via ai.agent.run(dry_run=False). `state` is an in-memory dict
    the caller keeps across calls (keys: 'date', 'hours_run' -- a set) so this
    function is safe to call frequently (e.g. every minute) without
    double-firing within the same hour. Returns a list of results produced
    this call (usually 0 or 1)."""
    if state is None:
        state = {}
    now = datetime.datetime.now(datetime.timezone.utc)
    today = _today_key()
    if state.get("date") != today:
        state["date"] = today
        state["hours_run"] = set()

    windows = _configured_windows()
    produced = []
    if now.hour in windows and now.hour not in state["hours_run"]:
        state["hours_run"].add(now.hour)
        from ai.agent import run as run_agent
        try:
            result = run_agent(dry_run=False)
            produced.append(result)
        except Exception as e:  # noqa: BLE001 -- scheduler must never crash the process
            produced.append({"error": str(e), "hour": now.hour})
    return produced


def start_background_thread(poll_seconds: int = 60) -> threading.Thread:
    """Starts a daemon thread that calls run_due_predictions_if_needed() every
    poll_seconds. Intended to be started once from api.py at server startup
    when AUTOWATCH_SCHEDULER_ENABLED=true."""
    state: dict = {}

    def loop():
        while not _STOP.is_set():
            try:
                run_due_predictions_if_needed(state)
            except Exception:  # noqa: BLE001 -- scheduler thread must never die
                pass
            _STOP.wait(poll_seconds)

    t = threading.Thread(target=loop, daemon=True, name="astrowatch-scheduler")
    t.start()
    return t


def stop():
    _STOP.set()


if __name__ == "__main__":
    print(f"Astrowatch scheduler: PREDICTIONS_PER_DAY="
          f"{os.environ.get('PREDICTIONS_PER_DAY', '2')}, windows(UTC hour)="
          f"{_configured_windows()}. Polling every 60s. Ctrl-C to stop.")
    state: dict = {}
    try:
        while True:
            produced = run_due_predictions_if_needed(state)
            for p in produced:
                print(f"[{datetime.datetime.now(datetime.timezone.utc).isoformat()}] "
                      f"produced: {p.get('entities') or p.get('error')}")
            _time.sleep(60)
    except KeyboardInterrupt:
        print("stopped")
