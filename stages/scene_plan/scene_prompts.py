"""Prompts, technique registries, and vocabulary for the Scene Plan stage.

Enforces editorial visual storytelling over template selection.
"""
from __future__ import annotations

import json
from typing import Any

VALID_VISUAL_TECHNIQUES: set[str] = {
    "diagram_reveal",
    "analogy_visualization",
    "stat_punch",
    "timeline_progression",
    "network_build",
    "system_assembly",
    "system_explosion",
    "cause_effect",
    "comparison",
    "scale_transition",
    "object_transformation",
    "evidence_wall",
    "cinematic_broll",
    "document_stack",
    "interface_walkthrough",
    "code_walkthrough",
    "zoom_and_focus",
    "kinetic_typography",
    "map_journey",
    "data_dashboard",
}

VALID_CAMERA_INTENTS: set[str] = {
    "reveal_space",
    "approach_subject",
    "follow_subject",
    "expand_scale",
    "shift_focus",
    "observe_static",
    "cross_system",
}

VALID_MOTION_INTENTS: set[str] = {
    "emerge",
    "assemble",
    "connect",
    "expand",
    "collapse",
    "trace",
    "flow",
    "pulse",
    "transform",
    "travel",
    "reveal",
    "compare",
    "count",
    "focus",
    "reorder",
}

VALID_SCENE_TYPES: set[str] = {
    "talking_head",
    "broll",
    "animation",
    "character_scene",
    "diagram",
    "text_card",
    "transition",
    "generated",
    "screen_recording",
}

SCENE_PLAN_SYSTEM_PROMPT = """You are the Lead Editorial Scene Director for AI Simplified Lab.
Your job is to transform a timed narration script and art direction into a shot-by-shot semantic scene plan.

CRITICAL EDITORIAL PRINCIPLES:
1. WHAT SHOULD EXIST (NOT RENDER CODE):
   - Describe editorial storytelling intent: camera intent, physical subjects, spatial shifts, and viewer comprehension.
   - FORBIDDEN FIELDS / VOCABULARY:
     * hero_chip, card, PIL coordinate, Remotion component name, pixel dimensions, widget.
     * Do NOT prescribe renderer code. Prescribe EDITORIAL VISION.

2. VIEWER UNDERSTANDING (MANDATORY):
   - Every scene must state specifically: "What can the viewer SEE that they could not understand from narration alone?"
   - FORBIDDEN: "Viewer sees AI visualization", "Viewer sees graphic", "Viewer understands AI".
   - REQUIRED: Specific mechanism or scale (e.g. "Viewer sees exponential memory pressure as context window grows").

3. VISUAL PURPOSE:
   - Why does this scene exist? (e.g. establish scale, introduce problem, make abstraction tangible, show mechanism, provide evidence).

4. VISUAL METAPHOR FIDELITY:
   - Ground visual subjects in the locked concept and art direction metaphor (e.g. industrial machine, power grid, historical archive, living network).
   - REJECT generic "modern AI graphics" or "futuristic dynamic background".

5. CONTINUITY AND PROGRESSION:
   - Scenes are NOT disconnected slides. Scene N flows organically from Scene N-1 into Scene N+1.
   - Describe `continuity_from_previous` and `continuity_to_next`.

6. VARIETY GOVERNOR RULES (STRICT QUALITY GATES):
   - CRITICAL: NO 3 consecutive scenes can share the same `type`!
     Allowed types: talking_head, broll, animation, character_scene, diagram, text_card, transition, generated, screen_recording.
     Vary scene types: e.g. broll -> diagram -> animation -> generated -> text_card
   - CRITICAL: NO 3 consecutive scenes can share the same `visual_technique`!
     Use at least 3 distinct visual techniques across the video.
   - NO 3 consecutive scenes can share the same `composition_intent`!
   - High visual variance requires bold shifts in perspective.

7. CTA FINALITY:
   - The CTA scene MUST be the absolute final scene.
   - `narrative_role`: "cta"
   - `type`: "text_card"
   - `visual_technique`: "kinetic_typography"
   - `viewer_understanding`: "Viewer knows how to continue following the channel and subscribe."
   - `visual_purpose`: "Convert attention into subscription."

8. JSON OUTPUT FORMAT:
   Return valid JSON without markdown wrapping:
   {
     "scenes": [
       {
         "scene_id": "scene_01",
         "type": "broll",
         "script_section_id": "sec_01",
         "start_seconds": 0.0,
         "end_seconds": 5.0,
         "narrative_role": "hook",
         "information_role": "problem_statement",
         "viewer_understanding": "Viewer grasps that ...",
         "visual_purpose": "establish scale",
         "visual_metaphor": "...",
         "subject": "...",
         "subject_action": "...",
         "environment": "...",
         "composition_intent": "wide isometric landscape",
         "spatial_relationships": "...",
         "depth_strategy": "foreground telemetry, deep background server racks",
         "camera_intent": "approach_subject",
         "motion_intent": "assemble",
         "transition_intent": "hard cut",
         "visual_technique": "cinematic_broll",
         "caption_intent": "kinetic phrase highlight",
         "continuity_from_previous": "cold open",
         "continuity_to_next": "camera dives into component core",
         "variation_reason": "shifts from scale to internal mechanics",
         "text_density": "low",
         "signature_device_usage": "subtle",
         "required_assets": [
           {
             "asset_type": "generated_video",
             "purpose": "establish tangible subject scale",
             "visual_role": "primary"
           }
         ]
       },
       {
         "scene_id": "scene_02",
         "type": "diagram",
         "script_section_id": "sec_02",
         "start_seconds": 5.0,
         "end_seconds": 15.0,
         "narrative_role": "mechanism",
         "information_role": "show_mechanism",
         "viewer_understanding": "Viewer sees how internal components interact ...",
         "visual_purpose": "show mechanism",
         "visual_metaphor": "...",
         "subject": "...",
         "subject_action": "...",
         "environment": "...",
         "composition_intent": "split-screen dynamic",
         "spatial_relationships": "...",
         "depth_strategy": "layered schematic plane",
         "camera_intent": "shift_focus",
         "motion_intent": "connect",
         "transition_intent": "directional push",
         "visual_technique": "system_assembly",
         "caption_intent": "metric callout",
         "continuity_from_previous": "tracks from overview",
         "continuity_to_next": "scales into cloud infrastructure",
         "variation_reason": "transitions from macro view to internal architecture",
         "text_density": "medium",
         "signature_device_usage": "none",
         "required_assets": [
           {
             "asset_type": "native_diagram",
             "purpose": "show internal data flow",
             "visual_role": "primary"
           }
         ]
       }
     ]
   }
"""


def build_scene_plan_prompt(
    topic: str,
    script_data: dict[str, Any],
    selected_concept: dict[str, Any],
    art_direction_data: dict[str, Any],
    research_brief_data: dict[str, Any] | None = None,
) -> str:
    """Build detailed prompt for editorial scene planning."""
    sections = script_data.get("sections", [])
    script_beats = []
    for s in sections:
        sec_id = s.get("section_id") or s.get("id")
        role = s.get("narrative_role")
        start = s.get("estimated_start") or s.get("timestamp_start", 0.0)
        end = s.get("estimated_end") or s.get("timestamp_end", 0.0)
        text = s.get("spoken_text", "")
        v_intent = s.get("visual_intent", "")
        primary_intent = s.get("primary_intent", "")
        entities = s.get("entities", [])
        emphasis = s.get("emphasis_words", [])

        script_beats.append(
            f"SECTION {sec_id} [{start:.1f}s - {end:.1f}s] Role: {role}\n"
            f"  Narration: \"{text}\"\n"
            f"  Visual Question Answer: {v_intent}\n"
            f"  Primary Intent: {primary_intent} | Entities: {', '.join(entities)} | Emphasis: {', '.join(emphasis)}"
        )

    # Concept & Art direction
    concept_title = selected_concept.get("title", "")
    visual_metaphor = art_direction_data.get("visual_metaphor") or selected_concept.get("visual_metaphor", "")
    signature_device = art_direction_data.get("signature_device", "Dynamic telemetry trail")
    anti_patterns = art_direction_data.get("anti_patterns", [])
    palette = art_direction_data.get("palette_discipline", {})

    return f"""TOPIC: {topic}
TOTAL DURATION: {script_data.get('estimated_duration', 45.0)}s

CREATIVE DIRECTION:
- Concept: {concept_title}
- Visual Metaphor: {visual_metaphor}
- Signature Device: {signature_device} (Assign to 1-2 KEY beats only)
- Anti-Patterns to Strictly Avoid: {json.dumps(anti_patterns)}
- Palette Mood: {json.dumps(palette.get('mood', 'technical high contrast'))}

TIMED SCRIPT BEATS TO COVER (EVERY BEAT MUST BE VISUALLY REPRESENTED):
{chr(10).join(script_beats)}

AVAILABLE VISUAL TECHNIQUES:
{', '.join(sorted(VALID_VISUAL_TECHNIQUES))}

CAMERA INTENTS:
{', '.join(sorted(VALID_CAMERA_INTENTS))}

MOTION INTENTS:
{', '.join(sorted(VALID_MOTION_INTENTS))}

INSTRUCTIONS:
Design a scene for each script beat (or sub-beat) with exact timing matching the script.
Ensure the story progresses organically from beat to beat without falling into repeating slide templates.
"""
