"""Android fixture helpers."""
from __future__ import annotations

import typer

from iapetus.curated_fixture_analysis import extract_fixture_token_groups, resolve_fixture

from iapetus.cli.cli_console_and_path_helpers import console, print_token_group

android_app = typer.Typer(help="Android fixture static-analysis helpers.")


def _run_android_tokens(fixture: str) -> None:
    try:
        item = resolve_fixture(fixture)
        groups = extract_fixture_token_groups(item)
    except KeyError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1)
    console.print("[bold]Fixture token groups[/bold]")
    console.print(f"Fixture: {groups['fixture_slug']}")
    print_token_group("permissions", groups["permissions"])
    print_token_group("components", groups["components"])
    print_token_group("intent_filters", groups["intent_filters"])
    print_token_group("manifest_flags", groups["manifest_flags"])
    print_token_group("network_strings", groups["network_strings"])
    print_token_group("code_strings", groups["code_strings"])
    print_token_group("suspicious_indicators", groups["suspicious_indicators"])
    print_token_group("label_tokens", groups["label_tokens"])


@android_app.command("tokens")
def android_tokens(
    fixture: str = typer.Option(..., "--fixture", help="Fixture slug (e.g. malware_banker)."),
) -> None:
    """Show grouped static-analysis tokens for a curated fixture."""
    _run_android_tokens(fixture=fixture)
