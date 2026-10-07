"""Tests for production/controller.py (ProductionController)."""
import json
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from schemas.models.artifact import ProducerInfo
from schemas.models.common import ArtifactStatus, ProductionStatus, ProducerKind
from production.controller import ProductionController, ProductionAbortedError
from production.stage_registry import (
    StageRegistry,
    StageHandlerResult,
    StageResultStatus,
)


class DummyResearchHandler:
    def run(self, stage_name, state, inputs, **kwargs):
        return StageHandlerResult(
            status=StageResultStatus.READY,
            data={
                "topic": "AI Architecture",
                "audience": "Engineers",
                "sources": [
                    {"title": "Paper 1", "url": "https://example.com/1"},
                    {"title": "Paper 2", "url": "https://example.com/2"},
                    {"title": "Paper 3", "url": "https://example.com/3"}
                ],
                "facts": ["Fact A", "Fact B"],
                "angles_discovered": ["Angle 1"]
            },
            producer=ProducerInfo(kind=ProducerKind.TOOL),
        )


class DummyProposalHandler:
    def run(self, stage_name, state, inputs, **kwargs):
        return StageHandlerResult(
            status=StageResultStatus.READY,
            data={
                "selected_concept_id": "c1",
                "concepts": [
                    {
                        "concept_id": "c1",
                        "hook": "What is the secret of neural video production?",
                        "audience_promise": "Find out in 45 seconds.",
                        "narrative_structure": "Hook -> Details",
                        "visual_direction": "High tech editorial",
                        "tone": "Authoritative",
                        "target_duration": 45.0,
                        "renderer_family": "motion_graphics",
                        "render_runtime": "remotion",
                        "composition_mode": "atelier"
                    },
                    {
                        "concept_id": "c2",
                        "hook": "Why template video factories fail.",
                        "audience_promise": "Avoid the templating trap.",
                        "narrative_structure": "Problem -> Solution",
                        "visual_direction": "Documentary",
                        "tone": "Analytical",
                        "target_duration": 45.0,
                        "renderer_family": "explainer",
                        "render_runtime": "remotion",
                        "composition_mode": "atelier"
                    }
                ]
            },
            producer=ProducerInfo(kind=ProducerKind.TOOL),
        )


@pytest.fixture
def controller_fixture():
    with TemporaryDirectory() as td:
        root = Path(td)
        registry = StageRegistry()
        controller = ProductionController(projects_root=root, registry=registry)
        yield root, registry, controller


def test_start_production_creates_state_and_brief(controller_fixture):
    root, _, controller = controller_fixture
    state = controller.start(
        topic="Modern Agent Architecture",
        pipeline="youtube-short",
        options={"target_duration": 45.0}
    )

    assert state.project_id.startswith("proj_")
    assert state.status == ProductionStatus.CREATED
    assert state.current_stage == "research"
    assert (root / state.project_id / "brief" / "brief.json").exists()

    # Verify checkpoint and audit log
    chk_store = controller._get_checkpoint_store(state.project_id)
    chks = chk_store.list_checkpoints()
    assert len(chks) >= 1
    assert chks[0].event_type == "production_created"

    audit_log = controller._get_audit_log(state.project_id)
    evts = audit_log.list_events()
    assert len(evts) >= 1
    assert evts[0].event_type == "production_created"


def test_unimplemented_stage_marks_production_blocked(controller_fixture):
    _, _, controller = controller_fixture
    state = controller.start(topic="AI Agents", pipeline="youtube-short")
    result = controller.run_next_stage(state.project_id)

    assert result.status == StageResultStatus.NOT_IMPLEMENTED
    reloaded = controller.state_store.load(state.project_id)
    assert reloaded.status == ProductionStatus.BLOCKED
    assert len(reloaded.warnings) >= 1
    assert reloaded.warnings[0].code == "STAGE_NOT_IMPLEMENTED"


def test_auto_approval_and_human_approval_flow(controller_fixture):
    _, registry, controller = controller_fixture
    registry.register("research", DummyResearchHandler())
    registry.register("proposal", DummyProposalHandler())

    # In GUIDED run_mode, stages configured with approval: human pause for human review
    state = controller.start(
        topic="AI Agents",
        pipeline="youtube-short",
        options={"run_mode": "guided"}
    )

    # 1. Run research (youtube-short approval_policy for research is AUTO)
    res_research = controller.run_next_stage(state.project_id)
    assert res_research.status == StageResultStatus.READY

    st_after_research = controller.state_store.load(state.project_id)
    # Research auto-approved, so current stage advanced to proposal
    assert st_after_research.current_stage == "proposal"
    assert st_after_research.get_active_version("research_brief") == 1

    # 2. Run proposal (youtube-short approval_policy for proposal is HUMAN)
    res_proposal = controller.run_next_stage(state.project_id)
    assert res_proposal.status == StageResultStatus.WAITING_APPROVAL

    st_after_proposal = controller.state_store.load(state.project_id)
    assert st_after_proposal.status == ProductionStatus.WAITING_APPROVAL
    assert st_after_proposal.current_stage == "proposal"

    # 3. Explicit human approval
    st_approved = controller.approve(state.project_id, stage_name="proposal", actor="director_alice")
    assert st_approved.status == ProductionStatus.RUNNING
    assert st_approved.current_stage == "script"


def test_rejection_triggers_revision_and_invalidates_downstream(controller_fixture):
    _, registry, controller = controller_fixture
    registry.register("research", DummyResearchHandler())
    registry.register("proposal", DummyProposalHandler())

    state = controller.start(
        topic="AI Agents",
        pipeline="youtube-short",
        options={"run_mode": "guided"}
    )
    controller.run_next_stage(state.project_id)  # research ready/approved
    controller.run_next_stage(state.project_id)  # proposal waiting_approval

    # Rejection of proposal
    st_rejected = controller.reject(
        state.project_id, stage_name="proposal", reason="Hook needs more urgency", actor="editor_bob"
    )
    assert st_rejected.status == ProductionStatus.BLOCKED
    assert st_rejected.current_stage == "proposal"
    assert st_rejected.get_revision_count("proposal") == 1

    # Audit log reflects rejection
    audit = controller._get_audit_log(state.project_id)
    reject_events = audit.list_events(event_type="artifact_rejected")
    assert len(reject_events) == 1
    assert "Hook needs more urgency" in reject_events[0].details["reason"]


def test_crash_simulation_and_recovery(controller_fixture):
    """Simulate crash during production: approved stages remain valid, next stage resumes."""
    _, registry, controller = controller_fixture
    registry.register("research", DummyResearchHandler())

    state = controller.start(topic="NeRFs", pipeline="youtube-short")
    controller.run_next_stage(state.project_id)  # research completed & approved

    # Simulate abrupt process crash by creating a brand new controller instance
    # pointing to the same storage
    recovered_controller = ProductionController(
        projects_root=controller.projects_root,
        registry=registry,
    )

    resumed_state = recovered_controller.resume(state.project_id)
    # Research artifact is intact and approved
    assert resumed_state.get_active_version("research_brief") == 1
    # Current stage is correctly determined to be proposal
    assert resumed_state.current_stage == "proposal"


def test_idempotent_execution(controller_fixture):
    _, registry, controller = controller_fixture
    registry.register("research", DummyResearchHandler())

    state = controller.start(topic="NeRFs", pipeline="youtube-short")
    res1 = controller.run_next_stage(state.project_id)
    assert res1.status == StageResultStatus.READY
    assert res1.artifact_version == 1

    # Calling run_next_stage again does NOT recreate research v1; it advances to proposal
    res2 = controller.run_next_stage(state.project_id)
    # proposal is not implemented
    assert res2.stage == "proposal"
    assert res2.status == StageResultStatus.NOT_IMPLEMENTED


def test_abort_production(controller_fixture):
    _, _, controller = controller_fixture
    state = controller.start(topic="AI Agents", pipeline="youtube-short")

    aborted_state = controller.abort(state.project_id, reason="Topic obsolete")
    assert aborted_state.status == ProductionStatus.ABORTED

    # Running next stage on aborted production is blocked
    res = controller.run_next_stage(state.project_id)
    assert res.status == StageResultStatus.BLOCKED
    assert "is aborted" in res.message

    # Resuming aborted production raises ProductionAbortedError
    with pytest.raises(ProductionAbortedError):
        controller.resume(state.project_id)


def test_rerender_planning(controller_fixture):
    _, _, controller = controller_fixture
    state = controller.start(topic="Rerender Test", pipeline="youtube-short")

    # Before edit_decisions exists, rerender is blocked
    plan = controller.rerender(state.project_id)
    assert plan["status"] == "blocked"
    assert "No active 'edit_decisions'" in plan["reason"]
