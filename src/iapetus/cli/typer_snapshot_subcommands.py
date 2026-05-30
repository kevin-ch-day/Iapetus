"""Snapshot and label demo commands."""
from __future__ import annotations

from pathlib import Path

import typer

from iapetus.labels.malware_label_text_renderer import (
    MalwareLabel,
    NormalAppLabel,
    render_malware_label,
    render_normal_app_label,
)
from iapetus.snapshots.demo_snapshot_builder import build_curated_snapshot, build_demo_snapshot, snapshot_output

import iapetus.cli.cli_console_and_path_helpers as cli_common
from iapetus.cli.cli_console_and_path_helpers import console

labels_app = typer.Typer(help="Label rendering helpers.")
snapshot_app = typer.Typer(help="Snapshot helpers.")

def _run_demo_snapshot_summary() -> None:
    try:
        snapshot = build_demo_snapshot()
    except Exception as exc:
        console.print(f"[red]Demo snapshot preview failed: {exc}[/red]")
        raise typer.Exit(code=1)

    console.print("manifest.json")
    console.print("entities.json")
    console.print("labels.json")
    console.print(f"Name        : {snapshot.manifest.name}")
    console.print(f"Purpose     : {snapshot.manifest.purpose}")
    console.print(f"Entity count: {snapshot.manifest.entity_count}")


@labels_app.command("demo")
def labels_demo() -> None:
    """Print sample malware and normal app labels."""
    try:
        malware = MalwareLabel(
            platform="AndroidOS",
            malware_primary="Trojan",
            family="Anubis",
            variant="t",
            subtype="Banker",
        )
        normal = NormalAppLabel(
            platform="AndroidOS",
            app_name="Facebook",
            build_ref="64543615",
            app_category="SocialMedia",
        )
        console.print(render_malware_label(malware))
        console.print(render_normal_app_label(normal))
    except Exception as exc:
        console.print(f"[red]Label demo failed: {exc}[/red]")
        raise typer.Exit(code=1)


@snapshot_app.command("demo")
def snapshot_demo(
    write: bool = typer.Option(False, "--write", help="Write manifest.json, entities.json, and labels.json."),
    use_curated: bool = typer.Option(
        False,
        "--use-curated",
        help="Build snapshot from curated static-analysis fixtures.",
    ),
    output_dir: Path | None = None,
    name: str | None = None,
    purpose: str | None = None,
) -> None:
    """Print a demo or curated snapshot manifest and rendered labels."""
    if output_dir is None:
        output_dir = cli_common.CURATED_SNAPSHOT_DIR if use_curated else cli_common.DEMO_OUTPUT_DIR
    if name is None:
        name = "m3.5-curated-snapshot" if use_curated else "m1-demo-snapshot"
    if purpose is None:
        purpose = (
            "Curated fixture snapshot with static-analysis-shaped entities."
            if use_curated
            else "M1 demo snapshot containing seed entities and rendered labels."
        )

    if not name.strip():
        console.print("[red]Snapshot name cannot be empty.[/red]")
        raise typer.Exit(code=1)

    try:
        snapshot = build_curated_snapshot(name=name, purpose=purpose) if use_curated else build_demo_snapshot(
            name=name,
            purpose=purpose,
        )
    except Exception as exc:
        console.print(f"[red]Failed to build snapshot: {exc}[/red]")
        raise typer.Exit(code=1)

    if write:
        if output_dir.exists() and not output_dir.is_dir():
            console.print(f"[red]Output path is not a directory: {output_dir}[/red]")
            raise typer.Exit(code=1)
        try:
            snapshot_output(snapshot, output_dir=output_dir, write_curated_extras=use_curated)
        except OSError as exc:
            console.print(f"[red]Could not write snapshot files: {exc}[/red]")
            raise typer.Exit(code=1)

    console.print("[bold]Snapshot manifest[/bold]")
    console.print(snapshot.manifest.model_dump_json(indent=2))
    console.print("[bold]Labels[/bold]")
    for value in snapshot.labels:
        console.print(value)
    if write:
        console.print(f"[green]Wrote files to: {output_dir}[/green]")

