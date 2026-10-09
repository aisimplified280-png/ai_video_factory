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


_STOPWORDS: set[str] = {
    "this", "that", "with", "from", "have", "more", "then", "into", "when",
    "your", "will", "what", "how", "over", "fast", "they", "them", "about",
    "offers", "gives", "system", "systems", "getting", "smarter", "built",
    "dark", "minimalist", "studio", "obsidian", "matrix", "wireframe",
    "graphic", "visual", "concept", "slide", "scene", "clean", "just",
    "happened", "unprecedented", "today", "daily", "frontier", "does", "actually",
    "thin", "only", "entirely", "across", "within", "beyond", "under", "hood",
    "using", "where", "which", "being", "been", "each", "both", "such",
    # Conjunctions / glue words are never meaningful visual labels
    "and", "are", "was", "were", "not", "has", "its", "can", "may",
    "all", "any", "one", "two", "new", "also", "than", "while", "some",
    "very", "much", "most", "like", "still", "even", "make", "made", "get",
    # Pronouns & quantifiers name no visual concept
    "those", "these", "their", "there", "them", "another", "others", "several",
    "smaller", "larger", "bigger", "various", "multiple", "different",
    "current", "previous", "second", "third", "every", "nothing", "everything",
}


def _clean_entity_terms(text: str, domain: TopicDomain) -> list[str]:
    """Extract clean entity nouns and technical terms from text without noise."""
    tokens = re.findall(r"[A-Za-z0-9\-_]{3,}", text)
    stopwords = _STOPWORDS
    clean_terms: list[str] = []
    seen: set[str] = set()
    for tok in tokens:
        up = tok.upper()
        if up.lower() not in stopwords and up not in seen and len(up) >= 3:
            seen.add(up)
            clean_terms.append(up)
    return clean_terms


def _trim_clause_to_limit(clause: str, hi: int = 48) -> str:
    """Cut a long clause on a word boundary within `hi`, dropping stranded glue words."""
    kept: list[str] = []
    for w in clause.split():
        if len(" ".join(kept + [w])) > hi:
            break
        kept.append(w)
    glue = {
        "a", "an", "the", "of", "to", "and", "or", "in", "on", "at", "for",
        "with", "that", "which", "while", "each", "every", "is", "are", "as",
        "into", "from", "by", "without", "through", "across", "around",
    }
    while kept and kept[-1].strip("?!:;,.\"'“”‘’").lower() in glue:
        kept.pop()
    return " ".join(kept).strip()


def _extract_real_phrases_from_speech(speech: str, max_phrases: int = 2) -> list[str]:
    """Extract genuine factual snippets directly from spoken text with zero hallucinated boilerplate."""
    clauses = re.split(
        r"[,;.?!:]|(?:\s+and\s+)|\b(?:while|unlike|which|that|to)\b",
        speech,
        flags=re.IGNORECASE,
    )
    clean_clauses: list[str] = []
    for c in clauses:
        c_str = c.strip()
        # Clean leading prepositions and trailing punctuation
        c_str = re.sub(r"^(that|into|with|from|by|at|for|the|a|an)\s+", "", c_str, flags=re.IGNORECASE)
        c_str = c_str.strip("?!:;,\"'“”‘’").strip()
        if not c_str:
            continue
        if len(c_str) > 48:
            # Never discard a real sentence — trim it to the card limit instead
            # (empty cards are a worse sin than a slightly shortened phrase).
            c_str = _trim_clause_to_limit(c_str)
        if 8 <= len(c_str) <= 48:
            # Title case short phrase
            clean_clauses.append(c_str.capitalize())
        if len(clean_clauses) >= max_phrases:
            break
    return clean_clauses


def _narrative_label_pool(subject: str, speech: str, topic: str) -> list[str]:
    """Ordered pool of node labels derived strictly from what the narrator actually says.

    Subject words come first (they name the scene's subject), then spoken content words,
    then topic words. Generic technical words ("STAGE 1", "PIPELINE", "ENGINE") are never
    invented: if the narration does not name it, the node does not either.
    """
    pool: list[str] = []
    for src in (subject, speech, topic):
        for word in re.findall(r"[A-Za-z0-9\-_]{3,}", str(src or "")):
            up = word.upper()
            if up.lower() in _STOPWORDS or up in pool:
                continue
            pool.append(up)
    return pool


def _clip_words(text: str, limit: int) -> str:
    """Cut on a word boundary with an ellipsis — labels never break mid-word (§21)."""
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0].rstrip()
    return (cut or text[:limit]) + "…"


def _label_at(pool: list[str], idx: int, subject: str) -> str:
    """Label for the idx-th node, or the narration subject when the pool is exhausted."""
    if idx < len(pool):
        return pool[idx]
    subj = re.sub(r"[^\w\s-]", "", subject or "").strip().upper()
    return _clip_words(subj, 40)


def _content_words(text: str, limit: int | None = None) -> list[str]:
    """Meaningful narration words (glue words and quantifiers removed), in spoken order."""
    out: list[str] = []
    for word in re.findall(r"[A-Za-z][A-Za-z'\-]{2,}", text or ""):
        if word.lower() in _STOPWORDS:
            continue
        up = word.upper()
        if up not in out:
            out.append(up)
        if limit is not None and len(out) >= limit:
            break
    return out


def _transformation_labels(speech: str) -> Optional[tuple[str, str, str]]:
    """Read an actual transformation out of the narration: "<source> <action> into <result>".

    Example: "Documents are split into several smaller chunks."
      -> ("DOCUMENTS", "SPLIT", "CHUNKS")
    Returns None when the narration does not phrase a transformation this way, so the caller
    can fall back to the subject-word pool instead of inventing labels.
    """
    speech_lower = (speech or "").lower()
    conn = re.search(r"\s(into|to|as)\s", speech_lower)
    if not conn:
        return None
    left = (speech or "")[: conn.start()]
    right = (speech or "")[conn.end():]

    left_words = _content_words(left)
    dst_words = _content_words(right, limit=2)
    # The final word of the left side is the action; everything before it names the source.
    if len(left_words) < 2 or not dst_words:
        return None
    action = left_words[-1]
    src_words = left_words[:-1][:2]
    return " ".join(src_words), action, " ".join(dst_words)


_ACTION_STEMS: tuple[str, ...] = (
    "parse", "chunk", "split", "convert", "embed", "token", "store", "index",
    "retriev", "fetch", "rank", "route", "connect", "generat", "train", "infer",
    "decode", "encode", "extract", "load", "stream", "deploy", "monitor",
    "verif", "valid", "launch", "scale", "optimi", "search", "learn", "predict",
)


def _action_clauses(speech: str) -> list[str]:
    """Narration clauses that describe something actually happening."""
    clauses = re.split(
        r"[,;.]|\b(?:and|then|while|before|after|until|finally|next)\b",
        (speech or "").lower(),
    )
    return [c.strip() for c in clauses if len(c.strip()) > 3 and any(k in c for k in _ACTION_STEMS)]


def _action_clause_count(speech: str) -> int:
    """Whether the narration describes a multi-step process (>= 2 action clauses).

    Used to decide whether the narration describes a multi-step process (draw a flow)
    or one single concept (draw one clear object instead of filler boxes).
    """
    return len(_action_clauses(speech))


def _action_clause_labels(speech: str, limit: int = 3) -> list[str]:
    """One node label per narrated step — literally the action the narrator names.

    "Documents are chunked, embedded, and stored in an index."
      -> ["CHUNKED", "EMBEDDED", "STORED"]
    """
    labels: list[str] = []
    for clause in _action_clauses(speech):
        stem = next((k for k in _ACTION_STEMS if k in clause), None)
        words = _content_words(clause)
        if not words:
            continue
        match = next((w for w in words if stem and stem in w.lower()), words[0])
        if match not in labels:
            labels.append(match)
        if len(labels) >= limit:
            break
    return labels


def _contrast_labels(subject: str, speech: str) -> Optional[tuple[str, str]]:
    """Read the two compared sides out of the narration instead of guessing them.

    "Keyword Search vs Semantic Retrieval" / "Unlike keyword search, semantic retrieval..."
      -> ("KEYWORD SEARCH", "SEMANTIC RETRIEVAL")
    """
    for marker in (r"\bvs\.?\b", r"\bversus\b", r"\bagainst\b"):
        m = re.search(marker, subject or "", flags=re.IGNORECASE)
        if m:
            left = re.sub(r"[^\w\s-]", " ", (subject or "")[: m.start()]).strip()
            right = re.sub(r"[^\w\s-]", " ", (subject or "")[m.end():]).strip()
            if left and right:
                return _clip_words(left.upper(), 28), _clip_words(right.upper(), 28)

    speech_lower = (speech or "").lower()
    for marker in (r"\bunlike\b", r"\binstead of\b", r"\bversus\b", r"\bvs\b"):
        m = re.search(marker, speech_lower)
        if not m:
            continue
        left_clause = (speech or "")[: m.start()]
        right_clause = re.split(r"[,;.]", (speech or "")[m.end():])[0]
        left_words = _content_words(left_clause, limit=2)
        right_words = _content_words(right_clause, limit=2)
        if left_words and right_words:
            return " ".join(left_words), " ".join(right_words)
    return None


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
    # Every node label must be traceable to the narration (subject -> speech -> topic).
    label_pool = _narrative_label_pool(subject, speech, topic)

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
            details=real_facts[:1],  # spoken CTA copy only — never an invented claim
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
            required_visual_evidence=["AI SIMPLIFIED LAB"],
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
    if is_stack and len(label_pool) >= 3:
        top_label = label_pool[0]
        mid_label = label_pool[1]
        bot_label = label_pool[2]

        node_top = SceneNode(
            id="stack_top",
            label=top_label,
            node_type=SceneNodeType.ENTITY,
            details=[real_facts[0]] if real_facts else [],
            bounds=(180, 510, 900, 610),
            is_primary=False,
            shape_style="stack_layer",
        )
        node_mid = SceneNode(
            id="stack_core",
            label=mid_label,
            node_type=SceneNodeType.TRANSFORM,
            details=[real_facts[1]] if len(real_facts) > 1 else [],
            bounds=(140, 630, 940, 770),
            is_primary=True,
            shape_style="matrix_grid",
        )
        node_bot = SceneNode(
            id="stack_base",
            label=bot_label,
            node_type=SceneNodeType.ENTITY,
            details=[real_facts[2]] if len(real_facts) > 2 else [],
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
    # A transformation must be stated by the narration: either a strong transform verb, or a
    # weak one ("split", "chunk") paired with an explicit "<source> <action> into <result>" phrase.
    strong_transform = any(k in combined_ctx for k in ["convert", "vector embedding", "tokenized", "parse", "diffusion", "denois", "reverse gaussian", "synthesize entirely novel"]) or ("transform" in combined_ctx and "transformer" not in combined_ctx)
    weak_transform = any(k in combined_ctx for k in ["split", "chunk", "divid", "shard"])
    transform_labels = _transformation_labels(speech) if (strong_transform or weak_transform) else None
    is_transform = (strong_transform or (weak_transform and transform_labels is not None)) and (
        transform_labels is not None or len(label_pool) >= 3
    )
    if is_transform:
        if transform_labels:
            src_label, trn_label, dst_label = transform_labels
        else:
            src_label, trn_label, dst_label = label_pool[0], label_pool[1], label_pool[2]

        node_src = SceneNode(
            id="transform_source",
            label=src_label,
            node_type=SceneNodeType.STORAGE,
            details=[real_facts[0]] if real_facts else [],
            bounds=(140, 590, 380, 830),
            is_primary=False,
            shape_style="card",
        )
        node_trn = SceneNode(
            id="transform_kernel",
            label=trn_label,
            node_type=SceneNodeType.TRANSFORM,
            details=[real_facts[1]] if len(real_facts) > 1 else [],
            bounds=(420, 550, 660, 870),
            is_primary=True,
            shape_style="transform_kernel",
        )
        node_dst = SceneNode(
            id="transform_result",
            label=dst_label,
            node_type=SceneNodeType.ENTITY,
            details=[real_facts[2]] if len(real_facts) > 2 else [],
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
    is_contrast = any(k in speech_lower for k in ["unlike", "instead of", "versus", "vs", "classif", "balance"]) or bool(re.search(r"\bvs\.?\b|\bversus\b", subject or "", flags=re.IGNORECASE))
    contrast_labels = _contrast_labels(subject, speech) if is_contrast else None
    if is_contrast and (contrast_labels or len(label_pool) >= 2):
        if contrast_labels:
            left_label, right_label = contrast_labels
        else:
            left_label, right_label = label_pool[0], label_pool[1]

        node_left = SceneNode(
            id="contrast_left",
            label=left_label,
            node_type=SceneNodeType.ENTITY,
            details=[real_facts[0]] if real_facts else [],
            bounds=(150, 560, 500, 860),
            is_primary=False,
            shape_style="card",
        )
        node_right = SceneNode(
            id="contrast_right",
            label=right_label,
            node_type=SceneNodeType.ENTITY,
            details=[real_facts[1]] if len(real_facts) > 1 else [],
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

    # 5. PROCESS FLOW TOPOLOGY (only when the narration describes a multi-step process)
    # A flow diagram is never drawn just to fill space: it requires narration with at least two
    # clauses describing action, and its node count never exceeds the concepts the narration names.
    if len(label_pool) >= 2 and _action_clause_count(speech) >= 2:
        # Node labels are the steps the narrator actually names.
        flow_labels = _action_clause_labels(speech)
        if len(flow_labels) < 2:
            flow_labels = [_label_at(label_pool, i, subject) for i in range(min(3, len(label_pool)))]
        n_entities = max(2, min(3, len(flow_labels)))
        margin = 130
        total_w = 1080 - 2 * margin
        spacing = 28
        box_w = (total_w - (n_entities - 1) * spacing) // n_entities

        flow_nodes: list[SceneNode] = []
        flow_edges: list[SceneEdge] = []
        for i in range(n_entities):
            bx1 = margin + i * (box_w + spacing)
            bx2 = bx1 + box_w
            lbl = flow_labels[i]
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

    # 6. FOCAL EXPLANATION TOPOLOGY (One clear subject, sized to the narration — no filler nodes)
    hero_label = (subject or topic or (label_pool[0] if label_pool else "")).strip().upper()
    hero_label = _clip_words(re.sub(r"[^\w\s/&-]", "", hero_label).strip(), 70)

    hero_node = SceneNode(
        id="focal_hero",
        label=hero_label,
        node_type=SceneNodeType.ENTITY,
        details=real_facts,
        bounds=(200, 550, 880, 860),
        is_primary=True,
        shape_style="card",
    )
    contract = VisualEvidenceContract(
        scene_id=scene_id,
        subject=subject,
        subject_type="focal_explanation",
        entities=[hero_label],
        relationship="focal_inspection",
        action=f"inspecting {hero_label.lower()}",
        environment=f"{domain.value} facility",
        composition_intent="focal_explanation",
        character_intent="guide_focus",
        interaction_target_id="focal_hero",
        required_visual_evidence=[hero_label],
        forbidden_visuals=["template cards"],
    )
    return SemanticSceneGraph(
        scene_id=scene_id,
        topic_domain=domain.value,
        central_subject=hero_label,
        narrative_role=narrative_role,
        topology="focal",
        nodes=[hero_node],
        edges=[],
        primary_anchor=(540.0, 705.0),
        required_visual_evidence=[hero_label],
        evidence_contract=contract,
    )
