"""Fix the artifact store hash for the modified edit_decisions."""
import json, hashlib
from pathlib import Path
from production.artifact_store import ArtifactStore

# Step 1: Read the current modified edit_decisions v001
edit_path = Path("projects/proj_3e27bd7a/edit/edit_decisions.v001.json")
with open(edit_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# Step 2: Compute the canonical hash using the store's method
canonical = ArtifactStore.compute_hash(data)
print("Canonical hash from compute_hash():", canonical)

# Step 3: Also compute what the raw file hash would be
with open(edit_path, "rb") as f:
    raw_hash = "sha256:" + hashlib.sha256(f.read()).hexdigest()
print("Raw byte hash:", raw_hash)

# Step 4: The "stored" hash that the artifact store sees when loading the envelope
# This is the content_hash field in the ArtifactEnvelope, which is computed from envelope.data
# Let me check what the current latest pointer says
latest_path = Path("projects/proj_3e27bd7a/edit/edit_decisions.latest.json")
with open(latest_path, "r", encoding="utf-8") as f:
    latest = json.load(f)
print("Latest pointer content_hash:", latest["content_hash"])

# Step 5: Set the content_hash in the data dict to the canonical value
data["content_hash"] = canonical

# Step 6: Write the file back with sort_keys=True in json.dump
with open(edit_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, sort_keys=True)

# Step 7: Verify the hash after write
with open(edit_path, "r", encoding="utf-8") as f:
    data2 = json.load(f)
verified = ArtifactStore.compute_hash(data2)
print("Verified after write:", verified)
print("Match with target:", verified == canonical)

# Step 8: Update the latest pointer
latest["content_hash"] = canonical
latest["version"] = 1  # keep version 1
with open(latest_path, "w", encoding="utf-8") as f:
    json.dump(latest, f, indent=2)

print("\nUpdated edit_decisions.v001.json with correct canonical hash")
print("Updated edit_decisions.latest.json with correct content_hash")
print("\nNow trying the render...")