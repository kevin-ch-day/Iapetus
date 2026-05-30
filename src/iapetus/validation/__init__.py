"""Seed validation helpers (adversarial fixtures, data-quality probes)."""

from .fixture_quality import (
    FixtureQualityResult,
    build_training_quality_contract,
    classify_fixture_quality_issues,
    validate_fixture_quality,
)
from .gap_report import build_gap_report
from .edge_cases import analyze_edge_case, load_edge_case_fixtures, run_edge_case_analysis
from .regex_audit import run_regex_audit
from .stress_probe import run_stress_probe
from .adversarial_fixtures import (
    audit_adversarial_coverage,
    compare_bad_to_good,
    explain_bad_fixture,
    classify_bad_data_issues,
    load_bad_fixtures,
    resolve_bad_fixture,
    summarize_bad_fixture_results,
    validate_bad_fixture,
    validate_curated_fixtures_quality,
    BadFixtureValidation,
)

__all__ = [
    "FixtureQualityResult",
    "BadFixtureValidation",
    "analyze_edge_case",
    "build_gap_report",
    "load_edge_case_fixtures",
    "run_edge_case_analysis",
    "run_regex_audit",
    "run_stress_probe",
    "audit_adversarial_coverage",
    "build_training_quality_contract",
    "compare_bad_to_good",
    "explain_bad_fixture",
    "classify_bad_data_issues",
    "classify_fixture_quality_issues",
    "load_bad_fixtures",
    "resolve_bad_fixture",
    "summarize_bad_fixture_results",
    "validate_bad_fixture",
    "validate_curated_fixtures_quality",
    "validate_fixture_quality",
]
