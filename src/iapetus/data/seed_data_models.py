"""Pydantic models for curated seed data."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

TrustedLevel = Literal["low", "medium", "high", "unknown"]


class SourceManifest(BaseModel):
    source_id: str = Field(min_length=1)
    source_name: str = Field(min_length=1)
    source_url: str = Field(min_length=1)
    retrieved_at: str = Field(min_length=1)
    local_path: str = Field(min_length=1)
    sha256: str = Field(min_length=1)
    license_or_terms_note: str = Field(min_length=1)
    purpose: str = Field(min_length=1)
    source_kind: str = Field(min_length=1)
    trusted_level: TrustedLevel


class SeedFixtureSample(BaseModel):
    sample_id: str = Field(min_length=1)
    sample_name: str = Field(min_length=1)
    sample_type: str = Field(min_length=1)
    fixture_slug: str | None = None
    platform: str | None = None
    package_name: str | None = None
    display_name: str | None = None
    build_ref: str | None = None
    variant: str | None = None
    rendered_label: str | None = None
    permissions: list[str] = Field(min_length=1)
    labels: dict[str, Any] = Field(default_factory=dict)
    expected_classification: str | None = None
    components: list[str] = Field(default_factory=list)
    intent_filters: list[str] = Field(default_factory=list)
    manifest_flags: list[str] = Field(default_factory=list)
    network_strings: list[str] = Field(default_factory=list)
    code_strings: list[str] = Field(default_factory=list)
    suspicious_indicators: list[str] = Field(default_factory=list)
    notes: str | None = None
