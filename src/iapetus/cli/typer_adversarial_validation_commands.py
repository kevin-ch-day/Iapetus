"""Typer commands for adversarial / bad-data validation."""
from __future__ import annotations

import typer

from iapetus.cli.adversarial_validation_handlers import (
    _run_bad_data_audit,
    _run_bad_data_check_good,
    _run_bad_data_compare_good,
    _run_bad_data_edge_cases,
    _run_bad_data_explain,
    _run_bad_data_gaps,
    _run_bad_data_list,
    _run_bad_data_probe,
    _run_bad_data_regex_audit,
    _run_bad_data_show,
    _run_bad_data_validate,
)

bad_data_app = typer.Typer(help="Adversarial/bad-data validation (not training truth).")


@bad_data_app.command("list")
def bad_data_list() -> None:
    """List adversarial test fixtures."""
    _run_bad_data_list()


@bad_data_app.command("validate")
def bad_data_validate() -> None:
    """Validate all adversarial fixtures and print issue categories."""
    _run_bad_data_validate()


@bad_data_app.command("audit")
def bad_data_audit() -> None:
    """Audit adversarial expected-vs-detected issue coverage."""
    _run_bad_data_audit()


@bad_data_app.command("check-good")
def bad_data_check_good() -> None:
    """Verify curated good fixtures pass training quality gates."""
    _run_bad_data_check_good()


@bad_data_app.command("edge-cases")
def bad_data_edge_cases() -> None:
    """Run borderline fixtures and compare to expected validation outcomes."""
    _run_bad_data_edge_cases()


@bad_data_app.command("regex-audit")
def bad_data_regex_audit() -> None:
    """Run label/permission/package regex probes (must all match expectations)."""
    _run_bad_data_regex_audit()


@bad_data_app.command("probe")
def bad_data_probe() -> None:
    """Run synthetic bad-data stress probes (must all block training)."""
    _run_bad_data_probe()


@bad_data_app.command("gaps")
def bad_data_gaps(
    write: bool = typer.Option(False, "--write", help="Write gap_report.json under data/generated/."),
) -> None:
    """Summarize open validation holes across adversarial and stress probes."""
    _run_bad_data_gaps(write=write)


@bad_data_app.command("show")
def bad_data_show(
    fixture: str = typer.Option(..., "--fixture", help="Adversarial fixture slug."),
) -> None:
    """Show raw adversarial fixture fields."""
    _run_bad_data_show(fixture=fixture)


@bad_data_app.command("explain")
def bad_data_explain(
    fixture: str = typer.Option(..., "--fixture", help="Adversarial fixture slug."),
) -> None:
    """Explain why an adversarial fixture is invalid or contradictory."""
    _run_bad_data_explain(fixture=fixture)


@bad_data_app.command("compare-good")
def bad_data_compare_good(
    bad: str = typer.Option(..., "--bad", help="Adversarial fixture slug."),
    good: str = typer.Option(..., "--good", help="Curated good fixture slug."),
) -> None:
    """Compare adversarial fixture against a trusted curated fixture."""
    _run_bad_data_compare_good(bad=bad, good=good)
