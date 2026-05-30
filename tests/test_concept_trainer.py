from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from iapetus.cli import app
from iapetus.fixture_analysis import (
    extract_fixture_token_groups,
    fixture_record,
    resolve_fixture,
)
from iapetus.learning.concept_trainer import (
    absorb_curated_seed,
    build_token_vocabulary_document,
    compare_fixtures,
    explain_fixture,
    explain_token,
)


def test_malware_banker_has_package_name() -> None:
    record = fixture_record(resolve_fixture("malware_banker"))
    assert record["package_name"] == "com.fake.update.security"


def test_malware_banker_has_sms_permissions() -> None:
    record = fixture_record(resolve_fixture("malware_banker"))
    assert "android.permission.READ_SMS" in record["permissions"]
    assert "android.permission.RECEIVE_SMS" in record["permissions"]


def test_malware_banker_has_boot_intent() -> None:
    record = fixture_record(resolve_fixture("malware_banker"))
    intents = " ".join(record["intent_filters"]).upper()
    assert "BOOT_COMPLETED" in intents


def test_malware_banker_has_suspicious_indicators() -> None:
    record = fixture_record(resolve_fixture("malware_banker"))
    assert "sms_intercept" in record["suspicious_indicators"]
    assert "overlay_attack" in record["suspicious_indicators"]


def test_malware_dropper_has_dexclassloader() -> None:
    groups = extract_fixture_token_groups(resolve_fixture("malware_dropper"))
    assert "DexClassLoader" in groups["code_strings"]


def test_benign_social_app_is_normal_with_contacts() -> None:
    record = fixture_record(resolve_fixture("benign_social_app"))
    assert record["entity_kind"] == "normal_app"
    assert "android.permission.READ_CONTACTS" in record["permissions"]


def test_absorb_writes_generated_summary_files(tmp_path: Path) -> None:
    paths = absorb_curated_seed(generated_dir=tmp_path)
    assert paths["knowledge_summary"].is_file()
    assert paths["token_vocabulary"].is_file()
    assert paths["fixture_cooccurrence"].is_file()
    assert paths["training_corpus"].is_file()


def test_token_vocabulary_contains_seed_anchors() -> None:
    vocab = build_token_vocabulary_document()
    all_tokens = vocab["all_tokens"]
    assert "android.permission.READ_SMS" in all_tokens
    assert "DexClassLoader" in all_tokens


def test_explain_token_permission() -> None:
    detail = explain_token("android.permission.READ_SMS")
    assert detail["found"] is True
    assert detail["kind"] == "permission"
    assert detail["rough_risk"] == "critical"
    assert "malware_banker" in detail["fixture_keys"]


def test_explain_token_static_code_linked_to_dropper() -> None:
    detail = explain_token("DexClassLoader")
    assert detail["found"] is True
    assert "malware_dropper" in detail["fixture_keys"]


def test_explain_fixture_includes_package_and_indicators() -> None:
    detail = explain_fixture("malware_banker")
    assert detail["package_name"] == "com.fake.update.security"
    assert "sms_intercept" in detail["suspicious_indicators"]
    assert "interpretation" in detail
    assert "Banker-like" in detail["interpretation"]


def test_compare_fixtures_includes_permissions_and_interpretation() -> None:
    detail = compare_fixtures("benign_social_app", "malware_banker")
    assert "android.permission.INTERNET" in detail["shared_permissions"]
    assert "android.permission.READ_SMS" in detail["only_right_permissions"]
    assert detail["only_left_static_tokens"]
    assert "interpretation" in detail


def test_learn_absorb_cli(tmp_path: Path) -> None:
    result = CliRunner().invoke(
        app,
        ["learn", "absorb", "--generated-dir", str(tmp_path)],
    )
    assert result.exit_code == 0
    assert (tmp_path / "token_vocabulary.json").is_file()


def test_android_tokens_cli() -> None:
    result = CliRunner().invoke(
        app,
        ["android", "tokens", "--fixture", "malware_banker"],
    )
    assert result.exit_code == 0
    assert "BootReceiver" in result.stdout
    assert "sms_intercept" in result.stdout
    assert "android.permission.READ_SMS" in result.stdout


def test_learn_explain_fixture_cli() -> None:
    result = CliRunner().invoke(
        app,
        ["learn", "explain-fixture", "--fixture", "malware_banker"],
    )
    assert result.exit_code == 0
    assert "com.fake.update.security" in result.stdout
    assert "sms_intercept" in result.stdout
    assert "Interpretation" in result.stdout


def test_learn_compare_fixtures_cli() -> None:
    result = CliRunner().invoke(
        app,
        [
            "learn",
            "compare-fixtures",
            "--left",
            "benign_social_app",
            "--right",
            "malware_banker",
        ],
    )
    assert result.exit_code == 0
    assert "Shared permissions" in result.stdout
    assert "android.permission.READ_SMS" in result.stdout
    assert "Interpretation" in result.stdout
