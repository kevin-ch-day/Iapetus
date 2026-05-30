from __future__ import annotations

from typing import Any

from iapetus.data_library import load_fixture_seed
from iapetus.fixture_analysis import render_fixture_label
from iapetus.labels.renderer import render_malware_label, render_normal_app_label
from iapetus.validation.fixture_quality import (
    _MALWARE_LABEL_RE,
    _NORMAL_LABEL_RE,
    classify_fixture_quality_issues,
    is_canonical_permission,
    label_structure_issues,
    package_name_issues,
    validate_fixture_quality,
)


def _probe_row(
    name: str,
    *,
    expect_valid: bool,
    actual_valid: bool,
    detail: str = "",
) -> dict[str, Any]:
    slipped = actual_valid != expect_valid
    return {
        "probe": name,
        "expect_valid": expect_valid,
        "actual_valid": actual_valid,
        "slipped": slipped,
        "detail": detail,
    }


def label_regex_probes() -> list[tuple[str, str, bool]]:
    return [
        ("good_malware", "AndroidOS:Trojan.Anubis-t:[Banker]", True),
        ("good_normal", "AndroidOS:Facebook-1:[SocialMedia]", True),
        ("empty_family_dot", "AndroidOS:Trojan..Anubis-t:[Banker]", False),
        ("empty_platform_segment", "AndroidOS::Trojan.Anubis-t:[Banker]", False),
        ("missing_variant_hyphen", "AndroidOS:Trojan.Anubis:[Banker]", False),
        ("unbracketed_subtype", "AndroidOS:Trojan.Anubis-t:Banker", False),
        ("wrong_platform", "WindowsOS:Trojan.Anubis-t:[Banker]", False),
        ("dot_in_app_name_only", "AndroidOS:Face.book-1:[Social]", False),
        ("ambiguous_double_match", "AndroidOS:Trojan..Anubis-t:[Banker]", False),
    ]


def permission_regex_probes() -> list[tuple[str, str, bool]]:
    return [
        ("good_read_sms", "android.permission.READ_SMS", True),
        ("lowercase_suffix", "android.permission.read_sms", False),
        ("wrong_prefix_case", "Android.permission.READ_SMS", False),
        ("empty_suffix", "android.permission.", False),
        ("embedded_space", "android.permission.READ SMS", False),
        ("typo_still_canonical_shape", "android.permission.READ_SMSS", True),
    ]


def package_regex_probes() -> list[tuple[str, str, bool]]:
    return [
        ("good_nested", "com.example.app", True),
        ("two_segments", "com.example", True),
        ("single_segment", "com", False),
        ("mixed_case", "Com.example.app", False),
        ("double_dot", "com..evil.app", False),
        ("trailing_dot", "com.example.app.", False),
        ("numeric_segment", "com.123.app", False),
        ("underscore_only_segment", "com._hidden.app", False),
    ]


def rendered_label_consistency_probes() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    malware_payload = {
        "platform": "AndroidOS",
        "malware_primary": "Trojan",
        "family": "Anubis",
        "variant": "t",
        "subtype": "Banker",
    }
    normal_payload = {
        "platform": "AndroidOS",
        "app_name": "Facebook",
        "build_ref": "1",
        "app_category": "SocialMedia",
    }
    for kind, rendered in (
        ("malware", render_malware_label(malware_payload)),
        ("normal_app", render_normal_app_label(normal_payload)),
    ):
        issues = label_structure_issues(rendered)
        malware_match = bool(_MALWARE_LABEL_RE.match(rendered))
        normal_match = bool(_NORMAL_LABEL_RE.match(rendered))
        exclusive = malware_match ^ normal_match
        rows.append(
            {
                "probe": f"renderer_{kind}",
                "rendered": rendered,
                "structure_ok": not issues,
                "regex_exclusive": exclusive,
                "slipped": bool(issues) or not exclusive,
            }
        )

    for item in load_fixture_seed():
        rendered = render_fixture_label(item)
        issues = label_structure_issues(rendered)
        malware_match = bool(_MALWARE_LABEL_RE.match(rendered))
        normal_match = bool(_NORMAL_LABEL_RE.match(rendered))
        slipped = bool(issues) or not (malware_match ^ normal_match)
        rows.append(
            {
                "probe": f"curated_{item.get('fixture_slug', 'unknown')}",
                "rendered": rendered,
                "structure_ok": not issues,
                "regex_exclusive": malware_match ^ normal_match,
                "slipped": slipped,
            }
        )
    return rows


def run_regex_audit() -> dict[str, Any]:
    label_rows: list[dict[str, Any]] = []
    for name, label, expect_ok in label_regex_probes():
        issues = label_structure_issues(label)
        actual_ok = not issues
        label_rows.append(
            _probe_row(
                name,
                expect_valid=expect_ok,
                actual_valid=actual_ok,
                detail=f"issues={issues}",
            )
        )

    permission_rows: list[dict[str, Any]] = []
    for name, permission, expect_ok in permission_regex_probes():
        actual_ok = is_canonical_permission(permission)
        permission_rows.append(
            _probe_row(name, expect_valid=expect_ok, actual_valid=actual_ok, detail=permission)
        )

    package_rows: list[dict[str, Any]] = []
    for name, package, expect_ok in package_regex_probes():
        actual_ok = not package_name_issues(package)
        package_rows.append(
            _probe_row(name, expect_valid=expect_ok, actual_valid=actual_ok, detail=package)
        )

    consistency_rows = rendered_label_consistency_probes()
    consistency_slips = [row["probe"] for row in consistency_rows if row["slipped"]]

    label_slips = [row["probe"] for row in label_rows if row["slipped"]]
    permission_slips = [row["probe"] for row in permission_rows if row["slipped"]]
    package_slips = [row["probe"] for row in package_rows if row["slipped"]]

    typo_fixture = {
        "sample_type": "normal_app",
        "platform": "AndroidOS",
        "package_name": "com.example.typo",
        "permissions": ["android.permission.INTERNET", "android.permission.READ_SMSS"],
        "labels": {
            "platform": "AndroidOS",
            "app_name": "Typo",
            "build_ref": "1",
            "app_category": "Utility",
        },
    }
    typo_issues = classify_fixture_quality_issues(typo_fixture)
    typo_slipped = "malformed_permission" not in typo_issues

    all_slips = label_slips + permission_slips + package_slips + consistency_slips
    if typo_slipped:
        all_slips.append("seed_typo_permission_detection")

    return {
        "label_probes": label_rows,
        "permission_probes": permission_rows,
        "package_probes": package_rows,
        "rendered_consistency_probes": consistency_rows,
        "label_slip_count": len(label_slips),
        "permission_slip_count": len(permission_slips),
        "package_slip_count": len(package_slips),
        "consistency_slip_count": len(consistency_slips),
        "slip_count": len(all_slips),
        "slips": all_slips,
        "all_ok": len(all_slips) == 0,
    }
