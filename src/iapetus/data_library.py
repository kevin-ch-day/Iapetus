from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, Any
from urllib.request import urlopen

from pydantic import BaseModel, Field, ValidationError

from iapetus.labels import MalwareLabel, NormalAppLabel


DATA_DIR = Path("data")
CURATED_DIR = DATA_DIR / "curated"
RAW_DIR = DATA_DIR / "raw"
GENERATED_DIR = DATA_DIR / "generated"
MANIFESTS_DIR = DATA_DIR / "manifests"
REFERENCE_RAW_DIR = RAW_DIR / "reference"

SOURCE_MANIFEST_PATH = MANIFESTS_DIR / "android_reference_sources.json"
PERMISSIONS_SEED_PATH = CURATED_DIR / "android_permissions_seed.json"
STATIC_TOKEN_SEED_PATH = CURATED_DIR / "android_static_tokens_seed.json"
FIXTURE_SEED_PATH = CURATED_DIR / "android_fixture_samples_seed.json"

TrustedLevel = Literal["low", "medium", "high", "unknown"]


class SourceManifest(BaseModel):
    source_id: str = Field(min_length=1)
    source_name: str = Field(min_length=1)
    source_url: str = Field(min_length=1)
    retrieved_at: str = Field(min_length=1)
    local_path: str = Field(min_length=1)
    sha256: str = Field(min_length=1)
    license_or_terms_note: str = Field(min_length=1)
    purpose: str = Field(min_length=1)
    source_kind: str = Field(min_length=1)
    trusted_level: TrustedLevel


class SeedFixtureSample(BaseModel):
    sample_id: str = Field(min_length=1)
    sample_name: str = Field(min_length=1)
    sample_type: str = Field(min_length=1)
    permissions: list[str] = Field(min_length=1)
    labels: dict[str, Any] = Field(default_factory=dict)
    expected_classification: str | None = None
    suspicious_indicators: list[str] = Field(default_factory=list)


def _default_sources() -> list[SourceManifest]:
    now = datetime.now(UTC).isoformat()
    return [
        SourceManifest(
            source_id="android-manifest-permission-docs",
            source_name="Android Manifest.permission reference",
            source_url="https://developer.android.com/reference/android/Manifest.permission",
            retrieved_at=now,
            local_path="raw/reference/android_manifest_permission_docs.html",
            sha256="pending",
            license_or_terms_note="Android docs terms apply; public docs page.",
            purpose="Reference permission strings and protection-level descriptions.",
            source_kind="documentation",
            trusted_level="medium",
        ),
        SourceManifest(
            source_id="android-manifest-overview-docs",
            source_name="Android developer manifest overview",
            source_url="https://developer.android.com/guide/topics/manifest/manifest-intro",
            retrieved_at=now,
            local_path="raw/reference/android_manifest_overview.html",
            sha256="pending",
            license_or_terms_note="Android docs terms apply; public docs page.",
            purpose="Static manifest structure and component semantics.",
            source_kind="documentation",
            trusted_level="medium",
        ),
        SourceManifest(
            source_id="owasp-masvs",
            source_name="OWASP MASVS project",
            source_url="https://github.com/OWASP/owasp-masvs",
            retrieved_at=now,
            local_path="raw/reference/owasp_masvs.html",
            sha256="pending",
            license_or_terms_note="Check upstream project license terms before redistribution.",
            purpose="Baseline Android mobile security control references.",
            source_kind="reference_project",
            trusted_level="high",
        ),
    ]


def _load_json_payload(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Missing seed file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc


def _ensure_manifest_file() -> None:
    if SOURCE_MANIFEST_PATH.exists():
        return
    MANIFESTS_DIR.mkdir(parents=True, exist_ok=True)
    SOURCE_MANIFEST_PATH.write_text(
        json.dumps([m.model_dump(mode="json") for m in _default_sources()], indent=2),
        encoding="utf-8",
    )


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def list_source_manifests() -> list[SourceManifest]:
    _ensure_manifest_file()
    raw = _load_json_payload(SOURCE_MANIFEST_PATH)
    if not isinstance(raw, list):
        raise ValueError(f"Source manifest must be a JSON array: {SOURCE_MANIFEST_PATH}")

    parsed: list[SourceManifest] = []
    for entry in raw:
        try:
            parsed.append(SourceManifest.model_validate(entry))
        except ValidationError as exc:
            raise ValueError(f"Invalid source manifest entry {entry}: {exc}") from exc
    return parsed


def load_permission_seed() -> list[dict]:
    payload = _load_json_payload(PERMISSIONS_SEED_PATH)
    if not isinstance(payload, list):
        raise ValueError(f"Permission seed is not a list: {PERMISSIONS_SEED_PATH}")
    return payload


def load_static_token_seed() -> list[dict]:
    payload = _load_json_payload(STATIC_TOKEN_SEED_PATH)
    if not isinstance(payload, list):
        raise ValueError(f"Static token seed is not a list: {STATIC_TOKEN_SEED_PATH}")
    return payload


def load_fixture_seed() -> list[dict]:
    payload = _load_json_payload(FIXTURE_SEED_PATH)
    if not isinstance(payload, list):
        raise ValueError(f"Fixture seed is not a list: {FIXTURE_SEED_PATH}")
    return payload


def fixture_seed_as_labels() -> tuple[list[MalwareLabel], list[NormalAppLabel]]:
    items = load_fixture_seed()
    malware_labels: list[MalwareLabel] = []
    normal_labels: list[NormalAppLabel] = []
    for raw in items:
        sample = SeedFixtureSample.model_validate(raw)
        labels_payload = sample.labels or {}
        sample_type = str(sample.sample_type).strip().lower()
        if sample_type in {"malware", "malicious"}:
            malware_labels.append(
                MalwareLabel(
                    platform=labels_payload.get("platform", "AndroidOS"),
                    malware_primary=labels_payload["malware_primary"],
                    family=labels_payload["family"],
                    variant=labels_payload["variant"],
                    subtype=labels_payload["subtype"],
                )
            )
            continue
        if sample_type in {"benign", "normal", "normal_app", "normal-app"}:
            normal_labels.append(
                NormalAppLabel(
                    platform=labels_payload.get("platform", "AndroidOS"),
                    app_name=labels_payload["app_name"],
                    build_ref=labels_payload["build_ref"],
                    app_category=labels_payload["app_category"],
                )
            )
            continue
        raise ValueError(f"Unknown sample type in fixture seed: {sample.sample_type}")

    if not malware_labels and not normal_labels:
        raise ValueError("No label rows parsed from fixture seed file.")
    return malware_labels, normal_labels


def seed_summary() -> dict[str, int]:
    return {
        "permission_seed_count": len(load_permission_seed()),
        "static_token_seed_count": len(load_static_token_seed()),
        "fixture_sample_count": len(load_fixture_seed()),
        "source_manifest_count": len(list_source_manifests()),
    }


def build_token_summary() -> dict[str, dict[str, Any]]:
    permissions = load_permission_seed()
    static_tokens = load_static_token_seed()
    fixtures = load_fixture_seed()

    permissions_by_category: dict[str, int] = {}
    permissions_by_risk: dict[str, int] = {}
    for item in permissions:
        category = str(item.get("category", "uncategorized")).strip() or "uncategorized"
        permissions_by_category[category] = permissions_by_category.get(category, 0) + 1
        risk = str(item.get("rough_risk", "unknown")).strip() or "unknown"
        permissions_by_risk[risk] = permissions_by_risk.get(risk, 0) + 1

    static_token_by_type: dict[str, int] = {}
    suspicious_indicator_counts: dict[str, int] = {}
    for item in static_tokens:
        token_type = str(item.get("token_type", "untyped")).strip() or "untyped"
        static_token_by_type[token_type] = static_token_by_type.get(token_type, 0) + 1
        suspicious = item.get("suspicious_when")
        if isinstance(suspicious, str) and suspicious.strip():
            suspicious_indicator_counts[suspicious.strip()] = suspicious_indicator_counts.get(suspicious.strip(), 0) + 1

    fixture_by_kind: dict[str, int] = {}
    fixture_by_expected_classification: dict[str, int] = {}
    for item in fixtures:
        sample_type = str(item.get("sample_type", "")).strip().lower()
        if sample_type in {"malware", "malicious"}:
            kind = "malware"
        elif sample_type in {"benign", "normal", "normal_app", "normal-app"}:
            kind = "normal_app"
        else:
            kind = sample_type or "unknown"
        fixture_by_kind[kind] = fixture_by_kind.get(kind, 0) + 1

        labels = item.get("labels") if isinstance(item.get("labels"), dict) else {}
        expected = (
            str(
                item.get(
                    "expected_classification",
                    labels.get("subtype", labels.get("app_category", "unknown")),
                )
            )
            .strip()
        )
        if not expected:
            expected = "unknown"
        fixture_by_expected_classification[expected] = fixture_by_expected_classification.get(expected, 0) + 1

        for indicator in item.get("suspicious_indicators", []):
            if isinstance(indicator, str) and indicator.strip():
                suspicious_indicator_counts[indicator.strip()] = suspicious_indicator_counts.get(indicator.strip(), 0) + 1

    return {
        "permissions_by_category": permissions_by_category,
        "permissions_by_rough_risk": permissions_by_risk,
        "static_tokens_by_token_type": static_token_by_type,
        "fixture_samples_by_entity_kind": fixture_by_kind,
        "fixture_samples_by_expected_classification": fixture_by_expected_classification,
        "suspicious_indicator_counts": suspicious_indicator_counts,
    }


def build_feature_vocabulary() -> dict[str, list[str] | dict[str, int] | int]:
    permissions = load_permission_seed()
    static_tokens = load_static_token_seed()
    fixtures = load_fixture_seed()

    permission_vocab: set[str] = {str(item.get("permission", "")).strip() for item in permissions if item.get("permission")}
    static_token_vocab: set[str] = {
        str(item.get("token", "")).strip() for item in static_tokens if item.get("token")
    }
    network_vocab: set[str] = set()
    code_vocab: set[str] = set()
    suspicious_vocab: list[str] = []

    for item in permissions:
        suspicious = item.get("suspicious_when")
        if isinstance(suspicious, str) and suspicious.strip():
            suspicious_vocab.append(suspicious.strip())

    for item in static_tokens:
        token = str(item.get("token", "")).strip()
        token_type = str(item.get("token_type", "")).strip().lower()
        if token and ("http://" in token or "https://" in token):
            network_vocab.add(token)
        if token_type in {"code_string", "api_symbol", "code", "method_name", "class_name"}:
            if token:
                code_vocab.add(token)
        suspicious = item.get("suspicious_when")
        if isinstance(suspicious, str) and suspicious.strip():
            suspicious_vocab.append(suspicious.strip())

    for item in fixtures:
        sample_type = str(item.get("sample_type", "")).strip().lower()
        if sample_type in {"malware", "malicious"}:
            classification = item.get("labels", {}).get("subtype")
        else:
            classification = item.get("labels", {}).get("app_category")
        if isinstance(classification, str) and classification.strip():
            code_vocab.add(classification.strip())
        for permission in item.get("permissions", []):
            if isinstance(permission, str) and permission.strip():
                permission_vocab.add(permission.strip())
        for indicator in item.get("suspicious_indicators", []):
            if isinstance(indicator, str) and indicator.strip():
                suspicious_vocab.append(indicator.strip())

    permission_list = sorted(permission_vocab)
    static_token_list = sorted(static_token_vocab)
    network_list = sorted(network_vocab)
    code_list = sorted(code_vocab)
    suspicious_list = sorted(set(suspicious_vocab))
    all_tokens = sorted(set(permission_list + static_token_list + network_list + code_list + suspicious_list))

    return {
        "permissions": permission_list,
        "static_tokens": static_token_list,
        "network_strings": network_list,
        "code_strings": code_list,
        "suspicious_indicators": suspicious_list,
        "all_tokens": all_tokens,
        "counts": {
            "permissions": len(permission_list),
            "static_tokens": len(static_token_list),
            "network_strings": len(network_list),
            "code_strings": len(code_list),
            "suspicious_indicators": len(suspicious_list),
            "all_tokens": len(all_tokens),
        },
    }


def validate_seed_payloads() -> tuple[bool, list[str], dict[str, int]]:
    issues: list[str] = []
    counts = {
        "permission_seed_count": 0,
        "static_token_seed_count": 0,
        "fixture_sample_count": 0,
        "source_manifest_count": 0,
    }
    try:
        permissions = load_permission_seed()
        for index, item in enumerate(permissions):
            missing = [field for field in ("permission", "category", "rough_risk") if field not in item]
            if missing:
                issues.append(f"android_permissions_seed.json item {index}: missing {missing}")
        counts["permission_seed_count"] = len(permissions)
    except Exception as exc:
        issues.append(str(exc))

    try:
        tokens = load_static_token_seed()
        for index, item in enumerate(tokens):
            missing = [field for field in ("token", "token_type", "meaning") if field not in item]
            if missing:
                issues.append(f"android_static_tokens_seed.json item {index}: missing {missing}")
        counts["static_token_seed_count"] = len(tokens)
    except Exception as exc:
        issues.append(str(exc))

    try:
        fixtures = load_fixture_seed()
        for index, item in enumerate(fixtures):
            if not item.get("labels"):
                issues.append(f"android_fixture_samples_seed.json item {index}: missing labels")
            if not item.get("permissions"):
                issues.append(f"android_fixture_samples_seed.json item {index}: missing permissions")
        counts["fixture_sample_count"] = len(fixtures)
    except Exception as exc:
        issues.append(str(exc))

    try:
        manifests = list_source_manifests()
        counts["source_manifest_count"] = len(manifests)
    except Exception as exc:
        issues.append(str(exc))

    return (len(issues) == 0, issues, counts)


def download_reference_sources(limit: int | None = None, dry_run: bool = True) -> list[SourceManifest]:
    manifests = list_source_manifests()
    if dry_run:
        return manifests

    REFERENCE_RAW_DIR.mkdir(parents=True, exist_ok=True)
    updated: list[SourceManifest] = []
    selected = manifests if limit is None else manifests[:limit]
    for source in selected:
        target = DATA_DIR / source.local_path
        with urlopen(source.source_url, timeout=20) as response:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(response.read())
        sha = _sha256_file(target)
        updated.append(
            source.model_copy(
                update={
                    "retrieved_at": datetime.now(UTC).isoformat(),
                    "sha256": sha,
                }
            )
        )

    # keep all non-downloaded entries as-is
    manifest_by_id = {item.source_id: item for item in manifests}
    for source in updated:
        manifest_by_id[source.source_id] = source
    merged = list(manifest_by_id.values())
    SOURCE_MANIFEST_PATH.write_text(json.dumps([m.model_dump(mode="json") for m in merged], indent=2), encoding="utf-8")
    return merged
