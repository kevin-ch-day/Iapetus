"""Base class for kernel SQLite repositories."""
from __future__ import annotations

from pathlib import Path

import iapetus.database.core.connection as db_connection
from iapetus.database.core.kernel_database import KernelDatabase


class KernelRepository:
    """Shared DB path resolution and bootstrap for repository implementations."""

    def __init__(self, db_path: Path | None = None) -> None:
        self._db_path = db_path
        self._kernel = KernelDatabase(db_path=db_path)

    @property
    def db_path(self) -> Path:
        return self._db_path or db_connection.default_kernel_db_path()

    @property
    def kernel(self) -> KernelDatabase:
        return self._kernel

    def ensure_database(self) -> Path:
        return self._kernel.initialize()

    def connection(self):
        return db_connection.kernel_connection(self.db_path)
