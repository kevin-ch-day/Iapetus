from __future__ import annotations

from pathlib import Path
from typing import Any

import tomllib


def load_local_config(path: str | Path = "config/local.toml") -> dict[str, Any]:
    config_path = Path(path)
    if not config_path.exists():
        return {}
    with config_path.open("rb") as fp:
        return tomllib.load(fp)


def path_overrides_from_config(config: dict[str, Any] | None = None) -> dict[str, Path]:
    """Return optional ``[paths]`` entries from local config (string values only)."""
    payload = config if config is not None else load_local_config()
    section = payload.get("paths")
    if not isinstance(section, dict):
        return {}

    keys = (
        "data_dir",
        "output_dir",
        "generated_dir",
        "learning_index_db_path",
        "learning_runs_dir",
        "demo_snapshot_dir",
        "curated_snapshot_dir",
    )
    overrides: dict[str, Path] = {}
    for key in keys:
        raw = section.get(key)
        if isinstance(raw, str) and raw.strip():
            overrides[key] = Path(raw.strip())
    return overrides
