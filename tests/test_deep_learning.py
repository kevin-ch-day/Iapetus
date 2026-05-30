from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from iapetus.cli import app
from iapetus.learning.deep.features import STATIC_FEATURE_NAMES, prepare_training_batch
from iapetus.learning.deep.inference import evaluate_saved_run, load_model_bundle, predict_fixture
from iapetus.learning.deep.trainer import train_static_mlp
from iapetus.learning.static_v1 import build_static_v1_result, write_static_v1_artifacts
from iapetus.learning.training_corpus import build_training_corpus


def test_feature_matrix_shape_matches_schema() -> None:
    examples = build_training_corpus()["training_examples"]
    matrix, _, _, _, _, _ = prepare_training_batch(examples)
    assert len(matrix) == 12
    assert len(matrix[0]) == len(STATIC_FEATURE_NAMES)


def test_static_mlp_trains_with_high_loocv_accuracy() -> None:
    report, _, malware_model, benign_model = train_static_mlp(backend="pure_python")
    assert report["training_example_count"] == 12
    assert report["loocv"]["accuracy"] >= 0.75
    assert report["classification_train_accuracy"] >= 0.75
    assert all(row["entity_kind_correct"] for row in report["predictions"])
    assert all(row["classification_correct"] for row in report["predictions"])
    assert malware_model is not None
    assert benign_model is not None


def test_build_static_v1_result_passes() -> None:
    result, report, entity_model, malware_model, benign_model = build_static_v1_result(
        backend="pure_python"
    )
    assert result.mode == "static_v1"
    assert result.status in {"PASS", "WARN"}
    assert report["train_accuracy"] >= 0.75
    assert report["classification_train_accuracy"] >= 0.75
    assert entity_model is not None
    assert malware_model is not None
    assert benign_model is not None


def test_write_static_v1_artifacts(tmp_path: Path) -> None:
    result, report, entity_model, malware_model, benign_model = build_static_v1_result(
        backend="pure_python"
    )
    run_dir = tmp_path / result.run_id
    write_static_v1_artifacts(
        result,
        report,
        run_dir,
        entity_model=entity_model,
        malware_classification_model=malware_model,
        benign_classification_model=benign_model,
    )
    assert (run_dir / "training_metrics.json").is_file()
    assert (run_dir / "normalization.json").is_file()
    assert (run_dir / "malware_classification_weights.json").is_file()
    assert (run_dir / "benign_classification_weights.json").is_file()
    metrics = json.loads((run_dir / "training_metrics.json").read_text(encoding="utf-8"))
    assert metrics["loocv"]["accuracy"] >= 0.75
    assert metrics["classification_train_accuracy"] >= 0.75


def test_predict_fixture_after_train(tmp_path: Path) -> None:
    result, report, entity_model, malware_model, benign_model = build_static_v1_result(
        backend="pure_python"
    )
    run_dir = tmp_path / result.run_id
    write_static_v1_artifacts(
        result,
        report,
        run_dir,
        entity_model=entity_model,
        malware_classification_model=malware_model,
        benign_classification_model=benign_model,
    )
    bundle = load_model_bundle(tmp_path, run_id=result.run_id)
    detail = predict_fixture(bundle, "malware_banker")
    assert detail["predicted_entity_kind"] == "malware"
    assert detail["predicted_classification"] == "Banker"
    assert detail["entity_kind_correct"] is True
    assert detail["classification_correct"] is True


def test_evaluate_saved_run(tmp_path: Path) -> None:
    result, report, entity_model, malware_model, benign_model = build_static_v1_result(
        backend="pure_python"
    )
    run_dir = tmp_path / result.run_id
    write_static_v1_artifacts(
        result,
        report,
        run_dir,
        entity_model=entity_model,
        malware_classification_model=malware_model,
        benign_classification_model=benign_model,
    )
    bundle = load_model_bundle(tmp_path, run_id=result.run_id)
    evaluation = evaluate_saved_run(bundle)
    assert evaluation["entity_kind_accuracy"] >= 0.75
    assert evaluation["classification_accuracy"] >= 0.75


def test_learn_train_cli(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("iapetus.cli.LEARNING_RUNS_DIR", tmp_path / "runs")
    result = CliRunner().invoke(app, ["learn", "train", "--backend", "pure_python"])
    assert result.exit_code == 0
    assert "LOOCV" in result.stdout
    assert "malware_banker" in result.stdout


def test_learn_predict_cli(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("iapetus.cli.LEARNING_RUNS_DIR", tmp_path / "runs")
    runner = CliRunner()
    train = runner.invoke(app, ["learn", "train", "--backend", "pure_python", "--output-dir", str(tmp_path / "runs")])
    assert train.exit_code == 0
    predict = runner.invoke(
        app,
        ["learn", "predict", "--fixture", "malware_banker", "--output-dir", str(tmp_path / "runs")],
    )
    assert predict.exit_code == 0
    assert "malware" in predict.stdout


def test_learn_run_static_v1_mode(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("iapetus.cli.LEARNING_RUNS_DIR", tmp_path / "runs")
    result = CliRunner().invoke(
        app,
        [
            "learn",
            "run",
            "--mode",
            "static-v1",
            "--use-curated",
            "--write",
            "--backend",
            "pure_python",
            "--output-dir",
            str(tmp_path / "runs"),
        ],
    )
    assert result.exit_code == 0
    run_dirs = list((tmp_path / "runs").iterdir())
    assert len(run_dirs) == 1
    assert (run_dirs[0] / "normalization.json").is_file()
    assert (run_dirs[0] / "malware_classification_weights.json").is_file()
