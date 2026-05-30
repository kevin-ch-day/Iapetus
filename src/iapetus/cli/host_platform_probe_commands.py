"""Top-level kernel commands: probe, status, roadmap, device."""
from __future__ import annotations

from pathlib import Path

import typer

from iapetus.curated_seed_library_exports import KNOWLEDGE_SUMMARY_PATH, seed_summary
from iapetus.learning import list_learning_runs, read_latest_learning_result
import iapetus.cli.cli_console_and_path_helpers as cli_common
from iapetus.cli.cli_console_and_path_helpers import console, print_environment_probe


def _count_snapshot_artifacts() -> int:
    path = Path(cli_common.DEMO_OUTPUT_DIR)
    if not path.is_dir():
        return 0
    expected_files = {"manifest.json", "entities.json", "labels.json"}
    if all((path / name).is_file() for name in expected_files):
        return 1
    return 0


def _safe_environment_summary() -> tuple[str, str, str]:
    try:
        environment = cli_common.collect_environment_info()
        return environment.system, environment.release, environment.python_version
    except Exception:
        return "Unknown", "unknown", "unknown"


def _safe_device_state() -> str:
    try:
        return cli_common.collect_device_probe_state()
    except Exception:
        return "error"


def _status_output() -> None:
    system, host_version, python_version = _safe_environment_summary()
    device_state = _safe_device_state()

    snapshot_count = _count_snapshot_artifacts()
    learning_count = len(list_learning_runs(cli_common.LEARNING_RUNS_DIR))
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

    latest = read_latest_learning_result(cli_common.LEARNING_RUNS_DIR)
    if latest is not None:
        result, run_dir = latest
        console.print(f"Latest run     : {result.run_id} ({result.status})")
        if (run_dir / "entity_features.json").is_file():
            console.print("Latest artifacts: per-entity features present")


def _run_environment_device_probe() -> None:
    try:
        environment = cli_common.collect_environment_info()
        device_state = cli_common.collect_device_probe_state()
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


def _run_roadmap() -> None:
    console.print("[bold]ROADMAP[/bold]")
    console.print("M0  Kernel scaffold                 done")
    console.print("M1  Demo snapshot                   done")
    console.print("M2  Smoke learning engine           done")
    console.print("M3  Concept trainer (curated seed)  done")
    console.print("M3.5 Rich fixtures + per-entity     done")
    console.print("M4  Connector registry (seed stubs)  done")
    console.print("M5  Static MLP v2 (seed deep learn)  done")
    console.print("M6  Learning run index (SQLite)    seed")
    console.print("M7  Read-only upstream connectors   later")
    console.print("M8  Device / emulator runtime       later")
    console.print("M9  Production-scale DL pipelines   later")


def _print_seed_about() -> None:
    console.print("[bold]HELP / ABOUT[/bold]")
    console.print("Iapetus is a seed-mode Android security deep-learning kernel.")
    console.print("Current features are demo fixture workflows and seed diagnostics only.")
    console.print("Upstream connectors and real orchestration remain planned for later milestones.")


def register_core_commands(app: typer.Typer) -> None:
    @app.command()
    def probe(
        check_device: bool = typer.Option(False, "--check-device", help="Run the quick device probe."),
    ) -> None:
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
    def device(
        timeout: float = typer.Option(2.0, "--timeout", help="Device probe timeout in seconds."),
    ) -> None:
        """Run a quick, seed-only adb presence and connectivity probe."""
        if timeout <= 0:
            console.print("[red]Invalid timeout: must be a positive number of seconds.[/red]")
            raise typer.Exit(code=1)
        try:
            state = cli_common.collect_device_probe_state(timeout_seconds=timeout)
        except Exception as exc:
            console.print(f"[red]Device probe execution failed: {exc}[/red]")
            raise typer.Exit(code=1)
        console.print(f"Device probe: {state}")
