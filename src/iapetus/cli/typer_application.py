"""Assemble the Iapetus Typer application."""
from __future__ import annotations

import typer

from iapetus.cli.typer_android_fixture_commands import android_app
from iapetus.cli.typer_adversarial_validation_commands import bad_data_app
from iapetus.cli.typer_connector_catalog_commands import connectors_app
from iapetus.cli.host_platform_probe_commands import register_core_commands
from iapetus.cli.typer_curated_seed_data_commands import data_app
from iapetus.cli.typer_dataset_preview_commands import dataset_app
from iapetus.cli.typer_diagnostics_commands import doctor_app
from iapetus.cli.typer_learning_database_commands import db_app
from iapetus.cli.typer_knowledge_seed_commands import knowledge_app
from iapetus.cli.typer_learning_command_group import learn_app
from iapetus.cli.interactive_operator_menu import register_menu_command
from iapetus.cli.typer_snapshot_subcommands import labels_app, snapshot_app

app = typer.Typer(help="Iapetus Android security deep-learning kernel.")

register_core_commands(app)
register_menu_command(app)

app.add_typer(labels_app, name="labels")
app.add_typer(snapshot_app, name="snapshot")
app.add_typer(learn_app, name="learn")
app.add_typer(android_app, name="android")
app.add_typer(dataset_app, name="dataset")
app.add_typer(data_app, name="data")
app.add_typer(knowledge_app, name="knowledge")
app.add_typer(bad_data_app, name="bad-data")
app.add_typer(db_app, name="db")
app.add_typer(connectors_app, name="connectors")
app.add_typer(doctor_app, name="doctor")
