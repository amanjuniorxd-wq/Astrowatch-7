"""
Astrowatch backtest — backtest_results.db connection management.

Mirrors historical/database.py's pattern exactly but points at a completely
separate file and schema. Never opens historical_events.db / historical_events_v2.db
for writing -- see repository.py for the read-only usage of the historical DB.
"""

import os
import sqlite3
from contextlib import contextmanager

_SCHEMA_FILENAME = "backtest_results_schema.sql"


def _schema_path() -> str:
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # astrowatch/
    return os.path.join(here, _SCHEMA_FILENAME)


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def initialize_db(db_path: str, overwrite: bool = False) -> sqlite3.Connection:
    if os.path.exists(db_path):
        if not overwrite:
            raise FileExistsError(
                f"{db_path} already exists. Pass overwrite=True if you really mean "
                f"to recreate it. Prefer a new experiment_id over recreating the file."
            )
        os.remove(db_path)
    conn = connect(db_path)
    with open(_schema_path()) as f:
        conn.executescript(f.read())
    conn.commit()
    return conn


@contextmanager
def db_session(db_path: str):
    conn = connect(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
