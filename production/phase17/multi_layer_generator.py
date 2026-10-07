"""Phase 17 Multi-Layer Depth Asset Generator.

Generates 3 distinct transparent depth layers per scene for true Remotion parallax:
- Background Layer (z_index: 0): Distinct environment background (moves slowest in parallax)
- Midground Layer (z_index: 10): Hero kinetic subject with full alpha transparency
- Foreground Layer (z_index: 20): Floating Claude telemetry card / bokeh / framing element (moves fastest in parallax)
"""
from __future__ import annotations

import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from .style_systems import StyleSystem, get_style_system
from .environment_generator import generate_environment_for_scene


def _get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    paths = [
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]
    for p in paths:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    s = hex_str.lstrip("#")
    return int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)


def _draw_titanium_gripper(
    draw_ctx: ImageDraw.ImageDraw,
    cx: int,
    cy: int,
    scale: float = 1.0,
    open_angle: float = 0.0,
    accent_rgb: tuple[int, int, int] = (217, 119, 54),
    border_rgb: tuple[int, int, int] = (45, 55, 72),
):
    """Canonical titanium gripper mechanism for cross-scene object continuity."""
    uw = int(140 * scale)
    uh = int(70 * scale)
    draw_ctx.rectangle(
        [(cx - uw // 2, cy - uh - int(40 * scale)), (cx + uw // 2, cy - int(40 * scale))],
        fill=(35, 42, 56),
        outline=border_rgb,
        width=max(1, int(2 * scale)),
    )
    cw = int(100 * scale)
    ch = int(80 * scale)
    draw_ctx.rectangle(
        [(cx - cw // 2, cy - ch // 2), (cx + cw // 2, cy + ch // 2)],
        fill=(51, 65, 85),
        outline=border_rgb,
        width=max(1, int(2 * scale)),
    )
    ar = max(3, int(10 * scale))
    draw_ctx.ellipse([(cx - ar, cy - ar), (cx + ar, cy + ar)], fill=accent_rgb)

    # Left Jaw
    jaw_l = [
        (cx - int(130 * scale), cy - int(50 * scale)),
        (cx - int(55 * scale), cy - int(50 * scale)),
        (cx - int(45 * scale) - int(open_angle * scale), cy + int(70 * scale)),
        (cx - int(85 * scale) - int(open_angle * scale), cy + int(70 * scale)),
        (cx - int(115 * scale), cy + int(10 * scale)),
    ]
    draw_ctx.polygon(jaw_l, fill=(203, 213, 225), outline=(241, 245, 249))
    draw_ctx.rectangle(
        [(cx - int(53 * scale) - int(open_angle * scale), cy - int(20 * scale)), (cx - int(45 * scale) - int(open_angle * scale), cy + int(65 * scale))],
        fill=accent_rgb,
    )

    # Right Jaw
    jaw_r = [
        (cx + int(130 * scale), cy - int(50 * scale)),
        (cx + int(55 * scale), cy - int(50 * scale)),
        (cx + int(45 * scale) + int(open_angle * scale), cy + int(70 * scale)),
        (cx + int(85 * scale) + int(open_angle * scale), cy + int(70 * scale)),
        (cx + int(115 * scale), cy + int(10 * scale)),
    ]
    draw_ctx.polygon(jaw_r, fill=(203, 213, 225), outline=(241, 245, 249))
    draw_ctx.rectangle(
        [(cx + int(45 * scale) + int(open_angle * scale), cy - int(20 * scale)), (cx + int(53 * scale) + int(open_angle * scale), cy + int(65 * scale))],
        fill=accent_rgb,
    )


def generate_scene_layers(
    scene_index: int,
    narration: str,
    output_dir: Path,
    scene_id: str,
    style: StyleSystem | None = None,
    width: int = 1080,
    height: int = 1920,
) -> dict[str, Path]:
    """Generates and saves the 3 distinct depth layers for a scene:
    Returns dict: {"bg": path, "mid": path, "fg": path}
    """
    st = style or get_style_system()
    output_dir.mkdir(parents=True, exist_ok=True)
    accent_rgb = _hex_to_rgb(st.accent)
    border_rgb = _hex_to_rgb(st.border_color)
    text_rgb = _hex_to_rgb(st.primary_text)
    muted_rgb = _hex_to_rgb(st.secondary_text)

    font_title = _get_font(42, bold=True)
    font_sub = _get_font(24)
    font_badge = _get_font(18, bold=True)
    font_mono = _get_font(20)

    # 1. BACKGROUND LAYER (z_index: 0)
    bg_img = generate_environment_for_scene(scene_index, width, height, st)
    bg_path = output_dir / f"bg_{scene_id}.png"
    bg_img.save(bg_path, "PNG")

    # 2. MIDGROUND LAYER (z_index: 10, Transparent RGBA)
    mid_img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    mid_draw = ImageDraw.Draw(mid_img)

    # 3. FOREGROUND LAYER (z_index: 20, Transparent RGBA)
    fg_img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    fg_draw = ImageDraw.Draw(fg_img)

    # ---------------------------------------------------------------------
    # CLEAN CINEMATIC OVERLAYS (NO CLUTTERED FLOATING CARDS, NO FAKE AI PHOTOS)
    # Background provides unified architectural atmosphere.
    # Midground and foreground supply subtle optical depth cues.
    # ---------------------------------------------------------------------
    if scene_index == 0:
        # Scene 1: Optical Precision Target Reticle in active area
        cx, cy = 540, 880
        rw, b_len = 200, 24
        mid_draw.line([(cx - rw, cy - rw), (cx - rw + b_len, cy - rw)], fill=(*accent_rgb, 255), width=2)
        mid_draw.line([(cx - rw, cy - rw), (cx - rw, cy - rw + b_len)], fill=(*accent_rgb, 255), width=2)
        mid_draw.line([(cx + rw, cy + rw), (cx + rw - b_len, cy + rw)], fill=(*accent_rgb, 255), width=2)
        mid_draw.line([(cx + rw, cy + rw), (cx + rw, cy + rw - b_len)], fill=(*accent_rgb, 255), width=2)
    elif scene_index == 1:
        # Scene 2: High-tech precision alignment crosshair
        cx, cy = 540, 1080
        mid_draw.line([(cx - 30, cy), (cx + 30, cy)], fill=(*accent_rgb, 255), width=2)
        mid_draw.line([(cx, cy - 30), (cx, cy + 30)], fill=(*accent_rgb, 255), width=2)
        mid_draw.ellipse([(cx - 15, cy - 15), (cx + 15, cy + 15)], outline=(*accent_rgb, 255), width=1)
    elif scene_index == 2:
        # Scene 3: Clean waypoint reticle
        cx, cy = 540, 970
        mid_draw.line([(cx - 30, cy), (cx + 30, cy)], fill=(*accent_rgb, 255), width=2)
        mid_draw.line([(cx, cy - 30), (cx, cy + 30)], fill=(*accent_rgb, 255), width=2)
        mid_draw.ellipse([(cx - 45, cy - 45), (cx + 45, cy + 45)], outline=(56, 189, 248, 255), width=1)
    elif scene_index == 3:
        # Scene 4: Floor corridor alignment ticks
        for cx in [320, 540, 760]:
            mid_draw.line([(cx - 15, 1200), (cx + 15, 1200)], fill=(*accent_rgb, 255), width=2)
    else:
        # Scene 5: Keynote stage pedestal crosshair
        cx, cy = width // 2, 700
        mid_draw.line([(cx - 30, cy), (cx + 30, cy)], fill=(*accent_rgb, 255), width=2)
        mid_draw.line([(cx, cy - 30), (cx, cy + 30)], fill=(*accent_rgb, 255), width=2)

    # Foreground: Minimal safe-margin corner registration mark (x: 100, y: 320)
    fg_draw.line([(100, 320), (120, 320)], fill=(255, 255, 255, 255), width=1)
    fg_draw.line([(100, 320), (100, 340)], fill=(255, 255, 255, 255), width=1)

    mid_path = output_dir / f"mid_{scene_id}.png"
    mid_img.save(mid_path, "PNG")

    fg_path = output_dir / f"fg_{scene_id}.png"
    fg_img.save(fg_path, "PNG")

    # Also composite all 3 into the unified primary asset for backwards compatibility
    composite = Image.alpha_composite(bg_img.convert("RGBA"), mid_img)
    composite = Image.alpha_composite(composite, fg_img)
    primary_path = output_dir / f"ast_{scene_id}_primary.png"
    composite.convert("RGB").save(primary_path, "PNG")

    return {
        "bg": bg_path,
        "mid": mid_path,
        "fg": fg_path,
        "primary": primary_path,
    }
