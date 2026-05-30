from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Iterable, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, ValidationError

from iapetus.labels.renderer import render_malware_label, render_normal_app_label
from iapetus.data_library import fixture_seed_as_labels
from iapetus.snapshots.demo import demo_fixtures


LearningMode = Literal["smoke"]


class LearningRunResult(BaseModel):
    run_id: str = Field(min_length=1)
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    mode: LearningMode
    dataset_name: str = Field(min_length=1)
    entity_count: int = Field(ge=0)
    malware_count: int = Field(ge=0)
    normal_app_count: int = Field(ge=0)
    unique_classifications: list[str]
    model_name: str = Field(min_length=1)
    status: Literal["PASS", "FAIL", "WARN"]
    notes: str


class LearningRunManifest(BaseModel):
    run_id: str = Field(min_length=1)
    created_at: str = Field(min_length=1)
    mode: LearningMode
    dataset_name: str = Field(min_length=1)
    status: Literal["PASS", "FAIL", "WARN"]
    model_name: str = Field(min_length=1)


def generate_run_id() -> str:
    return f"run-{datetime.now(UTC).strftime('%Y%m%dT%H%M%S')}-{uuid4().hex[:8]}"


def _unique_classifications_from_entities(
    malware_entities: list,
    normal_entities: list,
) -> list[str]:
    values = [item.subtype for item in malware_entities] + [item.app_category for item in normal_entities]
    unique: list[str] = []
    for value in values:
        if value not in unique:
            unique.append(value)
    return unique


def _load_smoke_entities(use_curated_fixtures: bool) -> tuple[list, list]:
    if not use_curated_fixtures:
        return demo_fixtures()

    try:
        return fixture_seed_as_labels()
    except (KeyError, ValueError, OSError) as exc:
        raise ValueError(f"Failed to load curated seed fixtures: {exc}") from exc


def build_smoke_result(
    run_id: str | None = None,
    created_at: str | None = None,
    dataset_name: str = "m1-demo-snapshot",
    use_curated_fixtures: bool = False,
) -> tuple[LearningRunResult, list[str]]:
    if run_id is None:
        run_id = generate_run_id()
    if created_at is None:
        created_at = datetime.now(UTC).isoformat()

    malware_entities, normal_entities = _load_smoke_entities(use_curated_fixtures=use_curated_fixtures)
    labels = [render_malware_label(item) for item in malware_entities] + [
        render_normal_app_label(item) for item in normal_entities
    ]

    entity_count = len(malware_entities) + len(normal_entities)
    return (
        LearningRunResult(
            run_id=run_id,
            created_at=created_at,
            mode="smoke",
            dataset_name=dataset_name,
            entity_count=entity_count,
            malware_count=len(malware_entities),
            normal_app_count=len(normal_entities),
            unique_classifications=_unique_classifications_from_entities(malware_entities, normal_entities),
            model_name="smoke_placeholder",
            status="PASS",
            notes="Seed smoke learning run (fixture-backed, no model training).",
        ),
        labels,
    )


def write_learning_artifacts(
    result: LearningRunResult,
    labels: Iterable[str],
    run_dir: Path,
) -> tuple[Path, Path, Path]:
    run_dir.mkdir(parents=True, exist_ok=True)

    manifest = LearningRunManifest(
        run_id=result.run_id,
        created_at=result.created_at,
        mode=result.mode,
        dataset_name=result.dataset_name,
        status=result.status,
        model_name=result.model_name,
    )

    learning_result_path = run_dir / "learning_result.json"
    manifest_path = run_dir / "manifest.json"
    labels_path = run_dir / "labels.json"

    learning_result_path.write_text(result.model_dump_json(indent=2), encoding="utf-8")
    manifest_path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
    labels_path.write_text(json.dumps(list(labels), indent=2), encoding="utf-8")
    return learning_result_path, manifest_path, labels_path


def read_learning_result_file(path: Path) -> LearningRunResult:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not read learning result: {path}") from exc

    try:
        return LearningRunResult.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(f"Invalid learning result payload in {path}: {exc}") from exc


def list_learning_runs(output_dir: Path) -> list[tuple[Path, LearningRunResult]]:
    if not output_dir.exists() or not output_dir.is_dir():
        return []

    runs: list[tuple[Path, LearningRunResult]] = []
    for run_dir in sorted(output_dir.iterdir()):
        if not run_dir.is_dir():
            continue
        result_file = run_dir / "learning_result.json"
        if not result_file.is_file():
            continue
        try:
            result = read_learning_result_file(result_file)
        except ValueError:
            continue
        runs.append((run_dir, result))

    runs.sort(key=lambda item: item[1].created_at, reverse=True)
    return runs


def read_latest_learning_result(output_dir: Path) -> tuple[LearningRunResult, Path] | None:
    runs = list_learning_runs(output_dir)
    if not runs:
        return None
    run_dir, result = runs[0]
    return result, run_dir
