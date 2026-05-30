from __future__ import annotations

from typer.testing import CliRunner

from iapetus.cli import app


def test_doctor_command_prints_layout() -> None:
    result = CliRunner().invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "IAPETUS DOCTOR" in result.stdout
    assert "Learning runs dir" in result.stdout
    assert "Fixture samples" in result.stdout
