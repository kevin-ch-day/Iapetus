"""SQLite connection layer for the Iapetus kernel database."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from iapetus.project_filesystem_paths import LEARNING_INDEX_DB_PATH

KERNEL_DB_FILENAME = "iapetus_learning.db"

# Legacy alias used across docs and CLI.
LEARNING_INDEX_DB_FILENAME = KERNEL_DB_FILENAME


def default_kernel_db_path() -> Path:
    """Return the default on-disk path for the kernel SQLite database."""
    return LEARNING_INDEX_DB_PATH


def default_learning_index_db_path() -> Path:
    """Backward-compatible alias for :func:`default_kernel_db_path`."""
    return default_kernel_db_path()


def open_connection(db_path: Path | None = None) -> sqlite3.Connection:
    """Open a connection with ``sqlite3.Row`` row factory."""
    path = db_path or default_kernel_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def connect_learning_index(db_path: Path | None = None) -> sqlite3.Connection:
    """Backward-compatible alias for :func:`open_connection`."""
    return open_connection(db_path)


@contextmanager
def kernel_connection(db_path: Path | None = None) -> Iterator[sqlite3.Connection]:
    """Open a connection, commit on success, and always close."""
    conn = open_connection(db_path)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


@contextmanager
def learning_index_connection(db_path: Path | None = None) -> Iterator[sqlite3.Connection]:
    """Backward-compatible alias for :func:`kernel_connection`."""
    with kernel_connection(db_path) as conn:
        yield conn
