"""Shared learning-run index operations (CLI output, no Typer)."""
from __future__ import annotations

from pathlib import Path

from iapetus.database import index_learning_runs, kernel_database_health, learning_index_status

from iapetus.cli.cli_console_and_path_helpers import console


def print_registry_status(*, inspect: bool = False) -> None:
    if inspect:
        _print_kernel_database_inspect()
        return
    status = learning_index_status()
    console.print("[bold]Learning run index (M6 seed)[/bold]")
    console.print(f"Database     : {status['db_path']}")
    console.print(f"Exists       : {status['exists']}")
    console.print(f"Schema       : v{status['schema_version']}")
    if status.get("schema_current") is False and status.get("exists"):
        console.print("[yellow]Schema is not at the current kernel version — run db index or init.[/yellow]")
    console.print(f"Indexed runs : {status['run_count']}")
    if status.get("latest_run_id"):
        console.print(f"Latest run   : {status['latest_run_id']} ({status.get('latest_mode')})")


def _print_kernel_database_inspect() -> None:
    health = kernel_database_health()
    console.print("[bold]Kernel database inspect[/bold]")
    console.print(f"Database          : {health['db_path']}")
    console.print(f"Exists            : {health['exists']}")
    if not health["exists"]:
        return
    console.print(f"File size (bytes) : {health['file_size_bytes']}")
    console.print(f"Integrity         : {health['integrity_ok']}")
    console.print(
        f"Schema stored     : v{health['stored_schema_version']} "
        f"(expected v{health['expected_schema_version']})"
    )
    if health["schema_ahead_of_code"]:
        console.print("[red]Schema is newer than this code — upgrade Iapetus.[/red]")
    for table, count in sorted(health.get("table_row_counts", {}).items()):
        console.print(f"  {table:<16} {count} rows")


def print_index_learning_runs(runs_dir: Path) -> None:
    summary = index_learning_runs(runs_dir)
    console.print("[bold]Indexed learning runs[/bold]")
    console.print(f"Database : {summary['db_path']}")
    console.print(f"Runs dir : {summary['runs_dir']}")
    console.print(f"Indexed  : {summary['indexed_count']}")
    if summary["skipped_dirs"]:
        console.print(f"Skipped  : {', '.join(summary['skipped_dirs'])}")
