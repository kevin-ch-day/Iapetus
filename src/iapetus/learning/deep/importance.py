from __future__ import annotations

from typing import Any

from iapetus.learning.deep.features import STATIC_FEATURE_NAMES
from iapetus.learning.deep.model import PurePythonMLP


def first_layer_feature_importance(
    model: PurePythonMLP,
    row: list[float],
    *,
    top_k: int = 8,
) -> list[dict[str, Any]]:
    scores: list[tuple[str, float]] = []
    for feature_index, feature_name in enumerate(STATIC_FEATURE_NAMES):
        weight_sum = sum(abs(model.w1[hidden_index][feature_index]) for hidden_index in range(model.hidden_size))
        scores.append((feature_name, weight_sum * row[feature_index]))
    scores.sort(key=lambda item: item[1], reverse=True)
    return [
        {"feature": name, "attribution": round(value, 6)}
        for name, value in scores[:top_k]
    ]
