"""``schema_meta`` table — version and future kernel metadata keys."""
from __future__ import annotations

import sqlite3

SCHEMA_META_TABLE = "schema_meta"
SCHEMA_VERSION_KEY = "schema_version"

_SCHEMA_META_DDL = f"""
CREATE TABLE IF NOT EXISTS {SCHEMA_META_TABLE} (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
)
"""


def apply_schema_meta(conn: sqlite3.Connection) -> None:
    conn.execute(_SCHEMA_META_DDL)


def read_schema_version(conn: sqlite3.Connection) -> int | None:
    row = conn.execute(
        f"SELECT value FROM {SCHEMA_META_TABLE} WHERE key = ?",
        (SCHEMA_VERSION_KEY,),
    ).fetchone()
    if row is None:
        return None
    try:
        return int(row["value"])
    except (TypeError, ValueError):
        return None


def write_schema_version(conn: sqlite3.Connection, version: int) -> None:
    conn.execute(
        f"INSERT OR REPLACE INTO {SCHEMA_META_TABLE} (key, value) VALUES (?, ?)",
        (SCHEMA_VERSION_KEY, str(version)),
    )
