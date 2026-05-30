from __future__ import annotations

from dataclasses import dataclass
from typing import Any

STATIC_FEATURE_NAMES: tuple[str, ...] = (
    "permission_count",
    "component_count",
    "network_string_count",
    "code_string_count",
    "suspicious_indicator_count",
    "has_sms_permission",
    "has_boot_persistence",
    "has_overlay_indicator",
    "has_dynamic_loading",
    "has_cleartext_network",
    "has_accessibility_abuse",
    "has_install_abuse",
    "has_surveillance_markers",
    "has_contact_or_sms_exfil",
    "has_ad_fraud_markers",
    "high_risk_permission_count",
    "manifest_flag_count",
    "intent_filter_count",
    "training_quality_score",
)


def _coerce_feature_value(value: Any) -> float:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):
        return float(value)
    return 0.0


def encode_row(feature_vector: dict[str, Any]) -> list[float]:
    return [_coerce_feature_value(feature_vector.get(name, 0)) for name in STATIC_FEATURE_NAMES]


def encode_example_row(example: dict[str, Any], stats: NormalizationStats) -> list[float]:
    return apply_normalization([encode_row(example["feature_vector"])], stats)[0]


def encode_feature_matrix(examples: list[dict[str, Any]]) -> list[list[float]]:
    return [encode_row(example["feature_vector"]) for example in examples]


@dataclass
class NormalizationStats:
    column_maxima: list[float]

    def to_dict(self) -> dict[str, Any]:
        return {"column_maxima": self.column_maxima, "feature_names": list(STATIC_FEATURE_NAMES)}

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> NormalizationStats:
        return cls(column_maxima=[float(value) for value in payload["column_maxima"]])


def fit_normalization(matrix: list[list[float]]) -> NormalizationStats:
    if not matrix:
        return NormalizationStats(column_maxima=[1.0 for _ in STATIC_FEATURE_NAMES])
    column_count = len(matrix[0])
    maxima = []
    for column_index in range(column_count):
        peak = max(row[column_index] for row in matrix)
        maxima.append(peak if peak > 0 else 1.0)
    return NormalizationStats(column_maxima=maxima)


def apply_normalization(matrix: list[list[float]], stats: NormalizationStats) -> list[list[float]]:
    return [
        [
            row[column_index] / stats.column_maxima[column_index]
            for column_index in range(len(row))
        ]
        for row in matrix
    ]


def normalize_feature_matrix(matrix: list[list[float]]) -> list[list[float]]:
    return apply_normalization(matrix, fit_normalization(matrix))


def encode_entity_kind_labels(examples: list[dict[str, Any]]) -> list[int]:
    return [1 if example["entity_kind"] == "malware" else 0 for example in examples]


def encode_labels(examples: list[dict[str, Any]]) -> list[int]:
    return encode_entity_kind_labels(examples)


def build_classification_index(examples: list[dict[str, Any]]) -> tuple[dict[str, int], dict[int, str]]:
    classes = sorted({str(example["expected_classification"]) for example in examples})
    class_to_index = {name: index for index, name in enumerate(classes)}
    index_to_class = {index: name for name, index in class_to_index.items()}
    return class_to_index, index_to_class


def split_examples_by_entity_kind(
    examples: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    malware = [example for example in examples if example["entity_kind"] == "malware"]
    benign = [example for example in examples if example["entity_kind"] == "normal_app"]
    return malware, benign


def encode_classification_labels(
    examples: list[dict[str, Any]],
    class_to_index: dict[str, int],
) -> list[int]:
    return [class_to_index[str(example["expected_classification"])] for example in examples]


def prepare_training_batch(
    examples: list[dict[str, Any]],
) -> tuple[list[list[float]], list[int], list[int], NormalizationStats, dict[str, int], dict[int, str]]:
    raw_matrix = encode_feature_matrix(examples)
    stats = fit_normalization(raw_matrix)
    matrix = apply_normalization(raw_matrix, stats)
    entity_labels = encode_entity_kind_labels(examples)
    class_to_index, index_to_class = build_classification_index(examples)
    class_labels = encode_classification_labels(examples, class_to_index)
    return matrix, entity_labels, class_labels, stats, class_to_index, index_to_class


def feature_schema_document() -> dict[str, Any]:
    return {
        "schema_version": "static-v2",
        "feature_names": list(STATIC_FEATURE_NAMES),
        "targets": {
            "entity_kind": "binary (1=malware, 0=normal_app)",
            "classification": "multiclass expected_classification",
        },
        "source": "training_corpus feature_vector rows",
    }
