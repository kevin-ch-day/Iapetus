"""Iapetus command-line interface."""
from __future__ import annotations

from iapetus.cli.typer_application import app
from iapetus.cli.cli_console_and_path_helpers import (
    CURATED_SNAPSHOT_DIR,
    DEMO_OUTPUT_DIR,
    GENERATED_DIR,
    LEARNING_RUNS_DIR,
    collect_device_probe_state,
    collect_environment_info,
    console,
)
from iapetus.cli.interactive_operator_menu import menu_lines
from iapetus.snapshots.demo_snapshot_builder import snapshot_output

__all__ = [
    "app",
    "menu_lines",
    "LEARNING_RUNS_DIR",
    "GENERATED_DIR",
    "DEMO_OUTPUT_DIR",
    "CURATED_SNAPSHOT_DIR",
    "console",
    "collect_environment_info",
    "collect_device_probe_state",
    "snapshot_output",
]
