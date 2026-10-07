"""Phase 17 Visual Style Systems.

Provides dedicated visual identity systems:
- Claude Editorial: Warm charcoal, off-white, restrained terracotta, spacious cards, card morphs
- Apple Keynote: Deep obsidian, razor-sharp speculars, extreme macro, bold hero typography, zoom reveals
- Stripe Motion: Isometric architecture, clean slate, subtle fluid accents, sliding data blocks
- Linear Launch: Dark obsidian, fine hairline borders, glowing accents, snappy tracking
- Bloomberg Graphics: High-contrast technical indices, amber/slate split, tactical telemetry
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class StyleSystemId(str, Enum):
    CLAUDE_EDITORIAL = "claude_editorial"
    APPLE_KEYNOTE = "apple_keynote"
    STRIPE_MOTION = "stripe_motion"
    LINEAR_LAUNCH = "linear_launch"
    BLOOMBERG_GRAPHICS = "bloomberg_graphics"


@dataclass
class StyleSystem:
    system_id: StyleSystemId
    name: str
    description: str
    primary_bg: str
    surface_elevated: str
    primary_text: str
    secondary_text: str
    accent: str
    accent_secondary: str
    border_color: str
    corner_radius: int
    font_family: str
    depth_enabled: bool = True
    lighting_model: str = "key_specular_directional"
    preferred_transitions: list[str] = field(default_factory=lambda: [
        "zoom_transition", "directional_wipe", "object_transition", "motion_blur"
    ])

    def to_dict(self) -> dict[str, Any]:
        return {
            "system_id": self.system_id.value,
            "name": self.name,
            "description": self.description,
            "palette": {
                "primary_bg": self.primary_bg,
                "surface_elevated": self.surface_elevated,
                "primary_text": self.primary_text,
                "secondary_text": self.secondary_text,
                "accent": self.accent,
                "accent_secondary": self.accent_secondary,
                "border": self.border_color,
            },
            "corner_radius": self.corner_radius,
            "font_family": self.font_family,
            "depth_enabled": self.depth_enabled,
            "lighting_model": self.lighting_model,
            "preferred_transitions": self.preferred_transitions,
        }


STYLE_SYSTEMS: dict[StyleSystemId, StyleSystem] = {
    StyleSystemId.CLAUDE_EDITORIAL: StyleSystem(
        system_id=StyleSystemId.CLAUDE_EDITORIAL,
        name="Claude Editorial",
        description="Warm charcoal, spacious typography, restrained terracotta, structured editorial panels",
        primary_bg="#12151C",
        surface_elevated="#1A202C",
        primary_text="#F8FAFC",
        secondary_text="#94A3B8",
        accent="#D97736",
        accent_secondary="#E2E8F0",
        border_color="#2D3748",
        corner_radius=16,
        font_family="Segoe UI, Inter, sans-serif",
    ),
    StyleSystemId.APPLE_KEYNOTE: StyleSystem(
        system_id=StyleSystemId.APPLE_KEYNOTE,
        name="Apple Keynote",
        description="Deep graphite gradient, razor-sharp speculars, extreme macro scale, bold typography",
        primary_bg="#0B0D11",
        surface_elevated="#161A22",
        primary_text="#FFFFFF",
        secondary_text="#86868B",
        accent="#2997FF",
        accent_secondary="#F56300",
        border_color="#2E3440",
        corner_radius=20,
        font_family="SF Pro Display, Segoe UI, sans-serif",
    ),
    StyleSystemId.LINEAR_LAUNCH: StyleSystem(
        system_id=StyleSystemId.LINEAR_LAUNCH,
        name="Linear Product Launch",
        description="Dark obsidian, hairline borders, purple/amber accents, snappy tracking, high density",
        primary_bg="#0E1015",
        surface_elevated="#181B22",
        primary_text="#F2F4F8",
        secondary_text="#8B949E",
        accent="#5E6AD2",
        accent_secondary="#F59E0B",
        border_color="#262A34",
        corner_radius=12,
        font_family="Inter, Segoe UI, sans-serif",
    ),
    StyleSystemId.BLOOMBERG_GRAPHICS: StyleSystem(
        system_id=StyleSystemId.BLOOMBERG_GRAPHICS,
        name="Bloomberg Technical Graphics",
        description="High-contrast technical indices, amber/slate split, tactical telemetry, precise metrics",
        primary_bg="#0A0C10",
        surface_elevated="#141720",
        primary_text="#F0F4F8",
        secondary_text="#718096",
        accent="#F59E0B",
        accent_secondary="#10B981",
        border_color="#28303F",
        corner_radius=8,
        font_family="Consolas, Segoe UI, monospace",
    ),
}


def get_style_system(style_id: str | StyleSystemId | None = None) -> StyleSystem:
    if isinstance(style_id, str):
        try:
            return STYLE_SYSTEMS[StyleSystemId(style_id)]
        except Exception:
            pass
    return STYLE_SYSTEMS[StyleSystemId.CLAUDE_EDITORIAL]
