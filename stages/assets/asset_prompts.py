"""Structured prompt generation for visual asset generation models.

Constructs prompts strictly enforcing:
SUBJECT + ACTION + ENVIRONMENT + COMPOSITION + CAMERA + LIGHT + ART DIRECTION + CONTINUITY + QUALITY + NEGATIVE CONSTRAINTS.
"""
from __future__ import annotations

from typing import Any
from .asset_manifest import AssetItem


DEFAULT_NEGATIVE_PROMPT = (
    "blurry, low quality, distorted, cartoonish, 3D neon brain tropes, generic corporate stock illustration, "
    "watermarks, stock photo watermark, oversaturated purple neon, deformed hands, illegible typography, "
    "floating cards without anchor, vague abstract technology glow"
)


def build_asset_generation_prompt(
    asset_item: AssetItem,
    art_direction: dict[str, Any],
    reference_asset_ids: list[str] | None = None,
) -> tuple[str, str]:
    """Build high-fidelity positive prompt and strict negative constraints for asset generation."""
    subject = asset_item.subject.strip()
    action = asset_item.subject_action.strip()
    environment = asset_item.environment.strip()
    composition = asset_item.composition_requirements.strip()
    camera = asset_item.camera_requirements.strip()
    
    # Palette and lighting discipline from art direction
    palette = art_direction.get("palette_discipline", {})
    primary_color = palette.get("primary", "#0F172A")
    accent_color = palette.get("accent_1", "#38BDF8")
    color_mood = palette.get("mood", "Industrial technical high contrast")
    texture = art_direction.get("texture_language", "Subtle matte finish with 5% fine grain")
    metaphor = art_direction.get("visual_metaphor", "")

    # Lighting description derived from metaphor and colors
    lighting = (
        f"Dramatic cinematic directional lighting with deep shadows, stark highlights in {accent_color}, "
        f"and subtle reflections off metallic surfaces grounded in {primary_color} darkness."
    )

    # Continuity context
    continuity_desc = ""
    if reference_asset_ids:
        continuity_desc = f"Maintains visual identity and architectural consistency with prior anchor {reference_asset_ids[0]}. "
    elif asset_item.continuity_requirements:
        continuity_desc = f"Visual continuity: {asset_item.continuity_requirements}. "

    # Structured formula
    parts = [
        f"SUBJECT: {subject}.",
        f"ACTION & STATE: {action}.",
        f"ENVIRONMENT: {environment}.",
        f"COMPOSITION: {composition}, 9:16 vertical framing.",
        f"CAMERA: {camera} perspective, sharp focal depth.",
        f"LIGHTING & COLOR: {lighting} {color_mood}.",
        f"STYLE & TEXTURE: {texture}, photorealistic technical documentary aesthetic, physical material presence.",
    ]

    if metaphor and metaphor.lower() not in subject.lower():
        parts.append(f"CONCEPTUAL METAPHOR: Grounded in {metaphor}.")

    if continuity_desc:
        parts.append(f"CONTINUITY: {continuity_desc}")

    parts.append("QUALITY: 8k resolution, raw documentary detail, crisp edges, cinematic realism.")

    positive_prompt = " ".join(parts)

    # Negative prompt incorporates art direction anti-patterns
    anti_patterns = art_direction.get("anti_patterns", [])
    anti_str = ", ".join(anti_patterns) if anti_patterns else ""
    negative_prompt = DEFAULT_NEGATIVE_PROMPT
    if anti_str:
        negative_prompt = f"{DEFAULT_NEGATIVE_PROMPT}, {anti_str}"

    return positive_prompt, negative_prompt
