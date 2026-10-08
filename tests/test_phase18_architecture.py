"""Phase 18 Comprehensive Architecture & Integrity Test Suite.

Validates:
1. First-class Character / Mascot System (CharacterSpec, MascotRole, transparent asset rendering).
2. Unified Semantic Visual Director (Canonical 4-layer depth hierarchy, parallax factors, transitions).
3. Authoritative Artifact Synchronization (Canonical chronological creation and approval order).
4. Independent Visual Judge Ensemble & Strict Release Gate (Pixel perception, domain validation, gate rejection).
"""
import json
import pytest
from pathlib import Path
from PIL import Image, ImageDraw

from production.phase18.character_director import (
    CharacterSpec,
    MascotRole,
    MascotMotion,
    direct_scene_character,
    render_character_asset,
)
from production.phase18.visual_director import (
    CanonicalLayerSpec,
    CanonicalSceneSpec,
    UnifiedVisualPlan,
    direct_production_scenes,
)
from production.phase18.sync import sync_authoritative_artifacts
from production.phase18.visual_judge import (
    VisualGateRejectionError,
    SceneVisualJudgement,
    VisualJudgeScorecard,
    inspect_frame_pixels,
    judge_single_scene_frame,
    audit_and_enforce_release_gate,
)
from production.phase17.style_systems import get_style_system
from production.artifact_store import ArtifactStore
from schemas.models.artifact import ProducerInfo, ArtifactEnvelope
from schemas.models.common import ProducerKind
from production.state import StateStore


# -----------------------------------------------------------------------------
# 1. Mascot & Character System Tests
# -----------------------------------------------------------------------------

def test_mascot_directorial_roles():
    """Verify that direct_scene_character assigns contextual roles and tools."""
    # Context / Intro -> Explorer for entry hook
    intro_spec = direct_scene_character(
        scene_idx=0,
        total_scenes=5,
        narrative_role="hook",
        subject="vector database indexing",
        action="explaining embedding mechanics",
        topic="the architecture of naive rag",
    )
    assert intro_spec.role == MascotRole.EXPLORER
    assert intro_spec.depth_plane == "midground"
    assert intro_spec.motion == MascotMotion.STATIC

    # Mechanism / Runtime -> Engineer with tactile tool
    eng_spec = direct_scene_character(
        scene_idx=2,
        total_scenes=5,
        narrative_role="mechanism",
        subject="chunking engine parser",
        action="tuning parsing parameters",
        topic="the architecture of naive rag",
    )
    assert eng_spec.role == MascotRole.ENGINEER
    assert eng_spec.tool_held is not None
    assert eng_spec.motion == MascotMotion.STATIC

    # Scale / Implication -> Analyst with HUD panel
    analyst_spec = direct_scene_character(
        scene_idx=3,
        total_scenes=5,
        narrative_role="scale",
        subject="retrieval latency",
        action="monitoring telemetry throughput",
        topic="the architecture of naive rag",
    )
    assert analyst_spec.role == MascotRole.ANALYST
    assert analyst_spec.tool_held == "telemetry_hud_panel"
    assert analyst_spec.motion == MascotMotion.STATIC


def test_mascot_asset_rendering(tmp_path: Path):
    """Verify that render_character_asset outputs a transparent 1080x1920 PNG with alpha channel."""
    spec = CharacterSpec(
        role=MascotRole.ENGINEER,
        pose="pointing_active",
        action="inspecting node connections",
        target="chunking node",
        scale=1.0,
        depth_plane="midground",
        position={"x": 540.0, "y": 960.0},
        motion=MascotMotion.INTERACT,
        emotion="confident_didactic",
        tool_held="quantum_stylus",
    )
    out_file = tmp_path / "char_test.png"
    rendered = render_character_asset(spec, out_file)
    assert rendered.exists()

    with Image.open(rendered) as img:
        assert img.size == (1080, 1920)
        assert img.mode == "RGBA"
        # Check that top-left margin is fully transparent
        tl_pixel = img.getpixel((10, 10))
        assert tl_pixel[3] == 0, "Mascot background should be transparent alpha"
        # Check that center has visible mascot pixels
        center_pixel = img.getpixel((540, 960))
        assert center_pixel[3] > 0, "Mascot body should have visible alpha"


# -----------------------------------------------------------------------------
# 2. Unified Semantic Visual Director Tests
# -----------------------------------------------------------------------------

def test_unified_visual_plan_4layer_hierarchy():
    """Verify that direct_production_scenes creates a 4-layer depth hierarchy with correct parallax."""
    sections = [
        {"section_id": "sec_01", "narrative_role": "hook", "spoken_text": "Naive RAG sounds simple until you scale it.", "emphasis_words": ["Naive RAG", "scale"]},
        {"section_id": "sec_02", "narrative_role": "mechanism", "spoken_text": "First, documents are parsed and converted to vectors.", "emphasis_words": ["parsed", "vectors"]},
        {"section_id": "sec_03", "narrative_role": "scale", "spoken_text": "At millions of queries, vector latency dominates.", "emphasis_words": ["millions", "latency"]},
    ]
    topic = "the architecture of naive rag process"
    measured = [3.5, 4.2, 3.8]

    visual_plan = direct_production_scenes(
        production_id="prod_test_p18",
        sections=sections,
        topic=topic,
        measured_durations=measured,
    )

    assert visual_plan.production_id == "prod_test_p18"
    assert len(visual_plan.scenes) == 3

    for idx, sc in enumerate(visual_plan.scenes):
        assert sc.spoken_text == sections[idx]["spoken_text"]
        assert sc.emphasis_words == sections[idx]["emphasis_words"]
        assert sc.character_spec is not None

        # Verify 4-layer depth structure
        roles = [lyr.role for lyr in sc.layers]
        assert "background" in roles
        assert "midground" in roles
        assert "character" in roles
        assert "foreground" in roles
        assert "primary_visual" in roles or "primary_composite" in roles

        bg_layer = next(l for l in sc.layers if l.role == "background")
        mid_layer = next(l for l in sc.layers if l.role == "midground")
        char_layer = next(l for l in sc.layers if l.role == "character")
        fg_layer = next(l for l in sc.layers if l.role == "foreground")

        # Depth order and parallax factor integrity
        assert bg_layer.z_index < mid_layer.z_index < char_layer.z_index < fg_layer.z_index
        assert bg_layer.parallax_factor < mid_layer.parallax_factor < char_layer.parallax_factor < fg_layer.parallax_factor


# -----------------------------------------------------------------------------
# 3. Authoritative Artifact Synchronization Tests
# -----------------------------------------------------------------------------

def test_authoritative_artifact_synchronization(tmp_path: Path):
    """Verify that sync_authoritative_artifacts persists artifacts in strict canonical order."""
    store = ArtifactStore(tmp_path / "artifacts")
    state_store = StateStore(projects_root=tmp_path / "projects")
    prod_id = "prod_sync_test"
    state = state_store.create(project_id=prod_id, pipeline="youtube-short", pipeline_version="2.0", target_duration=30.0)

    # Seed schema-valid mock script and proposal
    script_payload = {
        "title": "Understanding Vector Retrieval Systems",
        "hook": "Understanding vector retrieval systems.",
        "target_duration_seconds": 30.0,
        "word_count": 4,
        "sections": [
            {
                "id": "sec_01",
                "narrative_role": "hook",
                "spoken_text": "Understanding vector retrieval systems.",
                "estimated_start": 0.0,
                "estimated_end": 3.5,
                "duration": 3.5,
                "visual_intent": "Overview of vector spaces",
                "primary_intent": "reveal",
                "primary_subject": "Vector systems",
                "emphasis_words": ["vector"],
            }
        ],
    }
    script_env = store.create(
        "script", prod_id, "script",
        script_payload,
        producer=ProducerInfo(kind=ProducerKind.SYSTEM, provider="test"),
    )
    store.save(script_env)
    store.approve("script", prod_id, script_env.artifact_version)

    proposal_payload = {
        "selected_concept_id": "c1",
        "concepts": [
            {
                "concept_id": "c1",
                "title": "Vector Breakdown",
                "concept_family": "explainer",
                "hook": "Vector breakdown",
                "audience_promise": "Promise",
                "narrative_structure": "Structure",
                "visual_direction": "Editorial",
                "visual_metaphor": "Metaphor",
                "tone": "Technical",
                "pacing": "Fast",
                "scene_grammar": "HUD",
                "renderer_family": "explainer",
                "render_runtime": "remotion",
                "composition_mode": "atelier",
                "asset_strategy": "vector",
                "target_duration": 30.0,
                "reasoning": "Reasoning",
            },
            {
                "concept_id": "c2",
                "title": "Vector Deep Dive",
                "concept_family": "explainer",
                "hook": "Deep dive into vectors",
                "audience_promise": "Promise 2",
                "narrative_structure": "Structure 2",
                "visual_direction": "Editorial",
                "visual_metaphor": "Metaphor 2",
                "tone": "Technical",
                "pacing": "Fast",
                "scene_grammar": "HUD",
                "renderer_family": "explainer",
                "render_runtime": "remotion",
                "composition_mode": "atelier",
                "asset_strategy": "vector",
                "target_duration": 30.0,
                "reasoning": "Reasoning 2",
            },
        ],
        "decision_log": {
            "selected_concept_id": "c1",
            "decision_reason": "Default",
            "selection_mode": "auto",
            "timestamp": "2026-10-08T00:00:00Z",
            "actor": "system",
        },
    }
    proposal_env = store.create(
        "proposal_packet", prod_id, "proposal",
        proposal_payload,
        producer=ProducerInfo(kind=ProducerKind.SYSTEM, provider="test"),
    )
    store.save(proposal_env)
    store.approve("proposal_packet", prod_id, proposal_env.artifact_version)

    sections = [
        {"section_id": "sec_01", "narrative_role": "hook", "spoken_text": "Understanding vector retrieval systems.", "emphasis_words": ["vector"]},
    ]
    plan = direct_production_scenes(prod_id, sections, "vector retrieval", [3.5])
    style = get_style_system("claude_editorial")

    edit_data = sync_authoritative_artifacts(
        store=store,
        state=state,
        visual_plan=plan,
        script_envelope=script_env,
        proposal_envelope=proposal_env,
        style_system=style,
        projects_root=tmp_path / "projects",
    )

    # Verify all 4 canonical artifacts exist and are approved
    assert state.get_active_version("scene_plan") == 1
    assert state.get_active_version("asset_manifest") == 1
    assert state.get_active_version("art_direction") == 1
    assert state.get_active_version("edit_decisions") == 1

    # Verify edit_decisions payload contains 4-layer depth tracks
    assert "multi_layer_timeline" in edit_data
    assert "video_tracks" in edit_data
    assert "video_bg" in edit_data["video_tracks"]
    assert "video_char" in edit_data["video_tracks"]
    assert len(edit_data["video_tracks"]["video_char"]) == 1


# -----------------------------------------------------------------------------
# 4. Independent Visual Judge Ensemble & Strict Release Gate Tests
# -----------------------------------------------------------------------------

def test_visual_judge_pixel_inspection(tmp_path: Path):
    """Verify that inspect_frame_pixels computes accurate metrics."""
    # 1. Blank solid image
    blank_img = Image.new("RGB", (1080, 1920), (20, 20, 20))
    blank_metrics = inspect_frame_pixels(blank_img)
    assert blank_metrics["stddev_luminance"] < 1.0
    assert blank_metrics["edge_density"] < 1.0

    # 2. Rich composite image with distinct center subject
    rich_img = Image.new("RGB", (1080, 1920), (248, 250, 252))
    draw = ImageDraw.Draw(rich_img)
    # Draw dark margin
    draw.rectangle([(0, 0), (1080, 300)], fill=(15, 23, 42))
    # Draw center subject
    draw.rectangle([(200, 500), (880, 1400)], fill=(30, 64, 175))
    draw.text((300, 700), "HIGH CONTRAST TECHNICAL SCHEMA", fill=(255, 255, 255))
    rich_metrics = inspect_frame_pixels(rich_img)
    assert rich_metrics["stddev_luminance"] > 20.0
    assert rich_metrics["edge_density"] > 1.0
    assert rich_metrics["lum_separation"] > 10.0


def test_visual_judge_rejection_on_blank_frame(tmp_path: Path):
    """Verify that blank frames fail judge_single_scene_frame."""
    blank_path = tmp_path / "blank.png"
    Image.new("RGB", (1080, 1920), (10, 10, 10)).save(blank_path)

    char_spec = CharacterSpec(
        role=MascotRole.GUIDE,
        pose="balanced_observer",
        action="floating near diagram",
        target="vector space",
        scale=1.0,
        depth_plane="midground",
        position={"x": 540.0, "y": 960.0},
        motion=MascotMotion.FLOAT,
        emotion="neutral_intelligent",
    )
    scene_spec = CanonicalSceneSpec(
        scene_id="scene_01",
        section_id="sec_01",
        narrative_role="hook",
        start_seconds=0.0,
        end_seconds=3.5,
        duration_seconds=3.5,
        spoken_text="Hello",
        subject="vector retrieval",
        action="indexing vectors",
        environment="clean architectural space",
        visual_purpose="show vector database",
        visual_metaphor="vector space",
        shot_type="medium",
        camera_motion="approach_subject",
        composition="rule_of_thirds",
        transition_in="hard_cut",
        transition_out="hard_cut",
        character_spec=char_spec,
    )

    judgement = judge_single_scene_frame(blank_path, scene_spec, 1.75, "vector database")
    assert not judgement.passed
    assert any("Blank frame" in r or "low detail" in r.lower() for r in judgement.reasons)


def test_visual_judge_rejection_on_domain_mismatch(tmp_path: Path):
    """Verify that software topic depicting robotic arm is rejected by judge."""
    test_path = tmp_path / "frame.png"
    img = Image.new("RGB", (1080, 1920), (248, 250, 252))
    draw = ImageDraw.Draw(img)
    draw.rectangle([(200, 500), (880, 1400)], fill=(30, 64, 175))
    img.save(test_path)

    char_spec = CharacterSpec(
        role=MascotRole.GUIDE,
        pose="balanced_observer",
        action="floating",
        target="arm",
        scale=1.0,
        depth_plane="midground",
        position={"x": 540.0, "y": 960.0},
        motion=MascotMotion.FLOAT,
        emotion="neutral",
    )
    scene_spec = CanonicalSceneSpec(
        scene_id="scene_01",
        section_id="sec_01",
        narrative_role="mechanism",
        start_seconds=0.0,
        end_seconds=4.0,
        duration_seconds=4.0,
        subject="robotic arm actuator",  # Physical robotics in software topic
        action="gripping workpiece",
        environment="factory floor",
        visual_purpose="robotic handling",
        visual_metaphor="physical grasp",
        shot_type="medium",
        camera_motion="approach_subject",
        composition="rule_of_thirds",
        transition_in="hard_cut",
        transition_out="hard_cut",
        character_spec=char_spec,
    )

    judgement = judge_single_scene_frame(test_path, scene_spec, 2.0, "naive rag software architecture")
    assert not judgement.passed
    assert any("Domain mismatch" in r for r in judgement.reasons)


def test_strict_release_gate_missing_file():
    """Verify that audit_and_enforce_release_gate raises VisualGateRejectionError if MP4 is missing."""
    missing_mp4 = Path("non_existent_file.mp4")
    plan = UnifiedVisualPlan(
        production_id="test_missing",
        topic="test",
        total_duration_seconds=10.0,
        scenes=[],
    )

    with pytest.raises(VisualGateRejectionError) as exc_info:
        audit_and_enforce_release_gate(missing_mp4, plan, Path("qa"))

    assert "Zero fallback allowed" in str(exc_info.value)


def test_phase18_2_enhancements():
    """Verify Phase 18.2 architectural upgrades:
    1. Mascot is anchored to dedicated empty zone below cards (y >= 1040) across all scenes.
    2. Explicit target_anchor coordinates exist for directional laser pointer.
    3. Zero fabricated numbers: extracting without numbers yields qualitative verified state, not fake % or ms.
    4. Strings do not truncate mid-token.
    """
    from production.phase17.multi_layer_generator import _extract_semantic_entities, TopicDomain

    # 1. Mascot anchoring & target vector
    for s_idx, role in [(0, "hook"), (1, "mechanism"), (2, "escalation"), (3, "implication"), (4, "cta")]:
        spec = direct_scene_character(
            scene_idx=s_idx,
            total_scenes=5,
            narrative_role=role,
            subject="Enterprise Architecture Gateway",
            action="verifying pipeline",
            topic="Naive RAG",
        )
        assert spec.position["y"] >= 1040.0, f"Scene {s_idx} mascot collides with cards (y={spec.position['y']})"
        assert spec.target_anchor is not None, f"Scene {s_idx} missing target_anchor"
        assert "x" in spec.target_anchor and "y" in spec.target_anchor

    # 2. Zero fabricated numbers
    narr_no_numbers = "The query parser directs tokens into the unindexed vector table."
    headline, cards, metric = _extract_semantic_entities(
        subject="Enterprise Architecture Gateway",
        visual_purpose="Multi-Agent Orchestration Mesh Engine",
        visual_metaphor="Data Pipeline",
        narration=narr_no_numbers,
        domain=TopicDomain.SOFTWARE_AI,
    )
    assert metric == "VERIFIED STATE", f"Expected qualitative status, got fabricated: {metric}"
    assert not headline.endswith(" GA"), f"Headline truncated mid-word: {headline}"
    assert "ENTERPRISE ARCHITECTURE" in headline

    # 3. Preserves real metrics when present in narration
    narr_with_number = "Throughput increases by 40% with sub-10ms response."
    _, _, real_metric = _extract_semantic_entities(
        subject="Enterprise Architecture Gateway",
        visual_purpose="Multi-Agent Orchestration Mesh Engine",
        visual_metaphor="Data Pipeline",
        narration=narr_with_number,
        domain=TopicDomain.SOFTWARE_AI,
    )
    assert real_metric == "40%"


def test_phase18_3_scene_graph_and_multimodal_judge(tmp_path: Path):
    """Verify Phase 18.3:
    1. Dynamic Semantic Scene Graph compilation (Zero rigid templates).
    2. Dynamic mascot targeting derived from actual primary subject centroid.
    3. Zero fabricated claims (all details strictly grounded in input semantics).
    4. Empirical connected-component visual judge with observed topology verification.
    """
    from production.phase18.scene_graph import (
        build_semantic_scene_graph,
        SceneNodeType,
    )
    from production.phase17.multi_layer_generator import generate_scene_layers
    from production.phase18.visual_judge import analyze_frame_geometry, judge_scene_frames

    # 1. Pipeline topology compilation
    sg_pipeline = build_semantic_scene_graph(
        scene_id="sec_01",
        scene_index=1,
        total_scenes=5,
        narrative_role="mechanism",
        subject="Vector Indexing and Embedding Pipeline",
        visual_purpose="Convert raw documents into dense vector embeddings",
        spoken_text="Raw documents are chunked and converted into vector embeddings stored in a vector index.",
    )
    assert sg_pipeline.topology in ("pipeline", "process_flow", "object_transformation")
    assert len(sg_pipeline.nodes) >= 2
    # Check that primary anchor exactly matches primary node bounds center
    pri_node = next(n for n in sg_pipeline.nodes if n.is_primary)
    expected_cx = (pri_node.bounds[0] + pri_node.bounds[2]) / 2.0
    expected_cy = (pri_node.bounds[1] + pri_node.bounds[3]) / 2.0
    assert sg_pipeline.primary_anchor == (expected_cx, expected_cy)

    # 2. Contrast topology without fabricated "BASELINE / NAIVE" claims
    sg_contrast = build_semantic_scene_graph(
        scene_id="sec_02",
        scene_index=2,
        total_scenes=5,
        narrative_role="escalation",
        subject="Exact Keyword Search versus Semantic Vector Retrieval",
        visual_purpose="Compare token matching against embedding similarity",
        spoken_text="Keyword matching fails on synonyms versus dense semantic retrieval.",
    )
    assert sg_contrast.topology == "bipartite"
    # Ensure no fabricated text
    for n in sg_contrast.nodes:
        assert "BASELINE / NAIVE" not in n.label
        assert "OPTIMIZED // TARGET" not in n.label

    # 3. Direct production scenes binds mascot target_anchor to actual scene graph primary anchor
    plan = direct_production_scenes(
        production_id="test_sg_prod",
        sections=[
            {"section_id": "sec_01", "role": "mechanism", "title": "Vector Pipeline", "voiceover": "Embeddings are calculated.", "duration": 4.0},
        ],
        topic="Naive RAG Architecture",
    )
    sc = plan.scenes[0]
    assert sc.scene_graph is not None
    assert sc.character_spec.target_anchor["x"] == sc.scene_graph.primary_anchor[0]
    assert sc.character_spec.target_anchor["y"] == sc.scene_graph.primary_anchor[1]

    # 4. Render layers and run empirical visual judge
    layers = generate_scene_layers(
        scene_index=1,
        narration="Raw documents are chunked into vectors",
        output_dir=tmp_path,
        scene_id="sec_01",
        subject="Vector Indexing and Embedding Pipeline",
        visual_purpose="Convert raw documents into dense vector embeddings",
        narrative_role="mechanism",
        total_scenes=5,
        scene_graph=sc.scene_graph,
    )
    mid_img = Image.open(layers["mid"])
    geom = analyze_frame_geometry(mid_img)
    assert geom["num_clusters"] >= 1
    # Check empirical judge scoring and description
    judgement = judge_scene_frames(
        scene_spec=sc,
        scene_frames={"mid": layers["primary"], "start": layers["primary"], "end": layers["primary"]},
        topic="Naive RAG Architecture",
    )
    assert judgement.passed is True
    assert judgement.semantic_grounding_score >= 8.0
    assert "detected clusters" in judgement.visible_description
    assert "primary subject at" in judgement.visible_description


def test_phase18_4_semantic_composition_rebuild():
    """Verify Phase 18.4 Rebuild requirements:
    1. Mascot motion is STATIC by default, zero idle oscillation.
    2. Visual composition derived from semantics, not index modulo.
    3. Distinct topics/claims yield materially different visual topologies.
    4. Zero invented facts appear in scene graph nodes.
    5. Mascot position dynamically avoids subject collisions.
    """
    from production.phase18.scene_graph import build_semantic_scene_graph

    # 1. Mascot is static by default
    spec = CharacterSpec()
    assert spec.motion == MascotMotion.STATIC

    # Verify CharacterLayer.tsx does not have floatOffset or idle bobbing
    char_tsx = Path("remotion-composer/src/primitives/CharacterLayer.tsx").read_text("utf-8")
    assert "Math.sin(frame / 12) * 14" not in char_tsx
    assert "floatOffset" not in char_tsx
    assert "floatTilt" not in char_tsx

    # 2. Semantic Composition Diversity (Not repeating the same cards)
    # Transformation scene: Documents -> Parser -> Vectors
    sg_transform = build_semantic_scene_graph(
        scene_id="sc_01",
        scene_index=0,
        total_scenes=5,
        subject="Document Ingestion & Embedding",
        spoken_text="Raw input documents are parsed and converted into vector embeddings.",
        topic="Vector Databases",
    )
    assert sg_transform.topology == "object_transformation"
    assert sg_transform.evidence_contract is not None
    assert sg_transform.evidence_contract.composition_intent == "object_transformation"
    assert len(sg_transform.nodes) == 3
    assert sg_transform.nodes[1].shape_style == "transform_kernel"

    # Layered architecture scene: Transformer Attention Stack
    sg_stack = build_semantic_scene_graph(
        scene_id="sc_02",
        scene_index=1,
        total_scenes=5,
        subject="Transformer Self-Attention Matrix",
        spoken_text="At the architectural core is the Transformer, using multi-head self-attention across layers.",
        topic="Transformer Architecture",
    )
    assert sg_stack.topology == "layered_architecture"
    assert sg_stack.evidence_contract.composition_intent == "layered_architecture"
    assert sg_stack.nodes[1].shape_style == "matrix_grid"

    # Contrast scene: Classification vs Synthesis
    sg_bipartite = build_semantic_scene_graph(
        scene_id="sc_03",
        scene_index=2,
        total_scenes=5,
        subject="Synthesis versus Classification",
        spoken_text="Unlike classical AI that only classifies data, generative models synthesize novel outputs.",
        topic="Generative AI",
    )
    assert sg_bipartite.topology == "bipartite"
    assert sg_bipartite.evidence_contract.composition_intent == "bipartite_comparison"

    # 3. Zero Invented Facts
    all_details = [d for n in sg_transform.nodes + sg_stack.nodes + sg_bipartite.nodes for d in n.details]
    all_details_text = " ".join(all_details).lower()
    assert "daemon.init()" not in all_details_text
    assert "telemetry state verified" not in all_details_text
    assert "single-turn prompt flow" not in all_details_text
    assert "runtime error self-healing" not in all_details_text

    # 4. Scene-Aware Mascot Position & Anchoring
    # When primary node is in center, mascot stands at side corner to avoid collision
    char_directed = direct_scene_character(
        scene_idx=1,
        total_scenes=5,
        narrative_role="mechanism",
        subject="Transformer Attention",
        action="directing matrix",
        topic="Generative AI",
        scene_graph=sg_stack,
    )
    assert char_directed.position["x"] != 540.0, "Mascot must avoid center collision with hero node"
    assert char_directed.motion == MascotMotion.STATIC
    assert char_directed.target_anchor["x"] == sg_stack.primary_anchor[0]
    assert char_directed.target_anchor["y"] == sg_stack.primary_anchor[1]


