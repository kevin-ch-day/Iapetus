"""Environment and layout diagnostics."""
from __future__ import annotations

import typer

from iapetus import project_filesystem_paths as paths
from iapetus.data.curated_seed_loaders import seed_summary
from iapetus.database import kernel_database_health, learning_index_status

import iapetus.cli.cli_console_and_path_helpers as cli_common
from iapetus.cli.cli_console_and_path_helpers import console

doctor_app = typer.Typer(help="Seed kernel diagnostics.")


def print_doctor_report() -> None:
    console.print("[bold]IAPETUS DOCTOR[/bold]")
    console.print(f"Data dir           : {paths.DATA_DIR.resolve()}")
    console.print(f"Generated dir      : {paths.GENERATED_DIR.resolve()}")
    console.print(f"Learning runs dir  : {paths.LEARNING_RUNS_DIR.resolve()}")
    console.print(f"Demo snapshot dir  : {paths.DEMO_OUTPUT_DIR.resolve()}")

    summary = seed_summary()
    console.print(f"Fixture samples    : {summary['fixture_sample_count']}")
    console.print(f"Permission seeds   : {summary['permission_seed_count']}")
    console.print(f"Static token seeds : {summary['static_token_seed_count']}")

    try:
        from iapetus.learning.deep.static_mlp_trainer import torch_available

        console.print(f"PyTorch available  : {torch_available()}")
    except Exception as exc:
        console.print(f"PyTorch available  : unknown ({exc})")

    console.print(f"Learning index DB  : {paths.LEARNING_INDEX_DB_PATH.resolve()}")
    health = kernel_database_health()
    console.print(f"Index exists       : {health['exists']}")
    if health["exists"]:
        console.print(f"Schema version     : v{health.get('stored_schema_version')}")
        console.print(f"Integrity OK       : {health['integrity_ok']}")
    reg = learning_index_status()
    console.print(f"Indexed runs       : {reg['run_count']}")

    try:
        cli_common.collect_environment_info()
        device = cli_common.collect_device_probe_state(timeout_seconds=1.0)
        console.print(f"Device probe       : {device}")
    except Exception as exc:
        console.print(f"Device probe       : error ({exc})")


@doctor_app.callback(invoke_without_command=True)
def doctor_main(ctx: typer.Context) -> None:
    """Print resolved paths, seed counts, registry, and optional torch/device probes."""
    if ctx.invoked_subcommand is not None:
        return
    print_doctor_report()
