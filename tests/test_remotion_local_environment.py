"""Local environment tests: Node toolchain, lockfile, and version records."""
import json
from pathlib import Path

from composition.diagnostics import resolve_tool_argv

ROOT = Path(__file__).resolve().parent.parent


def test_node_and_npm_resolve_locally():
    assert resolve_tool_argv("node") is not None
    assert resolve_tool_argv("npm") is not None


def test_nvmrc_pins_node_24():
    content = (ROOT / "remotion-composer" / ".nvmrc").read_text(encoding="utf-8").strip()
    assert content.startswith("24"), content


def test_package_lock_exists_and_matches_pins():
    composer = ROOT / "remotion-composer"
    package = json.loads((composer / "package.json").read_text(encoding="utf-8"))
    lockfile = composer / "package-lock.json"
    assert lockfile.is_file(), "package-lock.json must be committed for reproducible installs"
    lock = json.loads(lockfile.read_text(encoding="utf-8"))
    entries = lock.get("packages", {})
    for name, pinned in {**package.get("dependencies", {}), **package.get("devDependencies", {})}.items():
        resolved = entries.get(f"node_modules/{name}", {}).get("version")
        assert resolved == pinned, f"{name}: lockfile has {resolved}, package.json pins {pinned}"


def test_remotion_pin_unchanged():
    package = json.loads((ROOT / "remotion-composer" / "package.json").read_text(encoding="utf-8"))
    assert package["dependencies"]["remotion"] == "4.0.0"
    assert package["dependencies"]["@remotion/cli"] == "4.0.0"
    assert "latest" not in json.dumps(package)
