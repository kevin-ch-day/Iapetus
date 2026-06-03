"""Pydantic models for Windows-native Android security import contracts."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

GovernanceSyntheticLevel = Literal["none", "low", "medium", "high"]
GovernanceReviewStatus = Literal["draft", "reviewed", "approved"]
TrainingEligibility = Literal[
    "teaching_only",
    "training_candidate",
    "training_approved",
    "validation_only",
    "explanation_only",
]


class GovernedImportContractRecord(BaseModel):
    schema_name: str = Field(min_length=1)
    schema_version: str = Field(min_length=1)
    source_kind: str = Field(min_length=1)
    teaching_use: bool
    training_use: bool
    training_eligibility: TrainingEligibility
    synthetic_level: GovernanceSyntheticLevel
    review_status: GovernanceReviewStatus
    confidence_note: str = Field(min_length=1)


class PermissionAuthorityFact(GovernedImportContractRecord):
    permission: str = Field(min_length=1)
    protection_level: str = Field(min_length=1)
    permission_group: str = Field(min_length=1)
    authority_type: Literal["public", "hidden", "platform", "custom"]
    grant_model: Literal["dangerous", "signature", "runtime", "install_time"]
    known_abuse_concepts: list[str]
    benign_commonality: Literal["low", "medium", "high"]
    malware_commonality: Literal["low", "medium", "high"]


class AndroidConceptLesson(GovernedImportContractRecord):
    concept_id: str = Field(min_length=1)
    topic: str = Field(min_length=1)
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    related_concepts: list[str]


class MalwareTypePattern(GovernedImportContractRecord):
    pattern_id: str = Field(min_length=1)
    malware_type: Literal["banker", "spyware", "stealer", "rat", "adware", "dropper", "sms_trojan", "unknown"]
    permissions: list[str] = Field(default_factory=list)
    static_tokens: list[str] = Field(default_factory=list)
    concepts: list[str] = Field(default_factory=list)


class BenignAppArchetype(GovernedImportContractRecord):
    archetype_id: str = Field(min_length=1)
    category: str = Field(min_length=1)
    expected_permissions: list[str] = Field(default_factory=list)
    expected_context: list[str] = Field(default_factory=list)
    contrast_notes: list[str] = Field(default_factory=list)


class PermissionPatternExample(GovernedImportContractRecord):
    example_id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    permissions: list[str] = Field(default_factory=list)
    benign_context: list[str] = Field(default_factory=list)
    suspicious_context: list[str] = Field(default_factory=list)
    teaches: str = Field(min_length=1)


class AttackMobileSeedMapping(GovernedImportContractRecord):
    mapping_id: str = Field(min_length=1)
    platform: Literal["android"]
    concept: str = Field(min_length=1)
    behavior_ref: str = Field(min_length=1)
    use_case: Literal["explanation_only", "training_hint", "mapping_only"]
