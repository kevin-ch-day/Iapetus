"""Operator menu."""
from __future__ import annotations

import sys

import typer

import iapetus.cli.cli_console_and_path_helpers as cli_common
from iapetus.cli.cli_console_and_path_helpers import (
    MENU_SEPARATOR,
    _collect_device_for_banner,
    _menu_line,
    _prompt_choice,
    _run_list,
    _run_with_error_context,
    console,
)
from iapetus.cli.typer_connector_catalog_commands import _run_connector_registry
from iapetus.cli.host_platform_probe_commands import (
    _print_seed_about,
    _run_environment_device_probe,
    _run_roadmap,
    _status_output,
)
from iapetus.cli.typer_dataset_preview_commands import _run_dataset_shape_preview
from iapetus.cli.interactive_learning_console_router import run_learning_console
from iapetus.cli.learning_subcommand_handler_bridge import _run_deep_learning_menu, print_label_laboratory
from iapetus.cli.typer_snapshot_subcommands import _run_demo_snapshot_summary


def menu_lines() -> list[str]:
    try:
        environment = cli_common.collect_environment_info()
        host_os = environment.system
        host_version = environment.release
        python_version = environment.python_version
    except Exception:
        host_os = "Unknown"
        host_version = "unknown"
        python_version = "unknown"

    device_state = _collect_device_for_banner()

    return [
        MENU_SEPARATOR,
        f"{'IAPETUS':^78}",
        f"{'Android Security Deep-Learning Operator':^78}",
        MENU_SEPARATOR,
        _menu_line("Host", host_os),
        _menu_line("Host Version", host_version),
        _menu_line("Python", python_version),
        _menu_line("Mode", "seed"),
        _menu_line("Data", "demo fixtures + curated seeds optional"),
        _menu_line("Learning", "smoke available"),
        _menu_line("Iapetus DB", "not initialized"),
        _menu_line("Upstream", "not connected"),
        _menu_line("Device", device_state),
        _menu_line("Emulator", "not checked"),
        "",
        "MAIN MENU",
        "---------",
        "  [1] Run Deep Learning",
        "  [2] Learning Console",
        "  [3] Build / View Demo Snapshot",
        "  [4] Label Laboratory",
        "  [5] Environment & Device Probe",
        "  [6] Connector Registry",
        "  [7] Roadmap",
        "  [8] Help / About",
        "  [0] Exit",
    ]


def register_menu_command(app: typer.Typer) -> None:
    @app.command()
    def menu(
        choice: int | None = typer.Option(
            None,
            "--choice",
            "-c",
            help="Menu item 0-8 (non-interactive).",
            min=0,
            max=8,
        ),
        deep_choice: int | None = typer.Option(
            None,
            "--deep-choice",
            help="Deep learning submenu 0-5 when choice=1.",
            min=0,
            max=5,
            show_default=False,
        ),
        console_command: str | None = typer.Option(
            None,
            "--console-command",
            help="Optional single command for Learning Console.",
            show_default=False,
        ),
    ) -> None:
        """Operator menu for the seed platform."""
        _run_list(menu_lines())

        if choice is None:
            if not sys.stdin.isatty():
                console.print(
                    "[yellow]Non-interactive mode: pass --choice with a value 0-8 to run an item quickly.[/yellow]",
                )
                return
            choice = _prompt_choice("Select [0-8]: ", 0, 8)
            if choice is None:
                return

        if choice == 0:
            console.print("[green]Exiting operator menu.[/green]")
            return
        if choice == 1:

            def _run_deep() -> None:
                if not _run_deep_learning_menu(deep_choice=deep_choice):
                    raise typer.Exit(code=1)

            _run_with_error_context("Run Deep Learning", _run_deep)
            return
        if choice == 2:
            _run_with_error_context(
                "Learning console",
                lambda: run_learning_console(optional_command=console_command),
            )
            return
        if choice == 3:
            _run_with_error_context("Demo snapshot preview", _run_demo_snapshot_summary)
            return
        if choice == 4:
            _run_with_error_context("Label Laboratory", print_label_laboratory)
            return
        if choice == 5:
            _run_environment_device_probe()
            return
        if choice == 6:
            _run_connector_registry()
            return
        if choice == 7:
            _run_roadmap()
            return
        if choice == 8:
            _print_seed_about()
            return

        console.print("[red]Unknown menu selection.[/red]")
