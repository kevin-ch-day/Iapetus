from __future__ import annotations

from typer.testing import CliRunner

from iapetus.cli import app, menu_lines


def test_menu_lines_have_operator_console_layout() -> None:
    lines = menu_lines()
    assert any("[1] Run Deep Learning" in line for line in lines)
    assert any("[2] Learning Console" in line for line in lines)
    assert any("[3] Build / View Demo Snapshot" in line for line in lines)
    assert any("[4] Label Laboratory" in line for line in lines)
    assert any("[5] Environment & Device Probe" in line for line in lines)
    assert any("[6] Connector Registry" in line for line in lines)
    assert any("[7] Roadmap" in line for line in lines)
    assert any("[8] Help / About" in line for line in lines)
    assert any("Mode        : seed" in line for line in lines)


def test_menu_run_deep_learning_smoke() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["menu", "--choice", "1", "--deep-choice", "1"])
    assert result.exit_code == 0
    assert "RUN DEEP LEARNING" in result.stdout
    assert "Learning run: smoke" in result.stdout
    assert "Dataset     : demo fixtures" in result.stdout
    assert "Entities    : 6" in result.stdout
    assert "Malware     : 3" in result.stdout
    assert "Normal apps : 3" in result.stdout
    assert "Status      : PASS" in result.stdout


def test_menu_run_deep_learning_pending_items_show_seed_notice() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["menu", "--choice", "1", "--deep-choice", "2"])
    assert result.exit_code == 0
    assert "Not available yet in seed mode." in result.stdout


def test_menu_learning_console_help_command() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["menu", "--choice", "2", "-c", "help"])
    assert result.exit_code == 0
    assert "LEARNING CONSOLE" in result.stdout
    assert "iapetus> status" in result.stdout
    assert "iapetus> labels" in result.stdout
    assert "iapetus> snapshot" in result.stdout
    assert "iapetus> learn smoke" in result.stdout
    assert "iapetus> connectors" in result.stdout
    assert "iapetus> help" in result.stdout
    assert "iapetus> exit" in result.stdout


def test_menu_learning_console_unknown_batch_command_fails() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["menu", "--choice", "2", "--console-command", "mystery"])
    assert result.exit_code == 1
    assert "Unknown command: mystery" in result.stdout


def test_menu_learning_console_batch_exit_command() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["menu", "--choice", "2", "--console-command", "exit"])
    assert result.exit_code == 0
    assert "Learning console closed." in result.stdout


def test_menu_deep_learning_invalid_choice_fails() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["menu", "--choice", "1", "--deep-choice", "5"])
    assert result.exit_code == 2
    assert "Invalid value for '--deep-choice'" in result.stderr


def test_menu_snapshot_builder_choice() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["menu", "--choice", "3"])
    assert result.exit_code == 0
    assert "manifest.json" in result.stdout
    assert "entities.json" in result.stdout
    assert "labels.json" in result.stdout
    assert "Entity count: 6" in result.stdout


def test_menu_label_laboratory_choice() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["menu", "--choice", "4"])
    assert result.exit_code == 0
    assert "LABEL LABORATORY" in result.stdout
    assert "AndroidOS:Trojan.Anubis-t:[Banker]" in result.stdout
    assert "platform:malware_primary.family-variant:[subtype]" in result.stdout


def test_menu_environment_probe_choice() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["menu", "--choice", "5"])
    assert result.exit_code == 0
    assert "ENVIRONMENT & DEVICE PROBE" in result.stdout
    assert "Host OS" in result.stdout
    assert "ADB" in result.stdout
    assert "Device" in result.stdout


def test_menu_connector_registry_choice() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["menu", "--choice", "6"])
    assert result.exit_code == 0
    assert "CONNECTOR REGISTRY" in result.stdout
    assert "Erebus             : not connected" in result.stdout
    assert "ObsidianDroid      : not connected" in result.stdout


def test_menu_roadmap_choice() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["menu", "--choice", "7"])
    assert result.exit_code == 0
    assert "ROADMAP" in result.stdout
    assert "M0  Kernel scaffold                 done" in result.stdout
    assert "M1  Demo snapshot                   current" in result.stdout
    assert "M7  Real deep-learning models       later" in result.stdout


def test_menu_help_choice() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["menu", "--choice", "8"])
    assert result.exit_code == 0
    assert "HELP / ABOUT" in result.stdout
    assert "seed-mode" in result.stdout


def test_menu_choice_invalid_integer_is_cleanly_rejected() -> None:
    result = CliRunner().invoke(app, ["menu", "--choice", "99"])
    assert result.exit_code == 2
