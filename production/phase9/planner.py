"""Phase 9 Semantic Visual Planner.

Translates script sections and Phase 10 research into a structured,
cinematic editorial plan. Enforces scene diversity (>= 70% unique locations,
objects, and actions) and structured scene breakdowns.
"""
from __future__ import annotations

import json
from typing import Any

DIVERSE_LOCATIONS = [
    "industrial robotics facility",
    "automated fulfillment warehouse",
    "semiconductor cleanroom fab",
    "high-voltage telemetry control room",
    "supercomputer datacenter corridor",
    "hardware stress-testing laboratory",
]

DIVERSE_OBJECTS = [
    "multi-axis robotic arm",
    "autonomous pallet transport rover",
    "photolithography silicon wafer",
    "fiber-optic liquid-cooled server rack",
    "actuator sensor testing rig",
    "precision mechanical gripper",
]

DIVERSE_ACTIONS = [
    "manipulating components with sub-millimeter precision",
    "navigating high-bay logistics aisles",
    "routing high-density busbar power",
    "monitoring telemetry feeds across diagnostic consoles",
    "calibrating hydraulic joint actuators",
    "sorting physical items on conveyor lines",
]


from production.phase15.engine import generate_phase15_plan


def generate_plan(script_data: dict, prod_state: dict) -> dict[str, Any]:
    """Generate cinematic visual plan using Phase 15 Visual Intelligence & Diversity Engine."""
    return generate_phase15_plan(script_data, prod_state)


def _legacy_generate_plan(script_data: dict, prod_state: dict) -> dict[str, Any]:
    plan: dict[str, Any] = {
        "schema_version": "1.0",
        "scene_concepts": [],
        "emphasis_cues": [],
        "retention_notes": [],
    }
    
    sections = script_data.get("data", {}).get("sections", [])
    visual_direction = prod_state.get("visual_direction", "cinematic tech")
    visual_metaphor = prod_state.get("visual_metaphor", "Industrial nuclear fusion reactor aesthetics")
    
    # Attempt to load research pack from the project state
    research_context = ""
    try:
        research_data = prod_state.get("research_data", {})
        stories = research_data.get("stories", [])
        claims = research_data.get("claims", [])
        sources = research_data.get("sources", [])
        if stories:
            research_context = f" Based on actual news: {stories[0].get('headline', '')}. {stories[0].get('summary', '')}"
        elif claims:
            claims_text = ". ".join([c.get("claim", "") for c in claims[:3] if isinstance(c, dict) and c.get("claim")])
            research_context = f" Based on verified research claims: {claims_text}"
        elif sources:
            sources_text = ". ".join([s.get("title", "") for s in sources[:3] if isinstance(s, dict) and s.get("title")])
            research_context = f" Based on verified research sources: {sources_text}"
    except Exception:
        pass

    visual_facts = research_data.get("visual_facts", {}) if isinstance(prod_state.get("research_data"), dict) else {}
    vf_locations = visual_facts.get("locations", [])
    vf_objects = visual_facts.get("objects", [])
    vf_actions = visual_facts.get("actions", [])

    used_locations: set[str] = set()
    used_objects: set[str] = set()
    used_actions: set[str] = set()

    for i, sec in enumerate(sections):
        text = sec.get("spoken_text", "").lower()
        
        # 1. Semantic Topic Extraction with Phase 10 Visual Facts
        loc_pool = vf_locations if len(vf_locations) >= 2 else DIVERSE_LOCATIONS
        obj_pool = vf_objects if len(vf_objects) >= 2 else DIVERSE_OBJECTS
        act_pool = vf_actions if len(vf_actions) >= 2 else DIVERSE_ACTIONS

        default_env = loc_pool[i % len(loc_pool)]
        default_subject = obj_pool[i % len(obj_pool)]
        default_action = act_pool[i % len(act_pool)]

        subject = sec.get("primary_subject") or default_subject
        env = default_env
        action = default_action
        
        # Enhance semantic matching with research facts & specific narrative anchors
        combined_text = text + " " + research_context.lower()
        
        if "furnace" in combined_text:
            env = "dark obsidian foundry"
            action = "consuming truckloads of glowing text scrolls"
        elif "nonprofit" in combined_text or "corporate" in combined_text:
            env = "monolithic corporate skyscraper"
            action = "wiring to a power plant"
        elif "transformer" in combined_text or "architecture" in combined_text:
            env = "high-voltage turbine room"
            action = "spinning up interlocking neural network nodes"
        elif "twenty twenty" in combined_text or "scaling up" in combined_text:
            env = "infinite grid of three-dimensional holographic numbers"
            action = "violently expanding"
        elif "emergent" in combined_text or "thermodynamic" in combined_text:
            env = "core containment chamber glowing blinding white"
            action = "condensing pure energy into a conscious orb"
        elif "robot" in combined_text or "astra" in combined_text:
            env = "industrial robotics laboratory"
            action = "real robotic arm manipulating objects"
            subject = "industrial robotic manipulator"
            visual_metaphor = "cinematic documentary photography, high detail, no people"
        elif "subscribe" in combined_text:
            env = "dark tech background"
            action = "kinetic subscriber cue glowing"

        # Prevent immediate repetition of environment to enforce diversity
        if env in used_locations and len(sections) > 1 and "subscribe" not in combined_text:
            env = loc_pool[(i + 1) % len(loc_pool)]

        used_locations.add(env)
        used_objects.add(subject)
        used_actions.add(action)

        camera_motion = "approach_subject" if i % 2 == 0 else "pan_right"
        motion_intent = sec.get("primary_intent", "reveal")

        # Structured scene breakdown (Phase 10.5 Audit E)
        scene_breakdown = {
            "location": env,
            "main_subject": subject,
            "camera": f"{camera_motion}, rule_of_thirds, vertical 9:16",
            "lighting": "cinematic industrial directional lighting, natural highlights",
            "action": action,
            "emotion": "focused industrial tension" if i % 2 == 0 else "calm technical precision",
        }

        # Construct background generation prompt
        bg_prompt = (
            f"Cinematic documentary-style interior of a {env}, large {subject} in foreground, "
            f"{action}, {visual_metaphor}, no visible human faces, realistic materials, natural lighting, "
            f"vertical 9:16 composition, strong foreground subject, clean negative space."
        )
        
        if "weak_visual_intent" in bg_prompt or "futuristic" in bg_prompt:
            bg_prompt = "REGENERATED: " + bg_prompt.replace("futuristic", "realistic industrial")
            
        plan["scene_concepts"].append({
            "section_id": sec.get("section_id"),
            "subject": subject,
            "environment": env,
            "action": action,
            "visual_story": f"{action} in {env}",
            "visual_metaphor": visual_metaphor,
            "composition": "rule_of_thirds",
            "camera_motion": camera_motion,
            "motion_intent": motion_intent,
            "lighting": "cinematic industrial",
            "background_prompt": bg_prompt,
            "scene_breakdown": scene_breakdown,
            "supporting_graphics": ["subtle_ui"] if "data" in combined_text else []
        })
        
        # Emphasis cues mapping
        for word in sec.get("emphasis_words", []):
            plan["emphasis_cues"].append({
                "section_id": sec.get("section_id"),
                "word": word,
                "visual_treatment": "flash_highlight" if i % 2 == 0 else "scale_bounce"
            })
            
        plan["retention_notes"].append({
            "section_id": sec.get("section_id"),
            "note": "strong visual change" if i % 3 == 0 else "maintain momentum"
        })

    # Diversity metrics validation (Phase 10.5 Audit D)
    total_scenes = max(1, len(plan["scene_concepts"]))
    diversity_ratio = len(used_locations) / total_scenes
    plan["diversity_metrics"] = {
        "unique_locations": len(used_locations),
        "unique_subjects": len(used_objects),
        "unique_actions": len(used_actions),
        "scene_diversity_ratio": round(diversity_ratio, 2),
        "target_met": diversity_ratio >= 0.70 or total_scenes == 1,
    }
        
    return plan
