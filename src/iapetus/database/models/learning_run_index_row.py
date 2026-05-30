"""Row shape for the ``learning_runs`` index table."""
from __future__ import annotations

from typing import TypedDict


class LearningRunIndexRow(TypedDict):
    run_id: str
    created_at: str
    mode: str
    status: str
    model_name: str
    dataset_name: str
    entity_count: int
    run_dir: str
    backend: str | None
    entity_loocv: float | None
    classification_train_accuracy: float | None
    malware_subgroup_train: float | None
    benign_subgroup_train: float | None
