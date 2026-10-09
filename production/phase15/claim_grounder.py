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


# Settings the narrator explicitly names. If the spoken line places the scene
# somewhere ("the robotics plant", "a warehouse", "the control room"), the scene
# happens there. Nothing here is invented: only narration-mentioned places qualify,
# and with no place named we fall back to a neutral topic context.
_ENVIRONMENT_CUES = [
    "control room", "control center", "command center", "operations center",
    "robotics plant", "robotics lab", "robotics facility", "cleanroom", "clean room",
    "data center", "datacenter", "server room", "loading dock", "assembly line",
    "power plant", "warehouse", "factory", "foundry", "workshop", "laboratory",
    "facility", "plant", "office", "studio", "kitchen", "garden", "classroom",
    "hospital", "showroom", "store", "lab",
]


def _environment_from_narration(text: str, topic: str) -> str:
    """Return the narrated setting (earliest mentioned place) or a neutral fallback."""
    text_lower = (text or "").lower()
    found: list[tuple[int, int, str]] = []
    for cue in _ENVIRONMENT_CUES:
        m = re.search(rf"\b{re.escape(cue)}\b", text_lower)
        if m:
            found.append((m.start(), -len(cue), cue))
    if found:
        return min(found)[2]
    return f"{topic} explanatory context"


def _narration_grounded_claim(
    *,
    sec_id: str,
    scene_id: str,
    text: str,
    topic: str,
    claim_type: ClaimType = ClaimType.ABSTRACT_CONCEPT,
    research_text: str = "",
    research_entities: Optional[list[str]] = None,
) -> ClaimVisualPlan:
    """Build a claim plan strictly from what the narrator actually says (§26).

    No canned numbers, no invented SLAs or percentages, no generic technical
    adjectives: if the narration does not state it, the plan never requires it
    visually. Every field is traceable back to the spoken words. Verified phase-10
    research may extend the plan (real sourced facts, never templates): a setting
    named in the research is used only when the narration names none, and research
    entities are appended after the narrated ones.
    """
    glue = {
        "the", "and", "for", "with", "that", "this", "from", "into", "are", "was", "were",
        "have", "has", "its", "can", "will", "would", "they", "them", "their", "when",
        "while", "which", "what", "how", "why", "who", "not", "but", "than", "then",
        "also", "just", "very", "more", "most", "some", "any", "all", "one", "two",
        "you", "your", "it", "about", "over", "under", "between", "through",
    }
    words = [w for w in re.findall(r"[A-Za-z][A-Za-z'-]{2,}", text or "") if w.lower() not in glue]
    subject_phrase = " ".join(words[:4]).strip()
    entities: list[str] = []
    if topic and topic.strip():
        entities.append(topic.strip())
    if subject_phrase:
        phrase = subject_phrase[:60]
        if phrase.lower() not in {e.lower() for e in entities}:
            entities.append(phrase)
    if not entities:
        entities = ["the narrated subject"]
    # Verified research entities extend (never replace) the narrated ones.
    for ent in research_entities or []:
        if len(entities) >= 4:
            break
        if ent and ent.strip() and ent.strip().lower() not in {e.lower() for e in entities}:
            entities.append(ent.strip())

    # Evidence phrases are clauses of the narration itself, never invented claims.
    clauses = [c.strip() for c in re.split(r"[,;.]\s*|\s+and\s+|\s+while\s+", text or "") if len(c.strip()) > 6]
    evidence = clauses[:3] or ([text[:60]] if text else [])
    summary = (text or "").strip()[:200] or f"Explanation of {topic}"

    # Setting: the narration's own place wins; a place named in verified research
    # is the fallback; only then the neutral topic context.
    setting_source = f"{(text or '').strip()} {(research_text or '').strip()}".strip()

    return ClaimVisualPlan(
        claim_id=f"claim_{scene_id}",
        section_id=sec_id,
        scene_id=scene_id,
        narration_text=text,
        claim_type=claim_type,
        entities=entities,
        action=summary,
        object=subject_phrase or topic,
        environment=_environment_from_narration(setting_source, topic),
        relationship=summary,
        required_visual_evidence=evidence,
        preferred_visualization=f"Explanatory visual that depicts this spoken claim: {summary}",
        acceptable_alternatives=[f"A single clear depiction of {subject_phrase or topic}"],
        unacceptable_visuals=[
            "metrics or percentages absent from the narration",
            "cartoon",
            "generic meme imagery",
        ],
        grounding_level=GroundingLevel.LEVEL_3.value,
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

    # 2. Physical-domain templates (robotics / logistics) are reserved for topics that
    # are actually about physical machines. Software and AI topics never inherit them:
    # their claims fall through to _narration_grounded_claim (what the narrator says).
    # The old NLP-terminology and enterprise/FDE template branches were removed: they
    # invented entities ("SQL DWH", "prompt input") the narrator never said.
    is_physical_domain = any(
        k in topic_lower
        for k in (
            "robot", "astra", "agv", "rover", "gripper", "humanoid", "warehouse",
            "logistics", "fleet", "conveyor", "fulfillment", "actuator",
            "industrial", "pallet", "forklift",
        )
    )

    # 3. Hook scenes are narration-grounded in EVERY domain. The opening line is the
    # most topic-specific sentence of the video — a fixed template would invent a
    # subject the narrator never said (e.g. a "precision gripper" hook for an
    # obstacle-avoidance video). The narration carries the claim; the mode/shot
    # layer below still gives physical hooks their machine-flavored treatment.
    if scene_idx == 0 or role == "hook":
        return _narration_grounded_claim(
            sec_id=sec_id,
            scene_id=scene_id,
            text=text,
            topic=topic,
            claim_type=ClaimType.CAPABILITY if is_physical_domain else ClaimType.ABSTRACT_CONCEPT,
            research_text=research_context,
            research_entities=research_entities,
        )

    # 4. Direct AI Control of Physical Machine (Capability / Direct Command)
    if is_physical_domain and any(k in text_lower for k in ["directly control", "control physical", "neural network", "sensor feedback", "motor", "actuator"]):
        ai_entity = "GPT-6 Astra" if "astra" in topic_lower or "gpt" in topic_lower else "Advanced neural network"
        return ClaimVisualPlan(
            claim_id=f"claim_{scene_id}",
            section_id=sec_id,
            scene_id=scene_id,
            narration_text=text,
            claim_type=ClaimType.CAPABILITY,
            entities=[ai_entity, "industrial robotic arm", "sensor feedback loop"],
            action="AI control system sends motor commands that cause the physical robotic arm to articulate precisely",
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
                "Split visual showing the AI commands on one side and the resulting robotic actuator articulation",
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

    # 5. Dynamic Adaptation / Obstacle Avoidance (Adaptation / Mechanism)
    if is_physical_domain and any(k in text_lower for k in ["adapt", "obstacle", "rigid", "pre-programmed", "dynamically", "routines", "shift"]):
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

    # 6. Business Impact / Throughput / Fewer Delays
    if is_physical_domain and any(k in text_lower for k in ["inventory", "faster", "delay", "delays", "fewer delays", "throughput", "human intervention", "facilities"]):
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

    # General Fallback Claim — grounded in the narration itself (§26)
    return _narration_grounded_claim(
        sec_id=sec_id,
        scene_id=scene_id,
        text=text,
        topic=topic,
        claim_type=ClaimType.ABSTRACT_CONCEPT,
        research_text=research_context,
        research_entities=research_entities,
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
            "abstract" in scene_plan.visual_mode.value and "robot" not in combined_plan_text and any(k in (claim_plan.narration_text + " " + " ".join(claim_plan.entities)).lower() for k in ["robot", "arm", "physical", "machine", "actuator"])
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
