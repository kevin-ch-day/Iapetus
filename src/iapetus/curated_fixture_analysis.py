from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from iapetus.curated_seed_library_exports import (
    GENERATED_DIR,
    KNOWLEDGE_SUMMARY_PATH,
    TOKEN_VOCABULARY_PATH,
    FIXTURE_COOCCURRENCE_PATH,
    TRAINING_CORPUS_PATH,
    SeedFixtureSample,
    load_fixture_seed,
    load_permission_seed,
)
from iapetus.labels import MalwareLabel, NormalAppLabel
from iapetus.labels.malware_label_text_renderer import render_malware_label, render_normal_app_label

_SLUG_RE = re.compile(r"[^a-z0-9]+")

_TOKEN_GROUP_KEYS = (
    "permissions",
    "components",
    "intent_filters",
    "manifest_flags",
    "network_strings",
    "code_strings",
    "suspicious_indicators",
    "label_tokens",
)


def fixture_slug_from_name(sample_name: str) -> str:
    return _SLUG_RE.sub("_", sample_name.strip().lower()).strip("_")


def resolve_fixture_slug(sample: SeedFixtureSample) -> str:
    if sample.fixture_slug and sample.fixture_slug.strip():
        return sample.fixture_slug.strip().lower().replace("-", "_")
    return fixture_slug_from_name(sample.sample_name)


def resolve_fixture(fixture_key: str) -> dict[str, Any]:
    normalized = fixture_key.strip().lower().replace("-", "_")
    for item in load_fixture_seed():
        sample = SeedFixtureSample.model_validate(item)
        slug = resolve_fixture_slug(sample)
        sample_id = sample.sample_id.strip().lower()
        if slug == normalized or sample_id == normalized or sample_id.replace("-", "_") == normalized:
            return item
    raise KeyError(f"Unknown fixture key '{fixture_key}'")


def _label_tokens_from_labels(labels: dict[str, Any], sample_type: str) -> list[str]:
    tokens: list[str] = []
    st = sample_type.strip().lower()
    if st in {"malware", "malicious"}:
        for key in ("platform", "malware_primary", "family", "variant", "subtype"):
            value = labels.get(key)
            if isinstance(value, str) and value.strip():
                tokens.append(value.strip())
    else:
        for key in ("platform", "app_name", "build_ref", "app_category"):
            value = labels.get(key)
            if isinstance(value, str) and value.strip():
                tokens.append(value.strip())
    return tokens


def render_fixture_label(item: dict[str, Any]) -> str:
    if item.get("rendered_label"):
        return str(item["rendered_label"]).strip()
    sample = SeedFixtureSample.model_validate(item)
    labels = sample.labels or {}
    sample_type = str(sample.sample_type).strip().lower()
    if sample_type in {"malware", "malicious"}:
        return render_malware_label(
            MalwareLabel(
                platform=labels.get("platform", sample.platform or "AndroidOS"),
                malware_primary=labels["malware_primary"],
                family=labels["family"],
                variant=labels.get("variant", sample.variant or "x"),
                subtype=labels["subtype"],
            )
        )
    return render_normal_app_label(
        NormalAppLabel(
            platform=labels.get("platform", sample.platform or "AndroidOS"),
            app_name=labels.get("app_name", sample.display_name or "UnknownApp"),
            build_ref=labels.get("build_ref", sample.build_ref or "0"),
            app_category=labels["app_category"],
        )
    )


def fixture_record(item: dict[str, Any]) -> dict[str, Any]:
    sample = SeedFixtureSample.model_validate(item)
    labels = sample.labels or {}
    sample_type = str(sample.sample_type).strip().lower()
    slug = resolve_fixture_slug(sample)
    if sample_type in {"malware", "malicious"}:
        classification = sample.expected_classification or labels.get("subtype", "unknown")
        entity_kind = "malware"
    else:
        classification = sample.expected_classification or labels.get("app_category", "unknown")
        entity_kind = "normal_app"

    return {
        "fixture_slug": slug,
        "sample_id": sample.sample_id,
        "sample_name": sample.sample_name,
        "sample_type": sample.sample_type,
        "platform": sample.platform or labels.get("platform", "AndroidOS"),
        "package_name": sample.package_name or "",
        "display_name": sample.display_name or "",
        "build_ref": sample.build_ref or labels.get("build_ref"),
        "variant": sample.variant or labels.get("variant"),
        "entity_kind": entity_kind,
        "expected_classification": classification,
        "rendered_label": render_fixture_label(item),
        "permissions": list(sample.permissions),
        "components": list(sample.components),
        "intent_filters": list(sample.intent_filters),
        "manifest_flags": list(sample.manifest_flags),
        "network_strings": list(sample.network_strings),
        "code_strings": list(sample.code_strings),
        "suspicious_indicators": list(sample.suspicious_indicators),
        "notes": sample.notes or "",
        "labels": labels,
    }


def extract_fixture_token_groups(item: dict[str, Any]) -> dict[str, Any]:
    record = fixture_record(item)
    return {
        "fixture_slug": record["fixture_slug"],
        "permissions": record["permissions"],
        "components": record["components"],
        "intent_filters": record["intent_filters"],
        "manifest_flags": record["manifest_flags"],
        "network_strings": record["network_strings"],
        "code_strings": record["code_strings"],
        "suspicious_indicators": record["suspicious_indicators"],
        "label_tokens": _label_tokens_from_labels(record["labels"], record["sample_type"]),
    }


def build_entity_features(
    record: dict[str, Any],
    token_groups: dict[str, Any],
    raw_item: dict[str, Any] | None = None,
) -> dict[str, Any]:
    permissions = set(token_groups["permissions"])
    intents = " ".join(token_groups["intent_filters"]).lower()
    indicators = set(token_groups["suspicious_indicators"])
    manifest_flags = " ".join(token_groups["manifest_flags"]).lower()
    network = " ".join(token_groups["network_strings"]).lower()
    code = " ".join(token_groups["code_strings"]).lower()
    components = " ".join(token_groups["components"]).lower()

    from iapetus.curated_seed_library_exports import load_permission_seed
    from iapetus.validation.fixture_quality_report import validate_fixture_quality

    quality = validate_fixture_quality(raw_item if raw_item is not None else record)
    risk_index = {
        str(item.get("permission", "")): str(item.get("rough_risk", "")).strip().lower()
        for item in load_permission_seed()
        if item.get("permission")
    }
    high_risk_count = sum(
        1
        for permission in permissions
        if risk_index.get(permission, "") in {"high", "critical"}
    )

    return {
        "fixture_slug": record["fixture_slug"],
        "entity_kind": record["entity_kind"],
        "expected_classification": record["expected_classification"],
        "training_eligible": quality.training_eligible,
        "quality_issues": quality.issues,
        "training_blockers": quality.training_blockers,
        "permission_count": len(token_groups["permissions"]),
        "component_count": len(token_groups["components"]),
        "network_string_count": len(token_groups["network_strings"]),
        "code_string_count": len(token_groups["code_strings"]),
        "suspicious_indicator_count": len(token_groups["suspicious_indicators"]),
        "has_sms_permission": any(
            p in permissions
            for p in ("android.permission.READ_SMS", "android.permission.RECEIVE_SMS", "android.permission.SEND_SMS")
        ),
        "has_boot_persistence": (
            "boot_persistence" in indicators
            or "boot_completed" in intents
            or "android.intent.action.boot_completed" in intents
        ),
        "has_overlay_indicator": (
            "overlay_attack" in indicators
            or "overlay" in code
            or "overlayservice" in components
            or "system_alert_window" in code
        ),
        "has_dynamic_loading": (
            "dynamic_code_loading" in indicators
            or "dexclassloader" in code.lower()
        ),
        "has_cleartext_network": (
            "cleartext_c2" in indicators
            or "usescleartexttraffic=true" in manifest_flags
            or "http://" in network
        ),
        "has_accessibility_abuse": (
            "accessibility_abuse" in indicators
            or "accessibilityservice" in code
            or "android.permission.BIND_ACCESSIBILITY_SERVICE" in permissions
        ),
        "has_install_abuse": (
            "package_install_request" in indicators
            or "secondary_payload" in indicators
            or "android.permission.REQUEST_INSTALL_PACKAGES" in permissions
        ),
        "has_surveillance_markers": (
            "surveillance_capability" in indicators
            or "location_tracking" in indicators
            or "stalkerware" in indicators
            or ("camera" in code and "recordaudio" in code)
        ),
        "has_contact_or_sms_exfil": (
            "contact_exfil" in indicators
            or "sms_exfil" in indicators
            or ("readcontacts" in code and "upload" in network)
        ),
        "has_ad_fraud_markers": (
            "click_fraud" in indicators
            or "ad_overlay_abuse" in indicators
            or "injectclick" in code
        ),
        "high_risk_permission_count": high_risk_count,
        "manifest_flag_count": len(token_groups["manifest_flags"]),
        "intent_filter_count": len(token_groups["intent_filters"]),
    }


def build_entity_row(item: dict[str, Any]) -> dict[str, Any]:
    record = fixture_record(item)
    return {
        "sample_id": record["sample_id"],
        "fixture_slug": record["fixture_slug"],
        "entity_kind": record["entity_kind"],
        "package_name": record["package_name"],
        "display_name": record["display_name"],
        "rendered_label": record["rendered_label"],
        "expected_classification": record["expected_classification"],
    }


def build_curated_entity_artifacts() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    entities: list[dict[str, Any]] = []
    token_groups: list[dict[str, Any]] = []
    features: list[dict[str, Any]] = []
    for item in load_fixture_seed():
        record = fixture_record(item)
        groups = extract_fixture_token_groups(item)
        entities.append(build_entity_row(item))
        token_groups.append(groups)
        features.append(build_entity_features(record, groups, raw_item=item))
    return entities, token_groups, features


def generated_summary_paths() -> dict[str, str]:
    mapping = {
        "knowledge_summary": KNOWLEDGE_SUMMARY_PATH,
        "token_vocabulary": TOKEN_VOCABULARY_PATH,
        "fixture_cooccurrence": FIXTURE_COOCCURRENCE_PATH,
        "training_corpus": TRAINING_CORPUS_PATH,
    }
    return {key: str(path) for key, path in mapping.items() if path.is_file()}


def generated_summaries_available() -> bool:
    return bool(generated_summary_paths())


def _permission_index() -> dict[str, dict[str, Any]]:
    return {str(item["permission"]): item for item in load_permission_seed() if item.get("permission")}


def interpret_fixture(record: dict[str, Any]) -> str:
    slug = record["fixture_slug"]
    kind = record["entity_kind"]
    if slug == "malware_banker":
        return (
            "Banker-like fixture: combines SMS read/receive permissions, boot persistence "
            "(BOOT_COMPLETED), overlay/accessibility-style components, and cleartext C2-style "
            "network strings. Co-occurrence suggests credential/SMS interception rather than "
            "benign networking alone."
        )
    if slug == "benign_social_app":
        return (
            "Normal social app fixture: high permission surface (camera, contacts, media APIs) "
            "aligns with social-media functions. Lacks banker-specific SMS interception, overlay "
            "abuse, boot-persistence, and cleartext C2 indicators."
        )
    if slug == "malware_dropper":
        return (
            "Dropper-like fixture: dynamic loading markers (DexClassLoader), install/package "
            "permissions, and secondary-payload network strings suggest staged APK delivery."
        )
    if slug == "malware_rat":
        return (
            "RAT-like fixture: surveillance code strings, command-loop networking, and boot "
            "persistence indicators suggest remote control rather than benign media use."
        )
    if slug == "benign_mobile_banking":
        return (
            "Legitimate mobile banking fixture: TLS-pinned API strings and device-binding "
            "permissions without SMS interception, overlay abuse, or cleartext C2 markers."
        )
    if slug == "malware_spyware":
        return (
            "Spyware fixture: contact/SMS harvest code paths with cleartext upload endpoints "
            "and staged file writes—PII exfil without declared user function."
        )
    if slug == "malware_stalkerware":
        return (
            "Stalkerware fixture: location, microphone, and accessibility surveillance with "
            "hidden-launcher indicators—covert monitoring stack."
        )
    if slug == "malware_adware_fraud":
        return (
            "Adware/fraud fixture: boot-persistent overlay with click-injection code—monetization "
            "abuse rather than declared app utility."
        )
    if kind == "normal_app":
        return (
            f"Normal app fixture ({record['expected_classification']}): static evidence is "
            f"consistent with declared app category; review co-occurrence before escalating."
        )
    return (
        f"Curated {kind} fixture ({record['expected_classification']}): review permissions, "
        "components, and suspicious indicators together."
    )


def interpret_fixture_comparison(left: dict[str, Any], right: dict[str, Any], detail: dict[str, Any]) -> str:
    if left["fixture_slug"] == "benign_social_app" and right["fixture_slug"] == "malware_banker":
        return (
            "Shared INTERNET and ACCESS_NETWORK_STATE are insufficient for a malware call. "
            "Banker-like interpretation comes from co-occurrence of SMS permissions, boot persistence, "
            "overlay/accessibility markers, and C2-style network strings on the right only; the social "
            "fixture shows media/contact surface without SMS interception or persistence indicators."
        )
    return (
        f"Compared {left['fixture_slug']} with {right['fixture_slug']}: "
        f"{len(detail['shared_permissions'])} shared permissions; "
        f"{len(detail['only_left_static_tokens'])} static tokens only on left; "
        f"{len(detail['only_right_static_tokens'])} static tokens only on right."
    )


def _static_token_set(record: dict[str, Any]) -> set[str]:
    tokens: set[str] = set()
    for key in (
        "components",
        "intent_filters",
        "manifest_flags",
        "network_strings",
        "code_strings",
        "suspicious_indicators",
    ):
        for value in record.get(key, []):
            if isinstance(value, str) and value.strip():
                tokens.add(value.strip())
    return tokens


def compare_fixture_records(left_key: str, right_key: str) -> dict[str, Any]:
    left = fixture_record(resolve_fixture(left_key))
    right = fixture_record(resolve_fixture(right_key))
    left_permissions = set(left["permissions"])
    right_permissions = set(right["permissions"])
    left_static = _static_token_set(left)
    right_static = _static_token_set(right)

    detail = {
        "left": {
            "fixture_slug": left["fixture_slug"],
            "entity_kind": left["entity_kind"],
            "expected_classification": left["expected_classification"],
        },
        "right": {
            "fixture_slug": right["fixture_slug"],
            "entity_kind": right["entity_kind"],
            "expected_classification": right["expected_classification"],
        },
        "shared_permissions": sorted(left_permissions & right_permissions),
        "only_left_permissions": sorted(left_permissions - right_permissions),
        "only_right_permissions": sorted(right_permissions - left_permissions),
        "only_left_static_tokens": sorted(left_static - right_static),
        "only_right_static_tokens": sorted(right_static - left_static),
        "shared_static_tokens": sorted(left_static & right_static),
        "only_left_intent_filters": sorted(set(left["intent_filters"]) - set(right["intent_filters"])),
        "only_right_intent_filters": sorted(set(right["intent_filters"]) - set(left["intent_filters"])),
        "only_left_suspicious_indicators": sorted(
            set(left["suspicious_indicators"]) - set(right["suspicious_indicators"])
        ),
        "only_right_suspicious_indicators": sorted(
            set(right["suspicious_indicators"]) - set(left["suspicious_indicators"])
        ),
        "entity_kind_match": left["entity_kind"] == right["entity_kind"],
        "classification_match": left["expected_classification"] == right["expected_classification"],
    }
    detail["interpretation"] = interpret_fixture_comparison(left, right, detail)
    return detail


def explain_fixture_detail(fixture_key: str) -> dict[str, Any]:
    item = resolve_fixture(fixture_key)
    record = fixture_record(item)
    groups = extract_fixture_token_groups(item)
    permission_index = _permission_index()
    permission_details: list[dict[str, Any]] = []
    for permission in record["permissions"]:
        meta = permission_index.get(permission, {})
        permission_details.append(
            {
                "permission": permission,
                "rough_risk": meta.get("rough_risk", "unknown"),
                "category": meta.get("category", "uncategorized"),
                "notes": meta.get("notes", ""),
            }
        )

    return {
        **record,
        "token_groups": groups,
        "permissions_detail": permission_details,
        "interpretation": interpret_fixture(record),
    }
