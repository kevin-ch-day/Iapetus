from __future__ import annotations

from dataclasses import dataclass
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Literal

DeviceProbeState = Literal[
    "not_checked",
    "adb_missing",
    "disconnected",
    "connected",
    "unauthorized",
    "multiple_devices",
    "error",
]


@dataclass(frozen=True)
class EnvironmentProbe:
    system: str
    release: str
    python_version: str


def _linux_release_or_fallback() -> str:
    version = _parse_release_from_os_release()
    if version:
        return version
    return platform.release()


def _parse_release_from_os_release() -> str:
    os_release = Path("/etc/os-release")
    if not os_release.exists():
        return ""

    version = ""
    try:
        content = os_release.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""

    for line in content.splitlines():
        if not line.startswith("VERSION_ID="):
            continue
        version = line.split("=", 1)[1].strip().strip('"')
        break

    if version:
        return version

    for line in content.splitlines():
        if line.startswith("VERSION="):
            version = line.split("=", 1)[1].strip().strip('"')
            break

    return version


def collect_environment_info() -> EnvironmentProbe:
    system = platform.system()
    if system == "Linux":
        release = _linux_release_or_fallback()
    elif system == "Windows":
        release = platform.release()
    else:
        release = platform.release()

    return EnvironmentProbe(
        system=system,
        release=release,
        python_version=platform.python_version(),
    )


def collect_device_probe_state(timeout_seconds: float = 2.0) -> DeviceProbeState:
    adb_command = shutil.which("adb")
    if adb_command is None:
        return "adb_missing"

    try:
        result = subprocess.run(
            [adb_command, "devices"],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return "error"

    if result.returncode != 0:
        return "error"

    rows = [
        line.strip()
        for line in result.stdout.splitlines()
        if line.strip() and not line.strip().startswith("List of devices attached")
    ]
    if not rows:
        return "disconnected"

    if len(rows) > 1:
        return "multiple_devices"

    status = rows[0].split()
    if len(status) < 2:
        return "error"
    if status[1] == "unauthorized":
        return "unauthorized"
    return "connected"
