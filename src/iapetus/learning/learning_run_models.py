"""Learning run Pydantic models and identifiers."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field

LearningMode = Literal["smoke", "static_v1"]


class LearningRunResult(BaseModel):
    run_id: str = Field(min_length=1)
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    mode: LearningMode
    dataset_name: str = Field(min_length=1)
    entity_count: int = Field(ge=0)
    malware_count: int = Field(ge=0)
    normal_app_count: int = Field(ge=0)
    unique_classifications: list[str]
    model_name: str = Field(min_length=1)
    status: Literal["PASS", "FAIL", "WARN"]
    notes: str
    use_curated_fixtures: bool = False
    generated_summaries_available: bool = False
    generated_summary_paths: dict[str, str] = Field(default_factory=dict)
    training_example_count: int = Field(default=0, ge=0)
    average_training_quality_score: float = Field(default=0.0, ge=0.0)


class LearningRunManifest(BaseModel):
    run_id: str = Field(min_length=1)
    created_at: str = Field(min_length=1)
    mode: LearningMode
    dataset_name: str = Field(min_length=1)
    status: Literal["PASS", "FAIL", "WARN"]
    model_name: str = Field(min_length=1)
    use_curated_fixtures: bool = False
    generated_summaries_available: bool = False
    generated_summary_paths: dict[str, str] = Field(default_factory=dict)


def generate_run_id() -> str:
    return f"run-{datetime.now(UTC).strftime('%Y%m%dT%H%M%S')}-{uuid4().hex[:8]}"
