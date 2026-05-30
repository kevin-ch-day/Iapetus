from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable, Iterable

import typer
from rich.console import Console

from iapetus.labels.renderer import (
    MalwareLabel,
    NormalAppLabel,
    render_malware_label,
    render_normal_app_label,
)
from iapetus.probes.environment import collect_device_probe_state, collect_environment_info
from iapetus.snapshots.demo import (
    DEMO_OUTPUT_DIR,
    build_demo_snapshot,
    demo_fixtures,
    snapshot_output,
)

app = typer.Typer(help="Iapetus Android security deep-learning kernel.")
labels_app = typer.Typer(help="Label rendering helpers.")
snapshot_app = typer.Typer(help="Snapshot helpers.")
console = Console()
MENU_SEPARATOR = "=" * 78


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
        _menu_line("Data", "demo fixtures only"),
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


def _run_smoke_learning() -> None:
    malware_entities, normal_entities = demo_fixtures()
    console.print("Learning run: smoke")
    console.print("Dataset     : demo fixtures")
    console.print(f"Entities    : {len(malware_entities) + len(normal_entities)}")
    console.print(f"Malware     : {len(malware_entities)}")
    console.print(f"Normal apps : {len(normal_entities)}")
    console.print("Model       : smoke_placeholder")
    console.print("Status      : PASS")


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
        _run_smoke_learning()
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
        print_environment_probe()
        return True
    if command == "labels":
        print_label_laboratory()
        return True
    if command == "snapshot":
        _run_demo_snapshot_summary()
        return True
    if command == "learn smoke":
        _run_smoke_learning()
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
        "entity_id",
        "entity_kind",
        "platform",
        "package_name",
        "sha256",
        "rendered_label",
        "permission_tokens",
        "av_tokens",
        "static_features",
        "dynamic_features",
        "target_label",
        "provenance",
    ]:
        console.print(f"- {item}")


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
    console.print("M1  Demo snapshot                   current")
    console.print("M2  Smoke learning engine           next")
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


app.add_typer(labels_app, name="labels")
app.add_typer(snapshot_app, name="snapshot")

__all__ = ["app"]


if __name__ == "__main__":
    app()
