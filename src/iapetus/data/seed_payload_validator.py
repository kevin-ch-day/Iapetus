"""Validate curated seed JSON payloads."""
from __future__ import annotations

from pydantic import ValidationError

from iapetus.data.seed_data_models import SeedFixtureSample
from iapetus.data.curated_seed_loaders import load_fixture_seed, load_permission_seed, load_static_token_seed
from iapetus.data.reference_source_manifests import list_source_manifests


def validate_seed_payloads() -> tuple[bool, list[str], dict[str, int]]:
    issues: list[str] = []
    counts = {
        "permission_seed_count": 0,
        "static_token_seed_count": 0,
        "fixture_sample_count": 0,
        "source_manifest_count": 0,
    }
    try:
        permissions = load_permission_seed()
        for index, item in enumerate(permissions):
            missing = [field for field in ("permission", "category", "rough_risk") if field not in item]
            if missing:
                issues.append(f"android_permissions_seed.json item {index}: missing {missing}")
        counts["permission_seed_count"] = len(permissions)
    except Exception as exc:
        issues.append(str(exc))

    try:
        tokens = load_static_token_seed()
        for index, item in enumerate(tokens):
            missing = [field for field in ("token", "token_type", "meaning") if field not in item]
            if missing:
                issues.append(f"android_static_tokens_seed.json item {index}: missing {missing}")
        counts["static_token_seed_count"] = len(tokens)
    except Exception as exc:
        issues.append(str(exc))

    try:
        fixtures = load_fixture_seed()
        for index, item in enumerate(fixtures):
            try:
                sample = SeedFixtureSample.model_validate(item)
            except ValidationError as exc:
                issues.append(f"android_fixture_samples_seed.json item {index}: {exc}")
                continue
            if not sample.labels:
                issues.append(f"android_fixture_samples_seed.json item {index}: missing labels")
            if not sample.permissions:
                issues.append(f"android_fixture_samples_seed.json item {index}: missing permissions")
        counts["fixture_sample_count"] = len(fixtures)
        try:
            from iapetus.validation import validate_curated_fixtures_quality

            for quality in validate_curated_fixtures_quality():
                if not quality.training_eligible:
                    issues.append(
                        f"curated fixture {quality.fixture_slug}: not training-eligible "
                        f"({', '.join(quality.training_blockers)})"
                    )
        except Exception as exc:
            issues.append(f"curated quality probe failed: {exc}")
    except Exception as exc:
        issues.append(str(exc))

    try:
        manifests = list_source_manifests()
        counts["source_manifest_count"] = len(manifests)
    except Exception as exc:
        issues.append(str(exc))

    return (len(issues) == 0, issues, counts)
