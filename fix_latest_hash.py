"""Fix .latest.json content_hash to match the actual artifact.

This script recomputes the canonical hash of edit_decisions.v001.json
and updates edit_decisions.latest.json so the pointer is consistent.

Usage:
    python fix_latest_hash.py

Safety:
- Reads edit_decisions.v001.json
- Computes canonical hash via ArtifactStore.compute_hash() convention
- Writes the corrected content_hash into .latest.json
- Does NOT modify edit_decisions.v001.json
"""

import sys
from pathlib import Path

# Use the workspace root as parent of the scripts/ directory
# __file__ is .../AI-Simplified-Video-Factory/fix_latest_hash.py
# We need to go up one level from scripts to workspace root
SCRIPT_DIR = Path(__file__).resolve().parent  # .../fix_latest_hash.py
WORKSPACE_ROOT = SCRIPT_DIR.parent.parent  # .../AI-Simplified-Video-Factory (3 levels up from fix_latest_hash.py? No...)

# Actually, let's just use the known project structure directly
PROJECT_ROOT = Path.cwd()
if "AI-Simplified-Video-Factory" in str(PROJECT_ROOT):
    # We're inside the project
    PROJECT_ROOT = PROJECT_ROOT
else:
    # Try to find it
    PROJECT_ROOT = PROJECT_ROOT.parent

EDIT_DIR = PROJECT_ROOT / "projects" / "proj_3e27bd7a" / "edit"

V001_PATH = EDIT_DIR / "edit_decisions.v001.json"
LATEST_PATH = EDIT_DIR / "edit_decisions.latest.json"


def compute_hash(data: dict) -> str:
    """Canonical hash: sort_keys=True, separators=(",", ":")."""
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def main() -> None:
    # Read v001
    v001_data = json.loads(V001_PATH.read_text())

    # Compute canonical hash
    actual_hash = compute_hash(v001_data)

    # Read latest
    latest_data = json.loads(LATEST_PATH.read_text())

    # Update content_hash to match v001
    latest_data["content_hash"] = f"sha256:{actual_hash}"

    # Preserve other fields
    # version should stay 1
    # file should point to v001
    latest_data["file"] = "edit_decisions.v001.json"

    # Write back
    LATEST_PATH.write_text(json.dumps(latest_data, indent=2, sort_keys=False))

    # Verify roundtrip
    verify = json.loads(LATEST_PATH.read_text())
    verify_hash = verify["content_hash"]
    assert verify_hash == f"sha256:{actual_hash}", f"Hash mismatch after fix: {verify_hash}"

    print(f"✓ Fixed .latest.json content_hash")
    print(f"  v001 canonical hash: {actual_hash}")
    print(f"  .latest.json content_hash: {verify['content_hash']}")
    print(f"  Match: {verify['content_hash'] == f'sha256:{actual_hash}'}")
    print(f"  v001 unchanged: {V001_PATH.read_text()[:50]}...")


if __name__ == "__main__":
    main()