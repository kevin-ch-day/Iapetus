from __future__ import annotations

from pathlib import Path
from typing import Literal

LearningModeName = Literal["smoke", "static_v1"]

BASE_RUN_ARTIFACTS: tuple[str, ...] = (
    "learning_result.json",
    "manifest.json",
    "labels.json",
)

CURATED_RUN_ARTIFACTS: tuple[str, ...] = (
    "entities.json",
    "labeled_entities.json",
    "entity_token_groups.json",
    "entity_features.json",
    "training_corpus.json",
    "training_features.json",
)

STATIC_MLP_ARTIFACTS: tuple[str, ...] = (
    "training_metrics.json",
    "predictions.json",
    "feature_schema.json",
    "normalization.json",
    "classification_index.json",
    "feature_importance.json",
    "model_weights.json",
    "malware_classification_weights.json",
    "benign_classification_weights.json",
    "model_torch.pt",
    "classification_malware_torch.pt",
    "classification_benign_torch.pt",
)

CURATED_EXTRAS: tuple[str, ...] = (
    "feature_vocabulary.json",
    "token_summary.json",
    "training_quality_contract.json",
)


def expected_artifacts_for_mode(
    mode: LearningModeName,
    *,
    use_curated: bool = False,
) -> tuple[str, ...]:
    names: list[str] = list(BASE_RUN_ARTIFACTS)
    if use_curated or mode == "static_v1":
        names.extend(CURATED_RUN_ARTIFACTS)
        names.extend(CURATED_EXTRAS)
    if mode == "static_v1":
        names.extend(STATIC_MLP_ARTIFACTS)
    return tuple(dict.fromkeys(names))


def artifact_presence(run_dir: Path, artifact_names: tuple[str, ...]) -> list[tuple[str, bool]]:
    return [(name, (run_dir / name).is_file()) for name in artifact_names]
