from __future__ import annotations

import subprocess
import pytest

from iapetus.probes.host_environment_probe import collect_device_probe_state
from typer.testing import CliRunner

from iapetus.cli import app


class _RunResult:
    def __init__(self, returncode: int = 0, stdout: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout


def test_device_probe_without_adb(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("iapetus.probes.host_environment_probe.shutil.which", lambda name: None)
    assert collect_device_probe_state() == "adb_missing"


def test_device_probe_disconnected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("iapetus.probes.host_environment_probe.shutil.which", lambda name: "adb")

    def _fake_run(*args, **kwargs):
        return _RunResult(0, "List of devices attached\n")

    monkeypatch.setattr("iapetus.probes.host_environment_probe.subprocess.run", _fake_run)
    assert collect_device_probe_state() == "disconnected"


def test_device_probe_connected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("iapetus.probes.host_environment_probe.shutil.which", lambda name: "adb")

    def _fake_run(*args, **kwargs):
        return _RunResult(0, "List of devices attached\nemulator-5554\tdevice\n")

    monkeypatch.setattr("iapetus.probes.host_environment_probe.subprocess.run", _fake_run)
    assert collect_device_probe_state() == "connected"


def test_device_probe_unauthorized(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("iapetus.probes.host_environment_probe.shutil.which", lambda name: "adb")

    def _fake_run(*args, **kwargs):
        return _RunResult(0, "List of devices attached\nemulator-5554\tunauthorized\n")

    monkeypatch.setattr("iapetus.probes.host_environment_probe.subprocess.run", _fake_run)
    assert collect_device_probe_state() == "unauthorized"


def test_device_probe_offline_reports_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("iapetus.probes.host_environment_probe.shutil.which", lambda name: "adb")

    def _fake_run(*args, **kwargs):
        return _RunResult(0, "List of devices attached\ntest-device\toffline\n")

    monkeypatch.setattr("iapetus.probes.host_environment_probe.subprocess.run", _fake_run)
    assert collect_device_probe_state() == "error"


def test_device_probe_multiple_devices(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("iapetus.probes.host_environment_probe.shutil.which", lambda name: "adb")

    def _fake_run(*args, **kwargs):
        return _RunResult(
            0,
            "List of devices attached\nemulator-5554\tdevice\nemulator-5555\tdevice\n",
        )

    monkeypatch.setattr("iapetus.probes.host_environment_probe.subprocess.run", _fake_run)
    assert collect_device_probe_state() == "multiple_devices"


def test_device_probe_error_on_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("iapetus.probes.host_environment_probe.shutil.which", lambda name: "adb")
    monkeypatch.setattr(
        "iapetus.probes.host_environment_probe.subprocess.run",
        lambda *args, **kwargs: (_ for _ in ()).throw(subprocess.TimeoutExpired(cmd="adb", timeout=2.0)),
    )
    assert collect_device_probe_state() == "error"


def test_device_command_reports_probe_state(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("iapetus.probes.host_environment_probe.shutil.which", lambda name: "adb")

    def _fake_run(*args, **kwargs):
        return _RunResult(0, "List of devices attached\nemulator-5554\tdevice\n")

    monkeypatch.setattr("iapetus.probes.host_environment_probe.subprocess.run", _fake_run)
    result = CliRunner().invoke(app, ["device"])
    assert result.exit_code == 0
    assert "Device probe: connected" in result.stdout


def test_device_command_invalid_timeout_exits() -> None:
    result = CliRunner().invoke(app, ["device", "--timeout", "0"])
    assert result.exit_code == 1
    assert "Invalid timeout" in result.stdout
