"""CompositionJob contract. References an exact edit artifact; executes nothing."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

FACTORY_ROOT = Path(__file__).resolve().parent.parent

RENDERER_FAMILIES = frozenset({"explainer", "cinematic", "motion_graphics", "documentary", "screen_demo", "hybrid"})
COMPOSITION_MODES = frozenset({"templated", "atelier"})

# Single place for container expectations. The profile supplies resolution and
# frame rate; these defaults describe what "mp4" means for validation only.
OUTPUT_FORMATS = {"mp4": {"video_codec": "h264", "audio_codec": "aac", "container": "mp4"}}


def load_platform_profile(profile_ref: str, factory_root: Path | None = None) -> dict[str, Any]:
    """Load a platform profile by repo-relative reference (no scattered constants)."""
    root = Path(factory_root) if factory_root is not None else FACTORY_ROOT
    path = root / Path(str(profile_ref).replace("\\", "/"))
    if not path.is_file():
        raise FileNotFoundError(f"Platform profile not found: {profile_ref}")
    return json.loads(path.read_text(encoding="utf-8"))


def platform_aspect_ratio(profile: dict[str, Any]) -> str:
    """Derive 'W:H' from the profile resolution instead of hard-coding it."""
    resolution = profile.get("resolution", {})
    width, height = int(resolution.get("width", 0)), int(resolution.get("height", 0))
    if width <= 0 or height <= 0:
        raise ValueError(f"Platform profile has invalid resolution: {resolution!r}")
    import math
    divisor = math.gcd(width, height)
    return f"{width // divisor}:{height // divisor}"


def build_output_path(projects_root: Path | str, production_id: str, runtime_id: str, edit_version: int) -> str:
    """Deterministic output path for a job. Computing it creates nothing."""
    return (Path(projects_root) / production_id / "composition" / f"{runtime_id}_edit-v{edit_version:03d}.mp4").as_posix()


def resolve_execution_target(
    remote_policy: str,
    supports_local: bool,
    supports_remote: bool,
    local_available: bool,
    remote_available: bool,
) -> str | None:
    """Resolve local/remote execution target. None means the policy cannot run."""
    if remote_policy == "local":
        return "local" if (supports_local and local_available) else None
    if remote_policy == "remote":
        return "remote" if (supports_remote and remote_available) else None
    # auto: prefer local, then remote, never invent a third option.
    if supports_local and local_available:
        return "local"
    if supports_remote and remote_available:
        return "remote"
    return None


class CompositionJob(BaseModel):
    """Immutable routing contract binding one edit artifact to one runtime."""
    production_id: str
    edit_artifact_version: int = Field(ge=1)
    edit_artifact_hash: str
    runtime_id: str
    runtime_version: str | None = None
    renderer_family: str
    composition_mode: str
    platform_profile: str
    output_format: Literal["mp4"] = "mp4"
    output_path: str
    remote_policy: Literal["local", "remote", "auto"] = "auto"
    execution_target: Literal["local", "remote"] = "local"
    preview: bool = False
    debug: bool = False
    sample_frames: bool = False
    runtime_lock_source: dict[str, Any] = Field(default_factory=dict)
    parent_artifacts: list[dict[str, Any]] = Field(default_factory=list)

    model_config = {"extra": "forbid", "frozen": True}

    @field_validator("edit_artifact_hash")
    @classmethod
    def validate_hash_format(cls, value: str) -> str:
        if not value.startswith("sha256:") or len(value) != len("sha256:") + 64:
            raise ValueError(f"edit_artifact_hash must be a sha256: digest, got {value!r}")
        return value

    @field_validator("renderer_family")
    @classmethod
    def validate_renderer_family(cls, value: str) -> str:
        if value not in RENDERER_FAMILIES:
            raise ValueError(f"Unsupported renderer_family: {value!r}")
        return value

    @field_validator("composition_mode")
    @classmethod
    def validate_composition_mode(cls, value: str) -> str:
        if value not in COMPOSITION_MODES:
            raise ValueError(f"Unsupported composition_mode: {value!r}")
        return value


@dataclass(frozen=True)
class JobResult:
    """Router outcome: a valid job, or structured blockers. Never a fallback."""
    status: str  # "ready" | "blocked"
    job: CompositionJob | None
    blockers: tuple
