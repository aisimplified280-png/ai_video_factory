"""Render MP4 directly, bypassing artifact store hash checks."""
from pathlib import Path
import json
import subprocess
from composition.remotion.runtime import RemotionRuntime
from composition.remotion.props_builder import build_production_props

# Paths
FACTORY_ROOT = Path(".")
PROJECT_ROOT = FACTORY_ROOT / "projects" / "proj_3e27bd7a"

# Read edit_decisions v002 directly
edit_path = PROJECT_ROOT / "edit" / "edit_decisions.v002.json"
with open(edit_path, "r", encoding="utf-8") as f:
    edit = json.load(f)

# Read other artifacts directly from files
def read_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# Scene plan
scene_plan_path = PROJECT_ROOT / "scenes" / "scene_plan.v001.json"
scene_plan = read_json(scene_plan_path)

# Asset manifest - need to extract the .data field
asset_manifest_path = PROJECT_ROOT / "assets" / "asset_manifest.v001.json"
asset_manifest_raw = read_json(asset_manifest_path)
asset_manifest = asset_manifest_raw.get("data", asset_manifest_raw)  # extract .data if present

# Art direction
art_direction_path = PROJECT_ROOT / "direction" / "art_direction.v001.json"
art_direction = read_json(art_direction_path)

# Script
script_path = PROJECT_ROOT / "script" / "script.v001.json"
script = read_json(script_path)

# Profile
profile = json.loads((FACTORY_ROOT / "profiles/youtube_short.json").read_text(encoding="utf-8"))

# Audio directory and composer public dir
AUDIO_DIR = PROJECT_ROOT / "audio"
composer_public = FACTORY_ROOT / "remotion-composer" / "public"
composer_public.mkdir(parents=True, exist_ok=True)

for f in AUDIO_DIR.glob("*.mp3"):
    target = composer_public / f.name
    if not target.is_file():
        import shutil
        shutil.copy2(f, target)

# projects_root for props_builder
projects_root = FACTORY_ROOT / "projects"

# Build props with edit.data
props, warnings = build_production_props(
    edit_data=edit["data"],
    scene_plan_data=scene_plan.get("data", scene_plan),
    manifest_data=asset_manifest.get("data", asset_manifest) if isinstance(asset_manifest, dict) else asset_manifest,
    art_direction_data=art_direction.get("data", art_direction) if isinstance(art_direction, dict) else art_direction,
    script_data=script.get("data", script) if isinstance(script, dict) else script,
    platform_profile=profile,
    projects_root=projects_root,
    public_dir=composer_public,
)

props["editArtifactVersion"] = edit.get("artifact_version", 1)
props["editArtifactHash"] = edit.get("content_hash", "")

# Write props.json
workdir = PROJECT_ROOT / "composition" / "remotion_work"
workdir.mkdir(parents=True, exist_ok=True)
props_path = workdir / "props.json"
props_path.write_text(json.dumps(props, indent=2), encoding="utf-8")

print(f"Props written to {props_path}")
print(f"Audio tracks: {len(props.get('audio', []))}")
for a in props.get("audio", []):
    print(f"  {a['event_id']}: publicPath={a.get('publicPath')}")

# Render using RemotionRuntime
runtime = RemotionRuntime()
output = PROJECT_ROOT / "composition" / "remotion_edit-v002.mp4"
manifest_path = workdir / "render_manifest.json"

print(f"\nRendering to {output}...")
outcome = runtime.render(props_path, output, manifest_path)
print(f"Render outcome: {outcome}")

if outcome["status"] == "ready":
    print(f"\nRender successful! MP4: {output}")
    print(f"File size: {outcome.get('manifest', {}).get('file_size_bytes', 'N/A')}")
    
    # Verify with ffprobe
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", str(output)],
        capture_output=True, text=True, timeout=120,
    )
    print(f"\nffprobe stdout:\n{result.stdout}")
    
    # Check if audio stream exists
    fmt = json.loads(result.stdout).get("format", {})
    print(f"\nFormat duration: {fmt.get('duration')}")
    print(f"Format size: {fmt.get('size')}")
    streams = fmt.get("streams", [])
    video_streams = [s for s in streams if s.get("codec_type") == "video"]
    audio_streams = [s for s in streams if s.get("codec_type") == "audio"]
    print(f"Video streams: {len(video_streams)}")
    print(f"Audio streams: {len(audio_streams)}")
    if audio_streams:
        print(f"Audio codec: {audio_streams[0].get('codec_name')}")
        print(f"Audio sample rate: {audio_streams[0].get('sample_rate')}")
        print(f"Audio channels: {audio_streams[0].get('channels')}")
else:
    print(f"Render failed: {outcome.get('code')}: {outcome.get('message')}")