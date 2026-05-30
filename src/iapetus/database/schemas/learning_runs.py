"""Learning-run index table (M6 seed schema)."""
from __future__ import annotations

import sqlite3

LEARNING_RUNS_TABLE = "learning_runs"

_LEARNING_RUNS_DDL = f"""
CREATE TABLE IF NOT EXISTS {LEARNING_RUNS_TABLE} (
    run_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    mode TEXT NOT NULL,
    status TEXT NOT NULL,
    model_name TEXT NOT NULL,
    dataset_name TEXT NOT NULL,
    entity_count INTEGER NOT NULL DEFAULT 0,
    run_dir TEXT NOT NULL,
    backend TEXT,
    entity_loocv REAL,
    classification_train_accuracy REAL,
    malware_subgroup_train REAL,
    benign_subgroup_train REAL,
    indexed_at TEXT NOT NULL
)
"""


def apply_learning_runs_schema(conn: sqlite3.Connection) -> None:
    conn.execute(_LEARNING_RUNS_DDL)
