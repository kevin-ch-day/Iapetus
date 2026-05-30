from __future__ import annotations

from pathlib import Path

import iapetus.project_filesystem_paths as paths
from iapetus.application_config import path_overrides_from_config


def test_path_overrides_from_config_parses_paths_section() -> None:
    overrides = path_overrides_from_config(
        {
            "paths": {
                "data_dir": "custom/data",
                "learning_runs_dir": "custom/runs",
            }
        }
    )
    assert overrides["data_dir"] == Path("custom/data")
    assert overrides["learning_runs_dir"] == Path("custom/runs")


def test_reload_paths_applies_overrides() -> None:
    paths.reload_paths(
        {
            "data_dir": Path("tmp/data"),
            "output_dir": Path("tmp/out"),
            "generated_dir": Path("tmp/data/generated"),
            "learning_index_db_path": Path("tmp/data/custom.db"),
            "learning_runs_dir": Path("tmp/out/runs"),
        }
    )
    try:
        assert paths.LEARNING_RUNS_DIR == Path("tmp/out/runs")
        assert paths.GENERATED_DIR == Path("tmp/data/generated")
        assert paths.LEARNING_INDEX_DB_PATH == Path("tmp/data/custom.db")
    finally:
        paths.reload_paths({})
