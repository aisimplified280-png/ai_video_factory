"""Concrete subject primitives (§3) and scene-meaning classification (§4).

Regression examples demanded by the audit: each narration must VISUALLY DEPICT
its central concept — the object the narration names gets a real glyph on the
node and the relationship gets a semantic edge — not merely a label inside a
generic card. Also locks the classification fixes:
  - "classifier" (mechanism word) does not force a comparison layout
  - "transformer" (mechanism word) does not force a layered stack
  - a bare "parse" mention does not force a transformation
"""
from production.phase18.scene_graph import build_semantic_scene_graph, _node_icon


def _icon_set(sg):
    return {n.icon for n in sg.nodes if n.icon}


def _labels(sg):
    return [n.label for n in sg.nodes]


def test_gps_satellites_and_phone_are_depicted():
    """GPS: satellites sending timing signals to a phone."""
    sg = build_semantic_scene_graph(
        scene_id="sec_gps",
        narrative_role="mechanism",
        subject="GPS positioning",
        visual_purpose="Explain how satellites let a phone fix its location",
        spoken_text=(
            "GPS satellites send precise timing signals to your phone. "
            "The phone compares four arrival times to fix its position."
        ),
        topic="How GPS works",
    )
    icons = _icon_set(sg)
    assert "satellite" in icons, f"no satellite glyph: {sg.topology} {_labels(sg)}"
    assert "phone" in icons, f"no phone glyph: {sg.topology} {_labels(sg)}"
    assert sg.edges and any(e.from_node != e.to_node for e in sg.edges), "signal relationship missing"


def test_naive_rag_chunks_vectors_and_index_are_depicted():
    """Naive RAG: documents → embeddings → vector index."""
    sg = build_semantic_scene_graph(
        scene_id="sec_rag",
        narrative_role="mechanism",
        subject="Naive RAG architecture",
        visual_purpose="Explain how documents become searchable vectors",
        spoken_text=(
            "Documents are chunked into passages. "
            "Embeddings capture each passage's meaning. "
            "A vector index stores every embedding for search."
        ),
        topic="Naive RAG",
    )
    icons = _icon_set(sg)
    assert "document" in icons, f"no document glyph: {sg.topology} {_labels(sg)}"
    assert "embedding" in icons, f"no embedding glyph: {sg.topology} {_labels(sg)}"
    assert "database" in icons, f"no vector-index glyph: {sg.topology} {_labels(sg)}"


def test_oauth_client_server_token_relationship():
    """OAuth: client ↔ authorization server issuing a token."""
    sg = build_semantic_scene_graph(
        scene_id="sec_oauth",
        narrative_role="mechanism",
        subject="OAuth authorization",
        visual_purpose="Explain how a client obtains a token",
        spoken_text=(
            "The client sends a request to the authorization server. "
            "The authorization server issues a signed token. "
            "The client reuses the token to call the API."
        ),
        topic="OAuth explained",
    )
    icons = _icon_set(sg)
    assert "client" in icons, f"no client glyph: {sg.topology} {_labels(sg)}"
    assert "server" in icons, f"no server glyph: {sg.topology} {_labels(sg)}"
    # Meaningful multiword entity preserved (not reduced to a generic word).
    assert any("authorization server" in lbl.lower() for lbl in _labels(sg)), _labels(sg)


def test_cpu_cache_and_memory_are_depicted():
    """CPU cache hierarchy: CPU → cache → main memory."""
    sg = build_semantic_scene_graph(
        scene_id="sec_cache",
        narrative_role="mechanism",
        subject="CPU cache hierarchy",
        visual_purpose="Explain why the cache makes the CPU fast",
        spoken_text=(
            "The CPU asks the cache for data. "
            "The cache returns hits instantly. "
            "On a miss, main memory supplies the block."
        ),
        topic="How CPU cache works",
    )
    icons = _icon_set(sg)
    assert "cpu" in icons, f"no cpu glyph: {sg.topology} {_labels(sg)}"
    assert "cache" in icons, f"no cache glyph: {sg.topology} {_labels(sg)}"
    assert "memory" in icons, f"no memory glyph: {sg.topology} {_labels(sg)}"


def test_robotics_arm_and_workpiece_are_depicted():
    """Robotics: a physical arm acting on a workpiece."""
    sg = build_semantic_scene_graph(
        scene_id="sec_arm",
        narrative_role="mechanism",
        subject="Robotic cell",
        visual_purpose="Explain how the arm handles the part",
        spoken_text=(
            "The workpiece enters the cell. "
            "A robotic arm grips it and loads the fixture."
        ),
        topic="Robotic manipulation",
    )
    icons = _icon_set(sg)
    assert "workpiece" in icons, f"no workpiece glyph: {sg.topology} {_labels(sg)}"
    assert "arm" in icons, f"no arm glyph: {sg.topology} {_labels(sg)}"


def test_classifier_mention_does_not_force_comparison():
    """'Classif*' is a mechanism word, not a narrated comparison (§4)."""
    sg = build_semantic_scene_graph(
        scene_id="sec_clf",
        narrative_role="mechanism",
        subject="Softmax classifier",
        visual_purpose="Explain what the classifier outputs",
        spoken_text="A classifier scores every class probability for the input vector.",
        topic="Neural network heads",
    )
    assert sg.topology != "bipartite", f"classifier mention forced a comparison: {_labels(sg)}"


def test_transformer_mention_does_not_force_stack():
    """'Transformer' names a mechanism; a stack needs structural language (§4)."""
    sg = build_semantic_scene_graph(
        scene_id="sec_tf",
        narrative_role="mechanism",
        subject="Transformer block",
        visual_purpose="Explain what the transformer does with the sequence",
        spoken_text="The transformer processes the whole sequence with attention in one step.",
        topic="Transformer architecture",
    )
    assert sg.topology != "layered_architecture", f"transformer mention forced a stack: {_labels(sg)}"


def test_bare_parse_mention_does_not_force_transformation():
    """A transformation requires a stated <source> → <result> conversion (§4)."""
    sg = build_semantic_scene_graph(
        scene_id="sec_parse",
        narrative_role="mechanism",
        subject="Stream parser",
        visual_purpose="Explain what the parser does",
        spoken_text="The parser reads tokens from the stream and counts them.",
        topic="Stream processing",
    )
    assert sg.topology != "object_transformation", f"bare parse mention forced a transform: {_labels(sg)}"


def test_narrated_transformation_still_fires():
    """The tightened rule must not kill genuine transformations."""
    sg = build_semantic_scene_graph(
        scene_id="sec_tr",
        narrative_role="mechanism",
        subject="Embedding pipeline",
        visual_purpose="Explain the conversion",
        spoken_text="Raw documents are parsed and converted into vector embeddings.",
        topic="RAG ingestion",
    )
    assert sg.topology == "object_transformation", f"{sg.topology}: {_labels(sg)}"
    assert any(n.shape_style == "transform_kernel" for n in sg.nodes)


def test_narrated_comparison_still_fires_with_two_sided_relationship():
    sg = build_semantic_scene_graph(
        scene_id="sec_vs",
        narrative_role="comparison",
        subject="Keyword search vs vector search",
        visual_purpose="Contrast the two retrieval styles",
        spoken_text="Keyword search fails on synonyms, whereas vector search matches meaning.",
        topic="Retrieval styles",
    )
    assert sg.topology == "bipartite"
    assert all(e.relationship == "contrasts_with" for e in sg.edges), [e.relationship for e in sg.edges]


def test_node_icon_lexicon_is_deterministic_and_bounded():
    assert _node_icon("GPS satellites talk to your phone") == "satellite"
    assert _node_icon("the authorization server issues a token") == "server"
    assert _node_icon("capture a photo of the sky") == ""
    # Word boundaries: "rapid"/"application" must not match "api"/"app"-style terms.
    assert _node_icon("a rapid sequence of frames") != "api"


def test_sync_passes_semantics_through_to_diagram_spec():
    """Wiring guard: the diagram spec must carry shape/node/relationship data
    (the behavior lives in the scene-graph tests above and in the renderer)."""
    import inspect
    from production.phase18 import sync as sync_mod

    src = inspect.getsource(sync_mod)
    for field in ('"shape_style"', '"node_type"', '"icon"', '"relationship"', '"topology"'):
        assert field in src, f"diagram_spec drops {field}"
