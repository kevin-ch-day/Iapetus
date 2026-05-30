from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from iapetus.data_library import (
    GENERATED_DIR,
    KNOWLEDGE_SUMMARY_PATH,
    TOKEN_VOCABULARY_PATH,
    FIXTURE_COOCCURRENCE_PATH,
    build_feature_vocabulary,
    build_token_summary,
    load_fixture_seed,
    load_permission_seed,
    load_static_token_seed,
    seed_summary,
)
from iapetus.learning.training_corpus import build_training_corpus
from iapetus.fixture_analysis import (
    compare_fixture_records,
    explain_fixture_detail,
    extract_fixture_token_groups,
    fixture_record,
    fixture_slug_from_name,
    resolve_fixture,
)

TokenKind = Literal["permission", "static", "unknown"]


def fixture_slug(sample_name: str) -> str:
    return fixture_slug_from_name(sample_name)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _permission_index() -> dict[str, dict[str, Any]]:
    return {str(item["permission"]): item for item in load_permission_seed() if item.get("permission")}


def _static_token_index() -> dict[str, dict[str, Any]]:
    return {str(item["token"]): item for item in load_static_token_seed() if item.get("token")}


def classify_token_kind(token: str) -> TokenKind:
    normalized = token.strip()
    if normalized.startswith("android.permission."):
        return "permission"
    if normalized in _static_token_index():
        return "static"
    if normalized in _permission_index():
        return "permission"
    return "unknown"


def _fixture_keys_for_token(token: str) -> list[str]:
    keys: list[str] = []
    normalized = token.strip()
    for item in load_fixture_seed():
        groups = extract_fixture_token_groups(item)
        for group_name, values in groups.items():
            if group_name == "fixture_slug":
                continue
            if normalized in values:
                slug = groups["fixture_slug"]
                if slug not in keys:
                    keys.append(slug)
    return sorted(keys)


def build_knowledge_summary() -> dict[str, Any]:
    counts = seed_summary()
    token_summary = build_token_summary()
    vocabulary = build_feature_vocabulary()
    fixtures = [fixture_record(item) for item in load_fixture_seed()]
    permission_index = _permission_index()

    high_risk_permissions = sorted(
        permission
        for permission, meta in permission_index.items()
        if str(meta.get("rough_risk", "")).strip().lower() in {"high", "critical"}
    )
    malware_permissions: set[str] = set()
    benign_permissions: set[str] = set()
    for fixture in fixtures:
        target = malware_permissions if fixture["entity_kind"] == "malware" else benign_permissions
        target.update(fixture["permissions"])

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "trainer": "concept_trainer",
        "purpose": "Summarize curated Android seed knowledge for operator explanations.",
        "seed_counts": counts,
        "fixture_count": len(fixtures),
        "fixture_keys": [fixture["fixture_slug"] for fixture in fixtures],
        "token_summary": token_summary,
        "vocabulary_counts": vocabulary.get("counts", {}),
        "high_risk_permissions": high_risk_permissions,
        "permissions_unique_to_malware_fixtures": sorted(malware_permissions - benign_permissions),
        "permissions_unique_to_benign_fixtures": sorted(benign_permissions - malware_permissions),
        "permissions_shared_across_kinds": sorted(malware_permissions & benign_permissions),
        "related_knowledge_concepts": [
            "android",
            "apk",
            "android_manifest",
            "permission_model",
            "android_app",
            "android_runtime",
        ],
        "training_corpus_available": True,
        "notes": [
            "Generated from curated JSON seeds only; no APKs or live connectors.",
            "Use learn explain-fixture and android tokens for drill-down detail.",
            "Run learn absorb to refresh training_corpus.json (quality-gated examples).",
        ],
    }


def build_token_vocabulary_document() -> dict[str, Any]:
    permission_index = _permission_index()
    static_index = _static_token_index()

    fixture_usage: dict[str, list[str]] = {}
    for raw in load_fixture_seed():
        record = fixture_record(raw)
        key = record["fixture_slug"]
        groups = extract_fixture_token_groups(raw)
        for group_name in (
            "permissions",
            "components",
            "intent_filters",
            "manifest_flags",
            "network_strings",
            "code_strings",
            "suspicious_indicators",
        ):
            for value in groups[group_name]:
                fixture_usage.setdefault(value, [])
                if key not in fixture_usage[value]:
                    fixture_usage[value].append(key)

    permission_entries: list[dict[str, Any]] = []
    for permission in sorted(permission_index):
        meta = permission_index[permission]
        permission_entries.append(
            {
                "token": permission,
                "kind": "permission",
                "category": meta.get("category"),
                "rough_risk": meta.get("rough_risk"),
                "common_context": meta.get("common_context"),
                "notes": meta.get("notes"),
                "fixture_keys": sorted(fixture_usage.get(permission, [])),
            }
        )

    static_entries: list[dict[str, Any]] = []
    for token in sorted(static_index):
        meta = static_index[token]
        static_entries.append(
            {
                "token": token,
                "kind": "static",
                "token_type": meta.get("token_type"),
                "meaning": meta.get("meaning"),
                "android_relevance": meta.get("android_relevance"),
                "suspicious_when": meta.get("suspicious_when"),
                "fixture_keys": sorted(fixture_usage.get(token, [])),
            }
        )

    all_tokens = sorted({entry["token"] for entry in permission_entries} | {entry["token"] for entry in static_entries})

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "trainer": "concept_trainer",
        "permissions": permission_entries,
        "static_tokens": static_entries,
        "all_tokens": all_tokens,
        "counts": {
            "permissions": len(permission_entries),
            "static_tokens": len(static_entries),
            "all_tokens": len(all_tokens),
        },
    }


def build_fixture_cooccurrence() -> dict[str, Any]:
    fixtures = [fixture_record(item) for item in load_fixture_seed()]
    pair_counts: dict[str, dict[str, Any]] = {}

    for fixture in fixtures:
        permissions = sorted(fixture["permissions"])
        for index, left in enumerate(permissions):
            for right in permissions[index + 1 :]:
                pair_key = f"{left}|{right}"
                bucket = pair_counts.setdefault(
                    pair_key,
                    {"permissions": [left, right], "fixture_count": 0, "fixture_keys": []},
                )
                bucket["fixture_count"] += 1
                slug = fixture["fixture_slug"]
                if slug not in bucket["fixture_keys"]:
                    bucket["fixture_keys"].append(slug)

    permission_fixture_map: dict[str, list[str]] = {}
    for fixture in fixtures:
        for permission in fixture["permissions"]:
            permission_fixture_map.setdefault(permission, [])
            slug = fixture["fixture_slug"]
            if slug not in permission_fixture_map[permission]:
                permission_fixture_map[permission].append(slug)

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "trainer": "concept_trainer",
        "fixtures": fixtures,
        "permission_fixture_map": {key: sorted(values) for key, values in sorted(permission_fixture_map.items())},
        "permission_pairs": [pair_counts[key] for key in sorted(pair_counts)],
    }


def absorb_curated_seed(generated_dir: Path | None = None) -> dict[str, Path]:
    root = generated_dir or GENERATED_DIR
    paths = {
        "knowledge_summary": root / "knowledge_summary.json",
        "token_vocabulary": root / "token_vocabulary.json",
        "fixture_cooccurrence": root / "fixture_cooccurrence.json",
        "training_corpus": root / "training_corpus.json",
    }
    _write_json(paths["knowledge_summary"], build_knowledge_summary())
    _write_json(paths["token_vocabulary"], build_token_vocabulary_document())
    _write_json(paths["fixture_cooccurrence"], build_fixture_cooccurrence())
    _write_json(paths["training_corpus"], build_training_corpus())
    return paths


def explain_token(token: str) -> dict[str, Any]:
    normalized = token.strip()
    kind = classify_token_kind(normalized)
    permission_index = _permission_index()
    static_index = _static_token_index()
    fixture_keys = _fixture_keys_for_token(normalized)

    if kind == "permission" and normalized in permission_index:
        meta = permission_index[normalized]
        return {
            "token": normalized,
            "kind": "permission",
            "found": True,
            "category": meta.get("category"),
            "rough_risk": meta.get("rough_risk"),
            "common_context": meta.get("common_context"),
            "notes": meta.get("notes"),
            "fixture_keys": fixture_keys,
            "explanation": (
                f"{normalized} is a {meta.get('rough_risk', 'unknown')}-risk {meta.get('category', 'uncategorized')} "
                f"permission. {meta.get('notes', '').strip()}"
            ).strip(),
        }

    if normalized in static_index:
        meta = static_index[normalized]
        return {
            "token": normalized,
            "kind": "static",
            "found": True,
            "token_type": meta.get("token_type"),
            "meaning": meta.get("meaning"),
            "android_relevance": meta.get("android_relevance"),
            "suspicious_when": meta.get("suspicious_when"),
            "fixture_keys": fixture_keys,
            "explanation": (
                f"{normalized} ({meta.get('token_type', 'token')}) — {meta.get('meaning', '').strip()} "
                f"Suspicious when: {meta.get('suspicious_when', 'n/a')}"
            ).strip(),
        }

    if fixture_keys:
        return {
            "token": normalized,
            "kind": "fixture_static",
            "found": True,
            "fixture_keys": fixture_keys,
            "explanation": f"{normalized} appears on curated fixture(s): {', '.join(fixture_keys)}.",
        }

    return {
        "token": normalized,
        "kind": kind,
        "found": False,
        "explanation": f"Token '{normalized}' is not present in curated permission or static token seeds.",
        "fixture_keys": [],
    }


def explain_fixture(fixture_key: str) -> dict[str, Any]:
    return explain_fixture_detail(fixture_key)


def compare_fixtures(left_key: str, right_key: str) -> dict[str, Any]:
    return compare_fixture_records(left_key, right_key)
