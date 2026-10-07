"""Visual fact & semantic entity extractor for Phase 10 research.

Extracts physical visual entities, locations, objects, and actions from
retrieved research headlines, snippets, and claims.
Explicitly rejects generic AI tropes ("glowing blue holograms", "matrix code")
in favor of physical engineering and documentary aesthetics.
"""
from __future__ import annotations

import re
from typing import Sequence
from .models import ClaimRecord, SourceRecord, VisualFactPack

# Taxonomies of physical grounding
PHYSICAL_OBJECTS = [
    "robot arm", "robotic gripper", "humanoid", "quadruped", "chassis",
    "silicon wafer", "microchip", "gpu cluster", "server rack", "cooling tubes",
    "heat sink", "fiber optic cable", "circuit board", "semiconductor die",
    "cleanroom suit", "soldering iron", "oscilloscope", "drone", "lidar sensor",
    "camera rig", "telemetry monitor", "actuator", "neural accelerator", "ai chip"
]

PHYSICAL_LOCATIONS = [
    "robotics lab", "automated warehouse", "logistics facility",
    "semiconductor fabrication plant", "cleanroom", "datacenter corridor",
    "server room", "industrial assembly plant", "control room",
    "hardware testing facility", "foundry", "supercomputer facility",
    "engineering workstation"
]

PHYSICAL_ACTIONS = [
    "sorting packages", "manipulating tools", "assembling hardware",
    "soldering connections", "inspecting silicon wafers", "monitoring server metrics",
    "routing power cables", "calibrating robotic arm", "docking into charging station",
    "testing mechanical actuators", "processing streaming data", "deploying autonomous models"
]

KNOWN_ENTITIES = [
    "OpenAI", "Anthropic", "DeepMind", "Google", "Meta", "NVIDIA",
    "Microsoft", "Apple", "Tesla", "Amazon", "xAI", "Perplexity",
    "Sam Altman", "Jensen Huang", "Demis Hassabis", "Dario Amodei",
    "GPT-6 Astra", "GPT-6", "GPT-5", "GPT-4o", "Claude 3.7", "Claude",
    "Gemini 2.5", "Gemini", "Llama 3", "Llama", "Blackwell", "Rubin",
    "H100", "B200", "CUDA", "Optimus", "Atlas", "Figure 01", "Figure 02"
]


def extract_visual_facts(
    topic: str,
    sources: Sequence[SourceRecord],
    claims: Sequence[ClaimRecord],
) -> VisualFactPack:
    """Extract physical visual keywords, entities, locations, objects, and actions."""
    # Combine all textual evidence
    texts: list[str] = [topic]
    for s in sources:
        texts.append(s.title)
        if s.snippet:
            texts.append(s.snippet)
    for c in claims:
        texts.append(c.claim)

    combined_text = " ".join(texts).lower()

    # 1. Match entities
    entities: list[str] = []
    for ent in KNOWN_ENTITIES:
        if ent.lower() in combined_text and ent not in entities:
            entities.append(ent)

    # 2. Match objects
    objects: list[str] = []
    for obj in PHYSICAL_OBJECTS:
        if obj.lower() in combined_text and obj not in objects:
            objects.append(obj)

    # 3. Match locations
    locations: list[str] = []
    for loc in PHYSICAL_LOCATIONS:
        if loc.lower() in combined_text and loc not in locations:
            locations.append(loc)

    # 4. Match actions
    actions: list[str] = []
    for act in PHYSICAL_ACTIONS:
        if act.lower() in combined_text and act not in actions:
            actions.append(act)

    # Domain-specific heuristic associations if none matched directly
    if not objects:
        if "robot" in combined_text or "astra" in combined_text:
            objects.extend(["robot arm", "actuator", "sensor array"])
        elif "chip" in combined_text or "hardware" in combined_text or "nvidia" in combined_text:
            objects.extend(["silicon wafer", "gpu cluster", "server rack"])
        elif "compute" in combined_text or "datacenter" in combined_text:
            objects.extend(["server rack", "cooling tubes", "fiber optic cable"])
        else:
            objects.extend(["high-density server rack", "telemetry monitor"])

    if not locations:
        if "robot" in combined_text:
            locations.append("industrial robotics lab")
        elif "chip" in combined_text or "hardware" in combined_text:
            locations.append("semiconductor fabrication plant")
        elif "datacenter" in combined_text or "model" in combined_text:
            locations.append("datacenter corridor")
        else:
            locations.append("modern industrial research facility")

    if not actions:
        if "robot" in combined_text:
            actions.append("manipulating objects with precision")
        elif "compute" in combined_text:
            actions.append("monitoring high-voltage power distribution")
        else:
            actions.append("processing real-time industrial telemetry")

    # 5. Extract visual keywords
    visual_keywords: list[str] = []
    for item in objects + locations + actions:
        for kw in item.split():
            if len(kw) > 3 and kw.lower() not in visual_keywords and kw.lower() not in {"with", "into", "real", "time"}:
                visual_keywords.append(kw.lower())

    primary_loc = locations[0]
    primary_obj = objects[0]
    primary_act = actions[0]

    visual_prompt_seed = (
        f"Cinematic documentary photography inside a {primary_loc}, "
        f"featuring a {primary_obj} {primary_act}. "
        f"Realistic industrial materials, natural directional lighting, vertical 9:16 composition, "
        f"crisp details, no visible human faces, no holographic overlays, no abstract neon tropes, clean background separation."
    )

    anti_cliche = (
        "Rejects generic neon UI, floating holographic spheres, and abstract digital code. "
        "Enforces physical hardware, industrial architecture, and authentic engineering environments."
    )

    return VisualFactPack(
        visual_keywords=visual_keywords[:15],
        entities=entities,
        locations=locations,
        objects=objects,
        actions=actions,
        visual_prompt_seed=visual_prompt_seed,
        anti_cliche_notes=anti_cliche,
    )
