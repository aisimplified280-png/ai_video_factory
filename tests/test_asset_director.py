"""Unit and integration tests for stages/assets/asset_director.py (AssetHandler)."""
import json
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from datetime import datetime, timezone
from schemas.models.artifact import ArtifactEnvelope, ProducerInfo
from schemas.models.common import ArtifactStatus, ProducerKind
from production.state import StateStore, BudgetState
from production.stage_registry import StageResultStatus
from stages.assets.asset_director import AssetHandler
from stages.assets.providers import MockAssetProvider


@pytest.fixture
def mock_scene_plan_envelope():
    now = datetime.now(timezone.utc)
    return ArtifactEnvelope(
        artifact_type="scene_plan",
        artifact_version=1,
        production_id="proj_test_assets",
        stage="scene_plan",
        status=ArtifactStatus.APPROVED,
        created_at=now,
        updated_at=now,
        content_hash="sha256:1111111111111111111111111111111111111111111111111111111111111111",
        producer=ProducerInfo(kind=ProducerKind.TOOL),
        data={
            "scenes": [
                {
                    "scene_id": "scene_01",
                    "type": "broll",
                    "narrative_role": "hook",
                    "visual_technique": "cinematic_broll",
                    "viewer_understanding": "Viewer sees an industrial high-voltage transformer overload with glowing coils.",
                    "visual_purpose": "establish scale",
                    "subject": "Industrial power transformer",
                    "subject_action": "Overloading with red-hot copper coils under surge demand",
                    "environment": "Dark industrial facility with massive metallic conduits",
                    "composition_intent": "wide low-angle perspective",
                    "camera_intent": "approach_subject",
                    "motion_intent": "pulse",
                    "start_seconds": 0.0,
                    "end_seconds": 7.0,
                },
                {
                    "scene_id": "scene_02",
                    "type": "diagram",
                    "narrative_role": "mechanism",
                    "visual_technique": "system_assembly",
                    "viewer_understanding": "Viewer sees request routing crossbar distributing compute across nodes.",
                    "visual_purpose": "show mechanism",
                    "subject": "Neural routing crossbar",
                    "subject_action": "Distributing compute requests across cluster nodes",
                    "environment": "Schematic blueprint technical plane",
                    "composition_intent": "split-screen dynamic",
                    "camera_intent": "shift_focus",
                    "motion_intent": "connect",
                    "start_seconds": 7.0,
                    "end_seconds": 16.0,
                },
                {
                    "scene_id": "scene_03",
                    "type": "text_card",
                    "narrative_role": "cta",
                    "visual_technique": "kinetic_typography",
                    "viewer_understanding": "Viewer knows how to continue following the channel and subscribe.",
                    "visual_purpose": "Convert attention into subscription.",
                    "subject": "AI Simplified Lab Brand Identity",
                    "subject_action": "Pulsing subscription CTA cue and channel logo reveal",
                    "environment": "Dark brushed metallic workspace slate",
                    "composition_intent": "centered brand focus",
                    "camera_intent": "observe_static",
                    "motion_intent": "pulse",
                    "start_seconds": 16.0,
                    "end_seconds": 20.0,
                },
            ]
        },
    )


@pytest.fixture
def mock_art_direction_envelope():
    now = datetime.now(timezone.utc)
    return ArtifactEnvelope(
        artifact_type="art_direction",
        artifact_version=1,
        production_id="proj_test_assets",
        stage="art_direction",
        status=ArtifactStatus.APPROVED,
        created_at=now,
        updated_at=now,
        content_hash="sha256:2222222222222222222222222222222222222222222222222222222222222222",
        producer=ProducerInfo(kind=ProducerKind.TOOL),
        data={
            "design_read": "High-contrast technical documentary with physical machinery metaphors.",
            "visual_metaphor": "industrial power grid under load",
            "visual_variance": 8,
            "motion_intensity": 7,
            "palette_discipline": {
                "primary": "#0A0D14",
                "accent_1": "#00FF88",
                "text": "#F0F4FC",
                "mood": "industrial technical",
            },
            "anti_patterns": ["no floating cards", "no generic 3D neon brain"],
        },
    )


def test_asset_handler_execution(tmp_path, mock_scene_plan_envelope, mock_art_direction_envelope):
    state_store = StateStore(projects_root=tmp_path)
    state = state_store.create(
        project_id="proj_test_assets",
        pipeline="youtube-short",
        pipeline_version="2.0",
        target_duration=20.0,
        aspect_ratio="9:16",
        platform="youtube_shorts",
    )

    handler = AssetHandler(use_mock=True)

    inputs = {
        "scene_plan": mock_scene_plan_envelope,
        "art_direction": mock_art_direction_envelope,
    }

    res = handler.run(
        stage_name="assets",
        state=state,
        inputs=inputs,
        projects_root=str(tmp_path),
    )

    assert res.status == StageResultStatus.READY
    assert "assets" in res.data
    assets = res.data["assets"]
    assert len(assets) == 3

    # Check that media types are diverse
    media_types = {a["type"] for a in assets}
    assert len(media_types) >= 2  # Mix of diagram, logo, and image/video

    # Check contact sheet and report generation
    assets_dir = tmp_path / "proj_test_assets" / "assets"
    assert (assets_dir / "contact_sheet.html").exists()
    assert (assets_dir / "asset_review_report.json").exists()
    assert (assets_dir / "asset_generation_report.json").exists()

    # Check individual asset files exist on disk
    for a in assets:
        fpath = Path(a["file_path"])
        assert fpath.exists()
        assert a["status"] in ("ready", "needs_review")


def test_anti_template_semantic_differences(mock_scene_plan_envelope, mock_art_direction_envelope, tmp_path):
    """Section 41 Anti-Template Test: confirm scenes differ in subject, composition, environment, camera, and type."""
    state_store = StateStore(projects_root=tmp_path)
    state = state_store.create(
        project_id="proj_test_anti_template",
        pipeline="youtube-short",
        pipeline_version="2.0",
        target_duration=20.0,
        aspect_ratio="9:16",
        platform="youtube_shorts",
    )

    handler = AssetHandler(use_mock=True)
    inputs = {
        "scene_plan": mock_scene_plan_envelope,
        "art_direction": mock_art_direction_envelope,
    }
    res = handler.run(
        stage_name="assets",
        state=state,
        inputs=inputs,
        projects_root=str(tmp_path),
    )
    assets = res.data["assets"]

    # Compare scene 1 vs scene 2 vs scene 3
    s1, s2, s3 = assets[0], assets[1], assets[2]

    # Subjects must differ
    assert s1["subject"] != s2["subject"] != s3["subject"]
    # Environments must differ
    assert s1["environment"] != s2["environment"] != s3["environment"]
    # Compositions must differ
    assert s1["composition_requirements"] != s2["composition_requirements"] != s3["composition_requirements"]
    # Media types must differ
    assert len({s1["type"], s2["type"], s3["type"]}) >= 2


def test_asset_handler_blocked_on_missing_scene_plan(tmp_path):
    state_store = StateStore(projects_root=tmp_path)
    state = state_store.create(
        project_id="proj_test_missing_sp",
        pipeline="youtube-short",
        pipeline_version="2.0",
        target_duration=20.0,
        aspect_ratio="9:16",
        platform="youtube_shorts",
    )
    handler = AssetHandler(use_mock=True)
    res = handler.run(
        stage_name="assets",
        state=state,
        inputs={},
        projects_root=str(tmp_path),
    )
    assert res.status == StageResultStatus.BLOCKED
    assert "MISSING_UPSTREAM_SCENE_PLAN" in res.errors
