from __future__ import annotations

from pathlib import Path

from iapetus.database.core import (
    KERNEL_SCHEMA_VERSION,
    KernelDatabase,
    apply_kernel_schema,
    init_kernel_database,
    kernel_connection,
    kernel_database_health,
    read_schema_version,
)
from iapetus.database.core.registry import iter_domain_schemas
from iapetus.database.repositories import LearningRunRepository
from iapetus.database.schemas.learning_runs import LEARNING_RUNS_TABLE


def test_core_bootstrap_creates_meta_and_domain_tables(tmp_path: Path) -> None:
    db_path = tmp_path / "kernel.db"
    init_kernel_database(db_path)
    health = kernel_database_health(db_path=db_path)
    assert health["exists"] is True
    assert health["stored_schema_version"] == KERNEL_SCHEMA_VERSION
    assert health["schema_current"] is True
    assert "schema_meta" in health["tables"]
    assert LEARNING_RUNS_TABLE in health["tables"]


def test_apply_kernel_schema_is_idempotent(tmp_path: Path) -> None:
    db_path = tmp_path / "kernel.db"
    with kernel_connection(db_path) as conn:
        apply_kernel_schema(conn)
    with kernel_connection(db_path) as conn:
        apply_kernel_schema(conn)
        assert read_schema_version(conn) == KERNEL_SCHEMA_VERSION


def test_domain_schemas_registered() -> None:
    names = {entry.name for entry in iter_domain_schemas()}
    assert "learning_runs" in names


def test_kernel_database_facade(tmp_path: Path) -> None:
    db = KernelDatabase(db_path=tmp_path / "k.db")
    path = db.initialize()
    assert path.is_file()
    health = db.health()
    assert health["exists"] is True


def test_learning_run_repository_class(tmp_path: Path) -> None:
    from iapetus.learning import build_smoke_result, write_learning_artifacts

    repo = LearningRunRepository(db_path=tmp_path / "repo.db")
    result, labels = build_smoke_result(run_id="run-repo-class")
    run_dir = tmp_path / "runs" / result.run_id
    write_learning_artifacts(result, labels, run_dir)
    assert repo.upsert_from_run_dir(run_dir) is True
    rows = repo.list_all()
    assert len(rows) == 1
    assert rows[0]["run_id"] == "run-repo-class"
