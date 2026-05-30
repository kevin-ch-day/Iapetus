from __future__ import annotations

from typer.testing import CliRunner

from iapetus.cli import app
from iapetus.validation.edge_cases import load_edge_case_fixtures, run_edge_case_analysis
from iapetus.validation.fixture_quality import validate_fixture_quality


def test_edge_case_fixture_count() -> None:
    assert len(load_edge_case_fixtures()) >= 12


def test_edge_case_analysis_matches_expectations() -> None:
    report = run_edge_case_analysis()
    assert report["all_match_expectations"] is True
    assert report["surprise_count"] == 0


def test_duplicate_permissions_blocked() -> None:
    fixture = next(
        item for item in load_edge_case_fixtures() if item["fixture_slug"] == "edge_duplicate_permissions"
    )
    result = validate_fixture_quality(fixture)
    assert result.training_eligible is False
    assert "malformed_permission" in result.issues


def test_empty_permissions_blocked() -> None:
    fixture = next(item for item in load_edge_case_fixtures() if item["fixture_slug"] == "edge_empty_permissions")
    result = validate_fixture_quality(fixture)
    assert result.training_eligible is False


def test_bad_data_edge_cases_cli() -> None:
    result = CliRunner().invoke(app, ["bad-data", "edge-cases"])
    assert result.exit_code == 0
    assert "edge_normal_malware_rendered" in result.stdout
    assert "SURPRISE" not in result.stdout
