"""End-to-end Remotion render tests. These render real pixels locally.

Skipped only when the Node toolchain is unavailable (environment limitation,
never a pass). With local Node installed, they must PASS.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from composition.remotion.props_builder import build_production_props
from composition.remotion.renderer import compare_frames, frames_differ
from composition.remotion.runtime import RemotionRuntime

COMPOSER = ROOT / "remotion-composer"


def _local_toolchain() -> bool:
    from composition.diagnostics import resolve_tool_argv
    return resolve_tool_argv("node") is not None and (COMPOSER / "node_modules").is_dir()


requires_local_remotion = pytest.mark.skipif(
    not _local_toolchain(),
    reason="Local Node toolchain unavailable (environment limitation, not a pass).",
)

PROFILE = {
    "profile": "profiles/youtube_short.json",
    "resolution": {"width": 1080, "height": 1920},
    "fps": 30,
    "duration_constraints": {"minimum_seconds": 10, "maximum_seconds": 60},
    "safe_zones": {"caption": "lower_center_safe", "cta": "center_safe", "brand": "bottom_safe"},
}


def _paint_asset(projects_root: Path) -> None:
    target = projects_root / "proj_e2e" / "assets" / "shot.png"
    target.parent.mkdir(parents=True, exist_ok=True)
    canvas = Image.new("RGB", (1080, 1920), (10, 14, 26))
    stripe = Image.new("RGB", (1080, 200), (56, 189, 248))
    canvas.paste(stripe, (0, 800))
    canvas.save(target)


def _props(projects_root: Path, public_dir: Path, camera: str):
    edit = {
        "production_id": "proj_e2e", "total_duration": 3.0,
        "platform_profile": "profiles/youtube_short.json", "platform": PROFILE,
        "runtime_lock_source": {"artifact_type": "proposal_packet", "version": 1,
                                "content_hash": "sha256:" + "a" * 64,
                                "locked_at": "2026-10-06T00:00:00+00:00", "locked_concept_id": "c1"},
        "renderer_family": "explainer", "render_runtime": "remotion", "composition_mode": "atelier",
        "timeline": [{
            "event_id": "edit_scene_01_01", "scene_id": "scene_01", "shot_id": "scene_01_shot_01",
            "track_id": "video_primary", "role": "primary_visual", "asset_id": "ast_01",
            "start": 0.0, "end": 3.0, "duration": 3.0, "z_index": 10, "purpose": "Establish the engine",
            "crop": "full_frame", "camera_intent": camera, "motion_intent": "emerge",
            "transition_in": "fade", "transition_out": None,
            "caption_ref": "caption_scene_01", "audio_ref": None}],
        "video_tracks": {}, "audio_tracks": {"narration": [], "music": [], "sfx": []},
        "caption_track": [{"event_id": "caption_scene_01", "scene_id": "scene_01", "start": 0.0, "end": 3.0,
                           "caption_text_reference": "sec_01", "emphasis_words": ["ENGINE"],
                           "safe_zone": "lower_center_safe"}],
        "cta": {"scene_id": "scene_01", "start": 0.0, "end": 3.0, "channel_branding": "AI Simplified Lab",
                "caption_event_id": "caption_scene_01",
                "audio_requirement": {"required": True, "spoken_text": "Subscribe."}},
        "tracks": {"video": []},
    }
    scenes = {"scenes": [{
        "id": "scene_01", "scene_id": "scene_01", "type": "animation", "start_seconds": 0.0, "end_seconds": 3.0,
        "shot_intent": "Establish the engine", "narrative_role": "hook", "subject": "compute engine",
        "visual_purpose": "Establish the engine", "visual_metaphor": "An engine.",
        "signature_device_usage": "none", "required_assets": [],
        "shots": [{"shot_id": "scene_01_shot_01", "start": 0, "end": 3.0}]}], "total_duration_seconds": 3.0,
        "variety_score": 80.0}
    manifest = {"assets": [{
        "asset_id": "ast_01", "scene_id": "scene_01", "purpose": "Establish the engine",
        "visual_role": "primary", "type": "image", "source": "generated", "status": "ready",
        "file_path": "projects/proj_e2e/assets/shot.png", "subject": "compute engine"}],
        "total_estimated_cost": 0.0}
    art = {"design_read": "E2E fixture treatment.", "visual_variance": 8, "motion_intensity": 6,
           "information_density": 5, "palette_discipline": {"primary": "#0F172A", "accent_1": "#38BDF8"},
           "typography_personality": "Direct", "layout_language": "Centered",
           "signature_device": "gauge", "anti_patterns": ["No cards."]}
    script = {"target_duration_seconds": 3, "word_count": 3,
              "sections": [{"id": "sec_01", "section_id": "sec_01", "spoken_text": "Hello engine.",
                            "narrative_role": "hook"}],
              "cta": {"spoken_text": "Subscribe."}}
    props, _ = build_production_props(
        edit_data=edit, scene_plan_data=scenes, manifest_data=manifest,
        art_direction_data=art, script_data=script, platform_profile=PROFILE,
        projects_root=projects_root, public_dir=public_dir)
    props["editArtifactVersion"] = 1
    props["editArtifactHash"] = "sha256:" + "b" * 64
    return props


def _render_case(tmp_path: Path, name: str, camera: str) -> Path:
    projects_root, public_dir = tmp_path / "projects", tmp_path / "public"
    _paint_asset(projects_root)
    props = _props(projects_root, public_dir, camera)
    props_path = tmp_path / f"{name}.json"
    props_path.write_text(json.dumps(props))
    output = tmp_path / f"{name}.mp4"
    result = RemotionRuntime().render(props_path, output)
    assert result["status"] == "ready", result.get("message")
    assert output.is_file()
    return output


def _probe(video: Path) -> dict:
    proc = subprocess.run(["ffprobe", "-v", "quiet", "-print_format", "json",
                           "-show_format", "-show_streams", str(video)],
                          capture_output=True, text=True, check=True)
    info = json.loads(proc.stdout)
    stream = next(s for s in info["streams"] if s["codec_type"] == "video")
    return {"codec": stream["codec_name"], "width": stream["width"],
            "height": stream["height"], "fps": stream["r_frame_rate"],
            "duration": float(info["format"]["duration"])}


@requires_local_remotion
def test_e2e_real_render_produces_valid_mp4(tmp_path):
    output = _render_case(tmp_path, "e2e_base", "observe_static")
    probe = _probe(output)
    assert probe["codec"] == "h264"
    assert (probe["width"], probe["height"]) == (1080, 1920)
    assert probe["fps"] in ("30/1", "30")
    assert abs(probe["duration"] - 3.0) <= 0.5


@requires_local_remotion
def test_e2e_pixel_authority_at_remotion_output(tmp_path):
    base = _render_case(tmp_path, "e2e_static", "observe_static")
    zoomed = _render_case(tmp_path, "e2e_zoom", "approach_subject")
    first, second = tmp_path / "a.png", tmp_path / "b.png"
    subprocess.run(["ffmpeg", "-y", "-ss", "2.0", "-i", str(base), "-frames:v", "1", str(first)],
                   capture_output=True, check=True)
    subprocess.run(["ffmpeg", "-y", "-ss", "2.0", "-i", str(zoomed), "-frames:v", "1", str(second)],
                   capture_output=True, check=True)
    assert frames_differ(first, second) is True
    assert compare_frames(first, second) > 1.0
