from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from iapetus.cli import app
from iapetus.contracts.learning import (
    LEARNING_ARTIFACT_MANIFEST_SCHEMA_NAME,
    LEARNING_ARTIFACT_MANIFEST_SCHEMA_VERSION,
    LEARNING_RUN_MANIFEST_SCHEMA_NAME,
    LEARNING_RUN_MANIFEST_SCHEMA_VERSION,
    LEARNING_RUN_RESULT_SCHEMA_NAME,
    LEARNING_RUN_RESULT_SCHEMA_VERSION,
)
from iapetus.learning import build_smoke_result, write_learning_artifacts
from iapetus.learning.learning_result_reader import read_learning_result_file
from iapetus.curated_seed_library_exports import build_feature_vocabulary, build_token_summary


def test_learn_run_smoke_write_creates_artifacts(tmp_path: Path) -> None:
    runner = CliRunner()
    output_dir = tmp_path / "learning_runs"
    result = runner.invoke(
        app,
        [
            "learn",
            "run",
            "--mode",
            "smoke",
            "--write",
            "--output-dir",
            str(output_dir),
        ],
    )
    assert result.exit_code == 0
    run_dirs = [path for path in output_dir.iterdir() if path.is_dir()]
    assert len(run_dirs) == 1

    payload = json.loads((run_dirs[0] / "learning_result.json").read_text(encoding="utf-8"))
    assert payload["schema_name"] == LEARNING_RUN_RESULT_SCHEMA_NAME
    assert payload["schema_version"] == LEARNING_RUN_RESULT_SCHEMA_VERSION
    assert payload["mode"] == "smoke"
    assert payload["dataset_name"] == "demo fixtures"
    assert payload["status"] == "PASS"
    assert payload["entity_count"] == 6
    assert (run_dirs[0] / "manifest.json").exists()
    assert (run_dirs[0] / "labels.json").exists()
    artifact_manifest = json.loads((run_dirs[0] / "artifact_manifest.json").read_text(encoding="utf-8"))
    assert artifact_manifest["schema_name"] == LEARNING_ARTIFACT_MANIFEST_SCHEMA_NAME
    assert artifact_manifest["schema_version"] == LEARNING_ARTIFACT_MANIFEST_SCHEMA_VERSION
    assert artifact_manifest["run_id"] == payload["run_id"]
    artifact_paths = {item["path"] for item in artifact_manifest["artifacts"]}
    assert "learning_result.json" in artifact_paths
    assert "manifest.json" in artifact_paths
    manifest = json.loads((run_dirs[0] / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["schema_name"] == LEARNING_RUN_MANIFEST_SCHEMA_NAME
    assert manifest["schema_version"] == LEARNING_RUN_MANIFEST_SCHEMA_VERSION


def test_learn_list_no_runs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("iapetus.cli.cli_console_and_path_helpers.LEARNING_RUNS_DIR", tmp_path / "empty_runs")
    result = CliRunner().invoke(app, ["learn", "list"])
    assert result.exit_code == 0
    assert "No learning runs found." in result.stdout


def test_learn_last_no_runs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("iapetus.cli.cli_console_and_path_helpers.LEARNING_RUNS_DIR", tmp_path / "empty_runs")
    result = CliRunner().invoke(app, ["learn", "last"])
    assert result.exit_code == 0
    assert "No learning runs found." in result.stdout


def test_learn_last_reads_latest_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    output_root = tmp_path / "learning_runs"
    output_root.mkdir()
    monkeypatch.setattr("iapetus.cli.cli_console_and_path_helpers.LEARNING_RUNS_DIR", output_root)

    older, older_labels = build_smoke_result(
        run_id="run-old",
        created_at="2026-01-01T00:00:00+00:00",
        dataset_name="demo fixtures",
    )
    newer, newer_labels = build_smoke_result(
        run_id="run-new",
        created_at="2026-01-02T00:00:00+00:00",
        dataset_name="demo fixtures",
    )
    write_learning_artifacts(older, older_labels, output_root / "run-old")
    write_learning_artifacts(newer, newer_labels, output_root / "run-new")

    result = CliRunner().invoke(app, ["learn", "last"])
    assert result.exit_code == 0
    assert f"Last learning run: {newer.run_id}" in result.stdout
    assert '"status":"PASS"' in result.stdout.replace(" ", "")
    assert f'"created_at":"{newer.created_at}"' in result.stdout.replace(" ", "")


def test_status_command_reports_mode_and_counts(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        "iapetus.cli.cli_console_and_path_helpers.collect_environment_info",
        lambda: type(
            "Info",
            (),
            {"system": "Windows", "release": "11", "python_version": "3.14.5"},
        )(),
    )
    monkeypatch.setattr("iapetus.cli.cli_console_and_path_helpers.collect_device_probe_state", lambda timeout_seconds=2.0: "adb_missing")
    monkeypatch.setattr("iapetus.cli.cli_console_and_path_helpers.LEARNING_RUNS_DIR", tmp_path / "learning_runs")
    monkeypatch.setattr("iapetus.cli.cli_console_and_path_helpers.DEMO_OUTPUT_DIR", tmp_path / "demo_snapshot")

    (tmp_path / "learning_runs").mkdir()
    (tmp_path / "demo_snapshot").mkdir()
    result = CliRunner().invoke(app, ["status"])
    assert result.exit_code == 0
    assert "IAPETUS STATUS" in result.stdout
    assert "Host OS        : Windows" in result.stdout
    assert "Host Version   : 11" in result.stdout
    assert "Python Version : 3.14.5" in result.stdout
    assert "Device         : adb_missing" in result.stdout
    assert "Snapshot count : 0" in result.stdout
    assert "Learning runs  : 0" in result.stdout
    assert "Mode           : seed" in result.stdout
    assert "Upstream       : not connected" in result.stdout


def test_dataset_shape_preview_contains_groups() -> None:
    result = CliRunner().invoke(app, ["dataset", "shape"])
    assert result.exit_code == 0
    assert "entity_features" in result.stdout
    assert "malware_banker" in result.stdout
    assert "has_sms_permission" in result.stdout
    assert "labeled_entities" in result.stdout
    assert "- permission observations" in result.stdout
    assert "- static features" in result.stdout
    assert "- dynamic windows" in result.stdout
    assert "- AV tokens" in result.stdout
    assert "- review decisions" in result.stdout
    assert "- training examples" in result.stdout


def test_learn_run_invalid_mode_fails_with_clear_message() -> None:
    result = CliRunner().invoke(
        app,
        [
            "learn",
            "run",
            "--mode",
            "full",
        ],
    )
    assert result.exit_code == 1
    assert "Learning mode 'full' is not available in seed kernel yet." in result.stdout


def test_learn_run_rejects_non_directory_output_path(tmp_path: Path) -> None:
    output_file = tmp_path / "not_a_directory"
    output_file.write_text("opaque", encoding="utf-8")
    result = CliRunner().invoke(
        app,
        [
            "learn",
            "run",
            "--mode",
            "smoke",
            "--write",
            "--output-dir",
            str(output_file),
        ],
    )
    assert result.exit_code == 1
    assert "Output path must be a directory:" in result.stdout


def test_build_token_summary_has_expected_counts() -> None:
    summary = build_token_summary()
    assert summary["permissions_by_category"]
    assert summary["permissions_by_rough_risk"]
    assert summary["static_tokens_by_token_type"]
    assert summary["fixture_samples_by_entity_kind"]
    assert summary["suspicious_indicator_counts"]


def test_token_summary_cli_loads_curated_files() -> None:
    result = CliRunner().invoke(app, ["data", "token-summary"])
    assert result.exit_code == 0
    assert "permissions by category" in result.stdout
    assert "network" in result.stdout
    assert "code_string" in result.stdout
    assert "fixture samples by entity_kind" in result.stdout
    assert "malware" in result.stdout
    assert "normal_app" in result.stdout


def test_build_feature_vocabulary_contains_seed_anchors() -> None:
    vocab = build_feature_vocabulary()
    assert "permissions" in vocab
    assert "static_tokens" in vocab
    permissions = vocab["permissions"]
    static_tokens = vocab["static_tokens"]
    assert "android.permission.READ_SMS" in permissions
    assert "DexClassLoader" in static_tokens


def test_learn_run_smoke_curated_write_creates_feature_artifacts(tmp_path: Path) -> None:
    runner = CliRunner()
    output_dir = tmp_path / "learning_runs"
    result = runner.invoke(
        app,
        [
            "learn",
            "run",
            "--mode",
            "smoke",
            "--use-curated",
            "--write",
            "--output-dir",
            str(output_dir),
        ],
    )
    assert result.exit_code == 0

    run_dirs = [path for path in output_dir.iterdir() if path.is_dir()]
    assert len(run_dirs) == 1
    run_dir = run_dirs[0]
    assert (run_dir / "feature_vocabulary.json").is_file()
    assert (run_dir / "token_summary.json").is_file()
    assert (run_dir / "entities.json").is_file()
    assert (run_dir / "labeled_entities.json").is_file()
    assert (run_dir / "entity_features.json").is_file()
    assert (run_dir / "entity_token_groups.json").is_file()
    assert (run_dir / "training_corpus.json").is_file()
    assert (run_dir / "training_features.json").is_file()
    artifact_manifest = json.loads((run_dir / "artifact_manifest.json").read_text(encoding="utf-8"))
    artifact_paths = {item["path"] for item in artifact_manifest["artifacts"]}
    assert "entity_features.json" in artifact_paths
    assert "feature_vocabulary.json" in artifact_paths

    corpus = json.loads((run_dir / "training_corpus.json").read_text(encoding="utf-8"))
    assert corpus["training_example_count"] == 12

    entities = json.loads((run_dir / "entities.json").read_text(encoding="utf-8"))
    banker = next(row for row in entities if row["fixture_slug"] == "malware_banker")
    assert banker["package_name"] == "com.fake.update.security"
    assert banker["entity_kind"] == "malware"

    features = json.loads((run_dir / "entity_features.json").read_text(encoding="utf-8"))
    banker_features = next(row for row in features if row["fixture_slug"] == "malware_banker")
    assert banker_features["has_sms_permission"] is True
    assert banker_features["has_boot_persistence"] is True
    assert banker_features["training_eligible"] is True

    result_payload = json.loads((run_dir / "learning_result.json").read_text(encoding="utf-8"))
    assert result_payload["use_curated_fixtures"] is True
    assert result_payload["training_example_count"] == 12
    assert result_payload["average_training_quality_score"] >= 80.0

    vocabulary = json.loads((run_dir / "feature_vocabulary.json").read_text(encoding="utf-8"))
    token_summary = json.loads((run_dir / "token_summary.json").read_text(encoding="utf-8"))
    assert "permissions" in vocabulary
    assert "suspicious_indicators" in vocabulary
    assert "fixture_samples_by_entity_kind" in token_summary


def test_legacy_learning_result_without_schema_fields_still_parses(tmp_path: Path) -> None:
    path = tmp_path / "learning_result.json"
    path.write_text(
        json.dumps(
            {
                "run_id": "run-legacy",
                "created_at": "2026-06-02T00:00:00+00:00",
                "mode": "static_v1",
                "dataset_name": "legacy curated fixtures",
                "entity_count": 12,
                "malware_count": 6,
                "normal_app_count": 6,
                "unique_classifications": ["Banker", "Messaging"],
                "model_name": "static_mlp_v2/pure_python",
                "status": "PASS",
                "notes": "legacy payload",
                "use_curated_fixtures": True,
                "generated_summaries_available": False,
                "generated_summary_paths": {},
                "training_example_count": 12,
                "average_training_quality_score": 88.5,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    result = read_learning_result_file(path)
    assert result.schema_name == LEARNING_RUN_RESULT_SCHEMA_NAME
    assert result.schema_version == LEARNING_RUN_RESULT_SCHEMA_VERSION
    assert result.mode == "static_mlp_v2"
