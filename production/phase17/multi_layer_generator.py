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
    surface_rgb = st.surface_rgb() if hasattr(st, "surface_rgb") else (255, 255, 255)

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
    # MEANINGFUL MULTI-LAYER DEPTH ARCHITECTURE (ISSUE #3)
    # Background (z=0): Architectural environment and perspective floor.
    # Midground (z=10): Real subject geometry (nodes, conduits, data streams).
    # Foreground (z=20): Floating telemetry tags and camera framing registration.
    # ---------------------------------------------------------------------
    cx = width // 2

    if scene_index == 0:
        # Scene 1: Central Architecture Gateway Bridge Plate
        mid_draw.rounded_rectangle([(cx - 320, 620), (cx + 320, 840)], radius=18, fill=(*surface_rgb, 235), outline=(*border_rgb, 255), width=2)
        mid_draw.line([(cx - 280, 730), (cx + 280, 730)], fill=(*accent_rgb, 255), width=3)
        mid_draw.ellipse([(cx - 16, 714), (cx + 16, 746)], fill=(*accent_rgb, 255))
        mid_draw.text((cx - 220, 650), "ENTERPRISE ARCHITECTURE BRIDGE", fill=(*text_rgb, 255), font=font_mono)
        # Foreground: Top status tag
        fg_draw.rounded_rectangle([(100, 310), (380, 360)], radius=10, fill=(*surface_rgb, 245), outline=(*border_rgb, 255), width=1)
        fg_draw.text((120, 324), "TELEMETRY // PROD-US-EAST", fill=(*muted_rgb, 255), font=font_badge)

    elif scene_index == 1:
        # Scene 2: Production Data Pipeline Stage Channels
        for off, label in [(-260, "DATA INGESTION"), (0, "ETL PIPELINE"), (260, "VECTOR STORE")]:
            mid_draw.rounded_rectangle([(cx + off - 110, 600), (cx + off + 110, 860)], radius=14, fill=(*surface_rgb, 230), outline=(*border_rgb, 255), width=2)
            mid_draw.line([(cx + off, 520), (cx + off, 600)], fill=(*accent_rgb, 255), width=3)
            mid_draw.text((cx + off - 80, 710), label, fill=(*text_rgb, 255), font=font_badge)
        # Foreground: Floating throughput pill
        fg_draw.rounded_rectangle([(width - 380, 310), (width - 100, 360)], radius=10, fill=(*surface_rgb, 245), outline=(*accent_rgb, 255), width=1)
        fg_draw.text((width - 360, 324), "THROUGHPUT: 1.4M T/S", fill=(*accent_rgb, 255), font=font_badge)

    elif scene_index == 2:
        # Scene 3: Multi-Agent Coordination Mesh
        mid_draw.ellipse([(cx - 70, 710), (cx + 70, 850)], fill=(*surface_rgb, 245), outline=(*accent_rgb, 255), width=3)
        mid_draw.line([(cx - 240, 640), (cx, 780)], fill=(*accent_rgb, 255), width=2)
        mid_draw.line([(cx + 240, 640), (cx, 780)], fill=(*accent_rgb, 255), width=2)
        mid_draw.line([(cx - 240, 920), (cx, 780)], fill=(*accent_rgb, 255), width=2)
        mid_draw.line([(cx + 240, 920), (cx, 780)], fill=(*accent_rgb, 255), width=2)
        mid_draw.text((cx - 50, 765), "AGENTS", fill=(*text_rgb, 255), font=font_badge)
        # Foreground: Agent concurrency tag
        fg_draw.rounded_rectangle([(100, 310), (360, 360)], radius=10, fill=(*surface_rgb, 245), outline=(*border_rgb, 255), width=1)
        fg_draw.text((120, 324), "CONCURRENCY: 16 THREADS", fill=(*muted_rgb, 255), font=font_badge)

    elif scene_index == 3:
        # Scene 4: Enterprise Performance Metrics Card
        mid_draw.rounded_rectangle([(cx - 360, 580), (cx + 360, 920)], radius=20, fill=(*surface_rgb, 240), outline=(*border_rgb, 255), width=2)
        mid_draw.line([(cx - 320, 740), (cx + 320, 740)], fill=(*border_rgb, 255), width=1)
        mid_draw.text((cx - 320, 630), "DEPLOYMENT VELOCITY", fill=(*muted_rgb, 255), font=font_badge)
        mid_draw.text((cx - 320, 670), "+340%", fill=(*accent_rgb, 255), font=font_title)
        # Foreground: SLA badge
        fg_draw.rounded_rectangle([(width - 340, 310), (width - 100, 360)], radius=10, fill=(*surface_rgb, 245), outline=(*border_rgb, 255), width=1)
        fg_draw.text((width - 320, 324), "SLA: 99.99% UPTIME", fill=(*accent_rgb, 255), font=font_badge)

    else:
        # Scene 5: Monogram Emblem Plate
        mid_draw.rounded_rectangle([(cx - 180, 620), (cx + 180, 840)], radius=24, fill=(*surface_rgb, 245), outline=(*accent_rgb, 255), width=3)
        mid_draw.text((cx - 45, 700), "AI", fill=(*text_rgb, 255), font=font_title)
        # Foreground: Safe margin corner marks
        fg_draw.line([(100, 320), (130, 320)], fill=(*accent_rgb, 255), width=2)
        fg_draw.line([(100, 320), (100, 350)], fill=(*accent_rgb, 255), width=2)

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
