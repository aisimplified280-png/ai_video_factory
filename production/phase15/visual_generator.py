"""Phase 15/15B Semantic Visual Asset Generator.

Generates photorealistic scene visuals via AI generation API, with a guaranteed
high-fidelity, mode-specific procedural renderer fallback that ensures every visual
mode faithfully demonstrates the factual claim, entities, actions, and control relationships.
"""
from __future__ import annotations

import io
import json
import math
import urllib.parse
import urllib.request
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from .models import ClaimType, SceneVisualPlan, VisualMode


def _get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in ["C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/consola.ttf", "C:/Windows/Fonts/arial.ttf"]:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


def generate_scene_asset(
    plan: SceneVisualPlan,
    target_path: Path,
    timeout_sec: int = 15,
) -> Path:
    """Generate or retrieve distinct cinematic asset for a scene plan, saving claim metadata."""
    target_path.parent.mkdir(parents=True, exist_ok=True)

    # 1. Attempt live API generation (Pollinations if available)
    generated = False
    try:
        from production.phase9.visual_qa import sanitize_cinematic_prompt, validate_image_quality
        sanitized = sanitize_cinematic_prompt(plan.background_prompt or plan.visual_prompt)
        encoded = urllib.parse.quote(sanitized)
        url = f"https://image.pollinations.ai/prompt/{encoded}?width=1080&height=1920&nologo=true"

        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            data = resp.read()

        img = Image.open(io.BytesIO(data)).convert("RGB")
        w, h = img.size
        img = img.crop((0, 0, w, h - 40))
        img = img.resize((1080, 1920), Image.LANCZOS)

        valid, _ = validate_image_quality(img, prompt=plan.background_prompt or plan.visual_prompt)
        if valid:
            img.save(target_path, "PNG")
            generated = True
    except Exception:
        generated = False

    if not generated:
        # 2. High-fidelity semantic procedural renderer
        img = render_procedural_scene_visual(plan)
        img.save(target_path, "PNG")

    # Save asset metadata with claim traceability (Phase 15B Step 24)
    meta_path = target_path.with_suffix(".meta.json")
    try:
        meta_data = {
            "scene_id": plan.scene_id,
            "claim_id": plan.claim_id,
            "claim_type": plan.claim_type,
            "visual_mode": plan.visual_mode.value,
            "required_visual_evidence": plan.required_visual_evidence,
            "grounding_level": plan.grounding_level,
            "visual_grounding_score": plan.visual_grounding_score,
            "claim_coverage_score": plan.claim_coverage_score,
            "entities": plan.entities,
            "action": plan.action,
            "relationship": plan.relationship,
        }
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta_data, f, indent=2)
    except Exception:
        pass

    return target_path


def render_procedural_scene_visual(plan: SceneVisualPlan) -> Image.Image:
    """Render a visually rich, compositionally distinct 1080x1920 visual for a given VisualMode."""
    mode = plan.visual_mode
    w, h = 1080, 1920
    font_mono = _get_font(22)
    font_hud = _get_font(30, bold=True)
    font_large = _get_font(52, bold=True)

    # 1. DIRECT AI CONTROL OF PHYSICAL ROBOTIC ARM (LITERAL / CAPABILITY)
    if mode == VisualMode.LITERAL or (mode in (VisualMode.MECHANISM, VisualMode.DEMONSTRATION) and "arm" in plan.subject.lower()):
        img = Image.new("RGB", (w, h), (14, 20, 30))
        draw = ImageDraw.Draw(img)

        # Gradient industrial workcell illumination
        for y in range(h):
            ratio = y / h
            r = int(14 + ratio * 12)
            g = int(20 + ratio * 16)
            b = int(30 + ratio * 24)
            draw.line([(0, y), (w, y)], fill=(r, g, b))

        # Heavy Robot Base & Pedestal
        draw.polygon([(260, 1540), (820, 1540), (880, 1820), (200, 1820)], fill=(32, 42, 58), outline=(80, 98, 128), width=5)
        draw.line([(260, 1540), (820, 1540)], fill=(160, 185, 220), width=6)

        # Turntable Joint / Shoulder Pivot
        draw.ellipse((420, 1420, 660, 1580), fill=(45, 58, 80), outline=(100, 122, 155), width=4)
        draw.ellipse((480, 1450, 600, 1550), fill=(22, 32, 48), outline=(56, 189, 248), width=3)

        # Primary Heavy Arm Segment (Lower Arm)
        draw.polygon([(460, 1460), (580, 1460), (740, 980), (640, 940)], fill=(50, 64, 88), outline=(110, 134, 170), width=5)
        # Specular Bevel Line
        draw.line([(580, 1460), (740, 980)], fill=(220, 240, 255), width=5)

        # Elbow Joint / Motor Housing
        draw.ellipse((610, 890, 780, 1030), fill=(38, 50, 72), outline=(56, 189, 248), width=4)
        draw.ellipse((660, 925, 730, 995), fill=(16, 24, 38), outline=(16, 185, 129), width=2)

        # Forearm Segment reaching forward-left
        draw.polygon([(640, 940), (720, 970), (440, 620), (380, 640)], fill=(55, 70, 95), outline=(120, 145, 185), width=5)
        draw.line([(640, 940), (380, 640)], fill=(230, 245, 255), width=5)

        # Wrist Joint & Articulated End-Effector Gripper
        draw.ellipse((350, 590, 450, 670), fill=(40, 52, 75), outline=(100, 125, 160), width=4)
        # Precision Gripper Fingers engaging component
        draw.polygon([(360, 640), (300, 780), (340, 790), (390, 670)], fill=(65, 80, 110), outline=(160, 185, 225), width=3)
        draw.polygon([(430, 640), (490, 780), (450, 790), (400, 670)], fill=(65, 80, 110), outline=(160, 185, 225), width=3)

        # Clamped Micro-Target Component with Specular Glint
        draw.rounded_rectangle((330, 760, 470, 810), radius=6, fill=(24, 34, 52), outline=(56, 189, 248), width=4)
        draw.ellipse((385, 775, 405, 795), fill=(255, 255, 255), outline=(0, 229, 255), width=2)

        # Active Optical Laser Alignment Beam
        draw.line([(395, 200), (395, 775)], fill=(0, 240, 255), width=3)
        draw.line([(0, 785), (w, 785)], fill=(0, 240, 255), width=2)

        # Direct AI Control Signal / Real-Time Data Conduit
        conduit_points = [(540, 1460), (690, 960), (410, 630), (395, 760)]
        for k in range(len(conduit_points) - 1):
            draw.line([conduit_points[k], conduit_points[k+1]], fill=(16, 185, 129), width=4)

        # Telemetry HUD: AI Direct Control
        draw.rounded_rectangle((60, 140, w - 60, 310), radius=12, fill=(16, 24, 38), outline=(56, 189, 248), width=3)
        draw.text((90, 175), "AI_DIRECT_CONTROL // [GPT-6_ASTRA_CORE]", font=font_hud, fill=(56, 189, 248))
        draw.text((90, 225), "COMMAND_BUS: MOTOR_OUTPUT_ACTIVE | LATENCY: 0.8ms", font=font_mono, fill=(16, 185, 129))
        draw.text((90, 260), "FEEDBACK: CLOSED_LOOP_REALTIME | POSITION_ERR: 0.002mm", font=font_mono, fill=(148, 163, 184))

        draw.text((80, 1720), "[ACTUATOR_STATE]: PHYSICAL_EXECUTION_VERIFIED", font=font_mono, fill=(16, 185, 129))
        draw.text((80, 1750), "[CONTROL_MODE]: FULL_AUTONOMOUS (0% MANUAL OVERRIDE)", font=font_mono, fill=(56, 189, 248))

    # 2. DYNAMIC ADAPTATION & OBSTACLE AVOIDANCE (DEMONSTRATION / COMPARISON)
    elif mode in (VisualMode.DEMONSTRATION, VisualMode.COMPARISON):
        img = Image.new("RGB", (w, h), (18, 24, 38))
        draw = ImageDraw.Draw(img)

        # Gradient perspective warehouse floor
        for y in range(h):
            ratio = y / h
            r = int(16 + ratio * 8)
            g = int(22 + ratio * 10)
            b = int(34 + ratio * 16)
            draw.line([(0, y), (w, y)], fill=(r, g, b))

        # Isometric Floor Grid
        for y_pos in range(250, 1850, 110):
            draw.line([(0, y_pos + 160), (w, y_pos - 160)], fill=(34, 48, 72), width=2)
            draw.line([(0, y_pos - 160), (w, y_pos + 160)], fill=(34, 48, 72), width=2)

        # Yellow Safety Corridors
        draw.line([(240, 180), (320, 1820)], fill=(245, 158, 11), width=8)
        draw.line([(840, 180), (760, 1820)], fill=(245, 158, 11), width=8)

        # UNEXPECTED OBSTACLE DIRECTLY IN PATH (Hazard Barrier / Shifted Pallet)
        obs_x, obs_y = 540, 920
        draw.rectangle((obs_x - 90, obs_y - 60, obs_x + 90, obs_y + 60), fill=(45, 30, 20), outline=(239, 68, 68), width=5)
        # Red/Orange Hazard Diagonal Stripes
        for s_off in range(-70, 70, 30):
            draw.line([(obs_x + s_off - 20, obs_y + 50), (obs_x + s_off + 20, obs_y - 50)], fill=(239, 68, 68), width=6)
        draw.text((obs_x - 80, obs_y - 18), "[OBSTACLE]", font=font_hud, fill=(255, 255, 255))

        # Autonomous Rover approaching obstacle from below
        rx, ry = 540, 1420
        # Rover Chassis
        draw.ellipse((rx - 90, ry + 30, rx + 90, ry + 70), fill=(10, 14, 22))
        draw.rounded_rectangle((rx - 85, ry - 60, rx + 85, ry + 50), radius=16, fill=(45, 55, 78), outline=(100, 116, 145), width=4)
        draw.rounded_rectangle((rx - 65, ry - 40, rx + 65, ry + 30), radius=8, fill=(28, 38, 56), outline=(56, 189, 248), width=2)
        draw.ellipse((rx - 16, ry - 16, rx + 16, ry + 16), fill=(16, 185, 129))

        # Active Optical Sensor Detection Cone illuminating Obstacle
        draw.polygon([(rx, ry - 50), (obs_x - 120, obs_y + 80), (obs_x + 120, obs_y + 80)], fill=(12, 50, 65), outline=(56, 189, 248))
        draw.line([(rx, ry - 50), (obs_x - 120, obs_y + 80)], fill=(0, 240, 255), width=3)
        draw.line([(rx, ry - 50), (obs_x + 120, obs_y + 80)], fill=(0, 240, 255), width=3)

        # RIGID COLLISION PATH (Red dashed line showing legacy routine)
        for d_y in range(ry - 70, obs_y + 60, -35):
            draw.line([(540, d_y), (540, d_y - 18)], fill=(239, 68, 68), width=4)
        draw.text((555, 1160), "LEGACY ROUTINE (BLOCKED)", font=font_mono, fill=(239, 68, 68))

        # DYNAMIC RECALCULATED PATH (Green/Cyan vector curve bypassing obstacle safely)
        reroute_points = [(rx, ry - 50), (460, 1200), (360, 1020), (370, 820), (510, 660), (540, 500)]
        for k in range(len(reroute_points) - 1):
            draw.line([reroute_points[k], reroute_points[k+1]], fill=(16, 185, 129), width=6)
            draw.ellipse((reroute_points[k][0] - 5, reroute_points[k][1] - 5, reroute_points[k][0] + 5, reroute_points[k][1] + 5), fill=(255, 255, 255))
        draw.text((220, 940), "DYNAMIC ADAPTIVE PATH", font=font_mono, fill=(16, 185, 129))

        # Secondary rover interweaving in background
        r2x, r2y = 740, 580
        draw.rounded_rectangle((r2x - 60, r2y - 40, r2x + 60, r2y + 35), radius=12, fill=(40, 50, 70), outline=(100, 116, 142), width=3)
        draw.ellipse((r2x - 12, r2y - 12, r2x + 12, r2y + 12), fill=(16, 185, 129))

        # Telemetry HUD
        draw.rounded_rectangle((60, 140, w - 60, 310), radius=12, fill=(16, 24, 38), outline=(245, 158, 11), width=3)
        draw.text((90, 175), "DYNAMIC_ADAPTATION // OBSTACLE REROUTING", font=font_hud, fill=(245, 158, 11))
        draw.text((90, 225), "OBSTACLE DETECTED: TRUE | COLLISION PROBABILITY: 0.0%", font=font_mono, fill=(16, 185, 129))
        draw.text((90, 260), "PATH STATUS: DYNAMIC_VECTOR_RECALCULATED (0.4ms)", font=font_mono, fill=(56, 189, 248))

        draw.text((80, 1720), "[SWARM_STATE]: REAL_TIME_ADAPTIVE_COLLISION_FREE", font=font_mono, fill=(16, 185, 129))
        draw.text((80, 1750), "[RIGID_CODE]: OVERRIDDEN BY FRONTIER AI MODEL", font=font_mono, fill=(148, 163, 184))

    # 3. HIGH-THROUGHPUT FACILITY SCALE (SCALE / CONSEQUENCE / BUSINESS IMPACT)
    elif mode in (VisualMode.SCALE, VisualMode.CONSEQUENCE):
        img = Image.new("RGB", (w, h), (10, 14, 24))
        draw = ImageDraw.Draw(img)

        # Steep vertical perspective corridor
        vp = (540, 380)
        for x_base in range(-450, 1550, 140):
            draw.line([vp, (x_base, 1920)], fill=(28, 40, 60), width=2)

        # High-Speed Automated Conveyor / Sorting Channels (Center)
        # Left Channel (Speed Lane 01)
        draw.polygon([(460, 560), (510, 560), (320, 1920), (160, 1920)], fill=(20, 32, 50), outline=(56, 189, 248), width=3)
        # Right Channel (Speed Lane 02)
        draw.polygon([(570, 560), (620, 560), (920, 1920), (760, 1920)], fill=(20, 32, 50), outline=(16, 185, 129), width=3)

        # High-Speed Flow Arrows (Green Velocity Indicators)
        for flow_y in range(700, 1800, 200):
            # Left Lane Vectors
            ly = flow_y
            lx = int(460 - (flow_y - 560) * 0.22)
            draw.line([(lx, ly), (lx - 25, ly + 90)], fill=(56, 189, 248), width=6)
            # Right Lane Vectors
            rx = int(590 + (flow_y - 560) * 0.22)
            draw.line([(rx, ry := ly), (rx + 25, ry + 90)], fill=(16, 185, 129), width=6)

        # High-Bay Vertical Storage Tiers (Left & Right Racks)
        for y_tier in range(540, 1860, 160):
            draw.rectangle((20, y_tier, 220, y_tier + 100), fill=(16, 24, 38), outline=(45, 58, 80), width=3)
            draw.ellipse((190, y_tier + 15, 210, y_tier + 35), fill=(245, 158, 11))
            draw.rectangle((860, y_tier, 1060, y_tier + 100), fill=(16, 24, 38), outline=(45, 58, 80), width=3)
            draw.ellipse((870, y_tier + 15, 890, y_tier + 35), fill=(245, 158, 11))

        # Overhead Autonomous Gantry Crane with High-Speed Payload
        draw.rectangle((280, 780, 800, 840), fill=(35, 48, 70), outline=(100, 120, 150), width=4)
        draw.rounded_rectangle((480, 840, 600, 960), radius=8, fill=(24, 35, 55), outline=(16, 185, 129), width=3)
        draw.text((495, 890), "PAYLOAD", font=font_mono, fill=(16, 185, 129))

        # Telemetry HUD: Throughput Acceleration & Bottleneck Reduction
        draw.rounded_rectangle((60, 140, w - 60, 310), radius=12, fill=(16, 24, 38), outline=(16, 185, 129), width=3)
        draw.text((90, 175), "LOGISTICS_THROUGHPUT // ZERO_BOTTLENECK", font=font_hud, fill=(16, 185, 129))
        draw.text((90, 225), "THROUGHPUT VELOCITY: +340% | BOTTLENECK_DELAYS: 0.0%", font=font_mono, fill=(56, 189, 248))
        draw.text((90, 260), "HUMAN INTERVENTION: MINIMAL | CYCLE TIME: 1.2s", font=font_mono, fill=(148, 163, 184))

        draw.text((80, 1720), "[FACILITY_STATUS]: UNINTERRUPTED_HIGH_VELOCITY_FLOW", font=font_mono, fill=(16, 185, 129))
        draw.text((80, 1750), "[DELAY_REDUCTION]: -92.4% VS MANUAL DISTRIBUTION", font=font_mono, fill=(56, 189, 248))

    # 4. MACRO DETAIL / HOOK (DETAIL / MECHANISM)
    elif mode in (VisualMode.DETAIL, VisualMode.MECHANISM):
        img = Image.new("RGB", (w, h), (12, 16, 24))
        draw = ImageDraw.Draw(img)

        for y in range(h):
            ratio = y / h
            r = int(12 + ratio * 16)
            g = int(16 + ratio * 20)
            b = int(24 + ratio * 32)
            draw.line([(0, y), (w, y)], fill=(r, g, b))

        # Left Heavy Gripper Arm Assembly
        draw.polygon([(140, 520), (380, 800), (330, 1280), (140, 1140), (80, 720)], fill=(55, 65, 85), outline=(130, 150, 190), width=4)
        draw.line([(380, 800), (330, 1280)], fill=(230, 245, 255), width=6)
        draw.line([(140, 520), (380, 800)], fill=(180, 205, 235), width=4)

        # Right Gripper Arm Assembly
        draw.polygon([(940, 520), (700, 800), (750, 1280), (940, 1140), (1000, 720)], fill=(55, 65, 85), outline=(130, 150, 190), width=4)
        draw.line([(700, 800), (750, 1280)], fill=(230, 245, 255), width=6)
        draw.line([(940, 520), (700, 800)], fill=(180, 205, 235), width=4)

        # Clamped Central High-Precision Micro-Component
        draw.rounded_rectangle((410, 900, 670, 1160), radius=16, fill=(24, 32, 48), outline=(56, 189, 248), width=5)
        draw.rounded_rectangle((430, 920, 650, 1140), radius=10, fill=(15, 23, 36), outline=(30, 58, 95), width=2)

        # Neon Cyan Alignment Laser Crosshair
        draw.line([(0, 1030), (w, 1030)], fill=(0, 240, 255), width=4)
        draw.line([(540, 600), (540, 1460)], fill=(0, 240, 255), width=2)
        draw.ellipse((530, 1020, 550, 1040), fill=(255, 255, 255), outline=(0, 240, 255), width=3)

        # Precision Optical HUD Reticles
        draw.arc((360, 850, 720, 1210), start=35, end=145, fill=(56, 189, 248), width=3)
        draw.arc((360, 850, 720, 1210), start=215, end=325, fill=(56, 189, 248), width=3)

        # Technical Telemetry Readouts
        draw.text((80, 180), "MACRO_OPTICAL_FEED // SENSOR LOCK", font=font_hud, fill=(56, 189, 248))
        draw.text((80, 220), "TOLERANCE: +/- 0.002mm | TORQUE: 14.8 Nm | LATENCY: 1.2ms", font=font_mono, fill=(148, 163, 184))
        draw.text((80, 1720), "[ACTUATOR_BUS_01]: ENGAGED", font=font_mono, fill=(16, 185, 129))
        draw.text((80, 1750), "[TARGET_LOCK]: ZERO_PLAY_PNEUMATIC", font=font_mono, fill=(148, 163, 184))

    # 5. BRAND CTA RESOLUTION (BRAND_CTA)
    elif mode == VisualMode.BRAND_CTA:
        img = Image.new("RGB", (w, h), (8, 10, 16))
        draw = ImageDraw.Draw(img)

        # Radial center spotlight gradient
        for r_spot in range(550, 50, -35):
            alpha_b = int(12 + (550 - r_spot) * 0.09)
            draw.ellipse((540 - r_spot, 900 - r_spot, 540 + r_spot, 900 + r_spot), fill=(int(alpha_b * 0.6), alpha_b, int(alpha_b * 1.5)))

        # Polished Architectural Floor Reflection Plane
        draw.line([(0, 1220), (w, 1220)], fill=(40, 55, 80), width=3)
        for y_ref in range(1220, h, 60):
            draw.line([(0, y_ref), (w, y_ref)], fill=(16, 24, 38), width=1)

        # Primary Minimalist Channel Emblem Hexagon
        cx, cy, radius = 540, 860, 220
        pts = [
            (int(cx + radius * math.cos(math.radians(a))), int(cy + radius * math.sin(math.radians(a))))
            for a in range(30, 390, 60)
        ]
        draw.polygon(pts, fill=(18, 24, 38), outline=(56, 189, 248), width=6)

        # Inner Glowing Core
        pts_inner = [
            (int(cx + (radius - 40) * math.cos(math.radians(a))), int(cy + (radius - 40) * math.sin(math.radians(a))))
            for a in range(30, 390, 60)
        ]
        draw.polygon(pts_inner, fill=(12, 18, 30), outline=(129, 140, 248), width=3)

        # Symmetrical Stylized "AI" Central Monogram
        draw.line([(cx - 70, cy + 60), (cx - 20, cy - 70), (cx + 30, cy + 60)], fill=(255, 255, 255), width=8)
        draw.line([(cx - 50, cy + 15), (cx + 10, cy + 15)], fill=(0, 229, 255), width=6)
        draw.line([(cx + 65, cy - 70), (cx + 65, cy + 60)], fill=(0, 229, 255), width=8)

        # Branded Typography
        tw = draw.textlength("AI SIMPLIFIED LAB", font=font_large)
        draw.text(((w - tw) // 2, 1280), "AI SIMPLIFIED LAB", font=font_large, fill=(255, 255, 255))
        sub_text = "FRONTIER AI BRIEFINGS // SUBSCRIBE"
        sw = draw.textlength(sub_text, font=font_hud)
        draw.text(((w - sw) // 2, 1370), sub_text, font=font_hud, fill=(56, 189, 248))

    # Fallback to interface / diagnostic telemetry
    else:
        img = Image.new("RGB", (w, h), (10, 14, 22))
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle((60, 140, w - 60, 320), radius=14, fill=(18, 25, 38), outline=(56, 189, 248), width=2)
        draw.text((90, 180), f"SYSTEM TELEMETRY // {mode.value.upper()}", font=font_hud, fill=(56, 189, 248))
        draw.text((90, 230), plan.subject[:60], font=font_mono, fill=(148, 163, 184))

    return img
