"""Typer commands for learning runs and concept trainer."""
from __future__ import annotations

from pathlib import Path

import typer

import iapetus.cli.cli_console_and_path_helpers as cli_common
from iapetus.cli.learning_subcommand_handler_bridge import (
    _run_learn_absorb,
    _run_learn_compare_fixtures,
    _run_learn_corpus,
    _run_learn_evaluate,
    _run_learn_explain_fixture,
    _run_learn_explain_token,
    _run_learn_predict,
    _run_learning_last,
    _run_learning_list,
    _run_learning_run,
    _run_static_v1_learning,
)
from iapetus.cli.sqlite_learning_index_cli_output import print_index_learning_runs

learn_app = typer.Typer(help="Learning helpers.")


@learn_app.command("run")
def learn_run(
    mode: str = typer.Option(
        "smoke",
        "--mode",
        "-m",
        help="Learning mode: smoke | static-v1 | static-v2 (v1 is alias for v2).",
    ),
    write: bool = typer.Option(False, "--write", help="Write learning run artifacts."),
    use_curated: bool = typer.Option(
        False,
        "--use-curated",
        help="Use curated data seed files instead of hardcoded fixtures.",
    ),
    include_bad_data: bool = typer.Option(
        False,
        "--include-bad-data",
        help="Run adversarial fixture validation alongside write (does not merge bad fixtures).",
    ),
    backend: str | None = typer.Option(
        None,
        "--backend",
        help="DL backend for static-v1: pure_python or torch (default: torch if installed).",
    ),
    output_dir: Path | None = typer.Option(None, "--output-dir", help="Learning runs output directory."),
    notes: str | None = None,
) -> None:
    """Run a learning pass (smoke summary or static-v1 MLP training)."""
    _run_learning_run(
        mode=mode,
        write=write,
        output_dir=output_dir or cli_common.LEARNING_RUNS_DIR,
        notes=notes,
        use_curated=use_curated,
        include_bad_data=include_bad_data,
        backend=backend,
    )


@learn_app.command("predict")
def learn_predict(
    fixture: str = typer.Option(..., "--fixture", help="Fixture slug to score."),
    run_id: str | None = typer.Option(None, "--run-id", help="Learning run id (default: latest)."),
    output_dir: Path | None = typer.Option(None, "--output-dir", help="Learning runs output directory."),
) -> None:
    """Score a curated fixture with a saved static MLP model."""
    _run_learn_predict(fixture, output_dir=output_dir or cli_common.LEARNING_RUNS_DIR, run_id=run_id)


@learn_app.command("evaluate")
def learn_evaluate(
    run_id: str | None = typer.Option(None, "--run-id", help="Learning run id (default: latest)."),
    output_dir: Path | None = typer.Option(None, "--output-dir", help="Learning runs output directory."),
) -> None:
    """Re-score the curated corpus with a saved model bundle."""
    _run_learn_evaluate(output_dir=output_dir or cli_common.LEARNING_RUNS_DIR, run_id=run_id)


@learn_app.command("train")
def learn_train(
    write: bool = typer.Option(True, "--write/--no-write", help="Write run artifacts."),
    backend: str | None = typer.Option(
        None,
        "--backend",
        help="DL backend: pure_python or torch (default: torch if installed).",
    ),
    output_dir: Path | None = typer.Option(None, "--output-dir", help="Learning runs output directory."),
) -> None:
    """Train static MLP v2 on the curated training corpus."""
    _run_static_v1_learning(write=write, output_dir=output_dir or cli_common.LEARNING_RUNS_DIR, backend=backend)


@learn_app.command("index")
def learn_index(
    output_dir: Path | None = typer.Option(None, "--output-dir", help="Learning runs directory to scan."),
) -> None:
    """Index learning runs into the SQLite registry (M6 seed)."""
    print_index_learning_runs(output_dir or cli_common.LEARNING_RUNS_DIR)


@learn_app.command("list")
def learn_list() -> None:
    """List known local learning runs."""
    _run_learning_list(output_dir=cli_common.LEARNING_RUNS_DIR)


@learn_app.command("last")
def learn_last() -> None:
    """Show the latest local learning run."""
    _run_learning_last(output_dir=cli_common.LEARNING_RUNS_DIR)


@learn_app.command("corpus")
def learn_corpus() -> None:
    """Show quality-gated training corpus built from curated fixtures."""
    _run_learn_corpus()


@learn_app.command("absorb")
def learn_absorb(
    generated_dir: Path | None = typer.Option(
        None,
        "--generated-dir",
        help="Directory for generated knowledge artifacts (default: data/generated).",
    ),
) -> None:
    """Absorb curated seed data into generated knowledge artifacts."""
    _run_learn_absorb(generated_dir=generated_dir)


@learn_app.command("explain-token")
def learn_explain_token(
    token: str = typer.Option(..., "--token", help="Permission or static token to explain."),
) -> None:
    """Explain a curated seed token."""
    _run_learn_explain_token(token=token)


@learn_app.command("explain-fixture")
def learn_explain_fixture(
    fixture: str = typer.Option(..., "--fixture", help="Fixture slug (e.g. malware_banker)."),
) -> None:
    """Explain a curated fixture sample."""
    _run_learn_explain_fixture(fixture=fixture)


@learn_app.command("compare-fixtures")
def learn_compare_fixtures(
    left: str = typer.Option(..., "--left", help="Left fixture slug."),
    right: str = typer.Option(..., "--right", help="Right fixture slug."),
) -> None:
    """Compare permissions and classification between two fixtures."""
    _run_learn_compare_fixtures(left=left, right=right)
