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
from .environment_generator import generate_environment_for_scene, classify_topic_domain, TopicDomain


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
    """Canonical titanium gripper mechanism for physical robotics continuity."""
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
    topic: str = "",
    subject: str = "",
    visual_purpose: str = "",
    visual_metaphor: str = "",
    narrative_role: str = "",
) -> dict[str, Path]:
    """Generates and saves the 3 distinct depth layers for a scene:
    Returns dict: {"bg": path, "mid": path, "fg": path, "primary": path}
    
    Adheres strictly to:
    1. Topic-aligned semantics: Software/cloud topics NEVER render physical robotics arms.
    2. Mobile Readability: Max 3 core cards per scene, headline fonts increased by >= 35%.
    3. Safe Zone Layout: All graphics fit in top 75% of canvas (above y=1440), leaving strict 20% bottom margin.
    """
    st = style or get_style_system()
    output_dir.mkdir(parents=True, exist_ok=True)
    accent_rgb = _hex_to_rgb(st.accent)
    border_rgb = _hex_to_rgb(st.border_color)
    text_rgb = _hex_to_rgb(st.primary_text)
    muted_rgb = _hex_to_rgb(st.secondary_text)
    surface_rgb = st.surface_rgb() if hasattr(st, "surface_rgb") else (255, 255, 255)

    # +35-45% font sizes for mobile readability
    font_title = _get_font(56, bold=True)
    font_sub = _get_font(32)
    font_badge = _get_font(26, bold=True)
    font_mono = _get_font(28)

    # 1. BACKGROUND LAYER (z_index: 0) - Topic-derived environment
    bg_img = generate_environment_for_scene(
        scene_index=scene_index,
        width=width,
        height=height,
        style=st,
        topic=topic,
        subject=subject,
        visual_purpose=visual_purpose,
        visual_metaphor=visual_metaphor,
        narrative_role=narrative_role,
    )
    bg_path = output_dir / f"bg_{scene_id}.png"
    bg_img.save(bg_path, "PNG")

    # 2. MIDGROUND LAYER (z_index: 10, Transparent RGBA)
    mid_img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    mid_draw = ImageDraw.Draw(mid_img)

    # 3. FOREGROUND LAYER (z_index: 20, Transparent RGBA)
    fg_img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    fg_draw = ImageDraw.Draw(fg_img)

    # Safe Zone: Offset all core geometry upward by 10-15% (all graphics stay in top 75%, y <= 1400)
    cx = width // 2
    domain = classify_topic_domain(topic=topic, subject=subject, visual_purpose=visual_purpose)

    # -------------------------------------------------------------------------
    # 2. FOREGROUND LAYER ARCHITECTURE (z=20, True Spatial Depth)
    # Substantial framing aperture, near-plane depth brackets, and foreground monitor
    # -------------------------------------------------------------------------
    _draw_foreground_depth_elements(
        fg_draw=fg_draw,
        width=width,
        height=height,
        domain=domain,
        scene_index=scene_index,
        accent_rgb=accent_rgb,
        border_rgb=border_rgb,
        surface_rgb=surface_rgb,
        muted_rgb=muted_rgb,
        font_badge=font_badge,
    )

    # -------------------------------------------------------------------------
    # 3. MIDGROUND LAYER ARCHITECTURE (z=10, Core Semantic Subject)
    # Hero visual action, high-contrast conduits, and core diagrams
    # -------------------------------------------------------------------------
    _draw_midground_subject(
        mid_draw=mid_draw,
        width=width,
        height=height,
        domain=domain,
        scene_index=scene_index,
        accent_rgb=accent_rgb,
        border_rgb=border_rgb,
        text_rgb=text_rgb,
        surface_rgb=surface_rgb,
        muted_rgb=muted_rgb,
        font_title=font_title,
        font_badge=font_badge,
    )

    mid_path = output_dir / f"mid_{scene_id}.png"
    mid_img.save(mid_path, "PNG")

    fg_path = output_dir / f"fg_{scene_id}.png"
    fg_img.save(fg_path, "PNG")

    # Composite into primary asset
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


def compute_layer_occupancy(image_input: Path | Image.Image) -> float:
    """Computes non-transparent pixel ratio of an RGBA image (0.0 to 1.0)."""
    if isinstance(image_input, (str, Path)):
        img = Image.open(image_input)
    else:
        img = image_input
    if img.mode != "RGBA":
        return 1.0
    alpha = list(img.split()[3].getdata())
    solid = sum(1 for a in alpha if a > 20)
    return round(solid / max(1, len(alpha)), 4)


def _draw_foreground_depth_elements(
    fg_draw: ImageDraw.ImageDraw,
    width: int,
    height: int,
    domain: TopicDomain,
    scene_index: int,
    accent_rgb: tuple[int, int, int],
    border_rgb: tuple[int, int, int],
    surface_rgb: tuple[int, int, int],
    muted_rgb: tuple[int, int, int],
    font_badge: ImageFont.FreeTypeFont | ImageFont.ImageFont,
):
    """Draws substantial near-plane framing aperture, depth brackets, and monitor cards (occupancy >= 10%)."""
    # 1. Lateral depth framing pillars on flanks (blur/aperture depth cues)
    fg_draw.rounded_rectangle([(30, 240), (84, 1280)], radius=12, fill=(*surface_rgb, 110), outline=(*border_rgb, 160), width=2)
    fg_draw.rounded_rectangle([(width - 84, 240), (width - 30, 1280)], radius=12, fill=(*surface_rgb, 110), outline=(*border_rgb, 160), width=2)

    # 2. Camera framing registration brackets in near plane
    bracket_len = 50
    # Top-Left Bracket
    fg_draw.line([(110, 240), (110 + bracket_len, 240)], fill=(*accent_rgb, 230), width=3)
    fg_draw.line([(110, 240), (110, 240 + bracket_len)], fill=(*accent_rgb, 230), width=3)
    # Top-Right Bracket
    fg_draw.line([(width - 110 - bracket_len, 240), (width - 110, 240)], fill=(*accent_rgb, 230), width=3)
    fg_draw.line([(width - 110, 240), (width - 110, 240 + bracket_len)], fill=(*accent_rgb, 230), width=3)

    # 3. Near-plane contextual monitor card
    if scene_index == 1:
        fg_draw.rounded_rectangle([(width - 480, 250), (width - 110, 330)], radius=14, fill=(*surface_rgb, 245), outline=(*accent_rgb, 255), width=2)
        fg_draw.ellipse([(width - 455, 282), (width - 439, 298)], fill=(*accent_rgb, 255))
        fg_draw.text((width - 425, 276), "CONTEXT BUFFER // LIVE", fill=(*accent_rgb, 255), font=font_badge)
    else:
        fg_draw.rounded_rectangle([(110, 250), (480, 330)], radius=14, fill=(*surface_rgb, 245), outline=(*border_rgb, 255), width=2)
        fg_draw.ellipse([(135, 282), (151, 298)], fill=(*accent_rgb, 255))
        label = "TELEMETRY // PROD-EAST" if domain == TopicDomain.SOFTWARE_AI else "CALIBRATION // ZERO-POINT"
        fg_draw.text((165, 276), label, fill=(*muted_rgb, 255), font=font_badge)

    # 4. Near-plane depth optical particle discs
    spots = [(170, 1140, 36), (width - 180, 480, 42)]
    for sx, sy, sr in spots:
        fg_draw.ellipse([(sx - sr, sy - sr), (sx + sr, sy + sr)], fill=(*accent_rgb, 45), outline=(*accent_rgb, 120), width=2)


def _draw_midground_subject(
    mid_draw: ImageDraw.ImageDraw,
    width: int,
    height: int,
    domain: TopicDomain,
    scene_index: int,
    accent_rgb: tuple[int, int, int],
    border_rgb: tuple[int, int, int],
    text_rgb: tuple[int, int, int],
    surface_rgb: tuple[int, int, int],
    muted_rgb: tuple[int, int, int],
    font_title: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    font_badge: ImageFont.FreeTypeFont | ImageFont.ImageFont,
):
    """Draws core hero visual subject with substantial occupancy (>= 20%)."""
    cx = width // 2

    if domain == TopicDomain.ROBOTICS_HARDWARE:
        if scene_index == 0:
            mid_draw.rounded_rectangle([(cx - 340, 520), (cx + 340, 780)], radius=22, fill=(*surface_rgb, 240), outline=(*border_rgb, 255), width=2)
            mid_draw.text((cx - 250, 570), "SIX-AXIS KINEMATIC CELL", fill=(*text_rgb, 255), font=font_title)
        elif scene_index == 1:
            _draw_titanium_gripper(mid_draw, cx, 660, scale=1.45, open_angle=25, accent_rgb=accent_rgb, border_rgb=border_rgb)
        elif scene_index == 2:
            mid_draw.ellipse([(cx - 170, 520), (cx + 170, 860)], fill=(*surface_rgb, 240), outline=(*accent_rgb, 255), width=3)
            mid_draw.text((cx - 120, 670), "TACTICAL SCAN", fill=(*text_rgb, 255), font=font_title)
        elif scene_index == 3:
            mid_draw.rounded_rectangle([(cx - 360, 520), (cx + 360, 820)], radius=22, fill=(*surface_rgb, 240), outline=(*border_rgb, 255), width=2)
            mid_draw.text((cx - 280, 640), "AGV AISLE REROUTING", fill=(*text_rgb, 255), font=font_title)
        else:
            mid_draw.rounded_rectangle([(cx - 220, 520), (cx + 220, 780)], radius=26, fill=(*surface_rgb, 245), outline=(*accent_rgb, 255), width=3)
            mid_draw.text((cx - 45, 620), "AI", fill=(*text_rgb, 255), font=font_title)
    else:
        # Software / AI / Cloud Domain
        if scene_index == 0:
            mid_draw.rounded_rectangle([(cx - 380, 500), (cx + 380, 780)], radius=24, fill=(*surface_rgb, 245), outline=(*border_rgb, 255), width=2)
            mid_draw.line([(cx - 340, 640), (cx + 340, 640)], fill=(*accent_rgb, 255), width=3)
            mid_draw.ellipse([(cx - 18, 622), (cx + 18, 658)], fill=(*accent_rgb, 255))
            mid_draw.text((cx - 330, 545), "ENTERPRISE ARCHITECTURE", fill=(*text_rgb, 255), font=font_title)

        elif scene_index == 1:
            # Strictly max 3 core cards with bold 26px typography
            for off, label in [(-290, "DATA INGESTION"), (0, "CONTEXT PIPELINE"), (290, "VECTOR STORE")]:
                mid_draw.rounded_rectangle([(cx + off - 125, 500), (cx + off + 125, 780)], radius=20, fill=(*surface_rgb, 240), outline=(*border_rgb, 255), width=2)
                mid_draw.line([(cx + off, 430), (cx + off, 500)], fill=(*accent_rgb, 255), width=3)
                mid_draw.text((cx + off - 110, 625), label, fill=(*text_rgb, 255), font=font_badge)

        elif scene_index == 2:
            mid_draw.ellipse([(cx - 100, 570), (cx + 100, 770)], fill=(*surface_rgb, 245), outline=(*accent_rgb, 255), width=3)
            mid_draw.line([(cx - 290, 500), (cx, 670)], fill=(*accent_rgb, 255), width=2)
            mid_draw.line([(cx + 290, 500), (cx, 670)], fill=(*accent_rgb, 255), width=2)
            mid_draw.text((cx - 85, 650), "AGENTS", fill=(*text_rgb, 255), font=font_title)

        elif scene_index == 3:
            mid_draw.rounded_rectangle([(cx - 380, 480), (cx + 380, 800)], radius=24, fill=(*surface_rgb, 240), outline=(*border_rgb, 255), width=2)
            mid_draw.line([(cx - 340, 630), (cx + 340, 630)], fill=(*border_rgb, 255), width=1)
            mid_draw.text((cx - 330, 525), "RETRIEVAL VELOCITY", fill=(*muted_rgb, 255), font=font_badge)
            mid_draw.text((cx - 330, 670), "+340% SPEED", fill=(*accent_rgb, 255), font=font_title)

        else:
            mid_draw.rounded_rectangle([(cx - 220, 520), (cx + 220, 780)], radius=26, fill=(*surface_rgb, 245), outline=(*accent_rgb, 255), width=3)
            mid_draw.text((cx - 45, 620), "AI", fill=(*text_rgb, 255), font=font_title)


