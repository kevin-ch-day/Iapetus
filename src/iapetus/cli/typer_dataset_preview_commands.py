"""Dataset schema preview commands."""
from __future__ import annotations

import json

import typer

from iapetus.curated_fixture_analysis import fixture_record, resolve_fixture

from iapetus.cli.cli_console_and_path_helpers import console

dataset_app = typer.Typer(help="Dataset helpers.")

def _run_dataset_shape_preview() -> None:
    console.print("[bold]DATASET SHAPE PREVIEW[/bold]")
    for item in [
        "entities (fixture_slug, package_name, rendered_label)",
        "labeled_entities (identity + label)",
        "entity_token_groups (permissions, components, intents, ...)",
        "entity_features (toy boolean/count feature row)",
        "permission observations",
        "static features",
        "dynamic windows",
        "AV tokens",
        "review decisions",
        "training examples",
    ]:
        console.print(f"- {item}")
    try:
        from iapetus.curated_fixture_analysis import build_entity_features, extract_fixture_token_groups

        sample = resolve_fixture("malware_banker")
        record = fixture_record(sample)
        groups = extract_fixture_token_groups(sample)
        example = build_entity_features(record, groups)
        console.print("[bold]Example entity_features row (malware_banker)[/bold]")
        console.print(json.dumps(example, indent=2))
    except Exception as exc:
        console.print(f"[yellow]Could not load example feature row: {exc}[/yellow]")


@dataset_app.command("shape")
def dataset_shape() -> None:
    """Print a future dataset schema preview."""
    _run_dataset_shape_preview()
