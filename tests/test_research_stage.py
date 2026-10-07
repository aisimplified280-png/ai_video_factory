"""Tests for stages/research/research_director.py (ResearchHandler)."""
from pathlib import Path
from tempfile import TemporaryDirectory
import pytest

from schemas.models.artifact import ArtifactEnvelope, ProducerInfo
from schemas.models.common import ProducerKind
from production.artifact_store import ArtifactStore
from production.pipeline_loader import PipelineLoader
from production.state import StateStore
from production.stage_registry import StageResultStatus
from stages.research.research_director import ResearchHandler, ResearchRequest, is_topic_time_sensitive
from stages.research.source_collector import SourceRecord, MockSourceProvider


def make_mock_llm(return_data: dict, prov="gemini", mdl="gemini-2.0-flash", tokens=450):
    def _caller(prompt, system=None, **kwargs):
        return return_data, prov, mdl, tokens
    return _caller


@pytest.fixture
def mock_sources():
    return [
        SourceRecord(
            source_id="src_001",
            title="Google DeepMind SIMA 2 Overview",
            url="https://deepmind.google/discover/blog/sima-2-agentic-ai",
            domain="deepmind.google",
            published_at="2025-01-10T00:00:00Z",
            source_type="official_announcement",
            content_excerpt="SIMA 2 learns generalist 3D navigation and goal completion across virtual worlds.",
            relevance_score=0.95
        ),
        SourceRecord(
            source_id="src_002",
            title="ArXiv: Evaluative Foundation Models for Agent Control",
            url="https://arxiv.org/abs/2501.12345",
            domain="arxiv.org",
            published_at="2025-01-12T00:00:00Z",
            source_type="documentation",
            content_excerpt="We demonstrate zero-shot transfer across 14 commercial game environments.",
            relevance_score=0.92
        ),
        SourceRecord(
            source_id="src_003",
            title="TechCrunch: The Next Frontier of Embodied Agents",
            url="https://techcrunch.com/2025/01/14/embodied-ai-agents",
            domain="techcrunch.com",
            published_at="2025-01-14T00:00:00Z",
            source_type="reputable_publication",
            content_excerpt="Industry consensus centers on language-grounded policy distillation.",
            relevance_score=0.88
        ),
    ]


def test_time_sensitive_keyword_detection():
    assert is_topic_time_sensitive("Latest DeepSeek R1 Model Update Today") is True
    assert is_topic_time_sensitive("Breaking: OpenAI Announces Operator") is True
    assert is_topic_time_sensitive("How Neural Networks Work") is False


def test_research_handler_blocks_when_search_provider_unavailable():
    with TemporaryDirectory() as td:
        root = Path(td)
        state_store = StateStore(projects_root=root)
        state = state_store.create(
            project_id="proj_res_block",
            pipeline="youtube-short",
            pipeline_version="2.0",
            target_duration=35.0,
            metadata={"topic": "Quantum Machine Learning"},
        )

        # Mock provider that reports is_available() = False
        unavailable_prov = MockSourceProvider([])
        unavailable_prov.available = False

        handler = ResearchHandler(source_provider=unavailable_prov)
        result = handler.run("research", state, inputs={})

        assert result.status == StageResultStatus.BLOCKED
        assert "RESEARCH_PROVIDER_UNAVAILABLE" in result.message
        assert "RESEARCH_PROVIDER_UNAVAILABLE" in result.errors


def test_research_handler_successful_synthesis_with_mock_provider(mock_sources):
    with TemporaryDirectory() as td:
        root = Path(td)
        state_store = StateStore(projects_root=root)
        state = state_store.create(
            project_id="proj_res_ok",
            pipeline="youtube-short",
            pipeline_version="2.0",
            target_duration=35.0,
            metadata={"topic": "SIMA 2 Embodied AI Agents"},
        )

        mock_llm_data = {
            "topic": "SIMA 2 Embodied AI Agents",
            "audience": "general_tech",
            "content_landscape": "Rapid progression from 2D pixel agents to 3D continuous policy models.",
            "facts": [
                {
                    "claim": "SIMA 2 learns generalist navigation across diverse 3D environments.",
                    "source_ids": ["src_001"],
                    "confidence": 0.98
                },
                {
                    "claim": "Zero-shot transfer achieved across 14 game environments without retraining.",
                    "source_ids": ["src_002"],
                    "confidence": 0.94
                },
                {
                    "claim": "Language-grounded policy distillation forms the architectural core.",
                    "source_ids": ["src_003"],
                    "confidence": 0.91
                }
            ],
            "data_points": ["14 environments evaluated", "zero-shot baseline"],
            "expert_views": ["Grounding language directly into continuous motor actions is critical."],
            "audience_questions": ["Can these agents play real games autonomously?"],
            "angles_discovered": [
                "From language chat to physical embodied intelligence",
                "Why video game physics engines are the new training playground for robotics"
            ],
            "risks": ["Simulation-to-reality visual gap remains significant"]
        }

        mock_prov = MockSourceProvider(mock_sources)
        handler = ResearchHandler(
            source_provider=mock_prov,
            llm_caller=make_mock_llm(mock_llm_data, prov="gemini", mdl="gemini-2.0-flash", tokens=512)
        )

        result = handler.run("research", state, inputs={})
        assert result.status == StageResultStatus.READY
        assert result.data is not None
        assert len(result.data["sources"]) == 3
        assert len(result.data["facts"]) == 3
        assert result.producer.provider == "gemini"
        assert result.producer.prompt_hash is not None
        assert result.producer.estimated_cost is not None


def test_research_handler_persists_envelope_via_stage_runner(mock_sources):
    from production.stage_runner import StageRunner
    from production.stage_registry import StageRegistry

    with TemporaryDirectory() as td:
        root = Path(td)
        store = ArtifactStore(projects_root=root)
        state_store = StateStore(projects_root=root)
        loader = PipelineLoader()
        pipeline_def = loader.load("youtube-short")

        state = state_store.create(
            project_id="proj_runner_res",
            pipeline="youtube-short",
            pipeline_version="2.0",
            target_duration=35.0,
            metadata={"topic": "SIMA 2 Embodied AI Agents"},
        )

        # Seed brief
        brief_dir = root / "proj_runner_res" / "brief"
        brief_dir.mkdir(parents=True, exist_ok=True)
        import json
        (brief_dir / "brief.json").write_text(json.dumps({"topic": "SIMA 2 Embodied AI Agents"}), encoding="utf-8")

        mock_llm_data = {
            "topic": "SIMA 2 Embodied AI Agents",
            "audience": "general_tech",
            "content_landscape": "Overview of embodied AI.",
            "facts": [
                {"claim": "Fact 1 from official source", "source_ids": ["src_001"], "confidence": 0.95},
                {"claim": "Fact 2 from technical paper", "source_ids": ["src_002"], "confidence": 0.95},
                {"claim": "Fact 3 from industry news", "source_ids": ["src_003"], "confidence": 0.95}
            ],
            "data_points": ["Metric 1"],
            "expert_views": ["View 1"],
            "audience_questions": ["Question 1"],
            "angles_discovered": ["Angle 1", "Angle 2"],
            "risks": ["Risk 1"]
        }

        handler = ResearchHandler(
            source_provider=MockSourceProvider(mock_sources),
            llm_caller=make_mock_llm(mock_llm_data)
        )

        registry = StageRegistry()
        registry.register("research", handler)
        runner = StageRunner(artifact_store=store, registry=registry)

        stage_res = runner.run("research", pipeline_def, state)
        assert stage_res.status == StageResultStatus.READY, f"Message: {stage_res.message}, Errors: {stage_res.errors}"
        assert stage_res.artifact_type == "research_brief"
        assert stage_res.artifact_version == 1

        # Verify artifact exists in ArtifactStore
        loaded = store.load("research_brief", "proj_runner_res", version=1)
        assert loaded.artifact_type == "research_brief"
        assert loaded.artifact_version == 1
        assert len(loaded.data["sources"]) == 3
        assert state.get_active_version("research_brief") == 1
