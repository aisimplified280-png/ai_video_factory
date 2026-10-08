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

    if domain == TopicDomain.ROBOTICS_HARDWARE:
        # Physical Robotics Domain
        if scene_index == 0:
            # Macro Calibration Station
            mid_draw.rounded_rectangle([(cx - 320, 520), (cx + 320, 760)], radius=20, fill=(*surface_rgb, 240), outline=(*border_rgb, 255), width=2)
            mid_draw.text((cx - 240, 560), "SIX-AXIS KINEMATIC CELL", fill=(*text_rgb, 255), font=font_title)
            fg_draw.rounded_rectangle([(100, 260), (440, 320)], radius=12, fill=(*surface_rgb, 245), outline=(*border_rgb, 255), width=1)
            fg_draw.text((120, 276), "CALIBRATION // ZERO-POINT", fill=(*muted_rgb, 255), font=font_badge)
        elif scene_index == 1:
            # Gantry Industrial Gripper
            _draw_titanium_gripper(mid_draw, cx, 660, scale=1.4, open_angle=25, accent_rgb=accent_rgb, border_rgb=border_rgb)
            fg_draw.rounded_rectangle([(width - 440, 260), (width - 100, 320)], radius=12, fill=(*surface_rgb, 245), outline=(*accent_rgb, 255), width=1)
            fg_draw.text((width - 410, 276), "CLAMP FORCE: 14.8 kN", fill=(*accent_rgb, 255), font=font_badge)
        elif scene_index == 2:
            # Tactical LiDAR Field
            mid_draw.ellipse([(cx - 160, 540), (cx + 160, 860)], fill=(*surface_rgb, 240), outline=(*accent_rgb, 255), width=3)
            mid_draw.text((cx - 110, 680), "TACTICAL SCAN", fill=(*text_rgb, 255), font=font_title)
            fg_draw.rounded_rectangle([(100, 260), (400, 320)], radius=12, fill=(*surface_rgb, 245), outline=(*border_rgb, 255), width=1)
            fg_draw.text((120, 276), "LIDAR POINT CLOUD", fill=(*muted_rgb, 255), font=font_badge)
        elif scene_index == 3:
            # High-Bay Warehouse AGV Rerouting Aisle
            mid_draw.rounded_rectangle([(cx - 340, 540), (cx + 340, 820)], radius=20, fill=(*surface_rgb, 240), outline=(*border_rgb, 255), width=2)
            mid_draw.text((cx - 260, 640), "AGV AISLE REROUTING", fill=(*text_rgb, 255), font=font_title)
            fg_draw.rounded_rectangle([(width - 400, 260), (width - 100, 320)], radius=12, fill=(*surface_rgb, 245), outline=(*border_rgb, 255), width=1)
            fg_draw.text((width - 370, 276), "THROUGHPUT: 98.4%", fill=(*accent_rgb, 255), font=font_badge)
        else:
            mid_draw.rounded_rectangle([(cx - 200, 540), (cx + 200, 780)], radius=24, fill=(*surface_rgb, 245), outline=(*accent_rgb, 255), width=3)
            mid_draw.text((cx - 45, 630), "AI", fill=(*text_rgb, 255), font=font_title)
    else:
        # Software / AI / Cloud Domain (RAG, Bedrock, Agents, Pipelines)
        if scene_index == 0:
            # Scene 1: Central Architecture Gateway (Max 1 core card, large typography)
            mid_draw.rounded_rectangle([(cx - 360, 520), (cx + 360, 780)], radius=22, fill=(*surface_rgb, 245), outline=(*border_rgb, 255), width=2)
            mid_draw.line([(cx - 320, 650), (cx + 320, 650)], fill=(*accent_rgb, 255), width=3)
            mid_draw.ellipse([(cx - 18, 632), (cx + 18, 668)], fill=(*accent_rgb, 255))
            mid_draw.text((cx - 310, 560), "ENTERPRISE ARCHITECTURE", fill=(*text_rgb, 255), font=font_title)
            fg_draw.rounded_rectangle([(100, 260), (440, 320)], radius=12, fill=(*surface_rgb, 245), outline=(*border_rgb, 255), width=1)
            fg_draw.text((120, 276), "GATEWAY // PROD-US-EAST", fill=(*muted_rgb, 255), font=font_badge)

        elif scene_index == 1:
            # Scene 2: Production Data Pipeline (Strictly max 3 core cards, bold typography)
            for off, label in [(-280, "DATA INGESTION"), (0, "CONTEXT PIPELINE"), (280, "VECTOR STORE")]:
                mid_draw.rounded_rectangle([(cx + off - 120, 520), (cx + off + 120, 780)], radius=18, fill=(*surface_rgb, 240), outline=(*border_rgb, 255), width=2)
                mid_draw.line([(cx + off, 450), (cx + off, 520)], fill=(*accent_rgb, 255), width=3)
                mid_draw.text((cx + off - 105, 635), label, fill=(*text_rgb, 255), font=font_badge)
            fg_draw.rounded_rectangle([(width - 440, 260), (width - 100, 320)], radius=12, fill=(*surface_rgb, 245), outline=(*accent_rgb, 255), width=1)
            fg_draw.text((width - 410, 276), "RAG LATENCY < 12MS", fill=(*accent_rgb, 255), font=font_badge)

        elif scene_index == 2:
            # Scene 3: Multi-Agent Orchestration Hub
            mid_draw.ellipse([(cx - 90, 590), (cx + 90, 770)], fill=(*surface_rgb, 245), outline=(*accent_rgb, 255), width=3)
            mid_draw.line([(cx - 280, 520), (cx, 680)], fill=(*accent_rgb, 255), width=2)
            mid_draw.line([(cx + 280, 520), (cx, 680)], fill=(*accent_rgb, 255), width=2)
            mid_draw.text((cx - 75, 665), "AGENTS", fill=(*text_rgb, 255), font=font_title)
            fg_draw.rounded_rectangle([(100, 260), (440, 320)], radius=12, fill=(*surface_rgb, 245), outline=(*border_rgb, 255), width=1)
            fg_draw.text((120, 276), "MULTI-AGENT ORCHESTRATOR", fill=(*muted_rgb, 255), font=font_badge)

        elif scene_index == 3:
            # Scene 4: Enterprise Performance Metrics Card (Max 2 cards)
            mid_draw.rounded_rectangle([(cx - 360, 500), (cx + 360, 800)], radius=22, fill=(*surface_rgb, 240), outline=(*border_rgb, 255), width=2)
            mid_draw.line([(cx - 320, 640), (cx + 320, 640)], fill=(*border_rgb, 255), width=1)
            mid_draw.text((cx - 310, 540), "RETRIEVAL VELOCITY", fill=(*muted_rgb, 255), font=font_badge)
            mid_draw.text((cx - 310, 680), "+340% SPEED", fill=(*accent_rgb, 255), font=font_title)
            fg_draw.rounded_rectangle([(width - 380, 260), (width - 100, 320)], radius=12, fill=(*surface_rgb, 245), outline=(*border_rgb, 255), width=1)
            fg_draw.text((width - 350, 276), "SLA: 99.99%", fill=(*accent_rgb, 255), font=font_badge)

        else:
            # Scene 5: Clean Brand Emblem
            mid_draw.rounded_rectangle([(cx - 200, 540), (cx + 200, 780)], radius=24, fill=(*surface_rgb, 245), outline=(*accent_rgb, 255), width=3)
            mid_draw.text((cx - 45, 630), "AI", fill=(*text_rgb, 255), font=font_title)
            fg_draw.line([(100, 260), (140, 260)], fill=(*accent_rgb, 255), width=2)
            fg_draw.line([(100, 260), (100, 300)], fill=(*accent_rgb, 255), width=2)

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

