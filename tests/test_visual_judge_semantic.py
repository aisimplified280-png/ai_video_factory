"""Visual Judge semantic verification fixtures (§8).

The judge must distinguish the correct subject+relationship being depicted from
a readable but generic card layout. Fixtures use REAL rendered layer PNGs
(generate_scene_layers) so pixel geometry is identical in quality — only the
semantic inventory differs:

- Negative: generic cards ("STAGE ONE/TWO") claim to depict GPS positioning.
  It must NOT pass semantic correctness despite perfect clusters and contrast.
- Positive: the actual satellites→phone depiction passes verification.
- Unverified: a graph with no contract is capped below the release threshold.
"""
from pathlib import Path

from PIL import Image

from production.phase17.multi_layer_generator import generate_scene_layers
from production.phase18.scene_graph import (
    SceneEdge,
    SceneNode,
    SceneNodeType,
    SemanticSceneGraph,
    VisualEvidenceContract,
    build_semantic_scene_graph,
)
from production.phase18.visual_judge import judge_scene_frames, verify_semantic_evidence
from production.phase18.visual_director import direct_production_scenes

GPS_NARRATION = (
    "GPS satellites send precise timing signals to your phone. "
    "The phone compares four arrival times to fix its position."
)


def _generic_flow_graph() -> SemanticSceneGraph:
    """A technically perfect but semantically empty 3-card flow."""
    nodes = [
        SceneNode(id="s1", label="STAGE ONE", node_type=SceneNodeType.PROCESS, bounds=(130, 590, 430, 840)),
        SceneNode(id="s2", label="STAGE TWO", node_type=SceneNodeType.PROCESS, bounds=(450, 590, 750, 840), is_primary=True),
        SceneNode(id="s3", label="STAGE THREE", node_type=SceneNodeType.PROCESS, bounds=(770, 590, 1030, 840)),
    ]
    edges = [
        SceneEdge(from_node="s1", to_node="s2", relationship="flows_to"),
        SceneEdge(from_node="s2", to_node="s3", relationship="flows_to"),
    ]
    contract = VisualEvidenceContract(
        scene_id="sec_neg",
        subject="GPS satellites and your phone",
        subject_type="process_flow",
        entities=["GPS satellites", "your phone"],
        relationship="sequential_pipeline",
        action="satellites send timing signals to a phone",
        required_visual_evidence=["satellite", "phone", "timing signals"],
    )
    return SemanticSceneGraph(
        scene_id="sec_neg",
        topic_domain="ai",
        central_subject="GPS satellites and your phone",
        narrative_role="mechanism",
        topology="process_flow",
        nodes=nodes,
        edges=edges,
        primary_anchor=(600.0, 715.0),
        required_visual_evidence=["satellite", "phone"],
        evidence_contract=contract,
    )


def _scene_spec_with_graph(graph: SemanticSceneGraph, scene_id: str = "sec_judge"):
    """A fully valid CanonicalSceneSpec whose scene_graph we control."""
    plan = direct_production_scenes(
        production_id=f"judge_{scene_id}",
        sections=[
            {"section_id": "sec_01", "role": "mechanism", "title": "Mechanism", "voiceover": GPS_NARRATION, "duration": 5.0},
            {"section_id": "sec_02", "role": "context", "title": "Outro", "voiceover": "Subscribe for more.", "duration": 3.0},
        ],
        topic="How GPS works",
    )
    sc = plan.scenes[0]
    object.__setattr__(sc, "scene_id", scene_id)
    object.__setattr__(sc, "scene_graph", graph)
    object.__setattr__(sc, "required_visual_evidence", graph.required_visual_evidence)
    return sc


def _render(tmp_path: Path, name: str, graph: SemanticSceneGraph) -> dict:
    out = tmp_path / name
    out.mkdir(parents=True, exist_ok=True)
    return generate_scene_layers(
        scene_index=1,
        narration=GPS_NARRATION,
        output_dir=out,
        scene_id="sec_judge",
        subject="GPS positioning",
        visual_purpose="Explain satellite positioning",
        narrative_role="mechanism",
        total_scenes=5,
        scene_graph=graph,
    )


def test_negative_fixture_generic_cards_cannot_pass_semantics(tmp_path: Path):
    """Cluster-rich, high-contrast generic cards claiming GPS must be rejected."""
    graph = _generic_flow_graph()
    spec = _scene_spec_with_graph(graph, "sec_neg")
    layers = _render(tmp_path, "neg", graph)
    judgement = judge_scene_frames(
        scene_spec=spec,
        scene_frames={"mid": layers["primary"], "start": layers["primary"], "end": layers["primary"]},
        topic="How GPS works",
    )
    assert judgement.semantic_evidence == "contradicted", judgement.visible_description
    assert judgement.semantic_grounding_score <= 3.5
    assert judgement.passed is False
    assert any("CONTRADICTED" in r for r in judgement.reasons)


def test_positive_fixture_real_subject_and_relationship_pass(tmp_path: Path):
    """The actual satellites→phone depiction verifies and passes."""
    graph = build_semantic_scene_graph(
        scene_id="sec_pos",
        narrative_role="mechanism",
        subject="GPS positioning",
        visual_purpose="Explain satellite positioning",
        spoken_text=GPS_NARRATION,
        topic="How GPS works",
    )
    verdict, notes = verify_semantic_evidence(graph.evidence_contract, graph)
    assert verdict == "verified", notes
    spec = _scene_spec_with_graph(graph, "sec_pos")
    layers = _render(tmp_path, "pos", graph)
    judgement = judge_scene_frames(
        scene_spec=spec,
        scene_frames={"mid": layers["primary"], "start": layers["primary"], "end": layers["primary"]},
        topic="How GPS works",
    )
    assert judgement.semantic_evidence == "verified", judgement.visible_description
    assert judgement.semantic_grounding_score >= 7.0
    assert judgement.passed is True


def test_unverified_contract_is_capped_below_release_threshold(tmp_path: Path):
    """No contract → unverified → semantic capped at 6.5 → cannot release."""
    graph = build_semantic_scene_graph(
        scene_id="sec_unv",
        narrative_role="mechanism",
        subject="GPS positioning",
        visual_purpose="Explain satellite positioning",
        spoken_text=GPS_NARRATION,
        topic="How GPS works",
    )
    object.__setattr__(graph, "evidence_contract", None)
    spec = _scene_spec_with_graph(graph, "sec_unv")
    layers = _render(tmp_path, "unv", graph)
    judgement = judge_scene_frames(
        scene_spec=spec,
        scene_frames={"mid": layers["primary"], "start": layers["primary"], "end": layers["primary"]},
        topic="How GPS works",
    )
    assert judgement.semantic_evidence == "unverified"
    assert judgement.semantic_grounding_score <= 6.5
    assert judgement.passed is False


def test_verify_is_pure_and_handles_degenerate_inputs():
    assert verify_semantic_evidence(None, None)[0] == "unverified"
    empty_graph = SemanticSceneGraph(
        scene_id="e", topic_domain="ai", central_subject="", narrative_role="mechanism",
        topology="process_flow", nodes=[], edges=[],
    )
    assert verify_semantic_evidence(
        VisualEvidenceContract(scene_id="e", subject="", subject_type=""), empty_graph
    )[0] == "unverified"
