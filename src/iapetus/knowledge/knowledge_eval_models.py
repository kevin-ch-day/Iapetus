"""Models for deterministic Android security knowledge evaluation."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field


KnowledgeEvalDifficulty = Literal["baseline", "intermediate", "trick"]
KnowledgeEvalStatus = Literal["covered", "partial", "gap"]


class AndroidKnowledgeEvalQuestion(BaseModel):
    question_id: str = Field(min_length=1)
    topic: str = Field(min_length=1)
    difficulty: KnowledgeEvalDifficulty
    question: str = Field(min_length=1)
    expected_answer_summary: str = Field(min_length=1)
    expected_concepts: list[str] = Field(default_factory=list)
    expected_uncertainty_flags: list[str] = Field(default_factory=list)
    source_kind: str = Field(min_length=1)
    review_status: str = Field(min_length=1)


@dataclass(frozen=True)
class AndroidKnowledgeEvalResult:
    question_id: str
    topic: str
    difficulty: KnowledgeEvalDifficulty
    status: KnowledgeEvalStatus
    question: str
    matched_concepts: list[str]
    missing_concepts: list[str]
    matched_uncertainty_flags: list[str]
    missing_uncertainty_flags: list[str]

