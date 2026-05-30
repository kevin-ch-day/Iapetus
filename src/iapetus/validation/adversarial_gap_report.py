from __future__ import annotations

from typing import Any

from iapetus.validation.adversarial_fixture_validation import audit_adversarial_coverage, load_bad_fixtures, validate_bad_fixture
from iapetus.validation.label_permission_regex_audit import run_regex_audit
from iapetus.validation.adversarial_stress_probe import run_stress_probe


def build_gap_report() -> dict[str, Any]:
    adversarial = audit_adversarial_coverage()
    stress = run_stress_probe()
    regex = run_regex_audit()
    wrongly_eligible_adversarial = [
        item.fixture_slug
        for item in [validate_bad_fixture(fixture) for fixture in load_bad_fixtures()]
        if item.training_eligible
    ]
    return {
        "adversarial_coverage_ok": adversarial["adversarial_coverage_ok"],
        "curated_quality_ok": adversarial["curated_quality_ok"],
        "stress_probe_all_blocked": stress["all_blocked"],
        "regex_audit_ok": regex["all_ok"],
        "regex_slips": regex["slips"],
        "stress_slips": stress["slips"],
        "adversarial_wrongly_eligible": wrongly_eligible_adversarial,
        "adversarial_rows": adversarial["adversarial_rows"],
        "stress_probes": stress["probes"],
        "open_holes": _open_holes(adversarial, stress, regex, wrongly_eligible_adversarial),
    }


def _open_holes(
    adversarial: dict[str, Any],
    stress: dict[str, Any],
    regex: dict[str, Any],
    wrongly_eligible: list[str],
) -> list[str]:
    holes: list[str] = []
    if not regex.get("all_ok"):
        holes.append(f"Regex audit slips: {', '.join(regex['slips'])}")
    if not adversarial.get("adversarial_coverage_ok"):
        holes.append("Adversarial expected-issue coverage has gaps (run bad-data audit).")
    if not adversarial.get("curated_quality_ok"):
        holes.append("Curated good fixtures failed training eligibility.")
    if stress.get("slips"):
        holes.append(f"Synthetic stress probes slipped as training-eligible: {', '.join(stress['slips'])}")
    if wrongly_eligible:
        holes.append(
            "Adversarial fixtures marked training-eligible (should stay blocked): "
            + ", ".join(wrongly_eligible)
        )
    if not holes:
        holes.append("No open holes detected by current seed rules.")
    return holes
