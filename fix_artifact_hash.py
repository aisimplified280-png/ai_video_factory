"""Fix the artifact store hash mismatch after editing edit_decisions.json."""
import json
import hashlib
from pathlib import Path

from production.artifact_store import ArtifactStore

# Initialize artifact store
store = ArtifactStore(projects_root=Path("projects"))

# Compute the new hash from the modified file
edit_path = Path("projects/proj_3e27bd7a/edit/edit_decisions.v001.json")
with open(edit_path, "rb") as f:
    new_hash = "sha256:" + hashlib.sha256(f.read()).hexdigest()
print("New hash from file:", new_hash)

# The original stored hash was: sha256:fa386db030b8ca50bb4ee9cfdac4ec0b5ee25e6c80f0e2aad53b624b39733283
# Get the current/latest version info
versions = store.list_versions("edit_decisions", "proj_3e27bd7a")
print("Existing versions:", versions)

# Get the current envelope to update the hash
try:
    edit = store.latest("edit_decisions", "proj_3e27bd7a")
    print("Current edit version:", edit.artifact_version)
    print("Current content_hash:", edit.content_hash)
except Exception as e:
    print("Error getting latest:", e)
    # Try loading by version
    try:
        edit = store.load("edit_decisions", "proj_3e27bd7a", version=1)
        print("Loaded version 1:", edit.artifact_version, edit.content_hash)
    except Exception as e2:
        print("Error loading version 1:", e2)
"