"""Strongly typed, renderer-neutral Phase 6 edit-decision contract."""
from __future__ import annotations

from pathlib import Path
from typing import Literal
from urllib.parse import urlparse
from pydantic import BaseModel, Field, model_validator

FACTORY_ROOT = Path(__file__).resolve().parents[2]


def resolve_asset_path(
    production_id: str,
    asset: dict,
    projects_root: Path | str | None = None,
) -> Path | None:
    """Resolve a manifest asset file deterministically from the project root.

    Relative manifest paths never depend on the process working directory.
    Remote URLs have no local path and return None; remote references are
    validated separately as explicitly declared non-local sources.
    """
    file_path = (asset or {}).get("file_path")
    if not file_path:
        return None
    if urlparse(str(file_path)).scheme in {"http", "https"}:
        return None
    candidate = Path(str(file_path))
    if candidate.is_absolute():
        return candidate
    root = Path(projects_root) if projects_root is not None else FACTORY_ROOT / "projects"
    if candidate.parts and candidate.parts[0] == "projects":
        return root.parent / candidate
    return root / production_id / candidate

LayerRole = Literal["background", "primary_visual", "secondary_visual", "diagram", "metric", "overlay", "caption", "brand"]
TransitionType = Literal["hard_cut", "cross_dissolve", "motion_blur", "match_cut", "directional_wipe", "zoom_transition", "object_transition", "shape_morph", "light_flash", "fade"]
CameraIntent = Literal["reveal_space", "approach_subject", "expand_scale", "follow_subject", "shift_focus", "observe_static"]
MotionIntent = Literal["emerge", "assemble", "connect", "expand", "collapse", "trace", "flow", "pulse", "transform", "travel", "reveal", "compare", "count", "focus", "reorder"]
Framing = Literal["full_frame", "close", "medium", "detail", "split", "picture_in_picture", "edge_anchor", "center_focus", "off_axis"]


class TimelineEvent(BaseModel):
    event_id: str
    scene_id: str
    shot_id: str | None = None
    track_id: str
    asset_id: str | None = None
    start: float = Field(ge=0)
    end: float = Field(gt=0)
    duration: float = Field(gt=0)
    z_index: int = Field(ge=0)
    role: LayerRole
    purpose: str = Field(min_length=3)
    crop: Framing | None = None
    scale: str | None = None
    position: str | None = None
    opacity: float | None = Field(default=None, ge=0, le=1)
    blend_mode: str | None = None
    mask: str | None = None
    camera_intent: CameraIntent | None = None
    motion_intent: MotionIntent | None = None
    transition_in: TransitionType | None = None
    transition_out: TransitionType | None = None
    caption_ref: str | None = None
    audio_ref: str | None = None

    @model_validator(mode="after")
    def duration_matches_bounds(self) -> "TimelineEvent":
        if abs((self.end - self.start) - self.duration) > 0.02:
            raise ValueError("duration must equal end - start")
        return self


class CaptionEvent(BaseModel):
    event_id: str
    scene_id: str
    start: float = Field(ge=0)
    end: float = Field(gt=0)
    caption_mode: Literal["phrase", "word", "none"] = "phrase"
    caption_text_reference: str
    emphasis_words: list[str] = Field(default_factory=list)
    safe_zone: str


class AudioEvent(BaseModel):
    event_id: str
    track_id: Literal["narration", "music", "sfx"]
    start: float = Field(ge=0)
    end: float = Field(gt=0)
    audio_asset_id: str | None = None
    audio_requirement: dict | None = None
    purpose: str


class CTAPlan(BaseModel):
    scene_id: str
    start: float
    end: float
    channel_branding: str
    caption_event_id: str
    audio_asset_id: str | None = None
    audio_requirement: dict


class ValidationFlags(BaseModel):
    no_gaps: bool
    no_overlaps: bool
    all_assets_resolved: bool
    duration_covered: bool
    audio_valid: bool
    captions_valid: bool
    cta_present: bool
    renderer_locked: bool


class RuntimeLockSource(BaseModel):
    artifact_type: str = "proposal_packet"
    version: int = Field(ge=1)
    content_hash: str
    locked_at: str
    locked_concept_id: str


class EditDecisionsPayload(BaseModel):
    production_id: str
    total_duration: float = Field(gt=0)
    platform_profile: str
    platform: dict = Field(default_factory=dict)
    runtime_lock_source: RuntimeLockSource
    renderer_family: str
    render_runtime: Literal["remotion", "hyperframes", "ffmpeg_pil"]
    composition_mode: Literal["templated", "atelier"]
    timeline: list[TimelineEvent]
    video_tracks: dict[str, list[TimelineEvent]]
    audio_tracks: dict[str, list[AudioEvent]]
    caption_track: list[CaptionEvent]
    validation: ValidationFlags
    cta: CTAPlan
    asset_utilization_report: dict = Field(default_factory=dict)
    rhythm: dict = Field(default_factory=dict)
    edit_review_report: dict = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)

    def to_payload(self) -> dict:
        data = self.model_dump(mode="json")
        # Backward-compatible schema projection, while canonical named tracks stay explicit.
        data["tracks"] = {
            "video": data["timeline"],
            "narration": data["audio_tracks"].get("narration", []),
            "music": data["audio_tracks"].get("music", []),
            "sfx": data["audio_tracks"].get("sfx", []),
            "captions": data["caption_track"],
        }
        return data
