"""Seed connector registry (placeholders only; no live integrations)."""

from .external_connector_catalog import (
    ConnectorDescriptor,
    connector_registry_lines,
    get_connector,
    list_connectors,
)

__all__ = [
    "ConnectorDescriptor",
    "connector_registry_lines",
    "get_connector",
    "list_connectors",
]
