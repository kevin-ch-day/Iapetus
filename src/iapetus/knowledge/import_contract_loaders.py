"""JSONL loaders and validators for Android security import contracts."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from iapetus import project_filesystem_paths as paths
from iapetus.knowledge.import_contract_models import (
    AndroidConceptLesson,
    AttackMobileSeedMapping,
    BenignAppArchetype,
    GovernedImportContractRecord,
    MalwareTypePattern,
    PermissionAuthorityFact,
    PermissionPatternExample,
)


@dataclass(frozen=True)
class ImportContractSpec:
    file_name: str
    record_type: str
    model: type[GovernedImportContractRecord]


@dataclass(frozen=True)
class ImportContractValidationIssue:
    file_name: str
    row_number: int
    message: str


@dataclass(frozen=True)
class ImportContractValidationSummary:
    file_name: str
    row_count: int
    valid_count: int
    invalid_count: int
    record_types_found: list[str]
    training_eligible_count: int
    training_candidate_count: int
    training_approved_count: int
    teaching_only_count: int
    explanation_only_count: int
    validation_only_count: int
    synthetic_heavy: bool
    issues: list[ImportContractValidationIssue]


IMPORT_CONTRACT_SPECS: tuple[ImportContractSpec, ...] = (
    ImportContractSpec("permission_authority_facts.jsonl", "permission_authority_fact", PermissionAuthorityFact),
    ImportContractSpec("android_concept_lessons.jsonl", "android_concept_lesson", AndroidConceptLesson),
    ImportContractSpec("malware_type_patterns.jsonl", "malware_type_pattern", MalwareTypePattern),
    ImportContractSpec("benign_app_archetypes.jsonl", "benign_app_archetype", BenignAppArchetype),
    ImportContractSpec("permission_pattern_examples.jsonl", "permission_pattern_example", PermissionPatternExample),
    ImportContractSpec("attack_mobile_seed_mappings.jsonl", "attack_mobile_seed_mapping", AttackMobileSeedMapping),
)


def import_contracts_dir() -> Path:
    return paths.IMPORT_CONTRACTS_DIR


def _read_jsonl_lines(path: Path) -> list[tuple[int, str]]:
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"Could not read import contract file: {path}") from exc
    return [(index, line) for index, line in enumerate(content.splitlines(), start=1) if line.strip()]


def load_import_contract_file(path: Path, model: type[GovernedImportContractRecord]) -> list[GovernedImportContractRecord]:
    records: list[GovernedImportContractRecord] = []
    errors: list[str] = []
    for row_number, line in _read_jsonl_lines(path):
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"row {row_number}: invalid JSON ({exc.msg})")
            continue
        try:
            records.append(model.model_validate(payload))
        except ValidationError as exc:
            errors.append(f"row {row_number}: {exc.errors()[0]['loc'][0]} - {exc.errors()[0]['msg']}")
    if errors:
        raise ValueError(f"Import contract validation failed for {path.name}: " + "; ".join(errors))
    return records


def validate_import_contract_file(path: Path, model: type[GovernedImportContractRecord], record_type: str) -> ImportContractValidationSummary:
    valid_count = 0
    invalid_count = 0
    training_eligible_count = 0
    training_candidate_count = 0
    training_approved_count = 0
    teaching_only_count = 0
    explanation_only_count = 0
    validation_only_count = 0
    synthetic_count = 0
    issues: list[ImportContractValidationIssue] = []
    for row_number, line in _read_jsonl_lines(path):
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            invalid_count += 1
            issues.append(ImportContractValidationIssue(path.name, row_number, f"invalid JSON ({exc.msg})"))
            continue
        try:
            record = model.model_validate(payload)
        except ValidationError as exc:
            invalid_count += 1
            first = exc.errors()[0]
            issues.append(ImportContractValidationIssue(path.name, row_number, f"{first['loc'][0]} - {first['msg']}"))
            continue

        valid_count += 1
        if record.training_use:
            training_eligible_count += 1
        if record.training_eligibility == "training_candidate":
            training_candidate_count += 1
        elif record.training_eligibility == "training_approved":
            training_approved_count += 1
        elif record.training_eligibility == "teaching_only":
            teaching_only_count += 1
        elif record.training_eligibility == "explanation_only":
            explanation_only_count += 1
        elif record.training_eligibility == "validation_only":
            validation_only_count += 1
        if record.synthetic_level in {"medium", "high"}:
            synthetic_count += 1

    row_count = valid_count + invalid_count
    synthetic_heavy = valid_count > 0 and synthetic_count / valid_count >= 0.5
    return ImportContractValidationSummary(
        file_name=path.name,
        row_count=row_count,
        valid_count=valid_count,
        invalid_count=invalid_count,
        record_types_found=[record_type] if row_count else [],
        training_eligible_count=training_eligible_count,
        training_candidate_count=training_candidate_count,
        training_approved_count=training_approved_count,
        teaching_only_count=teaching_only_count,
        explanation_only_count=explanation_only_count,
        validation_only_count=validation_only_count,
        synthetic_heavy=synthetic_heavy,
        issues=issues,
    )


def validate_all_import_contract_files(root_dir: Path | None = None) -> list[ImportContractValidationSummary]:
    root = root_dir or import_contracts_dir()
    summaries: list[ImportContractValidationSummary] = []
    for spec in IMPORT_CONTRACT_SPECS:
        summaries.append(validate_import_contract_file(root / spec.file_name, spec.model, spec.record_type))
    return summaries
