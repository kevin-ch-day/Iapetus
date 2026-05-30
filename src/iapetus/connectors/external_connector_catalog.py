from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ConnectorDescriptor:
    connector_id: str
    display_name: str
    status: str
    adapter_kind: str
    read_only: bool
    planned_entity_artifacts: tuple[str, ...]
    notes: str


_CONNECTORS: tuple[ConnectorDescriptor, ...] = (
    ConnectorDescriptor(
        connector_id="erebus",
        display_name="Erebus",
        status="not_connected",
        adapter_kind="read_only_snapshot_adapter",
        read_only=True,
        planned_entity_artifacts=(
            "entities.json",
            "entity_token_groups.json",
            "entity_features.json",
        ),
        notes="Future governed evidence ingest; seed uses curated JSON fixtures instead.",
    ),
    ConnectorDescriptor(
        connector_id="permission_intel",
        display_name="Permission Intel",
        status="not_connected",
        adapter_kind="permission_observation_adapter",
        read_only=True,
        planned_entity_artifacts=("entity_token_groups.json",),
        notes="Future permission observations aligned with fixture permission groups.",
    ),
    ConnectorDescriptor(
        connector_id="scytale_droid",
        display_name="ScytaleDroid",
        status="not_connected",
        adapter_kind="static_analysis_adapter",
        read_only=True,
        planned_entity_artifacts=(
            "entity_token_groups.json",
            "entity_features.json",
        ),
        notes="Future static-analysis rows mapped to components, intents, and code strings.",
    ),
    ConnectorDescriptor(
        connector_id="obsidian_droid",
        display_name="ObsidianDroid",
        status="not_connected",
        adapter_kind="malware_label_adapter",
        read_only=True,
        planned_entity_artifacts=("entities.json", "labeled_entities.json"),
        notes="Future malware/normal label contracts; seed renders labels from fixtures.",
    ),
    ConnectorDescriptor(
        connector_id="web_review_exports",
        display_name="Web review exports",
        status="not_connected",
        adapter_kind="review_decision_adapter",
        read_only=True,
        planned_entity_artifacts=("labeled_entities.json",),
        notes="Future triage exports; no web/API in seed mode.",
    ),
    ConnectorDescriptor(
        connector_id="physical_device",
        display_name="Physical device",
        status="not_connected",
        adapter_kind="dynamic_session_adapter",
        read_only=True,
        planned_entity_artifacts=("entity_features.json",),
        notes="Future adb-backed dynamic windows; seed probe is adb presence only.",
    ),
    ConnectorDescriptor(
        connector_id="emulator_vm",
        display_name="Emulator / VM",
        status="not_connected",
        adapter_kind="dynamic_session_adapter",
        read_only=True,
        planned_entity_artifacts=("entity_features.json",),
        notes="Future emulator orchestration; not available in seed kernel.",
    ),
)


def list_connectors() -> list[ConnectorDescriptor]:
    return list(_CONNECTORS)


def get_connector(connector_id: str) -> ConnectorDescriptor | None:
    normalized = connector_id.strip().lower().replace("-", "_")
    for connector in _CONNECTORS:
        if connector.connector_id == normalized:
            return connector
    return None


def connector_registry_lines() -> list[str]:
    lines: list[str] = []
    for connector in _CONNECTORS:
        artifacts = ", ".join(connector.planned_entity_artifacts)
        lines.append(
            f"{connector.display_name:<20}: {connector.status} "
            f"[{connector.adapter_kind}, read_only={connector.read_only}]"
        )
        lines.append(f"  planned artifacts: {artifacts}")
        lines.append(f"  notes: {connector.notes}")
    return lines
