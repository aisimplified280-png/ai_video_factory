"""Debug the artifact store hash issue."""
from pathlib import Path
from production.artifact_store import ArtifactStore

store = ArtifactStore(projects_root=Path("projects"))

# Try loading the edit_decisions directly
edit = store.load("edit_decisions", "proj_3e27bd7a", version=1)
print("Loaded version 1")
print("artifact_version:", edit.artifact_version)
print("content_hash:", edit.content_hash)
print("First 200 chars of data:", str(edit.data)[:200])

# Also compute the hash from the raw file
edit_path = Path("projects/proj_3e27bd7a/edit/edit_decisions.v001.json")
with open(edit_path, "rb") as f:
    import hashlib
    computed = "sha256:" + hashlib.sha256(f.read()).hexdigest()
print("\nComputed from file:", computed)

# Read the latest pointer
latest_path = Path("projects/proj_3e27bd7a/edit/edit_decisions.latest.json")
with open(latest_path, "r") as f:
    latest = json.load(f)
print("\nLatest pointer:", latest)