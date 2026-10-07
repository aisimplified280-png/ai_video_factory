"""Update the .latest pointer to v002."""
import json
from pathlib import Path

latest_path = Path("projects/proj_3e27bd7a/edit/edit_decisions.latest.json")
with open(latest_path, "r", encoding="utf-8") as f:
    ptr = json.load(f)

print("Before:", ptr)

# Update version to 2 and file to v002
ptr["version"] = 2
ptr["file"] = "edit_decisions.v002.json"

# Also update content_hash to match the new version's hash
# We need to compute it from the v002 file
import hashlib, json
with open(Path("projects/proj_3e27bd7a/edit/edit_decisions.v002.json"), "rb") as f:
    raw = f.read()
raw_hash = "sha256:" + hashlib.sha256(raw).hexdigest()
# But the store uses canonical JSON hash, not raw bytes
from production.artifact_store import ArtifactStore
store = ArtifactStore(projects_root=Path("projects"))
canonical = ArtifactStore.compute_hash(json.loads(raw))
ptr["content_hash"] = canonical

print("After:", ptr)

with open(latest_path, "w", encoding="utf-8") as f:
    json.dump(ptr, f, indent=2)

print("Updated latest pointer to v002")