"""Registry of domain schema appliers applied during kernel bootstrap."""
from __future__ import annotations

import sqlite3
from collections.abc import Callable, Iterable
from dataclasses import dataclass

SchemaApplier = Callable[[sqlite3.Connection], None]

_REGISTERED: list[DomainSchema] = []


@dataclass(frozen=True, slots=True)
class DomainSchema:
    """Named DDL applier for one domain table group."""

    name: str
    apply: SchemaApplier


def register_domain_schema(name: str, apply: SchemaApplier) -> None:
    """Register a schema applier (typically called from ``database.schemas``)."""
    if any(entry.name == name for entry in _REGISTERED):
        raise ValueError(f"domain schema already registered: {name}")
    _REGISTERED.append(DomainSchema(name=name, apply=apply))


def clear_domain_schemas_for_tests() -> None:
    """Reset registry (tests only)."""
    _REGISTERED.clear()


def iter_domain_schemas() -> Iterable[DomainSchema]:
    return tuple(_REGISTERED)


def apply_registered_domain_schemas(conn: sqlite3.Connection) -> None:
    for entry in _REGISTERED:
        entry.apply(conn)
