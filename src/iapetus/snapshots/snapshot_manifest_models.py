from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field

from iapetus.contracts.learning import (
    SNAPSHOT_MANIFEST_SCHEMA_NAME,
    SNAPSHOT_MANIFEST_SCHEMA_VERSION,
)


class SnapshotManifest(BaseModel):
    schema_name: str = SNAPSHOT_MANIFEST_SCHEMA_NAME
    schema_version: str = SNAPSHOT_MANIFEST_SCHEMA_VERSION
    name: str = Field(min_length=1)
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    entity_count: int = Field(ge=0)
    purpose: str = Field(min_length=1, max_length=256)
