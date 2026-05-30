"""SQLite learning-run index commands."""
from __future__ import annotations

from pathlib import Path

import typer

import iapetus.cli.cli_console_and_path_helpers as cli_common
from iapetus.cli.sqlite_learning_index_cli_output import print_index_learning_runs, print_registry_status

db_app = typer.Typer(help="Seed local persistence (SQLite learning-run index).")


@db_app.command("status")
def db_status() -> None:
    """Show SQLite learning-run index status."""
    print_registry_status()


@db_app.command("inspect")
def db_inspect() -> None:
    """Detailed kernel database health (tables, integrity, schema version)."""
    print_registry_status(inspect=True)


@db_app.command("init")
def db_init() -> None:
    """Create or upgrade the kernel database schema in place."""
    from iapetus.database import default_kernel_database

    path = default_kernel_database().initialize()
    cli_common.console.print(f"[green]Kernel database ready:[/green] {path}")


@db_app.command("index")
def db_index(
    runs_dir: Path | None = typer.Option(None, "--runs-dir", help="Learning runs root to scan."),
) -> None:
    """Rebuild the learning-run index from disk."""
    print_index_learning_runs(runs_dir or cli_common.LEARNING_RUNS_DIR)
