"""APK-focused knowledge helpers for the seed knowledge layer."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ApkAnatomyPart:
    """Describes a key APK component expected in seed knowledge."""

    name: str
    notes: str


APK_ANATOMY_PARTS: tuple[ApkAnatomyPart, ...] = (
    ApkAnatomyPart(name="AndroidManifest.xml", notes="Manifest identity, permissions, components, SDK and feature declarations"),
    ApkAnatomyPart(name="classes.dex", notes="Primary DEX bytecode"),
    ApkAnatomyPart(name="classes2.dex", notes="Additional DEX in multi-DEX apps (if present)"),
    ApkAnatomyPart(name="resources.arsc / res/", notes="Compiled resources and resource IDs table"),
    ApkAnatomyPart(name="assets/", notes="Raw packaged assets"),
    ApkAnatomyPart(name="lib/", notes="Native libraries (ABI splits such as arm64-v8a)"),
    ApkAnatomyPart(name="META-INF/", notes="Signature files and signing metadata"),
    ApkAnatomyPart(name="network security config if present", notes="network-security-config references"),
    ApkAnatomyPart(name="MANIFEST.MF", notes="Package hash metadata and signed content listing"),
)


def apk_anatomy_lines() -> list[str]:
    return [part.name for part in APK_ANATOMY_PARTS]
