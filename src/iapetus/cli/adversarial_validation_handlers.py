"""Handlers for adversarial / bad-data validation commands."""
from __future__ import annotations

import json

import typer

import iapetus.cli.cli_console_and_path_helpers as cli_common
from iapetus.cli.cli_console_and_path_helpers import console
from iapetus.validation import (
    audit_adversarial_coverage,
    build_gap_report,
    compare_bad_to_good,
    explain_bad_fixture,
    load_bad_fixtures,
    resolve_bad_fixture,
    run_edge_case_analysis,
    run_regex_audit,
    run_stress_probe,
    summarize_bad_fixture_results,
    validate_curated_fixtures_quality,
)


def _run_bad_data_list() -> None:
    console.print("[bold]Adversarial test fixtures[/bold] (not training truth)")
    for item in load_bad_fixtures():
        slug = item.get("fixture_slug", item.get("sample_name"))
        console.print(f"- {slug}: {item.get('sample_name')}")


def _run_bad_data_validate() -> None:
    summary = summarize_bad_fixture_results()
    console.print("[bold]Bad-data validation[/bold]")
    console.print(f"Fixture count: {summary['fixture_count']}")
    console.print(f"Excluded from default learning: {summary['excluded_from_default_learning']}")
    console.print(f"Adversarial coverage OK: {summary.get('adversarial_coverage_ok')}")
    console.print(f"Curated quality OK: {summary.get('curated_quality_ok')}")
    for entry in summary["validations"]:
        issues = ", ".join(entry["issues"])
        console.print(
            f"- {entry['fixture_slug']} [{entry['severity']}] "
            f"eligible={entry.get('training_eligible', False)}: {issues}"
        )


def _run_bad_data_audit() -> None:
    audit = audit_adversarial_coverage()
    console.print("[bold]Adversarial coverage audit[/bold]")
    console.print(f"Coverage OK: {audit['adversarial_coverage_ok']}")
    for row in audit["adversarial_rows"]:
        status = "OK" if row["coverage_ok"] else "GAP"
        console.print(f"[{status}] {row['fixture_slug']}")
        if row["missing_expected"]:
            console.print(f"  missing expected: {', '.join(row['missing_expected'])}")
        if row["unexpected_extra"]:
            console.print(f"  unexpected extra: {', '.join(row['unexpected_extra'])}")
    console.print(
        f"Curated training-eligible: {audit['curated_training_eligible_count']}/"
        f"{audit['curated_fixture_count']}"
    )
    if audit["curated_with_blockers"]:
        console.print(f"Curated blockers: {', '.join(audit['curated_with_blockers'])}")


def _run_bad_data_regex_audit() -> None:
    report = run_regex_audit()
    console.print("[bold]Regex audit[/bold]")
    console.print(
        f"Label slips: {report['label_slip_count']}  "
        f"Permission slips: {report['permission_slip_count']}  "
        f"Package slips: {report['package_slip_count']}  "
        f"Consistency slips: {report['consistency_slip_count']}"
    )
    for row in report["label_probes"]:
        if row["slipped"]:
            console.print(f"[SLIP] label {row['probe']}: {row['detail']}")
    for row in report["permission_probes"]:
        if row["slipped"]:
            console.print(f"[SLIP] permission {row['probe']}: {row['detail']}")
    for row in report["package_probes"]:
        if row["slipped"]:
            console.print(f"[SLIP] package {row['probe']}: {row['detail']}")
    for row in report["rendered_consistency_probes"]:
        if row["slipped"]:
            console.print(f"[SLIP] consistency {row['probe']}: {row['rendered']}")
    if not report["all_ok"]:
        raise typer.Exit(code=1)
    console.print("All regex probes passed.")


def _run_bad_data_probe() -> None:
    report = run_stress_probe()
    console.print("[bold]Synthetic stress probe[/bold]")
    console.print(f"Probes: {report['probe_count']}")
    console.print(f"Slips (wrongly eligible): {report['slip_count']}")
    for row in report["probes"]:
        status = "SLIP" if row["slipped"] else "OK"
        console.print(f"[{status}] {row['probe']}: {', '.join(row['issues']) or 'none'}")
    if not report["all_blocked"]:
        raise typer.Exit(code=1)


def _run_bad_data_gaps(*, write: bool = False) -> None:
    report = build_gap_report()
    console.print("[bold]Bad-data gap report[/bold]")
    for hole in report["open_holes"]:
        console.print(f"- {hole}")
    if report["adversarial_wrongly_eligible"]:
        console.print("Wrongly eligible adversarial:")
        for slug in report["adversarial_wrongly_eligible"]:
            console.print(f"- {slug}")
    if write:
        cli_common.GENERATED_DIR.mkdir(parents=True, exist_ok=True)
        out_path = cli_common.GENERATED_DIR / "gap_report.json"
        out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        console.print(f"Wrote {out_path}")
    has_holes = any(
        hole != "No open holes detected by current seed rules." for hole in report["open_holes"]
    )
    if has_holes or report["adversarial_wrongly_eligible"]:
        raise typer.Exit(code=1)


def _run_bad_data_check_good() -> None:
    results = validate_curated_fixtures_quality()
    console.print("[bold]Curated fixture quality (training eligibility)[/bold]")
    for item in results:
        flag = "eligible" if item.training_eligible else "BLOCKED"
        console.print(f"- {item.fixture_slug}: {flag}")
        if item.training_blockers:
            console.print(f"    blockers: {', '.join(item.training_blockers)}")
    blocked = [item.fixture_slug for item in results if not item.training_eligible]
    if blocked:
        raise typer.Exit(code=1)


def _run_bad_data_show(fixture: str) -> None:
    try:
        item = resolve_bad_fixture(fixture)
    except KeyError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1)
    console.print("[bold]Adversarial fixture (raw)[/bold]")
    console.print(json.dumps(item, indent=2))


def _run_bad_data_explain(fixture: str) -> None:
    try:
        detail = explain_bad_fixture(fixture)
    except KeyError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1)
    console.print("[bold]Bad-data explanation[/bold]")
    console.print(f"Fixture: {detail['fixture_slug']}")
    console.print(f"Severity: {detail['severity']}")
    console.print(f"Issues: {', '.join(detail['issues'])}")
    if detail.get("android_markers"):
        console.print(f"Android-like markers: {', '.join(detail['android_markers'])}")
    if detail.get("windows_markers"):
        console.print(f"Windows-like markers: {', '.join(detail['windows_markers'])}")
    for message in detail.get("messages", []):
        console.print(f"- {message}")
    for hint in detail.get("remediation_hints", []):
        console.print(f"Remediation: {hint}")
    console.print(f"Training eligible: {detail.get('training_eligible', False)}")
    console.print(detail["explanation"])


def _run_bad_data_compare_good(bad: str, good: str) -> None:
    try:
        detail = compare_bad_to_good(bad, good)
    except KeyError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1)
    console.print("[bold]Bad vs good fixture comparison[/bold]")
    console.print(f"Bad : {detail['bad_fixture_slug']} ({', '.join(detail['bad_issues'])})")
    console.print(f"Good: {detail['good_fixture_slug']}")
    console.print(f"Android-like on bad : {', '.join(detail['android_like_on_bad']) or '(none)'}")
    console.print(f"Windows-like on bad : {', '.join(detail['windows_like_on_bad']) or '(none)'}")
    console.print(f"Android-like on good: {', '.join(detail['android_like_on_good']) or '(none)'}")
    console.print(detail["interpretation"])


def _run_bad_data_edge_cases() -> None:
    report = run_edge_case_analysis()
    console.print("[bold]Edge-case analysis[/bold]")
    console.print(f"Cases: {report['case_count']}  Matched expectations: {report['coverage_ok_count']}")
    for row in report["cases"]:
        flag = "OK" if row["coverage_ok"] else "SURPRISE"
        eligible = "eligible" if row["training_eligible"] else "BLOCKED"
        console.print(
            f"[{flag}] {row['fixture_slug']}: {eligible} issues={', '.join(row['detected_issues']) or 'none'}"
        )
        if row["description"]:
            console.print(f"    {row['description']}")
        if row["observe_note"]:
            console.print(f"    [dim]Note: {row['observe_note']}[/dim]")
        if not row["coverage_ok"]:
            if row["missing_expected"]:
                console.print(f"    missing: {', '.join(row['missing_expected'])}")
            if row["unexpected_extra"]:
                console.print(f"    unexpected: {', '.join(row['unexpected_extra'])}")
            if row["expected_training_eligible"] is not None and not row["eligible_match"]:
                console.print(
                    f"    eligibility: expected {row['expected_training_eligible']} "
                    f"got {row['training_eligible']}"
                )
    if report["observe_only_cases"]:
        console.print("[bold]Observe-only (documented lenient behavior)[/bold]")
        for item in report["observe_only_cases"]:
            console.print(f"- {item['fixture_slug']}: {item['note']}")
    if not report["all_match_expectations"]:
        raise typer.Exit(code=1)
