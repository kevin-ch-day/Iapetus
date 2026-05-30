from __future__ import annotations

from iapetus.learning.learning_run_artifacts import expected_artifacts_for_mode


def test_static_v1_expected_artifacts_include_split_heads() -> None:
    names = expected_artifacts_for_mode("static_v1", use_curated=True)
    assert "malware_classification_weights.json" in names
    assert "benign_classification_weights.json" in names
    assert "normalization.json" in names
    assert "classification_weights.json" not in names


def test_smoke_expected_artifacts_are_minimal() -> None:
    names = expected_artifacts_for_mode("smoke", use_curated=False)
    assert "learning_result.json" in names
    assert "training_metrics.json" not in names
