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
    STATIC = "static"           # Visually stable, zero idle oscillation (default)
    FLOAT = "float"             # Gentle hover
    STRIDE = "stride"           # Lateral stride
    INTERACT = "interact"       # Kinetic manipulation
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
    motion: MascotMotion = MascotMotion.STATIC
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
    scene_graph: Optional[Any] = None,
) -> CharacterSpec:
    """Direct contextual character presence and behavior derived strictly from scene meaning.
    Eliminates scene-index modulo rotation. Computes collision-free scene-aware position.
    """
    topic_lower = topic.lower()
    subj_lower = subject.lower()
    act_lower = action.lower()
    role_lower = narrative_role.lower()
    combined_ctx = f"{topic_lower} {subj_lower} {act_lower} {role_lower}"

    clean_subj = subject.strip() if subject.strip() else topic.strip()
    if len(clean_subj) > 35:
        clean_subj = clean_subj[:35].rsplit(" ", 1)[0]

    is_cta = (scene_idx == total_scenes - 1) or role_lower in ("cta", "outro") or "subscribe" in combined_ctx

    # 1. Determine safe scene-aware position & real subject anchor.
    # Reference layout: the mascot is a LEFT-anchored standing guide (the left
    # 25-30% presenter column), beside — never on top of — the active visual.
    # Only when the subject itself owns the left side does the guide step across
    # to the right margin. Never dead-center.
    pos_x, pos_y = 230.0, 1150.0
    anchor_x, anchor_y = 540.0, 720.0

    if scene_graph is not None and hasattr(scene_graph, "nodes") and scene_graph.nodes:
        # Find primary node or first significant node
        primary_node = next((n for n in scene_graph.nodes if getattr(n, "is_primary", False)), scene_graph.nodes[0])
        b = getattr(primary_node, "bounds", (0, 0, 0, 0))
        if b != (0, 0, 0, 0):
            node_cx = (b[0] + b[2]) / 2.0
            node_cy = (b[1] + b[3]) / 2.0
            anchor_x, anchor_y = float(node_cx), float(node_cy)

            # Subject on the left -> guide crosses to the right margin; otherwise
            # the guide holds the left column.
            if node_cx < 460:
                pos_x, pos_y = 850.0, 1150.0
            else:
                pos_x, pos_y = 230.0, 1150.0
    elif hasattr(scene_graph, "primary_anchor") and scene_graph.primary_anchor:
        anchor_x, anchor_y = float(scene_graph.primary_anchor[0]), float(scene_graph.primary_anchor[1])
        if anchor_x < 460:
            pos_x, pos_y = 850.0, 1150.0
        else:
            pos_x, pos_y = 230.0, 1150.0

    # 2. Derive Character Role, Pose, and Tool strictly from Scene Meaning
    # CTA -> the mascot performs exactly one deliberate action: notice the subscribe
    # control, tap it once, then hold a stable welcoming pose.
    if is_cta:
        return CharacterSpec(
            role=MascotRole.GUIDE,
            pose="point_tap_subscribe",
            action="tapping the subscribe control",
            target="subscribe control",
            scale=1.05,
            depth_plane="midground",
            position={"x": 540.0, "y": 1050.0},
            target_anchor={"x": 540.0, "y": 1640.0},  # subscribe control centre (see SceneComposition CTA card)
            motion=MascotMotion.INTERACT,
            emotion="confident_inviting",
            tool_held=None,
        )

    # Hook / Topic Introduction -> Explorer
    if role_lower in ("hook", "intro") or (scene_idx == 0 and not any(k in act_lower for k in ["tune", "debug", "benchmark", "vs"])):
        return CharacterSpec(
            role=MascotRole.EXPLORER,
            pose="presenting_forward",
            action=f"exploring {clean_subj}",
            target=clean_subj,
            scale=1.2,
            depth_plane="midground",
            position={"x": pos_x, "y": pos_y},
            target_anchor={"x": anchor_x, "y": anchor_y},
            motion=MascotMotion.STRIDE,
            emotion="intense_curious",
            tool_held="optical_scanner",
        )

    # Parsing, tokenizing, embedding, data vectors, pipeline flow
    if any(k in combined_ctx for k in ["token", "embed", "vector", "pipeline", "ingest", "parse", "dimension", "data"]):
        return CharacterSpec(
            role=MascotRole.ENGINEER,
            pose="directing_flow",
            action=f"directing {clean_subj} flow",
            target=clean_subj,
            scale=1.15,
            depth_plane="midground",
            position={"x": pos_x, "y": pos_y},
            target_anchor={"x": anchor_x, "y": anchor_y},
            motion=MascotMotion.INTERACT,
            emotion="analytical_focused",
            tool_held="vector_token",
        )

    # Telemetry, latency, throughput, benchmarking, comparison, contrast
    if any(k in combined_ctx for k in ["latency", "throughput", "telemetry", "metric", "cluster", "benchmark", "contrast", "vs", "versus", "legacy", "compute", "flops", "accelerator"]):
        return CharacterSpec(
            role=MascotRole.ANALYST,
            pose="inspecting_detail",
            action=f"verifying {clean_subj} execution",
            target=clean_subj,
            scale=1.1,
            depth_plane="midground",
            position={"x": pos_x, "y": pos_y},
            target_anchor={"x": anchor_x, "y": anchor_y},
            motion=MascotMotion.INSPECT,
            emotion="analytical_focused",
            tool_held="telemetry_hud_panel",
        )

    # Transformers, self-attention, neural models, architecture matrix
    if any(k in combined_ctx for k in ["transformer", "attention", "neural", "weight", "matrix", "architecture", "model", "layer"]):
        return CharacterSpec(
            role=MascotRole.BUILDER,
            pose="mapping_structure",
            action=f"orchestrating {clean_subj} architecture",
            target=clean_subj,
            scale=1.15,
            depth_plane="midground",
            position={"x": pos_x, "y": pos_y},
            target_anchor={"x": anchor_x, "y": anchor_y},
            motion=MascotMotion.INTERACT,
            emotion="focused_curious",
            tool_held="quantum_stylus",
        )

    # Image diffusion, denoising, generative algorithms, physics
    if any(k in combined_ctx for k in ["diffusion", "denois", "image", "gaussian", "u-net", "generative", "synthesis"]):
        return CharacterSpec(
            role=MascotRole.EXPLORER,
            pose="observing_system",
            action=f"examining {clean_subj} process",
            target=clean_subj,
            scale=1.15,
            depth_plane="midground",
            position={"x": pos_x, "y": pos_y},
            target_anchor={"x": anchor_x, "y": anchor_y},
            motion=MascotMotion.INSPECT,
            emotion="intense_curious",
            tool_held="optical_scanner",
        )

    # Default: Grounded Explorer/Guide for concept introduction
    return CharacterSpec(
        role=MascotRole.GUIDE,
        pose="presenting_forward",
        action=f"guiding focus toward {clean_subj}",
        target=clean_subj,
        scale=1.2,
        depth_plane="midground",
        position={"x": pos_x, "y": pos_y},
        target_anchor={"x": anchor_x, "y": anchor_y},
        motion=MascotMotion.STRIDE,
        emotion="neutral_intelligent",
        tool_held="optical_scanner",
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

