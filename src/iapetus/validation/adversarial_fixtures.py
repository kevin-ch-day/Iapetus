from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from iapetus.data_library import load_fixture_seed
from iapetus.validation.fixture_quality import (
    FixtureQualityResult,
    build_training_quality_contract,
    classify_fixture_quality_issues,
    collect_android_markers,
    collect_windows_markers,
    validate_fixture_quality,
)

BadFixtureValidation = FixtureQualityResult
_BAD_FIXTURE_RELATIVE = Path("tests/fixtures/android_bad_fixture_samples_seed.json")


def bad_fixture_seed_path() -> Path:
    cwd_candidate = Path.cwd() / _BAD_FIXTURE_RELATIVE
    if cwd_candidate.is_file():
        return cwd_candidate
    module_root = Path(__file__).resolve().parents[3]
    packaged = module_root / _BAD_FIXTURE_RELATIVE
    if packaged.is_file():
        return packaged
    return cwd_candidate


def load_bad_fixtures() -> list[dict[str, Any]]:
    path = bad_fixture_seed_path()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Adversarial fixture seed not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid adversarial fixture JSON in {path}: {exc}") from exc

    if not isinstance(payload, dict):
        raise ValueError("Adversarial fixture seed must be a JSON object with a fixtures array.")
    if payload.get("fixture_set") != "adversarial_test":
        raise ValueError("Adversarial fixture seed is missing fixture_set=adversarial_test marker.")
    fixtures = payload.get("fixtures")
    if not isinstance(fixtures, list):
        raise ValueError("Adversarial fixture seed must include a fixtures list.")
    return [item for item in fixtures if isinstance(item, dict)]


def resolve_bad_fixture(fixture_key: str) -> dict[str, Any]:
    normalized = fixture_key.strip().lower().replace("-", "_")
    for item in load_bad_fixtures():
        slug = str(item.get("fixture_slug", "")).strip().lower()
        sample_id = str(item.get("sample_id", "")).strip().lower()
        if slug == normalized or sample_id == normalized or sample_id.replace("-", "_") == normalized:
            return item
    raise KeyError(f"Unknown adversarial fixture '{fixture_key}'")


def classify_bad_data_issues(fixture: dict[str, Any]) -> list[str]:
    return classify_fixture_quality_issues(fixture)


def validate_bad_fixture(fixture: dict[str, Any]) -> BadFixtureValidation:
    result = validate_fixture_quality(fixture)
    return BadFixtureValidation(
        fixture_slug=result.fixture_slug,
        sample_id=result.sample_id,
        sample_name=result.sample_name,
        issues=result.issues,
        messages=result.messages,
        severity=result.severity,
        training_eligible=result.training_eligible,
        training_blockers=result.training_blockers,
    )


def validate_curated_fixtures_quality() -> list[FixtureQualityResult]:
    return [validate_fixture_quality(item) for item in load_fixture_seed()]


def audit_adversarial_coverage() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for fixture in load_bad_fixtures():
        detected = classify_fixture_quality_issues(fixture)
        detected_clean = [issue for issue in detected if issue != "low_confidence_unknown"]
        expected = [str(item) for item in fixture.get("expected_issues", [])]
        missing = [issue for issue in expected if issue not in detected_clean]
        unexpected = [issue for issue in detected_clean if issue not in expected]
        rows.append(
            {
                "fixture_slug": fixture.get("fixture_slug"),
                "expected_issues": expected,
                "detected_issues": detected_clean,
                "missing_expected": missing,
                "unexpected_extra": unexpected,
                "coverage_ok": not missing,
            }
        )
    curated = validate_curated_fixtures_quality()
    curated_blockers = [item for item in curated if not item.training_eligible]
    return {
        "adversarial_rows": rows,
        "adversarial_coverage_ok": all(row["coverage_ok"] for row in rows),
        "curated_fixture_count": len(curated),
        "curated_training_eligible_count": sum(1 for item in curated if item.training_eligible),
        "curated_with_blockers": [item.fixture_slug for item in curated_blockers],
        "curated_quality_ok": not curated_blockers,
        "training_quality_contract": build_training_quality_contract(),
    }


def summarize_bad_fixture_results() -> dict[str, Any]:
    validations = [validate_bad_fixture(item) for item in load_bad_fixtures()]
    issue_counts: dict[str, int] = {}
    for result in validations:
        for issue in result.issues:
            issue_counts[issue] = issue_counts.get(issue, 0) + 1
    audit = audit_adversarial_coverage()
    return {
        "fixture_set": "adversarial_test",
        "fixture_count": len(validations),
        "not_training_truth": True,
        "validations": [item.to_dict() for item in validations],
        "issue_counts": issue_counts,
        "excluded_from_default_learning": True,
        "adversarial_coverage_ok": audit["adversarial_coverage_ok"],
        "curated_quality_ok": audit["curated_quality_ok"],
        "training_quality_contract": audit["training_quality_contract"],
    }


def explain_bad_fixture(fixture_key: str) -> dict[str, Any]:
    fixture = resolve_bad_fixture(fixture_key)
    validation = validate_bad_fixture(fixture)
    remediation: list[str] = []
    if "malformed_permission" in validation.issues:
        remediation.append("Map permissions to canonical android.permission.NAME strings from permission seed.")
    if "entity_kind_label_conflict" in validation.issues:
        remediation.append("Align sample_type, labels payload, and rendered_label to the same entity contract.")
    if "windows_artifact_in_android_context" in validation.issues:
        remediation.append("Do not ingest this row as Android malware; route to PE/Windows analysis path instead.")
    if "contradictory_context" in validation.issues or "suspicious_overclaim" in validation.issues:
        remediation.append("Keep as review-only unless analyst confirms benign; do not auto-label for training.")
    return {
        "fixture_slug": validation.fixture_slug,
        "sample_name": validation.sample_name,
        "issues": validation.issues,
        "messages": validation.messages,
        "severity": validation.severity,
        "training_eligible": validation.training_eligible,
        "training_blockers": validation.training_blockers,
        "android_markers": collect_android_markers(fixture),
        "windows_markers": collect_windows_markers(fixture),
        "remediation_hints": remediation,
        "explanation": (
            f"Adversarial test fixture '{validation.fixture_slug}' is for hardening only. "
            f"Detected issues: {', '.join(validation.issues) or 'none'}. "
            + " ".join(validation.messages)
        ).strip(),
        "not_training_truth": True,
    }


def compare_bad_to_good(bad_key: str, good_key: str) -> dict[str, Any]:
    from iapetus.fixture_analysis import fixture_record, resolve_fixture

    bad = resolve_bad_fixture(bad_key)
    good_raw = resolve_fixture(good_key)
    good = fixture_record(good_raw)
    bad_validation = validate_bad_fixture(bad)
    good_validation = validate_fixture_quality(good_raw)

    return {
        "bad_fixture_slug": bad_validation.fixture_slug,
        "good_fixture_slug": good["fixture_slug"],
        "bad_issues": bad_validation.issues,
        "good_issues": good_validation.issues,
        "good_training_eligible": good_validation.training_eligible,
        "android_like_on_bad": collect_android_markers(bad),
        "windows_like_on_bad": collect_windows_markers(bad),
        "android_like_on_good": collect_android_markers(good),
        "windows_like_on_good": collect_windows_markers(good),
        "good_rendered_label": good.get("rendered_label", ""),
        "interpretation": (
            f"Good fixture '{good['fixture_slug']}' is training-eligible={good_validation.training_eligible}. "
            f"Bad fixture '{bad_validation.fixture_slug}' has blockers: {', '.join(bad_validation.training_blockers) or 'none'}. "
            "Do not treat the spoofed sample as Android malware training data. "
            f"Good reference label: {good.get('rendered_label', '')}."
        ),
    }
