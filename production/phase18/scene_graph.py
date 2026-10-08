"""Phase 18.4 Semantic Visual Composition Engine & Evidence Contract Compiler.

Translates scene claims and extracted entities into genuine informational visualizations:
Research Claim & Script Entities
      ↓
VisualEvidenceContract
      ↓
SemanticSceneGraph (Nodes, Edges, Semantic Geometry)
      ↓
Spatial Geometry Compiler (Dynamic Bounding Boxes & Anchors)
      ↓
Primary Subject Target Anchor (Passed to Mascot Director)
      ↓
Multimodal Visual Judge Inspection
"""
from __future__ import annotations

import re
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field

from production.phase17.environment_generator import TopicDomain, classify_topic_domain


class SceneNodeType(str, Enum):
    ENTITY = "entity"           # Primary architectural entity (e.g. "Query Parser", "Vector Index")
    PROCESS = "process"         # Transformation / compute step
    METRIC = "metric"           # Verified numeric or status callout
    STORAGE = "storage"         # Storage, buffer, or memory unit
    TRANSFORM = "transform"     # Kernel or converter (e.g. "Attention Matrix", "Denoiser")
    BRAND = "brand"             # Lab identity & CTA crest


class SceneNode(BaseModel):
    id: str
    label: str
    node_type: SceneNodeType = SceneNodeType.ENTITY
    details: list[str] = Field(default_factory=list) # Strictly verified claims/facts only from speech
    bounds: tuple[int, int, int, int] = (0, 0, 0, 0) # (x1, y1, x2, y2) in 1080x1920 canvas
    is_primary: bool = False
    shape_style: str = "card"   # "card", "matrix_grid", "cylindrical_storage", "transform_kernel", "stack_layer"


class SceneEdge(BaseModel):
    from_node: str
    to_node: str
    relationship: str = "flows_to" # "flows_to", "transforms_to", "contrasts_with", "indexes", "routes_down"
    label: Optional[str] = None


class VisualEvidenceContract(BaseModel):
    """Canonical per-scene contract defining what must visibly appear and what is forbidden."""
    scene_id: str
    subject: str
    subject_type: str
    entities: list[str] = Field(default_factory=list)
    relationship: str = ""
    action: str = ""
    environment: str = ""
    composition_intent: str = "process_flow" # "object_transformation", "process_flow", "layered_architecture", "bipartite_comparison", "focal_explanation", "brand_identity"
    character_intent: str = "guide_focus"
    interaction_target_id: str = ""
    required_visual_evidence: list[str] = Field(default_factory=list)
    forbidden_visuals: list[str] = Field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()


class SemanticSceneGraph(BaseModel):
    scene_id: str
    topic_domain: str
    central_subject: str
    narrative_role: str
    topology: str                   # "object_transformation", "process_flow", "layered_architecture", "bipartite", "focal", "brand"
    nodes: list[SceneNode] = Field(default_factory=list)
    edges: list[SceneEdge] = Field(default_factory=list)
    primary_anchor: tuple[float, float] = (540.0, 720.0) # (x, y) center of primary subject geometry
    required_visual_evidence: list[str] = Field(default_factory=list)
    evidence_contract: Optional[VisualEvidenceContract] = None

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()


def _clean_entity_terms(text: str, domain: TopicDomain) -> list[str]:
    """Extract clean entity nouns and technical terms from text without noise."""
    tokens = re.findall(r"[A-Za-z0-9\-_]{3,}", text)
    stopwords = {
        "this", "that", "with", "from", "have", "more", "then", "into", "when",
        "your", "will", "what", "how", "over", "fast", "they", "them", "about",
        "offers", "gives", "system", "systems", "getting", "smarter", "built",
        "dark", "minimalist", "studio", "obsidian", "matrix", "wireframe",
        "graphic", "visual", "concept", "slide", "scene", "clean", "just",
        "happened", "unprecedented", "today", "daily", "frontier", "does", "actually",
        "thin", "only", "entirely", "across", "within", "beyond", "under", "hood",
        "using", "where", "which", "being", "been", "each", "both", "such",
    }
    clean_terms: list[str] = []
    seen: set[str] = set()
    for tok in tokens:
        up = tok.upper()
        if up.lower() not in stopwords and up not in seen and len(up) >= 3:
            seen.add(up)
            clean_terms.append(up)
    return clean_terms


def _extract_real_phrases_from_speech(speech: str, max_phrases: int = 2) -> list[str]:
    """Extract genuine factual snippets directly from spoken text with zero hallucinated boilerplate."""
    clauses = re.split(r"[,;.]|(?:\s+and\s+)|\b(?:while|unlike|which|to)\b", speech, flags=re.IGNORECASE)
    clean_clauses: list[str] = []
    for c in clauses:
        c_str = c.strip()
        # Clean leading prepositions
        c_str = re.sub(r"^(that|into|with|from|by|at|for|the|a|an)\s+", "", c_str, flags=re.IGNORECASE).strip()
        if 8 <= len(c_str) <= 45:
            # Title case short phrase
            clean_clauses.append(c_str.capitalize())
        if len(clean_clauses) >= max_phrases:
            break
    return clean_clauses


def build_semantic_scene_graph(
    scene_id: str = "scene_01",
    scene_index: int = 0,
    total_scenes: int = 5,
    narrative_role: str = "mechanism",
    subject: str = "",
    visual_purpose: str = "",
    visual_metaphor: str = "",
    spoken_text: str = "",
    topic: str = "",
    research_claim: str = "",
    narration: str = "",
    domain: Optional[TopicDomain] = None,
) -> SemanticSceneGraph:
    """Constructs a dynamically compiled semantic scene graph from research and script facts.
    Eliminates predetermined card templates. Visual structure is derived strictly from
    the scene's semantic intent and extracted entities.
    """
    speech = spoken_text or narration
    if domain is None:
        domain = classify_topic_domain(topic=topic, subject=subject, visual_purpose=visual_purpose, narration=speech)
    role_lower = narrative_role.lower()
    speech_lower = speech.lower()
    subj_lower = subject.lower()
    combined_ctx = f"{subj_lower} {speech_lower} {visual_purpose.lower()} {visual_metaphor.lower()}"
    clean_terms = _clean_entity_terms(f"{subject} {speech} {research_claim}", domain)
    real_facts = _extract_real_phrases_from_speech(speech, max_phrases=3)

    # Metric extraction (only if present in narration/claim)
    metric_match = re.search(r"(\+?\d+%|\d+x|\d+ms|\d+s|\d+\.\d+%)", speech + " " + research_claim)
    extracted_metric = metric_match.group(1) if metric_match else None

    is_cta = (scene_index == total_scenes - 1) or role_lower in ("cta", "outro") or any(k in speech_lower for k in ["subscribe", "lab emblem", "outro"])

    # 1. BRAND IDENTITY TOPOLOGY (CTA strictly)
    if is_cta:
        brand_node = SceneNode(
            id="brand_crest",
            label="AI SIMPLIFIED LAB",
            node_type=SceneNodeType.BRAND,
            details=["FRONTIER ARCHITECTURE BRIEFINGS", "VERIFIED RESEARCH"],
            bounds=(340, 580, 740, 860),
            is_primary=True,
            shape_style="card",
        )
        contract = VisualEvidenceContract(
            scene_id=scene_id,
            subject="AI Simplified Lab Brand Identity",
            subject_type="brand_identity",
            entities=["AI SIMPLIFIED LAB", "SUBSCRIBER EMBLEM"],
            relationship="callout",
            action="inviting subscription to research briefings",
            environment="minimalist studio",
            composition_intent="brand_identity",
            character_intent="welcoming_salute",
            interaction_target_id="brand_crest",
            required_visual_evidence=["AI SIMPLIFIED LAB", "BRIEFINGS"],
            forbidden_visuals=["generic error boxes", "unrelated schematics"],
        )
        return SemanticSceneGraph(
            scene_id=scene_id,
            topic_domain=domain.value,
            central_subject="AI Simplified Lab Brand Identity",
            narrative_role="cta",
            topology="brand",
            nodes=[brand_node],
            edges=[],
            primary_anchor=(540.0, 720.0),
            required_visual_evidence=["AI SIMPLIFIED LAB", "BRAND EMBLEM"],
            evidence_contract=contract,
        )

    # 2. LAYERED ARCHITECTURE TOPOLOGY (Evaluated before transformation to avoid 'transformer' matching 'transform')
    # e.g. "Transformer using multi-head self-attention across sequences simultaneously" or "technology stack"
    is_stack = any(k in combined_ctx for k in ["transformer", "self-attention", "attention matrix", "stack", "hierarch", "depth layer", "multi-head"])
    if is_stack:
        top_label = clean_terms[0] if len(clean_terms) > 0 else "INPUT SEQUENCE"
        mid_label = clean_terms[1] if len(clean_terms) > 1 else "ATTENTION MATRIX"
        bot_label = clean_terms[2] if len(clean_terms) > 2 else "REPRESENTATION LAYER"

        node_top = SceneNode(
            id="stack_top",
            label=top_label,
            node_type=SceneNodeType.ENTITY,
            details=[real_facts[0]] if real_facts else [f"{top_label.lower()} layer"],
            bounds=(180, 510, 900, 610),
            is_primary=False,
            shape_style="stack_layer",
        )
        node_mid = SceneNode(
            id="stack_core",
            label=mid_label,
            node_type=SceneNodeType.TRANSFORM,
            details=[real_facts[1]] if len(real_facts) > 1 else ["Multi-head self-attention"],
            bounds=(140, 630, 940, 770),
            is_primary=True,
            shape_style="matrix_grid",
        )
        node_bot = SceneNode(
            id="stack_base",
            label=bot_label,
            node_type=SceneNodeType.ENTITY,
            details=[real_facts[2]] if len(real_facts) > 2 else [f"{bot_label.lower()} layer"],
            bounds=(200, 790, 880, 890),
            is_primary=False,
            shape_style="stack_layer",
        )
        e1 = SceneEdge(from_node="stack_top", to_node="stack_core", relationship="routes_down")
        e2 = SceneEdge(from_node="stack_core", to_node="stack_base", relationship="routes_down")

        contract = VisualEvidenceContract(
            scene_id=scene_id,
            subject=subject,
            subject_type="layered_architecture",
            entities=[top_label, mid_label, bot_label],
            relationship="hierarchical_stack",
            action=f"calculating {mid_label.lower()} across layers",
            environment=f"{domain.value} architectural stack",
            composition_intent="layered_architecture",
            character_intent="orchestrating_architecture",
            interaction_target_id="stack_core",
            required_visual_evidence=[top_label, mid_label, bot_label],
            forbidden_visuals=["horizontal pipeline", "single terminal window"],
        )
        return SemanticSceneGraph(
            scene_id=scene_id,
            topic_domain=domain.value,
            central_subject=f"{mid_label} Hierarchical Stack",
            narrative_role=narrative_role,
            topology="layered_architecture",
            nodes=[node_top, node_mid, node_bot],
            edges=[e1, e2],
            primary_anchor=(540.0, 700.0), # Exact center of mid attention matrix
            required_visual_evidence=[top_label, mid_label, bot_label],
            evidence_contract=contract,
        )

    # 3. OBJECT TRANSFORMATION TOPOLOGY
    # e.g. "Documents are parsed and converted into vectors" or "diffusion noise reversed into image"
    is_transform = any(k in combined_ctx for k in ["convert", "vector embedding", "tokenized", "diffusion", "denois", "reverse gaussian", "synthesize entirely novel"]) or ("transform" in combined_ctx and "transformer" not in combined_ctx)
    if is_transform:
        src_label = clean_terms[0] if len(clean_terms) > 0 else "SOURCE DATA"
        trn_label = clean_terms[1] if len(clean_terms) > 1 else "TRANSFORM KERNEL"
        dst_label = clean_terms[2] if len(clean_terms) > 2 else "EMBEDDING SPACE"

        node_src = SceneNode(
            id="transform_source",
            label=src_label,
            node_type=SceneNodeType.STORAGE,
            details=[real_facts[0]] if real_facts else [f"Raw {src_label.lower()}"],
            bounds=(140, 590, 380, 830),
            is_primary=False,
            shape_style="card",
        )
        node_trn = SceneNode(
            id="transform_kernel",
            label=trn_label,
            node_type=SceneNodeType.TRANSFORM,
            details=[real_facts[1]] if len(real_facts) > 1 else ["Transformation process"],
            bounds=(420, 550, 660, 870),
            is_primary=True,
            shape_style="transform_kernel",
        )
        node_dst = SceneNode(
            id="transform_result",
            label=dst_label,
            node_type=SceneNodeType.ENTITY,
            details=[real_facts[2]] if len(real_facts) > 2 else [f"Synthesized {dst_label.lower()}"],
            bounds=(700, 590, 940, 830),
            is_primary=False,
            shape_style="card",
        )
        edge_1 = SceneEdge(from_node="transform_source", to_node="transform_kernel", relationship="flows_to")
        edge_2 = SceneEdge(from_node="transform_kernel", to_node="transform_result", relationship="transforms_to")

        contract = VisualEvidenceContract(
            scene_id=scene_id,
            subject=subject,
            subject_type="object_transformation",
            entities=[src_label, trn_label, dst_label],
            relationship=f"{src_label} -> {trn_label} -> {dst_label}",
            action=f"transforming {src_label.lower()} into {dst_label.lower()}",
            environment=f"{domain.value} transformation pipeline",
            composition_intent="object_transformation",
            character_intent="direct_transformation_flow",
            interaction_target_id="transform_kernel",
            required_visual_evidence=[src_label, trn_label, dst_label],
            forbidden_visuals=["static card grid", "telemetry HUD boilerplate"],
        )
        return SemanticSceneGraph(
            scene_id=scene_id,
            topic_domain=domain.value,
            central_subject=f"{src_label} -> {trn_label} -> {dst_label}",
            narrative_role=narrative_role,
            topology="object_transformation",
            nodes=[node_src, node_trn, node_dst],
            edges=[edge_1, edge_2],
            primary_anchor=(540.0, 710.0), # Exact center of transform kernel
            required_visual_evidence=[src_label, trn_label, dst_label],
            evidence_contract=contract,
        )

    # 4. BIPARTITE COMPARISON TOPOLOGY
    # e.g. "Unlike classical AI that only classifies existing data, generative models learn probability distributions"
    is_contrast = any(k in speech_lower for k in ["unlike", "instead of", "versus", "vs", "classif", "balance"])
    if is_contrast:
        left_label = clean_terms[0] if clean_terms else "CLASSIFICATION"
        right_label = clean_terms[1] if len(clean_terms) > 1 else "GENERATIVE SYNTHESIS"

        node_left = SceneNode(
            id="contrast_left",
            label=left_label,
            node_type=SceneNodeType.ENTITY,
            details=[real_facts[0]] if real_facts else [f"Existing {left_label.lower()}"],
            bounds=(150, 560, 500, 860),
            is_primary=False,
            shape_style="card",
        )
        node_right = SceneNode(
            id="contrast_right",
            label=right_label,
            node_type=SceneNodeType.ENTITY,
            details=[real_facts[1]] if len(real_facts) > 1 else [f"Novel {right_label.lower()}"],
            bounds=(580, 560, 930, 860),
            is_primary=True,
            shape_style="card",
        )
        edge = SceneEdge(from_node="contrast_left", to_node="contrast_right", relationship="contrasts_with", label="VS")

        contract = VisualEvidenceContract(
            scene_id=scene_id,
            subject=subject,
            subject_type="bipartite_comparison",
            entities=[left_label, right_label],
            relationship=f"{left_label} vs {right_label}",
            action=f"contrasting {left_label.lower()} with {right_label.lower()}",
            environment="comparative analysis",
            composition_intent="bipartite_comparison",
            character_intent="comparing_systems",
            interaction_target_id="contrast_right",
            required_visual_evidence=[left_label, right_label, "CONTRAST"],
            forbidden_visuals=["legacy prefix", "active prefix"],
        )
        return SemanticSceneGraph(
            scene_id=scene_id,
            topic_domain=domain.value,
            central_subject=f"{left_label} vs {right_label}",
            narrative_role=narrative_role,
            topology="bipartite",
            nodes=[node_left, node_right],
            edges=[edge],
            primary_anchor=(755.0, 710.0), # Center of primary target node
            required_visual_evidence=[left_label, right_label, "CONTRAST"],
            evidence_contract=contract,
        )

    # 5. PROCESS FLOW TOPOLOGY (Dynamically sized by entity count)
    # e.g. RAG database connect, client authorization flow, etc.
    if len(clean_terms) >= 3 or any(k in speech_lower for k in ["connect", "route", "database", "retrieval", "grounding", "step"]):
        n_entities = min(3, max(2, len(clean_terms)))
        margin = 130
        total_w = 1080 - 2 * margin
        spacing = 28
        box_w = (total_w - (n_entities - 1) * spacing) // n_entities

        flow_nodes: list[SceneNode] = []
        flow_edges: list[SceneEdge] = []
        for i in range(n_entities):
            bx1 = margin + i * (box_w + spacing)
            bx2 = bx1 + box_w
            lbl = clean_terms[i] if i < len(clean_terms) else f"STAGE {i+1}"
            is_p = (i == 1) or (i == n_entities - 1)
            f_detail = [real_facts[i]] if i < len(real_facts) else []
            flow_nodes.append(SceneNode(
                id=f"flow_stage_{i+1}",
                label=lbl,
                node_type=SceneNodeType.PROCESS if is_p else SceneNodeType.ENTITY,
                details=f_detail,
                bounds=(bx1, 590, bx2, 840),
                is_primary=is_p,
                shape_style="card",
            ))
            if i > 0:
                flow_edges.append(SceneEdge(
                    from_node=f"flow_stage_{i}",
                    to_node=f"flow_stage_{i+1}",
                    relationship="flows_to",
                ))

        primary_node = next((n for n in flow_nodes if n.is_primary), flow_nodes[0])
        p_cx = (primary_node.bounds[0] + primary_node.bounds[2]) / 2.0
        p_cy = (primary_node.bounds[1] + primary_node.bounds[3]) / 2.0

        contract = VisualEvidenceContract(
            scene_id=scene_id,
            subject=subject,
            subject_type="process_flow",
            entities=[n.label for n in flow_nodes],
            relationship="sequential_pipeline",
            action=f"streaming data across {len(flow_nodes)} connected stages",
            environment=f"{domain.value} pipeline",
            composition_intent="process_flow",
            character_intent="inspect_flow",
            interaction_target_id=primary_node.id,
            required_visual_evidence=[n.label for n in flow_nodes],
            forbidden_visuals=["generic terminal window"],
        )
        return SemanticSceneGraph(
            scene_id=scene_id,
            topic_domain=domain.value,
            central_subject=f"Sequential Process: {' -> '.join(n.label for n in flow_nodes)}",
            narrative_role=narrative_role,
            topology="process_flow",
            nodes=flow_nodes,
            edges=flow_edges,
            primary_anchor=(p_cx, p_cy),
            required_visual_evidence=[n.label for n in flow_nodes],
            evidence_contract=contract,
        )

    # 6. FOCAL EXPLANATION TOPOLOGY (Core Architectural Subject & Real Fact Callouts)
    hero_term = clean_terms[0] if clean_terms else (subject.split()[0].upper() if subject else "SYSTEM")
    sub_term = clean_terms[1] if len(clean_terms) > 1 else (subject.split()[-1].upper() if subject else "ARCHITECTURE")

    hero_node = SceneNode(
        id="focal_hero",
        label=f"{hero_term} // {sub_term}",
        node_type=SceneNodeType.ENTITY,
        details=real_facts if real_facts else [f"{hero_term} verified core structure"],
        bounds=(200, 550, 880, 860),
        is_primary=True,
        shape_style="card",
    )
    contract = VisualEvidenceContract(
        scene_id=scene_id,
        subject=subject,
        subject_type="focal_explanation",
        entities=[hero_term, sub_term],
        relationship="focal_inspection",
        action=f"inspecting {hero_term} architecture",
        environment=f"{domain.value} facility",
        composition_intent="focal_explanation",
        character_intent="guide_focus",
        interaction_target_id="focal_hero",
        required_visual_evidence=[hero_term, sub_term],
        forbidden_visuals=["template cards"],
    )
    return SemanticSceneGraph(
        scene_id=scene_id,
        topic_domain=domain.value,
        central_subject=f"{hero_term} Focal Explanation",
        narrative_role=narrative_role,
        topology="focal",
        nodes=[hero_node],
        edges=[],
        primary_anchor=(540.0, 705.0),
        required_visual_evidence=[hero_term, sub_term],
        evidence_contract=contract,
    )
