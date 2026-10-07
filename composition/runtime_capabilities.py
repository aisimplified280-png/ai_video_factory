"""Typed capability model for composition runtimes.

Capabilities describe execution ability, not marketing claims. The sets below
are contractual declarations of what each runtime is designed to execute once
available; environment availability is probed separately by diagnostics.py.
A capability being declared never implies the runtime is installed here.
"""
from __future__ import annotations

from typing import Literal

Capability = Literal[
    "html",
    "css",
    "react",
    "svg",
    "canvas",
    "timeline_animation",
    "kinetic_typography",
    "video_layers",
    "image_layers",
    "diagram_layers",
    "masking",
    "blend_modes",
    "camera_transform",
    "parallax",
    "motion_blur",
    "custom_geometry",
    "external_media",
    "audio_sync",
    "caption_layers",
    "remote_render",
    "deterministic_render",
    "headless_browser",
]

CAPABILITY_DESCRIPTIONS: dict[str, str] = {
    "html": "Render HTML documents as composition sources",
    "css": "Apply CSS styling and layout inside compositions",
    "react": "Execute React component trees as composition sources",
    "svg": "Render resolution-independent SVG artwork and motion",
    "canvas": "Execute scripted 2D canvas drawing per frame",
    "timeline_animation": "Evaluate time-based keyframes against edit_decisions timing",
    "kinetic_typography": "Animate text with per-word emphasis and motion",
    "video_layers": "Composite decoded video streams as layers",
    "image_layers": "Composite still images as layers",
    "diagram_layers": "Composite declarative diagrams as layers",
    "masking": "Apply alpha masks between layers",
    "blend_modes": "Composite layers with blend modes",
    "camera_transform": "Apply semantic camera intents as frame transforms",
    "parallax": "Offset layers at different depths for parallax",
    "motion_blur": "Apply motion blur across animated transitions",
    "custom_geometry": "Author arbitrary per-scene geometry",
    "external_media": "Fetch and embed remote media assets",
    "audio_sync": "Align audio streams to timeline events",
    "caption_layers": "Render timed caption layers in safe zones",
    "remote_render": "Execute the composition on remote compute",
    "deterministic_render": "Produce byte-identical output for identical inputs",
    "headless_browser": "Drive a headless browser for web-based composition",
}

# Contractual capability declarations per runtime. These state what the runtime
# is designed to execute, not what is installed on this machine.
DECLARED_CAPABILITIES: dict[str, frozenset[str]] = {
    "remotion": frozenset({
        "html", "css", "react", "svg", "timeline_animation", "kinetic_typography",
        "video_layers", "image_layers", "diagram_layers", "masking", "blend_modes",
        "camera_transform", "parallax", "motion_blur", "custom_geometry",
        "external_media", "audio_sync", "caption_layers", "remote_render",
        "headless_browser",
    }),
    "hyperframes": frozenset({
        "html", "css", "svg", "canvas", "timeline_animation", "kinetic_typography",
        "video_layers", "image_layers", "diagram_layers", "masking", "blend_modes",
        "camera_transform", "parallax", "motion_blur", "custom_geometry",
        "external_media", "audio_sync", "caption_layers", "remote_render",
    }),
    "ffmpeg_pil": frozenset({
        "video_layers", "image_layers", "diagram_layers", "audio_sync",
        "deterministic_render",
    }),
}


def declared_capabilities(runtime_id: str) -> frozenset[str]:
    """Return the contractual capability set for a runtime (empty when unknown)."""
    return DECLARED_CAPABILITIES.get(runtime_id, frozenset())
