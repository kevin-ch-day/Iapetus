from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Literal

from iapetus.labels.renderer import InvalidLabelError, render_malware_label, render_normal_app_label

IssueCategory = Literal[
    "platform_extension_conflict",
    "entity_kind_label_conflict",
    "malformed_permission",
    "malformed_label",
    "suspicious_overclaim",
    "android_platform_conflict",
    "windows_artifact_in_android_context",
    "contradictory_context",
    "unknown_or_unsupported_platform",
    "missing_required_identity",
    "invalid_package_name",
    "low_confidence_unknown",
]

_HARD_BLOCKING_ISSUES = frozenset(
    {
        "windows_artifact_in_android_context",
        "entity_kind_label_conflict",
        "malformed_permission",
        "malformed_label",
        "platform_extension_conflict",
        "unknown_or_unsupported_platform",
        "android_platform_conflict",
        "missing_required_identity",
        "invalid_package_name",
    }
)
_NORMAL_APP_TRAINING_BLOCKERS = frozenset({"contradictory_context", "suspicious_overclaim"})

_CANONICAL_PERMISSION_RE = re.compile(r"^android\.permission\.[A-Z][A-Z0-9_]+$")
_MALWARE_LABEL_RE = re.compile(r"^[^:]+:[^:.\[\]]+\.[^:.\[\]]+-[^:.\[\]]+:\[[^\]]+\]$")
_NORMAL_LABEL_RE = re.compile(r"^[^:]+:[^:.\[\]]+-[^:.\[\]]+:\[[^\]]+\]$")
_ANDROID_PACKAGE_SEGMENT_RE = re.compile(r"^[a-z][a-z0-9_]*$")
_WINDOWS_MARKERS = (
    "kernel32",
    "createprocessw",
    "mz",
    " pe",
    ".exe",
    "c:\\windows",
    "system32",
)
_ANDROID_PACKAGE_RE = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$")
_BANKER_LIKE_INDICATORS = frozenset(
    {"sms_intercept", "overlay_attack", "accessibility_abuse", "cleartext_c2", "boot_persistence"}
)
_HIGH_RISK_PERMISSIONS = frozenset(
    {
        "android.permission.READ_SMS",
        "android.permission.RECEIVE_SMS",
        "android.permission.SEND_SMS",
        "android.permission.BIND_ACCESSIBILITY_SERVICE",
        "android.permission.SYSTEM_ALERT_WINDOW",
        "android.permission.REQUEST_INSTALL_PACKAGES",
    }
)


def entity_kind_from_sample_type(sample_type: str) -> str:
    lowered = sample_type.strip().lower()
    if lowered in {"malware", "malicious"}:
        return "malware"
    if lowered in {"benign", "normal", "normal_app", "normal-app"}:
        return "normal_app"
    return "unknown"


def string_list_field(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def is_canonical_permission(permission: str) -> bool:
    return bool(_CANONICAL_PERMISSION_RE.fullmatch(permission.strip()))


def known_permission_set() -> set[str]:
    from iapetus.data_library import load_permission_seed

    return {
        str(item.get("permission", "")).strip()
        for item in load_permission_seed()
        if item.get("permission")
    }


def package_name_issues(package_name: str) -> list[str]:
    package = package_name.strip()
    if not package:
        return []
    if "\\" in package or "/" in package or package.lower().endswith((".exe", ".dll", ".sys")):
        return ["invalid_package_name"]
    if package != package.strip() or " " in package or ".." in package or package.startswith(".") or package.endswith("."):
        return ["invalid_package_name"]
    if "\x00" in package or "\u0000" in package:
        return ["invalid_package_name"]
    if package != package.lower():
        return ["invalid_package_name"]
    if not _ANDROID_PACKAGE_RE.fullmatch(package):
        return ["invalid_package_name"]
    segments = package.split(".")
    if any(not segment or not _ANDROID_PACKAGE_SEGMENT_RE.fullmatch(segment) for segment in segments):
        return ["invalid_package_name"]
    return []


def smuggled_normal_label_issues(label: str) -> list[str]:
    """Catch app_name-build_ref shapes written with an extra dot (Face.book-1)."""
    if not _MALWARE_LABEL_RE.match(label):
        return []
    parts = label.split(":", 2)
    if len(parts) < 3:
        return []
    body = parts[1]
    if "." not in body or "-" not in body:
        return []
    _primary, rest = body.split(".", 1)
    _family, variant = rest.rsplit("-", 1)
    if variant.isdigit():
        return ["normal-app label shape smuggled with embedded dot"]
    return []


def label_segment_issues(label: str) -> list[str]:
    issues: list[str] = []
    if "::" in label or ".." in label:
        issues.append("empty or doubled label segment")
    if ".-" in label or "-." in label:
        issues.append("invalid dot-hyphen sequence")
    body = label.split(":", 2)
    if len(body) >= 2 and not body[1].strip():
        issues.append("empty label body segment")
    return issues


def label_structure_issues(label: str) -> list[str]:
    issues: list[str] = []
    text = label.strip()
    if not text:
        issues.append("empty label")
        return issues
    issues.extend(label_segment_issues(text))
    issues.extend(smuggled_normal_label_issues(text))
    if ":[:" in text:
        issues.append("empty label segment")
    if text.count(":") < 2:
        issues.append("missing colon segments")
    if "[" not in text or "]" not in text:
        issues.append("missing bracketed subtype/category")
    elif not text.endswith("]"):
        issues.append("subtype/category must be bracketed at end")
    platform = text.split(":", 1)[0] if ":" in text else ""
    if platform and platform != "AndroidOS":
        issues.append(f"unexpected platform '{platform}'")
    malware_match = bool(_MALWARE_LABEL_RE.match(text))
    normal_match = bool(_NORMAL_LABEL_RE.match(text))
    if malware_match and normal_match:
        issues.append("ambiguous malware/normal label shape")
    elif malware_match or normal_match:
        return issues
    if "-" not in text or ":" not in text:
        issues.append("does not match malware or normal label shape")
    else:
        issues.append("does not match malware or normal label shape")
    return issues


def collect_windows_markers(fixture: dict[str, Any]) -> list[str]:
    markers: list[str] = []
    haystack_parts = [
        str(fixture.get("package_name", "")),
        str(fixture.get("file_name", "")),
        str(fixture.get("file_extension", "")),
        " ".join(string_list_field(fixture.get("code_strings"))),
    ]
    haystack = " ".join(haystack_parts).lower()
    for marker in _WINDOWS_MARKERS:
        if marker.strip() and marker in haystack:
            markers.append(marker.strip())
    if str(fixture.get("file_extension", "")).strip().lower() in {"exe", "dll", "sys"}:
        markers.append(f"file_extension={fixture.get('file_extension')}")
    return sorted(set(markers))


def collect_android_markers(fixture: dict[str, Any]) -> list[str]:
    markers: list[str] = []
    package = str(fixture.get("package_name", "")).strip()
    if package and not package_name_issues(package):
        markers.append(f"package_name={package}")
    for permission in string_list_field(fixture.get("permissions")):
        if permission.startswith("android.permission."):
            markers.append(permission)
    if str(fixture.get("file_extension", "")).strip().lower() == "apk":
        markers.append("file_extension=apk")
    for token in string_list_field(fixture.get("code_strings")):
        lowered = token.lower()
        if lowered in {"dexclassloader", "smsmanager", "telephonymanager"}:
            markers.append(token)
    return markers


def labels_match_entity_kind(entity_kind: str, labels: dict[str, Any]) -> bool:
    if entity_kind == "malware":
        required = ("malware_primary", "family", "variant", "subtype")
        return all(key in labels for key in required)
    if entity_kind == "normal_app":
        required = ("app_name", "build_ref", "app_category")
        return all(key in labels for key in required)
    return False


def classify_fixture_quality_issues(fixture: dict[str, Any]) -> list[IssueCategory]:
    issues: list[IssueCategory] = []
    sample_type = str(fixture.get("sample_type", "")).strip()
    entity_kind = entity_kind_from_sample_type(sample_type)
    platform = str(fixture.get("platform", "")).strip()
    labels = fixture.get("labels") if isinstance(fixture.get("labels"), dict) else {}
    raw_package_name = str(fixture.get("package_name", ""))
    package_name = raw_package_name.strip()
    file_extension = str(fixture.get("file_extension", "")).strip().lower()

    if not sample_type:
        issues.append("missing_required_identity")
    if raw_package_name != package_name:
        issues.append("invalid_package_name")
    if not package_name and not fixture.get("file_name"):
        issues.append("missing_required_identity")

    windows_markers = collect_windows_markers(fixture)
    if platform == "AndroidOS" and windows_markers:
        issues.append("windows_artifact_in_android_context")
    if platform == "AndroidOS" and file_extension in {"exe", "dll", "sys"}:
        issues.append("platform_extension_conflict")
    if file_extension == "apk" and platform not in {"", "AndroidOS"}:
        issues.append("platform_extension_conflict")
    if platform and platform not in {"AndroidOS"}:
        issues.append("unknown_or_unsupported_platform")
    if platform == "AndroidOS" and file_extension == "apk" and windows_markers:
        issues.append("android_platform_conflict")

    permissions = string_list_field(fixture.get("permissions"))
    if not permissions:
        issues.append("malformed_permission")
    elif len(permissions) != len(set(permission.strip() for permission in permissions)):
        issues.append("malformed_permission")
    known_permissions = known_permission_set()
    for permission in permissions:
        if not permission.strip() or not is_canonical_permission(permission):
            issues.append("malformed_permission")
            break
        if permission.strip() not in known_permissions:
            issues.append("malformed_permission")
            break

    for package_issue in package_name_issues(package_name):
        if package_issue not in issues:
            issues.append(package_issue)  # type: ignore[arg-type]

    rendered = str(fixture.get("rendered_label", "")).strip()
    label_examples = string_list_field(fixture.get("rendered_label_examples"))
    labels_to_check = label_examples if label_examples else ([rendered] if rendered else [])
    for label in labels_to_check:
        if label_structure_issues(label):
            issues.append("malformed_label")
            break

    if entity_kind in {"malware", "normal_app"}:
        if not labels or not labels_match_entity_kind(entity_kind, labels):
            issues.append("entity_kind_label_conflict")
        else:
            try:
                if entity_kind == "malware":
                    render_malware_label(labels)
                else:
                    render_normal_app_label(labels)
            except (InvalidLabelError, KeyError, TypeError, ValueError):
                issues.append("entity_kind_label_conflict")

    if rendered:
        if entity_kind == "malware" and _NORMAL_LABEL_RE.match(rendered) and not _MALWARE_LABEL_RE.match(rendered):
            issues.append("entity_kind_label_conflict")
        if entity_kind == "normal_app" and _MALWARE_LABEL_RE.match(rendered):
            issues.append("entity_kind_label_conflict")

    has_malware_label_fields = any(key in labels for key in ("malware_primary", "family", "subtype"))
    has_normal_label_fields = any(key in labels for key in ("app_name", "app_category"))
    if entity_kind == "normal_app" and has_malware_label_fields:
        issues.append("entity_kind_label_conflict")
    if entity_kind == "malware" and has_normal_label_fields and not has_malware_label_fields:
        issues.append("entity_kind_label_conflict")
    if entity_kind == "malware" and has_normal_label_fields and has_malware_label_fields:
        issues.append("entity_kind_label_conflict")
    if entity_kind == "unknown" and sample_type:
        issues.append("entity_kind_label_conflict")

    suspicious = set(string_list_field(fixture.get("suspicious_indicators")))
    permission_set = set(permissions)
    if entity_kind == "normal_app" and suspicious & _BANKER_LIKE_INDICATORS:
        issues.append("contradictory_context")
    if entity_kind == "normal_app" and permission_set & _HIGH_RISK_PERMISSIONS and suspicious:
        issues.append("contradictory_context")

    classification = str(fixture.get("expected_classification", labels.get("app_category", ""))).lower()
    if entity_kind == "normal_app":
        risky_code = " ".join(string_list_field(fixture.get("code_strings"))).lower()
        utility_like = classification in {"utility", "utilities", "tools", "flashlight"}
        if utility_like and (
            permission_set & _HIGH_RISK_PERMISSIONS
            or "dexclassloader" in risky_code
            or "payload.apk" in risky_code
        ):
            issues.append("suspicious_overclaim")
        if classification in {"mobilebanking", "banking", "finance"} and suspicious & _BANKER_LIKE_INDICATORS:
            issues.append("suspicious_overclaim")

    if not issues:
        issues.append("low_confidence_unknown")

    deduped: list[IssueCategory] = []
    for item in issues:
        if item not in deduped:
            deduped.append(item)
    return deduped


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
