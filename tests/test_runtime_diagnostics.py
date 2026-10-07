"""Tests for runtime environment diagnostics. No rendering, no network."""
import sys

import pytest

from composition import diagnostics as diagnostics_module
from composition.diagnostics import diagnose_all, diagnose_runtime
from composition.runtime import RuntimeStatus
from composition.runtime_registry import create_default_registry


def test_diagnostics_have_structured_shape():
    for diag in diagnose_all(create_default_registry()):
        assert set(diag) == {"runtime_id", "status", "version", "checks", "remote_available"}
        assert diag["status"] in {status.value for status in RuntimeStatus}
        assert diag["checks"]
        for check in diag["checks"]:
            assert set(check) == {"name", "status", "message", "severity"}
            assert check["status"] in {"pass", "fail", "warn"}


def test_unknown_status_is_never_available():
    assert RuntimeStatus.UNKNOWN.value != RuntimeStatus.AVAILABLE.value
    registry = create_default_registry()
    diag = diagnose_runtime(registry.get("hyperframes"))
    assert diag["status"] in {RuntimeStatus.UNAVAILABLE.value, RuntimeStatus.UNKNOWN.value, RuntimeStatus.MISCONFIGURED.value}
    assert diag["status"] != RuntimeStatus.AVAILABLE.value


def test_missing_toolchain_reports_unavailable(monkeypatch):
    monkeypatch.setattr(diagnostics_module, "_command_version", lambda command, args: None)
    registry = create_default_registry()
    assert diagnose_runtime(registry.get("remotion"))["status"] == RuntimeStatus.UNAVAILABLE.value
    assert diagnose_runtime(registry.get("ffmpeg_pil"))["status"] == RuntimeStatus.UNAVAILABLE.value


def test_toolchain_without_project_reports_misconfigured(monkeypatch, tmp_path):
    monkeypatch.setattr(diagnostics_module, "_command_version", lambda command, args: "v9.9.9")
    monkeypatch.setattr(diagnostics_module, "FACTORY_ROOT", tmp_path)
    registry = create_default_registry()
    diag = diagnose_runtime(registry.get("remotion"))
    assert diag["status"] == RuntimeStatus.MISCONFIGURED.value


def test_ffmpeg_detection_reports_real_binary():
    registry = create_default_registry()
    diag = diagnose_runtime(registry.get("ffmpeg_pil"))
    names = {check["name"] for check in diag["checks"]}
    assert {"python_available", "pillow_available", "ffmpeg_available"} <= names


def test_cli_runtime_list_exits_zero(monkeypatch, capsys):
    import production.__main__ as cli

    monkeypatch.setattr(sys, "argv", ["production", "runtime-list"])
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 0
    assert "hyperframes" in capsys.readouterr().out


def test_cli_runtime_check_unknown_runtime_exits_two(monkeypatch):
    import production.__main__ as cli

    monkeypatch.setattr(sys, "argv", ["production", "runtime-check", "vegas_pro"])
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 2
