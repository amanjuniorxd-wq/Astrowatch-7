"""
Astrowatch — historical_events.db connection management.

Deliberately separate from astronomy.db / panchang.db / backtest_results.db /
predictions.db -- this module never opens or references any of those.
"""

import os
import sqlite3
from contextlib import contextmanager

_SCHEMA_FILENAME = "historical_events_schema.sql"


def _schema_path() -> str:
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # astrowatch/
    return os.path.join(here, _SCHEMA_FILENAME)


def connect(db_path: str) -> sqlite3.Connection:
    """Open a connection with foreign-key enforcement ON (SQLite does not default
    to this -- see historical_events_schema.sql's header comment)."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def initialize_db(db_path: str, overwrite: bool = False) -> sqlite3.Connection:
    """Creates historical_events.db and applies the schema. Refuses to silently
    clobber an existing database unless overwrite=True is passed explicitly."""
    if os.path.exists(db_path):
        if not overwrite:
            raise FileExistsError(
                f"{db_path} already exists. Pass overwrite=True if you really mean "
                f"to recreate it (this destroys any existing data -- prefer creating "
                f"a new dataset_version instead of overwriting)."
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
