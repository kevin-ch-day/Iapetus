"""Smoke learning run build, artifact write, and directory listing."""
from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable

from iapetus.data.curated_seed_loaders import fixture_seed_as_labels
from iapetus.curated_fixture_analysis import generated_summaries_available, generated_summary_paths
from iapetus.labels.malware_label_text_renderer import render_malware_label, render_normal_app_label
from iapetus.learning.learning_run_models import LearningRunManifest, LearningRunResult, generate_run_id
from iapetus.learning.quality_gated_training_corpus import build_training_corpus
from iapetus.snapshots.demo_snapshot_builder import demo_fixtures


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
    summary_paths = generated_summary_paths() if use_curated_fixtures else {}
    training_stats = {"training_example_count": 0, "average_training_quality_score": 0.0}
    if use_curated_fixtures:
        corpus = build_training_corpus()
        training_stats = {
            "training_example_count": corpus["training_example_count"],
            "average_training_quality_score": corpus["average_training_quality_score"],
        }
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
            use_curated_fixtures=use_curated_fixtures,
            generated_summaries_available=bool(summary_paths),
            generated_summary_paths=summary_paths,
            training_example_count=training_stats["training_example_count"],
            average_training_quality_score=training_stats["average_training_quality_score"],
        ),
        labels,
    )


def write_learning_artifacts(
    result: LearningRunResult,
    labels: Iterable[str],
    run_dir: Path,
    *,
    write_curated_entities: bool = False,
) -> tuple[Path, Path, Path]:
    run_dir.mkdir(parents=True, exist_ok=True)

    manifest = LearningRunManifest(
        run_id=result.run_id,
        created_at=result.created_at,
        mode=result.mode,
        dataset_name=result.dataset_name,
        status=result.status,
        model_name=result.model_name,
        use_curated_fixtures=result.use_curated_fixtures,
        generated_summaries_available=result.generated_summaries_available,
        generated_summary_paths=result.generated_summary_paths,
    )

    learning_result_path = run_dir / "learning_result.json"
    manifest_path = run_dir / "manifest.json"
    labels_path = run_dir / "labels.json"

    learning_result_path.write_text(result.model_dump_json(indent=2), encoding="utf-8")
    manifest_path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
    labels_path.write_text(json.dumps(list(labels), indent=2), encoding="utf-8")

    if write_curated_entities:
        from iapetus.learning.curated_learning_artifacts import write_curated_learning_run_artifacts

        write_curated_learning_run_artifacts(run_dir, kind="smoke")

    from iapetus.database import register_learning_run  # noqa: PLC0415

    register_learning_run(run_dir)

    return learning_result_path, manifest_path, labels_path


def list_learning_runs(output_dir: Path) -> list[tuple[Path, LearningRunResult]]:
    from iapetus.learning.learning_result_reader import read_learning_result_file

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
