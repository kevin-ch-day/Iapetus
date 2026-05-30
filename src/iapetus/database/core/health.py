"""Kernel database inspection and health reporting."""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from iapetus.database.core.constants import KERNEL_SCHEMA_VERSION
import iapetus.database.core.connection as db_connection
from iapetus.database.core.migrations import SchemaAheadError, reconcile_schema_version
from iapetus.database.core.schema_meta import read_schema_version
from iapetus.database.schemas.learning_runs import LEARNING_RUNS_TABLE


def _list_user_tables(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        """
        SELECT name FROM sqlite_master
        WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name
        """
    ).fetchall()
    return [str(row[0]) for row in rows]


def _table_row_count(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()
    return int(row["n"]) if row is not None else 0


def kernel_database_health(*, db_path: Path | None = None) -> dict[str, Any]:
    """Summarize on-disk state, schema version, and table counts."""
    path = db_path or db_connection.default_kernel_db_path()
    exists = path.is_file()
    file_size_bytes = path.stat().st_size if exists else 0

    base: dict[str, Any] = {
        "db_path": str(path),
        "exists": exists,
        "file_size_bytes": file_size_bytes,
        "expected_schema_version": KERNEL_SCHEMA_VERSION,
        "stored_schema_version": None,
        "schema_current": False,
        "schema_ahead_of_code": False,
        "integrity_ok": None,
        "tables": [],
        "table_row_counts": {},
        "learning_run_count": 0,
        "latest_learning_run_id": None,
        "latest_learning_run_mode": None,
    }

    if not exists:
        return base

    conn = db_connection.open_connection(path)
    try:
        stored = read_schema_version(conn)
        base["stored_schema_version"] = stored
        base["schema_current"] = stored == KERNEL_SCHEMA_VERSION
        integrity = conn.execute("PRAGMA integrity_check").fetchone()
        base["integrity_ok"] = integrity is not None and integrity[0] == "ok"
        tables = _list_user_tables(conn)
        base["tables"] = tables
        counts = {name: _table_row_count(conn, name) for name in tables}
        base["table_row_counts"] = counts
        if LEARNING_RUNS_TABLE in tables:
            base["learning_run_count"] = counts.get(LEARNING_RUNS_TABLE, 0)
            latest = conn.execute(
                f"""
                SELECT run_id, mode FROM {LEARNING_RUNS_TABLE}
                ORDER BY created_at DESC
                LIMIT 1
                """
            ).fetchone()
            if latest is not None:
                base["latest_learning_run_id"] = latest["run_id"]
                base["latest_learning_run_mode"] = latest["mode"]
    finally:
        conn.close()

    try:
        with db_connection.kernel_connection(path) as conn:
            reconcile_schema_version(conn)
    except SchemaAheadError:
        base["schema_ahead_of_code"] = True

    return base
