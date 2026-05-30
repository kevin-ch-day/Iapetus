"""Curated data library commands."""
from __future__ import annotations

import typer

from iapetus.curated_seed_library_exports import (
    SOURCE_MANIFEST_PATH,
    build_token_summary,
    list_source_manifests,
    seed_summary,
    validate_seed_payloads,
)

from iapetus.cli.cli_console_and_path_helpers import console

data_app = typer.Typer(help="Data library helpers.")

def _run_data_sources() -> None:
    try:
        sources = list_source_manifests()
    except Exception as exc:
        console.print(f"[red]Could not load source manifests: {exc}[/red]")
        raise typer.Exit(code=1)

    console.print("[bold]DATA SOURCES[/bold]")
    if not sources:
        console.print("No sources configured.")
        return

    for source in sources:
        console.print(f"- {source.source_id} [{source.source_kind}, {source.trusted_level}]")
        console.print(f"  name     : {source.source_name}")
        console.print(f"  url      : {source.source_url}")
        console.print(f"  local    : {source.local_path}")
        console.print(f"  retrieved: {source.retrieved_at}")


def _run_data_manifest() -> None:
    if not SOURCE_MANIFEST_PATH.exists():
        console.print(f"Source manifest file not found: {SOURCE_MANIFEST_PATH}")
        return
    console.print(SOURCE_MANIFEST_PATH.read_text(encoding="utf-8"))


def _run_data_seed_summary() -> None:
    counts = seed_summary()
    console.print("[bold]seed summary[/bold]")
    console.print(f"permission seed count   : {counts['permission_seed_count']}")
    console.print(f"static token seed count : {counts['static_token_seed_count']}")
    console.print(f"fixture sample count    : {counts['fixture_sample_count']}")
    console.print(f"source manifest count   : {counts['source_manifest_count']}")


def _run_data_token_summary() -> None:
    summary = build_token_summary()
    console.print("[bold]token summary[/bold]")
    console.print("permissions by category:")
    for key, value in sorted(summary["permissions_by_category"].items()):
        console.print(f"- {key}: {value}")
    console.print("permissions by rough_risk:")
    for key, value in sorted(summary["permissions_by_rough_risk"].items()):
        console.print(f"- {key}: {value}")
    console.print("static tokens by token_type:")
    for key, value in sorted(summary["static_tokens_by_token_type"].items()):
        console.print(f"- {key}: {value}")
    console.print("fixture samples by entity_kind:")
    for key, value in sorted(summary["fixture_samples_by_entity_kind"].items()):
        console.print(f"- {key}: {value}")
    console.print("fixture samples by expected_classification:")
    for key, value in sorted(summary["fixture_samples_by_expected_classification"].items()):
        console.print(f"- {key}: {value}")
    suspicious = summary.get("suspicious_indicator_counts", {})
    if suspicious:
        console.print("suspicious indicators:")
        for key, value in sorted(suspicious.items()):
            console.print(f"- {key}: {value}")
    else:
        console.print("suspicious indicators: none")


def _run_data_validate() -> None:
    ok, issues, counts = validate_seed_payloads()
    if not ok:
        console.print("[red]data validation failed[/red]")
        for issue in issues:
            console.print(f"- {issue}")
        raise typer.Exit(code=1)

    console.print("[green]data validation passed[/green]")
    console.print(f"permission seeds : {counts['permission_seed_count']}")
    console.print(f"static tokens   : {counts['static_token_seed_count']}")
    console.print(f"fixture samples : {counts['fixture_sample_count']}")
    console.print(f"source manifests: {counts['source_manifest_count']}")


@data_app.command("sources")
def data_sources() -> None:
    """List configured source manifests."""
    _run_data_sources()


@data_app.command("manifest")
def data_manifest() -> None:
    """Show source manifest JSON."""
    _run_data_manifest()


@data_app.command("seed-summary")
def data_seed_summary() -> None:
    """Show curated seed counts."""
    _run_data_seed_summary()


@data_app.command("token-summary")
def data_token_summary() -> None:
    """Show seed token and fixture summary."""
    _run_data_token_summary()


@data_app.command("validate")
def data_validate() -> None:
    """Validate curated seed files and source manifests."""
    _run_data_validate()
