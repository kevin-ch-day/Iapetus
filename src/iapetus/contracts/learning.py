"""Contract constants for learning and snapshot manifests."""
from __future__ import annotations

from iapetus.contracts.versions import CONTRACT_VERSION_V1

LEARNING_RUN_MANIFEST_SCHEMA_NAME = "iapetus.learning.run_manifest"
LEARNING_RUN_MANIFEST_SCHEMA_VERSION = CONTRACT_VERSION_V1

LEARNING_RUN_RESULT_SCHEMA_NAME = "iapetus.learning.run_result"
LEARNING_RUN_RESULT_SCHEMA_VERSION = CONTRACT_VERSION_V1

LEARNING_ARTIFACT_MANIFEST_SCHEMA_NAME = "iapetus.learning.artifact_manifest"
LEARNING_ARTIFACT_MANIFEST_SCHEMA_VERSION = CONTRACT_VERSION_V1

SNAPSHOT_MANIFEST_SCHEMA_NAME = "iapetus.snapshot.manifest"
SNAPSHOT_MANIFEST_SCHEMA_VERSION = CONTRACT_VERSION_V1

STATIC_MLP_V2_MODE = "static_mlp_v2"

_LEARNING_MODE_ALIASES = {
    "smoke": "smoke",
    "static-v1": STATIC_MLP_V2_MODE,
    "static-v2": STATIC_MLP_V2_MODE,
    "static_v1": STATIC_MLP_V2_MODE,
    "static_v2": STATIC_MLP_V2_MODE,
    STATIC_MLP_V2_MODE: STATIC_MLP_V2_MODE,
}


def normalize_learning_mode_alias(mode: str) -> str:
    """Map CLI- and legacy-facing mode names to the canonical internal value."""
    normalized = mode.strip().lower().replace(" ", "_")
    return _LEARNING_MODE_ALIASES.get(normalized, normalized)


__all__ = [
    "LEARNING_RUN_MANIFEST_SCHEMA_NAME",
    "LEARNING_RUN_MANIFEST_SCHEMA_VERSION",
    "LEARNING_RUN_RESULT_SCHEMA_NAME",
    "LEARNING_RUN_RESULT_SCHEMA_VERSION",
    "LEARNING_ARTIFACT_MANIFEST_SCHEMA_NAME",
    "LEARNING_ARTIFACT_MANIFEST_SCHEMA_VERSION",
    "SNAPSHOT_MANIFEST_SCHEMA_NAME",
    "SNAPSHOT_MANIFEST_SCHEMA_VERSION",
    "STATIC_MLP_V2_MODE",
    "normalize_learning_mode_alias",
]
