"""Render manifest tests: execution records project into manifests without rendering."""
from pathlib import Path

from composition.remotion.renderer import build_render_manifest, build_render_report


def _log(**overrides):
    log = {
        "production_id": "proj_man",
        "edit_artifact_version": 1,
        "edit_artifact_hash": "sha256:" + "b" * 64,
        "runtime": "remotion",
        "runtime_version": "4.0.0",
        "renderer_family": "cinematic",
        "composition_mode": "atelier",
        "profile": "profiles/youtube_short.json",
        "scenes": ["scene_01", "scene_02"],
        "shots_executed": ["scene_01_shot_01", "scene_02_shot_01"],
        "assets_executed": ["ast_scene_01_primary"],
        "motions_executed": ["emerge", "assemble"],
        "camera_operations": ["reveal_space"],
        "transitions_executed": ["fade"],
        "captions_executed": ["caption_scene_01"],
        "audio_tracks": [{"event_id": "narration_scene_01", "track": "narration", "file": False}],
        "cta_executed": True,
        "warnings": [],
        "errors": [],
    }
    log.update(overrides)
    return log


def test_manifest_records_exact_execution():
    manifest = build_render_manifest(_log())
    assert manifest["shots_executed"] == ["scene_01_shot_01", "scene_02_shot_01"]
    assert manifest["assets_executed"] == ["ast_scene_01_primary"]
    assert manifest["cta_executed"] is True
    assert manifest["edit_artifact_hash"] == "sha256:" + "b" * 64


def test_manifest_never_invents_unexecuted_work():
    manifest = build_render_manifest(_log(shots_executed=[], assets_executed=[], cta_executed=False))
    assert manifest["shots_executed"] == []
    assert manifest["cta_executed"] is False


def test_render_report_conforms_to_schema(tmp_path):
    from datetime import datetime, timezone

    from production.artifact_store import ArtifactStore
    from schemas.models.artifact import ArtifactEnvelope, ProducerInfo
    from schemas.models.common import ArtifactStatus, ProducerKind

    job = {"runtime_id": "remotion", "edit_artifact_version": 1, "edit_artifact_hash": "sha256:" + "c" * 64}
    report = build_render_report(
        job=job, output_path=tmp_path / "final.mp4", duration_rendered=36.88, scenes_rendered=6,
        environment={"node_version": "v22.0.0", "remotion_version": "4.0.0", "os": "linux",
                     "ffmpeg_version": "ffmpeg 7.0", "npm_version": "10.0.0"},
        render_started="2026-10-06T00:00:00+00:00", render_completed="2026-10-06T00:05:00+00:00",
        render_duration_seconds=300.0)
    now = datetime.now(timezone.utc)
    envelope = ArtifactEnvelope(
        artifact_type="render_report", artifact_version=1, production_id="proj_man",
        stage="compose", status=ArtifactStatus.READY, created_at=now, updated_at=now,
        producer=ProducerInfo(kind=ProducerKind.SYSTEM),
        content_hash=ArtifactStore.compute_hash(report), data=report)
    # Same two-pass validation the production store applies at the boundary.
    ArtifactStore(tmp_path).validate(envelope)
    assert report["codec"] == "h264"
    assert report["resolution"] == "1080x1920"
    assert report["fps"] == 30
    assert report["file_size_bytes"] is None
