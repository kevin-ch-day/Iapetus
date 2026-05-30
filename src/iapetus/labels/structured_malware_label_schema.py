from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MalwareLabel:
    platform: str
    malware_primary: str
    family: str
    variant: str
    subtype: str


@dataclass(frozen=True)
class NormalAppLabel:
    platform: str
    app_name: str
    build_ref: str
    app_category: str
