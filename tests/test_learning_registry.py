from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from iapetus.cli import app
from iapetus.learning import build_smoke_result, write_learning_artifacts
from iapetus.learning.static_mlp_training_pipeline import build_static_v1_result, write_static_v1_artifacts
from iapetus.storage.sqlite_learning_run_registry import (
    index_learning_runs,
    list_indexed_runs,
    register_learning_run,
    registry_status,
)


def test_register_smoke_run(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    result, labels = build_smoke_result(run_id="run-smoke-test")
    run_dir = tmp_path / "runs" / result.run_id
    write_learning_artifacts(result, labels, run_dir)
    assert register_learning_run(run_dir, db_path=db_path) is True
    rows = list_indexed_runs(db_path=db_path)
    assert len(rows) == 1
    assert rows[0]["run_id"] == "run-smoke-test"
    assert rows[0]["mode"] == "smoke"


def test_index_static_v1_run_with_metrics(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    result, report, entity_model, malware_model, benign_model = build_static_v1_result(
        backend="pure_python"
    )
    run_dir = tmp_path / "runs" / result.run_id
    write_static_v1_artifacts(
        result,
        report,
        run_dir,
        entity_model=entity_model,
        malware_classification_model=malware_model,
        benign_classification_model=benign_model,
    )
    summary = index_learning_runs(tmp_path / "runs", db_path=db_path)
    assert summary["indexed_count"] == 1
    row = list_indexed_runs(db_path=db_path)[0]
    assert row["entity_loocv"] is not None
    assert row["classification_train_accuracy"] >= 0.75
    assert row["malware_subgroup_train"] >= 0.75


def test_db_status_cli(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "iapetus.db"
    monkeypatch.setattr(
        "iapetus.storage.sqlite_learning_run_registry.default_registry_db_path",
        lambda: db_path,
    )
    result, labels = build_smoke_result(run_id="run-db-cli")
    write_learning_artifacts(result, labels, tmp_path / "run-db-cli")
    register_learning_run(tmp_path / "run-db-cli", db_path=db_path)
    out = CliRunner().invoke(app, ["db", "status"])
    assert out.exit_code == 0
    assert "run-db-cli" in out.stdout


def test_learn_index_cli(tmp_path: Path, monkeypatch) -> None:
    runs_dir = tmp_path / "learning_runs"
    monkeypatch.setattr("iapetus.cli.cli_console_and_path_helpers.LEARNING_RUNS_DIR", runs_dir)
    result, labels = build_smoke_result(run_id="run-index-cli")
    write_learning_artifacts(result, labels, runs_dir / result.run_id)
    out = CliRunner().invoke(app, ["learn", "index", "--output-dir", str(runs_dir)])
    assert out.exit_code == 0
    assert "Indexed" in out.stdout


def test_bad_data_gaps_write(tmp_path: Path, monkeypatch) -> None:
    generated = tmp_path / "generated"
    monkeypatch.setattr("iapetus.cli.cli_console_and_path_helpers.GENERATED_DIR", generated)
    out = CliRunner().invoke(app, ["bad-data", "gaps", "--write"])
    assert (generated / "gap_report.json").is_file()
    payload = json.loads((generated / "gap_report.json").read_text(encoding="utf-8"))
    assert "open_holes" in payload
