"""Fix the v002 content_hash to match what the artifact store will compute."""
import json, hashlib
from pathlib import Path
from production.artifact_store import ArtifactStore

v002_path = Path("projects/proj_3e27bd7a/edit/edit_decisions.v002.json")

# Read the raw file
with open(v002_path, "rb") as f:
    raw_bytes = f.read()

# Parse the JSON
data = json.loads(raw_bytes)

# Compute the canonical hash using the store's method
canonical = ArtifactStore.compute_hash(data)
print("Canonical hash:", canonical)

# Also compute what the "stored" hash would be if we just set content_hash in the dict
# and then re-serialize
# The store's compute_hash does: json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
# Let me verify
canonical_check = hashlib.sha256(
    json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
).hexdigest()
print("Manual canonical hash:", "sha256:" + canonical_check)
print("Match:", canonical_check == canonical.split(":")[1])

# Now set the content_hash in the data dict
data["content_hash"] = canonical

# Write the file back with sort_keys=True to ensure consistent ordering
with open(v002_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, sort_keys=True)

# Verify: read the file back and compute the hash
with open(v002_path, "rb") as f:
    raw2 = f.read()
data2 = json.loads(raw2)
computed = ArtifactStore.compute_hash(data2)
print("Verified after write:", computed)
print("Match:", computed == canonical)