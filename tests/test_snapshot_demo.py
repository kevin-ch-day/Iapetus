from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from iapetus.cli import app
from iapetus.labels.malware_label_text_renderer import render_malware_label, render_normal_app_label
from iapetus.snapshots.demo_snapshot_builder import build_demo_snapshot, demo_fixtures
import pytest


def test_demo_fixture_count() -> None:
    malware, normal = demo_fixtures()
    assert len(malware) == 3
    assert len(normal) == 3


def test_demo_malware_labels_render() -> None:
    malware, _ = demo_fixtures()
    values = [render_malware_label(item) for item in malware]
    assert values == [
        "AndroidOS:Trojan.Anubis-t:[Banker]",
        "AndroidOS:Trojan.SharkBot-a:[Banker]",
        "AndroidOS:Backdoor.SpyNote-x:[RAT]",
    ]


def test_demo_normal_labels_render() -> None:
    _, normal = demo_fixtures()
    values = [render_normal_app_label(item) for item in normal]
    assert values == [
        "AndroidOS:Facebook-64543615:[SocialMedia]",
        "AndroidOS:Signal-7000000:[Messaging]",
        "AndroidOS:TikTok-390000000:[ShortVideo]",
    ]


def test_demo_snapshot_manifest_entity_count() -> None:
    snapshot = build_demo_snapshot()
    assert snapshot.manifest.entity_count == 6
    assert snapshot.manifest.name == "m1-demo-snapshot"


def test_snapshot_demo_write_flag(tmp_path: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "snapshot",
            "demo",
            "--write",
            "--output-dir",
            str(tmp_path / "demo_snapshot"),
        ],
    )
    assert result.exit_code == 0
    assert (tmp_path / "demo_snapshot" / "manifest.json").exists()
    assert (tmp_path / "demo_snapshot" / "entities.json").exists()
    assert (tmp_path / "demo_snapshot" / "labels.json").exists()


def test_snapshot_demo_write_error_reports_exit(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        "iapetus.cli.typer_snapshot_subcommands.snapshot_output",
        lambda *args, **kwargs: (_ for _ in ()).throw(OSError("read-only filesystem")),
    )
    result = CliRunner().invoke(
        app,
        [
            "snapshot",
            "demo",
            "--write",
            "--output-dir",
            str(tmp_path / "demo_snapshot"),
        ],
    )
    assert result.exit_code == 1
    assert "Could not write snapshot files" in result.stdout


def test_snapshot_demo_rejects_non_directory_output_path(tmp_path: Path) -> None:
    output = tmp_path / "not_a_directory"
    output.write_text("opaque")
    result = CliRunner().invoke(
        app,
        [
            "snapshot",
            "demo",
            "--write",
            "--output-dir",
            str(output),
        ],
    )
    assert result.exit_code == 1
    assert "Output path is not a directory" in result.stdout


def test_snapshot_demo_rejects_empty_name() -> None:
    result = CliRunner().invoke(
        app,
        [
            "snapshot",
            "demo",
            "--write",
            "--name",
            "   ",
        ],
    )
    assert result.exit_code == 1
    assert "Snapshot name cannot be empty." in result.stdout
