"""Phase 16 Global Visual Design System & Style Bible (Editorial Intelligence).

Establishes a unified, premium, editorial visual language across the entire video.
Inspired by the restrained, sophisticated design principles of frontier editorial technology communication:
- Intentional negative space and clear foreground/background separation
- Warm, neutral charcoal/slate backgrounds rather than pitch-black voids
- Natural directional lighting and realistic physical materials (brushed titanium, matte polymer, architectural concrete)
- Sophisticated typography hierarchy with zero overlapping elements
- Strict blacklist against "AI slop" clichés: no cyan circuit lines, glowing neural brains, floating random code, or sci-fi HUDs.
"""
from __future__ import annotations

import json
from pathlib import Path
from pydantic import BaseModel, Field


class VisualIdentity(BaseModel):
    overall_style: str = "Editorial Intelligence"
    visual_temperature: str = "balanced_neutral_warm"  # warm undertones, never harsh cold cyan
    realism_level: str = "high_documentary_realism"    # physical material presence
    editorial_character: str = "restrained_authoritative"
    visual_density: str = "spacious_minimalist"        # generous breathing room


class ColorPalette(BaseModel):
    background: str = "#12151C"         # deep warm charcoal (not pure black void)
    surface: str = "#1A202C"            # soft elevated slate surface
    surface_elevated: str = "#242C3D"   # card / container surface
    primary_text: str = "#F8FAFC"       # off-white high contrast readable text
    secondary_text: str = "#94A3B8"     # muted slate for labels and telemetry
    accent: str = "#D97736"             # warm terracotta / amber editorial accent (replaces cyan)
    accent_secondary: str = "#4F709C"   # subdued intelligent steel blue
    border: str = "#2D3748"             # subtle architectural border
    shadow: str = "rgba(0, 0, 0, 0.45)"


class TypographyStyle(BaseModel):
    font_family: str = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
    headline_weight: str = "600"
    body_weight: str = "400"
    metadata_weight: str = "500"
    headline_tracking: str = "-0.02em"
    body_line_height: str = "1.4"
    safe_zone_margin_pct: float = 8.0   # minimum distance from screen edges


class CompositionRules(BaseModel):
    safe_margin_px: int = 64
    subject_zone: str = "center_three_quarter"
    text_zone: str = "bottom_anchor"
    negative_space_ratio: float = 0.40  # minimum 40% clean negative space
    aspect_ratio: str = "9:16"
    width: int = 1080
    height: int = 1920


class LightingRules(BaseModel):
    key_direction: str = "top_left_45"
    contrast_ratio: str = "medium_high_controlled"
    shadow_behavior: str = "soft_directional_falloff"
    highlight_behavior: str = "subtle_matte_specular"  # no blown-out neon glows


class MaterialRules(BaseModel):
    primary: list[str] = Field(default_factory=lambda: [
        "brushed matte titanium",
        "anodized aluminum",
        "matte industrial polymer",
        "clean architectural concrete",
        "frosted optical glass",
    ])
    prohibited: list[str] = Field(default_factory=lambda: [
        "glowing cyan neon lines",
        "abstract floating particles",
        "random binary code rain",
        "glowing transparent neural brains",
        "generic sci-fi HUD crosshairs",
        "pitch-black empty voids with floating wires",
    ])


class GraphicLanguage(BaseModel):
    line_style: str = "refined_subtle_1px"
    border_radius_px: int = 12
    card_style: str = "flat_surface_with_subtle_border"
    diagram_style: str = "clean_editorial_flow"
    ui_style: str = "minimal_restrained_telemetry"


class MotionLanguage(BaseModel):
    camera_movement: str = "motivated_slow_track"      # camera only moves to follow subject or reveal action
    transition_style: str = "clean_hard_cut_or_subtle_dissolve"
    motion_damping: float = 24.0
    motion_stiffness: float = 75.0


class VisualDesignSystem(BaseModel):
    """Canonical visual design system inherited by every scene in a production."""
    version: str = "1.0.0"
    production_id: str = ""
    topic: str = ""
    visual_identity: VisualIdentity = Field(default_factory=VisualIdentity)
    palette: ColorPalette = Field(default_factory=ColorPalette)
    typography: TypographyStyle = Field(default_factory=TypographyStyle)
    composition: CompositionRules = Field(default_factory=CompositionRules)
    lighting: LightingRules = Field(default_factory=LightingRules)
    materials: MaterialRules = Field(default_factory=MaterialRules)
    graphic_language: GraphicLanguage = Field(default_factory=GraphicLanguage)
    motion_language: MotionLanguage = Field(default_factory=MotionLanguage)

    def to_dict(self) -> dict:
        return self.model_dump()

    def generate_style_bible_markdown(self) -> str:
        """Render a human-readable visual style bible document."""
        return f"""# AI SIMPLIFIED LAB — VISUAL STYLE BIBLE
## Art Direction: {self.visual_identity.overall_style}

### 1. Visual Philosophy
- **Style Character**: {self.visual_identity.editorial_character}
- **Visual Temperature**: {self.visual_identity.visual_temperature}
- **Realism Level**: {self.visual_identity.realism_level}
- **Density**: {self.visual_identity.visual_density} (Minimum {int(self.composition.negative_space_ratio*100)}% intentional negative space)

### 2. Color Palette & Surfaces
- **Background**: `{self.palette.background}` (Deep warm charcoal, never an empty pitch-black void)
- **Primary Surface**: `{self.palette.surface}` (Subtle elevated tone)
- **Container / Card**: `{self.palette.surface_elevated}`
- **Primary Text**: `{self.palette.primary_text}` (High contrast readable off-white)
- **Secondary / Labels**: `{self.palette.secondary_text}` (Restrained slate)
- **Primary Accent**: `{self.palette.accent}` (Warm terracotta / amber editorial punch)
- **Secondary Accent**: `{self.palette.accent_secondary}` (Subdued steel blue)

### 3. Composition & Layer Separation
Every frame must maintain strict foreground/background separation:
1. **Background Layer**: Quiet, architectural or studio context with soft light falloff.
2. **Subject Layer**: Primary physical object / interface occupying dominant visual focus.
3. **Supporting Layer**: Restrained labels and data cards placed in designated zones.
4. **Caption Layer**: Bottom anchor with generous padding, zero collision with subjects.

### 4. Permitted & Prohibited Materials
**Permitted Materials**:
{chr(10).join(f"- {m}" for m in self.materials.primary)}

**Strictly Prohibited Clichés**:
{chr(10).join(f"- ❌ {p}" for p in self.materials.prohibited)}

### 5. Camera & Motion Language
- Motion must be purposeful and motivated by subject action (e.g., following movement or revealing a transformation).
- No arbitrary zoom ramps, random jitter, or decorative floating particles.
"""


def create_default_design_system(production_id: str = "", topic: str = "") -> VisualDesignSystem:
    """Instantiate the canonical Editorial Intelligence design system."""
    return VisualDesignSystem(production_id=production_id, topic=topic)
