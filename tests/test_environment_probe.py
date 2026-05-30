from __future__ import annotations

import pytest
from iapetus.probes.host_environment_probe import collect_environment_info


def test_environment_probe_returns_system_info() -> None:
    probe = collect_environment_info()
    assert probe.system
    assert probe.release
    assert probe.python_version


def test_collect_environment_info_prefers_linux_version_id(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("iapetus.probes.host_environment_probe.platform.system", lambda: "Linux")
    monkeypatch.setattr("iapetus.probes.host_environment_probe._parse_release_from_os_release", lambda: "41")
    monkeypatch.setattr("iapetus.probes.host_environment_probe.platform.release", lambda: "6.5.0-mock")
    assert collect_environment_info().release == "41"


def test_collect_environment_info_windows_release_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("iapetus.probes.host_environment_probe.platform.system", lambda: "Windows")
    monkeypatch.setattr("iapetus.probes.host_environment_probe.platform.release", lambda: "11")
    assert collect_environment_info().release == "11"
