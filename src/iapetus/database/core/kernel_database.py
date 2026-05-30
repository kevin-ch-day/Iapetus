"""High-level handle for the Iapetus kernel SQLite database."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

import sqlite3

from iapetus.database.core.bootstrap import init_kernel_database
import iapetus.database.core.connection as db_connection
from iapetus.database.core.health import kernel_database_health
from iapetus.database.core.migrations import ensure_schema_compatible


@dataclass
class KernelDatabase:
    """Entry point for kernel DB lifecycle (init, health, connections)."""

    db_path: Path | None = field(default=None)

    def resolved_path(self) -> Path:
        return self.db_path or db_connection.default_kernel_db_path()

    def initialize(self) -> Path:
        """Create tables and record schema version if needed."""
        return init_kernel_database(self.db_path)

    def ensure_compatible(self) -> None:
        """Run migrations when the on-disk schema lags behind the code."""
        path = self.initialize()
        ensure_schema_compatible(path)

    def health(self) -> dict[str, Any]:
        return kernel_database_health(db_path=self.db_path)

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        """Open a connection after ensuring the database file and schema exist."""
        path = self.initialize()
        with db_connection.kernel_connection(path) as conn:
            yield conn


def default_kernel_database() -> KernelDatabase:
    return KernelDatabase()
