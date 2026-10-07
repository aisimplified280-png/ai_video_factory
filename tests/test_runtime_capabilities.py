"""Tests for the typed capability model."""
from composition.runtime_capabilities import CAPABILITY_DESCRIPTIONS, declared_capabilities


EXPECTED_CAPABILITIES = {
    "html", "css", "react", "svg", "canvas", "timeline_animation",
    "kinetic_typography", "video_layers", "image_layers", "diagram_layers",
    "masking", "blend_modes", "camera_transform", "parallax", "motion_blur",
    "custom_geometry", "external_media", "audio_sync", "caption_layers",
    "remote_render", "deterministic_render", "headless_browser",
}


def test_capability_catalog_is_complete_and_documented():
    assert set(CAPABILITY_DESCRIPTIONS) == EXPECTED_CAPABILITIES
    assert all(text.strip() for text in CAPABILITY_DESCRIPTIONS.values())


def test_remotion_declares_web_native_execution():
    capabilities = declared_capabilities("remotion")
    assert {"html", "css", "react", "timeline_animation", "remote_render"} <= capabilities


def test_hyperframes_declares_motion_graphics_without_react():
    capabilities = declared_capabilities("hyperframes")
    assert {"html", "css", "svg", "kinetic_typography", "remote_render"} <= capabilities
    assert "react" not in capabilities


def test_legacy_runtime_declares_only_deterministic_local_work():
    capabilities = declared_capabilities("ffmpeg_pil")
    assert capabilities == {"video_layers", "image_layers", "diagram_layers", "audio_sync", "deterministic_render"}


def test_unknown_runtime_declares_nothing():
    assert declared_capabilities("vegas_pro") == frozenset()
