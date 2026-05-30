"""Learning-console command routing (menu choice 2 and batch ``--console-command``)."""
from __future__ import annotations

import typer

import iapetus.cli.cli_console_and_path_helpers as cli_common
from iapetus.cli.typer_android_fixture_commands import _run_android_tokens
from iapetus.cli.cli_console_and_path_helpers import console
from iapetus.cli.typer_connector_catalog_commands import _run_connector_registry
from iapetus.cli.host_platform_probe_commands import _run_roadmap, _status_output
from iapetus.cli.typer_dataset_preview_commands import _run_dataset_shape_preview
from iapetus.cli.learning_subcommand_handler_bridge import (
    _run_learn_absorb,
    _run_learn_compare_fixtures,
    _run_learn_corpus,
    _run_learn_explain_fixture,
    _run_learning_last,
    _run_learning_list,
    _run_smoke_learning_summary,
    print_label_laboratory,
)
from iapetus.cli.sqlite_learning_index_cli_output import print_index_learning_runs, print_registry_status
from iapetus.cli.typer_snapshot_subcommands import _run_demo_snapshot_summary


def learning_console_command_is_known(command: str) -> bool:
    normalized = command.strip().lower()
    if normalized in {
        "help",
        "status",
        "labels",
        "snapshot",
        "learn smoke",
        "learn list",
        "learn last",
        "learn absorb",
        "learn corpus",
        "learn index",
        "db status",
        "dataset shape",
        "roadmap",
        "connectors",
        "exit",
        "",
    }:
        return True
    return normalized.startswith(
        (
            "android tokens ",
            "learn explain-fixture ",
            "learn compare-fixtures ",
        )
    )


def run_learning_console_command(command: str) -> bool:
    """Return False when the console session should exit."""
    command = command.strip().lower()
    if not command:
        return True
    if command == "exit":
        console.print("Learning console closed.")
        return False
    if command == "help":
        print_learning_console_help()
        return True
    if command == "status":
        _status_output()
        return True
    if command == "labels":
        print_label_laboratory()
        return True
    if command == "snapshot":
        _run_demo_snapshot_summary()
        return True
    if command == "learn smoke":
        _run_smoke_learning_summary()
        return True
    if command == "learn list":
        _run_learning_list(output_dir=cli_common.LEARNING_RUNS_DIR)
        return True
    if command == "learn last":
        _run_learning_last(output_dir=cli_common.LEARNING_RUNS_DIR)
        return True
    if command == "learn absorb":
        _run_learn_absorb()
        return True
    if command == "learn corpus":
        _run_learn_corpus()
        return True
    if command == "learn index":
        print_index_learning_runs(cli_common.LEARNING_RUNS_DIR)
        return True
    if command == "db status":
        print_registry_status()
        return True
    if command.startswith("android tokens"):
        parts = command.split(maxsplit=2)
        fixture = parts[-1] if len(parts) >= 3 else "malware_banker"
        _run_android_tokens(fixture=fixture)
        return True
    if command.startswith("learn explain-fixture"):
        parts = command.split(maxsplit=2)
        fixture = parts[-1] if len(parts) >= 3 else "malware_banker"
        _run_learn_explain_fixture(fixture=fixture)
        return True
    if command.startswith("learn compare-fixtures"):
        parts = command.split()
        left = parts[2] if len(parts) > 2 else "benign_social_app"
        right = parts[3] if len(parts) > 3 else "malware_banker"
        _run_learn_compare_fixtures(left=left, right=right)
        return True
    if command == "dataset shape":
        _run_dataset_shape_preview()
        return True
    if command == "roadmap":
        _run_roadmap()
        return True
    if command == "connectors":
        _run_connector_registry()
        return True

    console.print(f"[yellow]Unknown command: {command}[/yellow]")
    console.print("Type 'help' for available commands.")
    return True


def run_learning_console_command_for_batch(command: str) -> bool:
    normalized = command.strip().lower()
    if not learning_console_command_is_known(normalized):
        run_learning_console_command(command)
        raise typer.Exit(code=1)
    return run_learning_console_command(command)


def print_learning_console_help() -> None:
    console.print("iapetus> status")
    console.print("iapetus> labels")
    console.print("iapetus> snapshot")
    console.print("iapetus> learn smoke")
    console.print("iapetus> learn list")
    console.print("iapetus> learn last")
    console.print("iapetus> learn absorb")
    console.print("iapetus> learn index")
    console.print("iapetus> db status")
    console.print("iapetus> android tokens malware_banker")
    console.print("iapetus> learn explain-fixture malware_banker")
    console.print("iapetus> learn compare-fixtures benign_social_app malware_banker")
    console.print("iapetus> dataset shape")
    console.print("iapetus> roadmap")
    console.print("iapetus> connectors")
    console.print("iapetus> help")
    console.print("iapetus> exit")


def run_learning_console(optional_command: str | None = None) -> None:
    """Interactive or single-shot learning console (menu choice 2)."""
    console.print("[bold]LEARNING CONSOLE[/bold]")
    print_learning_console_help()

    if optional_command is not None:
        if not run_learning_console_command_for_batch(optional_command):
            return
        console.print("Learning console session complete.")
        return

    while True:
        try:
            raw_command = input("iapetus> ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("[yellow]Learning console closed.[/yellow]")
            return

        if not run_learning_console_command(raw_command):
            return
