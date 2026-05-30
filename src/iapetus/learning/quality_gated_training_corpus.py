from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from iapetus.curated_seed_library_exports import load_fixture_seed
from iapetus.curated_fixture_analysis import (
    build_entity_features,
    extract_fixture_token_groups,
    fixture_record,
)
from iapetus.validation.fixture_quality_report import validate_fixture_quality

_HIGH_RISK_PERMISSIONS = frozenset(
    {
        "android.permission.READ_SMS",
        "android.permission.RECEIVE_SMS",
        "android.permission.SEND_SMS",
        "android.permission.BIND_ACCESSIBILITY_SERVICE",
        "android.permission.SYSTEM_ALERT_WINDOW",
        "android.permission.REQUEST_INSTALL_PACKAGES",
        "android.permission.READ_CONTACTS",
        "android.permission.WRITE_EXTERNAL_STORAGE",
    }
)


def compute_training_quality_score(
    record: dict[str, Any],
    features: dict[str, Any],
    *,
    training_eligible: bool,
) -> int:
    if not training_eligible:
        return 0

    score = 45
    if features.get("permission_count", 0) >= 3:
        score += 10
    if features.get("component_count", 0) >= 2:
        score += 8
    if features.get("network_string_count", 0) >= 1:
        score += 7
    if features.get("code_string_count", 0) >= 2:
        score += 8
    if features.get("suspicious_indicator_count", 0) >= 1:
        score += 7
    if record.get("rendered_label"):
        score += 10
    if record.get("package_name"):
        score += 5
    return min(score, 100)


def build_training_example(item: dict[str, Any]) -> dict[str, Any] | None:
    record = fixture_record(item)
    groups = extract_fixture_token_groups(item)
    features = build_entity_features(record, groups, raw_item=item)
    quality = validate_fixture_quality(item)
    if not quality.training_eligible:
        return None

    permissions = set(record["permissions"])
    score = compute_training_quality_score(
        record,
        features,
        training_eligible=quality.training_eligible,
    )
    features["training_quality_score"] = score
    features["high_risk_permission_count"] = len(permissions & _HIGH_RISK_PERMISSIONS)

    return {
        "example_id": f"train-{record['fixture_slug']}",
        "fixture_slug": record["fixture_slug"],
        "sample_id": record["sample_id"],
        "entity_kind": record["entity_kind"],
        "expected_classification": record["expected_classification"],
        "rendered_label": record["rendered_label"],
        "package_name": record["package_name"],
        "training_quality_score": score,
        "feature_vector": features,
        "token_summary": {
            "permission_count": len(groups["permissions"]),
            "component_count": len(groups["components"]),
            "static_surface_tokens": (
                len(groups["components"])
                + len(groups["intent_filters"])
                + len(groups["code_strings"])
                + len(groups["network_strings"])
            ),
        },
        "quality": {
            "training_eligible": quality.training_eligible,
            "severity": quality.severity,
            "issues": quality.issues,
            "training_blockers": quality.training_blockers,
        },
    }


def build_training_corpus() -> dict[str, Any]:
    examples: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []

    for item in load_fixture_seed():
        record = fixture_record(item)
        quality = validate_fixture_quality(item)
        if quality.training_eligible:
            example = build_training_example(item)
            if example is not None:
                examples.append(example)
        else:
            blocked.append(
                {
                    "fixture_slug": record["fixture_slug"],
                    "training_blockers": quality.training_blockers,
                    "issues": quality.issues,
                }
            )

    examples.sort(key=lambda row: (row["entity_kind"], row["fixture_slug"]))
    scores = [row["training_quality_score"] for row in examples]
    malware = [row for row in examples if row["entity_kind"] == "malware"]
    benign = [row for row in examples if row["entity_kind"] == "normal_app"]
    by_class: dict[str, int] = {}
    for row in examples:
        key = str(row["expected_classification"])
        by_class[key] = by_class.get(key, 0) + 1

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "corpus_version": "seed-1",
        "purpose": "Quality-gated training examples from curated fixtures only.",
        "fixture_count": len(examples) + len(blocked),
        "training_example_count": len(examples),
        "blocked_fixture_count": len(blocked),
        "malware_example_count": len(malware),
        "normal_app_example_count": len(benign),
        "classifications": sorted(by_class.keys()),
        "examples_per_classification": by_class,
        "average_training_quality_score": round(sum(scores) / len(scores), 1) if scores else 0.0,
        "min_training_quality_score": min(scores) if scores else 0,
        "max_training_quality_score": max(scores) if scores else 0,
        "training_examples": examples,
        "blocked_fixtures": blocked,
        "notes": [
            "Only training_eligible curated rows are included.",
            "Scores reward complete static-analysis surfaces (permissions, components, strings).",
            "No model weights are trained in seed mode; this corpus feeds future pipelines.",
        ],
    }
