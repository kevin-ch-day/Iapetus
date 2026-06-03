from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from typing import Literal

from iapetus.contracts.learning import (
    LEARNING_ARTIFACT_MANIFEST_SCHEMA_NAME,
    LEARNING_ARTIFACT_MANIFEST_SCHEMA_VERSION,
    LEARNING_RUN_MANIFEST_SCHEMA_NAME,
    LEARNING_RUN_MANIFEST_SCHEMA_VERSION,
    LEARNING_RUN_RESULT_SCHEMA_NAME,
    LEARNING_RUN_RESULT_SCHEMA_VERSION,
    STATIC_MLP_V2_MODE,
    normalize_learning_mode_alias,
)

LearningModeName = Literal["smoke", "static_mlp_v2"]

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

_ARTIFACT_METADATA: dict[str, dict[str, Any]] = {
    "learning_result.json": {
        "artifact_kind": "learning_run_result",
        "schema_name": LEARNING_RUN_RESULT_SCHEMA_NAME,
        "schema_version": LEARNING_RUN_RESULT_SCHEMA_VERSION,
        "required": True,
    },
    "manifest.json": {
        "artifact_kind": "learning_run_manifest",
        "schema_name": LEARNING_RUN_MANIFEST_SCHEMA_NAME,
        "schema_version": LEARNING_RUN_MANIFEST_SCHEMA_VERSION,
        "required": True,
    },
    "labels.json": {
        "artifact_kind": "label_render_list",
        "schema_name": None,
        "schema_version": None,
        "required": True,
    },
    "entities.json": {"artifact_kind": "curated_entities", "schema_name": None, "schema_version": None, "required": False},
    "labeled_entities.json": {"artifact_kind": "labeled_entities", "schema_name": None, "schema_version": None, "required": False},
    "entity_token_groups.json": {"artifact_kind": "entity_token_groups", "schema_name": None, "schema_version": None, "required": False},
    "entity_features.json": {"artifact_kind": "entity_features", "schema_name": None, "schema_version": None, "required": False},
    "training_corpus.json": {"artifact_kind": "training_corpus", "schema_name": None, "schema_version": None, "required": False},
    "training_features.json": {"artifact_kind": "training_features", "schema_name": None, "schema_version": None, "required": False},
    "feature_vocabulary.json": {"artifact_kind": "feature_vocabulary", "schema_name": None, "schema_version": None, "required": False},
    "token_summary.json": {"artifact_kind": "token_summary", "schema_name": None, "schema_version": None, "required": False},
    "training_quality_contract.json": {"artifact_kind": "training_quality_contract", "schema_name": None, "schema_version": None, "required": False},
    "bad_data_validation.json": {"artifact_kind": "bad_data_validation", "schema_name": None, "schema_version": None, "required": False},
    "training_metrics.json": {"artifact_kind": "training_metrics", "schema_name": None, "schema_version": None, "required": False},
    "predictions.json": {"artifact_kind": "predictions", "schema_name": None, "schema_version": None, "required": False},
    "feature_schema.json": {"artifact_kind": "feature_schema", "schema_name": None, "schema_version": None, "required": False},
    "normalization.json": {"artifact_kind": "normalization", "schema_name": None, "schema_version": None, "required": False},
    "classification_index.json": {"artifact_kind": "classification_index", "schema_name": None, "schema_version": None, "required": False},
    "feature_importance.json": {"artifact_kind": "feature_importance", "schema_name": None, "schema_version": None, "required": False},
    "model_weights.json": {"artifact_kind": "model_weights", "schema_name": None, "schema_version": None, "required": False},
    "malware_classification_weights.json": {"artifact_kind": "malware_classification_weights", "schema_name": None, "schema_version": None, "required": False},
    "benign_classification_weights.json": {"artifact_kind": "benign_classification_weights", "schema_name": None, "schema_version": None, "required": False},
    "model_torch.pt": {"artifact_kind": "model_weights_torch", "schema_name": None, "schema_version": None, "required": False},
    "classification_malware_torch.pt": {"artifact_kind": "malware_classification_weights_torch", "schema_name": None, "schema_version": None, "required": False},
    "classification_benign_torch.pt": {"artifact_kind": "benign_classification_weights_torch", "schema_name": None, "schema_version": None, "required": False},
}


def expected_artifacts_for_mode(
    mode: LearningModeName,
    *,
    use_curated: bool = False,
) -> tuple[str, ...]:
    normalized_mode = normalize_learning_mode_alias(mode)
    names: list[str] = list(BASE_RUN_ARTIFACTS)
    if use_curated or normalized_mode == STATIC_MLP_V2_MODE:
        names.extend(CURATED_RUN_ARTIFACTS)
        names.extend(CURATED_EXTRAS)
    if normalized_mode == STATIC_MLP_V2_MODE:
        names.extend(STATIC_MLP_ARTIFACTS)
    return tuple(dict.fromkeys(names))


def artifact_presence(run_dir: Path, artifact_names: tuple[str, ...]) -> list[tuple[str, bool]]:
    return [(name, (run_dir / name).is_file()) for name in artifact_names]


def write_artifact_manifest(run_dir: Path, *, run_id: str, producer: str = "iapetus") -> Path:
    """Write a manifest describing the artifacts currently present in a learning run directory."""
    artifacts: list[dict[str, Any]] = []
    for path in sorted(run_dir.iterdir()):
        if not path.is_file():
            continue
        if path.name == "artifact_manifest.json":
            continue
        meta = _ARTIFACT_METADATA.get(
            path.name,
            {
                "artifact_kind": "unknown",
                "schema_name": None,
                "schema_version": None,
                "required": False,
            },
        )
        artifacts.append(
            {
                "path": path.name,
                "artifact_kind": meta["artifact_kind"],
                "schema_name": meta["schema_name"],
                "schema_version": meta["schema_version"],
                "required": meta["required"],
            }
        )

    manifest = {
        "schema_name": LEARNING_ARTIFACT_MANIFEST_SCHEMA_NAME,
        "schema_version": LEARNING_ARTIFACT_MANIFEST_SCHEMA_VERSION,
        "generated_at": datetime.now(UTC).isoformat(),
        "producer": producer,
        "run_id": run_id,
        "artifacts": artifacts,
    }
    out_path = run_dir / "artifact_manifest.json"
    out_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return out_path
