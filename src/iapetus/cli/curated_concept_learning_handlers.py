"""Concept-trainer and corpus explain handlers."""
from __future__ import annotations

import json
from pathlib import Path

import typer

from iapetus.curated_fixture_analysis import resolve_fixture
from iapetus.learning.curated_concept_trainer import absorb_curated_seed, compare_fixtures, explain_fixture, explain_token
from iapetus.learning.quality_gated_training_corpus import build_training_corpus
from iapetus.validation import (
    audit_adversarial_coverage,
    build_training_quality_contract,
    validate_fixture_quality,
)

import iapetus.cli.cli_console_and_path_helpers as cli_common
from iapetus.cli.cli_console_and_path_helpers import console, print_token_group

def _run_learn_absorb(generated_dir: Path | None = None) -> None:
    try:
        paths = absorb_curated_seed(generated_dir=generated_dir)
    except (OSError, ValueError) as exc:
        console.print(f"[red]Concept trainer absorb failed: {exc}[/red]")
        raise typer.Exit(code=1)
    root = generated_dir or cli_common.GENERATED_DIR
    root.mkdir(parents=True, exist_ok=True)
    contract = build_training_quality_contract()
    audit = audit_adversarial_coverage()
    (root / "training_quality_contract.json").write_text(json.dumps(contract, indent=2), encoding="utf-8")
    (root / "adversarial_coverage_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    console.print("[bold]Concept trainer absorb[/bold]")
    for label, path in paths.items():
        console.print(f"Wrote {label}: {path}")
    console.print(f"Wrote training_quality_contract: {root / 'training_quality_contract.json'}")
    console.print(f"Wrote adversarial_coverage_audit: {root / 'adversarial_coverage_audit.json'}")
    console.print(f"Adversarial coverage OK: {audit['adversarial_coverage_ok']}")
    corpus = build_training_corpus()
    console.print(
        f"Training corpus: {corpus['training_example_count']} examples "
        f"(avg quality {corpus['average_training_quality_score']})"
    )


def _run_learn_explain_token(token: str) -> None:
    try:
        detail = explain_token(token)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1)
    console.print("[bold]Token explanation[/bold]")
    console.print(f"Token: {detail['token']}")
    console.print(f"Kind: {detail['kind']}")
    console.print(f"Found in seed: {detail['found']}")
    console.print(detail["explanation"])
    if detail.get("rough_risk"):
        console.print(f"Rough risk: {detail['rough_risk']}")
    if detail.get("token_type"):
        console.print(f"Token type: {detail['token_type']}")
    if detail.get("meaning"):
        console.print(f"Meaning: {detail['meaning']}")
    if detail.get("suspicious_when"):
        console.print(f"Suspicious when: {detail['suspicious_when']}")
    fixture_keys = detail.get("fixture_keys") or []
    if fixture_keys:
        console.print("Fixture usage:")
        for key in fixture_keys:
            console.print(f"- {key}")
    concepts = detail.get("related_concepts") or []
    if concepts:
        console.print(f"Related concepts: {', '.join(concepts)}")


def _run_learn_explain_fixture(fixture: str) -> None:
    try:
        detail = explain_fixture(fixture)
        quality = validate_fixture_quality(resolve_fixture(fixture))
    except KeyError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1)
    console.print("[bold]Fixture explanation[/bold]")
    console.print(f"Fixture: {detail['fixture_slug']}")
    console.print(f"Sample ID: {detail['sample_id']}")
    console.print(f"Package: {detail.get('package_name') or '(none)'}")
    console.print(f"Display name: {detail.get('display_name') or '(none)'}")
    console.print(f"Kind: {detail['entity_kind']}")
    console.print(f"Expected classification: {detail['expected_classification']}")
    console.print(f"Label: {detail['rendered_label']}")
    console.print("Permissions:")
    for entry in detail.get("permissions_detail", []):
        console.print(
            f"- {entry['permission']} ({entry['rough_risk']}, {entry['category']}): {entry['notes']}"
        )
    groups = detail.get("token_groups", {})
    print_token_group("components", groups.get("components", []))
    print_token_group("intent_filters", groups.get("intent_filters", []))
    print_token_group("manifest_flags", groups.get("manifest_flags", []))
    print_token_group("network_strings", groups.get("network_strings", []))
    print_token_group("code_strings", groups.get("code_strings", []))
    print_token_group("suspicious_indicators", groups.get("suspicious_indicators", []))
    console.print("[bold]Interpretation[/bold]")
    console.print(detail.get("interpretation", ""))
    console.print(f"Training eligible: {quality.training_eligible}")
    if quality.training_blockers:
        console.print(f"Training blockers: {', '.join(quality.training_blockers)}")


def _run_learn_compare_fixtures(left: str, right: str) -> None:
    try:
        detail = compare_fixtures(left, right)
    except KeyError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1)
    console.print("[bold]Fixture comparison[/bold]")
    console.print(
        f"Left : {detail['left']['fixture_slug']} "
        f"({detail['left']['entity_kind']}/{detail['left']['expected_classification']})"
    )
    console.print(
        f"Right: {detail['right']['fixture_slug']} "
        f"({detail['right']['entity_kind']}/{detail['right']['expected_classification']})"
    )
    print_token_group("Shared permissions", detail["shared_permissions"])
    print_token_group("Only left permissions", detail["only_left_permissions"])
    print_token_group("Only right permissions", detail["only_right_permissions"])
    print_token_group("Only left static tokens", detail["only_left_static_tokens"])
    print_token_group("Only right static tokens", detail["only_right_static_tokens"])
    print_token_group("Only left intent filters", detail["only_left_intent_filters"])
    print_token_group("Only right intent filters", detail["only_right_intent_filters"])
    print_token_group("Only left suspicious indicators", detail["only_left_suspicious_indicators"])
    print_token_group("Only right suspicious indicators", detail["only_right_suspicious_indicators"])
    console.print("[bold]Interpretation[/bold]")
    console.print(detail.get("interpretation", ""))


def _run_learn_corpus() -> None:
    corpus = build_training_corpus()
    console.print("[bold]Training corpus (quality-gated)[/bold]")
    console.print(f"Examples: {corpus['training_example_count']} / {corpus['fixture_count']} fixtures")
    console.print(f"Malware: {corpus['malware_example_count']}  Benign: {corpus['normal_app_example_count']}")
    console.print(f"Quality score: avg {corpus['average_training_quality_score']}  "
                  f"min {corpus['min_training_quality_score']}  max {corpus['max_training_quality_score']}")
    console.print(f"Classifications: {', '.join(corpus['classifications'])}")
    for row in corpus["training_examples"]:
        console.print(
            f"  {row['fixture_slug']}: {row['entity_kind']} / {row['expected_classification']} "
            f"(score {row['training_quality_score']})"
        )
    if corpus["blocked_fixture_count"]:
        console.print(f"[yellow]Blocked: {corpus['blocked_fixture_count']}[/yellow]")


