"""Debug the artifact hash using the store's own compute_hash."""
from pathlib import Path
import json
from production.artifact_store import ArtifactStore

store = ArtifactStore(projects_root=Path("projects"))

# Compute hash using the store's own method
edit_path = Path("projects/proj_3e27bd7a/edit/edit_decisions.v001.json")
with open(edit_path, "r", encoding="utf-8") as f:
    data = json.load(f)

canonical_hash = ArtifactStore.compute_hash(data)
print("Canonical hash from store.compute_hash():", canonical_hash)

# Also compute from raw bytes (for comparison)
with open(edit_path, "rb") as f:
    raw_hash = "sha256:" + __import__("hashlib").sha256(f.read()).hexdigest()
print("Raw byte hash:", raw_hash)

# The various hashes we've seen:
print("\nKnown hashes:")
print("  Original stored:       sha256:fa386db030b8ca50bb4ee9cfdac4ec0b5ee25e6c80f0e2aad53b624b39733283")
print("  New byte hash:        ", end="")
with open(edit_path, "rb") as f:
    print(raw_hash.split(":")[1])
print("  Canonical store hash:  ", canonical_hash)