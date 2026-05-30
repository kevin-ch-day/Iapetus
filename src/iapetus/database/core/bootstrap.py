"""Kernel database initialization — wires core connection + domain schemas."""
from __future__ import annotations

import sqlite3
from pathlib import Path

import iapetus.database.schemas  # noqa: F401 — register domain DDL appliers
import iapetus.database.core.connection as db_connection
from iapetus.database.core.constants import KERNEL_SCHEMA_VERSION, SCHEMA_VERSION
from iapetus.database.core.migrations import reconcile_schema_version
from iapetus.database.core.registry import apply_registered_domain_schemas
from iapetus.database.core.schema_meta import apply_schema_meta, write_schema_version


def _configure_connection(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")


def apply_kernel_schema(conn: sqlite3.Connection) -> None:
    """Create all kernel tables and persist the schema version."""
    _configure_connection(conn)
    apply_schema_meta(conn)
    apply_registered_domain_schemas(conn)
    write_schema_version(conn, KERNEL_SCHEMA_VERSION)


def init_kernel_database(db_path: Path | None = None) -> Path:
    """Ensure the kernel database file exists with the current schema."""
    path = db_path or db_connection.default_kernel_db_path()
    with db_connection.kernel_connection(path) as conn:
        apply_kernel_schema(conn)
        reconcile_schema_version(conn)
    return path


def init_learning_index_database(db_path: Path | None = None) -> Path:
    """Backward-compatible alias for :func:`init_kernel_database`."""
    return init_kernel_database(db_path)


def apply_schema(conn: sqlite3.Connection) -> None:
    """Backward-compatible alias for :func:`apply_kernel_schema`."""
    apply_kernel_schema(conn)
