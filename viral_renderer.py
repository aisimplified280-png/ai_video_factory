"""
VIRAL_SHORT_V2 — Deterministic High-Retention Cinematic Scene Renderer.

All drawing functions here are pure procedural PIL drawing — zero LLM code execution,
zero arbitrary coordinates. AI provides content data; this engine owns all visual
composition, 3-layer depth parallax, kinetic typography, and procedural events.
"""
from __future__ import annotations
import math
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# Template constants & safe zones
from viral_template import (
    W, H, FPS,
    ZONE_A, ZONE_B, ZONE_C, ZONE_D, ZONE_E,
    BACKGROUND_0, BACKGROUND_1, PANEL, PANEL_2, PANEL_GLOW,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_DIM,
    ACCENT, ACCENT_2, ACCENT_CYAN, ACCENT_GOLD, SUCCESS, WARNING, DANGER,
    ROLE_HOOK, ROLE_PROBLEM, ROLE_PROCESS, ROLE_PROOF, ROLE_PAYOFF, ROLE_CTA,
    ROLE_ACCENTS, ROLE_SCALES,
    HERO_FALLBACK, HERO_PRIMITIVES,
    ZoneLayout, sanitize_text, truncate_headline,
    CAPTION_CX, CAPTION_Y, CAPTION_MAX_W,
    HEADLINE_MAX_W,
)

# Animation helpers
from animation import (
    _f, _center, _box, _circle, _arrow, _rect, ease_out_back, ease_out_cubic,
    ease_out_elastic, ease_in_out_quad, _lerp,
)
from viral_template import get_brand_theme

# ── Typography ────────────────────────────────────────────────────────────
FT_VIRAL   = _f(100, True)        # Climax / Payoff word
FH1_VIRAL  = _f(76,  True)        # Giant headline
FH2_VIRAL  = _f(58,  True)        # Subhead / Section title
FB_VIRAL   = _f(40,  False)       # Editorial body text
FS_VIRAL   = _f(30,  False)       # Micro annotations
FL_VIRAL   = _f(26,  True)        # Badge / status labels
FMONO_V    = _f(32,  False, True) # Code / Terminal monospace
FNUM_V     = _f(180, True)        # Giant Numeric Stat
FBRAND_V   = _f(28,  True)        # Brand header

# ── Color Utility Functions ───────────────────────────────────────────────
def _hex_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c*2 for c in h)
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _rgba(h: str, a: int = 255) -> tuple[int, int, int, int]:
    r, g, b = _hex_rgb(h)
    return (r, g, b, max(0, min(255, int(a))))


def _lerp_color(c1: str, c2: str, t: float) -> str:
    r1, g1, b1 = _hex_rgb(c1)
    r2, g2, b2 = _hex_rgb(c2)
    return "#{:02x}{:02x}{:02x}".format(
        int(_lerp(r1, r2, t)), int(_lerp(g1, g2, t)), int(_lerp(b1, b2, t))
    )


def _ping_pong_value(t_seconds: float, period: float = 1.0) -> float:
    """Continuous triangle-wave motion with no abrupt reset at cycle boundaries."""
    if period <= 0:
        return 0.0
    cycle = t_seconds % period
    return 1.0 - abs((2.0 * cycle / period) - 1.0)


# ── Procedural Glow & Bloom Utility (High Performance) ────────────────────
def _render_glow_bloom(img: Image.Image, cx: int, cy: int, r: int,
                       color: str, intensity: float = 0.6) -> None:
    """Ultra-fast procedural concentric glow bloom — canvas-edge clamped."""
    glow_r = max(8, int(r * 1.4))
    glow = Image.new("RGBA", (glow_r * 2 + 8, glow_r * 2 + 8), (0, 0, 0, 0))
    dg = ImageDraw.Draw(glow)
    r_, g_, b_ = _hex_rgb(color)
    steps = 8
    for i in range(steps, 0, -1):
        rad = int(glow_r * (i / steps))
        alpha = int(intensity * 34 * ((1.0 - (i / steps)) ** 1.3))
        dg.ellipse((glow_r - rad + 4, glow_r - rad + 4, glow_r + rad + 4, glow_r + rad + 4),
                   fill=(r_, g_, b_, alpha))
    # Clamp paste position to prevent PIL out-of-bounds errors
    px = max(0, cx - glow_r - 4)
    py = max(0, cy - glow_r - 4)
    img.paste(glow, (px, py), glow)


# ══════════════════════════════════════════════════════════════════════════
# 1. THREE-LAYER DEPTH SYSTEM & PARALLAX BACKGROUND
# ══════════════════════════════════════════════════════════════════════════

def render_viral_background(img: Image.Image, t_seconds: float = 0.0,
                            role: str = ROLE_HOOK) -> None:
    """
    3-Layer Depth System:
      - Layer 1 (0.10x): Deep dark base (#070A12) + role-tinted radial ambient bloom
      - Layer 2 (0.25x): Perspective cyber grid + moving scanbeam
      - Layer 3 (0.35x): Floating ambient stardust particles with continuous sin/cos drift
    """
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, W, H), fill=BACKGROUND_0)

    color_a, color_b = ROLE_ACCENTS.get(role, (ACCENT, ACCENT_2))
    r1, g1, b1 = _hex_rgb(color_a)
    r2, g2, b2 = _hex_rgb(color_b)

    # Single RGBA overlay for Bloom + Grid + Scanbeam + Stardust
    bg_overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    do = ImageDraw.Draw(bg_overlay)

    # Ambient radial bloom — role-tuned intensity for scene variety
    hero_cy = 920
    bloom_intensity = {
        ROLE_HOOK: 20, ROLE_PROBLEM: 14, ROLE_PROCESS: 16,
        ROLE_PROOF: 18, ROLE_PAYOFF: 22, ROLE_CTA: 12,
    }.get(role, 16)
    for i in range(8, 0, -1):
        rad = int(400 * (i / 8))
        alpha = int(bloom_intensity * ((1.0 - (i / 8)) ** 1.2))
        do.ellipse((W // 2 - rad, hero_cy - rad, W // 2 + rad, hero_cy + rad),
                   fill=(r1, g1, b1, alpha))
    for i in range(5, 0, -1):
        rad = int(240 * (i / 5))
        alpha = int((bloom_intensity - 4) * ((1.0 - (i / 5)) ** 1.2))
        do.ellipse((W // 2 - rad, hero_cy + 60 - rad, W // 2 + rad, hero_cy + 60 + rad),
                   fill=(r2, g2, b2, alpha))

    # Grid lines — subtle perspective
    grid_step = 108
    for y in range(0, H, grid_step):
        do.line([(0, y), (W, y)], fill=(255, 255, 255, 4), width=1)
    for x in range(0, W, grid_step):
        do.line([(x, 0), (x, H)], fill=(255, 255, 255, 3), width=1)

    # Moving scan line sweep — smooth triangle-wave motion, no modulo resets.
    scan_y = int(H * _ping_pong_value(t_seconds * 0.5, 1.0))
    for si in range(3):
        alpha_s = max(0, 12 - si * 4)
        do.line([(0, scan_y + si), (W, scan_y + si)], fill=(r2, g2, b2, alpha_s), width=1)

    # Stardust particles — fixed seed per role for scene-to-scene visual consistency
    role_seed = {"hook": 1337, "problem": 2448, "process": 3559,
                 "proof": 4670, "payoff": 5781, "cta": 6892}.get(role, 1337)
    rng = random.Random(role_seed)
    for i in range(20):
        base_x = rng.randint(40, W - 40)
        base_y = rng.randint(80, H - 160)
        drift_speed = rng.uniform(6.0, 18.0)
        phase = rng.uniform(0, math.pi * 2)

        px = int(max(6, min(W - 6, base_x + math.sin(t_seconds * 0.35 + phase) * 18)))
        py = int(max(120, min(H - 120, base_y - t_seconds * drift_speed)))
        pr = rng.randint(1, 3)

        c_choice = [color_a, color_b, TEXT_SECONDARY, TEXT_DIM][rng.randint(0, 3)]
        r_, g_, b_ = _hex_rgb(c_choice)
        alpha_p = rng.randint(25, 65)
        do.ellipse((px - pr, py - pr, px + pr, py + pr), fill=(r_, g_, b_, alpha_p))

    img.paste(bg_overlay, (0, 0), bg_overlay)


# ══════════════════════════════════════════════════════════════════════════
# 2. BRAND HEADER & SAFE STRIP (ZONE A)
# ══════════════════════════════════════════════════════════════════════════

def render_viral_header(d: ImageDraw.Draw, counter: int, total: int,
                        progress: float, t_seconds: float = 0.0) -> None:
    """Zone A sleek brand header with live pulsing status light."""
    s = min(1.0, progress * 3.0)
    if s < 0.02:
        return

    theme = get_brand_theme()
    brand_y = (ZONE_A[0] + ZONE_A[1]) // 2  # ~95px
    pill_w, pill_h = 330, 46
    px1 = 36
    py1 = brand_y - pill_h // 2

    # Brand pill with translucent glassmorphic backdrop
    pill_buf = Image.new("RGBA", (pill_w, pill_h), (0, 0, 0, 0))
    dp = ImageDraw.Draw(pill_buf)
    dp.rounded_rectangle((0, 0, pill_w, pill_h), radius=23,
                         fill=_rgba(PANEL_2, int(220 * s)),
                         outline=_rgba(theme.colors["brand_primary"], int(180 * s)), width=1)

    # Pulsing live indicator dot
    pulse_alpha = int(180 + 75 * math.sin(t_seconds * 4.0))
    dp.ellipse((14, pill_h // 2 - 5, 24, pill_h // 2 + 5), fill=_rgba(theme.colors["brand_secondary"], min(255, pulse_alpha)))
    dp.text((38, pill_h // 2), theme.name.upper(), font=FBRAND_V,
            fill=_rgba(TEXT_PRIMARY, int(255 * s)), anchor="lm")
    d._image.paste(pill_buf, (px1, py1), pill_buf)

    # Right: Scene role / step counter
    if total > 1:
        ctr_text = f"{counter:02d} / {total:02d}"
        d.text((W - 48, brand_y), ctr_text, font=FL_VIRAL,
               fill=_rgba(TEXT_DIM, int(220 * s)), anchor="rm")

    # Separator beam with glowing center
    sep_y = ZONE_A[1]
    sep_overlay = Image.new("RGBA", (W, 2), (0, 0, 0, 0))
    ds = ImageDraw.Draw(sep_overlay)
    r_, g_, b_ = _hex_rgb(theme.colors["brand_primary"])
    ds.line([(0, 0), (W, 0)], fill=(r_, g_, b_, int(45 * s)), width=1)
    d._image.paste(sep_overlay, (0, sep_y), sep_overlay)


# ══════════════════════════════════════════════════════════════════════════
# 3. KINETIC EDITORIAL HEADLINE (ZONE B)
# ══════════════════════════════════════════════════════════════════════════

def render_viral_headline(d: ImageDraw.Draw, text: str, layout: ZoneLayout,
                          progress: float, accent_color: str = ACCENT,
                          t_seconds: float = 0.0) -> None:
    """
    Kinetic editorial headline in Zone B.
    Bolds dominant keyword and applies radiant sweep underbar.
    Fixed: better font thresholds, safe word-wrap with textbbox error handling.
    """
    text = sanitize_text(text, "")
    if not text:
        return

    s = ease_out_back(min(1.0, progress * 1.1))
    if s < 0.02:
        return

    fnt = FT_VIRAL if len(text) <= 14 else (FH1_VIRAL if len(text) <= 26 else FH2_VIRAL)
    words = text.upper().split()
    max_w = layout.headline_max_w

    # Wrap to max 2 punchy lines — safe single-word fallback
    lines = []
    curr = []
    for w in words:
        test = " ".join(curr + [w])
        try:
            bb = d.textbbox((0, 0), test, font=fnt, anchor="mm")
            line_w = bb[2] - bb[0]
        except Exception:
            line_w = len(test) * 40
        if line_w <= max_w:
            curr.append(w)
        else:
            if curr:
                lines.append(" ".join(curr))
            curr = [w]
        if len(lines) >= 2:
            break
    if curr:
        lines.append(" ".join(curr))
    lines = lines[:2]

    line_h = fnt.size + 16
    total_h = len(lines) * line_h
    start_y = layout.headline_y - total_h // 2
    start_y = max(ZONE_B[0] + 15, start_y)

    for i, line in enumerate(lines):
        ly = int(start_y + i * line_h + line_h // 2)
        ly = min(ZONE_B[1] - 20, ly)
        offset_y = int((1.0 - s) * 48)

        d.text((layout.headline_x, ly - offset_y), line,
               font=fnt, fill=TEXT_PRIMARY, anchor="mm")

    # Accent Kinetic Sweep Underbar
    if progress > 0.35:
        bar_s = ease_out_cubic(min(1.0, (progress - 0.35) * 2.2))
        bar_w = int(HEADLINE_MAX_W * 0.28 * bar_s)
        bar_y = start_y + total_h + 10
        if bar_y < ZONE_B[1] - 8:
            theme = get_brand_theme()
            r_, g_, b_ = _hex_rgb(theme.colors["brand_secondary"])
            d.rounded_rectangle(
                (layout.headline_x - bar_w // 2, bar_y,
                 layout.headline_x + bar_w // 2, bar_y + 5),
                radius=3, fill=(r_, g_, b_, 240))


# ══════════════════════════════════════════════════════════════════════════
# 4. PROCEDURAL VISUAL EVENTS (MIDGROUND LAYER 2)
# ══════════════════════════════════════════════════════════════════════════

def render_particle_burst(img: Image.Image, cx: int, cy: int,
                          t_seconds: float, progress: float,
                          color: str = ACCENT_2) -> None:
    """Procedural outward expanding particle burst — canvas-edge clamped."""
    if progress < 0.15:
        return
    burst_s = ease_out_cubic(min(1.0, (progress - 0.15) * 1.8))
    n_sparks = 16
    r_, g_, b_ = _hex_rgb(color)

    spark_overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ds = ImageDraw.Draw(spark_overlay)

    for i in range(n_sparks):
        angle = (2 * math.pi * i / n_sparks) + i * 0.3
        dist = int(220 * burst_s + 12 * math.sin(t_seconds * 3.0 + i))
        sx = max(4, min(W - 4, cx + int(dist * math.cos(angle))))
        sy = max(4, min(H - 4, cy + int(dist * 0.85 * math.sin(angle))))
        sr = max(1, int(4 * (1.0 - burst_s * 0.7)))
        alpha_s = max(0, int(200 * (1.0 - burst_s * 0.85)))
        ds.ellipse((sx - sr, sy - sr, sx + sr, sy + sr), fill=(r_, g_, b_, alpha_s))

    img.paste(spark_overlay, (0, 0), spark_overlay)


def render_impact_ring(img: Image.Image, cx: int, cy: int,
                       t_seconds: float, progress: float,
                       color: str = ACCENT) -> None:
    """Expanding radiant shockwave impact ring — clamped to canvas bounds."""
    if progress < 0.20:
        return
    ring_s = ease_out_cubic(min(1.0, (progress - 0.20) * 1.5))
    ring_r = int(360 * ring_s)
    alpha = max(0, int(170 * (1.0 - ring_s)))
    if ring_r < 10 or alpha <= 0:
        return
    # Validate bounding box stays on canvas
    if cx - ring_r >= W or cy - ring_r >= H or cx + ring_r <= 0 or cy + ring_r <= 0:
        return

    ring_buf = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(ring_buf)
    r_, g_, b_ = _hex_rgb(color)
    dr.ellipse((cx - ring_r, cy - ring_r, cx + ring_r, cy + ring_r),
               outline=(r_, g_, b_, alpha), width=3)
    img.paste(ring_buf, (0, 0), ring_buf)


# ══════════════════════════════════════════════════════════════════════════
# 5. SIX VISUAL SCENE GRAMMARS & HERO PRIMITIVES (FOREGROUND LAYER 3)
# ══════════════════════════════════════════════════════════════════════════

# ──────────────────────────────────────────────────────────────────────────
# SCENE 1 — IMPACT HOOK: Dominant Hero with 3D Depth & Rings
# ──────────────────────────────────────────────────────────────────────────

def render_hero_orb(img: Image.Image, layout: ZoneLayout,
                    label: str, t_seconds: float, progress: float,
                    color_a: str = ACCENT, color_b: str = ACCENT_CYAN) -> None:
    """Luminous AI core with tilted 3D orbital rings and active satellite nodes."""
    s = ease_out_back(min(1.0, progress * 1.2))
    if s < 0.02:
        return

    cx, cy = layout.hero_cx, layout.hero_cy
    core_r = int(min(layout.hero_w, layout.hero_h) * 0.32 * s)

    # Procedural effects
    render_particle_burst(img, cx, cy, t_seconds, progress, color_b)
    render_impact_ring(img, cx, cy, t_seconds, progress, color_a)

    # Multi-layered glow
    _render_glow_bloom(img, cx, cy, core_r, color_a, 0.8 + 0.15 * math.sin(t_seconds * 2.0))
    _render_glow_bloom(img, cx, cy, int(core_r * 0.6), color_b, 0.9)

    # Tilted 3D Orbital Rings (Midground)
    for i, ring_scale in enumerate([1.15, 1.55, 1.95]):
        ring_r = int(core_r * ring_scale)
        tilt_y = 0.52 + i * 0.08
        rot_angle = t_seconds * (0.6 - i * 0.15)
        
        ring_buf = Image.new("RGBA", (ring_r * 2 + 8, int(ring_r * 2 * tilt_y) + 8), (0, 0, 0, 0))
        dr = ImageDraw.Draw(ring_buf)
        r_, g_, b_ = _hex_rgb(color_a if i % 2 == 0 else color_b)
        alpha_ring = int((140 - i * 30) * s)
        
        dr.ellipse((4, 4, ring_r * 2 + 4, int(ring_r * 2 * tilt_y) + 4),
                   outline=(r_, g_, b_, alpha_ring), width=2)
        img.paste(ring_buf, (cx - ring_r - 4, cy - int(ring_r * tilt_y) - 4), ring_buf)

    # Concentric Luminous Sphere Core
    core_buf = Image.new("RGBA", (core_r * 2 + 8, core_r * 2 + 8), (0, 0, 0, 0))
    dc = ImageDraw.Draw(core_buf)
    for ri in range(core_r, 0, -6):
        t_frac = 1.0 - (ri / core_r)
        col_blend = _lerp_color(color_a, color_b, t_frac)
        r_, g_, b_ = _hex_rgb(col_blend)
        alpha_core = int(180 + 75 * t_frac)
        dc.ellipse((core_r - ri + 4, core_r - ri + 4, core_r + ri + 4, core_r + ri + 4),
                   fill=(r_, g_, b_, alpha_core))

    # Inner bright hot-spot
    hot_r = int(core_r * 0.35)
    dc.ellipse((core_r - hot_r + 4, core_r - hot_r + 4, core_r + hot_r + 4, core_r + hot_r + 4),
               fill=(255, 255, 255, 240))
    img.paste(core_buf, (cx - core_r - 4, cy - core_r - 4), core_buf)

    # Orbiting Satellite Energy Particles
    n_satellites = 6
    for i in range(n_satellites):
        orbit_angle = (2 * math.pi * i / n_satellites) + t_seconds * 1.4
        orbit_rx = int(core_r * 1.6)
        orbit_ry = int(core_r * 0.8)
        px_s = cx + int(orbit_rx * math.cos(orbit_angle))
        py_s = cy + int(orbit_ry * math.sin(orbit_angle))
        
        pr = 6
        sat_col = color_b if i % 2 == 0 else color_a
        r_, g_, b_ = _hex_rgb(sat_col)
        sat_buf = Image.new("RGBA", (pr * 2 + 4, pr * 2 + 4), (0, 0, 0, 0))
        dsat = ImageDraw.Draw(sat_buf)
        dsat.ellipse((2, 2, pr * 2 + 2, pr * 2 + 2), fill=(r_, g_, b_, 240))
        img.paste(sat_buf, (px_s - pr - 2, py_s - pr - 2), sat_buf)

    # Hero Label (Optional)
    if label and progress > 0.45:
        lbl = sanitize_text(label)
        d = ImageDraw.Draw(img)
        d.text((cx, cy + core_r + 48), lbl.upper(), font=FL_VIRAL,
               fill=TEXT_SECONDARY, anchor="mm")


# ──────────────────────────────────────────────────────────────────────────
# SCENE 2 — PROBLEM: Visual Conflict & Broken Energy Conduits
# ──────────────────────────────────────────────────────────────────────────

def render_comparison_split(img: Image.Image, layout: ZoneLayout,
                            left: str, right: str, t_seconds: float, progress: float) -> None:
    """Visual conflict between two opposing systems separated by energy fissure."""
    s = ease_out_back(min(1.0, progress * 1.1))
    if s < 0.02:
        return

    cx, cy = layout.hero_cx, layout.hero_cy
    half_w = int(layout.hero_w * 0.42 * s)
    node_h = int(layout.hero_h * 0.55 * s)
    gap = 70

    # Left Conflict Node (Problem / Broken state)
    lx = cx - gap // 2 - half_w
    ly = cy - node_h // 2
    _render_glow_bloom(img, lx + half_w // 2, cy, half_w // 2, DANGER, 0.4)

    card_l = Image.new("RGBA", (half_w, node_h), (0, 0, 0, 0))
    dl = ImageDraw.Draw(card_l)
    dl.rounded_rectangle((0, 0, half_w, node_h), radius=24,
                         fill=_rgba(PANEL, 235), outline=_rgba(DANGER, 220), width=3)
    # Warning status badge inside left node
    dl.rounded_rectangle((20, 20, half_w - 20, 56), radius=12, fill=_rgba(DANGER, 60))
    dl.text((half_w // 2, 38), "SYSTEM A (BLOCKED)", font=FL_VIRAL, fill=DANGER, anchor="mm")
    
    # Broken communication glyph
    dl.text((half_w // 2, node_h // 2), sanitize_text(left, "REQUEST ERROR"),
            font=FB_VIRAL, fill=TEXT_PRIMARY, anchor="mm")
    img.paste(card_l, (lx, ly), card_l)

    # Right Conflict Node (Target / Isolated state)
    rx = cx + gap // 2
    ry = cy - node_h // 2
    _render_glow_bloom(img, rx + half_w // 2, cy, half_w // 2, WARNING, 0.4)

    card_r = Image.new("RGBA", (half_w, node_h), (0, 0, 0, 0))
    dr = ImageDraw.Draw(card_r)
    dr.rounded_rectangle((0, 0, half_w, node_h), radius=24,
                         fill=_rgba(PANEL, 235), outline=_rgba(WARNING, 220), width=3)
    dr.rounded_rectangle((20, 20, half_w - 20, 56), radius=12, fill=_rgba(WARNING, 60))
    dr.text((half_w // 2, 38), "SYSTEM B (DISCONNECTED)", font=FL_VIRAL, fill=WARNING, anchor="mm")
    
    dr.text((half_w // 2, node_h // 2), sanitize_text(right, "NO CONNECTION"),
            font=FB_VIRAL, fill=TEXT_PRIMARY, anchor="mm")
    img.paste(card_r, (rx, ry), card_r)

    # Central Jagged Energy Fissure / Conflict Clash
    if progress > 0.35:
        fissure_overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        df = ImageDraw.Draw(fissure_overlay)
        # Jagged lightning lines
        shake = int(math.sin(t_seconds * 20.0) * 4)
        points = [
            (cx + shake, cy - node_h // 2 - 20),
            (cx - 12 + shake, cy - node_h // 4),
            (cx + 14 + shake, cy),
            (cx - 10 + shake, cy + node_h // 4),
            (cx + shake, cy + node_h // 2 + 20)
        ]
        df.line(points, fill=_rgba(DANGER, 240), width=4)
        # Conflict ✕ Icon
        vs_r = 38
        df.ellipse((cx - vs_r, cy - vs_r, cx + vs_r, cy + vs_r),
                   fill=_rgba(DANGER, 240), outline=_rgba(TEXT_PRIMARY, 240), width=3)
        df.text((cx, cy), "✕", font=FH2_VIRAL, fill=TEXT_PRIMARY, anchor="mm")
        img.paste(fissure_overlay, (0, 0), fissure_overlay)


# ──────────────────────────────────────────────────────────────────────────
# SCENE 3 — PROCESS: Flowing Data Conduits & Dynamic Active Packets
# ──────────────────────────────────────────────────────────────────────────

def render_pipeline(img: Image.Image, layout: ZoneLayout,
                    steps: list, t_seconds: float, progress: float) -> None:
    """Flowing data environment: REQUEST → API → SERVER → RESPONSE with travelling packets.
    
    Improved: alternating label positions above/below, active-node pulsing glow.
    """
    if not steps:
        steps = ["REQUEST", "API BRIDGE", "SERVER", "RESPONSE"]
    n = min(len(steps), 4)
    s = ease_out_cubic(min(1.0, progress))

    cx, cy = layout.hero_cx, layout.hero_cy
    total_w = int(layout.hero_w * 0.90)
    node_r = 60

    # Calculate horizontal distribution
    x_positions = []
    for i in range(n):
        xp = int(cx - total_w // 2 + (total_w * i // max(n - 1, 1))) if n > 1 else cx
        x_positions.append(xp)

    # 1. Flowing Data Conduit Lines with Animated Travelling Packets
    conduit_overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dc = ImageDraw.Draw(conduit_overlay)

    for i in range(n - 1):
        x1 = x_positions[i]
        x2 = x_positions[i + 1]

        # Conduit base
        r_c, g_c, b_c = _hex_rgb(ACCENT_CYAN)
        dc.line([(x1, cy), (x2, cy)], fill=(r_c, g_c, b_c, 80), width=6)

        # Travelling data packet along conduit with a smooth ping-pong path.
        packet_t = _ping_pong_value(t_seconds * 1.6 + i * 0.4, 1.0)
        packet_x = int(_lerp(x1, x2, packet_t))
        packet_x = max(node_r + 5, min(W - node_r - 5, packet_x))
        dc.ellipse((packet_x - 8, cy - 8, packet_x + 8, cy + 8),
                   fill=(255, 255, 255, 255))
        dc.ellipse((packet_x - 14, cy - 14, packet_x + 14, cy + 14),
                   fill=(r_c, g_c, b_c, 120))

    img.paste(conduit_overlay, (0, 0), conduit_overlay)

    # 2. Glowing Step Nodes
    d = ImageDraw.Draw(img)
    active_node = int(_ping_pong_value(t_seconds * 1.8, float(n)) * max(1, n - 1))
    for i, (step_txt, xp) in enumerate(zip(steps[:n], x_positions)):
        node_prog = min(1.0, max(0.0, (progress - i * 0.15) / 0.30))
        ns = ease_out_back(node_prog)
        if ns < 0.02:
            continue

        nr = int(node_r * ns)
        is_active = (active_node == i)
        node_col = ACCENT_CYAN if is_active else ACCENT

        # Active-node gets brighter glow
        glow_intensity = 0.55 * ns + (0.25 if is_active else 0.0)
        _render_glow_bloom(img, xp, cy, nr, node_col, glow_intensity)

        # 3D Node Shell
        d2 = ImageDraw.Draw(img)
        d2.ellipse((xp - nr, cy - nr, xp + nr, cy + nr),
                   fill=PANEL_2, outline=node_col, width=3)

        # Inner step index
        d2.text((xp, cy - 4), str(i + 1), font=FH2_VIRAL, fill=TEXT_PRIMARY, anchor="mm")

        # Step Label alternates above/below to prevent crowding
        if node_prog > 0.4:
            lbl = sanitize_text(str(step_txt), "")
            label_offset = nr + 36 if i % 2 == 0 else -(nr + 36)
            label_y = max(ZONE_C[0] + 10, min(ZONE_C[1] - 10, cy + label_offset))
            d2.text((xp, label_y), lbl.upper(), font=FS_VIRAL,
                    fill=ACCENT_CYAN if is_active else TEXT_SECONDARY, anchor="mm")


def render_data_stream(img: Image.Image, layout: ZoneLayout,
                       left_label: str, center_label: str, right_label: str,
                       t_seconds: float, progress: float) -> None:
    """3-node directional data flow with continuous conduit pulses."""
    render_pipeline(img, layout, [left_label, center_label, right_label], t_seconds, progress)


# ──────────────────────────────────────────────────────────────────────────
# SCENE 4 — PROOF / DEMO: Perspective Terminal & Live Code/Browser Shell
# ──────────────────────────────────────────────────────────────────────────

def render_code_panel(img: Image.Image, layout: ZoneLayout,
                      lines: list, t_seconds: float, progress: float) -> None:
    """Perspective IDE/terminal mockup with active typing cursor and drop shadow."""
    s = ease_out_back(min(1.0, progress * 1.1))
    if s < 0.02:
        return

    cx, cy = layout.hero_cx, layout.hero_cy
    pw = int(layout.hero_w * 0.92 * s)
    ph = int(layout.hero_h * 0.78 * s)
    x1, y1 = cx - pw // 2, cy - ph // 2

    # Depth Shadow
    _render_glow_bloom(img, cx, cy, pw // 2, ACCENT, 0.35)

    panel_buf = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    dp = ImageDraw.Draw(panel_buf)

    # Shell body
    dp.rounded_rectangle((0, 0, pw, ph), radius=24,
                         fill=_rgba("#0B0F19", 245), outline=_rgba(ACCENT, 200), width=2)

    # Header Bar
    header_h = 50
    dp.rounded_rectangle((0, 0, pw, header_h), radius=24, fill=_rgba(PANEL_2, 255))
    dp.rectangle((0, header_h - 10, pw, header_h), fill=_rgba(PANEL_2, 255))

    # Window Control Dots
    for xi, col in [(18, DANGER), (44, WARNING), (70, SUCCESS)]:
        dp.ellipse((xi, header_h // 2 - 7, xi + 14, header_h // 2 + 7), fill=_rgba(col, 255))

    # Active Tab Title
    dp.text((pw // 2, header_h // 2), "api_engine.py — LIVE EXECUTION",
            font=FL_VIRAL, fill=TEXT_SECONDARY, anchor="mm")

    # Code Lines / Output Stream
    if not lines:
        lines = [
            "import fastapi",
            "app = fastapi.FastAPI()",
            "",
            "@app.get('/api/v1/predict')",
            "def query(data: dict):",
            "    return {'status': 200, 'result': 'AI_READY'}"
        ]

    line_y = header_h + 26
    line_h_code = 40
    cursor_visible = (int(t_seconds * 3.0) % 2) == 0

    for li, line_str in enumerate(lines[:7]):
        if line_y + line_h_code > ph - 16:
            break

        # Syntax color tokens
        col = _rgba(TEXT_DIM, 220) if line_str.strip().startswith("#") else (
              _rgba(ACCENT_CYAN, 240) if any(line_str.strip().startswith(k) for k in
                                             ["import ", "from ", "def ", "return ", "@app"])
              else _rgba(TEXT_PRIMARY, 235))

        display = line_str
        if li == len(lines[:7]) - 1 and cursor_visible:
            display += " ▍"

        dp.text((28, line_y), display, font=FMONO_V, fill=col, anchor="lm")
        line_y += line_h_code

    img.paste(panel_buf, (x1, y1), panel_buf)


# ──────────────────────────────────────────────────────────────────────────
# SCENE 5 — PAYOFF: Climax Keyword Explosion & Scale Crescendo
# ──────────────────────────────────────────────────────────────────────────

def render_keyword_burst(img: Image.Image, layout: ZoneLayout,
                         keyword: str, subtitle: str,
                         t_seconds: float, progress: float) -> None:
    """Climax payoff: giant keyword occupying 70%+ width with network explosion.
    
    Improved: font auto-scales to fit canvas width safely.
    """
    s = ease_out_back(min(1.0, progress * 1.15))
    if s < 0.02:
        return

    cx, cy = layout.hero_cx, layout.hero_cy
    text = truncate_headline(keyword, 4).upper()

    # Explosive Radiant Burst Behind Climax Word
    render_particle_burst(img, cx, cy, t_seconds, progress, ACCENT_CYAN)
    render_impact_ring(img, cx, cy, t_seconds, progress, ACCENT)
    _render_glow_bloom(img, cx, cy, 320, ACCENT, 0.75 + 0.20 * math.sin(t_seconds * 2.0))

    # Giant Impact Typography — auto-fit to canvas width
    d = ImageDraw.Draw(img)
    base_size = int(140 * min(s, 1.0) * layout.scale_multiplier)
    fnt = _f(base_size, True)

    # Measure and shrink if too wide
    try:
        bb = d.textbbox((0, 0), text, font=fnt, anchor="mm")
        text_w = bb[2] - bb[0]
        if text_w > W - 80:
            shrink = (W - 80) / text_w
            base_size = max(48, int(base_size * shrink))
            fnt = _f(base_size, True)
    except Exception:
        pass

    d.text((cx, cy), text, font=fnt, fill=TEXT_PRIMARY, anchor="mm")

    if subtitle and progress > 0.40:
        sub_s = ease_out_cubic(min(1.0, (progress - 0.40) * 2.0))
        sub = sanitize_text(subtitle)
        d.text((cx, cy + base_size // 2 + 50), sub.upper(), font=FH2_VIRAL,
               fill=_rgba(ACCENT_CYAN, int(230 * sub_s)), anchor="mm")


def render_stat_burst(img: Image.Image, layout: ZoneLayout,
                      value: str, label: str, t_seconds: float, progress: float) -> None:
    """Giant numeric impact payoff."""
    render_keyword_burst(img, layout, value, label, t_seconds, progress)


# ──────────────────────────────────────────────────────────────────────────
# SCENE 6 — BRAND CTA: Holographic Brand Emblem & Subscribe Action
# ──────────────────────────────────────────────────────────────────────────

def render_cta_brand(img: Image.Image, layout: ZoneLayout,
                     t_seconds: float, progress: float) -> None:
    """Premium final-brand CTA: clean branded lockup, exact channel name, and controlled subscribe cue."""
    s = ease_out_back(min(1.0, progress * 1.15))
    if s < 0.02:
        return

    theme = get_brand_theme()
    cx, cy = layout.hero_cx, layout.hero_cy
    width, height = img.size
    safe_left, safe_top, safe_right, safe_bottom = (0, 0, width, height)
    try:
        from viral_template import brand_safe_zone
        safe_left, safe_top, safe_right, safe_bottom = brand_safe_zone(width, height)
    except Exception:
        pass

    # Subtle brand glow without overwhelming the scene.
    _render_glow_bloom(img, cx, cy, int(220 * s), theme.colors["brand_primary"], 0.38)

    d = ImageDraw.Draw(img)

    # Top brand chip
    if progress > 0.12:
        brand_bar_w = min(width - 180, 420)
        brand_bar_h = 58
        brand_x = cx - brand_bar_w // 2
        brand_y = max(80, min(180, int(height * 0.18)))
        d.rounded_rectangle((brand_x, brand_y, brand_x + brand_bar_w, brand_y + brand_bar_h), radius=29,
                            fill=_rgba(PANEL_2, 200), outline=_rgba(theme.colors["brand_primary"], 180), width=2)
        dot_x = brand_x + 22
        d.ellipse((dot_x - 6, brand_y + 22, dot_x + 6, brand_y + 34), fill=_rgba(theme.colors["brand_secondary"], 240))
        d.text((brand_x + 42, brand_y + brand_bar_h // 2), theme.name.upper(), font=FBRAND_V,
               fill=_rgba(TEXT_PRIMARY, 220), anchor="lm")

    # Main CTA lockup: "Subscribe to AI Simplified Lab"
    cta_text = theme.cta["text"]
    cta_y = int(cy + (18 if height >= width else 44))
    lead = "Subscribe to "
    branded = theme.name
    lead_font = _f(54, True)
    brand_font = _f(54, True)
    if width < 1200:
        lead_font = _f(42, True)
        brand_font = _f(42, True)

    lead_w = d.textlength(lead, font=lead_font)
    brand_w = d.textlength(branded, font=brand_font)
    total_w = lead_w + brand_w + 26
    left_x = max(safe_left + 50, cx - total_w / 2)
    right_x = min(safe_right - 50, left_x + total_w)
    left_x = max(left_x, safe_left + 32)
    right_x = min(right_x, safe_right - 32)
    badge_left = left_x + lead_w + 14
    badge_right = min(badge_left + brand_w + 20, safe_right - 32)

    # Light accent pill behind the brand name segment.
    if progress > 0.24:
        d.rounded_rectangle((badge_left - 12, cta_y - 32, badge_right + 12, cta_y + 32), radius=20,
                            fill=_rgba(theme.colors["brand_primary"], 160),
                            outline=_rgba(theme.colors["brand_secondary"], 170), width=1)
        d.text((left_x + lead_w / 2, cta_y), lead, font=lead_font, fill=_rgba(TEXT_PRIMARY, 245), anchor="mm")
        d.text((badge_left + brand_w / 2 + 6, cta_y), branded, font=brand_font,
               fill=_rgba(theme.colors["brand_secondary"], 255), anchor="mm")
    else:
        d.text((cx, cta_y), cta_text, font=_f(48, True), fill=_rgba(TEXT_PRIMARY, 210), anchor="mm")

    # Small support line for premium channel tone.
    if progress > 0.38:
        subtext = "More AI breakdowns"
        sub_y = cta_y + 76
        if height < width:
            sub_y = cta_y + 52
        d.text((cx, sub_y), subtext, font=FB_VIRAL, fill=_rgba(TEXT_SECONDARY, 220), anchor="mm")

    # Brand-safe, compact subscribe pill.
    if progress > 0.58:
        btn_w = min(width - 220, 320)
        btn_h = 68
        btn_x = cx - btn_w // 2
        btn_y = cta_y + 122
        if height < width:
            btn_y = cta_y + 90
        d.rounded_rectangle((btn_x, btn_y, btn_x + btn_w, btn_y + btn_h), radius=34,
                            fill=_rgba(theme.colors["brand_primary"], 235),
                            outline=_rgba(theme.colors["brand_secondary"], 180), width=2)
        d.text((cx, btn_y + btn_h // 2), "SUBSCRIBE", font=FL_VIRAL, fill=_rgba(TEXT_PRIMARY, 245), anchor="mm")

    # Quiet pulse confirmation to feel premium rather than flashy.
    if progress > 0.78:
        pulse_r = int(100 + 35 * math.sin(t_seconds * 6.0))
        pbuf = Image.new("RGBA", (pulse_r * 2 + 20, pulse_r * 2 + 20), (0, 0, 0, 0))
        pd = ImageDraw.Draw(pbuf)
        pd.ellipse((10, 10, pulse_r * 2 + 10, pulse_r * 2 + 10), outline=(r := _hex_rgb(theme.colors["brand_secondary"])[0], _hex_rgb(theme.colors["brand_secondary"])[1], _hex_rgb(theme.colors["brand_secondary"])[2], 100), width=2)
        img.paste(pbuf, (cx - pulse_r - 10, cta_y - pulse_r - 10), pbuf)


# ──────────────────────────────────────────────────────────────────────────
# HARDWARE / CHIP PRIMITIVE (UPGRADED)
# ──────────────────────────────────────────────────────────────────────────

def render_hero_chip(img: Image.Image, layout: ZoneLayout,
                     label: str, t_seconds: float, progress: float) -> None:
    """Microchip architecture hero with circuit traces and animated data pulse."""
    s = ease_out_back(min(1.0, progress * 1.15))
    if s < 0.02:
        return

    cx, cy = layout.hero_cx, layout.hero_cy
    chip_w = int(layout.hero_w * 0.65 * s)
    chip_h = int(chip_w * 0.85)

    _render_glow_bloom(img, cx, cy, chip_w // 2, ACCENT, 0.45)

    d = ImageDraw.Draw(img)
    x1, y1 = cx - chip_w // 2, cy - chip_h // 2

    # Chip Frame
    d.rounded_rectangle((x1, y1, x1 + chip_w, y1 + chip_h),
                        radius=20, fill=PANEL, outline=ACCENT, width=3)
    # Inner Die
    m = chip_w // 6
    d.rounded_rectangle((x1 + m, y1 + m, x1 + chip_w - m, y1 + chip_h - m),
                        radius=12, fill=PANEL_2, outline=ACCENT_CYAN, width=2)

    # Circuit traces on die surface
    trace_overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dt = ImageDraw.Draw(trace_overlay)
    r_c, g_c, b_c = _hex_rgb(ACCENT_CYAN)
    die_x1 = x1 + m + 4
    die_y1 = y1 + m + 4
    die_w = chip_w - 2 * m - 8
    die_h_v = chip_h - 2 * m - 8
    for row in range(3):
        ty = die_y1 + int(die_h_v * (row + 1) / 4)
        dt.line([(die_x1 + 10, ty), (die_x1 + die_w - 10, ty)],
                fill=(r_c, g_c, b_c, 55), width=1)
    for col in range(3):
        tx = die_x1 + int(die_w * (col + 1) / 4)
        dt.line([(tx, die_y1 + 10), (tx, die_y1 + die_h_v - 10)],
                fill=(r_c, g_c, b_c, 55), width=1)
    # Animated data pulse with continuous travel to avoid visual snaps.
    pulse_t = _ping_pong_value(t_seconds * 1.2, 1.0)
    pulse_x = int(die_x1 + 10 + (die_w - 20) * pulse_t)
    pulse_y = die_y1 + die_h_v // 2
    dt.ellipse((pulse_x - 5, pulse_y - 5, pulse_x + 5, pulse_y + 5),
               fill=(r_c, g_c, b_c, 240))
    dt.ellipse((pulse_x - 10, pulse_y - 10, pulse_x + 10, pulse_y + 10),
               fill=(r_c, g_c, b_c, 80))
    img.paste(trace_overlay, (0, 0), trace_overlay)

    # Pin Connections
    n_pins = 6
    for i in range(n_pins):
        frac = (i + 1) / (n_pins + 1)
        px_c = int(x1 + chip_w * frac)
        d.line([(px_c, y1 - 24), (px_c, y1)], fill=ACCENT_CYAN, width=3)
        d.line([(px_c, y1 + chip_h), (px_c, y1 + chip_h + 24)], fill=ACCENT_CYAN, width=3)

    # Active Scanline using a continuous triangle wave so it never jumps.
    scan_y = int(y1 + max(1, chip_h) * _ping_pong_value(t_seconds * 0.9, 1.0))
    d.line([(x1, scan_y), (x1 + chip_w, scan_y)], fill=ACCENT_CYAN, width=2)

    if label and progress > 0.45:
        d.text((cx, y1 + chip_h + 48), sanitize_text(label).upper(),
               font=FL_VIRAL, fill=TEXT_SECONDARY, anchor="mm")


def render_hero_glow(img: Image.Image, layout: ZoneLayout,
                     label: str, t_seconds: float, progress: float) -> None:
    """Universal fallback: glowing AI sphere."""
    render_hero_orb(img, layout, label, t_seconds, progress, ACCENT, ACCENT_CYAN)


# ══════════════════════════════════════════════════════════════════════════
# 6. CAPTION SYSTEM (FIXED SAFE ZONE AT Y ≈ 1710)
# ══════════════════════════════════════════════════════════════════════════

def render_viral_caption(img: Image.Image, subs: list, t_seconds: float,
                         accent_color: str = ACCENT) -> Image.Image:
    """
    Renders subtitles in the locked Zone E (Y≈1710, X=540, max width=900).
    Uses dark translucent pill with highlighted active word.

    BUG FIX: curr_x now correctly advances by (word_width + space_width) each iteration.
    """
    if not subs:
        return img

    active_sub = None
    for s in subs:
        if s["start"] <= t_seconds <= s["end"]:
            active_sub = s
            break
    if not active_sub:
        return img

    text = sanitize_text(active_sub.get("text", ""))
    words = text.split()
    if not words:
        return img

    cy_cap = CAPTION_Y
    cap_overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(cap_overlay)

    fnt = FB_VIRAL
    pad_x = 36
    word_widths = [d.textlength(w, font=fnt) for w in words]
    space_w = d.textlength(" ", font=fnt)
    total_w = sum(word_widths) + space_w * (len(words) - 1)

    sw = min(total_w + pad_x * 2, CAPTION_MAX_W)
    sh = 70
    x1 = int(CAPTION_CX - sw / 2)
    y1 = int(cy_cap - sh / 2)

    # Strict clamping to Zone E
    y1 = max(ZONE_E[0], min(ZONE_E[1] - sh, y1))
    x1 = max(50, min(W - 50 - int(sw), x1))

    # Translucent glassmorphic container
    r_, g_, b_ = _hex_rgb(BACKGROUND_1)
    d.rounded_rectangle((x1, y1, x1 + int(sw), y1 + sh),
                        radius=22, fill=(r_, g_, b_, 225),
                        outline=_rgba(ACCENT, 110), width=1)

    # Active word progression
    duration = max(active_sub["end"] - active_sub["start"], 0.1)
    t_progress = max(0.0, min(1.0, (t_seconds - active_sub["start"]) / duration))
    active_word_idx = min(int(t_progress * len(words)), len(words) - 1)

    curr_x = CAPTION_CX - total_w / 2
    for idx, (w_str, w_width) in enumerate(zip(words, word_widths)):
        if idx == active_word_idx:
            r_a, g_a, b_a = _hex_rgb(accent_color)
            hx1 = curr_x - 6
            hy1 = cy_cap - 22
            hx2 = curr_x + w_width + 6
            hy2 = cy_cap + 22
            d.rounded_rectangle((hx1, hy1, hx2, hy2), radius=6, fill=(r_a, g_a, b_a, 190))
            d.text((curr_x, cy_cap), w_str, font=fnt, fill=_rgba(TEXT_PRIMARY, 255), anchor="lm")
        else:
            d.text((curr_x, cy_cap), w_str, font=fnt, fill=_rgba(TEXT_SECONDARY, 230), anchor="lm")
        # FIXED: advance curr_x after each word (was missing, causing all words to stack at same position)
        curr_x += w_width + space_w
    img.paste(cap_overlay, (0, 0), cap_overlay)
    return img


# ══════════════════════════════════════════════════════════════════════════
# 7. OPTIONAL SUPPORTING FACT (ZONE D)
# ══════════════════════════════════════════════════════════════════════════

def render_viral_impact(d: ImageDraw.Draw, text: str, layout: ZoneLayout,
                        progress: float) -> None:
    """Renders supporting fact in Zone D only when text is non-empty."""
    text = sanitize_text(text, "")
    if not text or progress < 0.35:
        return

    s = ease_out_back(min(1.0, (progress - 0.35) / 0.45))
    if s < 0.02:
        return

    iy = max(ZONE_D[0] + 30, min(ZONE_D[1] - 30, layout.impact_y))
    fnt = FB_VIRAL
    bb = d.textbbox((0, 0), text.upper(), font=fnt, anchor="mm")
    tw = bb[2] - bb[0] + 64
    th = bb[3] - bb[1] + 28
    pill_w = max(tw, 380)

    r_, g_, b_ = _hex_rgb(PANEL_2)
    buf = Image.new("RGBA", (pill_w, th), (0, 0, 0, 0))
    db = ImageDraw.Draw(buf)
    db.rounded_rectangle((0, 0, pill_w, th), radius=th // 2,
                         fill=(r_, g_, b_, int(210 * s)),
                         outline=_rgba(ACCENT_CYAN, int(180 * s)), width=1)
    d._image.paste(buf, (layout.impact_x - pill_w // 2, iy - th // 2), buf)

    d.text((layout.impact_x, iy), text.upper(), font=fnt,
           fill=_rgba(ACCENT_CYAN, int(240 * s)), anchor="mm")


# ══════════════════════════════════════════════════════════════════════════
# 8. HERO DISPATCHER
# ══════════════════════════════════════════════════════════════════════════

# ── Phone / Browser / Dashboard Mockup Renderers ─────────────────────────

def render_phone_mockup(img: Image.Image, layout: ZoneLayout,
                        label: str, t_seconds: float, progress: float) -> None:
    """Sleek phone frame with animated app screen, notification bar, and staggered content."""
    s = ease_out_back(min(1.0, progress * 1.1))
    if s < 0.02:
        return
    cx, cy = layout.hero_cx, layout.hero_cy
    ph_w = int(min(layout.hero_w * 0.45, 320) * s)
    ph_h = int(ph_w * 2.0)
    if ph_w < 60 or ph_h < 120:
        return
    x1 = cx - ph_w // 2
    y1 = cy - ph_h // 2
    _render_glow_bloom(img, cx, cy, ph_w // 2, ACCENT_CYAN, 0.40)
    buf = Image.new("RGBA", (ph_w, ph_h), (0, 0, 0, 0))
    dp = ImageDraw.Draw(buf)
    dp.rounded_rectangle((0, 0, ph_w, ph_h), radius=max(8, int(ph_w * 0.12)),
                         fill=_rgba(PANEL, 245), outline=_rgba(ACCENT, 220), width=3)
    notch_w = int(ph_w * 0.32)
    notch_h = max(4, int(ph_h * 0.025))
    dp.rounded_rectangle((ph_w // 2 - notch_w // 2, 8, ph_w // 2 + notch_w // 2, 8 + notch_h),
                         radius=notch_h // 2, fill=_rgba(PANEL_2, 255))
    status_y = notch_h + 16
    dp.text((ph_w // 2, status_y), "9:41  ●●●●  WiFi", font=_f(13, False),
            fill=_rgba(TEXT_DIM, 180), anchor="mm")
    screen_y = status_y + 16
    app_bar_h = min(42, int(ph_h * 0.07))
    dp.rounded_rectangle((8, screen_y, ph_w - 8, screen_y + app_bar_h), radius=8,
                         fill=_rgba(ACCENT, 200))
    app_title = (sanitize_text(label, "APP") if label else "APP")[:12]
    dp.text((ph_w // 2, screen_y + app_bar_h // 2), app_title.upper(),
            font=_f(14, True), fill=_rgba(TEXT_PRIMARY, 255), anchor="mm")
    card_y = screen_y + app_bar_h + 10
    card_h = max(30, int((ph_h - card_y - int(ph_h * 0.12)) * 0.26))
    for i in range(3):
        card_prog = min(1.0, max(0.0, (progress - 0.3 - i * 0.12) / 0.25))
        if card_prog < 0.05:
            break
        cs = ease_out_cubic(card_prog)
        cy_card = card_y + i * (card_h + 8)
        cw = int((ph_w - 20) * cs)
        dp.rounded_rectangle((10, cy_card, 10 + cw, cy_card + card_h),
                             radius=6, fill=_rgba(PANEL_2, 220),
                             outline=_rgba(ACCENT_CYAN, int(110 * cs)), width=1)
        dp.ellipse((16, cy_card + 6, 30, cy_card + 20), fill=_rgba(ACCENT_CYAN, 180))
        if cw > 50:
            dp.rounded_rectangle((36, cy_card + 8, min(cw + 8, ph_w - 12), cy_card + 16),
                                 radius=3, fill=_rgba(TEXT_SECONDARY, 70))
            dp.rounded_rectangle((36, cy_card + 22, min(int(cw * 0.6) + 8, ph_w - 12), cy_card + 28),
                                 radius=3, fill=_rgba(TEXT_DIM, 50))
    hi_y = ph_h - max(8, int(ph_h * 0.05))
    dp.rounded_rectangle((ph_w // 2 - 28, hi_y, ph_w // 2 + 28, hi_y + 5),
                         radius=3, fill=_rgba(TEXT_DIM, 140))
    img.paste(buf, (x1, y1), buf)


def render_browser_mockup(img: Image.Image, layout: ZoneLayout,
                          label: str, t_seconds: float, progress: float) -> None:
    """Chrome-style browser window with URL bar, tabs, and animated page content."""
    s = ease_out_back(min(1.0, progress * 1.1))
    if s < 0.02:
        return
    cx, cy = layout.hero_cx, layout.hero_cy
    bw = int(layout.hero_w * 0.90 * s)
    bh = int(layout.hero_h * 0.70 * s)
    if bw < 100 or bh < 80:
        return
    x1, y1 = cx - bw // 2, cy - bh // 2
    _render_glow_bloom(img, cx, cy, bw // 2, ACCENT, 0.35)
    buf = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    dp = ImageDraw.Draw(buf)
    dp.rounded_rectangle((0, 0, bw, bh), radius=20,
                         fill=_rgba("#0D1117", 245), outline=_rgba(ACCENT, 200), width=2)
    title_h = 44
    dp.rounded_rectangle((0, 0, bw, title_h), radius=20, fill=_rgba(PANEL_2, 255))
    dp.rectangle((0, title_h - 8, bw, title_h), fill=_rgba(PANEL_2, 255))
    for xi, col in [(14, DANGER), (36, WARNING), (58, SUCCESS)]:
        dp.ellipse((xi, title_h // 2 - 6, xi + 12, title_h // 2 + 6), fill=_rgba(col, 255))
    tab_w = min(bw // 3, 180)
    dp.rounded_rectangle((78, 6, 78 + tab_w, title_h - 4), radius=7,
                         fill=_rgba("#0D1117", 255))
    pg = (sanitize_text(label, "Page") if label else "Loading...")[:20]
    dp.text((78 + tab_w // 2, title_h // 2), pg, font=_f(13, False),
            fill=_rgba(TEXT_SECONDARY, 210), anchor="mm")
    url_y = title_h + 8
    url_h = 30
    dp.rounded_rectangle((78, url_y, bw - 12, url_y + url_h), radius=15,
                         fill=_rgba(PANEL, 255), outline=_rgba(TEXT_DIM, 70), width=1)
    url_slug = (sanitize_text(label, "home") if label else "home").lower().replace(" ", "-")[:22]
    dp.text((bw // 2, url_y + url_h // 2), f"https://aisimplified.ai/{url_slug}",
            font=_f(12, False), fill=_rgba(TEXT_DIM, 190), anchor="mm")
    content_y = url_y + url_h + 10
    content_h = bh - content_y - 8
    hero_bh = int(content_h * 0.35)
    dp.rounded_rectangle((14, content_y, bw - 14, content_y + hero_bh),
                         radius=8, fill=_rgba(PANEL_GLOW, 200))
    if progress > 0.4:
        pulse = 0.5 + 0.5 * math.sin(t_seconds * 2.5)
        bar_w = int((bw - 80) * 0.55 * pulse)
        dp.rounded_rectangle((bw // 2 - bar_w // 2, content_y + hero_bh // 2 - 7,
                              bw // 2 + bar_w // 2, content_y + hero_bh // 2 + 7),
                             radius=4, fill=_rgba(ACCENT, int(170 * pulse)))
    line_y = content_y + hero_bh + 14
    for w_frac in [0.70, 0.52, 0.82, 0.58]:
        if line_y + 12 > content_y + content_h:
            break
        lw = int((bw - 40) * w_frac)
        dp.rounded_rectangle((20, line_y, 20 + lw, line_y + 9), radius=4,
                             fill=_rgba(TEXT_DIM, 55))
        line_y += 20
    img.paste(buf, (x1, y1), buf)


def render_dashboard_mockup(img: Image.Image, layout: ZoneLayout,
                            label: str, t_seconds: float, progress: float) -> None:
    """Analytics dashboard with animated metric tiles and bar chart."""
    s = ease_out_back(min(1.0, progress * 1.1))
    if s < 0.02:
        return
    cx, cy = layout.hero_cx, layout.hero_cy
    dw = int(layout.hero_w * 0.92 * s)
    dh = int(layout.hero_h * 0.75 * s)
    if dw < 100 or dh < 80:
        return
    x1, y1 = cx - dw // 2, cy - dh // 2
    _render_glow_bloom(img, cx, cy, dw // 2, SUCCESS, 0.35)
    buf = Image.new("RGBA", (dw, dh), (0, 0, 0, 0))
    dp = ImageDraw.Draw(buf)
    dp.rounded_rectangle((0, 0, dw, dh), radius=20,
                         fill=_rgba(PANEL, 245), outline=_rgba(SUCCESS, 180), width=2)
    hdr_h = 44
    dp.rounded_rectangle((0, 0, dw, hdr_h), radius=20, fill=_rgba(PANEL_2, 255))
    dp.rectangle((0, hdr_h - 8, dw, hdr_h), fill=_rgba(PANEL_2, 255))
    dash_title = (sanitize_text(label, "ANALYTICS") if label else "ANALYTICS")[:20]
    dp.text((dw // 2, hdr_h // 2), f"{dash_title.upper()} DASHBOARD",
            font=FL_VIRAL, fill=_rgba(TEXT_PRIMARY, 225), anchor="mm")
    tile_y = hdr_h + 10
    tile_h = int(dh * 0.22)
    tile_w = (dw - 40) // 3
    for i, (val, lbl) in enumerate([("98.7%", "UPTIME"), ("2.4ms", "LATENCY"), ("14.2K", "REQS")]):
        tp = min(1.0, max(0.0, (progress - 0.2 - i * 0.1) / 0.3))
        if tp < 0.05:
            break
        ts = ease_out_back(tp)
        tx = 14 + i * (tile_w + 6)
        tw = int(tile_w * ts)
        th = int(tile_h * ts)
        dp.rounded_rectangle((tx, tile_y, tx + tw, tile_y + th), radius=10,
                             fill=_rgba(PANEL_GLOW, 225),
                             outline=_rgba(ACCENT_CYAN, int(95 * ts)), width=1)
        if tp > 0.4:
            dp.text((tx + tw // 2, tile_y + th // 2 - 8), val,
                    font=_f(22, True), fill=_rgba(ACCENT_CYAN, 225), anchor="mm")
            dp.text((tx + tw // 2, tile_y + th // 2 + 12), lbl,
                    font=_f(11, False), fill=_rgba(TEXT_DIM, 195), anchor="mm")
    chart_y = tile_y + tile_h + 12
    chart_h = dh - chart_y - 12
    if chart_h > 40:
        dp.rounded_rectangle((12, chart_y, dw - 12, chart_y + chart_h),
                             radius=7, fill=_rgba(PANEL_2, 175))
        n_bars = 7
        bpad = 5
        bw_px = max(8, (dw - 28 - (n_bars + 1) * bpad) // n_bars)
        bar_fracs = [0.45, 0.72, 0.58, 0.90, 0.65, 0.83, 0.70]
        for bi in range(n_bars):
            bp = min(1.0, max(0.0, (progress - 0.35 - bi * 0.05) / 0.25))
            if bp < 0.05:
                break
            bh_px = int(bar_fracs[bi] * ease_out_cubic(bp) * (chart_h - 18))
            bx = 14 + bpad + bi * (bw_px + bpad)
            by = chart_y + chart_h - 8 - bh_px
            col = ACCENT_CYAN if bi == 3 else ACCENT
            dp.rounded_rectangle((bx, by, bx + bw_px, chart_y + chart_h - 8),
                                 radius=4, fill=_rgba(col, 195))
    img.paste(buf, (x1, y1), buf)


HERO_RENDERERS = {
    "hero_orb":        lambda img, L, lbl, t, p: render_hero_orb(img, L, lbl, t, p, ACCENT, ACCENT_CYAN),
    "hero_chip":       lambda img, L, lbl, t, p: render_hero_chip(img, L, lbl, t, p),
    "hero_brain":      lambda img, L, lbl, t, p: render_hero_orb(img, L, lbl, t, p, ACCENT, SUCCESS),
    "hero_robot":      lambda img, L, lbl, t, p: render_hero_chip(img, L, lbl, t, p),
    "hero_device":     lambda img, L, lbl, t, p: render_phone_mockup(img, L, lbl, t, p),
    "hero_server":     lambda img, L, lbl, t, p: render_hero_chip(img, L, lbl, t, p),
    "hero_model":      lambda img, L, lbl, t, p: render_hero_orb(img, L, lbl, t, p, ACCENT_CYAN, ACCENT),
    "hero_logo_plate": lambda img, L, lbl, t, p: render_cta_brand(img, L, t, p),
    "code_panel":      lambda img, L, lbl, t, p: render_code_panel(img, L, [], t, p),
    "data_stream":     lambda img, L, lbl, t, p: render_data_stream(img, L, "Input", lbl or "Process", "Output", t, p),
    "pipeline":        lambda img, L, lbl, t, p: render_pipeline(img, L, [], t, p),
    "stat_burst":      lambda img, L, lbl, t, p: render_stat_burst(img, L, lbl or "100x", "", t, p),
    "keyword_burst":   lambda img, L, lbl, t, p: render_keyword_burst(img, L, lbl or "AI", "", t, p),
    "comparison_split":lambda img, L, lbl, t, p: render_comparison_split(img, L, "Before", "After", t, p),
    "cta_brand":       lambda img, L, lbl, t, p: render_cta_brand(img, L, t, p),
    "hero_glow":       lambda img, L, lbl, t, p: render_hero_glow(img, L, lbl, t, p),
    "glow_ring":       lambda img, L, lbl, t, p: render_hero_orb(img, L, lbl, t, p, ACCENT_CYAN, DANGER),
    "network_node":    lambda img, L, lbl, t, p: render_pipeline(img, L, [], t, p),
    "arrow_stream":    lambda img, L, lbl, t, p: render_data_stream(img, L, "Data", lbl or "Process", "Result", t, p),
    "quote_panel":     lambda img, L, lbl, t, p: render_keyword_burst(img, L, lbl or "INSIGHT", "", t, p),
    "warning_burst":   lambda img, L, lbl, t, p: render_hero_orb(img, L, lbl, t, p, DANGER, WARNING),
    "result_reveal":   lambda img, L, lbl, t, p: render_keyword_burst(img, L, lbl or "SUCCESS", "", t, p),
    # Differentiated mockups — each renders its own unique visual
    "browser_mockup":  lambda img, L, lbl, t, p: render_browser_mockup(img, L, lbl, t, p),
    "phone_mockup":    lambda img, L, lbl, t, p: render_phone_mockup(img, L, lbl, t, p),
    "device_mockup":   lambda img, L, lbl, t, p: render_phone_mockup(img, L, lbl, t, p),
    "dashboard_mockup":lambda img, L, lbl, t, p: render_dashboard_mockup(img, L, lbl, t, p),
    "particle_field":  lambda img, L, lbl, t, p: render_hero_orb(img, L, lbl, t, p, ACCENT, ACCENT_CYAN),
    "timeline":        lambda img, L, lbl, t, p: render_pipeline(img, L, [], t, p),
}


def dispatch_hero(hero_type: str, img: Image.Image, layout: ZoneLayout,
                  label: str, visual_data: dict, t_seconds: float, progress: float) -> None:
    """Dispatch to the correct hero renderer."""
    from viral_template import resolve_hero_type
    ht = resolve_hero_type(hero_type)
    renderer = HERO_RENDERERS.get(ht, HERO_RENDERERS["hero_glow"])

    if ht == "code_panel":
        lines = visual_data.get("lines", []) if visual_data else []
        render_code_panel(img, layout, lines, t_seconds, progress)
    elif ht == "data_stream":
        vd = visual_data or {}
        render_data_stream(img, layout,
                           vd.get("left", "Input"), vd.get("center", label or "Process"),
                           vd.get("right", "Output"), t_seconds, progress)
    elif ht == "pipeline":
        steps = (visual_data or {}).get("steps", [])
        render_pipeline(img, layout, steps, t_seconds, progress)
    elif ht == "stat_burst":
        vd = visual_data or {}
        render_stat_burst(img, layout,
                          vd.get("value", label or "100x"),
                          vd.get("label", ""), t_seconds, progress)
    elif ht == "keyword_burst":
        vd = visual_data or {}
        render_keyword_burst(img, layout,
                             vd.get("keyword", label or "AI"),
                             vd.get("subtitle", ""), t_seconds, progress)
    elif ht == "comparison_split":
        vd = visual_data or {}
        render_comparison_split(img, layout,
                                vd.get("left", "Before"), vd.get("right", "After"),
                                t_seconds, progress)
    elif ht == "cta_brand":
        render_cta_brand(img, layout, t_seconds, progress)
    elif ht == "browser_mockup":
        render_browser_mockup(img, layout, label, t_seconds, progress)
    elif ht in ("phone_mockup", "device_mockup"):
        render_phone_mockup(img, layout, label, t_seconds, progress)
    elif ht == "dashboard_mockup":
        render_dashboard_mockup(img, layout, label, t_seconds, progress)
    else:
        renderer(img, layout, label, t_seconds, progress)
