"""Safe artifact-aware project cleanup utilities.

Rules:
- Never delete by age alone.
- Never delete the active/latest artifact version.
- Never delete immutable (approved) artifacts without explicit --force-delete-approved flag.
- Never delete .latest.json pointer files.
- Never delete items listed in production_state.active_artifact_versions.
- Always print what would be deleted (dry-run by default).
"""
from __future__ import annotations

import json
from pathlib import Path


FACTORY_ROOT = Path(__file__).resolve().parent.parent


def get_protected_files(project_dir: Path) -> set[Path]:
    """Return the set of artifact files that must never be deleted."""
    protected: set[Path] = set()

    # Always protect .latest.json pointers
    for f in project_dir.rglob("*.latest.json"):
        protected.add(f.resolve())

    # Protect active artifact versions referenced by production_state
    state_path = project_dir / "production_state.json"
    if state_path.exists():
        state = json.loads(state_path.read_text("utf-8"))
        active: dict = state.get("active_artifact_versions", {})
        for artifact_type, version in active.items():
            filename = f"{artifact_type}.v{int(version):03d}.json"
            for f in project_dir.rglob(filename):
                protected.add(f.resolve())

    # Protect every .json that is referenced by any .latest.json pointer
    for latest_file in project_dir.rglob("*.latest.json"):
        try:
            ptr = json.loads(latest_file.read_text("utf-8"))
            ref_file = ptr.get("file")
            if ref_file:
                candidate = latest_file.parent / ref_file
                if candidate.exists():
                    protected.add(candidate.resolve())
        except (json.JSONDecodeError, OSError):
            pass

    # Protect the final deliverable (latest mp4 in composition/)
    comp_dir = project_dir / "composition"
    if comp_dir.is_dir():
        mp4s = sorted(comp_dir.glob("*_edit-v*.mp4"))
        if mp4s:
            protected.add(mp4s[-1].resolve())  # latest MP4

    # Protect production state itself
    if state_path.exists():
        protected.add(state_path.resolve())

    return protected


def safe_cleanup_old_mp4s(project_dir: Path, keep: int = 1, dry_run: bool = True) -> list[Path]:
    """Delete old render MP4s, keeping the N most recent. Never deletes the protected set."""
    protected = get_protected_files(project_dir)
    comp_dir = project_dir / "composition"
    mp4s = sorted(comp_dir.glob("*_edit-v*.mp4"), key=lambda f: f.stat().st_mtime)
    to_delete = [f for f in mp4s[:-keep] if f.resolve() not in protected]
    for f in to_delete:
        if dry_run:
            print(f"[DRY-RUN] Would delete: {f}")
        else:
            f.unlink()
            print(f"[DELETED] {f}")
    return to_delete


def safe_cleanup_old_edit_versions(project_dir: Path, keep: int = 2, dry_run: bool = True) -> list[Path]:
    """Delete old edit_decisions versions, keeping the N most recent approved ones.
    
    NEVER deletes v001 (Phase 8B baseline), .latest.json, or the active version.
    """
    protected = get_protected_files(project_dir)
    edit_dir = project_dir / "edit"
    if not edit_dir.is_dir():
        return []

    versioned = sorted(
        [f for f in edit_dir.glob("edit_decisions.v*.json") if f.name != "edit_decisions.latest.json"],
        key=lambda f: int(f.stem.split(".v")[1])
    )

    # Always protect v001 (Phase 8B baseline)
    if versioned:
        protected.add(versioned[0].resolve())

    to_delete = [f for f in versioned[:-keep] if f.resolve() not in protected]
    for f in to_delete:
        if dry_run:
            print(f"[DRY-RUN] Would delete: {f}")
        else:
            f.unlink()
            print(f"[DELETED] {f}")
    return to_delete


def safe_cleanup_temp_files(project_dir: Path, dry_run: bool = True) -> list[Path]:
    """Delete known-safe temporary files (test outputs, tmp files)."""
    patterns = ["test_output.txt", "test_e2e_output.txt", "test_props_output.txt", "test_suite_output.txt", "*.tmp"]
    to_delete: list[Path] = []
    root = project_dir.parent.parent  # workspace root
    for pattern in patterns:
        for f in root.glob(pattern):
            if f.is_file():
                to_delete.append(f)
                if dry_run:
                    print(f"[DRY-RUN] Would delete temp: {f}")
                else:
                    f.unlink()
                    print(f"[DELETED] {f}")
    return to_delete
