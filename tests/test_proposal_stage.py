"""Tests for stages/proposal/proposal_director.py (ProposalHandler)."""
from pathlib import Path
from tempfile import TemporaryDirectory
import pytest

from schemas.models.artifact import ArtifactEnvelope, ProducerInfo
from schemas.models.common import ProducerKind, RunMode
from production.artifact_store import ArtifactStore
from production.pipeline_loader import PipelineLoader
from production.state import StateStore
from production.stage_registry import StageResultStatus, StageRegistry
from production.stage_runner import StageRunner
from stages.proposal.proposal_director import ProposalHandler


def make_divergent_llm_response(target_duration=35.0):
    return {
        "concepts": [
            {
                "concept_id": "concept_01",
                "title": "Industrial Power Grid",
                "concept_family": "system_visualization",
                "hook": "What if an AI datacenter consumed as much instantaneous power as a mid-sized city?",
                "audience_promise": "Examine the extreme physics of megawatt compute clusters.",
                "narrative_structure": "Substation incoming -> Transformer bank -> GPU cooling racks -> Token generation",
                "visual_direction": "Heavy industrial isometric diagrams with glowing power conduits",
                "visual_metaphor": "Server rooms behaving like an industrial power grid under surge load",
                "tone": "Urgent and physical",
                "pacing": "Industrial mechanical rhythms with sharp diagnostic cuts",
                "scene_grammar": "Split telemetry HUD, voltage meters, thermal dissipation overlays",
                "renderer_family": "explainer",
                "render_runtime": "remotion",
                "composition_mode": "atelier",
                "asset_strategy": "vector blueprints and animated energy pulses",
                "target_duration": target_duration,
                "reasoning": "Emphasizes the tangible infrastructure barrier to AI expansion."
            },
            {
                "concept_id": "concept_02",
                "title": "The Paper Trail",
                "concept_family": "documentary",
                "hook": "The secret algorithm behind every modern chatbot was written in 17 lines of code.",
                "audience_promise": "Follow the mathematical discovery that reshaped Silicon Valley.",
                "narrative_structure": "Whiteboard formula -> Academic skepticism -> Secret prototype -> Trillion dollar industry",
                "visual_direction": "High-contrast archival documentary with kinetic typewriter text and paper grains",
                "visual_metaphor": "A single scribbled mathematical theorem igniting a global chain reaction",
                "tone": "Investigative and dramatic",
                "pacing": "Deliberate documentary cadence punctuated by archival reveals",
                "scene_grammar": "Archive zoom, redaction highlight bars, split biographical portraits",
                "renderer_family": "documentary",
                "render_runtime": "ffmpeg_pil",
                "composition_mode": "templated",
                "asset_strategy": "photographic archival scans, typography overlays, ink stains",
                "target_duration": target_duration,
                "reasoning": "Connects deeply with human curiosity and origin stories."
            },
            {
                "concept_id": "concept_03",
                "title": "Autonomous Swarm",
                "concept_family": "cinematic_story",
                "hook": "We gave 1,000 autonomous AI agents an open economy. Here is what they built in 24 hours.",
                "audience_promise": "Watch synthetic society evolve faster than human comprehension.",
                "narrative_structure": "Genesis initialization -> Trade network emergence -> Currency war -> Autonomous equilibrium",
                "visual_direction": "Dark obsidian field with luminescent dynamic constellation lines",
                "visual_metaphor": "A microscopic digital petri dish blooming into a sprawling neon metropolis",
                "tone": "Futuristic and sociological",
                "pacing": "Exponential acceleration mirroring the simulation speed",
                "scene_grammar": "Network graph topology, transaction cascades, holographic HUD displays",
                "renderer_family": "motion_graphics",
                "render_runtime": "hyperframes",
                "composition_mode": "atelier",
                "asset_strategy": "3D graph shaders, particle streams, telemetry tickers",
                "target_duration": target_duration,
                "reasoning": "Visualizes non-human coordination dynamics."
            }
        ],
        "selected_concept_id": None
    }


def make_mock_llm(data):
    def _caller(prompt, system=None, **kwargs):
        return data, "openai", "gpt-4o-mini", 680
    return _caller


@pytest.fixture
def mock_research_envelope():
    from datetime import datetime, timezone
    from schemas.models.common import ArtifactStatus
    now = datetime.now(timezone.utc)
    return ArtifactEnvelope(
        artifact_type="research_brief",
        schema_version="2.0",
        artifact_version=1,
        production_id="proj_prop_test",
        stage="research",
        status=ArtifactStatus.READY,
        created_at=now,
        updated_at=now,
        data={
            "topic": "Datacenter AI Power Constraints",
            "audience": "general_tech",
            "sources": [
                {"source_id": "src_001", "title": "Grid Impact Report", "url": "https://iea.org/grid-ai"}
            ],
            "facts": [
                {"claim": "AI datacenters require gigawatt-level power interconnects.", "source_ids": ["src_001"]}
            ],
            "angles_discovered": ["Energy bottleneck", "Economic scale"]
        },
        producer=ProducerInfo(kind=ProducerKind.LLM, provider="gemini", model="gemini-2.0-flash"),
        content_hash="sha256:" + "0" * 64,
    )


def test_proposal_handler_blocks_when_missing_upstream_research():
    with TemporaryDirectory() as td:
        root = Path(td)
        state_store = StateStore(projects_root=root)
        state = state_store.create(
            project_id="proj_no_res",
            pipeline="youtube-short",
            pipeline_version="2.0",
            target_duration=35.0,
        )
        handler = ProposalHandler()
        result = handler.run("proposal", state, inputs={})
        assert result.status == StageResultStatus.BLOCKED
        assert "missing required upstream artifact" in result.message


def test_proposal_handler_auto_mode_selects_and_locks_runtime(mock_research_envelope):
    with TemporaryDirectory() as td:
        root = Path(td)
        state_store = StateStore(projects_root=root)
        state = state_store.create(
            project_id="proj_prop_test",
            pipeline="youtube-short",
            pipeline_version="2.0",
            target_duration=35.0,
            run_mode=RunMode.AUTO,
        )

        mock_data = make_divergent_llm_response()
        handler = ProposalHandler(llm_caller=make_mock_llm(mock_data))

        result = handler.run("proposal", state, inputs={"research_brief": mock_research_envelope})
        assert result.status == StageResultStatus.READY
        assert result.data["selected_concept_id"] == "concept_01"

        # Check decision log
        d_log = result.data["decision_log"]
        assert d_log is not None
        assert d_log["selected_concept_id"] == "concept_01"
        assert d_log["actor"] == "system"
        assert d_log["selection_mode"] == "auto"

        # Check locked runtime decisions
        locked = d_log["locked_decisions"]
        assert locked["renderer_family"] == "explainer"
        assert locked["render_runtime"] == "remotion"
        assert locked["composition_mode"] == "atelier"

        # Check state recorded decisions
        assert len(state.decisions) >= 1
        assert "concept_01" in state.decisions[0].decision
        assert state.metadata["locked_runtime"] == locked


def test_proposal_handler_guided_mode_waits_for_approval(mock_research_envelope):
    with TemporaryDirectory() as td:
        root = Path(td)
        state_store = StateStore(projects_root=root)
        state = state_store.create(
            project_id="proj_prop_guided",
            pipeline="youtube-short",
            pipeline_version="2.0",
            target_duration=35.0,
            run_mode=RunMode.GUIDED,
        )

        mock_data = make_divergent_llm_response()
        handler = ProposalHandler(llm_caller=make_mock_llm(mock_data))

        result = handler.run("proposal", state, inputs={"research_brief": mock_research_envelope})
        assert result.status == StageResultStatus.WAITING_APPROVAL
        assert result.data["selected_concept_id"] is None
        assert len(result.data["concepts"]) == 3
