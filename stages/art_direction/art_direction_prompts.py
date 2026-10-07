"""Prompt engineering for Art Direction stage.

Enforces:
- Specific, concrete visual metaphor (rejects "futuristic graphics")
- Clamped dials: visual_variance=8, motion_intensity=6, information_density=5
- Concrete signature device (appears in 1-2 key beats)
- Explicit anti-patterns (no centered card every scene, etc.)
- Palette discipline with valid hex codes
"""
from __future__ import annotations

import json
from typing import Any


ART_DIRECTION_SYSTEM_PROMPT = """You are the Senior Art Director and Visual Systems Designer for AI Simplified Lab.
Your job is to define the complete visual identity, motion language, and design rules for a single production.

CRITICAL CREATIVE RULES:
1. SPECIFIC VISUAL METAPHOR: Never write generic phrases like "modern AI graphics" or "futuristic tech".
   Define a tangible physical, architectural, or technical metaphor (e.g. "server rooms behaving like an industrial power grid", "task graph unfolding like a mission control room").
2. AI SIMPLIFIED LAB DEFAULT DIALS:
   - visual_variance: 8 (high visual diversity scene-to-scene, avoids repetitive layouts)
   - motion_intensity: 6 (deliberate, punchy motion without overwhelming chaotic motion)
   - information_density: 5 (balanced technical clarity)
   All dials MUST be integers between 1 and 10.
3. SIGNATURE DEVICE: Define exactly one signature visual device that appears in 1-2 key narrative beats (e.g. "persistent telemetry HUD diagnostic overlay", "luminescent neural thread connecting components").
4. ANTI-PATTERNS: Explicitly list at least 3 things this production MUST NOT do (e.g. "no floating card in every scene", "no identical centered hero icon", "no generic stock circuit boards").
5. PALETTE DISCIPLINE: Provide exact 6-character hex codes (e.g. #0F172A, #38BDF8) with high visual contrast.
6. Output MUST be valid JSON matching the art_direction schema.
"""


def build_art_direction_prompt(
    concept: dict[str, Any],
    topic: str = "",
    script_data: dict[str, Any] | None = None,
) -> str:
    prompt_payload = {
        "topic": topic,
        "selected_concept": {
            "title": concept.get("title", ""),
            "hook": concept.get("hook", ""),
            "narrative_structure": concept.get("narrative_structure", ""),
            "visual_direction": concept.get("visual_direction", ""),
            "visual_metaphor": concept.get("visual_metaphor", ""),
            "renderer_family": concept.get("renderer_family", "explainer"),
            "render_runtime": concept.get("render_runtime", "remotion"),
            "composition_mode": concept.get("composition_mode", "atelier"),
            "tone": concept.get("tone", ""),
            "scene_grammar": concept.get("scene_grammar", ""),
        },
        "script_available": script_data is not None,
        "script_summary": script_data.get("scenes", [])[:3] if script_data else None,
        "defaults": {
            "visual_variance": 8,
            "motion_intensity": 6,
            "information_density": 5,
        },
        "expected_structure": {
            "design_read": "Detailed description of the visual identity and aesthetic principles",
            "visual_metaphor": concept.get("visual_metaphor", "Physical or architectural visual metaphor"),
            "visual_variance": 8,
            "motion_intensity": 6,
            "information_density": 5,
            "palette_discipline": {
                "primary": "#0F172A",
                "accent_1": "#38BDF8",
                "accent_2": "#F43F5E",
                "neutral": "#64748B",
                "warning": "#F59E0B"
            },
            "typography_personality": "Monospace telemetry headers paired with clean sans-serif body",
            "layout_language": "Asymmetric modular telemetry grid with split diagnostic panels",
            "texture_language": "Matte carbon background with subtle 5% grain and scanline sweeps",
            "transition_language": "Kinetic directional snap-zooms and hard graphic cuts; no cross-dissolves",
            "reference_strategy": "Wired technical diagrams meets NASA mission control monitors",
            "signature_device": "Pulsing diagnostic telemetry HUD overlay during key metric reveals",
            "anti_patterns": [
                "No floating card in every scene",
                "No identical centered hero composition",
                "No text-only explanation without tangible visual anchor",
                "No generic 3D neon brain animations"
            ],
            "quality_gates": {
                "min_visual_variance": 6
            }
        }
    }

    return (
        f"Define the Art Direction and Visual Identity for: {topic!r}\n\n"
        f"Context:\n{json.dumps(prompt_payload, indent=2)}\n\n"
        "Return ONLY a valid JSON object matching the expected structure."
    )
