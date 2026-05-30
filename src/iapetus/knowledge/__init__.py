"""Seed knowledge models and registry."""

from pathlib import Path
from typing import Iterable

from .android import (
    ArtifactTypeKnowledge,
    EvidenceTypeKnowledge,
    KnowledgeConcept,
    android_app_bundle_concept as aab_concept,
    android_concept,
    android_manifest_concept,
    android_app_concept,
    android_runtime_concept,
    android_components_concept,
    apk_signing_concept,
    apk_concept,
    permission_model_concept,
)
from .registry import (
    ArtifactRelevance,
    ArtifactType,
    ArtifactClassification,
    ArtifactClassifier,
    find_matching_concepts,
    normalize_artifact_path,
    concept_summary,
    concept_registry,
    get_concept,
    lesson_lines,
    list_lesson_ids,
    get_lesson,
    find_matching_lessons,
    list_concept_ids,
    print_concepts,
    classify_artifact,
)
from .apk import (
    ApkAnatomyPart,
    APK_ANATOMY_PARTS,
    apk_anatomy_lines as apk_anatomy_lines,
)
from .fake import (
    FakePermission,
    FakeComponent,
    FakeAndroidArtifact,
    DATASET_TOPICS,
    SYNTHETIC_DATASET_ROWS,
    FAKE_ANDROID_APPS,
    PERMISSION_LEVEL_REFERENCE,
    fake_data_lines,
    get_fake_data,
    list_fake_topics,
    get_dataset_row_count,
)

__all__ = [
    "KnowledgeConcept",
    "ArtifactTypeKnowledge",
    "EvidenceTypeKnowledge",
    "ArtifactType",
    "ArtifactRelevance",
    "ArtifactClassification",
    "ArtifactClassifier",
    "android_concept",
    "android_app_concept",
    "aab_concept",
    "apk_concept",
    "android_manifest_concept",
    "android_runtime_concept",
    "apk_signing_concept",
    "android_components_concept",
    "permission_model_concept",
    "run_concepts",
    "apk_anatomy_lines",
    "concept_summary",
    "concept_registry",
    "get_concept",
    "get_lesson",
    "list_concept_ids",
    "list_lesson_ids",
    "print_concepts",
    "classify_artifact",
    "find_matching_concepts",
    "find_matching_lessons",
    "normalize_artifact_path",
    "lesson_lines",
    "ApkAnatomyPart",
    "APK_ANATOMY_PARTS",
    "FakePermission",
    "FakeComponent",
    "FakeAndroidArtifact",
    "FAKE_ANDROID_APPS",
    "PERMISSION_LEVEL_REFERENCE",
    "SYNTHETIC_DATASET_ROWS",
    "DATASET_TOPICS",
    "fake_data_lines",
    "get_fake_data",
    "list_fake_topics",
    "get_dataset_row_count",
]


def run_concepts() -> Iterable[KnowledgeConcept]:
    """Iterate seed concepts in a stable order."""
    return (
        android_concept,
        android_app_concept,
        apk_concept,
        aab_concept,
        android_manifest_concept,
        android_runtime_concept,
        apk_signing_concept,
        android_components_concept,
        permission_model_concept,
    )


def concepts_root_dir() -> Path:
    """Return the repository seed knowledge location."""
    return Path(__file__).parent


def __all_imports__() -> dict[str, str]:
    return {
        "android": android_concept.concept_id,
        "android_app": android_app_concept.concept_id,
        "apk": apk_concept.concept_id,
        "aab": aab_concept.concept_id,
        "android_manifest": android_manifest_concept.concept_id,
        "android_runtime": android_runtime_concept.concept_id,
        "apk_signing": apk_signing_concept.concept_id,
        "android_components": android_components_concept.concept_id,
        "permission_model": permission_model_concept.concept_id,
    }
