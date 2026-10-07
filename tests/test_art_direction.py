"""Tests for stages/art_direction/art_direction_director.py (ArtDirectionHandler)."""
from pathlib import Path
from tempfile import TemporaryDirectory
import pytest

from schemas.models.artifact import ArtifactEnvelope, ProducerInfo
from schemas.models.common import ProducerKind
from production.artifact_store import ArtifactStore
from production.pipeline_loader import PipelineLoader
from production.state import StateStore
from production.stage_registry import StageResultStatus, StageRegistry
from production.stage_runner import StageRunner
from stages.art_direction.art_direction_director import ArtDirectionHandler


def make_valid_art_direction_response():
    return {
        "design_read": (
            "A high-precision technical telemetry aesthetic blending dark carbon backgrounds "
            "with luminescent cyan diagnostics and industrial schematic overlays."
        ),
        "visual_metaphor": "Server rooms behaving like an industrial power grid under surge load",
        "visual_variance": 8,
        "motion_intensity": 6,
        "information_density": 5,
        "palette_discipline": {
            "primary": "#0F172A",
            "accent_1": "#38BDF8",
            "accent_2": "#F43F5E",
            "neutral": "#64748B",
            "warning": "#F59E0B"
        },
        "typography_personality": "Monospace metric labels paired with bold geometric headlines",
        "layout_language": "Asymmetric multi-panel telemetry grid with split diagnostic feeds",
        "texture_language": "Subtle matte carbon finish with 5% fine grain and scanline pulse",
        "transition_language": "Snap zoom cuts and directional whip-pans with zero cross-dissolves",
        "reference_strategy": "Bloomberg telemetry monitors meet Wired schematic infographics",
        "signature_device": "Pulsing diagnostic telemetry HUD overlay on critical metric beats",
        "anti_patterns": [
            "No floating card in every scene",
            "No identical centered hero composition",
            "No text-only explanation without tangible visual anchor",
            "No generic 3D neon brain animations"
        ],
        "quality_gates": {
            "min_visual_variance": 6
        }
    }


def make_mock_llm(data):
    def _caller(prompt, system=None, **kwargs):
        return data, "gemini", "gemini-2.0-flash", 420
    return _caller


@pytest.fixture
def mock_proposal_envelope():
    from datetime import datetime, timezone
    from schemas.models.common import ArtifactStatus
    now = datetime.now(timezone.utc)
    return ArtifactEnvelope(
        artifact_type="proposal_packet",
        schema_version="2.0",
        artifact_version=1,
        production_id="proj_art_test",
        stage="proposal",
        status=ArtifactStatus.READY,
        created_at=now,
        updated_at=now,
        data={
            "concepts": [
                {
                    "concept_id": "concept_01",
                    "title": "Industrial Power Grid",
                    "hook": "What if an AI cluster consumed as much power as a city?",
                    "visual_direction": "Heavy industrial isometric diagrams",
                    "visual_metaphor": "Server rooms behaving like an industrial power grid under surge load",
                    "narrative_structure": "Hook -> Substation power -> Core compute -> Scale reveal",
                    "renderer_family": "explainer",
                    "render_runtime": "remotion",
                    "composition_mode": "atelier",
                    "tone": "Urgent and physical",
                    "scene_grammar": "Split telemetry HUD",
                    "target_duration": 35.0,
                    "audience_promise": "See the energy cost of AI."
                },
                {
                    "concept_id": "concept_02",
                    "title": "The Paper Trail",
                    "hook": "The secret algorithm behind every chatbot was 17 lines of code.",
                    "narrative_structure": "Whiteboard formula -> Academic trial -> Global infrastructure",
                    "visual_direction": "High-contrast archival documentary",
                    "visual_metaphor": "A single scribbled mathematical theorem igniting a global chain reaction",
                    "renderer_family": "documentary",
                    "render_runtime": "ffmpeg_pil",
                    "composition_mode": "templated",
                    "tone": "Investigative",
                    "scene_grammar": "Archive zoom and paper texture",
                    "target_duration": 35.0,
                    "audience_promise": "The origin story of modern AI."
                }
            ],
            "selected_concept_id": "concept_01",
            "decision_log": {
                "selected_concept_id": "concept_01",
                "actor": "system"
            }
        },
        producer=ProducerInfo(kind=ProducerKind.LLM, provider="openai", model="gpt-4o-mini"),
        content_hash="sha256:" + "1" * 64,
    )


def test_art_direction_handler_blocks_when_missing_proposal():
    with TemporaryDirectory() as td:
        root = Path(td)
        state_store = StateStore(projects_root=root)
        state = state_store.create(
            project_id="proj_art_block",
            pipeline="youtube-short",
            pipeline_version="2.0",
            target_duration=35.0,
        )
        handler = ArtDirectionHandler()
        result = handler.run("art_direction", state, inputs={})
        assert result.status == StageResultStatus.BLOCKED
        assert "missing upstream 'proposal_packet'" in result.message


def test_art_direction_generates_from_proposal_alone(mock_proposal_envelope):
    with TemporaryDirectory() as td:
        root = Path(td)
        state_store = StateStore(projects_root=root)
        state = state_store.create(
            project_id="proj_art_test",
            pipeline="youtube-short",
            pipeline_version="2.0",
            target_duration=35.0,
            metadata={"topic": "AI Energy Crisis"},
        )

        mock_data = make_valid_art_direction_response()
        handler = ArtDirectionHandler(llm_caller=make_mock_llm(mock_data))

        result = handler.run("art_direction", state, inputs={"proposal_packet": mock_proposal_envelope})
        assert result.status == StageResultStatus.READY
        assert result.data["visual_variance"] == 8
        assert result.data["motion_intensity"] == 6
        assert result.data["information_density"] == 5
        assert result.data["visual_metaphor"] == "Server rooms behaving like an industrial power grid under surge load"
        assert len(result.data["anti_patterns"]) >= 3
        assert result.data.get("signature_device") != ""
        assert result.producer.prompt_hash is not None


def test_art_direction_clamps_dials(mock_proposal_envelope):
    with TemporaryDirectory() as td:
        root = Path(td)
        state_store = StateStore(projects_root=root)
        state = state_store.create(
            project_id="proj_art_clamp",
            pipeline="youtube-short",
            pipeline_version="2.0",
            target_duration=35.0,
        )

        mock_data = make_valid_art_direction_response()
        mock_data["visual_variance"] = 12  # Over 10
        mock_data["motion_intensity"] = -2  # Under 1

        handler = ArtDirectionHandler(llm_caller=make_mock_llm(mock_data))
        result = handler.run("art_direction", state, inputs={"proposal_packet": mock_proposal_envelope})

        assert result.status == StageResultStatus.READY
        # Should be clamped to 1..10
        assert result.data["visual_variance"] == 10
        assert result.data["motion_intensity"] == 1


def test_art_direction_stage_runner_persistence(mock_proposal_envelope):
    with TemporaryDirectory() as td:
        root = Path(td)
        store = ArtifactStore(projects_root=root)
        state_store = StateStore(projects_root=root)
        loader = PipelineLoader()
        pipeline_def = loader.load("youtube-short")

        state = state_store.create(
            project_id="proj_art_persist",
            pipeline="youtube-short",
            pipeline_version="2.0",
            target_duration=35.0,
            metadata={"topic": "AI Energy Crisis"},
        )

        # Save proposal_packet to store so dependencies can resolve
        mock_proposal_envelope.production_id = "proj_art_persist"
        mock_proposal_envelope.content_hash = store.compute_hash(mock_proposal_envelope.data)
        store.save(mock_proposal_envelope)
        state.set_active_version("proposal_packet", 1)

        handler = ArtDirectionHandler(llm_caller=make_mock_llm(make_valid_art_direction_response()))
        registry = StageRegistry()
        registry.register("art_direction", handler)

        runner = StageRunner(artifact_store=store, registry=registry)
        stage_res = runner.run("art_direction", pipeline_def, state)

        assert stage_res.status == StageResultStatus.READY
        assert stage_res.artifact_type == "art_direction"
        assert stage_res.artifact_version == 1

        # Check in store
        loaded = store.load("art_direction", "proj_art_persist", version=1)
        assert loaded.data["visual_variance"] == 8
        assert state.get_active_version("art_direction") == 1
