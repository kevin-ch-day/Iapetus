"""Shared CLI utilities and console output."""
from __future__ import annotations

from collections.abc import Callable, Iterable
from pathlib import Path

import typer
from rich.console import Console

from iapetus import project_filesystem_paths as paths
from iapetus.probes.host_environment_probe import collect_device_probe_state, collect_environment_info

console = Console()
MENU_SEPARATOR = "=" * 78

# Re-export seed paths for CLI commands and tests (monkeypatch ``iapetus.cli.cli_console_and_path_helpers``).
GENERATED_DIR = paths.GENERATED_DIR
LEARNING_RUNS_DIR = paths.LEARNING_RUNS_DIR
DEMO_OUTPUT_DIR = paths.DEMO_OUTPUT_DIR
CURATED_SNAPSHOT_DIR = paths.CURATED_SNAPSHOT_DIR


def sync_path_aliases() -> None:
    """Refresh CLI aliases after ``iapetus.project_filesystem_paths.reload_paths()``."""
    global GENERATED_DIR, LEARNING_RUNS_DIR, DEMO_OUTPUT_DIR, CURATED_SNAPSHOT_DIR
    GENERATED_DIR = paths.GENERATED_DIR
    LEARNING_RUNS_DIR = paths.LEARNING_RUNS_DIR
    DEMO_OUTPUT_DIR = paths.DEMO_OUTPUT_DIR
    CURATED_SNAPSHOT_DIR = paths.CURATED_SNAPSHOT_DIR


def _menu_line(label: str, value: str, width: int = 12) -> str:
    return f"{label:<{width}}: {value}"


def _collect_device_for_banner(timeout_seconds: float = 1.0) -> str:
    try:
        return collect_device_probe_state(timeout_seconds=timeout_seconds)
    except Exception:
        return "error"


def _prompt_choice(prompt: str, minimum: int, maximum: int) -> int | None:
    try:
        raw_choice = input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        return None

    try:
        choice = int(raw_choice)
    except ValueError:
        console.print(f"[red]Invalid input '{raw_choice}'; expected a number {minimum}-{maximum}.[/red]")
        return None

    if choice < minimum or choice > maximum:
        console.print(
            f"[red]Selection '{choice}' is outside valid range {minimum}-{maximum}.[/red]",
        )
        return None

    return choice


def _run_list(lines: Iterable[str]) -> None:
    for line in lines:
        console.print(line)


def _run_with_error_context(context: str, fn: Callable[[], None]) -> None:
    try:
        fn()
    except typer.Exit:
        raise
    except Exception as exc:
        console.print(f"[red]{context} failed: {exc}[/red]")
        raise typer.Exit(code=1)


def print_token_group(title: str, values: list[str]) -> None:
    console.print(f"[bold]{title}[/bold]")
    if not values:
        console.print("- (none)")
        return
    for value in values:
        console.print(f"- {value}")


def print_environment_probe(check_device: bool = False) -> None:
    try:
        environment = collect_environment_info()
    except Exception as exc:
        console.print(f"[red]Environment probe failed: {exc}[/red]")
        raise typer.Exit(code=1)

    console.print("[bold]Iapetus environment probe[/bold]")
    console.print(f"Host OS       : {environment.system}")
    console.print(f"Host Version  : {environment.release}")
    console.print(f"Python        : {environment.python_version}")
    if check_device:
        try:
            state = collect_device_probe_state()
            console.print(f"Device probe  : {state}")
        except Exception as exc:
            console.print(f"[yellow]Device probe failed: {exc}[/yellow]")
            raise typer.Exit(code=1)
