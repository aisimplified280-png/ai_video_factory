"""Environment discovery for composition runtimes.

Probes installations, executables, packages, and versions without rendering
anything and without touching the network. Unknown is never available.
"""
from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

from .runtime import CheckStatus, RuntimeDiagnostics, RuntimeStatus
from .runtime_registry import RuntimeRecord

FACTORY_ROOT = Path(__file__).resolve().parent.parent
_COMMAND_TIMEOUT = 10

# Fallback when a shell predates a Node MSI install (PATH not yet refreshed).
_WINDOWS_NODE_DIR = Path("C:/Program Files/nodejs")


def _which(command: str) -> str | None:
    return shutil.which(command)


def resolve_tool_argv(command: str) -> list[str] | None:
    """Argv prefix for a tool, robust to stale PATH on Windows.

    Prefers PATH discovery; falls back to the default Windows Node.js install
    directory (node.exe runs directly, npm/npx .cmd shims run via cmd /c).
    Returns None when the tool cannot be found anywhere.
    """
    found = shutil.which(command)
    if found:
        return [found]
    import os
    if os.name == "nt":
        found_cmd = shutil.which(f"{command}.cmd")
        if found_cmd:
            return ["cmd", "/c", found_cmd]
        
    if _WINDOWS_NODE_DIR.is_dir():
        if command == "node":
            candidate = _WINDOWS_NODE_DIR / "node.exe"
            if candidate.is_file():
                return [str(candidate)]
        else:
            candidate = _WINDOWS_NODE_DIR / f"{command}.cmd"
            if candidate.is_file():
                return ["cmd", "/c", str(candidate)]
    return None


def _command_version(command: str, args: list[str]) -> str | None:
    argv = resolve_tool_argv(command)
    if argv is None:
        return None
    try:
        proc = subprocess.run(
            [*argv, *args],
            capture_output=True, text=True, timeout=_COMMAND_TIMEOUT,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    return (proc.stdout or proc.stderr or "").strip().splitlines()[0][:120] if (proc.stdout or proc.stderr) else None


def _pass(name: str, message: str) -> dict:
    return {"name": name, "status": CheckStatus.PASS.value, "message": message, "severity": "info"}


def _fail(name: str, message: str, severity: str = "critical") -> dict:
    return {"name": name, "status": CheckStatus.FAIL.value, "message": message, "severity": severity}


def _warn(name: str, message: str) -> dict:
    return {"name": name, "status": CheckStatus.WARN.value, "message": message, "severity": "warning"}


def _python_check() -> dict:
    return _pass("python_available", f"Python {sys.version.split()[0]} at {sys.executable}")


def _pillow_check() -> dict:
    spec = importlib.util.find_spec("PIL")
    if spec is None:
        return _fail("pillow_available", "Pillow is not importable")
    try:
        import PIL
        return _pass("pillow_available", f"Pillow {getattr(PIL, '__version__', 'unknown')} importable")
    except Exception as exc:  # pragma: no cover - import machinery edge
        return _fail("pillow_available", f"Pillow import failed: {exc}")


def _browser_runtime_check() -> dict:
    """Detect a usable headless browser for local Remotion rendering."""
    home = Path.home()
    candidates = [
        home / ".cache" / "puppeteer" / "chrome-headless-shell",
        home / ".cache" / "puppeteer" / "chrome",
    ]
    for candidate in candidates:
        if candidate.is_dir() and any(candidate.iterdir()):
            return _pass("browser_runtime", f"Headless browser runtime found at {candidate}")
    system_chrome = _which("chrome") or _which("chromium") or _which("google-chrome")
    if system_chrome:
        return _pass("browser_runtime", f"System browser found at {system_chrome}")
    return _fail("browser_runtime", "No headless browser runtime found (Remotion downloads one on first render)")


def _remotion_checks() -> tuple[list[dict], str | None]:
    checks = [_python_check()]
    node = _command_version("node", ["--version"])
    npm = _command_version("npm", ["--version"])
    if node is None:
        checks.append(_fail("node_available", "node executable not found on PATH"))
    else:
        checks.append(_pass("node_available", f"node {node}"))
    if npm is None:
        checks.append(_fail("npm_available", "npm executable not found on PATH"))
    else:
        checks.append(_pass("npm_available", f"npm {npm}"))
    project = FACTORY_ROOT / "remotion-composer" / "package.json"
    if project.exists():
        checks.append(_pass("remotion_project", f"Remotion project found at {project}"))
    else:
        checks.append(_fail("remotion_project", "No remotion-composer/package.json in this factory"))
    checks.append(_browser_runtime_check())
    return checks, None


def _hyperframes_checks() -> tuple[list[dict], str | None]:
    checks = [_python_check()]
    project = FACTORY_ROOT / "hyperframes"
    if project.is_dir():
        checks.append(_pass("hyperframes_project", f"HyperFrames project found at {project}"))
    else:
        checks.append(_fail("hyperframes_local", "No local HyperFrames implementation in this factory (remote-only runtime)", severity="info"))
    return checks, None


def _ffmpeg_checks() -> tuple[list[dict], str | None]:
    checks = [_python_check(), _pillow_check()]
    version = _command_version("ffmpeg", ["-version"])
    if version is None:
        checks.append(_fail("ffmpeg_available", "ffmpeg executable not found on PATH"))
    else:
        checks.append(_pass("ffmpeg_available", version))
    return checks, None


def diagnose_runtime(record: RuntimeRecord) -> RuntimeDiagnostics:
    """Probe one runtime and return its structured availability."""
    if record.runtime_id == "remotion":
        checks, version = _remotion_checks()
        toolchain = [c for c in checks if c["name"] in {"node_available", "npm_available"}]
        project = next(c for c in checks if c["name"] == "remotion_project")
        browser = next(c for c in checks if c["name"] == "browser_runtime")
        if not all(c["status"] == "pass" for c in toolchain):
            status = RuntimeStatus.UNAVAILABLE
        elif project["status"] != "pass" or browser["status"] != "pass":
            status = RuntimeStatus.MISCONFIGURED
        else:
            status = RuntimeStatus.AVAILABLE
    elif record.runtime_id == "hyperframes":
        checks, version = _hyperframes_checks()
        # Remote-only runtime with no local implementation and no remote
        # endpoint probing in Phase 7: explicitly unknown, never available.
        status = RuntimeStatus.UNKNOWN
    elif record.runtime_id == "ffmpeg_pil":
        checks, version = _ffmpeg_checks()
        status = RuntimeStatus.AVAILABLE if all(c["status"] == "pass" for c in checks) else RuntimeStatus.UNAVAILABLE
    else:
        checks, version = [], None
        status = RuntimeStatus.UNKNOWN
    if not record.enabled:
        status = RuntimeStatus.UNAVAILABLE
        checks.append(_fail("runtime_enabled", f"Runtime {record.runtime_id} is disabled in the registry"))
    return RuntimeDiagnostics(record.runtime_id, status, version, checks)


def diagnose_all(registry) -> list[RuntimeDiagnostics]:
    """Diagnose every registered runtime in registry order."""
    return [diagnose_runtime(registry.get(runtime_id)) for runtime_id in registry.list_registered()]
