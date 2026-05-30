from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from iapetus.validation.fixture_quality_heuristics import (
    IssueCategory,
    _HARD_BLOCKING_ISSUES,
    _MALWARE_LABEL_RE,
    _NORMAL_APP_TRAINING_BLOCKERS,
    _NORMAL_LABEL_RE,
    classify_fixture_quality_issues,
    collect_android_markers,
    collect_windows_markers,
    entity_kind_from_sample_type,
    is_canonical_permission,
    label_structure_issues,
    package_name_issues,
)

__all__ = [
    "FixtureQualityResult",
    "IssueCategory",
    "_MALWARE_LABEL_RE",
    "_NORMAL_LABEL_RE",
    "build_training_quality_contract",
    "classify_fixture_quality_issues",
    "collect_android_markers",
    "collect_windows_markers",
    "is_canonical_permission",
    "label_structure_issues",
    "package_name_issues",
    "validate_fixture_quality",
]

def severity_for_issues(issues: list[IssueCategory]) -> str:
    if any(
        issue in issues
        for issue in (
            "windows_artifact_in_android_context",
            "entity_kind_label_conflict",
            "malformed_permission",
            "malformed_label",
            "invalid_package_name",
        )
    ):
        return "error"
    if any(
        issue in issues
        for issue in ("contradictory_context", "suspicious_overclaim", "platform_extension_conflict")
    ):
        return "warn"
    if issues == ["low_confidence_unknown"]:
        return "info"
    return "info"


def messages_for_issues(issues: list[IssueCategory]) -> list[str]:
    messages: list[str] = []
    if "windows_artifact_in_android_context" in issues:
        messages.append("Windows PE/path markers appear inside an AndroidOS-labeled record.")
    if "platform_extension_conflict" in issues:
        messages.append("File extension and platform disagree (e.g., exe/apk vs AndroidOS/UnknownOS).")
    if "entity_kind_label_conflict" in issues:
        messages.append("sample_type does not match label payload or rendered label shape.")
    if "malformed_permission" in issues:
        messages.append("One or more permission strings are blank or not canonical android.permission.* form.")
    if "malformed_label" in issues:
        messages.append("Rendered or example labels do not match Iapetus label grammar.")
    if "contradictory_context" in issues:
        messages.append(
            "Benign entity_kind co-occurs with banker-like permissions or suspicious indicators; "
            "requires analyst review before benign training use."
        )
    if "suspicious_overclaim" in issues:
        messages.append("Claimed benign category is inconsistent with high-risk permissions/code strings.")
    if "unknown_or_unsupported_platform" in issues:
        messages.append("Platform is not AndroidOS; treat as unsupported for Android training contracts.")
    if "missing_required_identity" in issues:
        messages.append("Missing sample_type or package/file identity fields.")
    if "invalid_package_name" in issues:
        messages.append("package_name is not a valid Android applicationId-style identifier.")
    if "low_confidence_unknown" in issues:
        messages.append("No blocking issue detected by current seed rules.")
    return messages


@dataclass
class FixtureQualityResult:
    fixture_slug: str
    sample_id: str
    sample_name: str
    issues: list[IssueCategory]
    messages: list[str] = field(default_factory=list)
    severity: str = "info"
    training_eligible: bool = True
    training_blockers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "fixture_slug": self.fixture_slug,
            "sample_id": self.sample_id,
            "sample_name": self.sample_name,
            "issues": self.issues,
            "messages": self.messages,
            "severity": self.severity,
            "training_eligible": self.training_eligible,
            "training_blockers": self.training_blockers,
        }


def training_blockers_from_issues(issues: list[IssueCategory], entity_kind: str = "unknown") -> list[str]:
    blocking = set(_HARD_BLOCKING_ISSUES)
    if entity_kind == "normal_app":
        blocking.update(_NORMAL_APP_TRAINING_BLOCKERS)
    return [issue for issue in issues if issue in blocking]


def validate_fixture_quality(fixture: dict[str, Any]) -> FixtureQualityResult:
    slug = str(fixture.get("fixture_slug", fixture.get("sample_name", "unknown"))).strip()
    entity_kind = entity_kind_from_sample_type(str(fixture.get("sample_type", "")))
    issues = classify_fixture_quality_issues(fixture)
    blockers = training_blockers_from_issues(issues, entity_kind=entity_kind)
    clean_issues = [issue for issue in issues if issue != "low_confidence_unknown"]
    return FixtureQualityResult(
        fixture_slug=slug,
        sample_id=str(fixture.get("sample_id", "")),
        sample_name=str(fixture.get("sample_name", "")),
        issues=clean_issues or issues,
        messages=messages_for_issues(issues),
        severity=severity_for_issues(issues),
        training_eligible=len(blockers) == 0 and severity_for_issues(issues) != "error",
        training_blockers=blockers,
    )


def build_training_quality_contract() -> dict[str, Any]:
    return {
        "contract_version": "seed-1",
        "training_eligible_requires": [
            "canonical android.permission.* only",
            "sample_type aligned with label payload and rendered label",
            "platform AndroidOS for Android training rows",
            "no Windows PE markers in Android rows",
            "no entity_kind_label_conflict",
        ],
        "review_recommended_issues": [
            "contradictory_context (malware rows only; normal_app rows block training)",
            "suspicious_overclaim (malware rows only; normal_app rows block training)",
        ],
        "never_train_from": [
            "adversarial_test fixture set",
            "fixtures with training_blockers present",
        ],
        "blocking_issue_categories": sorted(_HARD_BLOCKING_ISSUES | _NORMAL_APP_TRAINING_BLOCKERS),
        "normal_app_extra_blockers": sorted(_NORMAL_APP_TRAINING_BLOCKERS),
    }
