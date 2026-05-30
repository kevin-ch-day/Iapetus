from __future__ import annotations

from typer.testing import CliRunner

from iapetus.cli import app
from iapetus.validation.fixture_quality_report import (
    _MALWARE_LABEL_RE,
    _NORMAL_LABEL_RE,
    label_structure_issues,
    package_name_issues,
)
from iapetus.validation.label_permission_regex_audit import run_regex_audit


def test_malware_and_normal_regex_are_mutually_exclusive_on_curated_shapes() -> None:
    malware = "AndroidOS:Trojan.Anubis-t:[Banker]"
    normal = "AndroidOS:Facebook-1:[SocialMedia]"
    assert _MALWARE_LABEL_RE.match(malware)
    assert not _NORMAL_LABEL_RE.match(malware)
    assert _NORMAL_LABEL_RE.match(normal)
    assert not _MALWARE_LABEL_RE.match(normal)


def test_double_dot_family_fails_label_structure() -> None:
    issues = label_structure_issues("AndroidOS:Trojan..Anubis-t:[Banker]")
    assert issues
    assert any("doubled" in item or "segment" in item for item in issues)


def test_empty_platform_segment_fails_label_structure() -> None:
    issues = label_structure_issues("AndroidOS::Trojan.Anubis-t:[Banker]")
    assert issues


def test_dot_in_app_name_fails_normal_shape() -> None:
    label = "AndroidOS:Face.book-1:[Social]"
    assert not _NORMAL_LABEL_RE.match(label)
    assert label_structure_issues(label)


def test_numeric_package_segment_rejected() -> None:
    assert package_name_issues("com.123.app") == ["invalid_package_name"]


def test_regex_audit_all_ok() -> None:
    report = run_regex_audit()
    assert report["all_ok"] is True
    assert report["slip_count"] == 0


def test_bad_data_regex_audit_cli() -> None:
    result = CliRunner().invoke(app, ["bad-data", "regex-audit"])
    assert result.exit_code == 0
    assert "All regex probes passed" in result.stdout
