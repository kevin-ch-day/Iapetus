from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from iapetus.cli import app
from iapetus.snapshots.demo import build_curated_snapshot


def test_build_curated_snapshot_has_banker_package() -> None:
    snapshot = build_curated_snapshot()
    banker = next(
        entity for entity in snapshot.entities if entity.get("fixture_slug") == "malware_banker"
    )
    assert banker["package_name"] == "com.fake.update.security"
    assert "AndroidOS:Trojan.Anubis-t:[Banker]" in snapshot.labels


def test_snapshot_demo_curated_write(tmp_path: Path) -> None:
    output_dir = tmp_path / "curated_snapshot"
    result = CliRunner().invoke(
        app,
        [
            "snapshot",
            "demo",
            "--use-curated",
            "--write",
            "--output-dir",
            str(output_dir),
        ],
    )
    assert result.exit_code == 0
    assert (output_dir / "entity_features.json").is_file()
    assert (output_dir / "labeled_entities.json").is_file()
    entities = json.loads((output_dir / "entities.json").read_text(encoding="utf-8"))
    assert any(row.get("fixture_slug") == "malware_dropper" for row in entities)
