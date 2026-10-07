"""Phase 16 Editorial Intelligence Procedural Visual Generator.

Generates premium, restrained, editorial-quality 1080x1920 visuals:
- Adheres strictly to the VisualDesignSystem (Editorial Intelligence)
- Warm charcoal/slate architectural and studio backgrounds (no pitch-black voids or cyan circuits)
- Strong foreground/background separation with volumetric subjects, realistic shading, and natural lighting
- True Narrative Continuity & Object Inheritance across scenes:
  Scene 1: Precision gripper close-up
  Scene 2: Multi-axis arm holding THAT EXACT GRIPPER + Claude telemetry panel
  Scene 3: Mobile rover MOUNTING THAT ARM navigating around obstacle
  Scene 4: Warehouse floor FLEET OF THESE ROVERS accelerating with payloads
  Scene 5: Brand identity embedding the core hardware silhouette
- Multi-mode compositions (Hero macro, Asymmetric split-zone, Spatial tactical, Full-bleed perspective)
- Bold Claude-style editorial typography and structured cards
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from .design_system import VisualDesignSystem, create_default_design_system
from .evidence_contract import EditorialVisualMode, VisualEvidenceContract


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


def hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    s = hex_str.lstrip("#")
    return int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)


def _draw_editorial_background(
    draw: ImageDraw.ImageDraw,
    width: int,
    height: int,
    bg_rgb: tuple[int, int, int] = (18, 21, 28),
    surface_rgb: tuple[int, int, int] = (26, 32, 44),
    draw_floor: bool = True,
) -> Image.Image:
    """Draw a rich, warm, softly illuminated architectural studio background."""
    img = Image.new("RGB", (width, height), bg_rgb)
    d = ImageDraw.Draw(img)

    # Soft radial ambient glow from top-left (key light direction)
    glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for radius in range(900, 100, -80):
        alpha = int(25 * (1.0 - radius / 900))
        cx, cy = 400, 480
        color = (surface_rgb[0] + 15, surface_rgb[1] + 15, surface_rgb[2] + 20, alpha)
        gd.ellipse([(cx - radius, cy - radius), (cx + radius, cy + radius)], fill=color)

    img.paste(Image.alpha_composite(Image.new("RGBA", (width, height), (*bg_rgb, 255)), glow).convert("RGB"))
    d = ImageDraw.Draw(img)

    if draw_floor:
        floor_y = 1200
        for y in range(floor_y, height):
            pct = (y - floor_y) / (height - floor_y)
            r = int(bg_rgb[0] * (1 - pct * 0.3) + surface_rgb[0] * (pct * 0.3))
            g = int(bg_rgb[1] * (1 - pct * 0.3) + surface_rgb[1] * (pct * 0.3))
            b = int(bg_rgb[2] * (1 - pct * 0.3) + surface_rgb[2] * (pct * 0.3))
            d.line([(0, y), (width, y)], fill=(r, g, b))

        d.line([(0, floor_y), (width, floor_y)], fill=(45, 55, 72), width=1)

        vanishing_x, vanishing_y = 540, floor_y - 200
        for fx in range(-200, width + 400, 240):
            d.line([(vanishing_x, floor_y), (fx, height)], fill=(32, 39, 52), width=1)

    return img


def render_editorial_asset(
    contract: VisualEvidenceContract,
    design_system: VisualDesignSystem | None = None,
) -> Image.Image:
    """Render a fully grounded, human-relevant editorial visual frame for a given contract."""
    ds = design_system or create_default_design_system()
    w, h = ds.composition.width, ds.composition.height

    bg_rgb = hex_to_rgb(ds.palette.background)
    surf_rgb = hex_to_rgb(ds.palette.surface)
    accent_rgb = hex_to_rgb(ds.palette.accent)
    text_rgb = hex_to_rgb(ds.palette.primary_text)
    muted_rgb = hex_to_rgb(ds.palette.secondary_text)
    border_rgb = hex_to_rgb(ds.palette.border)

    font_title = _get_font(44, bold=True)
    font_sub = _get_font(24)
    font_badge = _get_font(18, bold=True)
    font_mono = _get_font(20)

    mode = contract.visual_mode
    text_lower = f"{contract.narration} {contract.claim} {contract.primary_subject} {contract.action}".lower()

    # Shared helper to draw the distinctive titanium gripper from Scene 1
    def _draw_titanium_gripper(
        draw_ctx: ImageDraw.ImageDraw,
        cx: int,
        cy: int,
        scale: float = 1.0,
        open_angle: float = 0.0,
    ):
        """Draws the canonical titanium gripper mechanism for object continuity across scenes."""
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

    # -------------------------------------------------------------------------
    # SCENE 01: HERO MACRO (Precision Robotic Gripper Close-Up)
    # Composition: Extreme close-up hero shot, bold editorial typography, huge negative space
    # -------------------------------------------------------------------------
    if (contract.scene_id in ("scene_01", "sec_01") or any(k in text_lower for k in ["gripper", "clamping", "sub-millimeter"])) and not any(k in text_lower for k in ["robotic arm", "industrial robotic arm"]):
        img = _draw_editorial_background(None, w, h, bg_rgb, surf_rgb, draw_floor=True)
        draw = ImageDraw.Draw(img)

        # Bold Claude-style Editorial Headline (Top Left, Asymmetric)
        draw.text((120, 160), "01 // TACTILE EMBODIMENT", font=font_badge, fill=accent_rgb)
        draw.text((120, 205), "GPT-6 ASTRA ROBOTICS", font=_get_font(42, bold=True), fill=text_rgb)
        draw.text((120, 260), "SUB-MILLIMETER TACTILE CLAMPING", font=font_sub, fill=muted_rgb)
        draw.line([(120, 310), (960, 310)], fill=(45, 55, 72), width=1)

        # Hero Subject: Massive volumetric titanium gripper in center-upper canvas
        cx, cy = 540, 850
        _draw_titanium_gripper(draw, cx, cy, scale=2.2, open_angle=0.0)

        # Target Workpiece Clamped by Jaws
        wp_w, wp_h = 240, 180
        draw.rounded_rectangle([(cx - wp_w // 2, cy - wp_h // 2 + 30), (cx + wp_w // 2, cy + wp_h // 2 + 30)], radius=12, fill=(45, 55, 72), outline=(148, 163, 184), width=2)
        draw.text((cx, cy + 30), "PAYLOAD // ZERO-SLIP", font=font_mono, fill=(241, 245, 249), anchor="mm")

        # Optical laser alignment guide (Warm Amber line)
        draw.line([(cx, cy - 420), (cx, cy + 360)], fill=accent_rgb, width=2)
        draw.ellipse([(cx - 7, cy + 30 - 7), (cx + 7, cy + 30 + 7)], fill=(255, 255, 255))

        # Editorial Data Capsule (Lower Canvas, Clean Whitespace)
        card_x, card_y = 120, 1260
        card_w, card_h = 840, 100
        draw.rounded_rectangle([(card_x, card_y), (card_x + card_w, card_y + card_h)], radius=12, fill=(26, 32, 44), outline=border_rgb, width=1)
        draw.text((card_x + 32, card_y + 32), "FORCE SENSING: ACTIVE", font=font_badge, fill=accent_rgb)
        draw.text((card_x + 32, card_y + 62), "CLOSED-LOOP FEEDBACK: 1000 Hz", font=font_mono, fill=text_rgb)
        draw.text((card_x + card_w - 32, card_y + 50), "STATUS: LOCKED", font=font_badge, fill=(34, 197, 94), anchor="rm")

        return img

    # -------------------------------------------------------------------------
    # SCENE 02: ASYMMETRIC SPLIT-ZONE (Articulated Arm Holding THAT EXACT GRIPPER + Claude Telemetry Panel)
    # Composition: Left/Lower = Articulated robotic arm holding Scene 1's gripper.
    #              Right/Upper = Large editorial Claude-style structured telemetry panel.
    # -------------------------------------------------------------------------
    elif contract.scene_id in ("scene_02", "sec_02") or any(k in text_lower for k in ["robotic arm", "industrial robot", "robot arm", "actuator"]) or (
        any(k in text_lower for k in ["robot", "physical robot", "machine"]) and any(k in text_lower for k in ["control", "motor", "sensor feedback", "directly"])
    ):
        img = _draw_editorial_background(None, w, h, bg_rgb, surf_rgb, draw_floor=True)
        draw = ImageDraw.Draw(img)

        # Bold Claude-style Header
        draw.text((120, 150), "02 // NEURAL CONTROL INTERFACE", font=font_badge, fill=accent_rgb)
        draw.text((120, 195), "DIRECT PHYSICAL CONTROL", font=_get_font(38, bold=True), fill=text_rgb)

        # Right / Upper Editorial Structured Panel
        card_x, card_y = 480, 280
        card_w, card_h = 500, 360
        draw.rounded_rectangle([(card_x, card_y), (card_x + card_w, card_y + card_h)], radius=16, fill=(22, 27, 36), outline=border_rgb, width=1)
        draw.rounded_rectangle([(card_x + 24, card_y + 24), (card_x + card_w - 24, card_y + 64)], radius=8, fill=(30, 38, 52))
        draw.text((card_x + 36, card_y + 44), "TELEMETRY // CLOSED-LOOP", font=font_badge, fill=accent_rgb, anchor="lm")
        draw.text((card_x + card_w - 36, card_y + 44), "1000 Hz", font=font_mono, fill=(34, 197, 94), anchor="rm")

        rows = [
            ("SOURCE", "GPT-6 Astra Motor Bus"),
            ("LATENCY", "0.8 ms (Real-Time)"),
            ("JOINT 1", "+42.4° [TORQUE: 18 Nm]"),
            ("JOINT 2", "-18.2° [TORQUE: 24 Nm]"),
            ("END EFFECTOR", "Titanium Gripper (Active)"),
        ]
        ry = card_y + 90
        for label, val in rows:
            draw.text((card_x + 28, ry), label, font=font_badge, fill=muted_rgb)
            draw.text((card_x + card_w - 28, ry), val, font=font_mono, fill=text_rgb if "0.8" not in val else accent_rgb, anchor="ra")
            ry += 48
            draw.line([(card_x + 24, ry - 8), (card_x + card_w - 24, ry - 8)], fill=(32, 40, 54), width=1)

        # Left / Lower Canvas: Articulated Robotic Arm holding the Scene 1 Gripper!
        base_x, base_y = 360, 1420
        draw.polygon([(base_x - 180, base_y + 100), (base_x + 180, base_y + 100), (base_x + 140, base_y + 30), (base_x - 140, base_y + 30)], fill=(30, 38, 50), outline=border_rgb)
        draw.ellipse([(base_x - 140, base_y - 10), (base_x + 140, base_y + 50)], fill=(45, 55, 72), outline=border_rgb, width=2)

        elbow_x, elbow_y = 280, 1020
        draw.polygon([
            (base_x - 45, base_y),
            (base_x + 45, base_y),
            (elbow_x + 35, elbow_y),
            (elbow_x - 35, elbow_y),
        ], fill=(148, 163, 184), outline=(203, 213, 225), width=2)
        draw.ellipse([(elbow_x - 55, elbow_y - 55), (elbow_x + 55, elbow_y + 55)], fill=(51, 65, 85), outline=(203, 213, 225), width=2)
        draw.ellipse([(elbow_x - 24, elbow_y - 24), (elbow_x + 24, elbow_y + 24)], fill=accent_rgb)

        wrist_x, wrist_y = 480, 800
        draw.polygon([
            (elbow_x - 30, elbow_y),
            (elbow_x + 30, elbow_y),
            (wrist_x + 28, wrist_y),
            (wrist_x - 28, wrist_y),
        ], fill=(203, 213, 225), outline=(241, 245, 249), width=2)
        draw.ellipse([(wrist_x - 36, wrist_y - 36), (wrist_x + 36, wrist_y + 36)], fill=(51, 65, 85), outline=(203, 213, 225), width=2)

        # OBJECT CONTINUITY: Draw the EXACT Titanium Gripper from Scene 1 at the wrist!
        _draw_titanium_gripper(draw, wrist_x + 60, wrist_y + 40, scale=0.9, open_angle=8.0)

        return img

    # -------------------------------------------------------------------------
    # SCENE 03: SPATIAL TACTICAL DIAGRAM (Mobile Robot MOUNTING THAT ARM avoiding obstacle)
    # Composition: High-angle spatial layout. Mobile rover carrying Scene 2's arm and Scene 1's gripper,
    #              active lidar cone, pallet obstacle, dynamic curved bypass path.
    # -------------------------------------------------------------------------
    elif any(k in text_lower for k in ["adapt", "obstacle", "rigid", "routines", "shift"]):
        img = _draw_editorial_background(None, w, h, bg_rgb, surf_rgb, draw_floor=True)
        draw = ImageDraw.Draw(img)

        # Bold Editorial Header (Top Left)
        draw.text((120, 150), "03 // ADAPTIVE NAVIGATION", font=font_badge, fill=accent_rgb)
        draw.text((120, 195), "DYNAMIC PATH RECALCULATION", font=_get_font(38, bold=True), fill=text_rgb)
        draw.text((120, 245), "PREDICTIVE OBSTACLE AVOIDANCE IN REAL-TIME", font=font_sub, fill=muted_rgb)
        draw.line([(120, 290), (960, 290)], fill=(45, 55, 72), width=1)

        rover_x, rover_y = 380, 1360
        obstacle_x, obstacle_y = 380, 860

        # Blocked direct path (dashed gray) with Red Cross
        for y in range(rover_y - 80, obstacle_y + 70, -28):
            draw.line([(rover_x, y), (rover_x, y - 14)], fill=(75, 85, 99), width=2)
        draw.line([(rover_x - 18, obstacle_y + 70), (rover_x + 18, obstacle_y + 104)], fill=(239, 68, 68), width=3)
        draw.line([(rover_x + 18, obstacle_y + 70), (rover_x - 18, obstacle_y + 104)], fill=(239, 68, 68), width=3)

        # Dynamic curved terracotta reroute spline bypassing obstacle to the right
        spline_pts = [
            (rover_x, rover_y - 60),
            (rover_x + 80, rover_y - 200),
            (rover_x + 280, 1020),
            (rover_x + 290, 780),
            (rover_x + 120, 600),
            (rover_x, 480),
        ]
        for i in range(len(spline_pts) - 1):
            draw.line([spline_pts[i], spline_pts[i + 1]], fill=accent_rgb, width=4)
        draw.polygon([(rover_x + 276, 910), (rover_x + 296, 885), (rover_x + 296, 935)], fill=accent_rgb)
        draw.polygon([(rover_x + 196, 680), (rover_x + 216, 655), (rover_x + 216, 705)], fill=accent_rgb)

        # Physical Obstacle Pallet
        ob_w, ob_h = 220, 140
        draw.rounded_rectangle([(obstacle_x - ob_w // 2, obstacle_y - ob_h // 2), (obstacle_x + ob_w // 2, obstacle_y + ob_h // 2)], radius=10, fill=(38, 46, 60), outline=(239, 68, 68), width=2)
        for offset in range(-80, 80, 28):
            draw.line([(obstacle_x + offset, obstacle_y - 35), (obstacle_x + offset + 24, obstacle_y + 35)], fill=(217, 119, 54), width=3)
        draw.text((obstacle_x, obstacle_y + 48), "DYNAMIC OBSTACLE DETECTED", font=font_badge, fill=(241, 245, 249), anchor="mm")

        # OBJECT CONTINUITY: Autonomous Mobile Rover MOUNTING the Robotic Arm + Gripper!
        r_w, r_h = 200, 240
        for wx in [-r_w // 2 - 16, r_w // 2 + 2]:
            draw.rounded_rectangle([(rover_x + wx, rover_y - r_h // 2 + 20), (rover_x + wx + 14, rover_y - r_h // 2 + 90)], radius=4, fill=(15, 23, 42))
            draw.rounded_rectangle([(rover_x + wx, rover_y + r_h // 2 - 90), (rover_x + wx + 14, rover_y + r_h // 2 - 20)], radius=4, fill=(15, 23, 42))

        draw.rounded_rectangle([(rover_x - r_w // 2, rover_y - r_h // 2), (rover_x + r_w // 2, rover_y + r_h // 2)], radius=18, fill=(203, 213, 225), outline=(241, 245, 249), width=2)
        draw.arc([(rover_x - 180, rover_y - 280), (rover_x + 180, rover_y + 60)], start=210, end=330, fill=accent_rgb, width=3)
        draw.ellipse([(rover_x - 30, rover_y - 60), (rover_x + 30, rover_y)], fill=(30, 41, 59), outline=accent_rgb, width=2)

        # Mounted Robotic Arm on the Rover (from Scene 2 & 1)
        draw.polygon([(rover_x - 20, rover_y + 10), (rover_x + 20, rover_y + 10), (rover_x + 40, rover_y + 70), (rover_x - 40, rover_y + 70)], fill=(71, 85, 105))
        _draw_titanium_gripper(draw, rover_x, rover_y + 70, scale=0.6, open_angle=4.0)

        # Tactical Status Card (Bottom Right Floating Panel)
        draw.rounded_rectangle([(560, 1340), (960, 1450)], radius=12, fill=(22, 27, 36), outline=border_rgb, width=1)
        draw.text((580, 1370), "REROUTE LATENCY: 1.2 ms", font=font_mono, fill=accent_rgb)
        draw.text((580, 1405), "COLLISION RISK: 0.0%", font=font_badge, fill=(34, 197, 94))

        return img

    # -------------------------------------------------------------------------
    # SCENE 04: FULL-BLEED FACILITY FLOOR (Fleet of These Same Rovers Moving Synchronously)
    # Composition: Deep perspective warehouse raceway lanes, fleet of rovers accelerating,
    #              large Claude-style facility throughput card floating in perspective.
    # -------------------------------------------------------------------------
    elif mode in (EditorialVisualMode.PROCESS, EditorialVisualMode.ENVIRONMENT) or any(k in text_lower for k in ["inventory", "faster", "delay", "throughput"]):
        img = _draw_editorial_background(None, w, h, bg_rgb, surf_rgb, draw_floor=True)
        draw = ImageDraw.Draw(img)

        # Bold Editorial Header
        draw.text((120, 150), "04 // FACILITY-SCALE COORDINATION", font=font_badge, fill=accent_rgb)
        draw.text((120, 195), "SYNCHRONIZED FLEET VELOCITY", font=_get_font(38, bold=True), fill=text_rgb)

        # Large Claude-style Throughput Metrics Card (Top Right / Perspective Float)
        card_x, card_y = 120, 260
        card_w, card_h = 840, 160
        draw.rounded_rectangle([(card_x, card_y), (card_x + card_w, card_y + card_h)], radius=16, fill=(22, 27, 36), outline=border_rgb, width=1)
        draw.text((card_x + 36, card_y + 36), "FACILITY PERFORMANCE INDEX", font=font_badge, fill=accent_rgb)
        m_cols = [
            ("FLEET VELOCITY", "+340% ACCELERATION"),
            ("QUEUE DELAY", "0.0 SECONDS"),
            ("DISPATCH SYNC", "99.8% OPTIMAL"),
        ]
        mx = card_x + 36
        for m_lbl, m_val in m_cols:
            draw.text((mx, card_y + 80), m_lbl, font=font_mono, fill=muted_rgb)
            draw.text((mx, card_y + 115), m_val, font=font_badge, fill=text_rgb if "0.0" not in m_val else (34, 197, 94))
            mx += 270

        center_x = 540
        horizon_y = 480

        # Left Raceway Lane
        draw.polygon([(center_x - 30, horizon_y), (center_x - 160, horizon_y), (center_x - 460, 1750), (center_x - 40, 1750)], fill=(28, 35, 48), outline=border_rgb, width=1)
        # Right Raceway Lane
        draw.polygon([(center_x + 30, horizon_y), (center_x + 160, horizon_y), (center_x + 460, 1750), (center_x + 40, 1750)], fill=(28, 35, 48), outline=border_rgb, width=1)

        # OBJECT CONTINUITY: Fleet of Mobile Arm Rovers from Scene 3 operating in lanes!
        r1_x, r1_y = center_x - 240, 1280
        draw.rounded_rectangle([(r1_x - 110, r1_y - 120), (r1_x + 110, r1_y + 120)], radius=14, fill=(203, 213, 225), outline=(241, 245, 249), width=2)
        draw.rounded_rectangle([(r1_x - 70, r1_y - 60), (r1_x + 70, r1_y + 60)], fill=(51, 65, 85))
        draw.text((r1_x, r1_y), "UNIT 01 // PAYLOAD", font=font_mono, fill=(241, 245, 249), anchor="mm")
        _draw_titanium_gripper(draw, r1_x, r1_y + 70, scale=0.5)

        r2_x, r2_y = center_x + 220, 1020
        draw.rounded_rectangle([(r2_x - 85, r2_y - 95), (r2_x + 85, r2_y + 95)], radius=12, fill=(148, 163, 184), outline=(203, 213, 225), width=2)
        draw.rounded_rectangle([(r2_x - 55, r2_y - 45), (r2_x + 55, r2_y + 45)], fill=(51, 65, 85))
        draw.text((r2_x, r2_y), "UNIT 02", font=font_mono, fill=(241, 245, 249), anchor="mm")
        _draw_titanium_gripper(draw, r2_x, r2_y + 55, scale=0.4)

        r3_x, r3_y = center_x - 100, 720
        draw.rounded_rectangle([(r3_x - 50, r3_y - 55), (r3_x + 50, r3_y + 55)], radius=8, fill=(100, 116, 139))
        draw.text((r3_x, r3_y), "UNIT 03", font=font_mono, fill=(241, 245, 249), anchor="mm")

        for cy_step in [620, 860, 1120, 1480]:
            draw.polygon([(center_x - 240, cy_step), (center_x - 210, cy_step + 30), (center_x - 270, cy_step + 30)], fill=accent_rgb)
            draw.polygon([(center_x + 220, cy_step - 80), (center_x + 250, cy_step - 50), (center_x + 190, cy_step - 50)], fill=accent_rgb)

        return img

    # -------------------------------------------------------------------------
    # CYBERSECURITY / THREAT / ATTACK / BREACH WORKFLOWS
    # -------------------------------------------------------------------------
    elif any(k in text_lower for k in ["cyber", "breach", "attack", "security", "threat", "vulnerability", "infrastructure"]):
        img = _draw_editorial_background(None, w, h, bg_rgb, surf_rgb, draw_floor=True)
        draw = ImageDraw.Draw(img)

        draw.text((120, 150), "CRITICAL INFRASTRUCTURE DEFENSE", font=font_badge, fill=(239, 68, 68))
        draw.text((120, 195), "ENTERPRISE DMZ CONTAINMENT", font=_get_font(38, bold=True), fill=text_rgb)

        cx, cy = 540, 950
        nodes = [
            (cx - 240, cy - 200, "CORE CLUSTER 01", False),
            (cx + 240, cy - 200, "CORE CLUSTER 02", False),
            (cx, cy - 50, "GATEWAY ROUTER", False),
            (cx - 200, cy + 240, "TENANT ALPHA", True),
            (cx + 200, cy + 240, "TENANT BETA", True),
        ]
        for nx, ny, _, _ in nodes:
            draw.line([(cx, cy - 50), (nx, ny)], fill=(75, 85, 99), width=2)

        draw.line([(cx - 360, cy + 340), (cx - 200, cy + 240)], fill=(239, 68, 68), width=4)
        draw.polygon([(cx - 200, cy + 240), (cx - 230, cy + 260), (cx - 210, cy + 275)], fill=(239, 68, 68))

        for nx, ny, label, is_tenant in nodes:
            nw, nh = 260, 90
            fill_col = (36, 44, 61) if not is_tenant else (26, 32, 44)
            border_col = (239, 68, 68) if "ALPHA" in label else (100, 116, 139)
            draw.rounded_rectangle([(nx - nw // 2, ny - nh // 2), (nx + nw // 2, ny + nh // 2)], radius=10, fill=fill_col, outline=border_col, width=2)
            draw.ellipse([(nx - nw // 2 + 16, ny - 8), (nx - nw // 2 + 32, ny + 8)], fill=border_col)
            draw.text((nx + 10, ny), label, font=font_badge, fill=text_rgb, anchor="mm")

        card_x, card_y = 120, 1340
        card_w, card_h = 840, 100
        draw.rounded_rectangle([(card_x, card_y), (card_x + card_w, card_y + card_h)], radius=12, fill=(26, 32, 44), outline=(239, 68, 68), width=1)
        draw.text((card_x + 32, card_y + 32), "INTRUSION STATUS: CONTAINED IN ISOLATED DMZ", font=font_badge, fill=(239, 68, 68))
        draw.text((card_x + 32, card_y + 64), "CORE ENTERPRISE CLUSTERS 01 & 02: 100% UNCOMPROMISED", font=font_mono, fill=text_rgb)

        return img

    # -------------------------------------------------------------------------
    # DEVELOPER / CODING AGENT / SOFTWARE WORKFLOWS
    # -------------------------------------------------------------------------
    elif any(k in text_lower for k in ["code", "coding", "software", "developer", "agent", "prompt", "workflow", "production environment"]):
        img = _draw_editorial_background(None, w, h, bg_rgb, surf_rgb, draw_floor=True)
        draw = ImageDraw.Draw(img)

        draw.text((120, 150), "01 // AUTONOMOUS AGENT RUNTIME", font=font_badge, fill=accent_rgb)
        draw.text((120, 195), "PRODUCTION PIPELINE EXECUTION", font=_get_font(38, bold=True), fill=text_rgb)

        win_x, win_y = 100, 280
        win_w, win_h = 880, 1040
        draw.rounded_rectangle([(win_x, win_y), (win_x + win_w, win_y + win_h)], radius=16, fill=(22, 27, 36), outline=border_rgb, width=1)

        draw.rectangle([(win_x, win_y), (win_x + win_w, win_y + 54)], fill=(28, 35, 48))
        draw.ellipse([(win_x + 24, win_y + 20), (win_x + 38, win_y + 34)], fill=(239, 68, 68))
        draw.ellipse([(win_x + 48, win_y + 20), (win_x + 62, win_y + 34)], fill=(234, 179, 8))
        draw.ellipse([(win_x + 72, win_y + 20), (win_x + 86, win_y + 34)], fill=(34, 197, 94))
        draw.text((win_x + win_w // 2, win_y + 27), "AUTONOMOUS RUNTIME // PRODUCTION DEPLOYMENT", font=font_badge, fill=muted_rgb, anchor="mm")

        line_y = win_y + 90
        code_snippets = [
            ("import", " frontier_engine as engine", (217, 119, 54)),
            ("from", " runtime.security import verify_sandbox", (217, 119, 54)),
            ("@production_agent", "", (79, 112, 156)),
            ("async def", " execute_coordinated_task():", (217, 119, 54)),
            ("    cluster = ", "await engine.orchestrate_cluster()", text_rgb),
            ("    status = ", "cluster.verify_integrity()", text_rgb),
            ("    # Live Execution Check: PASS", "", (34, 197, 94)),
        ]
        for kw, rest, kw_col in code_snippets:
            draw.text((win_x + 36, line_y), kw, font=font_mono, fill=kw_col)
            draw.text((win_x + 36 + len(kw) * 14, line_y), rest, font=font_mono, fill=text_rgb if kw_col != (34, 197, 94) else (34, 197, 94))
            line_y += 46

        term_y = win_y + 600
        draw.rectangle([(win_x, term_y), (win_x + win_w, win_y + win_h)], fill=(15, 18, 25))
        draw.line([(win_x, term_y), (win_x + win_w, term_y)], fill=border_rgb, width=1)
        draw.text((win_x + 24, term_y + 24), "TERMINAL: autonomous_agent --deploy", font=font_badge, fill=accent_rgb)
        draw.text((win_x + 24, term_y + 60), "[INFO] Connecting to enterprise cluster...", font=font_mono, fill=muted_rgb)
        draw.text((win_x + 24, term_y + 96), "[INFO] Synchronizing production workflows: 100% complete", font=font_mono, fill=(34, 197, 94))
        draw.text((win_x + 24, term_y + 132), "[STATUS] Zero human intervention required.", font=font_mono, fill=text_rgb)

        return img

    # -------------------------------------------------------------------------
    # SCENE 05: EDITORIAL BRAND CONVERGENCE (AI Simplified Lab Studio)
    # Composition: Expansive editorial finish. Monogram embedding the hardware silhouette.
    # -------------------------------------------------------------------------
    else:
        img = _draw_editorial_background(None, w, h, bg_rgb, surf_rgb, draw_floor=True)
        draw = ImageDraw.Draw(img)

        cx, cy = 540, 740

        # Refined Editorial Monogram Emblem (Hexagonal Framing)
        emblem_size = 150
        pts = [
            (cx, cy - emblem_size),
            (cx + emblem_size, cy - emblem_size // 2),
            (cx + emblem_size, cy + emblem_size // 2),
            (cx, cy + emblem_size),
            (cx - emblem_size, cy + emblem_size // 2),
            (cx - emblem_size, cy - emblem_size // 2),
        ]
        draw.polygon(pts, fill=(26, 32, 44), outline=border_rgb, width=2)
        draw.polygon([
            (cx, cy - emblem_size + 24),
            (cx + emblem_size - 24, cy - emblem_size // 2 + 12),
            (cx + emblem_size - 24, cy + emblem_size // 2 - 12),
            (cx, cy + emblem_size - 24),
            (cx - emblem_size + 24, cy + emblem_size // 2 - 12),
            (cx - emblem_size + 24, cy - emblem_size // 2 + 12),
        ], fill=(36, 44, 61), outline=accent_rgb, width=1)

        draw.text((cx, cy), "AI", font=_get_font(90, bold=True), fill=text_rgb, anchor="mm")

        draw.text((cx, cy + 240), "AI SIMPLIFIED LAB", font=font_title, fill=text_rgb, anchor="mm")
        draw.text((cx, cy + 300), "Frontier AI & Autonomous Systems Intelligence", font=font_sub, fill=muted_rgb, anchor="mm")

        card_y = cy + 380
        draw.rounded_rectangle([(cx - 260, card_y), (cx + 260, card_y + 68)], radius=34, fill=(36, 44, 61), outline=border_rgb, width=1)
        draw.text((cx, card_y + 34), "SUBSCRIBE FOR DAILY BRIEFINGS", font=font_badge, fill=accent_rgb, anchor="mm")

        return img
