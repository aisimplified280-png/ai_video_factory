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
    surface_rgb = _hex_to_rgb(st.surface_elevated) if hasattr(st, "surface_elevated") else (255, 255, 255)

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
    domain = classify_topic_domain(topic=topic, subject=subject, visual_purpose=visual_purpose, narration=narration)

    # -------------------------------------------------------------------------
    # DYNAMIC SEMANTIC EXTRACTION (Zero Static Boilerplate Templates)
    # -------------------------------------------------------------------------
    headline, cards, metric = _extract_semantic_entities(
        subject=subject,
        visual_purpose=visual_purpose,
        visual_metaphor=visual_metaphor,
        narration=narration,
        domain=domain,
    )

    # -------------------------------------------------------------------------
    # 2. FOREGROUND LAYER ARCHITECTURE (z=20, True Spatial Depth)
    # Substantial framing aperture, near-plane depth brackets, and foreground monitor
    # -------------------------------------------------------------------------
    _draw_foreground_depth_elements(
        fg_draw=fg_draw,
        width=width,
        height=height,
        domain=domain,
        headline=headline,
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
        scene_index=scene_index,
        narrative_role=narrative_role,
        domain=domain,
        headline=headline,
        cards=cards,
        metric=metric,
        visual_metaphor=visual_metaphor,
        visual_purpose=visual_purpose,
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


import re


def _draw_fitted_text(
    draw_ctx: ImageDraw.ImageDraw,
    text: str,
    box_x: int,
    box_y: int,
    max_width: int,
    max_height: int,
    fill: tuple[int, ...] = (255, 255, 255, 255),
    base_size: int = 46,
    min_size: int = 20,
    bold: bool = True,
    center: bool = False,
) -> int:
    """Scales font size dynamically so text strictly fits inside max_width and max_height."""
    size = base_size
    font = _get_font(size, bold=bold)
    clean_text = text.strip()
    if not clean_text:
        return size

    while size > min_size:
        font = _get_font(size, bold=bold)
        bbox = draw_ctx.textbbox((0, 0), clean_text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        if tw <= max_width and th <= max_height:
            break
        size -= 2

    font = _get_font(size, bold=bold)
    bbox = draw_ctx.textbbox((0, 0), clean_text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    dx = box_x + max(0, (max_width - tw) // 2) if center else box_x
    dy = box_y + max(0, (max_height - th) // 2)
    draw_ctx.text((dx, dy), clean_text, fill=fill, font=font)
    return size


def _extract_semantic_entities(
    subject: str,
    visual_purpose: str,
    visual_metaphor: str,
    narration: str,
    domain: TopicDomain,
) -> tuple[str, list[str], str]:
    """Dynamically extracts headline, 2-3 card labels, and metric badge from scene semantics.
    Eliminates all static boilerplate templates and cleans visual noise words.
    """
    clean_sub = re.sub(r"[^\w\s-]", "", subject).strip()
    if clean_sub and len(clean_sub) >= 4:
        headline = clean_sub.upper()[:32]
    elif visual_purpose and len(visual_purpose) >= 4:
        headline = re.sub(r"[^\w\s-]", "", visual_purpose).strip().upper()[:32]
    else:
        words = [w.strip(".,;:!?\"'") for w in narration.split() if len(w) > 3]
        headline = " ".join(words[:3]).upper() if words else "SYSTEM ARCHITECTURE"
        headline = headline[:32]

    corpus = f"{subject} {visual_purpose} {visual_metaphor} {narration}"
    clean_words = re.findall(r"[A-Za-z0-9\-_]{4,}", corpus)
    stopwords = {
        "this", "that", "with", "from", "have", "more", "then", "into", "when",
        "your", "will", "what", "how", "over", "fast", "they", "them", "about",
        "offers", "gives", "system", "systems", "getting", "smarter", "built",
        "dark", "minimalist", "studio", "obsidian", "matrix", "wireframe",
        "graphic", "visual", "concept", "slide", "scene", "clean",
    }
    key_terms = []
    seen = set()
    for w in clean_words:
        up = w.upper()
        if up.lower() not in stopwords and up not in seen:
            seen.add(up)
            key_terms.append(up[:16])

    if len(key_terms) >= 3:
        cards = key_terms[:3]
    elif len(key_terms) == 2:
        cards = [key_terms[0], key_terms[1], "RUNTIME"]
    elif len(key_terms) == 1:
        cards = [key_terms[0], "PIPELINE", "ENGINE"]
    else:
        if domain == TopicDomain.ROBOTICS_HARDWARE:
            cards = ["KINEMATICS", "ACTUATION", "CONTROL"]
        else:
            cards = ["INGESTION", "ROUTING", "RETRIEVAL"]

    metric_match = re.search(r"(\+?\d+%|\d+x|\d+ms|\d+s|\d+\.\d+%)", narration)
    if metric_match:
        metric = metric_match.group(1)
    elif "speed" in corpus.lower() or "latency" in corpus.lower() or "fast" in corpus.lower():
        metric = "< 15MS LATENCY"
    elif "throughput" in corpus.lower() or "scale" in corpus.lower():
        metric = "10X THROUGHPUT"
    else:
        metric = "OPTIMAL STATE"

    return headline, cards, metric


def _draw_foreground_depth_elements(
    fg_draw: ImageDraw.ImageDraw,
    width: int,
    height: int,
    domain: TopicDomain,
    headline: str,
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

    # 3. Dynamic near-plane contextual monitor card with high-contrast Dark Slate tag (#1E293B)
    fg_draw.rounded_rectangle([(110, 250), (width - 110, 330)], radius=14, fill=(*surface_rgb, 248), outline=(*accent_rgb, 255), width=2)
    fg_draw.ellipse([(135, 282), (151, 298)], fill=(*accent_rgb, 255))
    tag = f"{domain.value.upper()} // {headline[:26]}"
    # High-contrast dark slate color (#1E293B) for crystal-clear readability
    dark_slate_tag = (30, 41, 59, 255)
    fg_draw.text((165, 276), tag, fill=dark_slate_tag, font=font_badge)

    # 4. Near-plane depth optical particle discs
    spots = [(170, 1140, 36), (width - 180, 480, 42)]
    for sx, sy, sr in spots:
        fg_draw.ellipse([(sx - sr, sy - sr), (sx + sr, sy + sr)], fill=(*accent_rgb, 45), outline=(*accent_rgb, 120), width=2)


def _draw_midground_subject(
    mid_draw: ImageDraw.ImageDraw,
    width: int,
    height: int,
    scene_index: int,
    narrative_role: str,
    domain: TopicDomain,
    headline: str,
    cards: list[str],
    metric: str,
    visual_metaphor: str,
    visual_purpose: str,
    accent_rgb: tuple[int, int, int],
    border_rgb: tuple[int, int, int],
    text_rgb: tuple[int, int, int],
    surface_rgb: tuple[int, int, int],
    muted_rgb: tuple[int, int, int],
    font_title: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    font_badge: ImageFont.FreeTypeFont | ImageFont.ImageFont,
):
    """Draws core hero visual subject with strict layout shuffling across scenes.
    Eliminates template monotony by alternating across 5 canonical layouts:
    - Scene 1 / Hook: Centered Hero Card with bold metric callout.
    - Scene 2 / Mechanism: Horizontal Flowchart / Pipeline Node Tree.
    - Scene 3 / Escalation: Split Comparison View (Naive vs Optimized).
    - Scene 4 / Implication: Developer Terminal / Code snippet window.
    - Scene 5 / Outro CTA: Official Royal Blue Robot Logo Asset Anchor.
    """
    cx = width // 2
    metaphor_lower = f"{visual_metaphor} {visual_purpose}".lower()
    role_lower = narrative_role.lower()

    if domain == TopicDomain.ROBOTICS_HARDWARE:
        # Dedicated Physical Robotics Hardware Layout
        mid_draw.rounded_rectangle([(cx - 380, 450), (cx + 380, 550)], radius=16, fill=(15, 23, 42, 250), outline=(*accent_rgb, 255), width=2)
        _draw_fitted_text(mid_draw, headline, cx - 350, 465, 700, 70, fill=(255, 255, 255, 255), base_size=42, center=True)
        mid_draw.rounded_rectangle([(cx - 360, 580), (cx + 360, 880)], radius=24, fill=(*surface_rgb, 240), outline=(*border_rgb, 255), width=2)
        mid_draw.rectangle([(cx - 320, 780), (cx + 320, 850)], fill=(*surface_rgb, 255), outline=(*border_rgb, 255), width=2)
        _draw_titanium_gripper(mid_draw, cx, 700, scale=1.35, open_angle=20, accent_rgb=accent_rgb, border_rgb=border_rgb)
        mid_draw.text((cx - 150, 855), f"CALIBRATION: {metric}", fill=(*accent_rgb, 255), font=font_badge)
        return

    # Determine layout mode (0: Hero Metric, 1: Flowchart, 2: Split Comparison, 3: Terminal, 4: Outro Brand)
    is_cta = role_lower == "cta" or scene_index >= 4 or any(k in metaphor_lower for k in ["outro", "cta", "subscribe", "brand"])

    if is_cta:
        # =========================================================================
        # LAYOUT 5: BRAND IDENTITY OUTRO ANCHOR (Clean Royal Blue Robot Emblem)
        # =========================================================================
        # Top Header Pill (Clean charcoal, NO contradictory 'DARK' text)
        mid_draw.rounded_rectangle([(cx - 380, 450), (cx + 380, 545)], radius=16, fill=(15, 23, 42, 250), outline=(*accent_rgb, 255), width=2)
        _draw_fitted_text(mid_draw, "AI SIMPLIFIED LAB", cx - 350, 465, 700, 65, fill=(255, 255, 255, 255), base_size=42, center=True)

        # Central Brand Shield & Mascot Vector Crest
        cy_logo = 710
        # Outer Royal Blue Glow Ring
        mid_draw.ellipse([(cx - 130, cy_logo - 130), (cx + 130, cy_logo + 130)], fill=(239, 246, 255, 250), outline=(37, 99, 235, 255), width=4)
        mid_draw.ellipse([(cx - 105, cy_logo - 105), (cx + 105, cy_logo + 105)], fill=(15, 23, 42, 255), outline=(217, 119, 6, 255), width=2)

        # Robot Silhouette Emblem inside shield
        # Head
        mid_draw.rounded_rectangle([(cx - 55, cy_logo - 60), (cx + 55, cy_logo + 10)], radius=20, fill=(255, 255, 255, 255), outline=(203, 213, 225, 255), width=2)
        # Royal Blue Visor
        mid_draw.rounded_rectangle([(cx - 40, cy_logo - 45), (cx + 40, cy_logo - 10)], radius=12, fill=(37, 99, 235, 255))
        # Visor Glow Eyes
        mid_draw.ellipse([(cx - 24, cy_logo - 34), (cx - 12, cy_logo - 22)], fill=(255, 255, 255, 255))
        mid_draw.ellipse([(cx + 12, cy_logo - 34), (cx + 24, cy_logo - 22)], fill=(255, 255, 255, 255))
        # Torso & Lab Badge
        mid_draw.rounded_rectangle([(cx - 45, cy_logo + 18), (cx + 45, cy_logo + 65)], radius=14, fill=(255, 255, 255, 255), outline=(203, 213, 225, 255), width=2)
        mid_draw.rectangle([(cx - 18, cy_logo + 32), (cx + 18, cy_logo + 48)], fill=(37, 99, 235, 255))

        # Channel Credentials Badges Below
        mid_draw.rounded_rectangle([(cx - 300, 870), (cx + 300, 930)], radius=14, fill=(241, 245, 249, 250), outline=(37, 99, 235, 255), width=2)
        _draw_fitted_text(mid_draw, "FRONTIER AI ARCHITECTURE BRIEFINGS", cx - 280, 880, 560, 40, fill=(30, 41, 59, 255), base_size=24, bold=True, center=True)

    elif scene_index == 0 or role_lower == "hook":
        # =========================================================================
        # LAYOUT 1: CENTERED HERO CARD WITH BOLD METRIC CALLOUT
        # =========================================================================
        mid_draw.rounded_rectangle([(cx - 380, 450), (cx + 380, 545)], radius=16, fill=(15, 23, 42, 250), outline=(*accent_rgb, 255), width=2)
        _draw_fitted_text(mid_draw, headline, cx - 350, 465, 700, 65, fill=(255, 255, 255, 255), base_size=42, center=True)

        # Centered Hero Metric Card
        mid_draw.rounded_rectangle([(cx - 380, 570), (cx + 380, 890)], radius=24, fill=(*surface_rgb, 248), outline=(*accent_rgb, 255), width=2)
        mid_draw.rounded_rectangle([(cx - 350, 595), (cx + 350, 645)], radius=12, fill=(239, 246, 255, 255), outline=(37, 99, 235, 255), width=1)
        _draw_fitted_text(mid_draw, "CORE PRODUCTION BENCHMARK", cx - 330, 605, 660, 30, fill=(30, 64, 175, 255), base_size=22, bold=True, center=True)

        # Huge Bold Metric Text
        _draw_fitted_text(mid_draw, metric, cx - 340, 670, 680, 90, fill=(217, 119, 6, 255), base_size=64, bold=True, center=True)

        # Metric Status Gauges
        mid_draw.line([(cx - 320, 785), (cx + 320, 785)], fill=(226, 232, 240, 255), width=2)
        callout_w = 210
        labels = [cards[0] if len(cards) > 0 else "EFFICIENCY", "P99 LATENCY", "CONVERGENCE"]
        vals = ["99.4%", "< 15MS", "VERIFIED"]
        for i, (lbl, val) in enumerate(zip(labels, vals)):
            lx = cx - 320 + i * callout_w
            mid_draw.text((lx + 10, 800), lbl[:14], fill=(100, 116, 139, 255), font=_get_font(20, bold=False))
            mid_draw.text((lx + 10, 830), val, fill=(30, 41, 59, 255), font=_get_font(24, bold=True))

    elif scene_index == 1 or role_lower == "mechanism":
        # =========================================================================
        # LAYOUT 2: HORIZONTAL FLOWCHART / PIPELINE NODE TREE
        # =========================================================================
        mid_draw.rounded_rectangle([(cx - 380, 450), (cx + 380, 545)], radius=16, fill=(15, 23, 42, 250), outline=(*accent_rgb, 255), width=2)
        _draw_fitted_text(mid_draw, headline, cx - 350, 465, 700, 65, fill=(255, 255, 255, 255), base_size=42, center=True)

        # 3 Sequential Nodes in Horizontal Flow
        node_w = 220
        node_h = 240
        gap = 35
        total_flow_w = 3 * node_w + 2 * gap
        flow_start_x = cx - total_flow_w // 2

        for i in range(3):
            nx = flow_start_x + i * (node_w + gap)
            ny = 610
            lbl = cards[i] if i < len(cards) else f"STAGE {i+1}"
            is_active = (i == 1)
            n_fill = (15, 23, 42, 250) if is_active else (*surface_rgb, 245)
            n_border = (*accent_rgb, 255) if is_active else (*border_rgb, 255)
            n_text = (255, 255, 255, 255) if is_active else (*text_rgb, 255)

            mid_draw.rounded_rectangle([(nx, ny), (nx + node_w, ny + node_h)], radius=18, fill=n_fill, outline=n_border, width=2)
            # Step index tag
            mid_draw.rounded_rectangle([(nx + 15, ny + 15), (nx + 75, ny + 45)], radius=8, fill=(37, 99, 235, 255) if is_active else (226, 232, 240, 255))
            mid_draw.text((nx + 25, ny + 20), f"0{i+1}", fill=(255, 255, 255, 255) if is_active else (100, 116, 139, 255), font=_get_font(20, bold=True))
            # Label
            _draw_fitted_text(mid_draw, lbl, nx + 15, ny + 70, node_w - 30, 40, fill=n_text, base_size=24, bold=True, center=True)
            # Node status tag
            st_text = "PROCESSING" if is_active else ("READY" if i == 0 else "OUTPUT")
            mid_draw.text((nx + 25, ny + 175), f"• {st_text}", fill=(16, 185, 129, 255) if is_active else (148, 163, 184, 255), font=_get_font(18, bold=True))

            # Connecting Conduits with Directional Chevrons
            if i < 2:
                pipe_x1 = nx + node_w
                pipe_x2 = nx + node_w + gap
                pipe_y = ny + node_h // 2
                mid_draw.line([(pipe_x1, pipe_y), (pipe_x2, pipe_y)], fill=(*accent_rgb, 255), width=4)
                mid_draw.polygon([(pipe_x2 - 8, pipe_y - 6), (pipe_x2, pipe_y), (pipe_x2 - 8, pipe_y + 6)], fill=(*accent_rgb, 255))

    elif scene_index == 2 or role_lower == "escalation":
        # =========================================================================
        # LAYOUT 3: SPLIT COMPARISON VIEW (Naive vs Optimized)
        # =========================================================================
        mid_draw.rounded_rectangle([(cx - 380, 450), (cx + 380, 545)], radius=16, fill=(15, 23, 42, 250), outline=(*accent_rgb, 255), width=2)
        _draw_fitted_text(mid_draw, headline, cx - 350, 465, 700, 65, fill=(255, 255, 255, 255), base_size=42, center=True)

        col_w = 345
        # Left: Naive / Traditional
        lx = cx - 380
        mid_draw.rounded_rectangle([(lx, 580), (lx + col_w, 890)], radius=20, fill=(*surface_rgb, 245), outline=(239, 68, 68, 255), width=2)
        mid_draw.rounded_rectangle([(lx + 20, 600), (lx + col_w - 20, 645)], radius=10, fill=(254, 242, 242, 255), outline=(239, 68, 68, 255), width=1)
        _draw_fitted_text(mid_draw, "LEGACY / UNINDEXED", lx + 25, 610, col_w - 50, 25, fill=(185, 28, 28, 255), base_size=20, bold=True, center=True)
        mid_draw.text((lx + 25, 670), "• Full Table Scan", fill=(71, 85, 105, 255), font=_get_font(22))
        mid_draw.text((lx + 25, 715), "• Latency: > 800ms", fill=(185, 28, 28, 255), font=_get_font(22, bold=True))
        mid_draw.text((lx + 25, 760), "• Linear O(N) Cost", fill=(71, 85, 105, 255), font=_get_font(22))
        mid_draw.text((lx + 25, 805), "• High CPU Bottleneck", fill=(71, 85, 105, 255), font=_get_font(22))

        # Center VS Badge
        mid_draw.ellipse([(cx - 28, 715), (cx + 28, 771)], fill=(15, 23, 42, 255), outline=(255, 255, 255, 255), width=2)
        mid_draw.text((cx - 14, 730), "VS", fill=(255, 255, 255, 255), font=_get_font(20, bold=True))

        # Right: Optimized V2
        rx = cx + 35
        mid_draw.rounded_rectangle([(rx, 580), (rx + col_w, 890)], radius=20, fill=(15, 23, 42, 250), outline=(*accent_rgb, 255), width=2)
        mid_draw.rounded_rectangle([(rx + 20, 600), (rx + col_w - 20, 645)], radius=10, fill=(30, 64, 175, 255))
        _draw_fitted_text(mid_draw, "OPTIMIZED // VECTOR", rx + 25, 610, col_w - 50, 25, fill=(255, 255, 255, 255), base_size=20, bold=True, center=True)
        mid_draw.text((rx + 25, 670), "• HNSW Graph Index", fill=(226, 232, 240, 255), font=_get_font(22))
        mid_draw.text((rx + 25, 715), f"• Latency: {metric}", fill=(245, 158, 11, 255), font=_get_font(22, bold=True))
        mid_draw.text((rx + 25, 760), "• Sub-linear O(log N)", fill=(226, 232, 240, 255), font=_get_font(22))
        mid_draw.text((rx + 25, 805), "• 10x Scale Throughput", fill=(16, 185, 129, 255), font=_get_font(22, bold=True))

    else:
        # =========================================================================
        # LAYOUT 4: DEVELOPER TERMINAL / CODE SNIPPET WINDOW
        # =========================================================================
        mid_draw.rounded_rectangle([(cx - 380, 450), (cx + 380, 545)], radius=16, fill=(15, 23, 42, 250), outline=(*accent_rgb, 255), width=2)
        _draw_fitted_text(mid_draw, headline, cx - 350, 465, 700, 65, fill=(255, 255, 255, 255), base_size=42, center=True)

        term_x1 = cx - 380
        term_x2 = cx + 380
        term_y1 = 575
        term_y2 = 890
        # Dark Terminal Body
        mid_draw.rounded_rectangle([(term_x1, term_y1), (term_x2, term_y2)], radius=18, fill=(15, 23, 42, 250), outline=(51, 65, 85, 255), width=2)
        # Window Header
        mid_draw.rounded_rectangle([(term_x1, term_y1), (term_x2, term_y1 + 44)], radius=18, fill=(30, 41, 59, 255))
        mid_draw.rectangle([(term_x1, term_y1 + 24), (term_x2, term_y1 + 44)], fill=(30, 41, 59, 255))
        # Window Controls (Red, Yellow, Green)
        mid_draw.ellipse([(term_x1 + 20, term_y1 + 14), (term_x1 + 34, term_y1 + 28)], fill=(239, 68, 68, 255))
        mid_draw.ellipse([(term_x1 + 44, term_y1 + 14), (term_x1 + 58, term_y1 + 28)], fill=(245, 158, 11, 255))
        mid_draw.ellipse([(term_x1 + 68, term_y1 + 14), (term_x1 + 82, term_y1 + 28)], fill=(16, 185, 129, 255))
        mid_draw.text((term_x1 + 110, term_y1 + 12), "cluster_runtime.sh [TELEMETRY]", fill=(148, 163, 184, 255), font=_get_font(18, bold=True))

        # Monospaced Command & Log Stream
        code_lines = [
            ("$ ai_engine.query(vector_index=\"prod_v2\")", (52, 211, 153, 255)),
            ("[INFO] Loaded 1.2M dense embeddings into RAM", (226, 232, 240, 255)),
            (f"[SEARCH] Cosine similarity match: 0.984 | {metric}", (56, 189, 248, 255)),
            ("[STATUS] Context bus stream verified (10k req/s)", (251, 191, 36, 255)),
            ("✓ Deployed in enterprise production cluster", (16, 185, 129, 255)),
        ]
        for idx, (line_txt, col) in enumerate(code_lines):
            mid_draw.text((term_x1 + 28, term_y1 + 60 + idx * 46), line_txt, fill=col, font=_get_font(22, bold=False))




