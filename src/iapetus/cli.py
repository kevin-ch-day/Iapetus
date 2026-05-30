from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable, Iterable
import json

import typer
from rich.console import Console

from iapetus.labels.renderer import (
    MalwareLabel,
    NormalAppLabel,
    render_malware_label,
    render_normal_app_label,
)
from iapetus.learning import (
    LearningRunResult,
    build_smoke_result,
    list_learning_runs,
    read_latest_learning_result,
    write_learning_artifacts,
)
from iapetus.learning.static_v1 import build_static_v1_result, write_static_v1_artifacts
from iapetus.learning.deep.inference import evaluate_saved_run, load_model_bundle, predict_fixture
from iapetus.learning.deep.trainer import torch_available
from iapetus.fixture_analysis import build_curated_entity_artifacts
from iapetus.learning.training_corpus import build_training_corpus
from iapetus.learning.concept_trainer import (
    absorb_curated_seed,
    compare_fixtures,
    explain_fixture,
    explain_token,
)
from iapetus.fixture_analysis import extract_fixture_token_groups
from iapetus.probes.environment import collect_device_probe_state, collect_environment_info
from iapetus.snapshots.demo import (
    CURATED_SNAPSHOT_DIR,
    DEMO_OUTPUT_DIR,
    build_curated_snapshot,
    build_demo_snapshot,
    demo_fixtures,
    snapshot_output,
)
from iapetus.connectors import connector_registry_lines
from iapetus.fixture_analysis import fixture_record, resolve_fixture
from iapetus.validation import (
    audit_adversarial_coverage,
    build_gap_report,
    build_training_quality_contract,
    run_edge_case_analysis,
    run_regex_audit,
    run_stress_probe,
    compare_bad_to_good,
    explain_bad_fixture,
    load_bad_fixtures,
    resolve_bad_fixture,
    summarize_bad_fixture_results,
    validate_curated_fixtures_quality,
    validate_fixture_quality,
)
from iapetus.data_library import GENERATED_DIR
from iapetus.knowledge import (
    ArtifactClassification,
    ArtifactClassifier,
    apk_anatomy_lines,
    classify_artifact,
    concept_summary,
    get_concept,
    find_matching_concepts,
    find_matching_lessons,
    list_fake_topics,
    fake_data_lines,
    list_concept_ids,
    list_lesson_ids,
    lesson_lines,
    print_concepts,
)
from iapetus.data_library import (
    SOURCE_MANIFEST_PATH,
    KNOWLEDGE_SUMMARY_PATH,
    build_feature_vocabulary,
    build_token_summary,
    seed_summary,
    list_source_manifests,
    validate_seed_payloads,
)

app = typer.Typer(help="Iapetus Android security deep-learning kernel.")
labels_app = typer.Typer(help="Label rendering helpers.")
snapshot_app = typer.Typer(help="Snapshot helpers.")
learn_app = typer.Typer(help="Learning helpers.")
android_app = typer.Typer(help="Android fixture static-analysis helpers.")
bad_data_app = typer.Typer(help="Adversarial/bad-data validation (not training truth).")
dataset_app = typer.Typer(help="Dataset helpers.")
data_app = typer.Typer(help="Data library helpers.")
knowledge_app = typer.Typer(help="Knowledge helpers.")
console = Console()
MENU_SEPARATOR = "=" * 78
LEARNING_RUNS_DIR = Path("output/learning_runs")


def _menu_line(label: str, value: str, width: int = 12) -> str:
    return f"{label:<{width}}: {value}"


def _collect_device_for_banner(timeout_seconds: float = 1.0) -> str:
    try:
        return collect_device_probe_state(timeout_seconds=timeout_seconds)
    except Exception:
        return "error"


def menu_lines() -> list[str]:
    try:
        environment = collect_environment_info()
        host_os = environment.system
        host_version = environment.release
        python_version = environment.python_version
    except Exception:
        host_os = "Unknown"
        host_version = "unknown"
        python_version = "unknown"

    device_state = _collect_device_for_banner()

    return [
        MENU_SEPARATOR,
        f"{'IAPETUS':^78}",
        f"{'Android Security Deep-Learning Operator':^78}",
        MENU_SEPARATOR,
        _menu_line("Host", host_os),
        _menu_line("Host Version", host_version),
        _menu_line("Python", python_version),
        _menu_line("Mode", "seed"),
        _menu_line("Data", "demo fixtures + curated seeds optional"),
        _menu_line("Learning", "smoke available"),
        _menu_line("Iapetus DB", "not initialized"),
        _menu_line("Upstream", "not connected"),
        _menu_line("Device", device_state),
        _menu_line("Emulator", "not checked"),
        "",
        "MAIN MENU",
        "---------",
        "  [1] Run Deep Learning",
        "  [2] Learning Console",
        "  [3] Build / View Demo Snapshot",
        "  [4] Label Laboratory",
        "  [5] Environment & Device Probe",
        "  [6] Connector Registry",
        "  [7] Roadmap",
        "  [8] Help / About",
        "  [0] Exit",
    ]


def _prompt_choice(prompt: str, minimum: int, maximum: int) -> int | None:
    try:
        raw_choice = input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        return None

    try:
        choice = int(raw_choice)
    except ValueError:
        console.print(f"[red]Invalid input '{raw_choice}'; expected a number {minimum}-{maximum}.[/red]")
        return None

    if choice < minimum or choice > maximum:
        console.print(
            f"[red]Selection '{choice}' is outside valid range {minimum}-{maximum}.[/red]",
        )
        return None

    return choice


def print_environment_probe(check_device: bool = False) -> None:
    try:
        environment = collect_environment_info()
    except Exception as exc:
        console.print(f"[red]Environment probe failed: {exc}[/red]")
        raise typer.Exit(code=1)

    console.print("[bold]Iapetus environment probe[/bold]")
    console.print(f"Host OS       : {environment.system}")
    console.print(f"Host Version  : {environment.release}")
    console.print(f"Python        : {environment.python_version}")
    if check_device:
        try:
            state = collect_device_probe_state()
            console.print(f"Device probe  : {state}")
        except Exception as exc:
            console.print(f"[yellow]Device probe failed: {exc}[/yellow]")
            raise typer.Exit(code=1)


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
    console.print("  [3] Static MLP train         curated fixtures (seed DL)")
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
        _run_static_v1_learning(write=True, output_dir=LEARNING_RUNS_DIR)
        return True
    if deep_choice == 4:
        _run_learn_evaluate(output_dir=LEARNING_RUNS_DIR)
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


def _write_curated_run_extras(run_dir: Path) -> None:
    entities, token_groups, features = build_curated_entity_artifacts()
    (run_dir / "entities.json").write_text(json.dumps(entities, indent=2), encoding="utf-8")
    (run_dir / "entity_features.json").write_text(json.dumps(features, indent=2), encoding="utf-8")
    (run_dir / "entity_token_groups.json").write_text(json.dumps(token_groups, indent=2), encoding="utf-8")
    corpus = build_training_corpus()
    (run_dir / "training_corpus.json").write_text(json.dumps(corpus, indent=2), encoding="utf-8")
    feature_vocabulary = build_feature_vocabulary()
    token_summary = build_token_summary()
    (run_dir / "feature_vocabulary.json").write_text(json.dumps(feature_vocabulary, indent=2), encoding="utf-8")
    (run_dir / "token_summary.json").write_text(json.dumps(token_summary, indent=2), encoding="utf-8")
    (run_dir / "training_quality_contract.json").write_text(
        json.dumps(build_training_quality_contract(), indent=2),
        encoding="utf-8",
    )


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
            _write_curated_run_extras(run_dir)
        except OSError as exc:
            console.print(f"[red]Could not write learning artifacts: {exc}[/red]")
            raise typer.Exit(code=1)

    console.print("[bold]Static MLP v2 training[/bold]")
    console.print(f"Run ID       : {result.run_id}")
    console.print(f"Backend      : {report['backend']} (torch installed: {torch_available()})")
    console.print(f"Examples     : {report['training_example_count']}")
    console.print(f"Entity train : {report['train_accuracy']}  LOOCV: {report['loocv']['accuracy']}")
    console.print(f"Class train  : {report['classification_train_accuracy']}")
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
    if normalized_mode == "static-v1":
        if not use_curated:
            console.print("[red]static-v1 mode requires --use-curated.[/red]")
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
            if use_curated:
                feature_vocabulary = build_feature_vocabulary()
                token_summary = build_token_summary()
                (run_dir / "feature_vocabulary.json").write_text(
                    json.dumps(feature_vocabulary, indent=2),
                    encoding="utf-8",
                )
                (run_dir / "token_summary.json").write_text(
                    json.dumps(token_summary, indent=2),
                    encoding="utf-8",
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
                contract_path = run_dir / "training_quality_contract.json"
                contract_path.write_text(
                    json.dumps(build_training_quality_contract(), indent=2),
                    encoding="utf-8",
                )
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

    console.print("[bold]Learning runs[/bold]")
    for run_dir, result in runs:
        console.print(f"{result.run_id}: {result.status} (path: {run_dir})")


def _run_learning_last(output_dir: Path) -> None:
    latest = read_latest_learning_result(output_dir)
    if latest is None:
        console.print("No learning runs found.")
        return

    result, run_dir = latest
    console.print(f"Last learning run: {result.run_id}")
    console.print(f"Path: {run_dir}")
    console.print(result.model_dump_json(indent=2))
    for artifact in (
        "entities.json",
        "labeled_entities.json",
        "entity_token_groups.json",
        "entity_features.json",
        "training_corpus.json",
        "training_features.json",
        "training_metrics.json",
        "predictions.json",
        "model_weights.json",
        "model_torch.pt",
    ):
        path = run_dir / artifact
        console.print(f"{'Has' if path.is_file() else 'Missing'} {artifact}")
    if result.use_curated_fixtures and (run_dir / "labeled_entities.json").is_file():
        rows = json.loads((run_dir / "labeled_entities.json").read_text(encoding="utf-8"))
        console.print("[bold]Labeled entities[/bold]")
        for row in rows:
            console.print(
                f"- {row['fixture_slug']}: {row['rendered_label']} "
                f"({row['entity_kind']}, {row.get('package_name', '')})"
            )


def _run_learning_console_command(command: str) -> bool:
    command = command.strip().lower()
    if not command:
        return True
    if command == "exit":
        console.print("Learning console closed.")
        return False
    if command == "help":
        _print_learning_console_help()
        return True
    if command == "status":
        _status_output()
        return True
    if command == "labels":
        print_label_laboratory()
        return True
    if command == "snapshot":
        _run_demo_snapshot_summary()
        return True
    if command == "learn smoke":
        _run_smoke_learning_summary()
        return True
    if command == "learn list":
        _run_learning_list(output_dir=LEARNING_RUNS_DIR)
        return True
    if command == "learn last":
        _run_learning_last(output_dir=LEARNING_RUNS_DIR)
        return True
    if command == "learn absorb":
        _run_learn_absorb()
        return True
    if command == "learn corpus":
        _run_learn_corpus()
        return True
    if command.startswith("android tokens"):
        parts = command.split(maxsplit=2)
        fixture = parts[-1] if len(parts) >= 3 else "malware_banker"
        _run_android_tokens(fixture=fixture)
        return True
    if command.startswith("learn explain-fixture"):
        parts = command.split(maxsplit=2)
        fixture = parts[-1] if len(parts) >= 3 else "malware_banker"
        _run_learn_explain_fixture(fixture=fixture)
        return True
    if command == "dataset shape":
        _run_dataset_shape_preview()
        return True
    if command == "roadmap":
        _run_roadmap()
        return True
    if command == "connectors":
        _run_connector_registry()
        return True

    console.print(f"[yellow]Unknown command: {command}[/yellow]")
    console.print("Type 'help' for available commands.")
    return True


def _learning_console_command_is_known(command: str) -> bool:
    normalized = command.strip().lower()
    if normalized in {
        "help",
        "status",
        "labels",
        "snapshot",
        "learn smoke",
        "learn list",
        "learn last",
        "learn absorb",
        "learn corpus",
        "dataset shape",
        "roadmap",
        "connectors",
        "exit",
        "",
    }:
        return True
    return normalized.startswith(
        (
            "android tokens ",
            "learn explain-fixture ",
            "learn compare-fixtures ",
        )
    )


def _run_learning_console_command_for_batch(command: str) -> bool:
    normalized = command.strip().lower()
    if not _learning_console_command_is_known(normalized):
        _run_learning_console_command(command)
        raise typer.Exit(code=1)
    return _run_learning_console_command(command)


def _print_learning_console_help() -> None:
    console.print("iapetus> status")
    console.print("iapetus> labels")
    console.print("iapetus> snapshot")
    console.print("iapetus> learn smoke")
    console.print("iapetus> learn list")
    console.print("iapetus> learn last")
    console.print("iapetus> learn absorb")
    console.print("iapetus> android tokens malware_banker")
    console.print("iapetus> learn explain-fixture malware_banker")
    console.print("iapetus> dataset shape")
    console.print("iapetus> roadmap")
    console.print("iapetus> connectors")
    console.print("iapetus> help")
    console.print("iapetus> exit")


def _run_learning_console(optional_command: str | None = None) -> None:
    console.print("[bold]LEARNING CONSOLE[/bold]")
    _print_learning_console_help()

    if optional_command is not None:
        if not _run_learning_console_command_for_batch(optional_command):
            return
        console.print("Learning console session complete.")
        return

    while True:
        try:
            raw_command = input("iapetus> ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("[yellow]Learning console closed.[/yellow]")
            return

        if not _run_learning_console_command(raw_command):
            return


def _run_dataset_shape_preview() -> None:
    console.print("[bold]DATASET SHAPE PREVIEW[/bold]")
    for item in [
        "entities (fixture_slug, package_name, rendered_label)",
        "labeled_entities (identity + label)",
        "entity_token_groups (permissions, components, intents, ...)",
        "entity_features (toy boolean/count feature row)",
        "permission observations",
        "static features",
        "dynamic windows",
        "AV tokens",
        "review decisions",
        "training examples",
    ]:
        console.print(f"- {item}")
    try:
        from iapetus.fixture_analysis import build_entity_features, extract_fixture_token_groups

        sample = resolve_fixture("malware_banker")
        record = fixture_record(sample)
        groups = extract_fixture_token_groups(sample)
        example = build_entity_features(record, groups)
        console.print("[bold]Example entity_features row (malware_banker)[/bold]")
        console.print(json.dumps(example, indent=2))
    except Exception as exc:
        console.print(f"[yellow]Could not load example feature row: {exc}[/yellow]")


def _run_knowledge_concepts() -> None:
    console.print("[bold]Knowledge concepts[/bold]")
    for concept_line in print_concepts():
        console.print(f"- {concept_line}")


def _run_knowledge_show(concept_id: str) -> None:
    try:
        concept = get_concept(concept_id)
    except KeyError as exc:
        console.print(f"[red]{exc}[/red]")
        suggestions = find_matching_concepts(concept_id)
        if suggestions:
            console.print(f"Did you mean: {', '.join(suggestions)}?")
        console.print(f"Available concepts: {', '.join(list_concept_ids())}")
        raise typer.Exit(code=1)
    console.print(f"[bold]{concept.display_name}[/bold]")
    console.print(concept_summary(concept))
    console.print(f"definition: {concept.definition}")
    console.print(f"key_fields: {', '.join(concept.key_fields) or 'none'}")
    console.print(f"static_evidence: {', '.join(concept.static_evidence) or 'none'}")
    console.print(f"dynamic_evidence: {', '.join(concept.dynamic_evidence) or 'none'}")
    console.print(f"relevant_tools: {', '.join(concept.relevant_tools) or 'none'}")
    console.print(f"iapetus_role: {concept.iapetus_role}")
    console.print(f"notes: {concept.notes}")


def _run_knowledge_apk_anatomy() -> None:
    console.print("[bold]APK Anatomy[/bold]")
    for item in apk_anatomy_lines():
        console.print(f"- {item}")


def _run_knowledge_teach(topic: str | None = None) -> None:
    if topic is None or not topic.strip():
        console.print("[bold]Knowledge teaching topics[/bold]")
        for lesson_id in list_lesson_ids():
            console.print(f"- {lesson_id}")
        console.print("Run with: iapetus knowledge teach <topic>")
        return

    try:
        for line in lesson_lines(topic):
            console.print(line)
        return
    except KeyError as exc:
        console.print(f"[red]{exc}[/red]")
        suggestions = find_matching_lessons(topic)
        if suggestions:
            console.print(f"Did you mean: {', '.join(suggestions)}?")
        console.print(f"Available topics: {', '.join(list_lesson_ids())}")
        raise typer.Exit(code=1)


def _run_knowledge_data(topic: str | None = None) -> None:
    if topic is None or not topic.strip():
        console.print("[bold]Seed synthetic data topics[/bold]")
        for item in list_fake_topics():
            console.print(f"- {item}")
        console.print("Run with: iapetus knowledge data <topic>")
        return

    try:
        for line in fake_data_lines(topic):
            console.print(line)
        return
    except KeyError as exc:
        console.print(f"[red]{exc}[/red]")
        console.print(f"Available topics: {', '.join(list_fake_topics())}")
        raise typer.Exit(code=1)


def _run_knowledge_classify(path: str) -> None:
    try:
        classification = ArtifactClassifier.classify(path)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1)
    console.print("[bold]Artifact classification[/bold]")
    console.print(f"Path: {classification.normalized_path}")
    console.print(f"Type: {classification.artifact_type}")
    console.print(f"Evidence: {classification.evidence}")
    if classification.relevant_concepts:
        console.print(
            "Relevant concepts: "
            f"{', '.join(classification.relevant_concepts)}",
        )
    console.print(f"Eligible for Android permission analysis: {classification.relevance.eligible_for_android_permission_analysis}")
    console.print(f"Eligible for Android static analysis: {classification.relevance.eligible_for_android_static_analysis}")
    console.print(f"Eligible for Android dynamic analysis: {classification.relevance.eligible_for_android_dynamic_analysis}")
    console.print(f"Eligible for Windows/PE analysis: {classification.relevance.eligible_for_windows_pe_analysis}")
    console.print(
        "Eligible for future generic AV/vendor-token learning: "
        f"{classification.relevance.eligible_for_generic_av_token_learning}",
    )


def _count_snapshot_artifacts() -> int:
    path = Path(DEMO_OUTPUT_DIR)
    if not path.is_dir():
        return 0
    expected_files = {"manifest.json", "entities.json", "labels.json"}
    if all((path / name).is_file() for name in expected_files):
        return 1
    return 0


def _safe_environment_summary() -> tuple[str, str, str]:
    try:
        environment = collect_environment_info()
        return environment.system, environment.release, environment.python_version
    except Exception:
        return "Unknown", "unknown", "unknown"


def _safe_device_state() -> str:
    try:
        return collect_device_probe_state()
    except Exception:
        return "error"


def _status_output() -> None:
    system, host_version, python_version = _safe_environment_summary()
    device_state = _safe_device_state()

    snapshot_count = _count_snapshot_artifacts()
    learning_count = len(list_learning_runs(LEARNING_RUNS_DIR))
    curated_counts = seed_summary()
    generated_ready = KNOWLEDGE_SUMMARY_PATH.is_file()

    console.print("[bold]IAPETUS STATUS[/bold]")
    console.print(f"Host OS        : {system}")
    console.print(f"Host Version   : {host_version}")
    console.print(f"Python Version : {python_version}")
    console.print(f"Device         : {device_state}")
    console.print(f"Snapshot count : {snapshot_count}")
    console.print(f"Learning runs  : {learning_count}")
    console.print(f"Curated fixtures: {curated_counts['fixture_sample_count']}")
    console.print(f"Generated absorb: {'ready' if generated_ready else 'not run'}")
    console.print("Mode           : seed")
    console.print("Upstream       : not connected (see: iapetus connectors)")

    latest = read_latest_learning_result(LEARNING_RUNS_DIR)
    if latest is not None:
        result, run_dir = latest
        console.print(f"Latest run     : {result.run_id} ({result.status})")
        if (run_dir / "entity_features.json").is_file():
            console.print("Latest artifacts: per-entity features present")


def _run_environment_device_probe() -> None:
    try:
        environment = collect_environment_info()
        device_state = collect_device_probe_state()
    except Exception as exc:
        console.print(f"[red]Probe failed: {exc}[/red]")
        raise typer.Exit(code=1)

    adb_status = "missing" if device_state == "adb_missing" else (
        "present" if device_state != "error" else "error"
    )
    console.print("[bold]ENVIRONMENT & DEVICE PROBE[/bold]")
    console.print(f"Host OS     : {environment.system}")
    console.print(f"Host Version: {environment.release}")
    console.print(f"Python      : {environment.python_version}")
    console.print(f"ADB         : {adb_status}")
    console.print(f"Device      : {device_state}")


def _run_connector_registry() -> None:
    console.print("[bold]CONNECTOR REGISTRY[/bold]")
    console.print("Seed placeholders only. Future adapters target learning-run entity artifacts.")
    for line in connector_registry_lines():
        console.print(line)


def _run_roadmap() -> None:
    console.print("[bold]ROADMAP[/bold]")
    console.print("M0  Kernel scaffold                 done")
    console.print("M1  Demo snapshot                   done")
    console.print("M2  Smoke learning engine           done")
    console.print("M3  Concept trainer (curated seed)  done")
    console.print("M3.5 Rich fixtures + per-entity     done")
    console.print("M4  Connector registry (seed stubs)  done")
    console.print("M5  Static MLP v1 (seed deep learn)  current")
    console.print("M6  Local Iapetus DB                later")
    console.print("M7  Read-only upstream connectors   later")
    console.print("M8  Device / emulator runtime       later")
    console.print("M9  Production-scale DL pipelines   later")


def _print_seed_about() -> None:
    console.print("[bold]HELP / ABOUT[/bold]")
    console.print("Iapetus is a seed-mode Android security deep-learning kernel.")
    console.print("Current features are demo fixture workflows and seed diagnostics only.")
    console.print("Upstream connectors and real orchestration remain planned for later milestones.")


def _run_demo_snapshot_summary() -> None:
    try:
        snapshot = build_demo_snapshot()
    except Exception as exc:
        console.print(f"[red]Demo snapshot preview failed: {exc}[/red]")
        raise typer.Exit(code=1)

    console.print("manifest.json")
    console.print("entities.json")
    console.print("labels.json")
    console.print(f"Name        : {snapshot.manifest.name}")
    console.print(f"Purpose     : {snapshot.manifest.purpose}")
    console.print(f"Entity count: {snapshot.manifest.entity_count}")


def _run_list(lines: Iterable[str]) -> None:
    for line in lines:
        console.print(line)


def _run_with_error_context(context: str, fn: Callable[[], None]) -> None:
    try:
        fn()
    except typer.Exit:
        raise
    except Exception as exc:
        console.print(f"[red]{context} failed: {exc}[/red]")
        raise typer.Exit(code=1)


@app.command()
def probe(check_device: bool = typer.Option(False, "--check-device", help="Run the quick device probe.")) -> None:
    """Print host environment details."""
    print_environment_probe(check_device=check_device)


@app.command()
def status() -> None:
    """Show seed system and pipeline status."""
    _status_output()


@app.command()
def roadmap() -> None:
    """Show milestone roadmap."""
    _run_roadmap()


@app.command()
def connectors() -> None:
    """Show upstream connector registry (seed placeholders)."""
    _run_connector_registry()


@app.command()
def device(timeout: float = typer.Option(2.0, "--timeout", help="Device probe timeout in seconds.")) -> None:
    """Run a quick, seed-only adb presence and connectivity probe."""
    if timeout <= 0:
        console.print("[red]Invalid timeout: must be a positive number of seconds.[/red]")
        raise typer.Exit(code=1)
    try:
        state = collect_device_probe_state(timeout_seconds=timeout)
    except Exception as exc:
        console.print(f"[red]Device probe execution failed: {exc}[/red]")
        raise typer.Exit(code=1)
    console.print(f"Device probe: {state}")


@app.command()
def menu(
    choice: int | None = typer.Option(None, help="Menu selection for non-interactive use.", min=0, max=8),
    deep_choice: int | None = typer.Option(
        None,
        "--deep-choice",
        help="Run deep-learning menu item directly (0-5).",
        min=0,
        max=5,
        show_default=False,
    ),
    console_command: str | None = typer.Option(
        None,
        "--console-command",
        "-c",
        help="Optional single command for Learning Console.",
        show_default=False,
    ),
) -> None:
    """Operator menu for the seed platform."""
    _run_list(menu_lines())

    if choice is None:
        if not sys.stdin.isatty():
            console.print(
                "[yellow]Non-interactive mode: pass --choice with a value 0-8 to run an item quickly.[/yellow]",
            )
            return
        choice = _prompt_choice("Select [0-8]: ", 0, 8)
        if choice is None:
            return

    if choice == 0:
        console.print("[green]Exiting operator menu.[/green]")
        return
    if choice == 1:
        def _run_deep() -> None:
            if not _run_deep_learning_menu(deep_choice=deep_choice):
                raise typer.Exit(code=1)

        _run_with_error_context("Run Deep Learning", _run_deep)
        return
    if choice == 2:
        _run_with_error_context(
            "Learning console",
            lambda: _run_learning_console(optional_command=console_command),
        )
        return
    if choice == 3:
        _run_with_error_context(
            "Demo snapshot preview",
            _run_demo_snapshot_summary,
        )
        return
    if choice == 4:
        _run_with_error_context("Label Laboratory", print_label_laboratory)
        return
    if choice == 5:
        _run_environment_device_probe()
        return
    if choice == 6:
        _run_connector_registry()
        return
    if choice == 7:
        _run_roadmap()
        return
    if choice == 8:
        _print_seed_about()
        return

    console.print("[red]Unknown menu selection.[/red]")


@labels_app.command("demo")
def labels_demo() -> None:
    """Print sample malware and normal app labels."""
    try:
        malware = MalwareLabel(
            platform="AndroidOS",
            malware_primary="Trojan",
            family="Anubis",
            variant="t",
            subtype="Banker",
        )
        normal = NormalAppLabel(
            platform="AndroidOS",
            app_name="Facebook",
            build_ref="64543615",
            app_category="SocialMedia",
        )
        console.print(render_malware_label(malware))
        console.print(render_normal_app_label(normal))
    except Exception as exc:
        console.print(f"[red]Label demo failed: {exc}[/red]")
        raise typer.Exit(code=1)


@snapshot_app.command("demo")
def snapshot_demo(
    write: bool = typer.Option(False, "--write", help="Write manifest.json, entities.json, and labels.json."),
    use_curated: bool = typer.Option(
        False,
        "--use-curated",
        help="Build snapshot from curated static-analysis fixtures.",
    ),
    output_dir: Path | None = None,
    name: str | None = None,
    purpose: str | None = None,
) -> None:
    """Print a demo or curated snapshot manifest and rendered labels."""
    if output_dir is None:
        output_dir = CURATED_SNAPSHOT_DIR if use_curated else DEMO_OUTPUT_DIR
    if name is None:
        name = "m3.5-curated-snapshot" if use_curated else "m1-demo-snapshot"
    if purpose is None:
        purpose = (
            "Curated fixture snapshot with static-analysis-shaped entities."
            if use_curated
            else "M1 demo snapshot containing seed entities and rendered labels."
        )

    if not name.strip():
        console.print("[red]Snapshot name cannot be empty.[/red]")
        raise typer.Exit(code=1)

    try:
        snapshot = build_curated_snapshot(name=name, purpose=purpose) if use_curated else build_demo_snapshot(
            name=name,
            purpose=purpose,
        )
    except Exception as exc:
        console.print(f"[red]Failed to build snapshot: {exc}[/red]")
        raise typer.Exit(code=1)

    if write:
        if output_dir.exists() and not output_dir.is_dir():
            console.print(f"[red]Output path is not a directory: {output_dir}[/red]")
            raise typer.Exit(code=1)
        try:
            snapshot_output(snapshot, output_dir=output_dir, write_curated_extras=use_curated)
        except (OSError, IOError) as exc:
            console.print(f"[red]Could not write snapshot files: {exc}[/red]")
            raise typer.Exit(code=1)

    console.print("[bold]Snapshot manifest[/bold]")
    console.print(snapshot.manifest.model_dump_json(indent=2))
    console.print("[bold]Labels[/bold]")
    for value in snapshot.labels:
        console.print(value)
    if write:
        console.print(f"[green]Wrote files to: {output_dir}[/green]")


@learn_app.command("run")
def learn_run(
    mode: str = typer.Option("smoke", "--mode", "-m", help="Learning mode: smoke | static-v1."),
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
        output_dir=output_dir or LEARNING_RUNS_DIR,
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
    _run_learn_predict(fixture, output_dir=output_dir or LEARNING_RUNS_DIR, run_id=run_id)


@learn_app.command("evaluate")
def learn_evaluate(
    run_id: str | None = typer.Option(None, "--run-id", help="Learning run id (default: latest)."),
    output_dir: Path | None = typer.Option(None, "--output-dir", help="Learning runs output directory."),
) -> None:
    """Re-score the curated corpus with a saved model bundle."""
    _run_learn_evaluate(output_dir=output_dir or LEARNING_RUNS_DIR, run_id=run_id)


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
    """Train static MLP v1 on the curated training corpus."""
    _run_static_v1_learning(write=write, output_dir=output_dir or LEARNING_RUNS_DIR, backend=backend)


def _run_bad_data_list() -> None:
    console.print("[bold]Adversarial test fixtures[/bold] (not training truth)")
    for item in load_bad_fixtures():
        slug = item.get("fixture_slug", item.get("sample_name"))
        console.print(f"- {slug}: {item.get('sample_name')}")


def _run_bad_data_validate() -> None:
    summary = summarize_bad_fixture_results()
    console.print("[bold]Bad-data validation[/bold]")
    console.print(f"Fixture count: {summary['fixture_count']}")
    console.print(f"Excluded from default learning: {summary['excluded_from_default_learning']}")
    console.print(f"Adversarial coverage OK: {summary.get('adversarial_coverage_ok')}")
    console.print(f"Curated quality OK: {summary.get('curated_quality_ok')}")
    for entry in summary["validations"]:
        issues = ", ".join(entry["issues"])
        console.print(
            f"- {entry['fixture_slug']} [{entry['severity']}] "
            f"eligible={entry.get('training_eligible', False)}: {issues}"
        )


def _run_bad_data_audit() -> None:
    audit = audit_adversarial_coverage()
    console.print("[bold]Adversarial coverage audit[/bold]")
    console.print(f"Coverage OK: {audit['adversarial_coverage_ok']}")
    for row in audit["adversarial_rows"]:
        status = "OK" if row["coverage_ok"] else "GAP"
        console.print(f"[{status}] {row['fixture_slug']}")
        if row["missing_expected"]:
            console.print(f"  missing expected: {', '.join(row['missing_expected'])}")
        if row["unexpected_extra"]:
            console.print(f"  unexpected extra: {', '.join(row['unexpected_extra'])}")
    console.print(f"Curated training-eligible: {audit['curated_training_eligible_count']}/{audit['curated_fixture_count']}")
    if audit["curated_with_blockers"]:
        console.print(f"Curated blockers: {', '.join(audit['curated_with_blockers'])}")


def _run_bad_data_regex_audit() -> None:
    report = run_regex_audit()
    console.print("[bold]Regex audit[/bold]")
    console.print(
        f"Label slips: {report['label_slip_count']}  "
        f"Permission slips: {report['permission_slip_count']}  "
        f"Package slips: {report['package_slip_count']}  "
        f"Consistency slips: {report['consistency_slip_count']}"
    )
    for row in report["label_probes"]:
        if row["slipped"]:
            console.print(f"[SLIP] label {row['probe']}: {row['detail']}")
    for row in report["permission_probes"]:
        if row["slipped"]:
            console.print(f"[SLIP] permission {row['probe']}: {row['detail']}")
    for row in report["package_probes"]:
        if row["slipped"]:
            console.print(f"[SLIP] package {row['probe']}: {row['detail']}")
    for row in report["rendered_consistency_probes"]:
        if row["slipped"]:
            console.print(f"[SLIP] consistency {row['probe']}: {row['rendered']}")
    if not report["all_ok"]:
        raise typer.Exit(code=1)
    console.print("All regex probes passed.")


def _run_bad_data_probe() -> None:
    report = run_stress_probe()
    console.print("[bold]Synthetic stress probe[/bold]")
    console.print(f"Probes: {report['probe_count']}")
    console.print(f"Slips (wrongly eligible): {report['slip_count']}")
    for row in report["probes"]:
        status = "SLIP" if row["slipped"] else "OK"
        console.print(f"[{status}] {row['probe']}: {', '.join(row['issues']) or 'none'}")
    if not report["all_blocked"]:
        raise typer.Exit(code=1)


def _run_bad_data_gaps() -> None:
    report = build_gap_report()
    console.print("[bold]Bad-data gap report[/bold]")
    for hole in report["open_holes"]:
        console.print(f"- {hole}")
    if report["adversarial_wrongly_eligible"]:
        console.print("Wrongly eligible adversarial:")
        for slug in report["adversarial_wrongly_eligible"]:
            console.print(f"- {slug}")
    if not report["stress_probe_all_blocked"] or report["adversarial_wrongly_eligible"]:
        raise typer.Exit(code=1)


def _run_bad_data_check_good() -> None:
    results = validate_curated_fixtures_quality()
    console.print("[bold]Curated fixture quality (training eligibility)[/bold]")
    for item in results:
        flag = "eligible" if item.training_eligible else "BLOCKED"
        console.print(f"- {item.fixture_slug}: {flag}")
        if item.training_blockers:
            console.print(f"    blockers: {', '.join(item.training_blockers)}")
    blocked = [item.fixture_slug for item in results if not item.training_eligible]
    if blocked:
        raise typer.Exit(code=1)


def _run_bad_data_show(fixture: str) -> None:
    try:
        item = resolve_bad_fixture(fixture)
    except KeyError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1)
    console.print("[bold]Adversarial fixture (raw)[/bold]")
    console.print(json.dumps(item, indent=2))


def _run_bad_data_explain(fixture: str) -> None:
    try:
        detail = explain_bad_fixture(fixture)
    except KeyError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1)
    console.print("[bold]Bad-data explanation[/bold]")
    console.print(f"Fixture: {detail['fixture_slug']}")
    console.print(f"Severity: {detail['severity']}")
    console.print(f"Issues: {', '.join(detail['issues'])}")
    if detail.get("android_markers"):
        console.print(f"Android-like markers: {', '.join(detail['android_markers'])}")
    if detail.get("windows_markers"):
        console.print(f"Windows-like markers: {', '.join(detail['windows_markers'])}")
    for message in detail.get("messages", []):
        console.print(f"- {message}")
    for hint in detail.get("remediation_hints", []):
        console.print(f"Remediation: {hint}")
    console.print(f"Training eligible: {detail.get('training_eligible', False)}")
    console.print(detail["explanation"])


def _run_bad_data_compare_good(bad: str, good: str) -> None:
    try:
        detail = compare_bad_to_good(bad, good)
    except KeyError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1)
    console.print("[bold]Bad vs good fixture comparison[/bold]")
    console.print(f"Bad : {detail['bad_fixture_slug']} ({', '.join(detail['bad_issues'])})")
    console.print(f"Good: {detail['good_fixture_slug']}")
    console.print(f"Android-like on bad : {', '.join(detail['android_like_on_bad']) or '(none)'}")
    console.print(f"Windows-like on bad : {', '.join(detail['windows_like_on_bad']) or '(none)'}")
    console.print(f"Android-like on good: {', '.join(detail['android_like_on_good']) or '(none)'}")
    console.print(detail["interpretation"])


@bad_data_app.command("list")
def bad_data_list() -> None:
    """List adversarial test fixtures."""
    _run_bad_data_list()


@bad_data_app.command("validate")
def bad_data_validate() -> None:
    """Validate all adversarial fixtures and print issue categories."""
    _run_bad_data_validate()


@bad_data_app.command("audit")
def bad_data_audit() -> None:
    """Audit adversarial expected-vs-detected issue coverage."""
    _run_bad_data_audit()


@bad_data_app.command("check-good")
def bad_data_check_good() -> None:
    """Verify curated good fixtures pass training quality gates."""
    _run_bad_data_check_good()


def _run_bad_data_edge_cases() -> None:
    report = run_edge_case_analysis()
    console.print("[bold]Edge-case analysis[/bold]")
    console.print(f"Cases: {report['case_count']}  Matched expectations: {report['coverage_ok_count']}")
    for row in report["cases"]:
        flag = "OK" if row["coverage_ok"] else "SURPRISE"
        eligible = "eligible" if row["training_eligible"] else "BLOCKED"
        console.print(
            f"[{flag}] {row['fixture_slug']}: {eligible} issues={', '.join(row['detected_issues']) or 'none'}"
        )
        if row["description"]:
            console.print(f"    {row['description']}")
        if row["observe_note"]:
            console.print(f"    [dim]Note: {row['observe_note']}[/dim]")
        if not row["coverage_ok"]:
            if row["missing_expected"]:
                console.print(f"    missing: {', '.join(row['missing_expected'])}")
            if row["unexpected_extra"]:
                console.print(f"    unexpected: {', '.join(row['unexpected_extra'])}")
            if row["expected_training_eligible"] is not None and not row["eligible_match"]:
                console.print(
                    f"    eligibility: expected {row['expected_training_eligible']} "
                    f"got {row['training_eligible']}"
                )
    if report["observe_only_cases"]:
        console.print("[bold]Observe-only (documented lenient behavior)[/bold]")
        for item in report["observe_only_cases"]:
            console.print(f"- {item['fixture_slug']}: {item['note']}")
    if not report["all_match_expectations"]:
        raise typer.Exit(code=1)


@bad_data_app.command("edge-cases")
def bad_data_edge_cases() -> None:
    """Run borderline fixtures and compare to expected validation outcomes."""
    _run_bad_data_edge_cases()


@bad_data_app.command("regex-audit")
def bad_data_regex_audit() -> None:
    """Run label/permission/package regex probes (must all match expectations)."""
    _run_bad_data_regex_audit()


@bad_data_app.command("probe")
def bad_data_probe() -> None:
    """Run synthetic bad-data stress probes (must all block training)."""
    _run_bad_data_probe()


@bad_data_app.command("gaps")
def bad_data_gaps() -> None:
    """Summarize open validation holes across adversarial and stress probes."""
    _run_bad_data_gaps()


@bad_data_app.command("show")
def bad_data_show(
    fixture: str = typer.Option(..., "--fixture", help="Adversarial fixture slug."),
) -> None:
    """Show raw adversarial fixture fields."""
    _run_bad_data_show(fixture=fixture)


@bad_data_app.command("explain")
def bad_data_explain(
    fixture: str = typer.Option(..., "--fixture", help="Adversarial fixture slug."),
) -> None:
    """Explain why an adversarial fixture is invalid or contradictory."""
    _run_bad_data_explain(fixture=fixture)


@bad_data_app.command("compare-good")
def bad_data_compare_good(
    bad: str = typer.Option(..., "--bad", help="Adversarial fixture slug."),
    good: str = typer.Option(..., "--good", help="Curated good fixture slug."),
) -> None:
    """Compare adversarial fixture against a trusted curated fixture."""
    _run_bad_data_compare_good(bad=bad, good=good)


def _run_data_sources() -> None:
    try:
        sources = list_source_manifests()
    except Exception as exc:
        console.print(f"[red]Could not load source manifests: {exc}[/red]")
        raise typer.Exit(code=1)

    console.print("[bold]DATA SOURCES[/bold]")
    if not sources:
        console.print("No sources configured.")
        return

    for source in sources:
        console.print(f"- {source.source_id} [{source.source_kind}, {source.trusted_level}]")
        console.print(f"  name     : {source.source_name}")
        console.print(f"  url      : {source.source_url}")
        console.print(f"  local    : {source.local_path}")
        console.print(f"  retrieved: {source.retrieved_at}")


def _run_data_manifest() -> None:
    if not SOURCE_MANIFEST_PATH.exists():
        console.print(f"Source manifest file not found: {SOURCE_MANIFEST_PATH}")
        return
    console.print(SOURCE_MANIFEST_PATH.read_text(encoding="utf-8"))


def _run_data_seed_summary() -> None:
    counts = seed_summary()
    console.print("[bold]seed summary[/bold]")
    console.print(f"permission seed count   : {counts['permission_seed_count']}")
    console.print(f"static token seed count : {counts['static_token_seed_count']}")
    console.print(f"fixture sample count    : {counts['fixture_sample_count']}")
    console.print(f"source manifest count   : {counts['source_manifest_count']}")


def _run_data_token_summary() -> None:
    summary = build_token_summary()
    console.print("[bold]token summary[/bold]")
    console.print("permissions by category:")
    for key, value in sorted(summary["permissions_by_category"].items()):
        console.print(f"- {key}: {value}")
    console.print("permissions by rough_risk:")
    for key, value in sorted(summary["permissions_by_rough_risk"].items()):
        console.print(f"- {key}: {value}")
    console.print("static tokens by token_type:")
    for key, value in sorted(summary["static_tokens_by_token_type"].items()):
        console.print(f"- {key}: {value}")
    console.print("fixture samples by entity_kind:")
    for key, value in sorted(summary["fixture_samples_by_entity_kind"].items()):
        console.print(f"- {key}: {value}")
    console.print("fixture samples by expected_classification:")
    for key, value in sorted(summary["fixture_samples_by_expected_classification"].items()):
        console.print(f"- {key}: {value}")
    suspicious = summary.get("suspicious_indicator_counts", {})
    if suspicious:
        console.print("suspicious indicators:")
        for key, value in sorted(suspicious.items()):
            console.print(f"- {key}: {value}")
    else:
        console.print("suspicious indicators: none")


def _run_data_validate() -> None:
    ok, issues, counts = validate_seed_payloads()
    if not ok:
        console.print("[red]data validation failed[/red]")
        for issue in issues:
            console.print(f"- {issue}")
        raise typer.Exit(code=1)

    console.print("[green]data validation passed[/green]")
    console.print(f"permission seeds : {counts['permission_seed_count']}")
    console.print(f"static tokens   : {counts['static_token_seed_count']}")
    console.print(f"fixture samples : {counts['fixture_sample_count']}")
    console.print(f"source manifests: {counts['source_manifest_count']}")


@learn_app.command("list")
def learn_list() -> None:
    """List known local learning runs."""
    _run_learning_list(output_dir=LEARNING_RUNS_DIR)


@learn_app.command("last")
def learn_last() -> None:
    """Show the latest local learning run."""
    _run_learning_last(output_dir=LEARNING_RUNS_DIR)


def _run_learn_absorb(generated_dir: Path | None = None) -> None:
    try:
        paths = absorb_curated_seed(generated_dir=generated_dir)
    except (OSError, ValueError) as exc:
        console.print(f"[red]Concept trainer absorb failed: {exc}[/red]")
        raise typer.Exit(code=1)
    root = generated_dir or GENERATED_DIR
    root.mkdir(parents=True, exist_ok=True)
    contract = build_training_quality_contract()
    audit = audit_adversarial_coverage()
    (root / "training_quality_contract.json").write_text(json.dumps(contract, indent=2), encoding="utf-8")
    (root / "adversarial_coverage_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    console.print("[bold]Concept trainer absorb[/bold]")
    for label, path in paths.items():
        console.print(f"Wrote {label}: {path}")
    console.print(f"Wrote training_quality_contract: {root / 'training_quality_contract.json'}")
    console.print(f"Wrote adversarial_coverage_audit: {root / 'adversarial_coverage_audit.json'}")
    console.print(f"Adversarial coverage OK: {audit['adversarial_coverage_ok']}")
    corpus = build_training_corpus()
    console.print(
        f"Training corpus: {corpus['training_example_count']} examples "
        f"(avg quality {corpus['average_training_quality_score']})"
    )


def _run_learn_explain_token(token: str) -> None:
    try:
        detail = explain_token(token)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1)
    console.print("[bold]Token explanation[/bold]")
    console.print(f"Token: {detail['token']}")
    console.print(f"Kind: {detail['kind']}")
    console.print(f"Found in seed: {detail['found']}")
    console.print(detail["explanation"])
    if detail.get("rough_risk"):
        console.print(f"Rough risk: {detail['rough_risk']}")
    if detail.get("token_type"):
        console.print(f"Token type: {detail['token_type']}")
    if detail.get("meaning"):
        console.print(f"Meaning: {detail['meaning']}")
    if detail.get("suspicious_when"):
        console.print(f"Suspicious when: {detail['suspicious_when']}")
    fixture_keys = detail.get("fixture_keys") or []
    if fixture_keys:
        console.print("Fixture usage:")
        for key in fixture_keys:
            console.print(f"- {key}")
    concepts = detail.get("related_concepts") or []
    if concepts:
        console.print(f"Related concepts: {', '.join(concepts)}")


def _print_token_group(title: str, values: list[str]) -> None:
    console.print(f"[bold]{title}[/bold]")
    if not values:
        console.print("- (none)")
        return
    for value in values:
        console.print(f"- {value}")


def _run_android_tokens(fixture: str) -> None:
    try:
        item = resolve_fixture(fixture)
        groups = extract_fixture_token_groups(item)
    except KeyError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1)
    console.print("[bold]Fixture token groups[/bold]")
    console.print(f"Fixture: {groups['fixture_slug']}")
    _print_token_group("permissions", groups["permissions"])
    _print_token_group("components", groups["components"])
    _print_token_group("intent_filters", groups["intent_filters"])
    _print_token_group("manifest_flags", groups["manifest_flags"])
    _print_token_group("network_strings", groups["network_strings"])
    _print_token_group("code_strings", groups["code_strings"])
    _print_token_group("suspicious_indicators", groups["suspicious_indicators"])
    _print_token_group("label_tokens", groups["label_tokens"])


def _run_learn_explain_fixture(fixture: str) -> None:
    try:
        detail = explain_fixture(fixture)
        quality = validate_fixture_quality(resolve_fixture(fixture))
    except KeyError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1)
    console.print("[bold]Fixture explanation[/bold]")
    console.print(f"Fixture: {detail['fixture_slug']}")
    console.print(f"Sample ID: {detail['sample_id']}")
    console.print(f"Package: {detail.get('package_name') or '(none)'}")
    console.print(f"Display name: {detail.get('display_name') or '(none)'}")
    console.print(f"Kind: {detail['entity_kind']}")
    console.print(f"Expected classification: {detail['expected_classification']}")
    console.print(f"Label: {detail['rendered_label']}")
    console.print("Permissions:")
    for entry in detail.get("permissions_detail", []):
        console.print(
            f"- {entry['permission']} ({entry['rough_risk']}, {entry['category']}): {entry['notes']}"
        )
    groups = detail.get("token_groups", {})
    _print_token_group("components", groups.get("components", []))
    _print_token_group("intent_filters", groups.get("intent_filters", []))
    _print_token_group("manifest_flags", groups.get("manifest_flags", []))
    _print_token_group("network_strings", groups.get("network_strings", []))
    _print_token_group("code_strings", groups.get("code_strings", []))
    _print_token_group("suspicious_indicators", groups.get("suspicious_indicators", []))
    console.print("[bold]Interpretation[/bold]")
    console.print(detail.get("interpretation", ""))
    console.print(f"Training eligible: {quality.training_eligible}")
    if quality.training_blockers:
        console.print(f"Training blockers: {', '.join(quality.training_blockers)}")


def _run_learn_compare_fixtures(left: str, right: str) -> None:
    try:
        detail = compare_fixtures(left, right)
    except KeyError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1)
    console.print("[bold]Fixture comparison[/bold]")
    console.print(
        f"Left : {detail['left']['fixture_slug']} "
        f"({detail['left']['entity_kind']}/{detail['left']['expected_classification']})"
    )
    console.print(
        f"Right: {detail['right']['fixture_slug']} "
        f"({detail['right']['entity_kind']}/{detail['right']['expected_classification']})"
    )
    _print_token_group("Shared permissions", detail["shared_permissions"])
    _print_token_group("Only left permissions", detail["only_left_permissions"])
    _print_token_group("Only right permissions", detail["only_right_permissions"])
    _print_token_group("Only left static tokens", detail["only_left_static_tokens"])
    _print_token_group("Only right static tokens", detail["only_right_static_tokens"])
    _print_token_group("Only left intent filters", detail["only_left_intent_filters"])
    _print_token_group("Only right intent filters", detail["only_right_intent_filters"])
    _print_token_group("Only left suspicious indicators", detail["only_left_suspicious_indicators"])
    _print_token_group("Only right suspicious indicators", detail["only_right_suspicious_indicators"])
    console.print("[bold]Interpretation[/bold]")
    console.print(detail.get("interpretation", ""))


def _run_learn_corpus() -> None:
    corpus = build_training_corpus()
    console.print("[bold]Training corpus (quality-gated)[/bold]")
    console.print(f"Examples: {corpus['training_example_count']} / {corpus['fixture_count']} fixtures")
    console.print(f"Malware: {corpus['malware_example_count']}  Benign: {corpus['normal_app_example_count']}")
    console.print(f"Quality score: avg {corpus['average_training_quality_score']}  "
                  f"min {corpus['min_training_quality_score']}  max {corpus['max_training_quality_score']}")
    console.print(f"Classifications: {', '.join(corpus['classifications'])}")
    for row in corpus["training_examples"]:
        console.print(
            f"  {row['fixture_slug']}: {row['entity_kind']} / {row['expected_classification']} "
            f"(score {row['training_quality_score']})"
        )
    if corpus["blocked_fixture_count"]:
        console.print(f"[yellow]Blocked: {corpus['blocked_fixture_count']}[/yellow]")


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


@android_app.command("tokens")
def android_tokens(
    fixture: str = typer.Option(..., "--fixture", help="Fixture slug (e.g. malware_banker)."),
) -> None:
    """Show grouped static-analysis tokens for a curated fixture."""
    _run_android_tokens(fixture=fixture)


@learn_app.command("compare-fixtures")
def learn_compare_fixtures(
    left: str = typer.Option(..., "--left", help="Left fixture slug."),
    right: str = typer.Option(..., "--right", help="Right fixture slug."),
) -> None:
    """Compare permissions and classification between two fixtures."""
    _run_learn_compare_fixtures(left=left, right=right)


@dataset_app.command("shape")
def dataset_shape() -> None:
    """Print a future dataset schema preview."""
    _run_dataset_shape_preview()


@data_app.command("sources")
def data_sources() -> None:
    """List configured source manifests."""
    _run_data_sources()


@data_app.command("manifest")
def data_manifest() -> None:
    """Show source manifest JSON."""
    _run_data_manifest()


@data_app.command("seed-summary")
def data_seed_summary() -> None:
    """Show curated seed counts."""
    _run_data_seed_summary()


@data_app.command("token-summary")
def data_token_summary() -> None:
    """Show seed token and fixture summary."""
    _run_data_token_summary()


@data_app.command("validate")
def data_validate() -> None:
    """Validate curated seed files and source manifests."""
    _run_data_validate()


@knowledge_app.command("concepts")
def knowledge_concepts() -> None:
    """List built-in knowledge concept IDs."""
    _run_knowledge_concepts()


@knowledge_app.command("show")
def knowledge_show(concept: str) -> None:
    """Show a built-in knowledge concept."""
    _run_knowledge_show(concept.strip())


@knowledge_app.command("apk-anatomy")
def knowledge_apk_anatomy() -> None:
    """Show the APK anatomy reference list."""
    _run_knowledge_apk_anatomy()


@knowledge_app.command("classify")
def knowledge_classify(path: str = typer.Option(..., "--path", help="Path to classify")) -> None:
    """Classify a file into a conservative artifact type."""
    _run_knowledge_classify(path=path)


@knowledge_app.command("teach")
def knowledge_teach(topic: str | None = typer.Argument(None, help="Optional lesson topic to print")) -> None:
    """Print a seed learning lesson for Android/AI operator context."""
    _run_knowledge_teach(topic=topic)


@knowledge_app.command("data")
def knowledge_data(topic: str | None = typer.Argument(None, help="Optional synthetic data topic")) -> None:
    """Show seed synthetic Android data used for learning."""
    _run_knowledge_data(topic=topic)


app.add_typer(labels_app, name="labels")
app.add_typer(snapshot_app, name="snapshot")
app.add_typer(learn_app, name="learn")
app.add_typer(android_app, name="android")
app.add_typer(dataset_app, name="dataset")
app.add_typer(data_app, name="data")
app.add_typer(knowledge_app, name="knowledge")
app.add_typer(bad_data_app, name="bad-data")

__all__ = ["app"]


if __name__ == "__main__":
    app()
