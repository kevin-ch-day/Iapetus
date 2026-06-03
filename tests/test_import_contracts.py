from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from iapetus.cli import app
from iapetus.knowledge.import_contract_loaders import (
    IMPORT_CONTRACT_SPECS,
    import_contracts_dir,
    load_import_contract_file,
    validate_import_contract_file,
    validate_all_import_contract_files,
)
from iapetus.knowledge.import_contract_models import AndroidConceptLesson
from iapetus.knowledge.type_training_corpus import build_type_training_corpus, preview_training_seed_summary


def test_seed_import_contract_files_parse() -> None:
    for spec in IMPORT_CONTRACT_SPECS:
        records = load_import_contract_file(Path("data/import_contracts") / spec.file_name, spec.model)
        assert records


def test_bad_jsonl_row_fails_cleanly(tmp_path: Path) -> None:
    path = tmp_path / "bad.jsonl"
    path.write_text('{"schema_name":"x"}\n{bad json}\n', encoding="utf-8")
    try:
        load_import_contract_file(path, AndroidConceptLesson)
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "row 1" in str(exc) or "row 2" in str(exc)
        assert "invalid JSON" in str(exc)


def test_missing_governance_field_fails_cleanly(tmp_path: Path) -> None:
    path = tmp_path / "missing.jsonl"
    path.write_text(
        '{"schema_name":"iapetus.android_concept_lesson","schema_version":"v1","source_kind":"seed","teaching_use":true,"training_use":false,"synthetic_level":"low","review_status":"reviewed","concept_id":"android_manifest","topic":"manifest","title":"x","summary":"y","related_concepts":[]}\n',
        encoding="utf-8",
    )
    try:
        load_import_contract_file(path, AndroidConceptLesson)
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "confidence_note" in str(exc) or "training_eligibility" in str(exc)


def test_missing_training_eligibility_fails_cleanly(tmp_path: Path) -> None:
    path = tmp_path / "missing_eligibility.jsonl"
    path.write_text(
        '{"schema_name":"iapetus.android_concept_lesson","schema_version":"v1","source_kind":"seed","teaching_use":true,"training_use":false,"synthetic_level":"low","review_status":"reviewed","confidence_note":"ok","concept_id":"android_manifest","topic":"manifest","title":"x","summary":"y","related_concepts":[]}\n',
        encoding="utf-8",
    )
    try:
        load_import_contract_file(path, AndroidConceptLesson)
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "training_eligibility" in str(exc)


def test_valid_training_eligibility_values_parse() -> None:
    records = load_import_contract_file(Path("data/import_contracts") / "attack_mobile_seed_mappings.jsonl", IMPORT_CONTRACT_SPECS[-1].model)
    assert all(record.training_eligibility == "explanation_only" for record in records)


def test_invalid_training_eligibility_value_fails(tmp_path: Path) -> None:
    path = tmp_path / "invalid_eligibility.jsonl"
    path.write_text(
        '{"schema_name":"iapetus.android_concept_lesson","schema_version":"v1","source_kind":"seed","teaching_use":true,"training_use":false,"training_eligibility":"train_now","synthetic_level":"low","review_status":"reviewed","confidence_note":"ok","concept_id":"android_manifest","topic":"manifest","title":"x","summary":"y","related_concepts":[]}\n',
        encoding="utf-8",
    )
    try:
        load_import_contract_file(path, AndroidConceptLesson)
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "training_eligibility" in str(exc)


def test_teaching_and_training_use_are_separated() -> None:
    summaries = validate_all_import_contract_files(Path("data/import_contracts"))
    assert any(summary.training_eligible_count < summary.valid_count for summary in summaries)
    assert all(summary.training_approved_count == 0 for summary in summaries)


def test_validate_import_contract_file_reports_windows_style_path(tmp_path: Path) -> None:
    path = tmp_path / "android_concept_lessons.jsonl"
    path.write_text(
        '{"schema_name":"iapetus.android_concept_lesson","schema_version":"v1","source_kind":"seed","teaching_use":true,"training_use":false,"training_eligibility":"teaching_only","synthetic_level":"low","review_status":"reviewed","confidence_note":"ok","concept_id":"android_manifest","topic":"manifest","title":"x","summary":"y","related_concepts":[]}\n',
        encoding="utf-8",
    )
    summary = validate_import_contract_file(path, AndroidConceptLesson, "android_concept_lesson")
    assert summary.file_name == "android_concept_lessons.jsonl"
    assert summary.valid_count == 1


def test_knowledge_validate_import_contracts_cli_runs() -> None:
    result = CliRunner().invoke(app, ["knowledge", "validate-import-contracts"])
    assert result.exit_code == 0
    assert "Import contract validation" in result.stdout
    assert "permission_authority_facts.jsonl" in result.stdout
    assert "Record types" in result.stdout
    assert "Training cand." in result.stdout
    assert "Teaching only" in result.stdout
    assert "Explanation only" in result.stdout


def test_preview_training_seed_summary_has_expected_sections() -> None:
    summary = preview_training_seed_summary()
    assert summary["permission_fact_count"] >= 5
    assert summary["malware_type_pattern_count"] >= 6
    assert summary["benign_archetype_count"] >= 5
    assert summary["contrast_example_count"] >= 5


def test_build_type_training_corpus_has_examples_and_warnings() -> None:
    corpus = build_type_training_corpus()
    assert corpus["example_count"] >= 8
    assert "banker" in corpus["class_counts"]
    assert "banking" in corpus["class_counts"]
    assert corpus["authority_fact_count"] >= 5
    assert corpus["warnings"]


def test_knowledge_preview_training_seeds_cli_runs() -> None:
    result = CliRunner().invoke(app, ["knowledge", "preview-training-seeds"])
    assert result.exit_code == 0
    assert "Training Seed Preview" in result.stdout
    assert "Permission facts" in result.stdout
    assert "Trainable malware patterns" in result.stdout


def test_knowledge_build_type_corpus_cli_runs(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("iapetus.project_filesystem_paths.GENERATED_DIR", tmp_path / "generated")
    result = CliRunner().invoke(app, ["knowledge", "build-type-corpus", "--write"])
    assert result.exit_code == 0
    assert "Type Training Corpus" in result.stdout
    assert "Wrote type corpus" in result.stdout
