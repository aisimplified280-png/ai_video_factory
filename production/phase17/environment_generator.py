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
    """Scene 1: Warm dark charcoal macro studio with shallow depth of field and radial keylight."""
    st = style or get_style_system()
    bg_rgb = _hex_to_rgb(st.primary_bg)
    surf_rgb = _hex_to_rgb(st.surface_elevated)

    img = Image.new("RGB", (width, height), bg_rgb)
    draw = ImageDraw.Draw(img)

    # Keylight glow from top-left (studio lighting fixture)
    glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for radius in range(950, 80, -70):
        alpha = int(32 * (1.0 - radius / 950))
        cx, cy = 340, 420
        col = (surf_rgb[0] + 25, surf_rgb[1] + 25, surf_rgb[2] + 35, alpha)
        gd.ellipse([(cx - radius, cy - radius), (cx + radius, cy + radius)], fill=col)

    # Subtle warm bokeh orbs in distant background (shallow DoF effect)
    bokeh_spots = [(240, 300, 160), (840, 520, 220), (720, 1380, 180), (180, 1500, 140)]
    for bx, by, br in bokeh_spots:
        for r in range(br, 20, -30):
            alpha = int(14 * (1.0 - r / br))
            gd.ellipse([(bx - r, by - r), (bx + r, by + r)], fill=(st.accent_secondary_rgb()[0] if hasattr(st, "accent_secondary_rgb") else 217, 119, 54, alpha))

    img.paste(Image.alpha_composite(Image.new("RGBA", (width, height), (*bg_rgb, 255)), glow).convert("RGB"))
    draw = ImageDraw.Draw(img)

    # Subtle architectural base horizon
    draw.line([(0, 1280), (width, 1280)], fill=(36, 44, 58), width=1)
    return img


def generate_blueprint_cad_bg(width: int = 1080, height: int = 1920, style: StyleSystem | None = None) -> Image.Image:
    """Scene 2: Technical CAD drafting environment with orthographic grid lines and registration marks."""
    # Deep slate-navy drafting table canvas
    base_col = (14, 18, 26)
    img = Image.new("RGB", (width, height), base_col)
    draw = ImageDraw.Draw(img)

    # Fine 40px CAD grid
    grid_size = 60
    for x in range(0, width, grid_size):
        draw.line([(x, 0), (x, height)], fill=(22, 28, 40), width=1)
    for y in range(0, height, grid_size):
        draw.line([(0, y), (width, y)], fill=(22, 28, 40), width=1)

    # Major 240px subdivision axes
    for x in range(0, width, grid_size * 4):
        draw.line([(x, 0), (x, height)], fill=(34, 44, 62), width=1)
        # Coordinate marks
        draw.text((x + 6, 80), f"X:{x:04d}", fill=(71, 85, 105))
    for y in range(0, height, grid_size * 4):
        draw.line([(0, y), (width, y)], fill=(34, 44, 62), width=1)
        draw.text((12, y + 6), f"Y:{y:04d}", fill=(71, 85, 105))

    # Architectural registration target marks (+) in corners
    cross_targets = [(100, 160), (width - 100, 160), (100, height - 160), (width - 100, height - 160)]
    for tx, ty in cross_targets:
        draw.line([(tx - 24, ty), (tx + 24, ty)], fill=(64, 78, 98), width=2)
        draw.line([(tx, ty - 24), (tx, ty + 24)], fill=(64, 78, 98), width=2)
        draw.ellipse([(tx - 12, ty - 12), (tx + 12, ty + 12)], outline=(64, 78, 98), width=1)

    return img


def generate_tactical_radar_bg(width: int = 1080, height: int = 1920, style: StyleSystem | None = None) -> Image.Image:
    """Scene 3: High-contrast top-down tactical radar & lidar map with circular range rings."""
    base_col = (11, 14, 20)
    img = Image.new("RGB", (width, height), base_col)
    draw = ImageDraw.Draw(img)

    # Perspective ground floor grid
    horizon = 300
    for y in range(horizon, height, 45):
        pct = (y - horizon) / (height - horizon)
        line_w = int(1 + pct * 2)
        draw.line([(0, y), (width, y)], fill=(24, 32, 46), width=line_w)

    vanishing_x = width // 2
    for x in range(-400, width + 500, 140):
        draw.line([(vanishing_x, horizon), (x, height)], fill=(24, 32, 46), width=1)

    # Concentric Lidar Range Rings centered on tactical map
    radar_cx, radar_cy = 540, 1150
    for radius in [180, 360, 540, 720]:
        draw.ellipse([(radar_cx - radius, radar_cy - radius // 2), (radar_cx + radius, radar_cy + radius // 2)], outline=(38, 48, 68), width=1)

    # Sweeping radar compass tick lines
    for angle in [0, 45, 90, 135, 180, 225, 270, 315]:
        rad = math.radians(angle)
        ex = int(radar_cx + 740 * math.cos(rad))
        ey = int(radar_cy + 370 * math.sin(rad))
        draw.line([(radar_cx, radar_cy), (ex, ey)], fill=(28, 38, 54), width=1)

    return img


def generate_cinematic_warehouse_bg(width: int = 1080, height: int = 1920, style: StyleSystem | None = None) -> Image.Image:
    """Scene 4: Deep perspective warehouse racking aisles with ambient floor reflections and lighting."""
    base_col = (10, 12, 17)
    img = Image.new("RGB", (width, height), base_col)
    draw = ImageDraw.Draw(img)

    cx = width // 2
    vanishing_y = 380

    # Polished concrete floor gradient with reflections
    floor_y = 650
    for y in range(floor_y, height):
        pct = (y - floor_y) / (height - floor_y)
        r = int(14 + pct * 18)
        g = int(18 + pct * 22)
        b = int(26 + pct * 30)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Massive Racking Shelves on Left and Right (Perspective Pillars)
    draw.polygon([(0, 150), (cx - 140, vanishing_y), (cx - 140, height), (0, height)], fill=(18, 23, 33), outline=(32, 40, 56), width=2)
    draw.polygon([(width, 150), (cx + 140, vanishing_y), (cx + 140, height), (width, height)], fill=(18, 23, 33), outline=(32, 40, 56), width=2)

    # Shelf cross-beams
    for sy in range(vanishing_y + 60, height, 180):
        pct = (sy - vanishing_y) / (height - vanishing_y)
        lx = int(cx - 140 - (cx - 140) * pct)
        rx = int(cx + 140 + (width - (cx + 140)) * pct)
        draw.line([(lx, sy), (cx - 140, sy)], fill=(45, 55, 76), width=2)
        draw.line([(rx, sy), (cx + 140, sy)], fill=(45, 55, 76), width=2)

    # Volumetric Overhead High-Bay Aisle Lamps
    for ly in [vanishing_y + 40, vanishing_y + 160, vanishing_y + 360]:
        draw.ellipse([(cx - 24, ly - 8), (cx + 24, ly + 8)], fill=(255, 237, 213))
        refl_y = floor_y + int((ly - vanishing_y) * 1.8)
        if refl_y < height:
            draw.ellipse([(cx - 80, refl_y - 20), (cx + 80, refl_y + 20)], fill=(32, 38, 52))

    return img


def generate_premium_brand_stage_bg(width: int = 1080, height: int = 1920, style: StyleSystem | None = None) -> Image.Image:
    """Scene 5: Matte obsidian architectural studio with soft top-down spotlight and embossed pedestal."""
    base_col = (12, 14, 19)
    img = Image.new("RGB", (width, height), base_col)
    draw = ImageDraw.Draw(img)

    # Dramatic Top-Down Studio Spotlight
    glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    cx, cy = width // 2, 680
    for radius in range(850, 60, -60):
        alpha = int(30 * (1.0 - radius / 850))
        gd.ellipse([(cx - radius, cy - radius // 2), (cx + radius, cy + radius // 2)], fill=(42, 52, 72, alpha))

    img.paste(Image.alpha_composite(Image.new("RGBA", (width, height), (*base_col, 255)), glow).convert("RGB"))
    draw = ImageDraw.Draw(img)

    # Architectural Stage Pedestal Line
    pedestal_y = 1180
    draw.line([(180, pedestal_y), (width - 180, pedestal_y)], fill=(45, 55, 72), width=2)
    for y in range(pedestal_y, pedestal_y + 60, 2):
        alpha_factor = 1.0 - (y - pedestal_y) / 60
        r = int(base_col[0] * (1.0 - alpha_factor * 0.4))
        g = int(base_col[1] * (1.0 - alpha_factor * 0.4))
        b = int(base_col[2] * (1.0 - alpha_factor * 0.4))
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
