"""Backward-compatible re-exports; prefer ``iapetus.database`` in new code."""
from __future__ import annotations

from iapetus.database import (
    SCHEMA_VERSION,
    default_learning_index_db_path,
    extract_run_index_row,
    index_learning_runs,
    init_learning_index_database,
    learning_index_status,
    list_indexed_runs,
    metrics_for_run_id,
    register_learning_run,
)

default_registry_db_path = default_learning_index_db_path
init_learning_registry = init_learning_index_database
registry_status = learning_index_status

__all__ = [
    "SCHEMA_VERSION",
    "default_registry_db_path",
    "extract_run_index_row",
    "index_learning_runs",
    "init_learning_registry",
    "list_indexed_runs",
    "metrics_for_run_id",
    "register_learning_run",
    "registry_status",
]
