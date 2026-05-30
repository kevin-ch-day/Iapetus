from __future__ import annotations

from typing import Any


def binary_confusion_matrix(predictions: list[int], labels: list[int]) -> dict[str, Any]:
    tp = sum(1 for pred, label in zip(predictions, labels, strict=True) if pred == 1 and label == 1)
    tn = sum(1 for pred, label in zip(predictions, labels, strict=True) if pred == 0 and label == 0)
    fp = sum(1 for pred, label in zip(predictions, labels, strict=True) if pred == 1 and label == 0)
    fn = sum(1 for pred, label in zip(predictions, labels, strict=True) if pred == 0 and label == 1)
    return {
        "true_positive": tp,
        "true_negative": tn,
        "false_positive": fp,
        "false_negative": fn,
        "matrix": [[tn, fp], [fn, tp]],
        "labels": ["normal_app", "malware"],
    }


def binary_precision_recall(predictions: list[int], labels: list[int]) -> dict[str, float]:
    matrix = binary_confusion_matrix(predictions, labels)
    tp, fp, fn = matrix["true_positive"], matrix["false_positive"], matrix["false_negative"]
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    return {
        "precision_malware": round(precision, 4),
        "recall_malware": round(recall, 4),
        "f1_malware": round(f1, 4),
    }


def per_class_accuracy(
    predictions: list[int],
    labels: list[int],
    *,
    index_to_label: dict[int, str],
) -> dict[str, float]:
    totals: dict[str, int] = {}
    correct: dict[str, int] = {}
    for pred, label in zip(predictions, labels, strict=True):
        name = index_to_label[label]
        totals[name] = totals.get(name, 0) + 1
        if pred == label:
            correct[name] = correct.get(name, 0) + 1
    return {
        name: round(correct.get(name, 0) / totals[name], 4)
        for name in sorted(totals)
    }
