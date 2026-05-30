"""Reference source manifests and optional download."""
from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from urllib.request import urlopen

from pydantic import ValidationError

from iapetus import project_filesystem_paths as paths
from iapetus.data.seed_json_reader import load_json_payload
from iapetus.data.seed_data_models import SourceManifest


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


def _ensure_manifest_file() -> None:
    if paths.SOURCE_MANIFEST_PATH.exists():
        return
    paths.MANIFESTS_DIR.mkdir(parents=True, exist_ok=True)
    paths.SOURCE_MANIFEST_PATH.write_text(
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
    raw = load_json_payload(paths.SOURCE_MANIFEST_PATH)
    if not isinstance(raw, list):
        raise ValueError(f"Source manifest must be a JSON array: {paths.SOURCE_MANIFEST_PATH}")

    parsed: list[SourceManifest] = []
    for entry in raw:
        try:
            parsed.append(SourceManifest.model_validate(entry))
        except ValidationError as exc:
            raise ValueError(f"Invalid source manifest entry {entry}: {exc}") from exc
    return parsed


def download_reference_sources(limit: int | None = None, dry_run: bool = True) -> list[SourceManifest]:
    manifests = list_source_manifests()
    if dry_run:
        return manifests

    paths.REFERENCE_RAW_DIR.mkdir(parents=True, exist_ok=True)
    updated: list[SourceManifest] = []
    selected = manifests if limit is None else manifests[:limit]
    for source in selected:
        target = paths.DATA_DIR / source.local_path
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

    manifest_by_id = {item.source_id: item for item in manifests}
    for source in updated:
        manifest_by_id[source.source_id] = source
    merged = list(manifest_by_id.values())
    paths.SOURCE_MANIFEST_PATH.write_text(
        json.dumps([m.model_dump(mode="json") for m in merged], indent=2),
        encoding="utf-8",
    )
    return merged
