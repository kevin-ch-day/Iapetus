"""Write curated-fixture JSON bundles into learning run or snapshot directories."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from iapetus.data.aggregated_feature_vocabulary import build_feature_vocabulary, build_token_summary
from iapetus.curated_fixture_analysis import build_curated_entity_artifacts
from iapetus.learning.quality_gated_training_corpus import build_training_corpus
from iapetus.validation.fixture_quality_report import build_training_quality_contract

CuratedRunKind = Literal["smoke", "static_mlp"]


def _labeled_entity_rows(entities: list[dict]) -> list[dict]:
    return [
        {
            "sample_id": row["sample_id"],
            "fixture_slug": row["fixture_slug"],
            "entity_kind": row["entity_kind"],
            "package_name": row["package_name"],
            "display_name": row.get("display_name", ""),
            "rendered_label": row["rendered_label"],
            "expected_classification": row["expected_classification"],
        }
        for row in entities
    ]


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_curated_learning_run_artifacts(run_dir: Path, *, kind: CuratedRunKind) -> None:
    """Persist curated entity/corpus files for a learning run directory."""
    run_dir.mkdir(parents=True, exist_ok=True)
    entities, token_groups, features = build_curated_entity_artifacts()
    corpus = build_training_corpus()

    _write_json(run_dir / "entities.json", entities)
    _write_json(run_dir / "entity_token_groups.json", token_groups)
    _write_json(run_dir / "entity_features.json", features)
    _write_json(run_dir / "training_corpus.json", corpus)

    if kind == "smoke":
        _write_json(run_dir / "labeled_entities.json", _labeled_entity_rows(entities))
        eligible_only = [row for row in features if row.get("training_eligible")]
        _write_json(run_dir / "training_features.json", eligible_only)
        return

    _write_json(run_dir / "feature_vocabulary.json", build_feature_vocabulary())
    _write_json(run_dir / "token_summary.json", build_token_summary())
    _write_json(run_dir / "training_quality_contract.json", build_training_quality_contract())


def write_curated_smoke_supplements(run_dir: Path) -> None:
    """Vocabulary/summary/contract files for curated smoke runs (non-adversarial path)."""
    run_dir.mkdir(parents=True, exist_ok=True)
    _write_json(run_dir / "feature_vocabulary.json", build_feature_vocabulary())
    _write_json(run_dir / "token_summary.json", build_token_summary())
    _write_json(run_dir / "training_quality_contract.json", build_training_quality_contract())


def write_curated_snapshot_supplement(output_dir: Path) -> None:
    """Extra curated files for ``snapshot demo --use-curated --write``."""
    output_dir.mkdir(parents=True, exist_ok=True)
    entities, token_groups, features = build_curated_entity_artifacts()
    _write_json(output_dir / "labeled_entities.json", _labeled_entity_rows(entities))
    _write_json(output_dir / "entity_token_groups.json", token_groups)
    _write_json(output_dir / "entity_features.json", features)
