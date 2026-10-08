"""Phase 18 Unified Semantic Visual Director.

Single authoritative orchestrator that maps:
Script Sections + Factual Claims + Domain Context
  ↓
Directorial Decisions:
  - Subject, Action, Environment, Visual Metaphor
  - 4-Layer Depth Strategy (Background, Midground, Character, Foreground)
  - Character / Mascot presence (CharacterSpec)
  - Camera intent & motion
  - Transformative transitions
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional
from pydantic import BaseModel, Field

from production.phase15.models import VisualMode
from production.phase15.claim_grounder import extract_claim_visual_plan
from production.phase15.semantic_analyzer import analyze_scene_intent
from production.phase15.shot_director import ShotDirector
from production.phase17.transition_director import assign_transformative_transitions
from .character_director import CharacterSpec, direct_scene_character
from .scene_graph import SemanticSceneGraph, build_semantic_scene_graph


class CanonicalLayerSpec(BaseModel):
    asset_id: str
    role: str                       # "background" | "midground" | "character" | "foreground" | "primary_composite"
    z_index: int                    # 0 (bg), 10 (mid), 15 (char), 20 (fg)
    purpose: str
    relative_path: str
    parallax_factor: float          # 0.2 (bg), 1.0 (mid), 1.15 (char), 1.4 (fg)


class CanonicalSceneSpec(BaseModel):
    scene_id: str
    section_id: str
    narrative_role: str
    start_seconds: float
    end_seconds: float
    duration_seconds: float
    spoken_text: str = ""
    emphasis_words: list[str] = Field(default_factory=list)
    subject: str
    action: str
    environment: str
    visual_purpose: str
    visual_metaphor: str
    shot_type: str
    camera_motion: str
    composition: str
    transition_in: str
    transition_out: str
    character_spec: CharacterSpec
    scene_graph: Optional[SemanticSceneGraph] = None
    required_visual_evidence: list[str] = Field(default_factory=list)
    layers: list[CanonicalLayerSpec] = Field(default_factory=list)


class UnifiedVisualPlan(BaseModel):
    production_id: str
    topic: str
    total_duration_seconds: float
    scenes: list[CanonicalSceneSpec] = Field(default_factory=list)


def direct_production_scenes(
    production_id: str,
    sections: list[dict[str, Any]],
    topic: str,
    measured_durations: Optional[list[float]] = None,
    research_context: str = "",
) -> UnifiedVisualPlan:
    """Direct all scenes into canonical 4-layer specifications with character integration."""
    total_scenes = len(sections)
    transitions = assign_transformative_transitions(total_scenes)

    # 1. Semantic intent & shot direction
    intents = [
        analyze_scene_intent(sec, i, total_scenes, topic, research_context=research_context)
        for i, sec in enumerate(sections)
    ]
    director = ShotDirector()
    directed_shots = director.direct_scenes(intents, topic)

    # 2. Timeline calculation with natural speech padding
    scenes_spec: list[CanonicalSceneSpec] = []
    current_time = 0.0

    for idx, (sec, shot) in enumerate(zip(sections, directed_shots)):
        sc_id = f"scene_{idx+1:02d}"
        measured = measured_durations[idx] if (measured_durations and idx < len(measured_durations)) else float(sec.get("estimated_duration", 5.5))
        dur = round(max(measured + 0.35, 3.2), 2)
        start = round(current_time, 2)
        end = round(current_time + dur, 2)
        current_time = end

        # 3. Explicit CTA narrative role for final scene
        narrative_role = "cta" if (idx == total_scenes - 1) else sec.get("narrative_role", "context")

        # 4. Compile Semantic Scene Graph & True Subject Geometry
        scene_graph = build_semantic_scene_graph(
            scene_id=sc_id,
            scene_index=idx,
            total_scenes=total_scenes,
            narrative_role=narrative_role,
            subject=shot.subject,
            visual_purpose=shot.visual_intent,
            visual_metaphor=shot.visual_metaphor if hasattr(shot, "visual_metaphor") else "",
            spoken_text=sec.get("spoken_text", ""),
            topic=topic,
            research_claim=research_context,
        )

        # 5. Direct Character / Mascot bound dynamically to actual subject geometry
        char_spec = direct_scene_character(
            scene_idx=idx,
            total_scenes=total_scenes,
            narrative_role=narrative_role,
            subject=shot.subject,
            action=shot.action,
            topic=topic,
        )
        # Authoritative target discovery: point directly at compiled primary subject center!
        char_spec.target_anchor = {
            "x": float(scene_graph.primary_anchor[0]),
            "y": float(scene_graph.primary_anchor[1]),
        }

        # 6. Transformative Transitions (No hard cuts on scene exits)
        trans_in = "hard_cut" if idx == 0 else (transitions[idx - 1] if (idx - 1 < len(transitions)) else "zoom_transition")
        trans_out = "fade" if idx == total_scenes - 1 else (transitions[idx] if idx < len(transitions) else "zoom_transition")

        # 7. Define Canonical 4-Layer Hierarchy
        layers = [
            CanonicalLayerSpec(
                asset_id=f"ast_{sc_id}_bg",
                role="background",
                z_index=0,
                purpose=f"Atmospheric background environment: {shot.environment}",
                relative_path=f"projects/{production_id}/assets/bg_{sc_id}.png",
                parallax_factor=0.2,
            ),
            CanonicalLayerSpec(
                asset_id=f"ast_{sc_id}_mid",
                role="midground",
                z_index=10,
                purpose=f"Core architectural subject: {shot.subject}",
                relative_path=f"projects/{production_id}/assets/mid_{sc_id}.png",
                parallax_factor=1.0,
            ),
            CanonicalLayerSpec(
                asset_id=f"ast_{sc_id}_char",
                role="character",
                z_index=15,
                purpose=f"AI Simplified Lab Mascot bot performing {char_spec.action}",
                relative_path=f"projects/{production_id}/assets/char_{sc_id}.png",
                parallax_factor=1.15,
            ),
            CanonicalLayerSpec(
                asset_id=f"ast_{sc_id}_fg",
                role="foreground",
                z_index=20,
                purpose="Cinematic foreground technical framing & telemetry bounds",
                relative_path=f"projects/{production_id}/assets/fg_{sc_id}.png",
                parallax_factor=1.4,
            ),
            CanonicalLayerSpec(
                asset_id=f"ast_{sc_id}_primary",
                role="primary_visual",
                z_index=10,
                purpose=f"Master composite: {shot.subject} in {shot.environment}",
                relative_path=f"projects/{production_id}/assets/ast_{sc_id}.png",
                parallax_factor=1.0,
            ),
        ]

        scene_spec = CanonicalSceneSpec(
            scene_id=sc_id,
            section_id=sec.get("id") or sec.get("section_id") or f"sec_{idx+1:02d}",
            narrative_role=sec.get("narrative_role", "context"),
            start_seconds=start,
            end_seconds=end,
            duration_seconds=dur,
            spoken_text=sec.get("spoken_text", ""),
            emphasis_words=sec.get("emphasis_words", []),
            subject=shot.subject,
            action=shot.action,
            environment=shot.environment,
            visual_purpose=shot.visual_intent,
            visual_metaphor=shot.visual_metaphor if hasattr(shot, "visual_metaphor") else "",
            shot_type=shot.shot_type,
            camera_motion=shot.camera_motion,
            composition=shot.composition,
            transition_in=trans_in,
            transition_out=trans_out,
            character_spec=char_spec,
            scene_graph=scene_graph,
            required_visual_evidence=scene_graph.required_visual_evidence,
            layers=layers,
        )
        scenes_spec.append(scene_spec)

    return UnifiedVisualPlan(
        production_id=production_id,
        topic=topic,
        total_duration_seconds=round(current_time, 2),
        scenes=scenes_spec,
    )
