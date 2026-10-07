"""Render the MP4 directly using RemotionRuntime, bypassing artifact store hash checks."""
from pathlib import Path
from composition.remotion.runtime import RemotionRuntime
from composition.remotion.props_builder import build_production_props

# Setup paths
FACTORY_ROOT = Path(".")
PROJECT_ROOT = FACTORY_ROOT / "projects" / "proj_3e27bd7a"
ASSETS_DIR = PROJECT_ROOT / "assets"
AUDIO_DIR = PROJECT_ROOT / "audio"

# Load the data needed for props_builder
from production.artifact_store import ArtifactStore
store = ArtifactStore(projects_root=FACTORY_ROOT / "projects")
edit = store.latest("edit_decisions", "proj_3e27bd7a")
print("Edit version:", edit.artifact_version)
print("Edit content_hash:", edit.content_hash)

# Load the other artifacts needed for props_builder
scene_plan = store.latest("scene_plan", "proj_3e27bd7a")
asset_manifest = store.latest("asset_manifest", "proj_3e27bd7a")
art_direction = store.latest("art_direction", "proj_3e27bd7a")
script = store.latest("script", "proj_3e27bd7a")

profile = json.loads((FACTORY_ROOT / "profiles/youtube_short.json").read_text(encoding="utf-8"))

public_dir = PROJECT_ROOT / "composition" / "remotion_work" / "public"
public_dir.mkdir(parents=True, exist_ok=True)

# Copy audio files to the composer public dir (as props_builder expects)
for f in AUDIO_DIR.glob("*.mp3"):
    target = public_dir / f.name
    if not target.is_file():
        import shutil
        shutil.copy2(f, target)
        print(f"Copied {f.name} to {target}")

# Now call build_production_props
# projects_root = FACTORY_ROOT / "projects"
# The public_dir should be the composer's public dir
composer_public = FACTORY_ROOT / "remotion-composer" / "public"

props, warnings = build_production_props(
    edit_data=edit.data,
    scene_plan_data=scene_plan.data,
    manifest_data=asset_manifest.data,
    art_direction_data=art_direction.data,
    script_data=script.data,
    platform_profile=profile,
    projects_root=FACTORY_ROOT / "projects",
    public_dir=composer_public,
)

props["editArtifactVersion"] = edit.artifact_version
props["editArtifactHash"] = edit.content_hash

# Write props.json
workdir = FACTORY_ROOT / "projects" / "proj_3e27bd7a" / "composition" / "remotion_work"
workdir.mkdir(parents=True, exist_ok=True)
props_path = workdir / "props.json"
props_path.write_text(json.dumps(props, indent=2), encoding="utf-8")

print(f"Props written to {props_path}")
print(f"Audio tracks in props: {len(props.get('audio', []))}")
for a in props.get("audio", []):
    print(f"  {a['event_id']}: publicPath={a.get('publicPath')}, track={a.get('track')}")

# Now render using RemotionRuntime
runtime = RemotionRuntime()
output = FACTORY_ROOT / "projects" / "proj_3e27bd7a" / "composition" / "remotion_edit-v002.mp4"
manifest_path = workdir / "render_manifest.json"

print(f"\nRendering to {output}...")
outcome = runtime.render(props_path, output, manifest_path)
print(f"Render outcome: {outcome}")

if outcome["status"] == "ready":
    print(f"\nRender successful! MP4: {output}")
    print(f"File size: {outcome.get('manifest', {}).get('file_size_bytes', 'N/A')}")
    
    # Verify with ffprobe
    import subprocess
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", str(output)],
        capture_output=True, text=True, timeout=120,
    )
    print(f"\nffprobe output:\n{result.stdout}")
else:
    print(f"Render failed: {outcome.get('code')}: {outcome.get('message')}")