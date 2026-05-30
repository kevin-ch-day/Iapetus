from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from iapetus.cli import app
from iapetus.learning import build_smoke_result, write_learning_artifacts


def _patch_default_db(monkeypatch, db_path: Path) -> None:
    monkeypatch.setattr(
        "iapetus.database.core.connection.default_kernel_db_path",
        lambda: db_path,
    )
    monkeypatch.setattr(
        "iapetus.database.core.connection.default_learning_index_db_path",
        lambda: db_path,
    )


def test_db_inspect_cli(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "inspect.db"
    _patch_default_db(monkeypatch, db_path)
    result, labels = build_smoke_result(run_id="run-inspect")
    run_dir = tmp_path / "run-inspect"
    write_learning_artifacts(result, labels, run_dir)
    from iapetus.database import register_learning_run

    register_learning_run(run_dir, db_path=db_path)
    out = CliRunner().invoke(app, ["db", "inspect"])
    assert out.exit_code == 0
    assert "learning_runs" in out.stdout
    assert "Integrity" in out.stdout


def test_db_init_cli(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "init.db"
    _patch_default_db(monkeypatch, db_path)
    out = CliRunner().invoke(app, ["db", "init"])
    assert out.exit_code == 0
    assert db_path.is_file()
    assert "Kernel database ready" in out.stdout
