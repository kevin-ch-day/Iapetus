from __future__ import annotations

from typer.testing import CliRunner

from iapetus.cli import app
from iapetus.validation import (
    audit_adversarial_coverage,
    build_gap_report,
    classify_bad_data_issues,
    load_bad_fixtures,
    run_stress_probe,
    summarize_bad_fixture_results,
    validate_bad_fixture,
    validate_curated_fixtures_quality,
    resolve_bad_fixture,
)


def test_bad_fixture_count_positive() -> None:
    fixtures = load_bad_fixtures()
    assert len(fixtures) > 0


def test_spoofed_windows_triggers_platform_or_windows_issue() -> None:
    fixture = resolve_bad_fixture("spoofed_windows_as_android")
    issues = classify_bad_data_issues(fixture)
    assert "platform_extension_conflict" in issues or "windows_artifact_in_android_context" in issues


def test_normal_app_with_malware_label_conflict() -> None:
    issues = classify_bad_data_issues(resolve_bad_fixture("normal_app_with_malware_label"))
    assert "entity_kind_label_conflict" in issues


def test_malware_with_social_label_conflict() -> None:
    issues = classify_bad_data_issues(resolve_bad_fixture("malware_with_social_label"))
    assert "entity_kind_label_conflict" in issues


def test_impossible_permission_format_malformed() -> None:
    issues = classify_bad_data_issues(resolve_bad_fixture("impossible_permission_format"))
    assert "malformed_permission" in issues


def test_bad_label_syntax_malformed() -> None:
    issues = classify_bad_data_issues(resolve_bad_fixture("bad_label_syntax"))
    assert "malformed_label" in issues


def test_suspicious_benign_overclaim() -> None:
    issues = classify_bad_data_issues(resolve_bad_fixture("suspicious_benign_overclaim"))
    assert "suspicious_overclaim" in issues


def test_validation_handles_blank_permission_without_crash() -> None:
    result = validate_bad_fixture(resolve_bad_fixture("impossible_permission_format"))
    assert result.fixture_slug == "impossible_permission_format"
    assert "malformed_permission" in result.issues


def test_summarize_bad_fixture_results() -> None:
    summary = summarize_bad_fixture_results()
    assert summary["fixture_count"] >= 11
    assert summary["excluded_from_default_learning"] is True


def test_bad_data_validate_cli() -> None:
    result = CliRunner().invoke(app, ["bad-data", "validate"])
    assert result.exit_code == 0
    assert "spoofed_windows_as_android" in result.stdout
    assert "malformed_permission" in result.stdout


def test_bad_data_explain_cli() -> None:
    result = CliRunner().invoke(
        app,
        ["bad-data", "explain", "--fixture", "normal_app_with_malware_label"],
    )
    assert result.exit_code == 0
    assert "entity_kind_label_conflict" in result.stdout


def test_bad_data_compare_good_cli() -> None:
    result = CliRunner().invoke(
        app,
        [
            "bad-data",
            "compare-good",
            "--bad",
            "spoofed_windows_as_android",
            "--good",
            "malware_banker",
        ],
    )
    assert result.exit_code == 0
    assert "malware_banker" in result.stdout
    assert "Windows" in result.stdout or "windows" in result.stdout


def test_contradictory_static_context_flags_overclaim() -> None:
    issues = classify_bad_data_issues(resolve_bad_fixture("contradictory_static_context"))
    assert "contradictory_context" in issues
    assert "suspicious_overclaim" in issues


def test_contradictory_static_context_blocks_training() -> None:
    result = validate_bad_fixture(resolve_bad_fixture("contradictory_static_context"))
    assert result.training_eligible is False
    assert "contradictory_context" in result.training_blockers


def test_new_adversarial_holes_detected() -> None:
    assert "malformed_permission" in classify_bad_data_issues(
        resolve_bad_fixture("permission_typo_otherwise_good")
    )
    assert "invalid_package_name" in classify_bad_data_issues(
        resolve_bad_fixture("invalid_package_name_case")
    )
    assert "entity_kind_label_conflict" in classify_bad_data_issues(
        resolve_bad_fixture("malware_missing_label_payload")
    )
    for slug in (
        "permission_typo_otherwise_good",
        "invalid_package_name_case",
        "malware_missing_label_payload",
    ):
        assert validate_bad_fixture(resolve_bad_fixture(slug)).training_eligible is False


def test_stress_probe_blocks_all_synthetic_bad_rows() -> None:
    report = run_stress_probe()
    assert report["all_blocked"] is True
    assert report["slip_count"] == 0


def test_gap_report_no_open_holes() -> None:
    report = build_gap_report()
    assert report["stress_probe_all_blocked"] is True
    assert report["adversarial_wrongly_eligible"] == []


def test_adversarial_coverage_audit_passes() -> None:
    audit = audit_adversarial_coverage()
    assert audit["adversarial_coverage_ok"] is True
    assert audit["curated_quality_ok"] is True


def test_curated_fixtures_are_training_eligible() -> None:
    results = validate_curated_fixtures_quality()
    assert len(results) == 12
    assert all(item.training_eligible for item in results)


def test_bad_data_audit_cli() -> None:
    result = CliRunner().invoke(app, ["bad-data", "audit"])
    assert result.exit_code == 0
    assert "Coverage OK: True" in result.stdout


def test_bad_data_check_good_cli() -> None:
    result = CliRunner().invoke(app, ["bad-data", "check-good"])
    assert result.exit_code == 0
    assert "eligible" in result.stdout


def test_bad_data_probe_cli() -> None:
    result = CliRunner().invoke(app, ["bad-data", "probe"])
    assert result.exit_code == 0
    assert "SLIP" not in result.stdout


def test_bad_data_gaps_cli() -> None:
    result = CliRunner().invoke(app, ["bad-data", "gaps"])
    assert result.exit_code == 0
    assert "No open holes" in result.stdout or "open holes" in result.stdout.lower()
