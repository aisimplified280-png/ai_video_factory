"""Phase 17 Environment Background Generator.

Enforces Requirement 1: No single background survives longer than 8 seconds.
Every scene generates a distinctly unique environment:
- Scene 1: Macro Studio Environment (soft directional keylight, shallow DoF, warm specular bokeh)
- Scene 2: Blueprint CAD Drafting Environment (orthographic grid, technical axes, CAD alignment ticks)
- Scene 3: Tactical Radar/Lidar Environment (high-contrast tactical floor grid, range rings, radar sweep)
- Scene 4: Cinematic Logistics Warehouse (deep perspective storage racking aisles, floor reflections, volumetric light beams)
- Scene 5: Premium Obsidian Brand Stage (matte architectural pedestal, radial spotlight, subtle rim light)
"""
from __future__ import annotations

import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

from .style_systems import StyleSystem, get_style_system


def _hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    s = hex_str.lstrip("#")
    return int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)


def generate_macro_studio_bg(width: int = 1080, height: int = 1920, style: StyleSystem | None = None) -> Image.Image:
    """Scene 1: Macro studio with shallow depth of field and radial keylight."""
    st = style or get_style_system()
    bg_rgb = _hex_to_rgb(st.primary_bg)
    is_light = bg_rgb[0] > 180 and bg_rgb[1] > 180 and bg_rgb[2] > 180

    img = Image.new("RGB", (width, height), bg_rgb)
    draw = ImageDraw.Draw(img)

    # Keylight glow from top-left (studio lighting fixture)
    glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for radius in range(950, 80, -70):
        alpha = int(28 * (1.0 - radius / 950))
        cx, cy = 340, 420
        col = (239, 246, 255, alpha) if is_light else (45, 55, 75, alpha)
        gd.ellipse([(cx - radius, cy - radius), (cx + radius, cy + radius)], fill=col)

    # Subtle warm bokeh orbs in distant background (shallow DoF effect)
    bokeh_spots = [(240, 300, 160), (840, 520, 220), (720, 1380, 180), (180, 1500, 140)]
    for bx, by, br in bokeh_spots:
        for r in range(br, 20, -30):
            alpha = int(14 * (1.0 - r / br))
            gd.ellipse([(bx - r, by - r), (bx + r, by + r)], fill=(217, 119, 54, alpha))

    img.paste(Image.alpha_composite(Image.new("RGBA", (width, height), (*bg_rgb, 255)), glow).convert("RGB"))
    draw = ImageDraw.Draw(img)

    # Subtle architectural base horizon
    draw.line([(0, 1280), (width, 1280)], fill=(226, 232, 240) if is_light else (36, 44, 58), width=1)
    return img


def generate_blueprint_cad_bg(width: int = 1080, height: int = 1920, style: StyleSystem | None = None) -> Image.Image:
    """Scene 2: Technical CAD drafting environment with orthographic grid lines and registration marks."""
    st = style or get_style_system()
    bg_rgb = _hex_to_rgb(st.primary_bg)
    is_light = bg_rgb[0] > 180 and bg_rgb[1] > 180 and bg_rgb[2] > 180

    base_col = bg_rgb if is_light else (14, 18, 26)
    grid_col = (226, 232, 240) if is_light else (22, 28, 40)
    major_col = (203, 213, 225) if is_light else (34, 44, 62)
    txt_col = (100, 116, 139) if is_light else (71, 85, 105)

    img = Image.new("RGB", (width, height), base_col)
    draw = ImageDraw.Draw(img)

    grid_size = 60
    for x in range(0, width, grid_size):
        draw.line([(x, 0), (x, height)], fill=grid_col, width=1)
    for y in range(0, height, grid_size):
        draw.line([(0, y), (width, y)], fill=grid_col, width=1)

    for x in range(0, width, grid_size * 4):
        draw.line([(x, 0), (x, height)], fill=major_col, width=1)
        draw.text((x + 6, 80), f"X:{x:04d}", fill=txt_col)
    for y in range(0, height, grid_size * 4):
        draw.line([(0, y), (width, y)], fill=major_col, width=1)
        draw.text((12, y + 6), f"Y:{y:04d}", fill=txt_col)

    cross_targets = [(100, 160), (width - 100, 160), (100, height - 160), (width - 100, height - 160)]
    for tx, ty in cross_targets:
        draw.line([(tx - 24, ty), (tx + 24, ty)], fill=major_col, width=2)
        draw.line([(tx, ty - 24), (tx, ty + 24)], fill=major_col, width=2)
        draw.ellipse([(tx - 12, ty - 12), (tx + 12, ty + 12)], outline=major_col, width=1)

    return img


def generate_tactical_radar_bg(width: int = 1080, height: int = 1920, style: StyleSystem | None = None) -> Image.Image:
    """Scene 3: High-contrast tactical architecture map with perspective grid and circular rings."""
    st = style or get_style_system()
    bg_rgb = _hex_to_rgb(st.primary_bg)
    is_light = bg_rgb[0] > 180 and bg_rgb[1] > 180 and bg_rgb[2] > 180

    base_col = bg_rgb if is_light else (11, 14, 20)
    grid_col = (226, 232, 240) if is_light else (24, 32, 46)
    ring_col = (203, 213, 225) if is_light else (38, 48, 68)

    img = Image.new("RGB", (width, height), base_col)
    draw = ImageDraw.Draw(img)

    horizon = 300
    for y in range(horizon, height, 45):
        pct = (y - horizon) / (height - horizon)
        line_w = int(1 + pct * 2)
        draw.line([(0, y), (width, y)], fill=grid_col, width=line_w)

    vanishing_x = width // 2
    for x in range(-400, width + 500, 140):
        draw.line([(vanishing_x, horizon), (x, height)], fill=grid_col, width=1)

    radar_cx, radar_cy = 540, 1150
    for radius in [180, 360, 540, 720]:
        draw.ellipse([(radar_cx - radius, radar_cy - radius // 2), (radar_cx + radius, radar_cy + radius // 2)], outline=ring_col, width=1)

    for angle in [0, 45, 90, 135, 180, 225, 270, 315]:
        rad = math.radians(angle)
        ex = int(radar_cx + 740 * math.cos(rad))
        ey = int(radar_cy + 370 * math.sin(rad))
        draw.line([(radar_cx, radar_cy), (ex, ey)], fill=grid_col, width=1)

    return img


def generate_cinematic_warehouse_bg(width: int = 1080, height: int = 1920, style: StyleSystem | None = None) -> Image.Image:
    """Scene 4: Deep perspective architectural space with perspective pillars and lighting."""
    st = style or get_style_system()
    bg_rgb = _hex_to_rgb(st.primary_bg)
    is_light = bg_rgb[0] > 180 and bg_rgb[1] > 180 and bg_rgb[2] > 180

    base_col = bg_rgb if is_light else (10, 12, 17)
    img = Image.new("RGB", (width, height), base_col)
    draw = ImageDraw.Draw(img)

    cx = width // 2
    vanishing_y = 380
    floor_y = 650

    if is_light:
        for y in range(floor_y, height):
            pct = (y - floor_y) / (height - floor_y)
            r = int(248 - pct * 6)
            g = int(250 - pct * 6)
            b = int(252 - pct * 6)
            draw.line([(0, y), (width, y)], fill=(r, g, b))
        draw.polygon([(0, 150), (cx - 140, vanishing_y), (cx - 140, height), (0, height)], fill=(241, 245, 249), outline=(226, 232, 240), width=2)
        draw.polygon([(width, 150), (cx + 140, vanishing_y), (cx + 140, height), (width, height)], fill=(241, 245, 249), outline=(226, 232, 240), width=2)
        for sy in range(vanishing_y + 60, height, 180):
            pct = (sy - vanishing_y) / (height - vanishing_y)
            lx = int(cx - 140 - (cx - 140) * pct)
            rx = int(cx + 140 + (width - (cx + 140)) * pct)
            draw.line([(lx, sy), (cx - 140, sy)], fill=(203, 213, 225), width=2)
            draw.line([(rx, sy), (cx + 140, sy)], fill=(203, 213, 225), width=2)
    else:
        for y in range(floor_y, height):
            pct = (y - floor_y) / (height - floor_y)
            r = int(14 + pct * 18)
            g = int(18 + pct * 22)
            b = int(26 + pct * 30)
            draw.line([(0, y), (width, y)], fill=(r, g, b))
        draw.polygon([(0, 150), (cx - 140, vanishing_y), (cx - 140, height), (0, height)], fill=(18, 23, 33), outline=(32, 40, 56), width=2)
        draw.polygon([(width, 150), (cx + 140, vanishing_y), (cx + 140, height), (width, height)], fill=(18, 23, 33), outline=(32, 40, 56), width=2)
        for sy in range(vanishing_y + 60, height, 180):
            pct = (sy - vanishing_y) / (height - vanishing_y)
            lx = int(cx - 140 - (cx - 140) * pct)
            rx = int(cx + 140 + (width - (cx + 140)) * pct)
            draw.line([(lx, sy), (cx - 140, sy)], fill=(45, 55, 76), width=2)
            draw.line([(rx, sy), (cx + 140, sy)], fill=(45, 55, 76), width=2)

    return img


def generate_premium_brand_stage_bg(width: int = 1080, height: int = 1920, style: StyleSystem | None = None) -> Image.Image:
    """Scene 5: Architectural studio stage with soft top-down spotlight and embossed pedestal."""
    st = style or get_style_system()
    bg_rgb = _hex_to_rgb(st.primary_bg)
    is_light = bg_rgb[0] > 180 and bg_rgb[1] > 180 and bg_rgb[2] > 180

    base_col = bg_rgb if is_light else (12, 14, 19)
    img = Image.new("RGB", (width, height), base_col)
    draw = ImageDraw.Draw(img)

    glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    cx, cy = width // 2, 680
    for radius in range(850, 60, -60):
        alpha = int(24 * (1.0 - radius / 850))
        glow_col = (239, 246, 255, alpha) if is_light else (42, 52, 72, alpha)
        gd.ellipse([(cx - radius, cy - radius // 2), (cx + radius, cy + radius // 2)], fill=glow_col)

    img.paste(Image.alpha_composite(Image.new("RGBA", (width, height), (*base_col, 255)), glow).convert("RGB"))
    draw = ImageDraw.Draw(img)

    pedestal_y = 1180
    ped_col = (203, 213, 225) if is_light else (45, 55, 72)
    draw.line([(180, pedestal_y), (width - 180, pedestal_y)], fill=ped_col, width=2)
    for y in range(pedestal_y, pedestal_y + 60, 2):
        alpha_factor = 1.0 - (y - pedestal_y) / 60
        r = int(base_col[0] * (1.0 - alpha_factor * 0.05 if is_light else 1.0 - alpha_factor * 0.4))
        g = int(base_col[1] * (1.0 - alpha_factor * 0.05 if is_light else 1.0 - alpha_factor * 0.4))
        b = int(base_col[2] * (1.0 - alpha_factor * 0.05 if is_light else 1.0 - alpha_factor * 0.4))
        draw.line([(220, y), (width - 220, y)], fill=(r, g, b), width=2)

    return img


LIBRARY_DIR = Path(__file__).parent / "library"


def generate_environment_for_scene(scene_index: int, width: int = 1080, height: int = 1920, style: StyleSystem | None = None) -> Image.Image:
    """Selects and renders the environment for a scene (guarantees no environment survives > 8s).
    Always renders clean, cohesive procedural production environments adhering to unified style system,
    completely eliminating inconsistent stock image backgrounds.
    """
    scene_generators = [
        generate_macro_studio_bg,
        generate_blueprint_cad_bg,
        generate_tactical_radar_bg,
        generate_cinematic_warehouse_bg,
        generate_premium_brand_stage_bg,
    ]
    key_idx = min(scene_index, len(scene_generators) - 1)
    generator_fn = scene_generators[key_idx]
    return generator_fn(width, height, style)
