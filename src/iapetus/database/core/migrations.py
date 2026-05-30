"""Schema version checks and migration hooks for the kernel database."""
from __future__ import annotations

import sqlite3
from pathlib import Path

from iapetus.database.core.constants import KERNEL_SCHEMA_VERSION
from iapetus.database.core.schema_meta import read_schema_version


class SchemaVersionError(RuntimeError):
    """Database schema is incompatible with this code version."""


class SchemaAheadError(SchemaVersionError):
    """On-disk schema is newer than the running code supports."""


def run_pending_migrations(
    conn: sqlite3.Connection,
    *,
    from_version: int,
    to_version: int = KERNEL_SCHEMA_VERSION,
) -> None:
    """Apply incremental migrations between stored and target versions."""
    if from_version >= to_version:
        return
    # v1 → v2+ migrations will be added here as tables evolve.
    for version in range(from_version + 1, to_version + 1):
        _migrate_to_version(conn, version)


def _migrate_to_version(conn: sqlite3.Connection, version: int) -> None:
    if version == 1:
        return
    raise SchemaVersionError(f"no migration implemented for schema version {version}")


def reconcile_schema_version(conn: sqlite3.Connection) -> int:
    """Run migrations when the stored version lags behind the code."""
    stored = read_schema_version(conn)
    if stored is None:
        return KERNEL_SCHEMA_VERSION
    if stored > KERNEL_SCHEMA_VERSION:
        raise SchemaAheadError(
            f"database schema v{stored} is ahead of code (supports v{KERNEL_SCHEMA_VERSION})"
        )
    run_pending_migrations(conn, from_version=stored, to_version=KERNEL_SCHEMA_VERSION)
    return KERNEL_SCHEMA_VERSION


def ensure_schema_compatible(db_path: Path) -> None:
    """Open the DB and migrate if the stored schema version is behind."""
    import iapetus.database.core.connection as db_connection

    with db_connection.kernel_connection(db_path) as conn:
        reconcile_schema_version(conn)
