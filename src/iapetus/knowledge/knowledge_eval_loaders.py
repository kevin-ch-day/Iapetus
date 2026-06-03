"""Deterministic benchmark evaluation for the Android teaching corpus."""
from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from iapetus import project_filesystem_paths as paths
from iapetus.knowledge.android_platform_concepts import (
    android_app_bundle_concept,
    android_app_concept,
    android_components_concept,
    android_concept,
    android_manifest_concept,
    android_runtime_concept,
    apk_concept,
    apk_signing_concept,
    permission_model_concept,
)
from iapetus.knowledge.import_contract_loaders import load_import_contract_file
from iapetus.knowledge.import_contract_models import (
    AndroidConceptLesson,
    AttackMobileSeedMapping,
    BenignAppArchetype,
    MalwareTypePattern,
    PermissionAuthorityFact,
    PermissionPatternExample,
)
from iapetus.knowledge.knowledge_eval_models import AndroidKnowledgeEvalQuestion, AndroidKnowledgeEvalResult

KNOWLEDGE_EVAL_FILE_NAME = "android_knowledge_eval_questions.jsonl"
KNOWLEDGE_EVAL_SCHEMA_NAME = "iapetus.android_knowledge_eval_question"
KNOWLEDGE_EVAL_SCHEMA_VERSION = "v1"

_WORD_SPLIT_RE = re.compile(r"[^a-z0-9.]+")


@dataclass(frozen=True)
class AndroidKnowledgeEvalSummary:
    total_questions: int
    covered_count: int
    partial_count: int
    gap_count: int
    gaps_by_topic: dict[str, int]
    gaps_by_difficulty: dict[str, int]
    trick_questions_not_fully_covered: list[AndroidKnowledgeEvalResult]
    recommended_next_seed_topics: list[str]
    results: list[AndroidKnowledgeEvalResult]


def knowledge_eval_file_path(root_dir: Path | None = None) -> Path:
    base_dir = root_dir or paths.IMPORT_CONTRACTS_DIR
    return base_dir / KNOWLEDGE_EVAL_FILE_NAME


def load_knowledge_eval_questions(path: Path | None = None) -> list[AndroidKnowledgeEvalQuestion]:
    file_path = path or knowledge_eval_file_path()
    try:
        content = file_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"Could not read knowledge eval file: {file_path}") from exc

    questions: list[AndroidKnowledgeEvalQuestion] = []
    errors: list[str] = []
    for row_number, line in enumerate(content.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"row {row_number}: invalid JSON ({exc.msg})")
            continue
        try:
            questions.append(AndroidKnowledgeEvalQuestion.model_validate(payload))
        except Exception as exc:  # pragma: no cover - defensive and still deterministic
            errors.append(f"row {row_number}: {exc}")
    if errors:
        raise ValueError(f"Knowledge eval validation failed for {file_path.name}: " + "; ".join(errors))
    return questions


def _normalize_term(value: str) -> str:
    normalized = _WORD_SPLIT_RE.sub("_", value.strip().lower()).strip("_")
    return normalized


def _add_value_terms(target: set[str], value: str) -> None:
    normalized = _normalize_term(value)
    if normalized and not any(character.isspace() for character in value):
        target.add(normalized)
    for part in re.split(r"[\s,/()]+", value.strip()):
        piece = _normalize_term(part)
        if piece:
            target.add(piece)


def _collect_structured_knowledge_terms(root_dir: Path | None = None) -> tuple[set[str], set[str]]:
    base_dir = root_dir or paths.IMPORT_CONTRACTS_DIR
    terms: set[str] = set()
    uncertainty_flags: set[str] = set()

    lessons = load_import_contract_file(base_dir / "android_concept_lessons.jsonl", AndroidConceptLesson)
    for row in lessons:
        for value in [row.concept_id, row.topic, row.title, row.summary, *row.related_concepts]:
            _add_value_terms(terms, value)

    permission_facts = load_import_contract_file(base_dir / "permission_authority_facts.jsonl", PermissionAuthorityFact)
    for row in permission_facts:
        for value in [row.permission, row.protection_level, row.permission_group, row.authority_type, row.grant_model, *row.known_abuse_concepts]:
            _add_value_terms(terms, value)

    patterns = load_import_contract_file(base_dir / "malware_type_patterns.jsonl", MalwareTypePattern)
    for row in patterns:
        for value in [row.pattern_id, row.malware_type, *row.permissions, *row.static_tokens, *row.concepts]:
            _add_value_terms(terms, value)

    archetypes = load_import_contract_file(base_dir / "benign_app_archetypes.jsonl", BenignAppArchetype)
    for row in archetypes:
        for value in [row.archetype_id, row.category, *row.expected_permissions, *row.expected_context, *row.contrast_notes]:
            _add_value_terms(terms, value)
        joined_notes = " ".join(row.contrast_notes).lower()
        if "not" in joined_notes and "malware" in joined_notes:
            uncertainty_flags.add("benign_contrast_required")
        if "context" in joined_notes:
            uncertainty_flags.add("requires_context")

    examples = load_import_contract_file(base_dir / "permission_pattern_examples.jsonl", PermissionPatternExample)
    for row in examples:
        for value in [row.example_id, row.label, row.teaches, *row.permissions, *row.benign_context, *row.suspicious_context]:
            _add_value_terms(terms, value)
        if "context" in row.teaches.lower():
            uncertainty_flags.add("requires_context")

    mappings = load_import_contract_file(base_dir / "attack_mobile_seed_mappings.jsonl", AttackMobileSeedMapping)
    for row in mappings:
        for value in [row.mapping_id, row.platform, row.concept, row.behavior_ref, row.use_case]:
            _add_value_terms(terms, value)
        if row.use_case == "explanation_only":
            uncertainty_flags.add("explanation_only_mapping")

    for concept in (
        android_concept,
        android_app_concept,
        apk_concept,
        android_app_bundle_concept,
        android_manifest_concept,
        android_runtime_concept,
        apk_signing_concept,
        android_components_concept,
        permission_model_concept,
    ):
        for value in [
            concept.concept_id,
            concept.display_name,
            concept.definition,
            concept.notes,
            *concept.key_fields,
            *concept.static_evidence,
            *concept.dynamic_evidence,
        ]:
            _add_value_terms(terms, value)
        if concept.concept_id == "permission_model":
            uncertainty_flags.add("runtime_permission_model")
        if concept.concept_id == "android_manifest":
            uncertainty_flags.add("manifest_is_foundation")

    return terms, uncertainty_flags


def _term_is_known(expected_term: str, known_terms: set[str]) -> bool:
    normalized_expected = _normalize_term(expected_term)
    if not normalized_expected:
        return False
    if normalized_expected in known_terms:
        return True
    return any(
        known == normalized_expected
        or known.startswith(f"{normalized_expected}_")
        for known in known_terms
    )


def evaluate_android_knowledge(root_dir: Path | None = None) -> AndroidKnowledgeEvalSummary:
    questions = load_knowledge_eval_questions(knowledge_eval_file_path(root_dir))
    known_terms, known_uncertainty_flags = _collect_structured_knowledge_terms(root_dir)

    results: list[AndroidKnowledgeEvalResult] = []
    gaps_by_topic: Counter[str] = Counter()
    gaps_by_difficulty: Counter[str] = Counter()
    missing_topic_counter: Counter[str] = Counter()

    for question in questions:
        matched_concepts = [concept for concept in question.expected_concepts if _term_is_known(concept, known_terms)]
        missing_concepts = [concept for concept in question.expected_concepts if concept not in matched_concepts]
        matched_flags = [flag for flag in question.expected_uncertainty_flags if _term_is_known(flag, known_uncertainty_flags)]
        missing_flags = [flag for flag in question.expected_uncertainty_flags if flag not in matched_flags]

        concept_total = len(question.expected_concepts)
        flag_total = len(question.expected_uncertainty_flags)
        concept_coverage = len(matched_concepts) / concept_total if concept_total else 1.0
        flag_coverage = len(matched_flags) / flag_total if flag_total else 1.0

        if not question.expected_concepts and not question.expected_uncertainty_flags:
            status = "gap"
        elif concept_coverage == 1.0 and flag_coverage == 1.0:
            status = "covered"
        elif concept_coverage >= 0.5 or flag_coverage >= 0.5:
            status = "partial"
        else:
            status = "gap"

        result = AndroidKnowledgeEvalResult(
            question_id=question.question_id,
            topic=question.topic,
            difficulty=question.difficulty,
            status=status,
            question=question.question,
            matched_concepts=matched_concepts,
            missing_concepts=missing_concepts,
            matched_uncertainty_flags=matched_flags,
            missing_uncertainty_flags=missing_flags,
        )
        results.append(result)

        if status != "covered":
            gaps_by_topic[question.topic] += 1
            gaps_by_difficulty[question.difficulty] += 1
            missing_topic_counter[question.topic] += len(missing_concepts) + len(missing_flags)

    covered_count = sum(1 for row in results if row.status == "covered")
    partial_count = sum(1 for row in results if row.status == "partial")
    gap_count = sum(1 for row in results if row.status == "gap")
    trick_questions_not_fully_covered = [
        row for row in results if row.difficulty == "trick" and row.status != "covered"
    ]
    recommended_next_seed_topics = [
        topic for topic, _ in missing_topic_counter.most_common(5)
    ]

    return AndroidKnowledgeEvalSummary(
        total_questions=len(results),
        covered_count=covered_count,
        partial_count=partial_count,
        gap_count=gap_count,
        gaps_by_topic=dict(sorted(gaps_by_topic.items())),
        gaps_by_difficulty=dict(sorted(gaps_by_difficulty.items())),
        trick_questions_not_fully_covered=trick_questions_not_fully_covered,
        recommended_next_seed_topics=recommended_next_seed_topics,
        results=results,
    )
