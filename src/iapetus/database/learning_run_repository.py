"""Backward-compatible module path — prefer ``iapetus.database.repositories``."""
from __future__ import annotations

from iapetus.database.core import init_learning_index_database
from iapetus.database.repositories.learning_run_repository import *  # noqa: F403
