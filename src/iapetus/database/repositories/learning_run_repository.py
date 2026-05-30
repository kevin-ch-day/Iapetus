"""Repository for the ``learning_runs`` index table."""
from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from iapetus.database.core.constants import KERNEL_SCHEMA_VERSION
from iapetus.database.models.learning_run_index_row import LearningRunIndexRow
from iapetus.database.repositories.base import KernelRepository
from iapetus.database.schemas.learning_runs import LEARNING_RUNS_TABLE

SCHEMA_VERSION = KERNEL_SCHEMA_VERSION


def _read_optional_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def extract_run_index_row(run_dir: Path) -> LearningRunIndexRow | None:
    from iapetus.learning.learning_result_reader import read_learning_result_file

    try:
        result = read_learning_result_file(run_dir / "learning_result.json")
    except ValueError:
        return None

    metrics = _read_optional_json(run_dir / "training_metrics.json") or {}
    config = _read_optional_json(run_dir / "model_config.json") or {}
    loocv = metrics.get("loocv") if isinstance(metrics.get("loocv"), dict) else {}
    subgroup_train = metrics.get("classification_subgroup_train_accuracy") or {}

    return LearningRunIndexRow(
        run_id=result.run_id,
        created_at=result.created_at,
        mode=result.mode,
        status=result.status,
        model_name=result.model_name,
        dataset_name=result.dataset_name,
        entity_count=result.entity_count,
        run_dir=str(run_dir.resolve()),
        backend=config.get("backend"),
        entity_loocv=loocv.get("accuracy"),
        classification_train_accuracy=metrics.get("classification_train_accuracy"),
        malware_subgroup_train=subgroup_train.get("malware"),
        benign_subgroup_train=subgroup_train.get("benign"),
    )


class LearningRunRepository(KernelRepository):
    """CRUD and filesystem indexing for local learning runs."""

    def upsert_from_run_dir(self, run_dir: Path) -> bool:
        row = extract_run_index_row(run_dir)
        if row is None:
            return False
        path = self.ensure_database()
        indexed_at = datetime.now(UTC).isoformat()
        with self.connection() as conn:
            conn.execute(
                f"""
                INSERT INTO {LEARNING_RUNS_TABLE} (
                    run_id, created_at, mode, status, model_name, dataset_name,
                    entity_count, run_dir, backend, entity_loocv,
                    classification_train_accuracy, malware_subgroup_train,
                    benign_subgroup_train, indexed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(run_id) DO UPDATE SET
                    created_at=excluded.created_at,
                    mode=excluded.mode,
                    status=excluded.status,
                    model_name=excluded.model_name,
                    dataset_name=excluded.dataset_name,
                    entity_count=excluded.entity_count,
                    run_dir=excluded.run_dir,
                    backend=excluded.backend,
                    entity_loocv=excluded.entity_loocv,
                    classification_train_accuracy=excluded.classification_train_accuracy,
                    malware_subgroup_train=excluded.malware_subgroup_train,
                    benign_subgroup_train=excluded.benign_subgroup_train,
                    indexed_at=excluded.indexed_at
                """,
                (
                    row["run_id"],
                    row["created_at"],
                    row["mode"],
                    row["status"],
                    row["model_name"],
                    row["dataset_name"],
                    row["entity_count"],
                    row["run_dir"],
                    row["backend"],
                    row["entity_loocv"],
                    row["classification_train_accuracy"],
                    row["malware_subgroup_train"],
                    row["benign_subgroup_train"],
                    indexed_at,
                ),
            )
        return True

    def list_all(self) -> list[dict[str, Any]]:
        if not self.db_path.is_file():
            return []
        self.ensure_database()
        with self.connection() as conn:
            rows = conn.execute(
                f"""
                SELECT * FROM {LEARNING_RUNS_TABLE}
                ORDER BY created_at DESC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def get_by_run_id(self, run_id: str) -> dict[str, Any] | None:
        for row in self.list_all():
            if row["run_id"] == run_id:
                return row
        return None

    def index_runs_directory(self, runs_dir: Path) -> dict[str, Any]:
        path = self.ensure_database()
        indexed: list[str] = []
        skipped: list[str] = []
        if runs_dir.exists() and runs_dir.is_dir():
            for child in sorted(runs_dir.iterdir()):
                if not child.is_dir():
                    continue
                if self.upsert_from_run_dir(child):
                    row = extract_run_index_row(child)
                    if row:
                        indexed.append(row["run_id"])
                else:
                    skipped.append(child.name)

        return {
            "db_path": str(path),
            "runs_dir": str(runs_dir.resolve()),
            "indexed_run_ids": indexed,
            "skipped_dirs": skipped,
            "indexed_count": len(indexed),
        }

    def status(self) -> dict[str, Any]:
        from iapetus.database.core.health import kernel_database_health

        health = kernel_database_health(db_path=self.db_path)
        return {
            "db_path": health["db_path"],
            "exists": health["exists"],
            "run_count": health["learning_run_count"],
            "latest_run_id": health["latest_learning_run_id"],
            "latest_mode": health["latest_learning_run_mode"],
            "schema_version": health.get("stored_schema_version") or SCHEMA_VERSION,
            "schema_current": health["schema_current"],
            "integrity_ok": health["integrity_ok"],
            "tables": health["tables"],
            "table_row_counts": health["table_row_counts"],
        }


_default_repository = LearningRunRepository()


def default_learning_run_repository() -> LearningRunRepository:
    return _default_repository


def register_learning_run(run_dir: Path, *, db_path: Path | None = None) -> bool:
    return LearningRunRepository(db_path=db_path).upsert_from_run_dir(run_dir)


def index_learning_runs(runs_dir: Path, *, db_path: Path | None = None) -> dict[str, Any]:
    return LearningRunRepository(db_path=db_path).index_runs_directory(runs_dir)


def list_indexed_runs(*, db_path: Path | None = None) -> list[dict[str, Any]]:
    return LearningRunRepository(db_path=db_path).list_all()


def learning_index_status(*, db_path: Path | None = None) -> dict[str, Any]:
    return LearningRunRepository(db_path=db_path).status()


def metrics_for_run_id(run_id: str, *, db_path: Path | None = None) -> dict[str, Any] | None:
    return LearningRunRepository(db_path=db_path).get_by_run_id(run_id)
