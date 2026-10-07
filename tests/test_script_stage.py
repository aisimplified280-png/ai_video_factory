"""Tests for ScriptHandler stage execution, blocking rules, and provenance."""
import pytest
from datetime import datetime, timezone

from schemas.models.artifact import ArtifactEnvelope, ProducerInfo
from schemas.models.common import ArtifactStatus, ProducerKind
from production.state import StateStore
from production.artifact_store import ArtifactStore
from production.stage_registry import StageResultStatus
from stages.script.script_director import ScriptHandler


@pytest.fixture
def mock_state(tmp_path):
    store = StateStore(projects_root=tmp_path)
    state = store.create(
        project_id="prod_script_test",
        pipeline="youtube-short",
        pipeline_version="2.0",
        target_duration=45.0,
    )
    state.metadata["topic"] = "Why AI Models Need More Compute"
    return state


@pytest.fixture
def research_envelope():
    return ArtifactEnvelope(
        artifact_type="research_brief",
        schema_version="2.0",
        artifact_version=1,
        production_id="prod_script_test",
        stage="research",
        status=ArtifactStatus.APPROVED,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        producer=ProducerInfo(kind=ProducerKind.SYSTEM),
        content_hash="sha256:" + "0" * 64,
        data={
            "topic": "Why AI Models Need More Compute",
            "facts": [{"claim": "Compute scaling requires 10x energy per generation", "source_ids": ["src_01"]}],
            "sources": [{"source_id": "src_01", "url": "https://example.com/ai"}],
            "data_points": [{"metric": "Power Demand", "value": "1 GW"}],
            "angles_discovered": ["Physical power grid bottlenecks"],
        },
    )


@pytest.fixture
def proposal_envelope():
    return ArtifactEnvelope(
        artifact_type="proposal_packet",
        schema_version="2.0",
        artifact_version=1,
        production_id="prod_script_test",
        stage="proposal",
        status=ArtifactStatus.APPROVED,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        producer=ProducerInfo(kind=ProducerKind.SYSTEM),
        content_hash="sha256:" + "1" * 64,
        data={
            "concepts": [
                {
                    "concept_id": "concept_01",
                    "title": "Industrial Grid AI",
                    "hook": "Every time an AI model doubles its intelligence, the energy spikes tenfold.",
                    "narrative_structure": "hook -> mechanism -> evidence -> payoff -> cta",
                    "visual_metaphor": "server rooms behaving like an industrial power grid",
                    "tone": "urgent and technical",
                    "renderer_family": "explainer",
                    "render_runtime": "remotion",
                    "composition_mode": "atelier",
                    "target_duration": 45.0,
                },
                {
                    "concept_id": "concept_02",
                    "title": "Historical Compute Timeline",
                    "hook": "We are running out of electricity to feed neural networks.",
                    "narrative_structure": "timeline -> scale -> cta",
                    "visual_metaphor": "historical timeline expanding across geographic maps",
                    "tone": "documentary",
                    "renderer_family": "documentary",
                    "render_runtime": "ffmpeg_pil",
                    "composition_mode": "templated",
                    "target_duration": 45.0,
                },
            ],
            "selected_concept_id": "concept_01",
            "renderer_family": "explainer",
            "render_runtime": "remotion",
            "composition_mode": "atelier",
        },
    )


def test_script_handler_blocks_on_missing_research(mock_state, proposal_envelope):
    handler = ScriptHandler()
    res = handler.run(
        stage_name="script",
        state=mock_state,
        inputs={"proposal_packet": proposal_envelope},
    )
    assert res.status == StageResultStatus.BLOCKED
    assert "MISSING_UPSTREAM_RESEARCH_BRIEF" in res.errors


def test_script_handler_blocks_on_missing_proposal(mock_state, research_envelope):
    handler = ScriptHandler()
    res = handler.run(
        stage_name="script",
        state=mock_state,
        inputs={"research_brief": research_envelope},
    )
    assert res.status == StageResultStatus.BLOCKED
    assert "MISSING_UPSTREAM_PROPOSAL_PACKET" in res.errors


def test_script_handler_successful_execution(mock_state, research_envelope, proposal_envelope):
    mock_llm_response = {
        "title": "Why AI Models Need More Compute",
        "hook": "Every time an AI model gets twice as smart, the compute needed does not double—it multiplies by ten.",
        "target_duration_seconds": 45.0,
        "sections": [
            {
                "section_id": "sec_01",
                "narrative_role": "hook",
                "spoken_text": "Every time an AI model gets twice as smart, the compute needed does not double—it multiplies by ten.",
                "emphasis_words": ["MULTIPACT"],
                "visual_intent": "Massive exponential power curve climbing across industrial grids.",
                "primary_intent": "reveal",
                "secondary_intents": ["show_scale"],
                "primary_subject": "Compute scaling",
                "entities": ["AI models"],
            },
            {
                "section_id": "sec_02",
                "narrative_role": "mechanism",
                "spoken_text": "Training isn't just data memorization; it's trillions of matrix calculations burning GPU power.",
                "emphasis_words": ["TRILLIONS"],
                "visual_intent": "Server blades glowing under sustained computational load.",
                "primary_intent": "show_process",
                "secondary_intents": [],
                "primary_subject": "Matrix operations",
                "entities": ["GPU clusters"],
            },
            {
                "section_id": "sec_03",
                "narrative_role": "evidence",
                "spoken_text": "A single new AI cluster now draws more power than an entire mid-sized city.",
                "emphasis_words": ["GIGAWATTS"],
                "visual_intent": "Satellite grid overlay comparing city lights to data center demand.",
                "primary_intent": "show_evidence",
                "secondary_intents": ["show_scale"],
                "primary_subject": "Data center power",
                "entities": ["Data centers"],
            },
            {
                "section_id": "sec_04",
                "narrative_role": "payoff",
                "spoken_text": "The frontier of AI is no longer code—it is raw physical energy.",
                "emphasis_words": ["PHYSICAL"],
                "visual_intent": "Macro transformation into industrial power substations.",
                "primary_intent": "explain",
                "secondary_intents": [],
                "primary_subject": "Energy frontier",
                "entities": ["Power substations"],
            },
            {
                "section_id": "sec_05",
                "narrative_role": "cta",
                "spoken_text": "Subscribe to AI Simplified Lab for more breakdowns like this.",
                "emphasis_words": ["SUBSCRIBE"],
                "visual_intent": "Channel signature brand device with kinetic subscribe cue.",
                "primary_intent": "conclude",
                "secondary_intents": [],
                "primary_subject": "Channel identity",
                "entities": ["AI Simplified Lab"],
            },
        ],
    }

    def fake_llm(prompt, system=""):
        return mock_llm_response, "mock_provider", "mock_model", 350

    handler = ScriptHandler(llm_caller=fake_llm)
    res = handler.run(
        stage_name="script",
        state=mock_state,
        inputs={
            "research_brief": research_envelope,
            "proposal_packet": proposal_envelope,
        },
    )

    assert res.status == StageResultStatus.READY
    assert res.data is not None
    assert "sections" in res.data
    assert len(res.data["sections"]) == 5
    assert res.data["cta"]["narrative_role"] == "cta"
    assert res.data["timing_status"] == "valid"
    assert res.producer is not None
    assert res.producer.provider == "mock_provider"
    assert res.producer.prompt_hash.startswith("sha256:")
