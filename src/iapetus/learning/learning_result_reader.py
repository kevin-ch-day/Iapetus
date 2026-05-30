"""Learning run result I/O (avoids circular imports with storage)."""
from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from iapetus.learning.learning_run_models import LearningRunResult


def read_learning_result_file(path: Path) -> LearningRunResult:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not read learning result: {path}") from exc

    try:
        return LearningRunResult.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(f"Invalid learning result payload in {path}: {exc}") from exc
