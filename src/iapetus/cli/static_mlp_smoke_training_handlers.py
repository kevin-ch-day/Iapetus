"""Learning run and static-MLP training handlers."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import typer

from iapetus.learning.curated_learning_artifacts import (
    write_curated_learning_run_artifacts,
    write_curated_smoke_supplements,
)
from iapetus.learning import (
    LearningRunResult,
    build_smoke_result,
    list_learning_runs,
    read_latest_learning_result,
    write_learning_artifacts,
)
from iapetus.learning.deep.static_mlp_inference import evaluate_saved_run, load_model_bundle, predict_fixture
from iapetus.learning.deep.static_mlp_trainer import torch_available
from iapetus.learning.learning_run_artifacts import artifact_presence, expected_artifacts_for_mode
from iapetus.learning.static_mlp_training_pipeline import build_static_v1_result, write_static_v1_artifacts
from iapetus.database import list_indexed_runs
from iapetus.validation import (
    build_training_quality_contract,
    summarize_bad_fixture_results,
    validate_curated_fixtures_quality,
)

import iapetus.cli.cli_console_and_path_helpers as cli_common
from iapetus.cli.cli_console_and_path_helpers import console, print_token_group, _prompt_choice


def _run_smoke_learning_summary(*, use_curated: bool = False) -> LearningRunResult:
    result, _ = build_smoke_result(
        dataset_name="curated seed fixtures" if use_curated else "demo fixtures",
        use_curated_fixtures=use_curated,
    )
    console.print("Learning run: smoke")
    console.print(f"Dataset     : {result.dataset_name}")
    console.print(f"Entities    : {result.entity_count}")
    console.print(f"Malware     : {result.malware_count}")
    console.print(f"Normal apps : {result.normal_app_count}")
    console.print(f"Model       : {result.model_name}")
    console.print(f"Status      : {result.status}")
    return result


def _run_deep_learning_menu(deep_choice: int | None = None) -> bool:
    console.print("RUN DEEP LEARNING")
    console.print("-----------------")
    console.print("  [1] Smoke learning summary   demo fixtures")
    console.print("  [2] Smoke learning summary   curated fixtures")
    console.print("  [3] Static MLP v2 train      curated fixtures (seed DL)")
    console.print("  [4] Evaluate latest model    re-score curated corpus")
    console.print("  [5] Watch mode               not available yet")
    console.print("  [0] Back")

    if deep_choice is None:
        if not sys.stdin.isatty():
            console.print(
                "[yellow]Non-interactive mode: pass --deep-choice 1 or 2 for smoke summary.[/yellow]",
            )
            return True
        deep_choice = _prompt_choice("Select [0-5]: ", 0, 5)
        if deep_choice is None:
            return False

    if deep_choice == 0:
        return True
    if deep_choice == 1:
        _run_smoke_learning_summary(use_curated=False)
        return True
    if deep_choice == 2:
        _run_smoke_learning_summary(use_curated=True)
        return True
    if deep_choice == 3:
        _run_static_v1_learning(write=True, output_dir=cli_common.LEARNING_RUNS_DIR)
        return True
    if deep_choice == 4:
        _run_learn_evaluate(output_dir=cli_common.LEARNING_RUNS_DIR)
        return True
    if deep_choice == 5:
        console.print("[yellow]Not available yet in seed mode.[/yellow]")
        return True

    console.print("[red]Invalid selection; choose 0-5.[/red]")
    return False


def print_label_laboratory() -> None:
    console.print("[bold]LABEL LABORATORY[/bold]")
    console.print("Malware:")
    console.print("  AndroidOS:Trojan.Anubis-t:[Banker]")
    console.print("Normal app:")
    console.print("  AndroidOS:Facebook-64543615:[SocialMedia]")
    console.print("Malware pattern:")
    console.print("  platform:malware_primary.family-variant:[subtype]", markup=False)
    console.print("Normal app pattern:")
    console.print("  platform:app_name-build_ref:[app_category]", markup=False)


def _run_static_v1_learning(
    *,
    write: bool,
    output_dir: Path,
    backend: str | None = None,
    notes: str | None = None,
) -> None:
    if output_dir.exists() and not output_dir.is_dir():
        console.print(f"[red]Output path must be a directory: {output_dir}[/red]")
        raise typer.Exit(code=1)

    blocked = [item for item in validate_curated_fixtures_quality() if not item.training_eligible]
    if blocked:
        console.print("[red]Curated fixtures failed training quality gate:[/red]")
        for item in blocked:
            console.print(f"- {item.fixture_slug}: {', '.join(item.training_blockers) or ', '.join(item.issues)}")
        raise typer.Exit(code=1)

    try:
        result, report, entity_model, malware_class_model, benign_class_model = build_static_v1_result(
            backend=backend
        )
    except ValueError as exc:
        console.print(f"[red]Static v1 training failed: {exc}[/red]")
        raise typer.Exit(code=1)

    if notes and notes.strip():
        result = result.model_copy(update={"notes": notes})

    if write:
        run_dir = output_dir / result.run_id
        try:
            write_static_v1_artifacts(
                result,
                report,
                run_dir,
                entity_model=entity_model,
                malware_classification_model=malware_class_model,
                benign_classification_model=benign_class_model,
            )
            write_curated_learning_run_artifacts(run_dir, kind="static_mlp")
        except OSError as exc:
            console.print(f"[red]Could not write learning artifacts: {exc}[/red]")
            raise typer.Exit(code=1)

    console.print("[bold]Static MLP v2 training[/bold]")
    console.print(f"Run ID       : {result.run_id}")
    console.print(f"Backend      : {report['backend']} (torch installed: {torch_available()})")
    console.print(f"Examples     : {report['training_example_count']}")
    console.print(f"Entity train : {report['train_accuracy']}  LOOCV: {report['loocv']['accuracy']}")
    console.print(f"Class train  : {report['classification_train_accuracy']}")
    subgroup = report.get("classification_subgroup_loocv") or {}
    malware_loocv = subgroup.get("malware")
    benign_loocv = subgroup.get("benign")
    subgroup_train = report.get("classification_subgroup_train_accuracy") or {}
    if subgroup_train:
        console.print(
            f"Class subgroup train: malware={subgroup_train.get('malware')} "
            f"benign={subgroup_train.get('benign')}"
        )
    if malware_loocv:
        console.print(
            f"Class subgroup LOOCV (stress): malware={malware_loocv['accuracy']} "
            f"benign={benign_loocv['accuracy'] if benign_loocv else 'n/a'}"
        )
    if report["loocv"].get("precision_recall"):
        pr = report["loocv"]["precision_recall"]
        console.print(f"Malware P/R/F1: {pr['precision_malware']}/{pr['recall_malware']}/{pr['f1_malware']}")
    console.print(f"Status       : {result.status}")
    if write:
        console.print(f"Wrote files  : {output_dir / result.run_id}")
    for row in report["predictions"]:
        mark = "ok" if row["entity_kind_correct"] else "MISS"
        console.print(
            f"  [{mark}] {row['fixture_slug']}: {row['predicted_entity_kind']}/"
            f"{row['predicted_classification']} "
            f"(expected {row['expected_entity_kind']}/{row['expected_classification']})"
        )


def _run_learn_predict(
    fixture: str,
    *,
    output_dir: Path,
    run_id: str | None = None,
) -> None:
    try:
        bundle = load_model_bundle(output_dir, run_id=run_id)
        detail = predict_fixture(bundle, fixture)
    except (FileNotFoundError, KeyError, ValueError) as exc:
        console.print(f"[red]Prediction failed: {exc}[/red]")
        raise typer.Exit(code=1)

    console.print("[bold]Fixture prediction[/bold]")
    console.print(f"Model run    : {bundle.run_dir.name}")
    console.print(f"Fixture      : {detail['fixture_slug']}")
    console.print(f"Predicted    : {detail['predicted_entity_kind']} / {detail['predicted_classification']}")
    console.print(f"Expected     : {detail['expected_entity_kind']} / {detail['expected_classification']}")
    console.print(f"P(malware)   : {detail['entity_kind_probability_malware']}")
    if detail.get("top_features"):
        console.print("Top features (first-layer attribution):")
        for item in detail["top_features"]:
            console.print(f"  - {item['feature']}: {item['attribution']}")


def _run_learn_evaluate(*, output_dir: Path, run_id: str | None = None) -> None:
    try:
        bundle = load_model_bundle(output_dir, run_id=run_id)
        report = evaluate_saved_run(bundle)
    except FileNotFoundError as exc:
        console.print(f"[red]Evaluate failed: {exc}[/red]")
        raise typer.Exit(code=1)

    console.print("[bold]Model evaluation (curated corpus)[/bold]")
    console.print(f"Run          : {bundle.run_dir.name}")
    console.print(f"Entity acc   : {report['entity_kind_accuracy']}")
    console.print(f"Class acc    : {report['classification_accuracy']}")
    subgroup = report.get("classification_subgroup_accuracy") or {}
    if subgroup:
        console.print(
            f"Class subgroup: malware={subgroup.get('malware')} benign={subgroup.get('benign')}"
        )
    for row in report["predictions"]:
        mark = "ok" if row["entity_kind_correct"] else "MISS"
        console.print(
            f"  [{mark}] {row['fixture_slug']}: {row['predicted_entity_kind']}/"
            f"{row['predicted_classification']}"
        )


def _run_learning_run(
    mode: str,
    write: bool,
    output_dir: Path,
    notes: str | None = None,
    use_curated: bool = False,
    include_bad_data: bool = False,
    backend: str | None = None,
) -> None:
    normalized_mode = mode.strip().lower().replace("_", "-")
    if normalized_mode in {"static-v1", "static-v2"}:
        if not use_curated:
            console.print("[red]static-v1/static-v2 mode requires --use-curated.[/red]")
            raise typer.Exit(code=1)
        _run_static_v1_learning(write=write, output_dir=output_dir, backend=backend, notes=notes)
        return
    if normalized_mode != "smoke":
        console.print(f"Learning mode '{mode}' is not available in seed kernel yet.")
        raise typer.Exit(code=1)

    if output_dir.exists() and not output_dir.is_dir():
        console.print(f"[red]Output path must be a directory: {output_dir}[/red]")
        raise typer.Exit(code=1)

    dataset_name = "curated seed fixtures" if use_curated else "demo fixtures"
    if use_curated:
        blocked = [item for item in validate_curated_fixtures_quality() if not item.training_eligible]
        if blocked:
            console.print("[red]Curated fixtures failed training quality gate:[/red]")
            for item in blocked:
                console.print(
                    f"- {item.fixture_slug}: {', '.join(item.training_blockers) or ', '.join(item.issues)}"
                )
            raise typer.Exit(code=1)

    result, labels = build_smoke_result(dataset_name=dataset_name, use_curated_fixtures=use_curated)
    if notes and notes.strip():
        result = result.model_copy(update={"notes": notes})

    if write:
        run_dir = output_dir / result.run_id
        try:
            write_learning_artifacts(
                result,
                labels,
                run_dir,
                write_curated_entities=use_curated,
            )
            if include_bad_data:
                bad_report = summarize_bad_fixture_results()
                (run_dir / "bad_data_validation.json").write_text(
                    json.dumps(bad_report, indent=2),
                    encoding="utf-8",
                )
                (run_dir / "training_quality_contract.json").write_text(
                    json.dumps(bad_report.get("training_quality_contract", build_training_quality_contract()), indent=2),
                    encoding="utf-8",
                )
                console.print(
                    "[yellow]Adversarial fixtures probed (not merged into entities): "
                    f"{bad_report['fixture_count']} cases; "
                    f"coverage_ok={bad_report.get('adversarial_coverage_ok')}[/yellow]"
                )
            elif use_curated:
                write_curated_smoke_supplements(run_dir)
        except (OSError, IOError) as exc:
            console.print(f"[red]Could not write learning artifacts: {exc}[/red]")
            raise typer.Exit(code=1)

    console.print("[bold]Learning run summary[/bold]")
    console.print(f"Run ID      : {result.run_id}")
    console.print(f"Created at  : {result.created_at}")
    console.print(f"Mode        : {result.mode}")
    console.print(f"Dataset     : {result.dataset_name}")
    console.print(f"Entities    : {result.entity_count}")
    console.print(f"Malware     : {result.malware_count}")
    console.print(f"Normal apps : {result.normal_app_count}")
    if result.use_curated_fixtures:
        console.print(f"Training ex.: {result.training_example_count} (avg quality {result.average_training_quality_score})")
    console.print(f"Model       : {result.model_name}")
    console.print(f"Status      : {result.status}")
    if write:
        console.print(f"Wrote files : {output_dir / result.run_id}")


def _run_learning_list(output_dir: Path) -> None:
    runs = list_learning_runs(output_dir)
    if not runs:
        console.print("No learning runs found.")
        return

    indexed = {row["run_id"]: row for row in list_indexed_runs()}
    console.print("[bold]Learning runs[/bold]")
    for run_dir, result in runs:
        extra = ""
        row = indexed.get(result.run_id)
        if row and row.get("entity_loocv") is not None:
            extra = f" LOOCV={row['entity_loocv']}"
            if row.get("classification_train_accuracy") is not None:
                extra += f" class_train={row['classification_train_accuracy']}"
        console.print(f"{result.run_id}: {result.status} ({result.mode}){extra} — {run_dir}")


def _run_learning_last(output_dir: Path) -> None:
    latest = read_latest_learning_result(output_dir)
    if latest is None:
        console.print("No learning runs found.")
        return

    result, run_dir = latest
    console.print(f"Last learning run: {result.run_id}")
    console.print(f"Path: {run_dir}")
    console.print(result.model_dump_json(indent=2))
    expected = expected_artifacts_for_mode(
        result.mode,  # type: ignore[arg-type]
        use_curated=result.use_curated_fixtures,
    )
    for artifact, present in artifact_presence(run_dir, expected):
        console.print(f"{'Has' if present else 'Missing'} {artifact}")
    if result.use_curated_fixtures and (run_dir / "labeled_entities.json").is_file():
        rows = json.loads((run_dir / "labeled_entities.json").read_text(encoding="utf-8"))
        console.print("[bold]Labeled entities[/bold]")
        for row in rows:
            console.print(
                f"- {row['fixture_slug']}: {row['rendered_label']} "
                f"({row['entity_kind']}, {row.get('package_name', '')})"
            )


