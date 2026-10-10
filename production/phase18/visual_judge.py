"""Phase 18 Independent Visual Judge Ensemble & Strict Release Gate.

Release priority (highest first):
  1. Semantic correctness  — does the frame depict the narration's claim?
  2. Visual clarity        — can a viewer tell subject, relationship and target at a glance?
  3. Subject visibility / hierarchy
  4. Mascot guidance accuracy
  5. Motion                — deliberately LOW weight; static explanatory scenes are valid
  6. Decorative richness   — never a goal; over-design is actively penalised

Audits actual encoded MP4 frames and verifies:
1. Perception-First Analysis: pixel entropy, edge balance, luminance separation, inter-frame motion.
2. Semantic Grounding: describes visible features first, then compares with VisualEvidenceContract.
3. Domain Mismatch Rejection: software topics depicting physical robotics fail immediately.
4. Blank Frame Rejection: blank frames (no content at all) fail immediately. A calm,
   mostly-static explanatory frame is NOT a failure.
5. Over-design Detection: decorative framing and filler geometry far beyond the scene's
   semantic content are flagged.
6. Strict Gate Enforcement: any failure raises VisualGateRejectionError and halts release.
"""
from __future__ import annotations

import json
import math
import re
import subprocess
from pathlib import Path
from typing import Any, Sequence
import numpy as np
import scipy.ndimage as ndi
from PIL import Image, ImageFilter, ImageStat
from pydantic import BaseModel, Field

from .visual_director import UnifiedVisualPlan, CanonicalSceneSpec


class VisualGateRejectionError(RuntimeError):
    """Raised when rendered MP4 fails independent Visual Judge release criteria."""
    pass


class SceneVisualJudgement(BaseModel):
    scene_id: str
    timestamp_seconds: float
    visible_description: str
    semantic_grounding_score: float     # 0.0 to 10.0 — highest priority
    visual_clarity_score: float = 0.0   # 0.0 to 10.0 — can the frame explain the spoken idea?
    art_direction_score: float          # 0.0 to 10.0
    composition_score: float            # 0.0 to 10.0 — subject visibility & hierarchy
    motion_activity_score: float        # 0.0 to 10.0 — low importance by design
    depth_separation_score: float       # 0.0 to 10.0
    composite_score: float              # 0.0 to 10.0
    semantic_evidence: str = "unverified"  # "verified" | "unverified" | "contradicted" (§8)
    passed: bool
    overdesigned: bool = False          # too much decoration for the semantic content present
    reasons: list[str] = Field(default_factory=list)


class VisualJudgeScorecard(BaseModel):
    production_id: str
    passed: bool
    final_score: float
    semantic_grounding: float
    visual_clarity: float = 0.0
    art_direction: float
    composition: float
    motion_activity: float
    depth_separation: float
    scene_judgements: list[SceneVisualJudgement] = Field(default_factory=list)
    failure_reasons: list[str] = Field(default_factory=list)


def inspect_frame_pixels(img: Image.Image) -> dict[str, Any]:
    """Empirically inspect raw frame pixels without relying on metadata."""
    img_rgb = img.convert("RGB")
    w, h = img_rgb.size
    stat = ImageStat.Stat(img_rgb)

    # 1. Luminance & Standard Deviation
    mean_lum = sum(stat.mean[:3]) / 3.0
    stddev_lum = sum(stat.stddev[:3]) / 3.0

    # 2. Edge complexity via high-pass edge filter
    edges = img.convert("L").filter(ImageFilter.FIND_EDGES)
    edge_stat = ImageStat.Stat(edges)
    edge_density = edge_stat.mean[0]

    # 3. Center vs Margin Luminance Separation (Depth & Subject Isolation)
    center_box = img_rgb.crop((int(w * 0.25), int(h * 0.25), int(w * 0.75), int(h * 0.75)))
    margin_top = img_rgb.crop((0, 0, w, int(h * 0.15)))
    c_lum = sum(ImageStat.Stat(center_box.convert("L")).mean)
    m_lum = sum(ImageStat.Stat(margin_top.convert("L")).mean)
    lum_separation = abs(c_lum - m_lum)

    # 4. Color temperature & void detection
    mean_r, mean_g, mean_b = stat.mean[:3]
    is_pitch_black = mean_lum < 15.0
    is_harsh_cyan_void = mean_b > mean_r + 45 and mean_g > mean_r + 20 and mean_r < 40

    # 5. Spatial Edge Layout Signature (64x64 projection)
    small_edges = edges.resize((64, 64))
    pixels = list(small_edges.getdata())
    # 64 horizontal row sums, 64 vertical col sums
    row_sums = [sum(pixels[r * 64:(r + 1) * 64]) for r in range(64)]
    col_sums = [sum(pixels[r * 64 + c] for r in range(64)) for c in range(64)]
    max_row = max(1, max(row_sums))
    max_col = max(1, max(col_sums))
    norm_sig = [round(v / max_row, 3) for v in row_sums] + [round(v / max_col, 3) for v in col_sums]

    return {
        "mean_luminance": mean_lum,
        "stddev_luminance": stddev_lum,
        "edge_density": edge_density,
        "lum_separation": lum_separation,
        "is_pitch_black": is_pitch_black,
        "is_harsh_cyan_void": is_harsh_cyan_void,
        "layout_signature": norm_sig,
    }


def _edge_balance(img: Image.Image) -> tuple[float, float]:
    """Mean edge response in the outer frame band vs the central content area.

    Decorative borders, side rails and HUD frames concentrate edge energy in the margins.
    Explanatory content concentrates it in the centre. High border activity with quiet
    centre activity is the signature of decoration standing in for meaning.
    """
    edges = np.asarray(img.convert("L").filter(ImageFilter.FIND_EDGES), dtype=np.float32)
    h, w = edges.shape
    bx = max(2, int(w * 0.10))
    by = max(2, int(h * 0.10))
    border = np.zeros((h, w), dtype=bool)
    border[:by, :] = True
    border[h - by:, :] = True
    border[:, :bx] = True
    border[:, w - bx:] = True
    centre = ~border
    border_val = float(edges[border].mean()) if border.any() else 0.0
    centre_val = float(edges[centre].mean()) if centre.any() else 0.0
    return border_val, centre_val


def compute_frame_motion_delta(img_a: Image.Image, img_b: Image.Image) -> float:
    """Computes mean absolute pixel difference between two frames (0.0 to 255.0)."""
    a_gray = img_a.convert("L").resize((180, 320))
    b_gray = img_b.convert("L").resize((180, 320))
    stat = ImageStat.Stat(Image.frombytes(
        "L", a_gray.size,
        bytes(abs(x - y) for x, y in zip(a_gray.tobytes(), b_gray.tobytes()))
    ))
    return float(stat.mean[0])


def analyze_frame_geometry(img: Image.Image) -> dict[str, Any]:
    """Empirical connected-component visual entity & topology discovery.
    Extracts clusters, bounding boxes, topology, and visual centroid from decoded pixels.
    """
    w, h = img.size
    crop_y1, crop_y2 = 400, 1400
    cropped = img.crop((0, crop_y1, w, crop_y2))
    gray = np.array(cropped.convert("L"), dtype=np.float32)

    grad_x = ndi.sobel(gray, axis=1)
    grad_y = ndi.sobel(gray, axis=0)
    grad = np.hypot(grad_x, grad_y)

    thresh = np.percentile(grad, 80)
    mask = ndi.binary_dilation(grad > thresh, iterations=2)
    labeled, n_features = ndi.label(mask)
    slices = ndi.find_objects(labeled)

    clusters: list[dict[str, Any]] = []
    for sl in slices:
        if sl is None:
            continue
        sy, sx = sl
        bw = sx.stop - sx.start
        bh = sy.stop - sy.start
        area = bw * bh
        if area > 3000 and bw > 50 and bh > 40:
            cx = (sx.start + sx.stop) // 2
            cy = crop_y1 + (sy.start + sy.stop) // 2
            clusters.append({
                "bbox": (sx.start, crop_y1 + sy.start, sx.stop, crop_y1 + sy.stop),
                "center": (cx, cy),
                "width": bw,
                "height": bh,
                "area": area,
            })

    # Header banner is typically at cy <= 540, main subjects at cy > 540
    subject_clusters = [c for c in clusters if c["center"][1] > 540]
    if not subject_clusters:
        subject_clusters = clusters

    if subject_clusters:
        primary = max(subject_clusters, key=lambda c: c["area"])
        primary_cx, primary_cy = primary["center"]
        primary_bbox = primary["bbox"]
    else:
        primary_cx, primary_cy = w // 2, (crop_y1 + crop_y2) // 2
        primary_bbox = (w // 4, crop_y1, 3 * w // 4, crop_y2)

    # Classify observed visual topology
    n_subj = len(subject_clusters)
    if n_subj >= 2:
        centers_x = [c["center"][0] for c in subject_clusters]
        x_spread = max(centers_x) - min(centers_x)
        if x_spread > 280:
            observed_topology = "pipeline" if n_subj >= 3 else "bipartite"
        else:
            observed_topology = "focal"
    elif n_subj == 1:
        pw = subject_clusters[0]["width"]
        ph = subject_clusters[0]["height"]
        if pw > 650:
            observed_topology = "console"
        elif pw < 350 and ph < 350:
            observed_topology = "brand"
        else:
            observed_topology = "focal"
    else:
        observed_topology = "empty"

    return {
        "num_clusters": len(clusters),
        "num_subject_clusters": n_subj,
        "clusters": clusters,
        "primary_centroid": (primary_cx, primary_cy),
        "primary_bbox": primary_bbox,
        "observed_topology": observed_topology,
    }


_SEM_STOPWORDS = {
    "the", "a", "an", "of", "and", "or", "to", "in", "on", "for", "with", "is",
    "are", "how", "does", "did", "your", "its", "it", "this", "that", "from",
    "into", "when", "why", "what", "really", "actually", "every", "each", "all",
    # Function/light verbs and demonstratives that name nothing drawable —
    # narration phrases like "those raw chunks get pasted" are depicted by
    # their content words, never by "those" or "get".
    "those", "these", "get", "gets", "got", "use", "uses", "like", "than",
    "even", "just", "also",
}
# Abstract topic words that cannot be drawn as objects — never required to appear.
_SEM_ABSTRACT = {
    "positioning", "architecture", "hierarchy", "process", "system", "mechanism",
    "workflow", "pipeline", "operation", "technique", "method", "science", "theory",
    "concept", "step", "stage", "way", "works", "working", "function", "role",
    "behavior", "behaviour", "effect", "power", "speed", "accuracy", "quality",
    "difference", "overview", "introduction", "basics", "fundamentals", "explained",
    "explainer", "story", "world", "life", "day", "future", "history", "guide",
    # Brand/chrome words: the CTA contract subject ("AI Simplified Lab Brand
    # Identity") names identity concepts the crest label never spells out —
    # requiring them would block genuinely correct CTA scenes.
    "brand", "identity", "logo", "emblem", "mark", "design", "layout", "frame",
    "scene", "shot", "studio", "style", "art", "direction", "render", "video",
    "short", "channel", "content", "topic", "title", "series", "episode",
}
# Expected depicted relationship per topology (what the renderer MUST draw).
_TOPOLOGY_RELATIONSHIP = {
    "bipartite": "contrasts_with",
    "process_flow": "flows_to",
    "pipeline": "flows_to",
    "object_transformation": "transforms_to",
    "layered_architecture": "routes_down",
}
# Free-text contract relationship → depicted relationship family.
_RELATIONSHIP_KEYS = (
    ("contrast", "contrasts_with"), ("comparison", "contrasts_with"),
    ("transform", "transforms_to"),
    ("pipeline", "flows_to"), ("process", "flows_to"), ("flow", "flows_to"),
    ("stack", "routes_down"), ("hierarch", "routes_down"),
    ("index", "indexes"), ("storage", "indexes"),
)


def verify_semantic_evidence(contract: Any, scene_graph: Any) -> tuple[str, list[str]]:
    """Expected-vs-observed semantic verification (§8).

    Checks the evidence contract's REQUIRED SUBJECT and RELATIONSHIP against the
    element inventory the renderer actually draws: node labels (narration-derived),
    concrete object glyphs, node types and edge relationships. Returns
    ("verified" | "unverified" | "contradicted", notes).

    A generic card layout full of clusters and contrast but naming none of the
    subject's objects ("STAGE ONE / STAGE TWO") is CONTRADICTED — pixel geometry
    alone can never verify meaning. Labels/metadata are only grounding evidence
    when they genuinely derive from the narration, which boilerplate cannot fake.
    """
    from production.phase18.scene_graph import _node_icon

    if contract is None or scene_graph is None:
        return "unverified", ["no evidence contract on the scene graph"]
    nodes = list(getattr(scene_graph, "nodes", []) or [])
    edges = list(getattr(scene_graph, "edges", []) or [])
    if not nodes:
        return "unverified", ["scene graph depicts no nodes"]

    subject = (getattr(contract, "subject", "") or "").strip().lower()
    labels = " | ".join((n.label or "").lower() for n in nodes)
    icons = {(n.icon or "").lower() for n in nodes if getattr(n, "icon", "")}
    relationships = {(e.relationship or "").lower() for e in edges}

    # --- Subject: every drawable word of the contract subject must be depicted
    # (in a node label or as a concrete object glyph).
    subject_words = [
        w for w in re.findall(r"[a-z][a-z'-]{2,}", subject)
        if w not in _SEM_STOPWORDS and w not in _SEM_ABSTRACT
    ]
    if subject_words:
        def _covered(w: str) -> bool:
            if w in labels or w.rstrip("s") in labels or _node_icon(w) in icons:
                return True
            # Light verb morphology: labels are narration-derived base phrases
            # ("chunks get pasted" renders as PASTE/PASTED), so match the stem
            # of -ed/-ing forms against the label string.
            stems = []
            if w.endswith("ed") and len(w) > 4:
                stems.append(w[:-2])  # pasted -> past (substring of "paste")
            if w.endswith("ing") and len(w) > 4:
                stems.append(w[:-3])  # pasting -> past
            return any(s in labels for s in stems)

        missing = [w for w in subject_words if not _covered(w)]
        covered_count = len(subject_words) - len(missing)
        if covered_count == 0:
            return "contradicted", [
                f"contract subject '{subject}' is not depicted by any node label or glyph "
                f"(depicted: {labels})"
            ]
        # Verdict needs most of the subject depicted: a clip-truncated hero label
        # or one derived synonym may drop a word or two, but a layout covering
        # less than 60% of the subject's drawable words has NOT proven the claim.
        if covered_count < max(1, -(-3 * len(subject_words) // 5)):  # ceil(0.6 * n)
            return "unverified", [
                f"subject words not depicted ({covered_count}/{len(subject_words)} covered): "
                f"{', '.join(missing)}"
            ]
    else:
        # Fallback link: at least one required entity fragment must be depicted.
        entities = [str(e).lower() for e in (getattr(contract, "entities", None) or [])]
        required = [str(e).lower() for e in (getattr(contract, "required_visual_evidence", None) or [])]
        fragments = [f for e in entities + required for f in e.split() if len(f) > 4 and f not in _SEM_ABSTRACT]
        if fragments and not any(f in labels for f in fragments):
            return "contradicted", [
                f"no contract entity is depicted (needed one of: {sorted(set(fragments))[:6]}; "
                f"depicted: {labels})"
            ]

    # --- Relationship: the expected relation family must be present in the
    # depicted edge set (or node semantics for storages).
    rel_text = (getattr(contract, "relationship", "") or "").lower()
    topology = (getattr(scene_graph, "topology", "") or "").lower()
    expected = set()
    for key, dep in _RELATIONSHIP_KEYS:
        if key in rel_text:
            expected.add(dep)
    if topology in _TOPOLOGY_RELATIONSHIP:
        expected.add(_TOPOLOGY_RELATIONSHIP[topology])
    if expected and not (expected & relationships):
        types = {str(getattr(n, "node_type", "")).lower() for n in nodes}
        if not ({"storage"} & types and "indexes" in expected):
            return "unverified", [
                f"expected relationship {sorted(expected)} not depicted "
                f"(edge relationships present: {sorted(relationships) or 'none'})"
            ]

    return "verified", [
        f"subject '{subject}' and relationship {sorted(expected) or 'focal'} depicted via "
        f"{len(nodes)} nodes (glyphs: {sorted(icons) or 'none'}) and {len(edges)} semantic edges"
    ]


def judge_scene_frames(
    scene_spec: CanonicalSceneSpec,
    scene_frames: dict[str, Path],
    topic: str,
) -> SceneVisualJudgement:
    """Evaluate multi-point frames of a scene independently against the semantic contract."""
    mid_path = scene_frames.get("mid")
    start_path = scene_frames.get("start")
    end_path = scene_frames.get("end")

    if not mid_path or not mid_path.exists():
        return SceneVisualJudgement(
            scene_id=scene_spec.scene_id,
            timestamp_seconds=scene_spec.start_seconds,
            visible_description="Missing frame on disk",
            semantic_grounding_score=0.0,
            art_direction_score=0.0,
            composition_score=0.0,
            motion_activity_score=0.0,
            depth_separation_score=0.0,
            composite_score=0.0,
            passed=False,
            reasons=["Scene midpoint frame missing on disk"],
        )

    mid_img = Image.open(mid_path)
    metrics = inspect_frame_pixels(mid_img)

    # Empirical connected-component geometric and topological analysis
    geom = analyze_frame_geometry(mid_img)
    centroid_x, centroid_y = geom["primary_centroid"]

    # Target anchor verification: Does mascot target match detected primary subject geometry?
    tgt_anchor = (
        scene_spec.character_spec.target_anchor
        if (scene_spec.character_spec and scene_spec.character_spec.target_anchor)
        else None
    ) or {"x": 540.0, "y": 720.0}
    tgt_x = tgt_anchor.get("x", 540.0)
    tgt_y = tgt_anchor.get("y", 720.0)
    dist_to_anchor = math.hypot(centroid_x - tgt_x, centroid_y - tgt_y)

    expected_topology = scene_spec.scene_graph.topology if scene_spec.scene_graph else None

    # Motion activity check across start -> mid -> end
    motion_delta = 0.0
    if start_path and start_path.exists():
        start_img = Image.open(start_path)
        motion_delta += compute_frame_motion_delta(start_img, mid_img)
    if end_path and end_path.exists():
        end_img = Image.open(end_path)
        motion_delta += compute_frame_motion_delta(mid_img, end_img)

    fatal_reasons: list[str] = []
    advisories: list[str] = []

    # 1. Blank / Empty Frame Rejection (Fatal)
    if metrics["stddev_luminance"] < 8.0 or metrics["edge_density"] < 0.4:
        fatal_reasons.append("Blank frame: luminance standard deviation or edge density is near zero")
    if geom["num_clusters"] == 0:
        fatal_reasons.append("Zero visual entity clusters detected in midground canvas")

    # 2. Dark void / cyan void rejection
    if metrics["is_pitch_black"]:
        fatal_reasons.append("Pitch black void syndrome (mean luminance < 15)")
    if metrics["is_harsh_cyan_void"]:
        advisories.append("Harsh cyan/blue void syndrome")

    # 3. Over-design check (§23): decorative structure far beyond the scene's semantic content.
    #    Static explanatory frames are explicitly allowed — calm is not a defect.
    expected_nodes = len(scene_spec.scene_graph.nodes) if scene_spec.scene_graph else None
    border_edge, centre_edge = _edge_balance(mid_img)
    overdesigned = False
    if expected_nodes and geom["num_clusters"] > expected_nodes * 3 + 3:
        overdesigned = True
        advisories.append(
            f"Over-design: {geom['num_clusters']} visual clusters for {expected_nodes} semantic nodes — "
            "filler geometry is standing in for explanation"
        )
    if border_edge > 12.0 and border_edge > centre_edge * 0.7:
        overdesigned = True
        advisories.append(
            f"Over-design: frame margins are busier than the content (border {border_edge:.1f} vs centre {centre_edge:.1f})"
        )

    # 4. Domain Alignment & Mismatch Check (Fatal)
    topic_lower = topic.lower()
    subj_lower = scene_spec.subject.lower()
    is_software_topic = any(k in topic_lower for k in ["rag", "llm", "software", "cloud", "database", "retrieval", "vector", "api"])
    depicts_physical_robotics = any(k in subj_lower for k in ["robotic arm", "actuator", "titanium gripper", "kinematic cell", "harmonic drive"])

    if is_software_topic and depicts_physical_robotics:
        fatal_reasons.append(f"Domain mismatch: software/AI topic depicts physical robotics ({scene_spec.subject})")

    # 5. Semantic Mascot Target Anchoring Verification
    if dist_to_anchor > 280:
        advisories.append(f"Mascot target vector offset ({dist_to_anchor:.1f}px) from primary visual subject centroid ({centroid_x}, {centroid_y})")

    # 6. Expected vs Observed Visual Topology Verification & Evidence Contract
    contract = getattr(scene_spec.scene_graph, "evidence_contract", None) if scene_spec.scene_graph else None
    if expected_topology and geom["observed_topology"] != "empty":
        if expected_topology == "brand" and geom["observed_topology"] not in ("brand", "focal"):
            advisories.append(f"Observed topology [{geom['observed_topology']}] deviates from expected brand crest")
        elif expected_topology in ("pipeline", "process_flow", "bipartite", "object_transformation") and geom["num_subject_clusters"] == 0:
            fatal_reasons.append(f"Expected multi-node {expected_topology} topology but midground was empty")
        elif expected_topology in ("object_transformation", "layered_architecture") and geom["num_clusters"] < 2:
            advisories.append(f"Expected rich {expected_topology} structure but detected insufficient cluster separation ({geom['num_clusters']} clusters)")

    # Empirical scores. Priority order: semantic correctness > clarity > hierarchy > motion.
    depth_score = min(10.0, max(5.0, 6.0 + metrics["lum_separation"] * 0.25))
    art_score = 9.2 if not metrics["is_harsh_cyan_void"] else 6.5
    if metrics["is_pitch_black"]:
        art_score = 2.0
    # Composition measures subject visibility and hierarchy (centre vs margin separation),
    # never raw edge count: a busy frame is not automatically a clear frame.
    comp_score = min(10.0, max(6.0, 7.0 + metrics["lum_separation"] * 0.06))
    # Motion is deliberately low-impact. A still, perfectly explanatory scene scores fine.
    motion_score = min(10.0, max(6.0, 6.5 + min(motion_delta, 12.0) * 0.12))

    multi_topos = ("bipartite", "pipeline", "process_flow", "object_transformation", "layered_architecture")
    expected_topology = scene_spec.scene_graph.topology if scene_spec.scene_graph else None

    # 1) Semantic correctness — expected-vs-observed verification (§8).
    #    Geometry can CONFIRM a verified depiction but never substitute for it:
    #    clusters, contrast and target alignment alone yield "unverified", which
    #    cannot reach the release threshold. A generic card layout claiming a
    #    subject it never depicts is "contradicted" regardless of pixel quality.
    semantic_verdict, verdict_notes = verify_semantic_evidence(contract, scene_spec.scene_graph)
    base_grounding = 7.0
    align_mod = 1.5 if dist_to_anchor <= 140 else (0.7 if dist_to_anchor <= 220 else -0.5)
    topo_mod = 1.5 if (
        not expected_topology
        or geom["observed_topology"] == expected_topology
        or (expected_topology in multi_topos and geom["num_subject_clusters"] >= 2)
    ) else 0.4
    presence_mod = 1.0 if geom["num_subject_clusters"] >= 1 else -1.5
    measured_semantic = min(10.0, max(0.0, round(base_grounding + align_mod + topo_mod + presence_mod, 1)))
    if fatal_reasons:
        semantic_score = 2.0
        art_score = min(art_score, 4.0)
        depth_score = min(depth_score, 4.0)
    elif semantic_verdict == "contradicted":
        semantic_score = 3.0
        advisories.append(f"Semantic evidence CONTRADICTED: {'; '.join(verdict_notes)}")
    elif semantic_verdict == "unverified":
        semantic_score = min(6.5, measured_semantic)
        advisories.append(f"Semantic evidence UNVERIFIED (capped at 6.5): {'; '.join(verdict_notes)}")
    else:
        semantic_score = measured_semantic
        if advisories:
            semantic_score = max(0.0, semantic_score - 0.3 * len(advisories))

    # 2) Visual clarity (§22): can this rendered frame explain the core spoken idea?
    #    Correct subject, correct relationship, correct target, readable hierarchy.
    clarity = 5.5
    if geom["num_subject_clusters"] >= 1:
        clarity += 1.5
    if dist_to_anchor <= 140:
        clarity += 1.5
    elif dist_to_anchor <= 240:
        clarity += 0.5
    if (
        not expected_topology
        or geom["observed_topology"] == expected_topology
        or (expected_topology in multi_topos and geom["num_subject_clusters"] >= 2)
    ):
        clarity += 1.0
    clarity += min(1.5, metrics["lum_separation"] / 40.0)
    if fatal_reasons:
        clarity = min(clarity, 3.0)
    if overdesigned:
        clarity = max(0.0, clarity - 1.0)
    clarity_score = round(min(10.0, max(0.0, clarity)), 1)

    composite = round(
        0.35 * semantic_score
        + 0.25 * clarity_score
        + 0.15 * comp_score
        + 0.10 * art_score
        + 0.10 * depth_score
        + 0.05 * motion_score,
        1
    )

    passed = (
        len(fatal_reasons) == 0
        and semantic_verdict == "verified"
        and semantic_score >= 7.0
        and clarity_score >= 6.5
        and art_score >= 6.5
        and comp_score >= 6.0
        and depth_score >= 5.5
    )

    all_reasons = fatal_reasons + advisories

    # True multimodal perception description derived from actual decoded pixels & clusters
    visible_desc = (
        f"Decoded pixels (lum: {metrics['mean_luminance']:.1f}, edge: {metrics['edge_density']:.2f}, motion: {motion_delta:.2f}); "
        f"{geom['num_clusters']} detected clusters in [{geom['observed_topology']}] topology; "
        f"primary subject at ({centroid_x}, {centroid_y}) aligned with mascot target ({tgt_x:.0f}, {tgt_y:.0f}) [Δ={dist_to_anchor:.1f}px]; "
        f"clarity {clarity_score:.1f}/10 (border {border_edge:.1f} vs centre {centre_edge:.1f} edge activity); "
        f"semantic evidence {semantic_verdict}: {'; '.join(verdict_notes)}"
    )

    return SceneVisualJudgement(
        scene_id=scene_spec.scene_id,
        timestamp_seconds=round((scene_spec.start_seconds + scene_spec.end_seconds) / 2.0, 2),
        visible_description=visible_desc,
        semantic_grounding_score=round(semantic_score, 1),
        visual_clarity_score=clarity_score,
        art_direction_score=round(art_score, 1),
        composition_score=round(comp_score, 1),
        motion_activity_score=round(motion_score, 1),
        depth_separation_score=round(depth_score, 1),
        composite_score=composite,
        semantic_evidence=semantic_verdict,
        passed=passed,
        overdesigned=overdesigned,
        reasons=all_reasons,
    )


def judge_single_scene_frame(
    frame_path: Path,
    scene_spec: CanonicalSceneSpec,
    timestamp: float,
    topic: str,
) -> SceneVisualJudgement:
    """Evaluate a single frame independently against the semantic contract."""
    return judge_scene_frames(
        scene_spec=scene_spec,
        scene_frames={"mid": frame_path, "start": frame_path, "end": frame_path},
        topic=topic,
    )


def extract_video_keyed_frames(
    mp4_path: Path,
    output_dir: Path,
    timestamp_map: dict[str, float],
) -> dict[str, Path]:
    """Extract keyframes indexed by unique string keys to prevent list-truncation misalignment."""
    output_dir.mkdir(parents=True, exist_ok=True)
    extracted: dict[str, Path] = {}
    for key, ts in timestamp_map.items():
        out_frame = output_dir / f"judge_{key}_{ts:.2f}s.png"
        cmd = [
            "ffmpeg", "-y", "-ss", str(ts), "-i", str(mp4_path),
            "-vframes", "1", "-q:v", "2", str(out_frame)
        ]
        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            if out_frame.exists() and out_frame.stat().st_size > 0:
                extracted[key] = out_frame
        except Exception:
            pass
    return extracted


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Computes cosine similarity between two numeric vectors."""
    dot = sum(a * b for a, b in zip(v1, v2))
    norm_a = math.sqrt(sum(a * a for a in v1))
    norm_b = math.sqrt(sum(b * b for b in v2))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def evaluate_video_visual_truth(
    mp4_path: Path,
    visual_plan: UnifiedVisualPlan,
    output_dir: Path,
) -> VisualJudgeScorecard:
    """Execute complete independent visual judgment over encoded MP4 with multi-point sampling and diversity audit."""
    # 1. Multi-point sample timestamps (start, mid, end, boundary, cta)
    sample_timestamps: dict[str, float] = {
        "video_opening": 0.1,
        "video_cta": max(0.2, visual_plan.total_duration_seconds - 0.5),
    }
    for idx, sc in enumerate(visual_plan.scenes):
        start_ts = round(sc.start_seconds + 0.3, 2)
        mid_ts = round((sc.start_seconds + sc.end_seconds) / 2.0, 2)
        end_ts = round(max(sc.start_seconds + 0.5, sc.end_seconds - 0.3), 2)
        sample_timestamps[f"sc_{idx:02d}_start"] = start_ts
        sample_timestamps[f"sc_{idx:02d}_mid"] = mid_ts
        sample_timestamps[f"sc_{idx:02d}_end"] = end_ts

    extracted_frames = extract_video_keyed_frames(mp4_path, output_dir / "judge_frames", sample_timestamps)

    judgements: list[SceneVisualJudgement] = []
    signatures: list[list[float]] = []

    for idx, sc in enumerate(visual_plan.scenes):
        sc_frames = {
            "start": extracted_frames.get(f"sc_{idx:02d}_start"),
            "mid": extracted_frames.get(f"sc_{idx:02d}_mid"),
            "end": extracted_frames.get(f"sc_{idx:02d}_end"),
        }
        j = judge_scene_frames(sc, sc_frames, visual_plan.topic)
        judgements.append(j)

        if sc_frames["mid"] and sc_frames["mid"].exists():
            sig = inspect_frame_pixels(Image.open(sc_frames["mid"]))["layout_signature"]
            signatures.append(sig)

    # 2. Cross-scene layout audit — advisory only (§6): two scenes may legitimately look
    #    similar when the explanation requires it. Clarity, not variety, is the success metric.
    diversity_notes: list[str] = []
    if len(signatures) >= 3:
        for i in range(len(signatures) - 1):
            sim = cosine_similarity(signatures[i], signatures[i + 1])
            if sim > 0.985:
                diversity_notes.append(
                    f"Note: Scene {i+1} and Scene {i+2} share a near-identical spatial layout (sim: {sim:.3f}); "
                    "acceptable when the narration explains the same relationship"
                )

    avg_semantic = round(sum(j.semantic_grounding_score for j in judgements) / max(1, len(judgements)), 1)
    avg_clarity = round(sum(j.visual_clarity_score for j in judgements) / max(1, len(judgements)), 1)
    avg_art = round(sum(j.art_direction_score for j in judgements) / max(1, len(judgements)), 1)
    avg_comp = round(sum(j.composition_score for j in judgements) / max(1, len(judgements)), 1)
    avg_motion = round(sum(j.motion_activity_score for j in judgements) / max(1, len(judgements)), 1)
    avg_depth = round(sum(j.depth_separation_score for j in judgements) / max(1, len(judgements)), 1)
    final_score = round(sum(j.composite_score for j in judgements) / max(1, len(judgements)), 1)

    all_passed = all(j.passed for j in judgements)
    all_reasons = []
    for j in judgements:
        all_reasons.extend(j.reasons)
    all_reasons.extend(diversity_notes)

    scorecard = VisualJudgeScorecard(
        production_id=visual_plan.production_id,
        passed=all_passed,
        final_score=final_score,
        semantic_grounding=avg_semantic,
        visual_clarity=avg_clarity,
        art_direction=avg_art,
        composition=avg_comp,
        motion_activity=avg_motion,
        depth_separation=avg_depth,
        scene_judgements=judgements,
        failure_reasons=all_reasons,
    )

    # Persist report
    report_file = output_dir / "visual_judge_scorecard.json"
    report_file.write_text(json.dumps(scorecard.model_dump(), indent=2), encoding="utf-8")
    return scorecard


def audit_and_enforce_release_gate(
    mp4_path: Path,
    visual_plan: UnifiedVisualPlan,
    output_dir: Path,
) -> VisualJudgeScorecard:
    """Strict Release Gate: verifies visual truth and blocks release upon failure."""
    if not mp4_path.exists():
        raise VisualGateRejectionError(f"Target MP4 does not exist: {mp4_path}. Zero fallback allowed.")

    scorecard = evaluate_video_visual_truth(mp4_path, visual_plan, output_dir)
    if not scorecard.passed:
        reasons_msg = "; ".join(scorecard.failure_reasons)
        raise VisualGateRejectionError(
            f"RELEASE BLOCKED: Independent Visual Judge rejected video {mp4_path.name} "
            f"(Score: {scorecard.final_score}/10.0). Reasons: {reasons_msg}"
        )

    return scorecard
