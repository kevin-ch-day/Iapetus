"""Knowledge registry and conservative artifact classifier."""

from __future__ import annotations

from dataclasses import dataclass
import difflib
from enum import Enum
from pathlib import Path
import re

from .android_platform_concepts import (
    ArtifactTypeKnowledge,
    EvidenceTypeKnowledge,
    KnowledgeConcept,
    android_app_bundle_concept as aab_concept,
    android_app_concept,
    android_concept,
    android_manifest_concept,
    android_components_concept,
    android_runtime_concept,
    apk_signing_concept,
    apk_concept,
    permission_model_concept,
)
from .apk_anatomy_reference import apk_anatomy_lines


class ArtifactType(str, Enum):
    ANDROID_APK = "Android APK"
    ANDROID_AAB = "Android AAB"
    ANDROID_DEX = "Android DEX"
    WINDOWS_PE = "Windows PE"
    WINDOWS_POWER_SHELL = "Windows PowerShell Script"
    LINUX_UNIX_ARTIFACT = "Linux/Unix Artifact"
    UNKNOWN = "Unknown"


@dataclass(frozen=True)
class ArtifactRelevance:
    eligible_for_android_permission_analysis: bool
    eligible_for_android_static_analysis: bool
    eligible_for_android_dynamic_analysis: bool
    eligible_for_windows_pe_analysis: bool
    eligible_for_generic_av_token_learning: bool


@dataclass(frozen=True)
class ArtifactClassification:
    artifact_type: str
    relevance: ArtifactRelevance
    normalized_path: str
    evidence: str = "extension"
    normalized_extension: str = ""
    relevant_concepts: tuple[str, ...] = ()


@dataclass(frozen=True)
class KnowledgeLesson:
    lesson_id: str
    title: str
    takeaways: tuple[str, ...]
    commands: tuple[str, ...]
    related_concepts: tuple[str, ...]


def _strip_uri_suffix(path: str) -> str:
    # Keep only a local path-style suffix when classifier input includes query strings
    # or fragment markers copied from logs/UI output.
    for marker in ("?", "#"):
        if marker in path:
            path = path.split(marker, 1)[0]
    return path


def concept_registry() -> dict[str, KnowledgeConcept]:
    return {
        android_concept.concept_id: android_concept,
        android_app_concept.concept_id: android_app_concept,
        apk_concept.concept_id: apk_concept,
        aab_concept.concept_id: aab_concept,
        android_manifest_concept.concept_id: android_manifest_concept,
        permission_model_concept.concept_id: permission_model_concept,
        android_runtime_concept.concept_id: android_runtime_concept,
        apk_signing_concept.concept_id: apk_signing_concept,
        android_components_concept.concept_id: android_components_concept,
    }


_LESSONS: tuple[KnowledgeLesson, ...] = (
    KnowledgeLesson(
        lesson_id="android_fundamentals",
        title="Android fundamentals",
        takeaways=(
            "Android is a Linux-based mobile OS with per-app isolation, manifest-driven package install, "
            "and managed lifecycle behavior.",
            "Permission behavior includes install-time and runtime grants depending on permission group and target API.",
            "ADB is the primary host-device protocol for local instrumentation and seed troubleshooting.",
            "Iapetus currently uses demo fixtures and static metadata only for this lesson.",
        ),
        commands=(
            "iapetus knowledge show android",
            "iapetus knowledge show permission_model",
        ),
        related_concepts=("android", "permission_model"),
    ),
    KnowledgeLesson(
        lesson_id="apk_anatomy",
        title="APK anatomy",
        takeaways=(
            "An APK is a signed ZIP-like package used to distribute installable Android apps.",
            "AndroidManifest.xml declares identity, permissions, and components.",
            "classes.dex is where app code is stored for ART runtime execution.",
            "META-INF and signature metadata are the seed trust artifact for install decisions.",
        ),
        commands=("iapetus knowledge apk-anatomy", "iapetus knowledge show apk", "iapetus knowledge show android_manifest"),
        related_concepts=("apk", "android_manifest", "apk_signing"),
    ),
    KnowledgeLesson(
        lesson_id="learning_pipeline",
        title="Seed learning pipeline",
        takeaways=(
            "Labels are source-of-truth structured fields, with rendered strings as export artifacts.",
            "Learning run artifacts are written under output/learning_runs/<run_id> for seed lifecycle tracking.",
            "Classifier behavior here is extension-based and intentionally conservative.",
            "Future steps add data quality checks before model training.",
        ),
        commands=(
            "iapetus learn run --mode smoke --write",
            "iapetus learn absorb",
            "iapetus learn explain-token --token android.permission.READ_SMS",
            "iapetus learn list",
            "iapetus dataset shape",
        ),
        related_concepts=("android_app", "android_runtime"),
    ),
)


def list_lesson_ids() -> list[str]:
    return [lesson.lesson_id for lesson in _LESSONS]


def get_lesson(lesson_id: str) -> KnowledgeLesson:
    normalized = _resolve_lesson_alias(lesson_id)
    lesson = {lesson.lesson_id: lesson for lesson in _LESSONS}.get(normalized)
    if lesson is None:
        raise KeyError(f"Unknown lesson '{lesson_id}'")
    return lesson


def lesson_lines(lesson_id: str) -> list[str]:
    lesson = get_lesson(lesson_id)
    lines = [
        f"{lesson.lesson_id} - {lesson.title}",
        "Takeaways:",
    ]
    lines.extend([f"  - {takeaway}" for takeaway in lesson.takeaways])
    lines.append("Commands:")
    lines.extend([f"  - {command}" for command in lesson.commands])
    lines.append(f"Related concepts: {', '.join(lesson.related_concepts)}")
    return lines


def find_matching_lessons(requested: str, limit: int = 3) -> list[str]:
    requested = requested.strip().lower()
    if not requested:
        return []
    return difflib.get_close_matches(
        requested,
        list_lesson_ids(),
        n=limit,
        cutoff=0.55,
    )


def _lesson_match_map() -> dict[str, str]:
    matches: dict[str, str] = {}
    for lesson in _LESSONS:
        matches[lesson.lesson_id] = lesson.lesson_id
        matches[lesson.lesson_id.replace("_", " ")] = lesson.lesson_id
        matches[lesson.lesson_id.replace("_", "-")] = lesson.lesson_id
    return matches


def _resolve_lesson_alias(lesson_id: str) -> str:
    normalized = _normalize_concept_id(lesson_id)
    return _lesson_match_map().get(normalized, normalized)


def _normalize_concept_id(value: str) -> str:
    cleaned = value.strip().lower()
    cleaned = re.sub(r"[_\s]+", "_", cleaned)
    return cleaned.replace("-", "_")


_CONCEPT_ALIAS_MAP: dict[str, str] = {
    "android_app_package": "android_app",
    "android app package": "android_app",
    "android app": "android_app",
    "apk artifact": "apk",
    "android manifest": "android_manifest",
    "permission model": "permission_model",
    "app bundle": "aab",
    "android app bundle": "aab",
    "aab": "aab",
    "android runtime": "android_runtime",
    "apk signing": "apk_signing",
    "apk signature": "apk_signing",
}


def _resolve_concept_alias(concept_id: str) -> str:
    normalized = _normalize_concept_id(concept_id)
    return _CONCEPT_ALIAS_MAP.get(normalized, normalized)


def get_concept(concept_id: str) -> KnowledgeConcept:
    normalized_id = _resolve_concept_alias(concept_id)
    concept = concept_registry().get(normalized_id)
    if concept is None:
        raise KeyError(f"Unknown concept '{concept_id}'")
    return concept


def list_concept_ids() -> list[str]:
    return sorted(concept_registry().keys())


def find_matching_concepts(requested: str, limit: int = 3) -> list[str]:
    requested = requested.strip().lower()
    if not requested:
        return []
    return difflib.get_close_matches(
        requested,
        list_concept_ids(),
        n=limit,
        cutoff=0.55,
    )


def normalize_artifact_path(path: str) -> str:
    return _strip_uri_suffix(path.strip().strip('"').strip("'"))


def _artifact_path_metadata(path: str) -> tuple[str, str]:
    normalized_path = normalize_artifact_path(path)
    if not normalized_path:
        raise ValueError("artifact path cannot be blank")
    suffix = Path(normalized_path).suffix.lower()
    if not suffix:
        return normalized_path, ""
    return normalized_path, suffix


def print_concepts() -> list[str]:
    lines = []
    for concept_id, concept in concept_registry().items():
        label = "Artifact" if isinstance(concept, ArtifactTypeKnowledge) else "Evidence"
        lines.append(f"{concept_id} ({label}): {concept.display_name}")
    return lines


def concept_summary(concept: KnowledgeConcept) -> str:
    return f"{concept.concept_id}: {concept.display_name} - {concept.definition}"


def _relevance_by_type(artifact_type: ArtifactType) -> ArtifactRelevance:
    if artifact_type in {ArtifactType.ANDROID_APK, ArtifactType.ANDROID_AAB, ArtifactType.ANDROID_DEX}:
        return ArtifactRelevance(
            eligible_for_android_permission_analysis=True,
            eligible_for_android_static_analysis=True,
            eligible_for_android_dynamic_analysis=True,
            eligible_for_windows_pe_analysis=False,
            eligible_for_generic_av_token_learning=True,
        )
    if artifact_type is ArtifactType.WINDOWS_PE:
        return ArtifactRelevance(
            eligible_for_android_permission_analysis=False,
            eligible_for_android_static_analysis=False,
            eligible_for_android_dynamic_analysis=False,
            eligible_for_windows_pe_analysis=True,
            eligible_for_generic_av_token_learning=True,
        )
    if artifact_type in {ArtifactType.WINDOWS_POWER_SHELL, ArtifactType.LINUX_UNIX_ARTIFACT}:
        return ArtifactRelevance(
            eligible_for_android_permission_analysis=False,
            eligible_for_android_static_analysis=False,
            eligible_for_android_dynamic_analysis=False,
            eligible_for_windows_pe_analysis=False,
            eligible_for_generic_av_token_learning=True,
        )
    return ArtifactRelevance(
        eligible_for_android_permission_analysis=False,
        eligible_for_android_static_analysis=False,
        eligible_for_android_dynamic_analysis=False,
        eligible_for_windows_pe_analysis=False,
        eligible_for_generic_av_token_learning=False,
    )


def _relevant_concepts_for_type(artifact_type: ArtifactType) -> tuple[str, ...]:
    if artifact_type is ArtifactType.ANDROID_APK:
        return (
            "apk",
            "android_manifest",
            "permission_model",
            "android_components",
            "apk_signing",
        )
    if artifact_type is ArtifactType.ANDROID_AAB:
        return (
            "aab",
            "apk",
            "android_manifest",
            "permission_model",
            "apk_signing",
        )
    if artifact_type is ArtifactType.ANDROID_DEX:
        return ("apk", "android_runtime", "android_app")
    if artifact_type is ArtifactType.WINDOWS_PE:
        return ()
    if artifact_type is ArtifactType.WINDOWS_POWER_SHELL:
        return ()
    if artifact_type is ArtifactType.LINUX_UNIX_ARTIFACT:
        return ()
    return ()


def _classify_extension(suffix: str) -> ArtifactType:
    mapping = {
        ".apk": ArtifactType.ANDROID_APK,
        ".aab": ArtifactType.ANDROID_AAB,
        ".dex": ArtifactType.ANDROID_DEX,
        ".exe": ArtifactType.WINDOWS_PE,
        ".dll": ArtifactType.WINDOWS_PE,
        ".ps1": ArtifactType.WINDOWS_POWER_SHELL,
        ".sh": ArtifactType.LINUX_UNIX_ARTIFACT,
        ".so": ArtifactType.LINUX_UNIX_ARTIFACT,
    }
    return mapping.get(suffix, ArtifactType.UNKNOWN)


def classify_artifact(path: str) -> ArtifactClassification:
    normalized_path, suffix = _artifact_path_metadata(path)
    artifact_type = _classify_extension(suffix)
    evidence = f"resolved by extension ({suffix or '<none>'})"

    return ArtifactClassification(
        artifact_type=artifact_type.value,
        normalized_path=normalized_path,
        evidence=evidence,
        normalized_extension=suffix,
        relevance=_relevance_by_type(artifact_type),
        relevant_concepts=_relevant_concepts_for_type(artifact_type),
    )


class ArtifactClassifier:
    @staticmethod
    def classify(path: str) -> ArtifactClassification:
        return classify_artifact(path)
