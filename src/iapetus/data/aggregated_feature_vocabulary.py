"""Aggregate token and feature vocabulary from seed files."""
from __future__ import annotations

from typing import Any

from iapetus.data.seed_data_models import SeedFixtureSample
from iapetus.data.curated_seed_loaders import load_fixture_seed, load_permission_seed, load_static_token_seed


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

    for raw in fixtures:
        sample = SeedFixtureSample.model_validate(raw)
        sample_type = str(sample.sample_type).strip().lower()
        if sample_type in {"malware", "malicious"}:
            classification = sample.expected_classification or sample.labels.get("subtype")
        else:
            classification = sample.expected_classification or sample.labels.get("app_category")
        if isinstance(classification, str) and classification.strip():
            code_vocab.add(classification.strip())
        for permission in sample.permissions:
            if permission.strip():
                permission_vocab.add(permission.strip())
        for token in (
            *sample.components,
            *sample.intent_filters,
            *sample.manifest_flags,
            *sample.network_strings,
            *sample.code_strings,
        ):
            if token.strip():
                if "http://" in token or "https://" in token:
                    network_vocab.add(token.strip())
                else:
                    code_vocab.add(token.strip())
        for indicator in sample.suspicious_indicators:
            if indicator.strip():
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
