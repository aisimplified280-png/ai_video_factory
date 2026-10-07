"""Phase 15/15B Visual Semantic Analyzer & Claim Grounding Integrator.

Analyzes narration text, technical claims, and narrative role to determine:
- What is being said? (semantic core, factual claim)
- What should the viewer see? (concrete physical evidence vs telemetry vs macro detail)
- What should the viewer feel? (visceral precision, mechanical agency, throughput velocity)
- Connects directly to ClaimVisualPlan and maps to grounded VisualMode.
"""
from __future__ import annotations

import re
from typing import Any, Optional
from .models import ClaimType, ClaimVisualPlan, VisualMode
from .claim_grounder import extract_claim_visual_plan


class SemanticSceneIntent:
    def __init__(
        self,
        section_id: str,
        scene_id: str,
        spoken_text: str,
        narrative_role: str,
        primary_intent: str,
        what_is_said: str,
        what_viewer_sees: str,
        what_viewer_feels: str,
        recommended_mode: VisualMode,
        fallback_modes: list[VisualMode],
        claim_plan: Optional[ClaimVisualPlan] = None,
    ) -> None:
        self.section_id = section_id
        self.scene_id = scene_id
        self.spoken_text = spoken_text
        self.narrative_role = narrative_role
        self.primary_intent = primary_intent
        self.what_is_said = what_is_said
        self.what_viewer_sees = what_viewer_sees
        self.what_viewer_feels = what_viewer_feels
        self.recommended_mode = recommended_mode
        self.fallback_modes = fallback_modes
        self.claim_plan = claim_plan


def analyze_scene_intent(
    section: dict[str, Any],
    scene_idx: int,
    total_scenes: int,
    topic: str,
    research_context: str = "",
    research_pack: Optional[dict[str, Any]] = None,
) -> SemanticSceneIntent:
    """Perform deep semantic decomposition of a script section grounded in factual claims."""
    sec_id = section.get("section_id") or section.get("id") or f"sec_{scene_idx+1:02d}"
    scene_id = section.get("scene_id") or f"scene_{scene_idx+1:02d}"
    text = section.get("spoken_text", "").strip()
    role = section.get("narrative_role", "").lower()
    intent = section.get("primary_intent", "reveal")
    text_lower = text.lower()
    topic_lower = topic.lower()

    # Extract intermediate ClaimVisualPlan first (Phase 15B Step 2)
    claim_plan = extract_claim_visual_plan(
        section=section,
        scene_idx=scene_idx,
        total_scenes=total_scenes,
        topic=topic,
        research_context=research_context,
        research_pack=research_pack,
    )

    # 1. Final Scene (CTA)
    is_cta = (total_scenes > 1 and scene_idx == total_scenes - 1) or role == "cta" or "subscribe" in text_lower
    if is_cta:
        return SemanticSceneIntent(
            section_id=sec_id,
            scene_id=scene_id,
            spoken_text=text,
            narrative_role="cta",
            primary_intent="brand_lock",
            what_is_said="Channel subscription, authority callout, frontier AI briefing",
            what_viewer_sees="Clean minimalist dark futuristic tech space with subtle kinetic brand emblem",
            what_viewer_feels="Authoritative clarity and invitation to subscribe without visual chaos",
            recommended_mode=VisualMode.BRAND_CTA,
            fallback_modes=[VisualMode.ABSTRACT, VisualMode.DATA_INTERFACE],
            claim_plan=claim_plan,
        )

    # 2. Hook (Scene 0)
    combined_ctx = f"{topic_lower} {text_lower} {research_context.lower()}"
    is_nlp_topic = any(w in combined_ctx for w in [
        "token", "embedding", "attention", "transformer", "language", "nlp", "prompt", "vocabulary", "vector", "word"
    ])
    if scene_idx == 0 or role == "hook":
        if is_nlp_topic:
            return SemanticSceneIntent(
                section_id=sec_id,
                scene_id=scene_id,
                spoken_text=text,
                narrative_role="hook",
                primary_intent="emerge",
                what_is_said="AI models decode language through dynamic text prompt tokenization and embedding spaces",
                what_viewer_sees="Animated typing prompt box where raw English text flows in, instantly highlighting words and breaking them apart with an energetic glow",
                what_viewer_feels="High-tech intellectual intrigue; watching human thought decode into machine understanding",
                recommended_mode=VisualMode.INTERFACE,
                fallback_modes=[VisualMode.DATA_VISUALIZATION, VisualMode.METAPHOR],
                claim_plan=claim_plan,
            )
        elif any(w in combined_ctx for w in ["robot", "astra", "arm", "physical", "hardware", "industrial", "foundry", "actuator"]):
            return SemanticSceneIntent(
                section_id=sec_id,
                scene_id=scene_id,
                spoken_text=text,
                narrative_role="hook",
                primary_intent="emerge",
                what_is_said="Physical robotic hardware is accelerating rapidly in real-world intelligence",
                what_viewer_sees="Extreme macro close-up of high-speed industrial robotic gripper clamping onto component with sub-millimeter precision and zero play",
                what_viewer_feels="Visceral physical precision and speed; immediate hook with no text distraction",
                recommended_mode=VisualMode.DETAIL,
                fallback_modes=[VisualMode.LITERAL, VisualMode.DEMONSTRATION],
                claim_plan=claim_plan,
            )
        else:
            return SemanticSceneIntent(
                section_id=sec_id,
                scene_id=scene_id,
                spoken_text=text,
                narrative_role="hook",
                primary_intent="emerge",
                what_is_said="Unprecedented breakthrough in frontier capability",
                what_viewer_sees="Dramatic high-contrast focal reveal of core computational architecture",
                what_viewer_feels="High stakes urgency and immediate curiosity",
                recommended_mode=VisualMode.DETAIL,
                fallback_modes=[VisualMode.LITERAL, VisualMode.ENVIRONMENT],
                claim_plan=claim_plan,
            )

    # 3. Lead Story / Capability Reveal (Scene 1)
    if is_nlp_topic and any(w in text_lower for w in ["token", "shatter", "fragment", "numerical", "bpe", "vocab", "id"]):
        return SemanticSceneIntent(
            section_id=sec_id,
            scene_id=scene_id,
            spoken_text=text,
            narrative_role="reveal",
            primary_intent="dolly_through",
            what_is_said="Text shatters into discrete numerical token ID chips cascading into 3D coordinate space",
            what_viewer_sees="Words exploding into numeric ID chips ([2044], #99301, [124]) cascading into a 3D matrix coordinate space",
            what_viewer_feels="Clarity of mathematical conversion; words becoming numerical coordinates",
            recommended_mode=VisualMode.DATA_VISUALIZATION,
            fallback_modes=[VisualMode.INTERFACE, VisualMode.METAPHOR],
            claim_plan=claim_plan,
        )

    # Check if text specifically claims physical machine control vs abstract neural architecture
    has_physical_control = any(w in text_lower for w in ["control", "physical", "motor", "actuator", "hardware", "direct", "sensor feedback"])
    if has_physical_control:
        return SemanticSceneIntent(
            section_id=sec_id,
            scene_id=scene_id,
            spoken_text=text,
            narrative_role="reveal",
            primary_intent="dolly_through",
            what_is_said="AI model sends direct control signals into physical actuators with real-time sensor feedback",
            what_viewer_sees="Multi-axis industrial robotic arm executing precision manipulation directly driven by live AI control HUD with real-time sensor feedback",
            what_viewer_feels="Visceral mechanical proof of artificial intelligence directly moving the physical world",
            recommended_mode=VisualMode.LITERAL,
            fallback_modes=[VisualMode.MECHANISM, VisualMode.DEMONSTRATION],
            claim_plan=claim_plan,
        )
    elif any(w in text_lower for w in ["neural", "signal", "weights", "latent", "model", "synapse", "flow"]):
        return SemanticSceneIntent(
            section_id=sec_id,
            scene_id=scene_id,
            spoken_text=text,
            narrative_role="reveal",
            primary_intent="dolly_through",
            what_is_said="Abstract data flow and neural signal transmission",
            what_viewer_sees="Abstract visualization of glowing electric synaptic data streams in deep void",
            what_viewer_feels="Technological wonder; understanding the invisible software intelligence behind the model",
            recommended_mode=VisualMode.METAPHOR,
            fallback_modes=[VisualMode.ABSTRACT, VisualMode.DATA_INTERFACE],
            claim_plan=claim_plan,
        )

    # 4. Multi-Head Self-Attention (Escalation / Mechanism for NLP)
    if is_nlp_topic and any(w in text_lower for w in ["attention", "self-attention", "weight", "weights", "multi-head"]):
        return SemanticSceneIntent(
            section_id=sec_id,
            scene_id=scene_id,
            spoken_text=text,
            narrative_role="mechanism",
            primary_intent="dynamic_track",
            what_is_said="Multi-head self-attention connects all tokens simultaneously through dynamic mathematical weights",
            what_viewer_sees="Interactive neural graph network where token nodes connect to each other via dynamic glowing lines that thicken based on attention strength",
            what_viewer_feels="Deep insight into parallel transformer computing and mathematical synergy",
            recommended_mode=VisualMode.INTERFACE,
            fallback_modes=[VisualMode.METAPHOR, VisualMode.DATA_VISUALIZATION],
            claim_plan=claim_plan,
        )

    # 5. Vector Space / Embeddings (Implication / Scale for NLP)
    if is_nlp_topic and any(w in text_lower for w in ["vector", "embedding", "mastering", "latent", "space", "model"]):
        return SemanticSceneIntent(
            section_id=sec_id,
            scene_id=scene_id,
            spoken_text=text,
            narrative_role="implication",
            primary_intent="scale_up",
            what_is_said="High-dimensional vector embeddings map semantic relationships in continuous latent space",
            what_viewer_sees="Rotating 3D vector point cloud showing cluster points floating in space with distance vectors connecting semantic neighbors",
            what_viewer_feels="Awe at the geometric elegance of semantic meaning in high-dimensional space",
            recommended_mode=VisualMode.DATA_VISUALIZATION,
            fallback_modes=[VisualMode.METAPHOR, VisualMode.INTERFACE],
            claim_plan=claim_plan,
        )

    # 6. Dynamic Adaptation / Obstacle Avoidance (Robotics Escalation)
    if any(w in text_lower for w in ["adapt", "obstacle", "rigid", "pre-programmed", "dynamically", "routines", "fleet"]):
        return SemanticSceneIntent(
            section_id=sec_id,
            scene_id=scene_id,
            spoken_text=text,
            narrative_role="mechanism",
            primary_intent="dynamic_track",
            what_is_said="Autonomous robots detect obstacles and dynamically recalculate vector paths in real time",
            what_viewer_sees="Autonomous logistics machine encountering unexpected obstacle, active sensor detection cone projecting onto floor, and dynamic vector path recalculation curving around obstacle",
            what_viewer_feels="Dynamic momentum, intelligent adaptation, and real-time swarm intelligence",
            recommended_mode=VisualMode.DEMONSTRATION,
            fallback_modes=[VisualMode.COMPARISON, VisualMode.MECHANISM],
            claim_plan=claim_plan,
        )

    # 5. Business Impact / Throughput / Fewer Delays (Implication / Scale)
    if any(w in text_lower for w in ["inventory", "faster", "delays", "fewer delays", "human intervention", "facilities"]):
        return SemanticSceneIntent(
            section_id=sec_id,
            scene_id=scene_id,
            spoken_text=text,
            narrative_role="implication",
            primary_intent="scale_up",
            what_is_said="Accelerated facility throughput: moving goods faster with fewer delays and minimal human intervention",
            what_viewer_sees="High-throughput dual-channel automated logistics flow with synchronized speed corridors, bottleneck delay counters dropping to zero, and minimal human presence",
            what_viewer_feels="Immense logistical efficiency and tangible economic acceleration",
            recommended_mode=VisualMode.SCALE,
            fallback_modes=[VisualMode.CONSEQUENCE, VisualMode.DATA_VISUALIZATION],
            claim_plan=claim_plan,
        )

    # General Fallback:
    return SemanticSceneIntent(
        section_id=sec_id,
        scene_id=scene_id,
        spoken_text=text,
        narrative_role=role or "context",
        primary_intent=intent,
        what_is_said=text[:60],
        what_viewer_sees=f"Concrete operational visualization expressing {topic}",
        what_viewer_feels="Engaged technical curiosity",
        recommended_mode=VisualMode.DEMONSTRATION,
        fallback_modes=[VisualMode.LITERAL, VisualMode.ENVIRONMENT],
        claim_plan=claim_plan,
    )
