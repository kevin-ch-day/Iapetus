from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from iapetus.learning import LearningRunResult, generate_run_id
from iapetus.learning.deep.trainer import train_static_mlp, write_training_artifacts
from iapetus.learning.training_corpus import build_training_corpus
from iapetus.fixture_analysis import generated_summary_paths


def build_static_v1_result(
    run_id: str | None = None,
    created_at: str | None = None,
    *,
    backend: str | None = None,
) -> tuple[LearningRunResult, dict[str, Any], Any, Any, Any]:
    if run_id is None:
        run_id = generate_run_id()
    if created_at is None:
        created_at = datetime.now(UTC).isoformat()

    corpus = build_training_corpus()
    report, entity_model, malware_class_model, benign_class_model = train_static_mlp(
        backend=backend if backend in {"pure_python", "torch"} else None,  # type: ignore[arg-type]
    )

    malware_count = corpus["malware_example_count"]
    normal_count = corpus["normal_app_example_count"]
    summary_paths = generated_summary_paths()

    result = LearningRunResult(
        run_id=run_id,
        created_at=created_at,
        mode="static_v1",
        dataset_name="curated seed fixtures (static MLP v2)",
        entity_count=corpus["training_example_count"],
        malware_count=malware_count,
        normal_app_count=normal_count,
        unique_classifications=corpus["classifications"],
        model_name=f"static_mlp_v2/{report['backend']}",
        status=report["status"],
        notes=(
            f"Static dual-head MLP on {corpus['training_example_count']} examples. "
            f"Entity LOOCV={report['loocv']['accuracy']}, entity train={report['train_accuracy']}, "
            f"classification train={report['classification_train_accuracy']}."
        ),
        use_curated_fixtures=True,
        generated_summaries_available=bool(summary_paths),
        generated_summary_paths=summary_paths,
        training_example_count=corpus["training_example_count"],
        average_training_quality_score=corpus["average_training_quality_score"],
    )
    return result, report, entity_model, malware_class_model, benign_class_model


def write_static_v1_artifacts(
    result: LearningRunResult,
    report: dict[str, Any],
    run_dir: Path,
    *,
    entity_model: Any | None = None,
    malware_classification_model: Any | None = None,
    benign_classification_model: Any | None = None,
) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "learning_result.json").write_text(result.model_dump_json(indent=2), encoding="utf-8")
    (run_dir / "manifest.json").write_text(
        json.dumps(
            {
                "run_id": result.run_id,
                "created_at": result.created_at,
                "mode": result.mode,
                "dataset_name": result.dataset_name,
                "status": result.status,
                "model_name": result.model_name,
                "use_curated_fixtures": True,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    write_training_artifacts(
        report,
        run_dir,
        entity_model=entity_model,
        malware_classification_model=malware_classification_model,
        benign_classification_model=benign_classification_model,
    )
