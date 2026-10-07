"""Phase 15B Claim-to-Visual Grounding Engine.

Extracts factual claims, entities, actions, and relationships from narration text
and research context, producing an intermediate ClaimVisualPlan with explicit
required visual evidence, unacceptable visual rules, and grounding audits.
"""
from __future__ import annotations

import re
from typing import Any, Optional
from .models import (
    ClaimType,
    ClaimVisualPlan,
    GroundingLevel,
    SceneClaimQAEvaluation,
    SceneVisualPlan,
)


def extract_claim_visual_plan(
    section: dict[str, Any],
    scene_idx: int,
    total_scenes: int,
    topic: str,
    research_context: str = "",
    research_pack: Optional[dict[str, Any]] = None,
) -> ClaimVisualPlan:
    """Extract structured factual claim and visual evidence requirements from script & research."""
    sec_id = section.get("section_id") or section.get("id") or f"sec_{scene_idx+1:02d}"
    scene_id = section.get("scene_id") or f"scene_{scene_idx+1:02d}"
    text = section.get("spoken_text", "").strip()
    role = section.get("narrative_role", "").lower()
    text_lower = text.lower()
    topic_lower = topic.lower()

    # Extract named entities from research pack if available
    research_entities: list[str] = []
    if research_pack:
        stories = research_pack.get("stories") or []
        for s in stories[:3]:
            for ent in s.get("entities") or []:
                if ent and ent not in research_entities:
                    research_entities.append(ent)
        claims = research_pack.get("claims") or []
        for c in claims[:3]:
            claim_text = c.get("claim", "")
            for word in ["Astra", "GPT-6", "Figure", "Boston Dynamics", "Tesla", "Kiva"]:
                if word.lower() in claim_text.lower() and word not in research_entities:
                    research_entities.append(word)

    # 1. Channel CTA / Brand Callout
    is_cta = (total_scenes > 1 and scene_idx == total_scenes - 1) or role == "cta" or "subscribe" in text_lower
    if is_cta:
        return ClaimVisualPlan(
            claim_id=f"claim_{scene_id}",
            section_id=sec_id,
            scene_id=scene_id,
            narration_text=text,
            claim_type=ClaimType.BRAND_CALLOUT,
            entities=["AI Simplified Lab"],
            action="subtle kinetic breathing pulse of channel emblem and subscriber callout",
            object="channel insignia and briefing badge",
            environment="minimalist dark obsidian architectural studio with polished reflection floor",
            relationship="viewer connects with authoritative frontier AI briefing channel",
            required_visual_evidence=[
                "channel brand emblem",
                "subscribe callout",
                "clean negative space",
            ],
            preferred_visualization="Minimalist dark obsidian studio with glowing AI Simplified emblem and clean typography",
            acceptable_alternatives=[
                "Obsidian reflective studio with cyan brand geometry",
                "Dark graphite presentation stage with subtle rim glow",
            ],
            unacceptable_visuals=[
                "generic cluttered UI",
                "random unrelated robotics footage",
                "server room",
                "giant permanent text boxes",
                "bright neon rainbow background",
            ],
            grounding_level=GroundingLevel.LEVEL_4.value,
        )

    # 2. NLP / AI Terminology Branch (Tokens, Embeddings, Attention, Language)
    is_nlp_topic = any(k in topic_lower or k in text_lower for k in [
        "token", "embedding", "attention", "transformer", "language", "nlp", "prompt", "vocabulary", "vector", "word"
    ])
    if is_nlp_topic:
        if scene_idx == 0 or role == "hook" or any(k in text_lower for k in ["how ai", "understands", "language", "human words", "prompt"]):
            return ClaimVisualPlan(
                claim_id=f"claim_{scene_id}",
                section_id=sec_id,
                scene_id=scene_id,
                narration_text=text,
                claim_type=ClaimType.CAPABILITY,
                entities=["natural language prompt input", "raw text stream", "interactive command prompt"],
                action="raw user prompt typing into terminal input box, keywords illuminating with glowing accents and splitting into word chips",
                object="interactive prompt box and raw text stream",
                environment="deep tech minimalist command console with subtle ambient slate glow",
                relationship="AI decodes human language by breaking sentences into discrete computational inputs",
                required_visual_evidence=[
                    "animated typing prompt box",
                    "text tokenization",
                    "word highlights",
                    "absence of warehouse robotics",
                ],
                preferred_visualization="Animated typing prompt box where raw English text flows in, instantly highlighting words and breaking them apart with an energetic glow",
                acceptable_alternatives=[
                    "Terminal prompt receiving human sentence with real-time character cursor and glowing keyword tokens",
                    "Splitting text stream with glowing bounding brackets around individual words",
                ],
                unacceptable_visuals=[
                    "warehouse robots",
                    "conveyor belt",
                    "robotic gripper clamp",
                    "forklift",
                    "unrelated factory floor",
                ],
                grounding_level=GroundingLevel.LEVEL_4.value,
            )
        elif any(k in text_lower for k in ["token", "shatter", "fragment", "numerical", "bpe", "vocab", "id"]):
            return ClaimVisualPlan(
                claim_id=f"claim_{scene_id}",
                section_id=sec_id,
                scene_id=scene_id,
                narration_text=text,
                claim_type=ClaimType.MECHANISM,
                entities=["text tokens", "numeric token IDs", "numerical coordinate matrix"],
                action="words exploding into numeric token ID chips ([2044], [9301], [124]) cascading into a 3D matrix coordinate space",
                object="numeric token chips and high-dimensional matrix",
                environment="cyber navy high-density data coordinate space",
                relationship="raw vocabulary maps into mathematical IDs that computers calculate",
                required_visual_evidence=[
                    "exploding token chips",
                    "numeric token IDs",
                    "numerical coordinate matrix",
                    "absence of robotic arms",
                ],
                preferred_visualization="Words exploding into numeric ID chips ([2044], #99301, [124]) cascading into a 3D matrix coordinate space",
                acceptable_alternatives=[
                    "Cascading stream of colored token chips with discrete ID numbers entering tensor memory",
                    "Subword split breakdown showing byte-pair encoding IDs",
                ],
                unacceptable_visuals=[
                    "robotic arms",
                    "conveyor belts",
                    "warehouse agv",
                    "factory floor",
                ],
                grounding_level=GroundingLevel.LEVEL_4.value,
            )
        elif any(k in text_lower for k in ["attention", "self-attention", "weight", "weights", "multi-head", "query", "key"]):
            return ClaimVisualPlan(
                claim_id=f"claim_{scene_id}",
                section_id=sec_id,
                scene_id=scene_id,
                narration_text=text,
                claim_type=ClaimType.MECHANISM,
                entities=["multi-head self-attention", "token nodes", "dynamic attention weight connections"],
                action="token nodes connecting via dynamic glowing weight lines that thicken and brighten based on calculated attention strength",
                object="interactive neural graph network and attention weight matrix",
                environment="dark indigo neural graph space with electric violet and amber lines",
                relationship="attention mechanism computes simultaneous contextual dependencies across all tokens",
                required_visual_evidence=[
                    "interactive neural graph",
                    "token nodes",
                    "dynamic glowing attention lines",
                    "scaling weight thickness",
                    "absence of warehouse obstacle maps",
                ],
                preferred_visualization="Interactive neural graph network where token nodes connect to each other via dynamic glowing lines that thicken based on attention strength",
                acceptable_alternatives=[
                    "Attention heatmap matrix grid lighting up cross-token dependency scores",
                    "Query-Key-Value vector projection with dynamic line intensity",
                ],
                unacceptable_visuals=[
                    "warehouse agv top-down map",
                    "obstacle rover",
                    "conveyor table",
                    "factory floor",
                ],
                grounding_level=GroundingLevel.LEVEL_4.value,
            )
        elif any(k in text_lower for k in ["vector", "embedding", "mastering", "latent", "space", "model", "mechanics"]):
            return ClaimVisualPlan(
                claim_id=f"claim_{scene_id}",
                section_id=sec_id,
                scene_id=scene_id,
                narration_text=text,
                claim_type=ClaimType.CAPABILITY,
                entities=["high-dimensional vector space", "3D vector point cloud", "cosine similarity vectors"],
                action="rotating 3D vector point cloud showing cluster points floating in space with distance vectors connecting semantic neighbors",
                object="3D coordinate space and semantic word vectors",
                environment="pitch black coordinate space with cyan and gold point cloud",
                relationship="tokens with similar semantic meaning cluster together in high-dimensional vector space",
                required_visual_evidence=[
                    "3D vector point cloud",
                    "semantic cluster points",
                    "distance vectors",
                    "cosine angle metrics",
                    "absence of logistics fleet",
                ],
                preferred_visualization="Rotating 3D vector point cloud showing cluster points floating in space with distance vectors connecting semantic neighbors",
                acceptable_alternatives=[
                    "3D coordinate axes with directional vector arrows and cosine similarity arc",
                    "Semantic clustering manifold rotating in dark obsidian space",
                ],
                unacceptable_visuals=[
                    "warehouse agvs",
                    "forklifts",
                    "conveyor lines",
                    "static tree diagram",
                ],
                grounding_level=GroundingLevel.LEVEL_4.value,
            )

    # 3. Hook / Immediate Dramatic Capability (Robotics & Physical Automation)
    if scene_idx == 0 or role == "hook":
        # Extract subject from topic
        subject_ent = "warehouse robots"
        if "astra" in topic_lower or "gpt-6" in topic_lower:
            subject_ent = "GPT-6 Astra controlled robotic mechanism"
        elif "robot" in topic_lower:
            subject_ent = "autonomous industrial robot"

        return ClaimVisualPlan(
            claim_id=f"claim_{scene_id}",
            section_id=sec_id,
            scene_id=scene_id,
            narration_text=text,
            claim_type=ClaimType.CAPABILITY,
            entities=[subject_ent, "industrial hardware", "precision gripper"],
            action="rapid high-speed pneumatic clamp executing sub-millimeter precision manipulation with zero play",
            object="physical industrial component",
            environment="industrial robotics testing rig / modern automated logistics facility",
            relationship="AI intelligence directly drives physical mechanical speed and precision",
            required_visual_evidence=[
                "robotic mechanism",
                "physical robot action",
                "precision mechanical execution",
                "absence of cartoon stylization",
            ],
            preferred_visualization="Extreme macro probe close-up of industrial robotic gripper clamping onto component with razor-sharp specular highlights and high speed",
            acceptable_alternatives=[
                "Close-up of multi-axis robotic joints pivoting rapidly with zero tolerance",
                "Dynamic tracking of robotic end-effector engaging a workpiece",
            ],
            unacceptable_visuals=[
                "cartoon stylization",
                "generic server racks",
                "static robot sitting idle",
                "abstract neural brain with no machine",
                "unrelated futuristic city",
            ],
            grounding_level=GroundingLevel.LEVEL_3.value,
        )

    # 3. Direct AI Control of Physical Machine (Capability / Direct Command)
    if any(k in text_lower for k in ["directly control", "control physical", "neural network", "sensor feedback", "motor", "actuator"]):
        ai_entity = "GPT-6 Astra" if "astra" in topic_lower or "gpt" in topic_lower else "Advanced neural network"
        return ClaimVisualPlan(
            claim_id=f"claim_{scene_id}",
            section_id=sec_id,
            scene_id=scene_id,
            narration_text=text,
            claim_type=ClaimType.CAPABILITY,
            entities=[ai_entity, "industrial robotic arm", "sensor feedback loop"],
            action="AI control system sends direct low-latency motor commands causing physical robotic arm to articulate precisely",
            object="multi-axis robotic actuators and physical end-effector",
            environment="industrial robotics automated workcell with real-time telemetry HUD",
            relationship="AI control source directly drives physical machine actuators with closed-loop sensor feedback",
            required_visual_evidence=[
                "AI / control source",
                "industrial robotic arm",
                "control relationship",
                "physical robot action",
            ],
            preferred_visualization="Multi-axis industrial robotic arm executing precision manipulation while visible optical telemetry conduits and control HUD show real-time command feedback",
            acceptable_alternatives=[
                "Split visual showing AI command latency HUD and robotic actuator articulation",
                "Close-up of robot joint motors pivoting with live optical sensor feedback lines",
            ],
            unacceptable_visuals=[
                "generic humanoid robot portrait",
                "server room",
                "abstract brain in dark void without robot",
                "generic AI circuitry without physical machine",
                "unrelated warehouse exterior",
                "random person using laptop",
                "futuristic city",
                "human manually operating the arm",
            ],
            grounding_level=GroundingLevel.LEVEL_4.value,
        )

    # 4. Dynamic Adaptation / Obstacle Avoidance (Adaptation / Mechanism)
    if any(k in text_lower for k in ["adapt", "obstacle", "rigid", "pre-programmed", "dynamically", "routines", "shift"]):
        return ClaimVisualPlan(
            claim_id=f"claim_{scene_id}",
            section_id=sec_id,
            scene_id=scene_id,
            narration_text=text,
            claim_type=ClaimType.DEMONSTRATION,
            entities=["autonomous logistics machines", "moving obstacles", "dynamic vector path"],
            action="machine detects moving obstacle in path and dynamically alters trajectory vector around it without stopping",
            object="unforeseen obstacles and shifting inventory pallets",
            environment="automated fulfillment warehouse floor with LED grid and active obstacle zones",
            relationship="machine senses environmental obstruction and dynamically adapts movement trajectory",
            required_visual_evidence=[
                "autonomous machine",
                "obstacle",
                "sensor detection cone",
                "altered trajectory vector",
            ],
            preferred_visualization="Autonomous rover encountering unexpected obstacle, active sensor detection cone projecting onto floor, and dynamic neon vector recalculation curving safely around obstacle",
            acceptable_alternatives=[
                "Overhead multi-agent tracking showing rovers dynamically interweaving around shifting barrier",
                "Dual-path comparison showing rigid collision route versus green dynamic rerouted curve",
            ],
            unacceptable_visuals=[
                "generic static warehouse with no obstacle",
                "single robot driving straight with no obstacle",
                "robot crashing into obstacle",
                "unrelated office space",
                "abstract neural void",
                "static machines sitting idle",
            ],
            grounding_level=GroundingLevel.LEVEL_4.value,
        )

    # 5. Business Impact / Throughput / Fewer Delays
    if any(k in text_lower for k in ["inventory", "faster", "delay", "delays", "fewer delays", "throughput", "human intervention", "facilities"]):
        return ClaimVisualPlan(
            claim_id=f"claim_{scene_id}",
            section_id=sec_id,
            scene_id=scene_id,
            narration_text=text,
            claim_type=ClaimType.BUSINESS_IMPACT,
            entities=["automated distribution facility", "high-speed inventory flow", "logistics telemetry"],
            action="high-speed synchronized conveyor and rover network moving goods continuously with bottleneck reduction and minimal human intervention",
            object="inventory totes and package payload streams",
            environment="modern automated distribution center with multi-lane high-speed sorting corridors",
            relationship="autonomous coordination eliminates human bottlenecks and accelerates inventory flow velocity",
            required_visual_evidence=[
                "facility inventory movement",
                "high-throughput flow",
                "bottleneck reduction / delay indicator",
                "absence of human bottleneck",
            ],
            preferred_visualization="High-speed dual-channel logistics corridor showing rapid synchronized flow with green velocity vectors and telemetry displaying throughput gains and zero delays",
            acceptable_alternatives=[
                "Multi-tier sorting gantry moving packages at velocity with delay delta counter",
                "Before/after comparison of congested legacy lane versus rapid autonomous throughput stream",
            ],
            unacceptable_visuals=[
                "empty warehouse with no inventory moving",
                "congested stalled traffic with red stop lights",
                "human workers performing manual heavy lifting",
                "abstract neural void with no facility",
                "random drone flying in open sky",
            ],
            grounding_level=GroundingLevel.LEVEL_3.value,
        )

    # General Fallback Claim
    return ClaimVisualPlan(
        claim_id=f"claim_{scene_id}",
        section_id=sec_id,
        scene_id=scene_id,
        narration_text=text,
        claim_type=ClaimType.TECHNICAL_CHANGE,
        entities=[topic, "technological system"],
        action="technical system operating with high precision",
        object="hardware and software elements",
        environment="technology testing lab or deployment facility",
        relationship="system performs automated operations",
        required_visual_evidence=[
            "relevant technology subject",
            "active mechanical or digital operation",
            "clear domain context",
        ],
        preferred_visualization=f"High-contrast technical visualization depicting {topic} in an authentic operational environment",
        acceptable_alternatives=["Technical demonstration in modern research setting"],
        unacceptable_visuals=["cartoon", "generic meme imagery", "unrelated stock photography"],
        grounding_level=GroundingLevel.LEVEL_3.value,
    )


def evaluate_claim_grounding(
    claim_plan: ClaimVisualPlan,
    scene_plan: SceneVisualPlan,
) -> SceneClaimQAEvaluation:
    """Evaluate whether a SceneVisualPlan directly satisfies the ClaimVisualPlan."""
    # Synthesize search text from the scene plan
    combined_plan_text = " ".join([
        scene_plan.visual_intent,
        scene_plan.subject,
        scene_plan.action,
        scene_plan.environment,
        scene_plan.visual_prompt,
        scene_plan.shot_type,
        " ".join(scene_plan.scene_breakdown.values()),
    ]).lower()

    # 1. Evaluate Required Evidence Presence
    detected_evidence: list[str] = []
    for req in claim_plan.required_visual_evidence:
        req_clean = req.lower().replace("/", " ").replace("-", " ")
        req_words = [w for w in req_clean.split() if len(w) > 3 and w not in ["relevant", "clear", "absence"]]
        if not req_words:
            detected_evidence.append(req)
            continue
        # Check if at least one meaningful word from the requirement appears in plan
        if any(w in combined_plan_text for w in req_words):
            detected_evidence.append(req)

    total_req = max(1, len(claim_plan.required_visual_evidence))
    claim_coverage = round(len(detected_evidence) / total_req, 2)

    # 2. Entity Preservation Check
    entity_matches = 0
    total_entities = max(1, len(claim_plan.entities))
    for ent in claim_plan.entities:
        ent_words = [w.lower() for w in re.split(r"[\s/]+", ent) if len(w) > 3]
        if not ent_words or any(w in combined_plan_text for w in ent_words):
            entity_matches += 1
    entity_match = (entity_matches / total_entities) >= 0.5

    # 3. Action Preservation Check
    action_words = [w.lower() for w in re.split(r"[\s,]+", claim_plan.action) if len(w) > 4 and w not in ["executing", "showing", "system"]]
    action_matches = sum(1 for w in action_words if w in combined_plan_text)
    action_match = (action_matches / max(1, len(action_words))) >= 0.35 if action_words else True

    # 4. Relationship Preservation Check
    rel_words = [w.lower() for w in re.split(r"[\s,]+", claim_plan.relationship) if len(w) > 4]
    rel_matches = sum(1 for w in rel_words if w in combined_plan_text)
    relationship_match = (rel_matches / max(1, len(rel_words))) >= 0.30 if rel_words else True

    # 5. Contradiction & Unacceptable Visuals Check
    rejection_reasons: list[str] = []
    contradiction_detected = False

    # Check unacceptable visuals (only in depicted elements, not in negative constraints)
    unacc_text = f"{scene_plan.subject} {scene_plan.action} {scene_plan.environment}".lower()
    for unacc in claim_plan.unacceptable_visuals:
        unacc_clean = unacc.lower()
        if unacc_clean in unacc_text:
            rejection_reasons.append(f"Unacceptable visual detected: '{unacc}'")

    # Domain contradiction rules
    if claim_plan.claim_type == ClaimType.DEMONSTRATION and "crash" in combined_plan_text:
        contradiction_detected = True
        rejection_reasons.append("Contradiction: Narration claims dynamic adaptation but visual describes a collision/crash.")

    if claim_plan.claim_type == ClaimType.CAPABILITY:
        if "human manually operating" in combined_plan_text:
            contradiction_detected = True
            rejection_reasons.append("Contradiction: Narration claims AI autonomous control but visual shows manual human operation.")
        if "abstract brain in dark void without robot" in combined_plan_text or (
            "abstract" in scene_plan.visual_mode.value and "robot" not in combined_plan_text
        ):
            rejection_reasons.append("Unacceptable generic metaphor: Abstract brain/data stream with no visible physical robot.")

    if claim_plan.claim_type == ClaimType.DEMONSTRATION and "obstacle" not in combined_plan_text and "adapt" not in combined_plan_text:
        rejection_reasons.append("Missing required adaptation element: No obstacle or altered trajectory path described.")

    # 6. Compute Grounding Score
    # Score 0 - 10:
    base_score = 10.0 * (
        claim_coverage * 0.40
        + (1.0 if entity_match else 0.2) * 0.20
        + (1.0 if action_match else 0.2) * 0.20
        + (1.0 if relationship_match else 0.2) * 0.20
    )
    if contradiction_detected:
        base_score -= 4.0
    if rejection_reasons:
        base_score -= min(3.0, len(rejection_reasons) * 1.5)

    visual_grounding_score = max(0.0, min(10.0, round(base_score, 1)))

    decision = "PASS"
    if visual_grounding_score < 7.0:
        decision = "REJECT"
        if f"Grounding score {visual_grounding_score} < 7.0" not in rejection_reasons:
            rejection_reasons.append(f"Grounding score {visual_grounding_score} < 7.0 threshold.")
    if claim_coverage < 0.75:
        decision = "REJECT"
        if f"Claim coverage {claim_coverage*100:.0f}% < 80%" not in rejection_reasons:
            rejection_reasons.append(f"Claim coverage {claim_coverage*100:.0f}% < 80% threshold.")
    if contradiction_detected:
        decision = "REJECT"

    return SceneClaimQAEvaluation(
        scene_id=scene_plan.scene_id,
        narration=claim_plan.narration_text,
        claim=claim_plan.preferred_visualization or claim_plan.narration_text,
        claim_type=claim_plan.claim_type.value,
        required_evidence=claim_plan.required_visual_evidence,
        detected_evidence=detected_evidence,
        claim_coverage=claim_coverage,
        visual_grounding_score=visual_grounding_score,
        entity_match=entity_match,
        action_match=action_match,
        relationship_match=relationship_match,
        contradiction_detected=contradiction_detected,
        rejection_reasons=rejection_reasons,
        decision=decision,
    )
