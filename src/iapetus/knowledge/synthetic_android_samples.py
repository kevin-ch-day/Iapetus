"""Seed-only synthetic Android evidence used for learning and teaching.

This module intentionally keeps all data local and deterministic, so operator workflows can
exercise concept understanding before any real upstream integration exists.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FakePermission:
    name: str
    protection_level: str
    rationale: str
    requested_from_manifest: bool = True


@dataclass(frozen=True)
class FakeComponent:
    component_type: str
    name: str
    exported: bool
    intent_filters: list[str]


@dataclass(frozen=True)
class FakeAndroidArtifact:
    entity_id: str
    package_name: str
    platform: str
    version_name: str
    version_code: int
    min_sdk: int
    target_sdk: int
    signing_identity: str
    sha256: str
    rendered_label: str
    permissions: list[FakePermission]
    components: list[FakeComponent]
    native_libs: list[str]
    assets: list[str]
    static_features: list[str]
    dynamic_features: list[str]
    target_label: str
    provenance: str
    av_tokens: list[str]


FAKE_ANDROID_APPS: tuple[FakeAndroidArtifact, ...] = (
    FakeAndroidArtifact(
        entity_id="android-app:com.iapetus.seed.bankingwallet",
        package_name="com.iapetus.seed.bankingwallet",
        platform="AndroidOS",
        version_name="1.4.2",
        version_code=1420,
        min_sdk=21,
        target_sdk=34,
        signing_identity="CN=Iapetus Seed CA, O=Iapetus Labs, C=US",
        sha256="ab12c9f4a6e3d1f8a1e8f2d4c3b0a91c8d7e6f5a4b3c2d1e0f9a8b7c6d5e4f3a2",
        rendered_label="AndroidOS:Trojan.Anubis-t:[Banker]",
        permissions=[
            FakePermission("android.permission.INTERNET", "normal", "Network traffic to command channel"),
            FakePermission("android.permission.ACCESS_NETWORK_STATE", "normal", "Network-state access for recon"),
            FakePermission("android.permission.READ_SMS", "dangerous", "SMS read for banking data abuse"),
            FakePermission("android.permission.REQUEST_INSTALL_PACKAGES", "signature", "Silent install privilege check"),
        ],
        components=[
            FakeComponent(
                "activity",
                "com.iapetus.seed.bankingwallet.MainActivity",
                True,
                ["android.intent.action.MAIN", "android.intent.category.LAUNCHER"],
            ),
            FakeComponent("service", "com.iapetus.seed.bankingwallet.SyncService", False, []),
            FakeComponent("receiver", "com.iapetus.seed.bankingwallet.BootReceiver", True, ["android.intent.action.BOOT_COMPLETED"]),
        ],
        native_libs=["libwallet.so"],
        assets=["configs/rules.json", "assets/model.json"],
        static_features=["high-risk permission set", "exported receiver", "networked background sync"],
        dynamic_features=["boot receiver fired", "foreground intent dispatch", "periodic background polling"],
        target_label="malware",
        provenance="seed_fixture.v1",
        av_tokens=["family=Trojan", "subtype=Banker", "variant=t", "permission_suspiciousness=high"],
    ),
    FakeAndroidArtifact(
        entity_id="android-app:com.iapetus.seed.signalclone",
        package_name="com.iapetus.seed.signalclone",
        platform="AndroidOS",
        version_name="3.2.0",
        version_code=3200,
        min_sdk=19,
        target_sdk=33,
        signing_identity="CN=Iapetus Seed CA, O=Iapetus Labs, C=US",
        sha256="22bbf3c4d5e6f708192a1b2c3d4e5f60718293a4b5c6d7e8f90123456789abcdef",
        rendered_label="AndroidOS:Signal-7000000:[Messaging]",
        permissions=[
            FakePermission("android.permission.INTERNET", "normal", "Contact app backend"),
            FakePermission("android.permission.RECORD_AUDIO", "dangerous", "VoIP call feature"),
            FakePermission("android.permission.READ_CONTACTS", "dangerous", "Contact discovery"),
        ],
        components=[
            FakeComponent(
                "activity",
                "com.iapetus.seed.signalclone.ChatActivity",
                True,
                ["android.intent.action.MAIN", "android.intent.category.LAUNCHER"],
            ),
            FakeComponent("service", "com.iapetus.seed.signalclone.RegistrationService", False, ["io.getstream.action.REGISTER"]),
            FakeComponent("receiver", "com.iapetus.seed.signalclone.MessageReceiver", False, ["android.intent.action.RECEIVE"]),
        ],
        native_libs=["libcrypto.so", "libwebrtc.so"],
        assets=["ringtones/", "themes/default.theme"],
        static_features=["normal permission set", "foreground service for call", "provider-based chat sync"],
        dynamic_features=["message send telemetry", "lifecycle service starts", "media permission checks"],
        target_label="normal_app",
        provenance="seed_fixture.v1",
        av_tokens=["family=Communication", "subtype=Messaging", "android:targetSdkVersion=33"],
    ),
    FakeAndroidArtifact(
        entity_id="android-app:com.iapetus.seed.tiktoker",
        package_name="com.iapetus.seed.tiktoker",
        platform="AndroidOS",
        version_name="2.1.9",
        version_code=209,
        min_sdk=24,
        target_sdk=34,
        signing_identity="CN=Iapetus Seed CA, O=Iapetus Labs, C=US",
        sha256="c1d2e3f4a5b6c7d8091a2b3c4d5e6f708192a0b1c2d3e4f50617283940506070",
        rendered_label="AndroidOS:TikTok-390000000:[ShortVideo]",
        permissions=[
            FakePermission("android.permission.INTERNET", "normal", "Media upload/download"),
            FakePermission("android.permission.CAMERA", "dangerous", "Photo/video capture"),
            FakePermission("android.permission.RECORD_AUDIO", "dangerous", "Video recording audio"),
            FakePermission("android.permission.ACCESS_FINE_LOCATION", "dangerous", "Location-based feed"),
        ],
        components=[
            FakeComponent(
                "activity",
                "com.iapetus.seed.tiktoker.HomeActivity",
                True,
                ["android.intent.action.MAIN", "android.intent.category.LAUNCHER"],
            ),
            FakeComponent("service", "com.iapetus.seed.tiktoker.UploadService", False, ["upload.video"]),
            FakeComponent("provider", "com.iapetus.seed.tiktoker.ContentProvider", False, []),
        ],
        native_libs=["libvideo.so", "libopencv.so"],
        assets=["onboarding.json", "icons/"],
        static_features=["content export features", "runtime camera + audio use", "upload pipeline"],
        dynamic_features=["stream session traces", "foreground service duration", "network retry behavior"],
        target_label="normal_app",
        provenance="seed_fixture.v1",
        av_tokens=["family=Media", "subtype=ShortVideo", "abi=arm64-v8a"],
    ),
)


PERMISSION_LEVEL_REFERENCE = (
    FakePermission("android.permission.INTERNET", "normal", "Auto-granted, no user confirmation"),
    FakePermission("android.permission.ACCESS_NETWORK_STATE", "normal", "Auto-granted network visibility"),
    FakePermission("android.permission.CAMERA", "dangerous", "Runtime prompt, user-visible"),
    FakePermission("android.permission.RECORD_AUDIO", "dangerous", "Runtime prompt, sensitive input"),
    FakePermission("android.permission.READ_SMS", "dangerous", "Runtime prompt, sensitive telecom data"),
    FakePermission("android.permission.REQUEST_INSTALL_PACKAGES", "signature", "Auto-granted only to trusted signer"),
)


SYNTHETIC_DATASET_ROWS = tuple(
    {
        "entity_id": app.entity_id,
        "entity_kind": "android_app",
        "platform": app.platform,
        "package_name": app.package_name,
        "sha256": app.sha256,
        "rendered_label": app.rendered_label,
        "permission_tokens": [permission.name for permission in app.permissions],
        "av_tokens": app.av_tokens,
        "static_features": app.static_features,
        "dynamic_features": app.dynamic_features,
        "target_label": app.target_label,
        "provenance": app.provenance,
    }
    for app in FAKE_ANDROID_APPS
)


DATASET_TOPICS = {
    "apps": "android_apps",
    "permissions": "permission_levels",
    "dataset_rows": "dataset_rows",
    "artifact-types": "artifact_types",
    "artifact_types": "artifact_types",
}


ARTIFACT_TYPE_REFERENCE = (
    {
        "extension": ".apk",
        "artifact_type": "Android APK",
        "notes": "Installable Android application package; signed ZIP-like archive.",
        "primary_evidence": [
            "AndroidManifest.xml",
            "classes.dex",
            "resources.arsc / res/",
            "assets/",
            "lib/",
            "META-INF/",
        ],
        "analysis_notes": [
            "Parse manifest for package identity, permissions, components.",
            "Extract static features from manifest and resource metadata.",
        ],
    },
    {
        "extension": ".aab",
        "artifact_type": "Android AAB",
        "notes": "Store-side publish artifact; device gets generated APKs from modules.",
        "primary_evidence": ["module-level manifests", "base and feature module directories", "asset packs"],
        "analysis_notes": [
            "Treat as metadata and bundle-source; APK generation is external in seed.",
            "Useful for pre-installability checks and module-level analysis planning.",
        ],
    },
    {
        "extension": ".dex",
        "artifact_type": "Android DEX",
        "notes": "Dalvik Executable bytecode artifact compiled for Android runtime.",
        "primary_evidence": ["bytecode opcodes", "method signatures", "string tables"],
        "analysis_notes": [
            "Run static decompilation heuristics when bytecode tools are available.",
            "Useful for call-pattern risk scoring.",
        ],
    },
)


def list_fake_topics() -> list[str]:
    return sorted(set(DATASET_TOPICS.values()))


def get_fake_data(topic: str) -> list[FakeAndroidArtifact] | tuple[FakePermission, ...] | tuple[dict, ...]:
    normalized = topic.strip().lower().replace("-", "_")
    if normalized in {"android_apps", "android app", "apps"}:
        return list(FAKE_ANDROID_APPS)
    if normalized in {"permission_levels", "permission", "permissions"}:
        return PERMISSION_LEVEL_REFERENCE
    if normalized in {"dataset_rows", "dataset rows", "rows", "records"}:
        return tuple(SYNTHETIC_DATASET_ROWS)
    if normalized in {"artifact_types", "artifact-types", "artifact type", "artifact-type"}:
        return ARTIFACT_TYPE_REFERENCE
    raise KeyError(f"Unknown synthetic topic '{topic}'")


def fake_data_lines(topic: str) -> list[str]:
    data = get_fake_data(topic)
    if isinstance(data, list):
        lines = [f"FAKE DATASET: {topic}"]
        for app in data:
            lines.append(f"- package: {app.package_name}")
            lines.append(f"  entity_id: {app.entity_id}")
            lines.append(f"  target_label: {app.target_label}")
            lines.append(f"  version_name: {app.version_name}")
            lines.append(f"  sha256: {app.sha256}")
            lines.append(f"  rendered_label: {app.rendered_label}")
            lines.append("  permissions:")
            for permission in app.permissions:
                lines.append(
                    f"    - {permission.name} [{permission.protection_level}] - {permission.rationale}",
                )
            lines.append("  components:")
            for component in app.components:
                lines.append(
                    f"    - {component.component_type}: {component.name} "
                    f"(exported={component.exported}, intents={', '.join(component.intent_filters) or 'none'})",
                )
        return lines

    if isinstance(data, tuple) and data and isinstance(data[0], FakePermission):
        lines = [f"FAKE DATASET: {topic}"]
        for permission in data:
            lines.append(f"- {permission.name}")
            lines.append(f"  protection: {permission.protection_level}")
            lines.append(f"  rationale: {permission.rationale}")
            lines.append(f"  requested_in_manifest: {permission.requested_from_manifest}")
        return lines

    if isinstance(data, tuple) and data and isinstance(data[0], dict) and "extension" in data[0]:
        return fake_artifact_type_reference_lines()

    # dataset rows
    lines = [f"FAKE DATASET: {topic}"]
    for row in data:
        lines.append(f"- entity_id: {row['entity_id']}")
        lines.append(f"  entity_kind: {row['entity_kind']}")
        lines.append(f"  target_label: {row['target_label']}")
        lines.append(f"  platform: {row['platform']}")
        lines.append(f"  rendered_label: {row['rendered_label']}")
        lines.append(f"  permission_tokens: {', '.join(row['permission_tokens'])}")
        lines.append(f"  av_tokens: {', '.join(row['av_tokens'])}")
    return lines


def fake_artifact_type_reference_lines() -> list[str]:
    lines = ["FAKE DATASET: artifact_types"]
    for entry in ARTIFACT_TYPE_REFERENCE:
        lines.append(f"- extension: {entry['extension']}")
        lines.append(f"  artifact_type: {entry['artifact_type']}")
        lines.append(f"  notes: {entry['notes']}")
        lines.append(f"  primary_evidence: {', '.join(entry['primary_evidence'])}")
    return lines


def get_dataset_row_count() -> int:
    return len(SYNTHETIC_DATASET_ROWS)
