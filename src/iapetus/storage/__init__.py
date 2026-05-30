"""Legacy storage package; SQLite lives in ``iapetus.database``."""
from __future__ import annotations

from iapetus.database import (
    default_learning_index_db_path,
    extract_run_index_row,
    index_learning_runs,
    init_learning_index_database,
    learning_index_status,
    list_indexed_runs,
    register_learning_run,
)
from iapetus.storage.sqlite_learning_run_registry import (
    default_registry_db_path,
    init_learning_registry,
    registry_status,
)

__all__ = [
    "default_learning_index_db_path",
    "default_registry_db_path",
    "extract_run_index_row",
    "index_learning_runs",
    "init_learning_index_database",
    "init_learning_registry",
    "learning_index_status",
    "list_indexed_runs",
    "register_learning_run",
    "registry_status",
]
