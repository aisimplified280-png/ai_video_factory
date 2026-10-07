"""Phase 16 Visual Evidence Contract.

Formalizes the contract between spoken narration, factual claims, and visible evidence:
Narration -> Claim -> Visual Evidence Contract -> Shot Design -> Asset Generation
Enforces:
1. Literal First: Exact real-world depiction > Strong illustrative > Editorial diagram > Controlled metaphor.
2. Visuals Must Show Action: A static object is NOT evidence of an action.
3. Strict Hierarchy: Subject (Level 1) > Environment (Level 2) > Supporting Info (Level 3) > Decoration (None).
4. Story Specificity: Every scene must contain 2 to 4 story-specific visual anchors.
"""
from __future__ import annotations

import re
from enum import Enum
from pydantic import BaseModel, Field


class EditorialVisualMode(str, Enum):
    DOCUMENTARY = "documentary"        # Realistic operational environment, real-world machine/system
    PRODUCT = "product"                # Hero subject in controlled studio lighting, premium materials
    DEMONSTRATION = "demonstration"    # Subject performing an action with visible cause-and-effect
    INTERFACE = "interface"            # Clean editorial screen / terminal layout, legible typography
    PROCESS = "process"                # Beginning state -> transformation -> result
    COMPARISON = "comparison"          # Side-by-side or before/after contrast
    CAUSE_EFFECT = "cause_effect"      # Visible relationship between two states
    DIAGRAM = "diagram"                # Clean editorial diagram with strong hierarchy, no sci-fi clutter
    ENVIRONMENT = "environment"        # Architectural space establishing context
    DETAIL = "detail"                  # Macro tactile close-up on physical mechanical interaction
    HUMAN_CONTEXT = "human_context"    # Operator or user interaction with the technology
    EVIDENCE = "evidence"              # Direct technical telemetry or benchmark confirmation
    METAPHOR = "metaphor"              # Controlled conceptual metaphor (strictly when literal is impossible)
    BRAND = "brand"                    # Minimalist editorial brand card


class VisualEvidenceContract(BaseModel):
    """The formal contract that every scene must satisfy before asset generation."""
    scene_id: str
    section_id: str = ""
    narration: str
    claim: str
    primary_subject: str               # LEVEL 1: Dominant subject receiving strongest visual focus
    action: str                        # What the subject is actively doing (kinetic proof)
    object: str = ""                   # Recipient or counterpart of the action
    environment: str                   # LEVEL 2: Environmental context supporting the story
    relationship: str = ""             # Visual connection (e.g. AI model -> command signal -> robotic arm)
    required_visual_evidence: list[str] = Field(default_factory=list)
    optional_supporting_evidence: list[str] = Field(default_factory=list)
    forbidden_visuals: list[str] = Field(default_factory=list)
    visual_mode: EditorialVisualMode = EditorialVisualMode.DEMONSTRATION
    literalness: str = "high_illustrative"  # exact_real_world, high_illustrative, editorial_diagram
    composition_intent: str = "isolated_subject_with_quiet_background"
    story_specific_anchors: list[str] = Field(default_factory=list)  # 2-4 anchors ensuring non-generic visuals

    def to_dict(self) -> dict:
        return self.model_dump()


def extract_evidence_contract(
    narration: str,
    scene_id: str = "scene_01",
    section_id: str = "sec_01",
    topic: str = "",
    narrative_role: str = "context",
) -> VisualEvidenceContract:
    """Extract a rigorous VisualEvidenceContract from the spoken text and narrative role."""
    text_lower = narration.lower()
    topic_lower = topic.lower()

    # Default blacklist forbidden elements
    common_forbidden = [
        "pitch-black empty void",
        "cyan circuit lines",
        "glowing transparent neural brain",
        "random floating code lines",
        "generic sci-fi HUD crosshairs",
        "unrelated generic stock photography",
        "human face distortion",
    ]

    # 1. Robotic physical control / capability
    if any(k in text_lower for k in ["control", "neural network", "directly control", "manipulat", "actuator"]):
        return VisualEvidenceContract(
            scene_id=scene_id,
            section_id=section_id,
            narration=narration,
            claim="Advanced neural network directly controls physical robotic arm with low-latency closed-loop feedback",
            primary_subject="multi-axis industrial robotic manipulator arm",
            action="articulating joint motors in direct response to digital command telemetry",
            object="precision mechanical assembly or component",
            environment="modern robotics engineering lab with warm directional architectural lighting",
            relationship="AI neural controller -> command telemetry -> robotic arm physical articulation",
            required_visual_evidence=[
                "physical articulated robotic arm with realistic titanium/aluminum joints",
                "active physical articulation or gripping action",
                "quiet contextual laboratory background with depth",
                "restrained editorial telemetry card indicating low latency",
            ],
            forbidden_visuals=common_forbidden + [
                "generic humanoid robot portrait",
                "server rack room with flashing LEDs",
                "abstract glowing wires in empty space",
            ],
            visual_mode=EditorialVisualMode.DEMONSTRATION,
            literalness="high_illustrative",
            composition_intent="hero_subject_center_with_clean_architectural_backdrop",
            story_specific_anchors=[
                "GPT-6 Astra telemetry label",
                "multi-axis robotic joint mechanism",
                "precision pick-and-place component",
            ],
        )

    # 2. Dynamic adaptation / obstacle rerouting
    if any(k in text_lower for k in ["adapt", "obstacle", "rigid", "routines", "dynamically", "shift"]):
        return VisualEvidenceContract(
            scene_id=scene_id,
            section_id=section_id,
            narration=narration,
            claim="Autonomous logistics machines detect shifting obstacles in real-time and dynamically recalculate path",
            primary_subject="autonomous logistics rover machine",
            action="detecting stationary obstacle and smoothly steering along an adapted curved trajectory",
            object="unexpected cargo obstruction on warehouse floor",
            environment="clean modern fulfillment warehouse floor with subtle guide markings and warm ambient light",
            relationship="onboard sensors -> detected barrier -> recalculated spline trajectory bypass",
            required_visual_evidence=[
                "autonomous mobile robot chassis on warehouse floor",
                "visible obstacle directly in original path",
                "subtle illuminated trajectory path curving around obstacle",
                "clean background logistics facility with realistic perspective",
            ],
            forbidden_visuals=common_forbidden + [
                "abstract software flowchart box",
                "single rover driving on empty floor with no obstacle",
                "crash or collision into obstacle",
                "transformer turbine diagram",
            ],
            visual_mode=EditorialVisualMode.DEMONSTRATION,
            literalness="high_illustrative",
            composition_intent="three_quarter_isometric_overview_showing_path_adaptation",
            story_specific_anchors=[
                "autonomous warehouse rover",
                "physical floor obstacle",
                "illuminated rerouting spline",
            ],
        )

    # 3. Business impact / faster inventory flow / fewer delays
    if any(k in text_lower for k in ["inventory", "faster", "delay", "fewer delays", "throughput", "intervention", "facilities"]):
        return VisualEvidenceContract(
            scene_id=scene_id,
            section_id=section_id,
            narration=narration,
            claim="Automated multi-channel logistics corridors eliminate bottlenecks and accelerate inventory flow",
            primary_subject="high-throughput dual automated logistics corridor",
            action="synchronized payload carriers moving continuously at speed without queuing delays",
            object="inventory transport containers and sorting belts",
            environment="state-of-the-art automated distribution hub with multi-tier organization",
            relationship="coordinated autonomous fleet -> continuous inventory movement -> zero delay bottlenecks",
            required_visual_evidence=[
                "organized logistics transit channels with moving cargo payloads",
                "visible acceleration / fluid continuous motion",
                "absence of congested manual bottlenecks",
                "clean architectural facility depth with warm neutral lighting",
            ],
            forbidden_visuals=common_forbidden + [
                "retro neon runway with arcade dots",
                "empty dark warehouse with nothing moving",
                "stalled traffic with red stop lights",
            ],
            visual_mode=EditorialVisualMode.PROCESS,
            literalness="high_illustrative",
            composition_intent="wide_perspective_channel_showing_speed_and_depth",
            story_specific_anchors=[
                "dual automated transit channels",
                "synchronized cargo payloads",
                "editorial cycle time / throughput metric",
            ],
        )

    # 4. Hook / introduction (getting smarter fast)
    if any(k in text_lower for k in ["smarter", "getting smarter", "fast", "robots are", "warehouse robots"]):
        return VisualEvidenceContract(
            scene_id=scene_id,
            section_id=section_id,
            narration=narration,
            claim="Next-generation industrial robotics hardware operating with unprecedented tactile precision",
            primary_subject="precision robotic end-effector and optical sensor array",
            action="high-speed sub-millimeter engagement onto precision component with zero backlash",
            object="precision machined physical workpiece",
            environment="precision industrial robotics cleanroom or automated workcell",
            relationship="intelligent sensing array -> immediate tactile mechanical engagement",
            required_visual_evidence=[
                "tangible metallic robotic gripper with realistic matte finish",
                "fine mechanical detail (screws, linkages, optical lenses)",
                "subtle directional spotlighting creating realistic depth",
                "clear separation between gripper and muted background",
            ],
            forbidden_visuals=common_forbidden + [
                "flat polygon shapes with cyan crosshair",
                "blurry CGI cartoon textures",
            ],
            visual_mode=EditorialVisualMode.DETAIL,
            literalness="high_illustrative",
            composition_intent="extreme_macro_tactile_crop_with_shallow_depth_of_field",
            story_specific_anchors=[
                "industrial robotic gripper",
                "machined workpiece",
                "optical alignment sensor",
            ],
        )

    # 5. Brand callout / CTA
    if any(k in text_lower for k in ["subscribe", "ai simplified", "briefing", "beginning", "lab"]):
        return VisualEvidenceContract(
            scene_id=scene_id,
            section_id=section_id,
            narration=narration,
            claim="Authoritative frontier AI intelligence briefing callout with clean channel identity",
            primary_subject="AI Simplified Lab editorial brand emblem",
            action="subtle kinetic illumination and refined subscription prompt",
            object="editorial frontier briefing archive",
            environment="minimalist architectural slate studio with soft ambient warm bounce light",
            relationship="channel identity -> authoritative daily frontier briefings",
            required_visual_evidence=[
                "clean AI Simplified emblem centered with generous negative space",
                "crisp typography hierarchy with zero overlapping text lines",
                "restrained warm terracotta / steel blue accent lighting",
            ],
            forbidden_visuals=common_forbidden + [
                "overlapping text blocks",
                "rainbow neon glow",
                "busy sci-fi background clutter",
            ],
            visual_mode=EditorialVisualMode.BRAND,
            literalness="editorial_diagram",
            composition_intent="centered_studio_card_with_spacious_breathing_room",
            story_specific_anchors=[
                "AI Simplified emblem",
                "editorial subscription callout",
            ],
        )

    # Fallback generic contract
    return VisualEvidenceContract(
        scene_id=scene_id,
        section_id=section_id,
        narration=narration,
        claim=f"Technical illustration explaining {topic or 'frontier AI'}",
        primary_subject=topic or "automated technical system",
        action="operating with high efficiency in authentic operational setting",
        object="technical components and interface",
        environment="modern technological development facility",
        relationship="system performs automated operation",
        required_visual_evidence=[
            "clear primary subject with realistic texture",
            "supportive architectural environment",
            "controlled directional lighting",
        ],
        forbidden_visuals=common_forbidden,
        visual_mode=EditorialVisualMode.DOCUMENTARY,
        literalness="high_illustrative",
        composition_intent="balanced_subject_with_restrained_context",
        story_specific_anchors=[topic or "frontier AI technology"],
    )
