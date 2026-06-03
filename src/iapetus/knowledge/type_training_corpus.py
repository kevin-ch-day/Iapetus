"""Build a first type-oriented training corpus from governed import contracts."""
from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from iapetus import project_filesystem_paths as paths
from iapetus.knowledge.import_contract_loaders import IMPORT_CONTRACT_SPECS, load_import_contract_file
from iapetus.knowledge.import_contract_models import (
    BenignAppArchetype,
    MalwareTypePattern,
    PermissionAuthorityFact,
    PermissionPatternExample,
)


def _load_records(model: type, file_name: str) -> list[Any]:
    return load_import_contract_file(paths.IMPORT_CONTRACTS_DIR / file_name, model)


def load_permission_authority_facts() -> list[PermissionAuthorityFact]:
    return _load_records(PermissionAuthorityFact, "permission_authority_facts.jsonl")


def load_malware_type_patterns() -> list[MalwareTypePattern]:
    return _load_records(MalwareTypePattern, "malware_type_patterns.jsonl")


def load_benign_app_archetypes() -> list[BenignAppArchetype]:
    return _load_records(BenignAppArchetype, "benign_app_archetypes.jsonl")


def load_permission_pattern_examples() -> list[PermissionPatternExample]:
    return _load_records(PermissionPatternExample, "permission_pattern_examples.jsonl")


def preview_training_seed_summary() -> dict[str, Any]:
    facts = load_permission_authority_facts()
    patterns = load_malware_type_patterns()
    archetypes = load_benign_app_archetypes()
    examples = load_permission_pattern_examples()
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "permission_fact_count": len(facts),
        "training_candidate_permission_facts": sum(1 for row in facts if row.training_eligibility == "training_candidate"),
        "malware_type_pattern_count": len(patterns),
        "trainable_malware_type_patterns": sum(1 for row in patterns if row.training_eligibility == "training_candidate"),
        "benign_archetype_count": len(archetypes),
        "trainable_benign_archetypes": sum(1 for row in archetypes if row.training_eligibility == "training_candidate"),
        "contrast_example_count": len(examples),
        "contrast_teaching_only_count": sum(1 for row in examples if row.training_eligibility == "teaching_only"),
        "contrast_explanation_only_count": sum(1 for row in examples if row.training_eligibility == "explanation_only"),
    }


def build_type_training_corpus() -> dict[str, Any]:
    permission_facts = {row.permission: row for row in load_permission_authority_facts()}
    malware_patterns = [
        row for row in load_malware_type_patterns() if row.training_eligibility in {"training_candidate", "training_approved"}
    ]
    benign_archetypes = [
        row for row in load_benign_app_archetypes() if row.training_eligibility in {"training_candidate", "training_approved"}
    ]
    contrast_examples = load_permission_pattern_examples()

    examples: list[dict[str, Any]] = []
    for row in malware_patterns:
        high_risk_permission_count = sum(
            1 for permission in row.permissions if permission_facts.get(permission) and permission_facts[permission].malware_commonality == "high"
        )
        examples.append(
            {
                "example_id": f"malware-type-{row.pattern_id}",
                "entity_kind": "malware",
                "target_label": row.malware_type,
                "permissions": row.permissions,
                "static_tokens": row.static_tokens,
                "concepts": row.concepts,
                "context_tokens": [],
                "feature_hints": {
                    "permission_count": len(row.permissions),
                    "static_token_count": len(row.static_tokens),
                    "high_malware_commonality_permission_count": high_risk_permission_count,
                },
                "governance": {
                    "source_kind": row.source_kind,
                    "training_eligibility": row.training_eligibility,
                    "synthetic_level": row.synthetic_level,
                    "review_status": row.review_status,
                },
                "explanation_note": row.confidence_note,
            }
        )

    for row in benign_archetypes:
        examples.append(
            {
                "example_id": f"benign-archetype-{row.archetype_id}",
                "entity_kind": "normal_app",
                "target_label": row.category,
                "permissions": row.expected_permissions,
                "static_tokens": [],
                "concepts": [],
                "context_tokens": row.expected_context,
                "feature_hints": {
                    "permission_count": len(row.expected_permissions),
                    "context_count": len(row.expected_context),
                    "contrast_note_count": len(row.contrast_notes),
                },
                "governance": {
                    "source_kind": row.source_kind,
                    "training_eligibility": row.training_eligibility,
                    "synthetic_level": row.synthetic_level,
                    "review_status": row.review_status,
                },
                "explanation_note": row.confidence_note,
            }
        )

    class_counts: dict[str, int] = {}
    for row in examples:
        class_counts[row["target_label"]] = class_counts.get(row["target_label"], 0) + 1

    synthetic_levels = [row["governance"]["synthetic_level"] for row in examples]
    synthetic_heavy = bool(synthetic_levels) and sum(1 for value in synthetic_levels if value in {"medium", "high"}) / len(synthetic_levels) >= 0.5
    warnings: list[str] = []
    if len(examples) < 12:
        warnings.append("Type corpus is still very small; do not overread model metrics.")
    if synthetic_heavy:
        warnings.append("Type corpus is synthetic-heavy; treat as teaching/training seed only.")
    if any(count < 2 for count in class_counts.values()):
        warnings.append("Several labels have only one example; class generalization will be weak.")

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "corpus_name": "iapetus_type_training_seed",
        "schema_name": "iapetus.knowledge.type_training_corpus",
        "schema_version": "v1",
        "purpose": "Type-oriented Android security teaching and training seed derived from governed import contracts.",
        "example_count": len(examples),
        "class_counts": class_counts,
        "authority_fact_count": len(permission_facts),
        "contrast_example_count": len(contrast_examples),
        "warnings": warnings,
        "examples": examples,
    }


def write_type_training_corpus(output_path: Path | None = None) -> Path:
    path = output_path or (paths.GENERATED_DIR / "type_training_corpus.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(build_type_training_corpus(), indent=2), encoding="utf-8")
    return path
