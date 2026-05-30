"""Domain table DDL — registers appliers with ``database.core.registry`` on import."""
from __future__ import annotations

from iapetus.database.core.registry import register_domain_schema
from iapetus.database.schemas.learning_runs import LEARNING_RUNS_TABLE, apply_learning_runs_schema

register_domain_schema("learning_runs", apply_learning_runs_schema)

__all__ = ["LEARNING_RUNS_TABLE", "apply_learning_runs_schema"]
