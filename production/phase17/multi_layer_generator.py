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


def _clip_to_width(
    draw_ctx: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    max_px: float,
) -> str:
    """Word-boundary clip with an ellipsis — text is never cut mid-word (§21)."""
    text = text.strip()
    if draw_ctx.textlength(text, font=font) <= max_px:
        return text
    out = ""
    for word in text.split():
        trial = f"{out} {word}".strip()
        if draw_ctx.textlength(f"{trial}…", font=font) > max_px:
            break
        out = trial
    return f"{out}…" if out else "…"


def _wrap_to_width(
    draw_ctx: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    max_px: float,
) -> list[str]:
    """Greedy word wrap at the measured pixel width of the actual card."""
    lines: list[str] = []
    current = ""
    for word in text.split():
        trial = f"{current} {word}".strip()
        if current and draw_ctx.textlength(trial, font=font) > max_px:
            lines.append(current)
            current = word
        else:
            current = trial
    if current:
        lines.append(current)
    return lines or [text]


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
    wrap: bool = False,
) -> int:
    """Scales font size dynamically so text strictly fits inside max_width and max_height.

    `wrap=True` lets a long subject use the card's vertical room (two clean lines)
    before shrinking. Whatever is left over-long is clipped on a word boundary with
    an ellipsis — labels read as complete phrases, never as "PIPELINE ENT".
    """
    clean_text = text.strip()
    if not clean_text:
        return base_size

    def _font(s: int) -> ImageFont.FreeTypeFont:
        return _get_font(s, bold=bold)

    def _fits_one_line(s: int) -> bool:
        f = _font(s)
        b = draw_ctx.textbbox((0, 0), clean_text, font=f)
        return (b[2] - b[0]) <= max_width and (b[3] - b[1]) <= max_height

    size = base_size
    while size > min_size and not _fits_one_line(size):
        size -= 2

    # Long subject in a tall card: keep the type readable and wrap to 2 lines.
    if wrap and not _fits_one_line(size):
        size = base_size
        lines = [clean_text]
        while size > min_size:
            f = _font(size)
            lines = _wrap_to_width(draw_ctx, clean_text, f, max_width)
            line_h = int(size * 1.35)
            widest = max(draw_ctx.textlength(ln, font=f) for ln in lines)
            if len(lines) * line_h <= max_height and widest <= max_width:
                break
            size -= 2
        f = _font(size)
        line_h = int(size * 1.35)
        max_lines = max(1, max_height // line_h)
        if len(lines) > max_lines:
            lines = lines[:max_lines]
            lines[-1] = _clip_to_width(draw_ctx, f"{lines[-1]}…", f, max_width)
        block_h = len(lines) * line_h
        y = box_y + max(0, (max_height - block_h) // 2)
        for line in lines:
            w = draw_ctx.textlength(line, font=f)
            x = box_x + max(0, (max_width - int(w)) // 2) if center else box_x
            draw_ctx.text((x, y), line, fill=fill, font=f)
            y += line_h
        return size

    font = _font(size)
    shown = clean_text
    bbox = draw_ctx.textbbox((0, 0), shown, font=font)
    if (bbox[2] - bbox[0]) > max_width:
        shown = _clip_to_width(draw_ctx, clean_text, font, max_width)
        bbox = draw_ctx.textbbox((0, 0), shown, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    dx = box_x + max(0, (max_width - tw) // 2) if center else box_x
    dy = box_y + max(0, (max_height - th) // 2)
    draw_ctx.text((dx, dy), shown, fill=fill, font=font)
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
    # Keep apostrophes inside words ("signal's") — only stray quote marks go.
    clean_sub = re.sub(r"(?<![A-Za-z0-9])'|'(?![A-Za-z0-9])", "", str(subject or ""))
    clean_sub = re.sub(r"[^\w\s'-]", "", clean_sub).strip()
    if clean_sub and len(clean_sub) >= 4:
        words = clean_sub.upper().split()
        acc = []
        cur_len = 0
        for w in words:
            if cur_len + len(w) + (1 if acc else 0) <= 36:
                acc.append(w)
                cur_len += len(w) + (1 if len(acc) > 1 else 0)
            else:
                break
        headline = " ".join(acc) if acc else clean_sub.upper()
    elif visual_purpose and len(visual_purpose) >= 4:
        clean_vp = re.sub(r"[^\w\s-]", "", visual_purpose).strip().upper()
        words = clean_vp.split()
        acc = []
        cur_len = 0
        for w in words:
            if cur_len + len(w) + (1 if acc else 0) <= 36:
                acc.append(w)
                cur_len += len(w) + (1 if len(acc) > 1 else 0)
            else:
                break
        headline = " ".join(acc) if acc else clean_vp
    else:
        words = [w.strip(".,;:!?\"'") for w in narration.split() if len(w) > 3]
        # Headline is only ever narration content — never a generic technical phrase.
        headline = " ".join(words[:3]).upper() if words else ""

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
    else:
        # Never pad with generic technical words ("RUNTIME", "PIPELINE", "ENGINE").
        # If the narration names fewer concepts, the visual shows fewer concepts.
        cards = key_terms[:3]

    # Extract strictly real metrics from narration; when there is no number there is no metric.
    metric_match = re.search(r"(\+?\d+%|\d+x|\d+ms|\d+s|\d+\.\d+%)", narration)
    metric = metric_match.group(1) if metric_match else ""

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
    """Near-plane focus falloff: a soft vignette at the extreme edges.

    Purpose-built for comprehension — it darkens the outer margins so the eye stays on the
    explained subject. It draws no frames, no rails, no labels and no telemetry: a decorative
    element without an explanatory purpose has no place in the foreground.
    """
    depth_w = 64
    for i in range(depth_w):
        alpha = int(255 * ((depth_w - i) / depth_w) ** 2)
        if alpha <= 8:
            continue
        fg_draw.rectangle([(i, 0), (i, height)], fill=(15, 23, 42, alpha))
        fg_draw.rectangle([(width - 1 - i, 0), (width - 1 - i, height)], fill=(15, 23, 42, alpha))


from production.phase18.scene_graph import (
    SemanticSceneGraph,
    SceneNodeType,
    build_semantic_scene_graph,
)


def _draw_midground_subject(
    mid_draw: ImageDraw.ImageDraw,
    width: int,
    height: int,
    scene_graph: SemanticSceneGraph,
    headline: str,
    accent_rgb: tuple[int, int, int],
    border_rgb: tuple[int, int, int],
    text_rgb: tuple[int, int, int],
    surface_rgb: tuple[int, int, int],
    muted_rgb: tuple[int, int, int],
    font_title: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    font_badge: ImageFont.FreeTypeFont | ImageFont.ImageFont,
):
    """Renders midground layer directly from compiled SemanticSceneGraph nodes and edges.
    Composes visuals dynamically based on semantic topology (transformation, stack, bipartite, flow, focal, brand).
    Zero fixed card templates and zero boilerplate header banners.
    """
    cx = width // 2
    topology = getattr(scene_graph, "topology", "process_flow")

    # 1. TOPOLOGY: BRAND IDENTITY (CTA Only)
    if topology == "brand":
        for node in scene_graph.nodes:
            cy_logo = 710
            # Outer Glow Ring & Shield
            mid_draw.ellipse([(cx - 130, cy_logo - 130), (cx + 130, cy_logo + 130)], fill=(239, 246, 255, 250), outline=(37, 99, 235, 255), width=4)
            mid_draw.ellipse([(cx - 105, cy_logo - 105), (cx + 105, cy_logo + 105)], fill=(15, 23, 42, 255), outline=(217, 119, 6, 255), width=2)
            # Robot Silhouette Emblem
            mid_draw.rounded_rectangle([(cx - 55, cy_logo - 60), (cx + 55, cy_logo + 10)], radius=20, fill=(255, 255, 255, 255), outline=(203, 213, 225, 255), width=2)
            mid_draw.rounded_rectangle([(cx - 40, cy_logo - 45), (cx + 40, cy_logo - 10)], radius=12, fill=(37, 99, 235, 255))
            mid_draw.ellipse([(cx - 24, cy_logo - 34), (cx - 12, cy_logo - 22)], fill=(255, 255, 255, 255))
            mid_draw.ellipse([(cx + 12, cy_logo - 34), (cx + 24, cy_logo - 22)], fill=(255, 255, 255, 255))
            mid_draw.rounded_rectangle([(cx - 45, cy_logo + 18), (cx + 45, cy_logo + 65)], radius=14, fill=(255, 255, 255, 255), outline=(203, 213, 225, 255), width=2)
            mid_draw.rectangle([(cx - 18, cy_logo + 32), (cx + 18, cy_logo + 48)], fill=(37, 99, 235, 255))

            # Brand line only when the CTA narration actually states copy for it.
            if node.details:
                mid_draw.rounded_rectangle([(cx - 300, 870), (cx + 300, 930)], radius=14, fill=(241, 245, 249, 250), outline=(37, 99, 235, 255), width=2)
                _draw_fitted_text(mid_draw, node.details[0], cx - 280, 880, 560, 40, fill=(30, 41, 59, 255), base_size=24, bold=True, center=True)
        return

    # 2. TOPOLOGY: LAYERED ARCHITECTURE (Vertical Hierarchical Stack)
    if topology == "layered_architecture":
        for node in scene_graph.nodes:
            x1, y1, x2, y2 = node.bounds
            is_core = node.is_primary or node.shape_style == "matrix_grid"
            n_fill = (15, 23, 42, 250) if is_core else (*surface_rgb, 245)
            n_border = (*accent_rgb, 255) if is_core else (*border_rgb, 220)
            n_text = (255, 255, 255, 255) if is_core else (*text_rgb, 255)

            mid_draw.rounded_rectangle([(x1, y1), (x2, y2)], radius=16, fill=n_fill, outline=n_border, width=2)
            _draw_fitted_text(mid_draw, node.label, x1 + 20, y1 + 18, (x2 - x1) - 40, 38, fill=n_text, base_size=26, bold=True, center=True)

            if is_core:
                # Draw subtle attention matrix grid lines
                grid_y = y1 + 65
                grid_w = (x2 - x1) - 80
                gx1 = x1 + 40
                gx2 = gx1 + grid_w
                mid_draw.line([(gx1, grid_y), (gx2, grid_y)], fill=(*accent_rgb, 120), width=1)
                # Cell nodes
                for ci in range(6):
                    cx_pos = gx1 + int((ci + 0.5) * (grid_w / 6))
                    mid_draw.ellipse([(cx_pos - 4, grid_y + 12), (cx_pos + 4, grid_y + 20)], fill=(*accent_rgb, 220))
                if node.details:
                    f_bullet = _get_font(20, bold=False)
                    line = _clip_to_width(mid_draw, f"• {node.details[0]}", f_bullet, grid_w - 20)
                    mid_draw.text((gx1 + 10, grid_y + 35), line, fill=(203, 213, 225, 255), font=f_bullet)
            else:
                if node.details:
                    f_bullet = _get_font(19, bold=False)
                    line = _clip_to_width(mid_draw, f"• {node.details[0]}", f_bullet, (x2 - x1) - 60)
                    mid_draw.text((x1 + 30, y1 + 58), line, fill=(100, 116, 139, 255), font=f_bullet)

        # Vertical flowing connectors
        for edge in scene_graph.edges:
            src = next((n for n in scene_graph.nodes if n.id == edge.from_node), None)
            dst = next((n for n in scene_graph.nodes if n.id == edge.to_node), None)
            if src and dst:
                sy = src.bounds[3]
                dy = dst.bounds[1]
                mid_draw.line([(cx, sy), (cx, dy)], fill=(*accent_rgb, 220), width=3)
                mid_draw.polygon([(cx - 6, dy - 8), (cx, dy), (cx + 6, dy - 8)], fill=(*accent_rgb, 220))
        return

    # 3. TOPOLOGY: OBJECT TRANSFORMATION (Source -> Transform Kernel -> Result)
    if topology == "object_transformation":
        for node in scene_graph.nodes:
            x1, y1, x2, y2 = node.bounds
            if node.shape_style == "transform_kernel":
                # Prominent transformation core
                mid_draw.rounded_rectangle([(x1, y1), (x2, y2)], radius=24, fill=(15, 23, 42, 255), outline=(*accent_rgb, 255), width=3)
                # Transformation glyph symbol (Σ or →)
                k_cx = (x1 + x2) // 2
                mid_draw.ellipse([(k_cx - 42, y1 + 35), (k_cx + 42, y1 + 119)], fill=(30, 41, 59, 255), outline=(*accent_rgb, 180), width=2)
                mid_draw.polygon([(k_cx - 14, y1 + 60), (k_cx + 16, y1 + 77), (k_cx - 14, y1 + 94)], fill=(*accent_rgb, 255))
                # Label
                _draw_fitted_text(mid_draw, node.label, x1 + 15, y1 + 140, (x2 - x1) - 30, 42, fill=(255, 255, 255, 255), base_size=24, bold=True, center=True)
                if node.details:
                    _draw_fitted_text(mid_draw, node.details[0], x1 + 15, y1 + 195, (x2 - x1) - 30, 50, fill=(203, 213, 225, 255), base_size=18, bold=False, center=True)
            else:
                # Source / Result Container
                mid_draw.rounded_rectangle([(x1, y1), (x2, y2)], radius=18, fill=(*surface_rgb, 245), outline=(*border_rgb, 220), width=2)
                _draw_fitted_text(mid_draw, node.label, x1 + 12, y1 + 22, (x2 - x1) - 24, 40, fill=(*text_rgb, 255), base_size=22, bold=True, center=True)
                if node.details:
                    f_bullet = _get_font(18, bold=False)
                    line = _clip_to_width(mid_draw, f"• {node.details[0]}", f_bullet, (x2 - x1) - 36)
                    mid_draw.text((x1 + 18, y1 + 80), line, fill=(100, 116, 139, 255), font=f_bullet)

        # Horizontal connectors
        for edge in scene_graph.edges:
            src = next((n for n in scene_graph.nodes if n.id == edge.from_node), None)
            dst = next((n for n in scene_graph.nodes if n.id == edge.to_node), None)
            if src and dst:
                p1_x = src.bounds[2]
                p2_x = dst.bounds[0]
                py = (src.bounds[1] + src.bounds[3]) // 2
                mid_draw.line([(p1_x, py), (p2_x, py)], fill=(*accent_rgb, 255), width=3)
                mid_draw.polygon([(p2_x - 8, py - 6), (p2_x, py), (p2_x - 8, py + 6)], fill=(*accent_rgb, 255))
        return

    # 4. TOPOLOGY: BIPARTITE COMPARISON (Split Side-by-Side)
    if topology == "bipartite":
        for node in scene_graph.nodes:
            x1, y1, x2, y2 = node.bounds
            is_active = node.is_primary
            n_fill = (15, 23, 42, 250) if is_active else (*surface_rgb, 245)
            n_border = (*accent_rgb, 255) if is_active else (*border_rgb, 220)
            n_text = (255, 255, 255, 255) if is_active else (*text_rgb, 255)

            mid_draw.rounded_rectangle([(x1, y1), (x2, y2)], radius=20, fill=n_fill, outline=n_border, width=2)
            _draw_fitted_text(mid_draw, node.label, x1 + 16, y1 + 25, (x2 - x1) - 32, 45, fill=n_text, base_size=24, bold=True, center=True, wrap=True)
            for d_idx, detail in enumerate(node.details[:3]):
                dy = y1 + 95 + d_idx * 45
                if dy + 30 <= y2:
                    f_bullet = _get_font(19, bold=False)
                    line = _clip_to_width(mid_draw, f"• {detail}", f_bullet, (x2 - x1) - 44)
                    mid_draw.text((x1 + 22, dy), line, fill=(203, 213, 225, 255) if is_active else (100, 116, 139, 255), font=f_bullet)

        # Central "VS" badge
        for edge in scene_graph.edges:
            src = next((n for n in scene_graph.nodes if n.id == edge.from_node), None)
            dst = next((n for n in scene_graph.nodes if n.id == edge.to_node), None)
            if src and dst:
                c_badge_x = (src.bounds[2] + dst.bounds[0]) // 2
                c_badge_y = (src.bounds[1] + src.bounds[3]) // 2
                mid_draw.ellipse([(c_badge_x - 28, c_badge_y - 28), (c_badge_x + 28, c_badge_y + 28)], fill=(15, 23, 42, 255), outline=(255, 255, 255, 255), width=2)
                mid_draw.text((c_badge_x - 14, c_badge_y - 12), "VS", fill=(255, 255, 255, 255), font=_get_font(20, bold=True))
        return

    # 5. TOPOLOGY: PROCESS FLOW / FOCAL (Sequential pipeline or Hero Subject)
    for node in scene_graph.nodes:
        x1, y1, x2, y2 = node.bounds
        is_p = node.is_primary
        n_fill = (15, 23, 42, 250) if is_p else (*surface_rgb, 245)
        n_border = (*accent_rgb, 255) if is_p else (*border_rgb, 220)
        n_text = (255, 255, 255, 255) if is_p else (*text_rgb, 255)

        mid_draw.rounded_rectangle([(x1, y1), (x2, y2)], radius=18, fill=n_fill, outline=n_border, width=2)
        _draw_fitted_text(mid_draw, node.label, x1 + 16, y1 + 24, (x2 - x1) - 32, 60, fill=n_text, base_size=24, bold=True, center=True, wrap=True)
        for d_idx, detail in enumerate(node.details[:3]):
            dy = y1 + 85 + d_idx * 42
            if dy + 30 <= y2:
                f_bullet = _get_font(19, bold=False)
                line = _clip_to_width(mid_draw, f"• {detail}", f_bullet, (x2 - x1) - 40)
                mid_draw.text((x1 + 20, dy), line, fill=(203, 213, 225, 255) if is_p else (100, 116, 139, 255), font=f_bullet)

    for edge in scene_graph.edges:
        src = next((n for n in scene_graph.nodes if n.id == edge.from_node), None)
        dst = next((n for n in scene_graph.nodes if n.id == edge.to_node), None)
        if src and dst:
            p1_x = src.bounds[2]
            p2_x = dst.bounds[0]
            py = (src.bounds[1] + src.bounds[3]) // 2
            mid_draw.line([(p1_x, py), (p2_x, py)], fill=(*accent_rgb, 255), width=3)
            mid_draw.polygon([(p2_x - 8, py - 6), (p2_x, py), (p2_x - 8, py + 6)], fill=(*accent_rgb, 255))



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
    total_scenes: int = 5,
    scene_graph: SemanticSceneGraph | None = None,
) -> dict[str, Path]:
    """Generates and saves the 3 distinct depth layers for a scene:
    Returns dict: {"bg": path, "mid": path, "fg": path, "primary": path}
    
    Adheres strictly to:
    1. Topic-aligned semantics: Software/cloud topics NEVER render physical robotics arms.
    2. Dynamic Scene Graph compilation: Renders verified claims into node topologies rather than rigid templates.
    3. Safe Zone Layout: All graphics fit in top 75% of canvas (above y=1440), leaving strict 20% bottom margin.
    """
    st = style or get_style_system()
    output_dir.mkdir(parents=True, exist_ok=True)
    accent_rgb = _hex_to_rgb(st.accent)
    border_rgb = _hex_to_rgb(st.border_color)
    text_rgb = _hex_to_rgb(st.primary_text)
    muted_rgb = _hex_to_rgb(st.secondary_text)
    surface_rgb = _hex_to_rgb(st.surface_elevated) if hasattr(st, "surface_elevated") else (255, 255, 255)

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

    cx = width // 2
    domain = classify_topic_domain(topic=topic, subject=subject, visual_purpose=visual_purpose, narration=narration)

    headline, cards, metric = _extract_semantic_entities(
        subject=subject,
        visual_purpose=visual_purpose,
        visual_metaphor=visual_metaphor,
        narration=narration,
        domain=domain,
    )

    # Compile scene graph if not passed in
    if scene_graph is None:
        scene_graph = build_semantic_scene_graph(
            scene_index=scene_index,
            narrative_role=narrative_role,
            subject=subject,
            visual_purpose=visual_purpose,
            narration=narration,
            domain=domain,
            total_scenes=total_scenes,
        )

    # FOREGROUND LAYER ARCHITECTURE (z=20, True Spatial Depth)
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

    # MIDGROUND LAYER (z=10) - Dynamic Scene Graph Visuals
    _draw_midground_subject(
        mid_draw=mid_draw,
        width=width,
        height=height,
        scene_graph=scene_graph,
        headline=headline,
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
    compat_path = output_dir / f"ast_{scene_id}.png"
    composite.convert("RGB").save(compat_path, "PNG")

    return {
        "bg": bg_path,
        "mid": mid_path,
        "fg": fg_path,
        "primary": primary_path,
    }





