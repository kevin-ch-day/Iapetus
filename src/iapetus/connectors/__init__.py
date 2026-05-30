"""Seed connector registry (placeholders only; no live integrations)."""

from .registry import (
    ConnectorDescriptor,
    connector_registry_lines,
    list_connectors,
)

__all__ = [
    "ConnectorDescriptor",
    "connector_registry_lines",
    "list_connectors",
]
