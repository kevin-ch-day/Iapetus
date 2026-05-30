from __future__ import annotations

from pathlib import Path

from iapetus.database import (
    SCHEMA_VERSION,
    connect_learning_index,
    init_learning_index_database,
    learning_index_status,
    read_schema_version,
    register_learning_run,
)
from iapetus.learning import build_smoke_result, write_learning_artifacts


def test_init_learning_index_database_creates_schema(tmp_path: Path) -> None:
    db_path = tmp_path / "kernel.db"
    init_learning_index_database(db_path)
    conn = connect_learning_index(db_path)
    try:
        assert read_schema_version(conn) == SCHEMA_VERSION
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
    finally:
        conn.close()
    assert "learning_runs" in tables
    assert "schema_meta" in tables


def test_learning_index_status_missing_db(tmp_path: Path) -> None:
    status = learning_index_status(db_path=tmp_path / "missing.db")
    assert status["exists"] is False
    assert status["run_count"] == 0


def test_register_run_via_database_module(tmp_path: Path) -> None:
    db_path = tmp_path / "index.db"
    result, labels = build_smoke_result(run_id="run-db-module")
    run_dir = tmp_path / "runs" / result.run_id
    write_learning_artifacts(result, labels, run_dir)
    assert register_learning_run(run_dir, db_path=db_path) is True
    status = learning_index_status(db_path=db_path)
    assert status["exists"] is True
    assert status["run_count"] == 1
    assert status["latest_run_id"] == "run-db-module"
