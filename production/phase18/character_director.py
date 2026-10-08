"""Phase 18 Character Director & Mascot System.

Defines the first-class AI Simplified Lab Mascot bot (`ai_simplified_bot`):
- Contextually drives narrative visual engagement across topics (AI, Cloud, Robotics, Biotech, Finance).
- Performs explicit kinetic actions interacting with scene entities (e.g., passing a data token,
  querying a vector index, adjusting a model parameter, deploying an agent container).
- Positions the character with spatial depth (midground or foreground) and parallax.
"""
from __future__ import annotations

import re
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class MascotRole(str, Enum):
    EXPLORER = "explorer"       # Investigating unknown data, inspecting embeddings, scouting
    ENGINEER = "engineer"       # Connecting pipelines, wiring models, optimizing latency
    ANALYST = "analyst"         # Examining telemetry, comparing benchmarks, auditing
    GUIDE = "guide"             # Directing viewer attention, presenting discoveries
    BUILDER = "builder"         # Constructing architectures, stacking blocks, deploying


class MascotMotion(str, Enum):
    FLOAT = "float"             # Gentle anti-gravity hovering with thruster micro-pulses
    STRIDE = "stride"           # Forward or lateral motion across architectural grid
    INTERACT = "interact"       # Kinetic manipulation with virtual tool or data token
    INSPECT = "inspect"         # Leaning in with scanner beam examining detail


class CharacterSpec(BaseModel):
    """Formal specification for the scene's character / mascot presence."""
    identity: str = "ai_simplified_bot"
    role: MascotRole = MascotRole.GUIDE
    pose: str = "presenting_forward"
    action: str = "pointing toward data flow"
    target: str = "scene telemetry"
    scale: float = 1.0          # 0.7 (distant) to 1.3 (hero closeup)
    depth_plane: str = "midground"  # "midground" (z=15) or "foreground" (z=25)
    position: dict[str, float] = Field(default_factory=lambda: {"x": 540.0, "y": 1050.0}) # Canvas coordinates (1080x1920)
    target_anchor: Optional[dict[str, float]] = None # Screen target coordinates (x, y)
    motion: MascotMotion = MascotMotion.FLOAT
    emotion: str = "focused_curious"
    tool_held: Optional[str] = None  # e.g., "data_tablet", "laser_caliper", "vector_token", "wrench"

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()


def direct_scene_character(
    scene_idx: int,
    total_scenes: int,
    narrative_role: str,
    subject: str,
    action: str,
    topic: str,
) -> CharacterSpec:
    """Direct contextual character presence and behavior aligned with narrative role.
    Anchors mascot to dedicated empty zones (y = 1040..1060) to eliminate collisions
    with primary cards, gauges, and terminal windows.
    """
    topic_lower = topic.lower()
    subj_lower = subject.lower()
    act_lower = action.lower()
    comb = f"{topic_lower} {subj_lower} {act_lower}"

    is_cta = (scene_idx == total_scenes - 1) or narrative_role.lower() in ("cta", "outro")

    if is_cta:
        return CharacterSpec(
            role=MascotRole.GUIDE,
            pose="welcoming_salute",
            action="gesturing towards subscriber briefing badge",
            target="AI Simplified Lab emblem",
            scale=1.05,
            depth_plane="midground",
            position={"x": 540.0, "y": 1050.0},
            target_anchor={"x": 540.0, "y": 710.0},
            motion=MascotMotion.FLOAT,
            emotion="confident_inviting",
            tool_held="briefing_tablet",
        )

    # 1. Hook (Scene 0) -> Explorer positioned below hero metric card pointing up at callout
    if scene_idx == 0 or narrative_role.lower() == "hook":
        return CharacterSpec(
            role=MascotRole.EXPLORER,
            pose="pointing_upward",
            action="pointing directly at core production benchmark",
            target=subject,
            scale=1.0,
            depth_plane="midground",
            position={"x": 540.0, "y": 1050.0},
            target_anchor={"x": 540.0, "y": 720.0},
            motion=MascotMotion.FLOAT,
            emotion="intense_curious",
            tool_held="optical_scanner",
        )

    # 2. Mechanism (Scene 1) -> Engineer positioned below Stage 2 node channeling data flow
    if scene_idx == 1 or narrative_role.lower() == "mechanism":
        return CharacterSpec(
            role=MascotRole.ENGINEER,
            pose="pointing_upward",
            action="routing vector tokens through active pipeline node",
            target=subject,
            scale=0.95,
            depth_plane="midground",
            position={"x": 540.0, "y": 1050.0},
            target_anchor={"x": 540.0, "y": 730.0},
            motion=MascotMotion.INTERACT,
            emotion="analytical_focused",
            tool_held="vector_token",
        )

    # 3. Escalation / Comparison (Scene 2) -> Analyst below the optimized side highlighting delta
    if scene_idx == 2 or narrative_role.lower() == "escalation":
        return CharacterSpec(
            role=MascotRole.ANALYST,
            pose="highlighting_optimization",
            action="benchmarking pipeline throughput against legacy scan",
            target="optimized cluster",
            scale=0.95,
            depth_plane="midground",
            position={"x": 720.0, "y": 1040.0},
            target_anchor={"x": 720.0, "y": 730.0},
            motion=MascotMotion.STRIDE,
            emotion="impressed_authoritative",
            tool_held="quantum_stylus",
        )

    # 4. Implication / Scale (Scene 3) -> Systems analyst below terminal window
    if scene_idx == 3 or narrative_role.lower() in ("implication", "scale"):
        return CharacterSpec(
            role=MascotRole.ANALYST,
            pose="monitoring_telemetry",
            action="verifying cluster deployment logs",
            target="production telemetry",
            scale=0.92,
            depth_plane="midground",
            position={"x": 540.0, "y": 1040.0},
            target_anchor={"x": 540.0, "y": 740.0},
            motion=MascotMotion.FLOAT,
            emotion="analytical_focused",
            tool_held="telemetry_hud_panel",
        )

    # Default -> Contextual Guide in dedicated lower zone
    return CharacterSpec(
        role=MascotRole.GUIDE,
        pose="balanced_observer",
        action=f"guiding focus toward {subject[:40]}",
        target=subject,
        scale=1.0,
        depth_plane="midground",
        position={"x": 540.0, "y": 1050.0},
        target_anchor={"x": 540.0, "y": 720.0},
        motion=MascotMotion.FLOAT,
        emotion="neutral_intelligent",
        tool_held=None,
    )


def render_character_asset(spec: CharacterSpec, output_path: Path) -> Path:
    """Render a clean transparent PNG asset representing the character/mascot."""
    from PIL import Image, ImageDraw
    img = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    cx = int(spec.position.get("x", 540))
    cy = int(spec.position.get("y", 960))
    s = spec.scale

    # Sleek bot mascot silhouette & visor
    visor_color = (217, 119, 6, 255) if spec.role == MascotRole.ENGINEER else ((16, 185, 129, 255) if spec.role == MascotRole.ANALYST else (30, 64, 175, 255))
    
    # Thruster glow
    draw.ellipse([(cx - int(35 * s), cy + int(110 * s)), (cx + int(35 * s), cy + int(130 * s))], fill=(*visor_color[:3], 140))
    
    # Body shell
    draw.rounded_rectangle([(cx - int(55 * s), cy - int(20 * s)), (cx + int(55 * s), cy + int(100 * s))], radius=int(28 * s), fill=(255, 255, 255, 255), outline=(226, 232, 240, 255), width=3)
    
    # Head shell
    draw.rounded_rectangle([(cx - int(65 * s), cy - int(130 * s)), (cx + int(65 * s), cy - int(30 * s))], radius=int(35 * s), fill=(255, 255, 255, 255), outline=(226, 232, 240, 255), width=3)
    
    # Visor screen
    draw.rounded_rectangle([(cx - int(48 * s), cy - int(110 * s)), (cx + int(48 * s), cy - int(50 * s))], radius=int(20 * s), fill=(15, 23, 42, 255))
    
    # Visor eyes
    draw.rounded_rectangle([(cx - int(36 * s), cy - int(92 * s)), (cx - int(12 * s), cy - int(72 * s))], radius=int(6 * s), fill=visor_color)
    draw.rounded_rectangle([(cx + int(12 * s), cy - int(92 * s)), (cx + int(36 * s), cy - int(72 * s))], radius=int(6 * s), fill=visor_color)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG")
    return output_path

