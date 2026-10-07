"""Remotion runtime adapter. Materializes validated props and invokes renders; invents nothing."""
from .props_builder import PropsError, build_production_props
from .renderer import (
    build_render_manifest,
    build_render_report,
    compare_frames,
    package_remote_bundle,
)
from .runtime import RemotionRuntime

__all__ = [
    "PropsError",
    "RemotionRuntime",
    "build_production_props",
    "build_render_manifest",
    "build_render_report",
    "compare_frames",
    "package_remote_bundle",
]
