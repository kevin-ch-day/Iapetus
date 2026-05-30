from __future__ import annotations

from types import SimpleNamespace

import pytest
from typer.testing import CliRunner

from iapetus.cli import app


def test_probe_command_prints_basic_host_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "iapetus.cli.cli_console_and_path_helpers.collect_environment_info",
        lambda: SimpleNamespace(system="Windows", release="11", python_version="3.14.5"),
    )
    result = CliRunner().invoke(app, ["probe"])
    assert result.exit_code == 0
    assert "Iapetus environment probe" in result.stdout
    assert "Host OS       : Windows" in result.stdout
    assert "Host Version  : 11" in result.stdout
    assert "Python        : 3.14.5" in result.stdout
    assert "Device probe" not in result.stdout


def test_probe_command_can_include_device_probe_state(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "iapetus.cli.cli_console_and_path_helpers.collect_environment_info",
        lambda: SimpleNamespace(system="Ubuntu", release="24.04", python_version="3.12.4"),
    )
    monkeypatch.setattr("iapetus.cli.cli_console_and_path_helpers.collect_device_probe_state", lambda timeout_seconds=2.0: "connected")
    result = CliRunner().invoke(app, ["probe", "--check-device"])
    assert result.exit_code == 0
    assert "Host OS       : Ubuntu" in result.stdout
    assert "Device probe  : connected" in result.stdout
