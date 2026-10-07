"""Create edit_decisions v002 with audio_asset_id changes."""
import json
from pathlib import Path

# Read the current v001
edit_path = Path("projects/proj_3e27bd7a/edit/edit_decisions.v001.json")
with open(edit_path, "r", encoding="utf-8") as f:
    edit = json.load(f)

# Update audio_asset_id in narration tracks (already done, but let's ensure it's correct)
audio_tracks = edit["data"]["audio_tracks"]
for track in audio_tracks.get("narration", []):
    track["audio_asset_id"] = "projects/proj_3e27bd7a/audio/" + track["event_id"] + ".mp3"
for track in audio_tracks.get("music", []):
    track["audio_asset_id"] = None
for track in audio_tracks.get("sfx", []):
    track["audio_asset_id"] = None

# Set new version
edit["artifact_version"] = 2
edit["content_hash"] = None  # Will be computed

# Write as v002
output_path = Path("projects/proj_3e27bd7a/edit/edit_decisions.v002.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(edit, f, indent=2)

print(f"Created {output_path}")
print(f"artifact_version: {edit['artifact_version']}")

# Compute the canonical hash
from production.artifact_store import ArtifactStore
from pathlib import Path as PPath
store = ArtifactStore(projects_root=PPath("projects"))
canonical_hash = ArtifactStore.compute_hash(edit)
print(f"Canonical hash: {canonical_hash}")

# Update the content_hash in the edit dict
edit["content_hash"] = canonical_hash

# Rewrite the file
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(edit, f, indent=2)

print("Done!")