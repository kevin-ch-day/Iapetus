"""Upstream connector registry (seed stubs)."""
from __future__ import annotations

import typer

from iapetus.connectors import connector_registry_lines, get_connector

from iapetus.cli.cli_console_and_path_helpers import console

connectors_app = typer.Typer(help="Upstream connector registry (seed placeholders).")


def _run_connector_registry() -> None:
    console.print("[bold]CONNECTOR REGISTRY[/bold]")
    console.print("Seed placeholders only. Future adapters target learning-run entity artifacts.")
    for line in connector_registry_lines():
        console.print(line)


def _run_connector_show(connector_id: str) -> None:
    connector = get_connector(connector_id)
    if connector is None:
        console.print(f"[red]Unknown connector: {connector_id}[/red]")
        raise typer.Exit(code=1)
    console.print(f"[bold]{connector.display_name}[/bold] ({connector.connector_id})")
    console.print(f"Status       : {connector.status}")
    console.print(f"Adapter kind : {connector.adapter_kind}")
    console.print(f"Read-only    : {connector.read_only}")
    console.print(f"Artifacts    : {', '.join(connector.planned_entity_artifacts)}")
    console.print(f"Notes        : {connector.notes}")


@connectors_app.callback(invoke_without_command=True)
def connectors_root(ctx: typer.Context) -> None:
    """Show upstream connector registry (seed placeholders)."""
    if ctx.invoked_subcommand is None:
        _run_connector_registry()


@connectors_app.command("show")
def connectors_show(
    connector_id: str = typer.Argument(..., help="Connector id (e.g. erebus, obsidian_droid)."),
) -> None:
    """Show one connector stub in detail."""
    _run_connector_show(connector_id)
