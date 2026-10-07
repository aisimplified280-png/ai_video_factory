"""Fix the v002 hash to match the artifact store's canonical hash."""
import json, hashlib
from pathlib import Path
from production.artifact_store import ArtifactStore

# Read the v002 file
v002_path = Path("projects/proj_3e27bd7a/edit/edit_decisions.v002.json")
with open(v002_path, "r", encoding="utf-8") as f:
    raw = f.read()

# Parse the data
data = json.loads(raw)

# Compute the canonical hash using the store's method
canonical = ArtifactStore.compute_hash(data)
print("Canonical hash from compute_hash():", canonical)

# Also compute raw byte hash for comparison
raw_hash = "sha256:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()
print("Raw byte hash:", raw_hash)

# The current content_hash in the file
current_ch = None
# Try to find content_hash in the raw JSON
# Actually, let me just rewrite the file with the correct content_hash

# Read the file as raw bytes and compute what the store will compute
# The store compute_hash takes a dict, not a string
# Let me just write the file with the correct content_hash embedded

# Read the file back as a dict
with open(v002_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# Set the content_hash using the store's method
data["content_hash"] = ArtifactStore.compute_hash(data)

# Now compute what the stored hash will be after writing
# The stored hash should match ArtifactStore.compute_hash(data)
# But we need to write the data back and verify

# Write the file with the correct content_hash
with open(v002_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)

# Now verify: read back and compute
with open(v002_path, "r", encoding="utf-8") as f:
    data2 = json.load(f)
verified = ArtifactStore.compute_hash(data2)
print("Verified canonical hash:", verified)

# Also check what the raw content_hash field says
print("content_hash in data:", data2.get("content_hash"))