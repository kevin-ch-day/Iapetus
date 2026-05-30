from __future__ import annotations

from typer.testing import CliRunner

from iapetus.cli import app
from iapetus.connectors import list_connectors


def test_connector_registry_lists_seed_stubs() -> None:
    connectors = list_connectors()
    assert len(connectors) >= 7
    erebus = next(item for item in connectors if item.connector_id == "erebus")
    assert erebus.read_only is True
    assert "entity_features.json" in erebus.planned_entity_artifacts


def test_connectors_cli_shows_planned_artifacts() -> None:
    result = CliRunner().invoke(app, ["connectors"])
    assert result.exit_code == 0
    assert "planned artifacts" in result.stdout
    assert "entity_token_groups.json" in result.stdout


def test_connectors_show_erebus() -> None:
    result = CliRunner().invoke(app, ["connectors", "show", "erebus"])
    assert result.exit_code == 0
    assert "Erebus" in result.stdout
    assert "entity_features.json" in result.stdout


def test_connectors_show_unknown() -> None:
    result = CliRunner().invoke(app, ["connectors", "show", "not_a_connector"])
    assert result.exit_code == 1
