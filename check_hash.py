"""Check the canonical hash of the modified edit_decisions."""
import json
from pathlib import Path
from production.artifact_store import ArtifactStore

edit_path = Path("projects/proj_3e27bd7a/edit/edit_decisions.v001.json")
with open(edit_path, "r", encoding="utf-8") as f:
    data = json.load(f)

canonical = ArtifactStore.compute_hash(data)
print("Canonical hash from store.compute_hash():", canonical)

# Print the audio_tracks section
at = data["data"]["audio_tracks"]
for track_name in ["narration", "music", "sfx"]:
    tracks = at.get(track_name, [])
    print(f"\n{track_name} tracks ({len(tracks)}):")
    for t in tracks:
        eid = t["event_id"]
        aaid = t.get("audio_asset_id", "None")
        print(f"  {eid}: audio_asset_id={aaid}")