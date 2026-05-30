from __future__ import annotations

from typing import Any

from iapetus.curated_seed_library_exports import load_fixture_seed
from iapetus.curated_fixture_analysis import fixture_record
from iapetus.validation.fixture_quality_report import validate_fixture_quality


def synthetic_bad_probes() -> list[tuple[str, dict[str, Any], bool]]:
    """(name, fixture_dict, should_block_training)."""
    good = fixture_record(load_fixture_seed()[0])
    return [
        ("empty_row", {}, True),
        (
            "missing_package_and_file",
            {
                "sample_type": "malware",
                "platform": "AndroidOS",
                "permissions": ["android.permission.INTERNET"],
                "labels": {
                    "platform": "AndroidOS",
                    "malware_primary": "Trojan",
                    "family": "X",
                    "variant": "a",
                    "subtype": "Banker",
                },
            },
            True,
        ),
        (
            "invalid_package_uppercase",
            {
                "sample_type": "normal_app",
                "platform": "AndroidOS",
                "package_name": "Com.Example.Bad",
                "permissions": ["android.permission.INTERNET"],
                "labels": {
                    "platform": "AndroidOS",
                    "app_name": "Bad",
                    "build_ref": "1",
                    "app_category": "SocialMedia",
                },
            },
            True,
        ),
        (
            "permission_typo_in_otherwise_good_row",
            {
                **good,
                "permissions": ["android.permission.INTERNET", "android.permission.READ_SMSS"],
            },
            True,
        ),
        (
            "banker_signals_on_normal_app",
            {
                "sample_type": "normal_app",
                "platform": "AndroidOS",
                "package_name": "com.example.banking.safe",
                "expected_classification": "MobileBanking",
                "permissions": [
                    "android.permission.READ_SMS",
                    "android.permission.RECEIVE_SMS",
                    "android.permission.BIND_ACCESSIBILITY_SERVICE",
                ],
                "suspicious_indicators": ["sms_intercept", "overlay_attack"],
                "labels": {
                    "platform": "AndroidOS",
                    "app_name": "SafeBank",
                    "build_ref": "1",
                    "app_category": "MobileBanking",
                },
            },
            True,
        ),
        (
            "malware_missing_label_payload",
            {
                "sample_type": "malware",
                "platform": "AndroidOS",
                "package_name": "com.evil.emptylabels",
                "permissions": ["android.permission.INTERNET"],
                "labels": {},
            },
            True,
        ),
        (
            "duplicate_permissions",
            {
                "sample_type": "normal_app",
                "platform": "AndroidOS",
                "package_name": "com.example.dup",
                "permissions": [
                    "android.permission.INTERNET",
                    "android.permission.INTERNET",
                ],
                "labels": {
                    "platform": "AndroidOS",
                    "app_name": "Dup",
                    "build_ref": "1",
                    "app_category": "Utility",
                },
            },
            True,
        ),
        (
            "empty_permissions",
            {
                "sample_type": "normal_app",
                "platform": "AndroidOS",
                "package_name": "com.example.noperm",
                "permissions": [],
                "labels": {
                    "platform": "AndroidOS",
                    "app_name": "NoPerm",
                    "build_ref": "1",
                    "app_category": "Utility",
                },
            },
            True,
        ),
        (
            "rendered_label_platform_mismatch",
            {
                "sample_type": "malware",
                "platform": "AndroidOS",
                "package_name": "com.evil.app",
                "rendered_label": "WindowsOS:Trojan.X-y:[Banker]",
                "permissions": ["android.permission.INTERNET"],
                "labels": {
                    "platform": "AndroidOS",
                    "malware_primary": "Trojan",
                    "family": "X",
                    "variant": "y",
                    "subtype": "Banker",
                },
            },
            True,
        ),
    ]


def run_stress_probe() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    slips: list[str] = []
    for name, fixture, should_block in synthetic_bad_probes():
        result = validate_fixture_quality(fixture)
        slipped = result.training_eligible and should_block
        if slipped:
            slips.append(name)
        rows.append(
            {
                "probe": name,
                "should_block_training": should_block,
                "training_eligible": result.training_eligible,
                "slipped": slipped,
                "issues": result.issues,
                "training_blockers": result.training_blockers,
            }
        )
    return {
        "probe_count": len(rows),
        "slip_count": len(slips),
        "slips": slips,
        "all_blocked": len(slips) == 0,
        "probes": rows,
    }
