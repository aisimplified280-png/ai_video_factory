"""Tests for production/dependencies.py (dependency locking and downstream invalidation)."""
import json
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from schemas.models.artifact import ProducerInfo
from schemas.models.common import ArtifactStatus, ProducerKind
from production.artifact_store import ArtifactStore
from production.pipeline_loader import PipelineLoader
from production.state import StateStore
from production.dependencies import (
    resolve_dependencies,
    is_artifact_stale,
    find_stale_artifacts,
    invalidate_downstream,
)


@pytest.fixture
def env_fixture():
    with TemporaryDirectory() as td:
        root = Path(td)
        store = ArtifactStore(projects_root=root)
        state_store = StateStore(projects_root=root)
        loader = PipelineLoader()
        pipeline_def = loader.load("youtube-short")
        pid = "proj_dep_test"

        # Create production state
        state = state_store.create(
            project_id=pid,
            pipeline="youtube-short",
            pipeline_version="2.0",
            target_duration=45.0,
        )

        # Seed brief
        brief_dir = root / pid / "brief"
        brief_dir.mkdir(parents=True, exist_ok=True)
        (brief_dir / "brief.json").write_text(json.dumps({"topic": "AI Agents"}), encoding="utf-8")

        yield root, store, state_store, pipeline_def, state


def test_resolve_brief_dependency(env_fixture):
    _, store, _, pipeline_def, state = env_fixture
    locked, blockers = resolve_dependencies("research", pipeline_def, state, store)
    assert blockers == []
    assert len(locked) == 1
    assert locked[0].artifact_type == "brief"
    assert locked[0].content_hash.startswith("sha256:")


def test_missing_upstream_dependency_blocks_stage(env_fixture):
    _, store, _, pipeline_def, state = env_fixture
    # Proposal consumes research_brief, which has not been produced yet
    locked, blockers = resolve_dependencies("proposal", pipeline_def, state, store)
    assert len(blockers) > 0
    assert any("research_brief" in b for b in blockers)
    assert locked == []


def test_dependency_locking_and_staleness_detection(env_fixture):
    root, store, state_store, pipeline_def, state = env_fixture
    pid = state.project_id
    producer = ProducerInfo(kind=ProducerKind.SYSTEM)

    # 1. Produce research_brief v1
    research_data = {
        "topic": "AI Agents",
        "audience": "Developers",
        "sources": [{"title": "Agent overview", "url": "https://example.com"}],
        "facts": ["Agents perceive and act in an environment."],
        "angles_discovered": ["ReAct loop architectures."]
    }
    art_r1 = store.create("research_brief", pid, "research", research_data, producer)
    art_r1.status = ArtifactStatus.APPROVED
    store.save(art_r1)
    state.set_active_version("research_brief", 1)

    # 2. Resolve dependencies for proposal (consumes research_brief)
    locked_refs, blockers = resolve_dependencies("proposal", pipeline_def, state, store)
    assert blockers == []
    assert len(locked_refs) == 1
    assert locked_refs[0].artifact_type == "research_brief"
    assert locked_refs[0].version == 1

    # 3. Create proposal_packet v1 with locked reference to research_brief v1
    proposal_data = {
        "selected_concept_id": "c1",
        "concepts": [
            {
                "concept_id": "c1",
                "hook": "Why AI agents will change software forever.",
                "audience_promise": "Learn modern agent design in 45s.",
                "narrative_structure": "Hook -> Body -> Conclusion",
                "visual_direction": "Cyberpunk UI",
                "tone": "Insightful",
                "target_duration": 45.0,
                "renderer_family": "motion_graphics",
                "render_runtime": "remotion",
                "composition_mode": "atelier"
            },
            {
                "concept_id": "c2",
                "hook": "The anatomy of an autonomous agent.",
                "audience_promise": "Master the loop in 45s.",
                "narrative_structure": "Problem -> Solution -> Code",
                "visual_direction": "Minimalist editorial",
                "tone": "Punchy",
                "target_duration": 45.0,
                "renderer_family": "explainer",
                "render_runtime": "remotion",
                "composition_mode": "atelier"
            }
        ]
    }
    art_p1 = store.create(
        "proposal_packet", pid, "proposal", proposal_data, producer,
        parent_artifacts=locked_refs
    )
    art_p1.status = ArtifactStatus.APPROVED
    store.save(art_p1)
    state.set_active_version("proposal_packet", 1)

    # At this point, proposal v1 is NOT stale
    is_st, reason = is_artifact_stale(art_p1, state, store)
    assert not is_st

    # 4. Now research_brief v2 is created with updated facts
    research_data_v2 = dict(research_data)
    research_data_v2["facts"] = ["Agents with tool use outperform baseline LLMs."]
    art_r2 = store.create("research_brief", pid, "research", research_data_v2, producer)
    art_r2.status = ArtifactStatus.APPROVED
    store.save(art_r2)
    state.set_active_version("research_brief", 2)

    # 5. proposal v1 must now be detected as STALE because active research_brief is v2!
    is_st2, reason2 = is_artifact_stale(art_p1, state, store)
    assert is_st2
    assert "locked v1 != active v2" in reason2

    # 6. find_stale_artifacts identifies proposal_packet
    stale_map = find_stale_artifacts(state, store)
    assert "proposal_packet" in stale_map

    # 7. Invalidation removes proposal_packet from active versions without deleting file
    invalidated = invalidate_downstream("research_brief", pipeline_def, state, store)
    assert "proposal_packet" in invalidated
    assert state.get_active_version("proposal_packet") is None
    # Artifact file still exists on disk for auditability
    assert store.exists("proposal_packet", pid, version=1)
