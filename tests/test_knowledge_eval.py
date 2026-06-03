from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from iapetus.cli import app
from iapetus.knowledge import evaluate_android_knowledge, knowledge_eval_file_path, load_knowledge_eval_questions


def test_android_knowledge_eval_questions_parse() -> None:
    questions = load_knowledge_eval_questions()
    assert len(questions) >= 12
    assert any(question.topic == "manifest" for question in questions)


def test_android_knowledge_eval_detects_covered_and_gap() -> None:
    summary = evaluate_android_knowledge()
    assert summary.covered_count >= 1
    assert summary.gap_count >= 1
    assert "permission_edge_cases" in summary.gaps_by_topic


def test_android_knowledge_eval_cli_runs() -> None:
    result = CliRunner().invoke(app, ["knowledge", "eval"])
    assert result.exit_code == 0
    assert "Android Knowledge Eval" in result.stdout
    assert "Total questions" in result.stdout
    assert "Gaps by topic" in result.stdout
    assert "Recommended next seed topics" in result.stdout


def test_android_knowledge_eval_file_path_uses_import_contracts_dir() -> None:
    path = knowledge_eval_file_path(Path("data/import_contracts"))
    assert path.name == "android_knowledge_eval_questions.jsonl"
    assert "import_contracts" in str(path)
