"""Tests for ScenePlanHandler stage execution, blocking rules, and shot coverage."""
import pytest
from datetime import datetime, timezone

from schemas.models.artifact import ArtifactEnvelope, ProducerInfo
from schemas.models.common import ArtifactStatus, ProducerKind
from production.state import StateStore
from production.stage_registry import StageResultStatus
from stages.scene_plan.scene_planner import ScenePlanHandler


@pytest.fixture
def mock_state(tmp_path):
    store = StateStore(projects_root=tmp_path)
    state = store.create(
        project_id="prod_scene_test",
        pipeline="youtube-short",
        pipeline_version="2.0",
        target_duration=45.0,
    )
    state.metadata["topic"] = "How ChatGPT Agents Work"
    return state


@pytest.fixture
def script_envelope():
    return ArtifactEnvelope(
        artifact_type="script",
        schema_version="2.0",
        artifact_version=1,
        production_id="prod_scene_test",
        stage="script",
        status=ArtifactStatus.APPROVED,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        producer=ProducerInfo(kind=ProducerKind.SYSTEM),
        content_hash="sha256:" + "0" * 64,
        data={
            "title": "How ChatGPT Agents Work",
            "target_duration_seconds": 45.0,
            "estimated_duration": 45.0,
            "word_count": 110,
            "sections": [
                {
                    "section_id": "sec_01",
                    "id": "sec_01",
                    "narrative_role": "hook",
                    "spoken_text": "An AI agent isn't just a chatbot; it is an autonomous loop that writes its own tasks.",
                    "estimated_start": 0.0,
                    "estimated_end": 7.0,
                    "duration": 7.0,
                    "visual_intent": "Task graph unfolding like a busy airport control room.",
                    "primary_subject": "Autonomous agent loop",
                },
                {
                    "section_id": "sec_02",
                    "id": "sec_02",
                    "narrative_role": "mechanism",
                    "spoken_text": "When you prompt the agent, it decomposes your request into a directed acyclic graph.",
                    "estimated_start": 7.0,
                    "estimated_end": 20.0,
                    "duration": 13.0,
                    "visual_intent": "Branching task tree dynamically assigning sub-workers.",
                    "primary_subject": "Directed task graph",
                },
                {
                    "section_id": "sec_03",
                    "id": "sec_03",
                    "narrative_role": "evidence",
                    "spoken_text": "Each worker executes tools in parallel, checking results before reporting back.",
                    "estimated_start": 20.0,
                    "estimated_end": 35.0,
                    "duration": 15.0,
                    "visual_intent": "Parallel workers firing API calls and verifying responses.",
                    "primary_subject": "Parallel tool workers",
                },
                {
                    "section_id": "sec_04",
                    "id": "sec_04",
                    "narrative_role": "cta",
                    "spoken_text": "Subscribe to AI Simplified Lab for more breakdowns like this.",
                    "estimated_start": 35.0,
                    "estimated_end": 45.0,
                    "duration": 10.0,
                    "visual_intent": "Channel brand identity and subscriber notification cue.",
                    "primary_subject": "Channel identity",
                },
            ],
        },
    )


@pytest.fixture
def art_direction_envelope():
    return ArtifactEnvelope(
        artifact_type="art_direction",
        schema_version="2.0",
        artifact_version=1,
        production_id="prod_scene_test",
        stage="art_direction",
        status=ArtifactStatus.APPROVED,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        producer=ProducerInfo(kind=ProducerKind.SYSTEM),
        content_hash="sha256:" + "1" * 64,
        data={
            "visual_metaphor": "task graph unfolding like an air traffic control room",
            "visual_variance": 8,
            "motion_intensity": 7,
            "information_density": 6,
            "signature_device": "Dynamic telemetry node trail",
            "anti_patterns": [
                "no floating cards every scene",
                "no text-only explanation without visual anchor",
                "no identical centered hero",
            ],
            "palette_discipline": {"mood": "technical high contrast"},
        },
    )


def test_scene_planner_blocks_on_missing_script(mock_state, art_direction_envelope):
    handler = ScenePlanHandler()
    res = handler.run(
        stage_name="scene_plan",
        state=mock_state,
        inputs={"art_direction": art_direction_envelope},
    )
    assert res.status == StageResultStatus.BLOCKED
    assert "MISSING_UPSTREAM_SCRIPT" in res.errors


def test_scene_planner_blocks_on_missing_art_direction(mock_state, script_envelope):
    handler = ScenePlanHandler()
    res = handler.run(
        stage_name="scene_plan",
        state=mock_state,
        inputs={"script": script_envelope},
    )
    assert res.status == StageResultStatus.BLOCKED
    assert "MISSING_UPSTREAM_ART_DIRECTION" in res.errors


def test_scene_planner_successful_execution(mock_state, script_envelope, art_direction_envelope):
    mock_llm_response = {
        "scenes": [
            {
                "scene_id": "scene_01",
                "type": "animation",
                "script_section_id": "sec_01",
                "start_seconds": 0.0,
                "end_seconds": 7.0,
                "narrative_role": "hook",
                "information_role": "reveal",
                "viewer_understanding": "Viewer grasps that agents are recursive loops rather than static conversational prompt-reply models.",
                "visual_purpose": "establish scale",
                "visual_metaphor": "task graph unfolding like an air traffic control room",
                "subject": "Agent Control Room",
                "subject_action": "Radar-like sweeping beam revealing hierarchical task queues",
                "environment": "Multi-tier control terminal",
                "composition_intent": "wide isometric landscape",
                "camera_intent": "reveal_space",
                "motion_intent": "emerge",
                "visual_technique": "scale_transition",
            },
            {
                "scene_id": "scene_02",
                "type": "diagram",
                "script_section_id": "sec_02",
                "start_seconds": 7.0,
                "end_seconds": 20.0,
                "narrative_role": "mechanism",
                "information_role": "show_process",
                "viewer_understanding": "Viewer visualizes prompt decomposition into a branching directed acyclic graph.",
                "visual_purpose": "show mechanism",
                "visual_metaphor": "task graph unfolding like an air traffic control room",
                "subject": "Directed Task Graph",
                "subject_action": "Single root node splitting into parallel worker branches",
                "environment": "Vector network plane",
                "composition_intent": "split-screen dynamic",
                "camera_intent": "approach_subject",
                "motion_intent": "assemble",
                "visual_technique": "diagram_reveal",
            },
            {
                "scene_id": "scene_03",
                "type": "broll",
                "script_section_id": "sec_03",
                "start_seconds": 20.0,
                "end_seconds": 35.0,
                "narrative_role": "evidence",
                "information_role": "show_evidence",
                "viewer_understanding": "Viewer sees concurrent worker pods querying external tools and validating telemetry.",
                "visual_purpose": "provide evidence",
                "visual_metaphor": "task graph unfolding like an air traffic control room",
                "subject": "Parallel Tool Execution",
                "subject_action": "Telemetry pulses streaming between worker pods and external API gateways",
                "environment": "High-density telemetry dashboard",
                "composition_intent": "macro focal detail",
                "camera_intent": "shift_focus",
                "motion_intent": "flow",
                "visual_technique": "evidence_wall",
            },
            {
                "scene_id": "scene_04",
                "type": "text_card",
                "script_section_id": "sec_04",
                "start_seconds": 35.0,
                "end_seconds": 45.0,
                "narrative_role": "cta",
                "information_role": "conclude",
                "viewer_understanding": "Viewer knows how to continue following the channel and subscribe.",
                "visual_purpose": "Convert attention into subscription.",
                "visual_metaphor": "task graph unfolding like an air traffic control room",
                "subject": "AI Simplified Lab Brand Identity",
                "subject_action": "Subscribing trigger pulse and channel icon assembly",
                "environment": "Clean brand atmosphere",
                "composition_intent": "centered brand focus",
                "camera_intent": "expand_scale",
                "motion_intent": "pulse",
                "visual_technique": "kinetic_typography",
            },
        ]
    }

    def fake_llm(prompt, system=""):
        return mock_llm_response, "mock_provider", "mock_model", 500

    handler = ScenePlanHandler(llm_caller=fake_llm)
    res = handler.run(
        stage_name="scene_plan",
        state=mock_state,
        inputs={
            "script": script_envelope,
            "art_direction": art_direction_envelope,
        },
    )

    assert res.status == StageResultStatus.READY
    assert res.data is not None
    assert "scenes" in res.data
    assert len(res.data["scenes"]) == 4
    assert res.data["variety_score"] >= 70.0

    # Verify shot beat generation coverage
    for sc in res.data["scenes"]:
        assert "shots" in sc
        assert len(sc["shots"]) >= 1
        dur = sc["end_seconds"] - sc["start_seconds"]
        assert sc["shots"][0]["start"] == 0.0
        assert abs(sc["shots"][-1]["end"] - dur) <= 0.05
