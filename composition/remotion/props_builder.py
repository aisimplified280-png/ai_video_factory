"""Build validated Remotion props from canonical artifacts.

Edit decisions are authoritative for timing, order, and asset choice. Scene
plan supplies semantic meaning, the manifest supplies media, art direction
supplies the theme, and the script supplies caption text. Anything missing
or contradictory raises PropsError; nothing is invented or substituted.
"""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

FACTORY_ROOT = Path(__file__).resolve().parent.parent.parent


class PropsError(Exception):
    """Raised when canonical artifacts cannot be projected into props."""


_IMAGE_KINDS = {"image", "logo", "icon", "texture", "background", "screenshot"}
_DIAGRAM_KINDS = {"diagram", "chart", "code", "svg"}
_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".svg"}


def _asset_kind(manifest_type: str, suffix: str = "") -> str:
    # A video-typed asset whose file is actually a still image (e.g. a native
    # fallback that produced a PNG) renders as an image layer with full
    # camera motion. Declared via warning, never silent.
    if manifest_type == "video" and suffix.lower() in _IMAGE_SUFFIXES:
        return "image-still"
    if manifest_type == "video":
        return "video"
    if manifest_type == "svg":
        return "svg"
    if manifest_type in _DIAGRAM_KINDS:
        return manifest_type if manifest_type in {"diagram", "chart"} else "diagram"
    return "image"


def _theme_from_art_direction(art: dict[str, Any]) -> dict[str, Any]:
    palette = art.get("palette_discipline", {}) or {}
    intensity = min(10, max(1, int(art.get("motion_intensity", 6))))

    def color(key: str, default: str) -> str:
        value = palette.get(key)
        if isinstance(value, str) and len(value) == 7 and value.startswith("#"):
            return value
        return default

    return {
        "background": color("primary", "#0F172A"),
        "surface": "#16213A",
        "text": "#F8F7F2",
        "mutedText": color("neutral", "#9AA6B2"),
        "accent": color("accent_1", "#38BDF8"),
        "accentSecondary": color("accent_2", "#F4A261"),
        "fontFamily": "Arial, Helvetica, sans-serif",
        "headlineSize": 64,
        "bodySize": 34,
        "lineWeight": 3,
        "cornerRadius": 20,
        "motion": {"stiffness": 80 + intensity * 8, "damping": 22 - intensity, "mass": 1},
    }


def build_production_props(
    *,
    edit_data: dict[str, Any],
    scene_plan_data: dict[str, Any],
    manifest_data: dict[str, Any],
    art_direction_data: dict[str, Any],
    script_data: dict[str, Any],
    platform_profile: dict[str, Any],
    projects_root: Path | str,
    public_dir: Path | str,
) -> tuple[dict[str, Any], list[str]]:
    """Project canonical artifacts into Remotion props.

    Copies manifest media into public_dir/assets/. Returns (props, warnings).
    Raises PropsError on anything unresolvable.
    """
    projects_root = Path(projects_root)
    public_dir = Path(public_dir)
    assets_out = public_dir / "assets"
    assets_out.mkdir(parents=True, exist_ok=True)
    warnings: list[str] = []

    scenes = {s.get("scene_id") or s.get("id"): s for s in scene_plan_data.get("scenes", [])}
    manifest_assets = {a.get("asset_id"): a for a in manifest_data.get("assets", [])}
    sections = {s.get("section_id"): s for s in script_data.get("sections", [])}

    props_assets = []
    for asset_id, asset in manifest_assets.items():
        file_path = asset.get("file_path")
        public_path: str | None = None
        if file_path:
            candidate = Path(str(file_path).replace("\\", "/"))
            source = projects_root.parent / candidate if candidate.parts[:1] == ("projects",) else projects_root / candidate
            if not source.is_file():
                raise PropsError(f"Asset {asset_id} file missing: {source}")
            # Flat filename: staticFile() URL-encodes its whole argument, so
            # nested public/ subdirectories are unreachable. Asset ids are
            # unique per scene, keeping flat names collision-free in practice.
            target = assets_out / f"{asset_id}{source.suffix or '.png'}"
            shutil.copyfile(source, target)
            public_path = target.name
        elif not (asset.get("source") == "native" or asset.get("diagram_spec") or asset.get("type") == "native_composition"):
            raise PropsError(f"Asset {asset_id} has no file and no native representation; refusing to substitute.")
        kind = _asset_kind(asset.get("type", "image"), source.suffix if file_path else "")
        if kind == "image-still":
            warnings.append(
                f"Asset {asset_id} is declared video but the file is a still image; "
                f"rendering as an image layer with camera motion.")
        props_assets.append({
            "asset_id": asset_id,
            "scene_id": asset.get("scene_id"),
            "kind": kind,
            "source": asset.get("source"),
            "publicPath": public_path,
            "nativeSpec": asset.get("diagram_spec"),
            "purpose": asset.get("purpose", ""),
            "subject": asset.get("subject"),
        })

    props_events = []
    for event in edit_data.get("timeline", []):
        if event.get("asset_id") and event["asset_id"] not in manifest_assets:
            raise PropsError(f"Event {event.get('event_id')} references unknown asset {event['asset_id']}.")
        if event.get("duration", 0) <= 0:
            raise PropsError(f"Event {event.get('event_id')} has non-positive duration.")
        props_events.append({
            "event_id": event.get("event_id"),
            "scene_id": event.get("scene_id"),
            "shot_id": event.get("shot_id"),
            "track_id": event.get("track_id"),
            "role": event.get("role"),
            "asset_id": event.get("asset_id"),
            "start": event.get("start"),
            "end": event.get("end"),
            "duration": event.get("duration"),
            "z_index": event.get("z_index", 0),
            "purpose": event.get("purpose"),
            "framing": event.get("crop"),
            "camera_intent": event.get("camera_intent"),
            "motion_intent": event.get("motion_intent"),
            "transition_in": event.get("transition_in"),
            "transition_out": event.get("transition_out"),
            "caption_ref": event.get("caption_ref"),
            "audio_ref": event.get("audio_ref"),
            "overlay_disabled": bool(event.get("overlay_disabled", False)),
        })

    props_scenes = []
    for scene_id, scene in scenes.items():
        scene_events = [ev for ev in edit_data.get("timeline", []) if ev.get("scene_id") == scene_id]
        sc_start = min((ev.get("start", 0.0) for ev in scene_events), default=scene.get("start_seconds", 0.0))
        sc_end = max((ev.get("end", 0.0) for ev in scene_events), default=scene.get("end_seconds", 0.0))
        props_scenes.append({
            "scene_id": scene_id,
            "narrative_role": scene.get("narrative_role", ""),
            "subject": scene.get("subject", ""),
            "visual_purpose": scene.get("visual_purpose", ""),
            "visual_metaphor": scene.get("visual_metaphor", ""),
            "environment": scene.get("environment"),
            "depth_strategy": scene.get("depth_strategy"),
            "signature_device_usage": scene.get("signature_device_usage", "none"),
            "start": sc_start if sc_start is not None else scene.get("start_seconds"),
            "end": sc_end if sc_end is not None else scene.get("end_seconds"),
        })

    props_captions = []
    for caption in edit_data.get("caption_track", []):
        section = sections.get(caption.get("caption_text_reference"), {})
        text = section.get("spoken_text", "")
        if not text:
            warnings.append(f"Caption {caption.get('event_id')} has no script text; carrying the reference through.")
        props_captions.append({
            "event_id": caption.get("event_id"),
            "scene_id": caption.get("scene_id"),
            "start": caption.get("start"),
            "end": caption.get("end"),
            "textReference": text or caption.get("caption_text_reference", ""),
            "emphasisWords": caption.get("emphasis_words", []),
        })

    props_audio = []
    for track in ("narration", "music", "sfx"):
        for clip in edit_data.get("audio_tracks", {}).get(track, []):
            requirement = clip.get("audio_requirement") or {}
            asset_file = clip.get("audio_asset_id")
            public_path = None
            if asset_file:
                candidate = Path(str(asset_file).replace("\\", "/"))
                source = projects_root.parent / candidate if candidate.parts[:1] == ("projects",) else projects_root / candidate
                if not source.is_file():
                    raise PropsError(f"Audio {clip.get('event_id')} references missing file {asset_file}; no silent placeholder created.")
                target = assets_out / f"{clip.get('event_id')}{source.suffix or '.mp3'}"
                if source.suffix.lower() == ".mp3":
                    target = target.with_suffix(".wav")
                    import subprocess
                    subprocess.run(["ffmpeg", "-y", "-i", str(source), "-acodec", "pcm_s16le", "-ar", "48000", "-ac", "2", str(target)], check=True, capture_output=True)
                else:
                    shutil.copyfile(source, target)
                public_path = f"http://127.0.0.1:8000/{target.name}"
            props_audio.append({
                "event_id": clip.get("event_id"),
                "track": track,
                "start": clip.get("start"),
                "end": clip.get("end"),
                "publicPath": public_path,
                "requirement": requirement,
            })

    cta = edit_data.get("cta", {})
    lock_source = edit_data.get("runtime_lock_source", {}) or {}
    props = {
        "productionId": edit_data.get("production_id"),
        "editArtifactVersion": None,  # filled by the caller from the envelope
        "editArtifactHash": None,  # filled by the caller from the envelope
        "lock": {
            "renderer_family": edit_data.get("renderer_family"),
            "render_runtime": edit_data.get("render_runtime"),
            "composition_mode": edit_data.get("composition_mode"),
            "locked_concept_id": lock_source.get("locked_concept_id"),
            "proposal_artifact_version": lock_source.get("version"),
            "proposal_artifact_hash": lock_source.get("content_hash"),
        },
        "platform": {
            "profile": edit_data.get("platform_profile"),
            "resolution": platform_profile.get("resolution"),
            "fps": platform_profile.get("fps"),
            "duration_constraints": platform_profile.get("duration_constraints"),
            "safe_zones": platform_profile.get("safe_zones"),
        },
        "theme": _theme_from_art_direction(art_direction_data),
        "scenes": props_scenes,
        "assets": props_assets,
        "events": props_events,
        "captions": props_captions,
        "audio": props_audio,
        "cta": {
            "scene_id": cta.get("scene_id"),
            "start": cta.get("start"),
            "end": cta.get("end"),
            "branding": cta.get("channel_branding", ""),
        },
    }
    return props, warnings
