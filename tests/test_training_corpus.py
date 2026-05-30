from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from iapetus.cli import app
from iapetus.learning.curated_concept_trainer import absorb_curated_seed
from iapetus.learning.quality_gated_training_corpus import build_training_corpus, build_training_example
from iapetus.curated_fixture_analysis import resolve_fixture


def test_training_corpus_has_twelve_eligible_examples() -> None:
    corpus = build_training_corpus()
    assert corpus["fixture_count"] == 12
    assert corpus["training_example_count"] == 12
    assert corpus["blocked_fixture_count"] == 0
    assert corpus["malware_example_count"] == 6
    assert corpus["normal_app_example_count"] == 6
    assert corpus["average_training_quality_score"] >= 80.0


def test_new_malware_fixtures_in_corpus() -> None:
    corpus = build_training_corpus()
    slugs = {row["fixture_slug"] for row in corpus["training_examples"]}
    assert "malware_spyware" in slugs
    assert "malware_adware_fraud" in slugs
    assert "malware_stalkerware" in slugs
    assert "benign_mobile_banking" in slugs


def test_training_example_includes_quality_score() -> None:
    example = build_training_example(resolve_fixture("malware_spyware"))
    assert example is not None
    assert example["training_quality_score"] >= 80
    assert example["feature_vector"]["has_contact_or_sms_exfil"] is True


def test_absorb_writes_training_corpus(tmp_path: Path) -> None:
    paths = absorb_curated_seed(generated_dir=tmp_path)
    assert paths["training_corpus"].is_file()
    payload = json.loads(paths["training_corpus"].read_text(encoding="utf-8"))
    assert payload["training_example_count"] == 12


def test_learn_corpus_cli() -> None:
    result = CliRunner().invoke(app, ["learn", "corpus"])
    assert result.exit_code == 0
    assert "malware_spyware" in result.stdout
    assert "Training corpus" in result.stdout
