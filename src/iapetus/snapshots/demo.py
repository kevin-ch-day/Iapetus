from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import cast

from pydantic import BaseModel

from iapetus.labels import (
    MalwareLabel,
    NormalAppLabel,
)
from iapetus.labels.renderer import render_malware_label, render_normal_app_label

from .manifest import SnapshotManifest


DEMO_OUTPUT_DIR = Path("output/demo_snapshot")


class DemoSnapshot(BaseModel):
    manifest: SnapshotManifest
    entities: list[dict]
    labels: list[str]


def demo_fixtures() -> tuple[list[MalwareLabel], list[NormalAppLabel]]:
    malware_entities = [
        MalwareLabel(
            platform="AndroidOS",
            malware_primary="Trojan",
            family="Anubis",
            variant="t",
            subtype="Banker",
        ),
        MalwareLabel(
            platform="AndroidOS",
            malware_primary="Trojan",
            family="SharkBot",
            variant="a",
            subtype="Banker",
        ),
        MalwareLabel(
            platform="AndroidOS",
            malware_primary="Backdoor",
            family="SpyNote",
            variant="x",
            subtype="RAT",
        ),
    ]
    normal_entities = [
        NormalAppLabel(
            platform="AndroidOS",
            app_name="Facebook",
            build_ref="64543615",
            app_category="SocialMedia",
        ),
        NormalAppLabel(
            platform="AndroidOS",
            app_name="Signal",
            build_ref="7000000",
            app_category="Messaging",
        ),
        NormalAppLabel(
            platform="AndroidOS",
            app_name="TikTok",
            build_ref="390000000",
            app_category="ShortVideo",
        ),
    ]
    return malware_entities, normal_entities


def _labels_from_entities(
    malware_entities: list[MalwareLabel],
    normal_entities: list[NormalAppLabel],
) -> list[str]:
    labels = [render_malware_label(item) for item in malware_entities]
    labels += [render_normal_app_label(item) for item in normal_entities]
    return labels


def build_demo_snapshot(
    name: str = "m1-demo-snapshot",
    purpose: str = "M1 demo snapshot containing seed entities and rendered labels.",
) -> DemoSnapshot:
    malware_entities, normal_entities = demo_fixtures()
    all_entities = [*malware_entities, *normal_entities]
    entity_data = [asdict(item) for item in all_entities]
    labels = _labels_from_entities(malware_entities, normal_entities)
    manifest = SnapshotManifest(
        name=name,
        entity_count=len(all_entities),
        purpose=purpose,
    )
    return DemoSnapshot(
        manifest=manifest,
        entities=cast(list[dict], entity_data),
        labels=labels,
    )


def snapshot_output(payload: DemoSnapshot, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "manifest.json").write_text(payload.manifest.model_dump_json(indent=2), encoding="utf-8")
    (output_dir / "entities.json").write_text(
        json.dumps(payload.entities, indent=2),
        encoding="utf-8",
    )
    (output_dir / "labels.json").write_text(
        json.dumps(payload.labels, indent=2),
        encoding="utf-8",
    )
