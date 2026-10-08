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


def test_render_report_derives_properties_from_different_profiles(tmp_path):
    """Verify render report reflects different platform profiles without hardcoded values."""
    job_landscape = {
        "runtime_id": "remotion",
        "platform_profile": "profiles/youtube_landscape.json",
        "edit_artifact_version": 1,
        "edit_artifact_hash": "sha256:" + "d" * 64,
    }
    report_land = build_render_report(
        job=job_landscape,
        output_path=tmp_path / "landscape.mp4",
        duration_rendered=60.0,
        scenes_rendered=4,
        environment={"os": "linux"},
        render_started="2026-10-06T00:00:00+00:00",
        render_completed="2026-10-06T00:01:00+00:00",
    )
    assert report_land["resolution"] == "1920x1080"
    assert report_land["fps"] == 60
    assert report_land["codec"] == "h264"

    # Profile passed explicitly
    custom_profile = {
        "id": "square_hd",
        "resolution": {"width": 1080, "height": 1080},
        "fps": 24,
        "codec": "hevc",
    }
    report_sq = build_render_report(
        job={"runtime_id": "remotion"},
        output_path=tmp_path / "square.mp4",
        duration_rendered=15.0,
        scenes_rendered=2,
        environment={"os": "linux"},
        render_started="2026-10-06T00:00:00+00:00",
        render_completed="2026-10-06T00:01:00+00:00",
        profile=custom_profile,
    )
    assert report_sq["resolution"] == "1080x1080"
    assert report_sq["fps"] == 24
    assert report_sq["codec"] == "hevc"


def test_render_report_probe_output_is_authoritative_over_metadata(tmp_path):
    """The render report must NEVER claim values that differ from the encoded MP4 probe."""
    fake_probe = {
        "streams": [
            {
                "codec_type": "video",
                "codec_name": "vp9",
                "width": 2560,
                "height": 1440,
                "r_frame_rate": "60/1",
            },
            {
                "codec_type": "audio",
                "codec_name": "aac",
            },
        ]
    }
    # Even if job metadata claims h264 at 1080x1920 @ 30fps
    job = {
        "runtime_id": "remotion",
        "codec": "h264",
        "resolution": "1080x1920",
        "fps": 30,
        "platform_profile": "profiles/youtube_short.json",
    }
    report = build_render_report(
        job=job,
        output_path=tmp_path / "probed.mp4",
        duration_rendered=30.0,
        scenes_rendered=3,
        environment={"os": "linux"},
        render_started="2026-10-06T00:00:00+00:00",
        render_completed="2026-10-06T00:01:00+00:00",
        probe=fake_probe,
    )
    # Probe output is authoritative
    assert report["codec"] == "vp9"
    assert report["resolution"] == "2560x1440"
    assert report["fps"] == 60
    assert report["audio_present"] is True

