from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from iapetus.validation.fixture_quality_report import classify_fixture_quality_issues, validate_fixture_quality

_EDGE_CASE_RELATIVE = Path("tests/fixtures/android_edge_case_samples_seed.json")


def edge_case_seed_path() -> Path:
    cwd_candidate = Path.cwd() / _EDGE_CASE_RELATIVE
    if cwd_candidate.is_file():
        return cwd_candidate
    module_root = Path(__file__).resolve().parents[3]
    packaged = module_root / _EDGE_CASE_RELATIVE
    if packaged.is_file():
        return packaged
    return cwd_candidate


def load_edge_case_fixtures() -> list[dict[str, Any]]:
    path = edge_case_seed_path()
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("fixture_set") != "edge_case_test":
        raise ValueError("Edge-case seed must set fixture_set=edge_case_test")
    fixtures = payload.get("fixtures")
    if not isinstance(fixtures, list):
        raise ValueError("Edge-case seed must include a fixtures list")
    return [item for item in fixtures if isinstance(item, dict)]


def analyze_edge_case(fixture: dict[str, Any]) -> dict[str, Any]:
    detected = classify_fixture_quality_issues(fixture)
    detected_clean = [issue for issue in detected if issue != "low_confidence_unknown"]
    validation = validate_fixture_quality(fixture)
    expected_issues = [str(item) for item in fixture.get("expected_issues", [])]
    expected_eligible = fixture.get("expected_training_eligible")
    missing = [issue for issue in expected_issues if issue not in detected_clean]
    unexpected = [issue for issue in detected_clean if issue not in expected_issues]
    eligible_match = (
        expected_eligible is None or validation.training_eligible == bool(expected_eligible)
    )
    return {
        "fixture_slug": fixture.get("fixture_slug"),
        "description": fixture.get("description", fixture.get("sample_name", "")),
        "observe_note": fixture.get("observe_note", ""),
        "expected_issues": expected_issues,
        "detected_issues": detected_clean,
        "missing_expected": missing,
        "unexpected_extra": unexpected,
        "expected_training_eligible": expected_eligible,
        "training_eligible": validation.training_eligible,
        "training_blockers": validation.training_blockers,
        "eligible_match": eligible_match,
        "coverage_ok": not missing and not unexpected and eligible_match,
    }


def run_edge_case_analysis() -> dict[str, Any]:
    rows = [analyze_edge_case(fixture) for fixture in load_edge_case_fixtures()]
    surprises = [
        row["fixture_slug"]
        for row in rows
        if not row["coverage_ok"]
    ]
    observe_only = [row for row in rows if row.get("observe_note")]
    return {
        "fixture_set": "edge_case_test",
        "case_count": len(rows),
        "coverage_ok_count": sum(1 for row in rows if row["coverage_ok"]),
        "surprise_count": len(surprises),
        "surprises": surprises,
        "all_match_expectations": len(surprises) == 0,
        "cases": rows,
        "observe_only_cases": [
            {"fixture_slug": row["fixture_slug"], "note": row["observe_note"], "detected": row["detected_issues"]}
            for row in observe_only
        ],
    }
