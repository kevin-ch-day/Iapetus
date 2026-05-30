"""Android-family concept models for the seed kernel."""

from typing import Literal

from pydantic import BaseModel, Field


ArtifactCategory = Literal[
    "android",
    "android_app",
    "apk",
    "android_manifest",
    "permission_model",
    "evidence_type",
    "artifact_type",
    "unknown",
]


class KnowledgeConcept(BaseModel):
    concept_id: str = Field(min_length=1)
    display_name: str = Field(min_length=1)
    definition: str = Field(min_length=1)
    key_fields: list[str] = Field(default_factory=list)
    static_evidence: list[str] = Field(default_factory=list)
    dynamic_evidence: list[str] = Field(default_factory=list)
    relevant_tools: list[str] = Field(default_factory=list)
    iapetus_role: str = Field(default="seed")
    notes: str = ""


class ArtifactTypeKnowledge(KnowledgeConcept):
    category: ArtifactCategory = "artifact_type"


class EvidenceTypeKnowledge(KnowledgeConcept):
    category: ArtifactCategory = "evidence_type"


android_app_bundle_concept = ArtifactTypeKnowledge(
    concept_id="aab",
    display_name="Android App Bundle",
    definition=(
        "A signed Android app-bundle artifact (`.aab`) published to app stores. "
        "It carries app modules and resources; stores are split into APKs per device profile."
    ),
    key_fields=[
        "bundle format extension and module structure",
        "base module and feature module split",
        "manifest declarations per module",
        "asset pack boundaries and delivery mode",
        "store-side APK generation and signing pipeline",
    ],
    static_evidence=[
        "module manifests and config files",
        "res/ and assets directories in module contexts",
        "native library splits per ABI",
    ],
    dynamic_evidence=[
        "device-specific APK generation behavior",
        "target-device dynamic delivery outcomes",
    ],
    relevant_tools=[
        "bundletool",
        "Google Play packaging pipeline",
    ],
    iapetus_role="seed concept for publish-time artifact understanding and future bundle-to-apk reasoning.",
    notes=(
        "Seed concept: AAB files are publishing artifacts; Android devices run APK outputs, "
        "so direct on-device execution is typically not from the `.aab` file itself."
    ),
)


android_concept = ArtifactTypeKnowledge(
    concept_id="android",
    display_name="Android",
    definition=(
        "Mobile operating system for phones, tablets, and other device types, built on a Linux "
        "foundation with per-app isolation."
    ),
    key_fields=[
        "Linux kernel and system service foundation",
        "application sandboxing by UID / process isolation",
        "permission model and package install policy",
        "package manager behavior and package visibility",
        "runtime permission model introduction from Android 6.0",
        "APK/AAB app format support",
    ],
    static_evidence=[
        "system property files",
        "build metadata",
        "AndroidManifest.xml declarations",
    ],
    dynamic_evidence=[
        "app process behavior",
        "runtime service state",
        "permission grant events",
    ],
    relevant_tools=[
        "ADB",
        "apktools",
        "aapt",
        "androguard",
    ],
    iapetus_role="platform identity and app runtime context",
    notes="Seed-level concept for operator orientation on app-platform fundamentals.",
)


android_app_concept = EvidenceTypeKnowledge(
    concept_id="android_app",
    display_name="Android app package",
    definition=(
        "An installed Android package object with declared identity, components, permissions, and "
        "runtime behavior context."
    ),
    key_fields=[
        "package_name",
        "version_code",
        "version_name",
        "uid sandbox and signing identity",
        "shared user ID (when declared)",
        "declared_permissions",
        "components",
        "package manager metadata and installer source",
        "launch/activation path",
        "runtime behavior traces",
    ],
    static_evidence=[
        "AndroidManifest.xml",
        "package metadata from app manifests",
        "declared permissions and permission trees",
        "component declarations",
    ],
    dynamic_evidence=[
        "foreground/background lifecycle transitions",
        "permission grant callbacks and denials",
        "network activity",
        "component invocation patterns",
    ],
    relevant_tools=[
        "adb shell pm",
        "adb shell dumpsys package",
        "strace",
    ],
    iapetus_role="primary modeling object for app-level learning.",
    notes="Contains installability, trust, behavior, and permission context.",
)


apk_concept = ArtifactTypeKnowledge(
    concept_id="apk",
    display_name="Android app artifact",
    definition=(
        "Android Package Kit (APK) is a signed distributable app artifact packaged as a ZIP-like "
        "archive used for install and static analysis."
    ),
    key_fields=[
        "AndroidManifest.xml",
        "classes.dex",
        "classes2.dex",
        "classes3.dex",
        "resources.arsc",
        "res/",
        "assets/",
        "lib/",
        "META-INF/",
        "signature",
        "network-security-config",
    ],
    static_evidence=[
        "APK ZIP entries",
        "manifest attributes",
        "signature block",
        "resource tables",
    ],
    dynamic_evidence=[
        "install-time behavior traces (future)",
    ],
    relevant_tools=[
        "apktool",
        "zipinfo",
        "jarsigner",
        "keytool",
    ],
    iapetus_role="seed input artifact for static analysis and permission extraction.",
    notes="Also used for malware family and label-aware fixture development.",
)


android_manifest_concept = ArtifactTypeKnowledge(
    concept_id="android_manifest",
    display_name="AndroidManifest schema",
    definition=(
        "Manifest schema declaring package identity and app-level constraints: components, permissions, "
        "compatibility boundaries, and metadata used by the Android package system."
    ),
    key_fields=[
        "package",
        "android:versionCode / android:versionName",
        "android:uses-permission and uses-permission-sdk-23",
        "uses-sdk (minSdkVersion / targetSdkVersion)",
        "application components (activity, service, receiver, provider)",
        "application flags and metadata",
        "network-security-config",
        "permission declaration and visibility constraints",
    ],
    static_evidence=[
        "permission declarations",
        "component declarations",
        "SDK compatibility declarations",
    ],
    dynamic_evidence=[
        "runtime permission behavior (requested by user)",
    ],
    relevant_tools=[
        "aapt",
        "apktool",
        "xml parsers",
    ],
    iapetus_role="core static schema for permission and component extraction.",
    notes="Source for app capability and risk-surface understanding.",
)


permission_model_concept = EvidenceTypeKnowledge(
    concept_id="permission_model",
    display_name="Android permission model",
    definition=(
        "Android permission model with install-time and runtime grant types, plus signature and "
        "custom permission controls for component and resource access."
    ),
    key_fields=[
        "requested_permissions from manifest",
        "normal permissions (auto-granted)",
        "dangerous permissions (runtime prompts)",
        "signature permissions",
        "special permissions",
        "custom permissions",
        "uses-permission-sdk-23 behavior for API 23+ apps",
    ],
    static_evidence=[
        "manifest permission tags",
        "permission groups",
        "protection levels",
    ],
    dynamic_evidence=[
        "runtime permission grant callbacks",
        "user-facing permission prompts",
    ],
    relevant_tools=[
        "adb shell pm",
        "manifest parsers",
        "permission mapping tables",
    ],
    iapetus_role="priority evidence source for malware-vs-normal classification.",
    notes="Future integration point for Permission Intel role.",
)


android_runtime_concept = ArtifactTypeKnowledge(
    concept_id="android_runtime",
    display_name="Android runtime",
    definition=(
        "Per-app runtime execution context that isolates app components in process and prepares code "
        "for execution through a managed runtime (ART), following Android lifecycle rules."
    ),
    key_fields=[
        "runtime = ART (historically Dalvik)",
        "per-process execution model",
        "activity/service lifecycle events",
        "component invocation through intents",
        "permissions applied at runtime",
    ],
    static_evidence=[
        "Dex/compiled bytecode entry points",
        "manifest intent filter structure",
    ],
    dynamic_evidence=[
        "foreground/background transitions",
        "intent dispatch and service starts",
        "runtime API calls tied to behavior",
    ],
    relevant_tools=[
        "adb shell am",
        "Android emulator",
        "runtime event logs",
    ],
    iapetus_role="helps interpret behavior and lifecycle-aware traces.",
    notes="Seed-level runtime framing for future dynamic analysis modeling.",
)


apk_signing_concept = EvidenceTypeKnowledge(
    concept_id="apk_signing",
    display_name="APK signing and trust",
    definition=(
        "Signature chain and signing metadata that lets Android verify package integrity and authentic "
        "publisher identity before install, updates, or trust-based access."
    ),
    key_fields=[
        "JAR/v1 signature scheme",
        "APK Signing Scheme v2+/v3+ block structure",
        "signature block and certificates",
        "signing identity and rotation context",
    ],
    static_evidence=[
        "META-INF/CERT.RSA, CERT.SF, MANIFEST.MF",
        "APK Signature Scheme v2+ blocks",
    ],
    dynamic_evidence=[
        "install/update rejection on signature mismatch",
        "runtime trust checks for updates and privileged components",
    ],
    relevant_tools=[
        "jarsigner",
        "apksigner",
        "keytool",
    ],
    iapetus_role="foundation evidence for authenticity and tamper checks.",
    notes=(
        "From Android 7.0 onward, v2+ signature checks validate the full APK body and improve "
        "tamper detection."
    ),
)


android_components_concept = ArtifactTypeKnowledge(
    concept_id="android_components",
    display_name="Android component model",
    definition=(
        "Android app behavior is exposed through components declared in the manifest, with the system "
        "starting and binding components through intents and lifecycle boundaries."
    ),
    key_fields=[
        "Activity entry points and launch modes",
        "Service background execution and foreground status",
        "BroadcastReceiver event/message entry points",
        "ContentProvider URI-based access and permissions",
        "Intent filters and exported component visibility",
    ],
    static_evidence=[
        "AndroidManifest.xml component declarations",
        "component permissions and exported attributes",
        "intent-filter nodes",
    ],
    dynamic_evidence=[
        "component lifecycle callbacks",
        "intent dispatch traces",
        "receiver trigger cadence",
    ],
    relevant_tools=[
        "adb shell dumpsys package",
        "adb shell am",
        "manifest parser",
    ],
    iapetus_role="maps static declarations to expected runtime behavior groups.",
    notes="Seed evidence model for lifecycle-aware feature extraction.",
)
