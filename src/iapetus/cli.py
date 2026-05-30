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
from iapetus.probes.environment import collect_device_probe_state, collect_environment_info
from iapetus.snapshots.demo import (
    DEMO_OUTPUT_DIR,
    build_demo_snapshot,
    demo_fixtures,
    snapshot_output,
)
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


def _run_smoke_learning_summary() -> LearningRunResult:
    result, _ = build_smoke_result(dataset_name="demo fixtures")
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
    console.print("  [1] Smoke learning run       demo fixtures only")
    console.print("  [2] Development run          not available yet")
    console.print("  [3] Full training run        not available yet")
    console.print("  [4] Watch mode               not available yet")
    console.print("  [0] Back")

    if deep_choice is None:
        if not sys.stdin.isatty():
            console.print(
                "[yellow]Non-interactive mode: pass --deep-choice 1 for smoke run.[/yellow]",
            )
            return True
        deep_choice = _prompt_choice("Select [0-4]: ", 0, 4)
        if deep_choice is None:
            return False

    if deep_choice == 0:
        return True
    if deep_choice == 1:
        _run_smoke_learning_summary()
        return True
    if deep_choice in {2, 3, 4}:
        console.print("[yellow]Not available yet in seed mode.[/yellow]")
        return True

    console.print("[red]Invalid selection; choose 0-4.[/red]")
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


def _run_learning_run(
    mode: str,
    write: bool,
    output_dir: Path,
    notes: str | None = None,
    use_curated: bool = False,
) -> None:
    normalized_mode = mode.strip().lower()
    if normalized_mode != "smoke":
        console.print(f"Learning mode '{mode}' is not available in seed kernel yet.")
        raise typer.Exit(code=1)

    if output_dir.exists() and not output_dir.is_dir():
        console.print(f"[red]Output path must be a directory: {output_dir}[/red]")
        raise typer.Exit(code=1)

    dataset_name = "curated seed fixtures" if use_curated else "demo fixtures"
    result, labels = build_smoke_result(dataset_name=dataset_name, use_curated_fixtures=use_curated)
    if notes and notes.strip():
        result = result.model_copy(update={"notes": notes})

    if write:
        run_dir = output_dir / result.run_id
        try:
            write_learning_artifacts(result, labels, run_dir)
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
    return command.strip().lower() in {
        "help",
        "status",
        "labels",
        "snapshot",
        "learn smoke",
        "learn list",
        "learn last",
        "dataset shape",
        "roadmap",
        "connectors",
        "exit",
        "",
    }


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
        "entities",
        "labels",
        "permission observations",
        "static features",
        "dynamic windows",
        "AV tokens",
        "review decisions",
        "training examples",
    ]:
        console.print(f"- {item}")


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

    console.print("[bold]IAPETUS STATUS[/bold]")
    console.print(f"Host OS        : {system}")
    console.print(f"Host Version   : {host_version}")
    console.print(f"Python Version : {python_version}")
    console.print(f"Device         : {device_state}")
    console.print(f"Snapshot count : {snapshot_count}")
    console.print(f"Learning runs  : {learning_count}")
    console.print("Mode           : seed")
    console.print("Upstream       : not connected")


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
    console.print("Erebus             : not connected")
    console.print("Permission Intel   : not connected")
    console.print("ScytaleDroid       : not connected")
    console.print("ObsidianDroid      : not connected")
    console.print("Web review exports : not connected")
    console.print("Physical device    : not connected")
    console.print("Emulator / VM      : not connected")


def _run_roadmap() -> None:
    console.print("[bold]ROADMAP[/bold]")
    console.print("M0  Kernel scaffold                 done")
    console.print("M1  Demo snapshot                   done")
    console.print("M2  Smoke learning engine           current")
    console.print("M3  Connector registry              next")
    console.print("M4  Local Iapetus DB                later")
    console.print("M5  Read-only upstream connectors   later")
    console.print("M6  Device / emulator runtime       later")
    console.print("M7  Real deep-learning models       later")


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
        help="Run deep-learning menu item directly (0-4).",
        min=0,
        max=4,
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
    output_dir: Path = Path(DEMO_OUTPUT_DIR),
    name: str = "m1-demo-snapshot",
    purpose: str = "M1 demo snapshot containing seed entities and rendered labels.",
) -> None:
    """Print a tiny demo snapshot manifest and rendered labels."""
    if not name.strip():
        console.print("[red]Snapshot name cannot be empty.[/red]")
        raise typer.Exit(code=1)

    if not purpose.strip():
        console.print("[yellow]Snapshot purpose is empty; using a placeholder description.[/yellow]")
        purpose = "M1 demo snapshot"

    try:
        snapshot = build_demo_snapshot(name=name, purpose=purpose)
    except Exception as exc:
        console.print(f"[red]Failed to build demo snapshot: {exc}[/red]")
        raise typer.Exit(code=1)

    if write:
        if output_dir.exists() and not output_dir.is_dir():
            console.print(f"[red]Output path is not a directory: {output_dir}[/red]")
            raise typer.Exit(code=1)
        try:
            snapshot_output(snapshot, output_dir=output_dir)
        except (OSError, IOError) as exc:
            console.print(f"[red]Could not write snapshot files: {exc}[/red]")
            raise typer.Exit(code=1)

    console.print("[bold]Snapshot manifest[/bold]")
    console.print(snapshot.manifest.model_dump_json(indent=2))
    console.print("[bold]Demo labels[/bold]")
    for value in snapshot.labels:
        console.print(value)
    if write:
        console.print(f"[green]Wrote files to: {output_dir}[/green]")


@learn_app.command("run")
def learn_run(
    mode: str = typer.Option("smoke", "--mode", "-m", help="Learning mode: smoke."),
    write: bool = typer.Option(False, "--write", help="Write learning run artifacts."),
    use_curated: bool = typer.Option(
        False,
        "--use-curated",
        help="Use curated data seed files instead of hardcoded fixtures.",
    ),
    output_dir: Path = LEARNING_RUNS_DIR,
    notes: str = "Seed smoke learning run (fixture-backed, no model training).",
) -> None:
    """Run a seed smoke learning pass."""
    _run_learning_run(
        mode=mode,
        write=write,
        output_dir=output_dir,
        notes=notes,
        use_curated=use_curated,
    )


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
app.add_typer(dataset_app, name="dataset")
app.add_typer(data_app, name="data")
app.add_typer(knowledge_app, name="knowledge")

__all__ = ["app"]


if __name__ == "__main__":
    app()
