"""Phase 17 Environment Background Generator.

Enforces:
1. Topic-Aligned Semantic Environments: Software topics receive distributed/cloud/vector topologies,
   robotics receives CAD/tactical workcells, biotech receives molecular/scans, etc.
   Never deterministically reuse templates solely based on scene_index.
2. Requirement 1: No single background survives longer than 8 seconds.
3. Every environment decision records structured rationale for QA auditing.
"""
from __future__ import annotations

import math
from enum import Enum
from pathlib import Path
from dataclasses import dataclass
from typing import Any
from PIL import Image, ImageDraw, ImageFilter

from .style_systems import StyleSystem, get_style_system


def _hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    s = hex_str.lstrip("#")
    return int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)


class TopicDomain(str, Enum):
    SOFTWARE_AI = "software_ai"
    ROBOTICS_HARDWARE = "robotics_hardware"
    BIOTECH_SCIENCE = "biotech_science"
    FINANCE_MARKETS = "finance_markets"
    GENERAL_TECH = "general_tech"


@dataclass
class EnvironmentDecision:
    topic: str
    domain: str
    archetype: str
    rationale: str
    structural_features: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "topic": self.topic,
            "domain": self.domain,
            "archetype": self.archetype,
            "rationale": self.rationale,
            "structural_features": self.structural_features,
        }


import re


def classify_topic_domain(topic: str = "", subject: str = "", visual_purpose: str = "", narration: str = "") -> TopicDomain:
    """Classifies topic into semantic domain using strict word-boundary checks."""
    text = f"{topic} {subject} {visual_purpose} {narration}".lower()

    # 1. Physical Robotics / Hardware (must be explicit physical hardware)
    is_explicit_hardware = bool(
        re.search(
            r"\b(robot arm|robotic arm|industrial robot|industrial robots|warehouse robots|warehouse robotics|manipulator|gripper|actuator|actuators|kinematics|tactile clamp|agv|six-axis)\b",
            text,
        )
    )
    is_software_context = bool(
        re.search(
            r"\b(rag|bedrock|llm|llms|software|data warehouse|cloud|api|apis|database|vector|vectors|pipeline)\b",
            text,
        )
    )
    if is_explicit_hardware and not is_software_context:
        return TopicDomain.ROBOTICS_HARDWARE

    # 2. Software / AI / Cloud (RAG, Bedrock, Transformers, Agentic AI, Cloud infrastructure)
    if bool(
        re.search(
            r"\b(rag|bedrock|llm|llms|agent|agents|retrieval|vector|vectors|embedding|embeddings|token|tokens|transformer|transformers|cloud|api|apis|software|database|data pipeline|neural|deep learning|gpt|claude|model|models|python|prompt|prompts|enterprise)\b",
            text,
        )
    ):
        return TopicDomain.SOFTWARE_AI

    # 3. Biotech / Health / Life Sciences
    if bool(
        re.search(
            r"\b(dna|crispr|gene|genes|genomic|genomics|protein|proteins|molecular|biology|medical|vaccine|vaccines)\b",
            text,
        )
    ):
        return TopicDomain.BIOTECH_SCIENCE

    # 4. Finance / Markets / Crypto
    if bool(
        re.search(
            r"\b(finance|financial|market|markets|trading|stock|stocks|liquidity|crypto|blockchain|order book|arbitrage)\b",
            text,
        )
    ):
        return TopicDomain.FINANCE_MARKETS

    return TopicDomain.GENERAL_TECH


# ---------------------------------------------------------------------------
# DOMAIN A: SOFTWARE / AI / CLOUD ENVIRONMENTS
# ---------------------------------------------------------------------------

def generate_vector_latent_space_bg(width: int = 1080, height: int = 1920, style: StyleSystem | None = None) -> Image.Image:
    """Software/AI Scene 1: Multi-dimensional vector latent space with coordinate projection points."""
    st = style or get_style_system()
    bg_rgb = _hex_to_rgb(st.primary_bg)
    is_light = bg_rgb[0] > 180 and bg_rgb[1] > 180 and bg_rgb[2] > 180

    img = Image.new("RGB", (width, height), bg_rgb)
    draw = ImageDraw.Draw(img)

    # Dimensional coordinate grid ticks
    grid_col = (210, 225, 245) if is_light else (28, 38, 55)
    point_col = (30, 64, 175) if is_light else (59, 130, 246)
    dim_col = (100, 116, 139) if is_light else (71, 85, 105)

    # Ambient coordinate plane bands
    for py in [380, 720, 1080]:
        draw.rectangle([(80, py - 30), (width - 80, py + 30)], fill=(241, 245, 249) if is_light else (18, 24, 38))
        draw.line([(80, py), (width - 80, py)], fill=grid_col, width=2)

    for x in range(120, width - 80, 160):
        for y in range(240, height - 200, 180):
            draw.line([(x - 8, y), (x + 8, y)], fill=dim_col, width=2)
            draw.line([(x, y - 8), (x, y + 8)], fill=dim_col, width=2)

    # Floating vector cluster constellations with visible node hubs
    cluster_centers = [(340, 520), (740, 840), (420, 1220)]
    for cx, cy in cluster_centers:
        draw.ellipse([(cx - 24, cy - 24), (cx + 24, cy + 24)], fill=(219, 234, 254) if is_light else (30, 58, 138), outline=point_col, width=2)
        for ox, oy in [(-80, -40), (60, -70), (-40, 60), (90, 40), (0, 0)]:
            px, py = cx + ox, cy + oy
            draw.ellipse([(px - 6, py - 6), (px + 6, py + 6)], fill=point_col)
            draw.line([(cx, cy), (px, py)], fill=grid_col, width=2)

    draw.text((120, 160), "LATENT_DIMENSION // 1536-D HYPERPLANE", fill=dim_col)
    return img


def generate_cloud_topology_mesh_bg(width: int = 1080, height: int = 1920, style: StyleSystem | None = None) -> Image.Image:
    """Software/AI Scene 2: Cloud schematic network tree with bus lines, gateway hubs, and routing nodes."""
    st = style or get_style_system()
    bg_rgb = _hex_to_rgb(st.primary_bg)
    is_light = bg_rgb[0] > 180 and bg_rgb[1] > 180 and bg_rgb[2] > 180

    img = Image.new("RGB", (width, height), bg_rgb)
    draw = ImageDraw.Draw(img)

    # Ambient cloud architecture gradient core
    for y in range(220, 1420):
        pct = math.sin((y - 220) / (1420 - 220) * math.pi)
        if is_light:
            r = int(248 - pct * 16)
            g = int(250 - pct * 10)
            b = int(252 + pct * 2)
        else:
            r = int(12 + pct * 10)
            g = int(16 + pct * 20)
            b = int(24 + pct * 36)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    bus_col = (147, 197, 253) if is_light else (30, 58, 138)
    hub_fill = (239, 246, 255) if is_light else (15, 23, 42)
    accent_col = (30, 64, 175) if is_light else (96, 165, 250)
    tag_col = (71, 85, 105) if is_light else (148, 163, 184)

    cx = width // 2
    # Vertical trunk data bus with distinct high-contrast width
    draw.line([(cx, 240), (cx, 1400)], fill=accent_col, width=4)

    # Cloud Gateway Hubs (structural presence)
    for branch_y in [440, 740, 1040, 1280]:
        draw.line([(140, branch_y), (width - 140, branch_y)], fill=bus_col, width=3)
        # Hub card
        draw.rounded_rectangle([(cx - 70, branch_y - 24), (cx + 70, branch_y + 24)], radius=10, fill=hub_fill, outline=accent_col, width=2)
        draw.ellipse([(cx - 8, branch_y - 8), (cx + 8, branch_y + 8)], fill=accent_col)
        # Lateral endpoints
        draw.rounded_rectangle([(120, branch_y - 18), (240, branch_y + 18)], radius=8, fill=hub_fill, outline=bus_col, width=1)
        draw.rounded_rectangle([(width - 240, branch_y - 18), (width - 120, branch_y + 18)], radius=8, fill=hub_fill, outline=bus_col, width=1)
        draw.text((130, branch_y - 8), "VPC_GATEWAY", fill=tag_col)

    draw.text((120, 160), "TOPOLOGY_MAP // SERVERLESS CLOUD FABRIC", fill=tag_col)
    return img


def generate_neural_attention_lattice_bg(width: int = 1080, height: int = 1920, style: StyleSystem | None = None) -> Image.Image:
    """Software/AI Scene 3: Multi-head attention weight pathways and high-contrast matrix lines."""
    st = style or get_style_system()
    bg_rgb = _hex_to_rgb(st.primary_bg)
    is_light = bg_rgb[0] > 180 and bg_rgb[1] > 180 and bg_rgb[2] > 180

    img = Image.new("RGB", (width, height), bg_rgb)
    draw = ImageDraw.Draw(img)

    mesh_col = (226, 232, 240) if is_light else (24, 32, 47)
    gold_accent = (217, 119, 6) if is_light else (245, 158, 11)
    tag_col = (100, 116, 139) if is_light else (71, 85, 105)

    # Diagonal cross-attention ray weave
    for i in range(0, width + 400, 120):
        draw.line([(i, 200), (i - 300, 1400)], fill=mesh_col, width=1)
        draw.line([(i - 300, 200), (i, 1400)], fill=mesh_col, width=1)

    draw.line([(width // 2, 280), (width // 2, 1320)], fill=gold_accent, width=2)
    draw.text((120, 160), "CROSS_ATTENTION // Q-K-V MATRIX WEAVE", fill=tag_col)
    return img


def generate_distributed_cluster_bg(width: int = 1080, height: int = 1920, style: StyleSystem | None = None) -> Image.Image:
    """Software/AI Scene 4: Enterprise cluster rack architecture perspective."""
    st = style or get_style_system()
    bg_rgb = _hex_to_rgb(st.primary_bg)
    is_light = bg_rgb[0] > 180 and bg_rgb[1] > 180 and bg_rgb[2] > 180

    img = Image.new("RGB", (width, height), bg_rgb)
    draw = ImageDraw.Draw(img)

    rack_col = (203, 213, 225) if is_light else (30, 41, 59)
    telemetry_col = (13, 148, 136) if is_light else (45, 212, 191)

    # Perspective vertical rack guides
    cx = width // 2
    for offset in [-420, -220, 220, 420]:
        x = cx + offset
        draw.line([(x, 320), (x, 1400)], fill=rack_col, width=2)
        for ry in range(400, 1350, 140):
            draw.rectangle([(x - 30, ry), (x + 30, ry + 12)], outline=rack_col, fill=None)

    draw.text((120, 160), "CLUSTER_TOPOLOGY // ZERO-DOWNTIME DISTRIBUTED SYSTEM", fill=telemetry_col)
    return img


def generate_glass_command_stage_bg(width: int = 1080, height: int = 1920, style: StyleSystem | None = None) -> Image.Image:
    """Software/AI Scene 5: Modern architectural glass podium stage."""
    st = style or get_style_system()
    bg_rgb = _hex_to_rgb(st.primary_bg)
    is_light = bg_rgb[0] > 180 and bg_rgb[1] > 180 and bg_rgb[2] > 180

    img = Image.new("RGB", (width, height), bg_rgb)
    draw = ImageDraw.Draw(img)

    cx, cy = width // 2, 700
    glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for radius in range(750, 40, -50):
        alpha = int(22 * (1.0 - radius / 750))
        glow_col = (239, 246, 255, alpha) if is_light else (30, 64, 175, alpha)
        gd.ellipse([(cx - radius, cy - radius // 2), (cx + radius, cy + radius // 2)], fill=glow_col)

    img.paste(Image.alpha_composite(Image.new("RGBA", (width, height), (*bg_rgb, 255)), glow).convert("RGB"))
    draw = ImageDraw.Draw(img)

    horizon_y = 1200
    draw.line([(140, horizon_y), (width - 140, horizon_y)], fill=(203, 213, 225) if is_light else (51, 65, 85), width=2)
    return img


# ---------------------------------------------------------------------------
# DOMAIN B: PHYSICAL ROBOTICS & HARDWARE WORKCELL ENVIRONMENTS
# ---------------------------------------------------------------------------

def generate_macro_studio_bg(width: int = 1080, height: int = 1920, style: StyleSystem | None = None) -> Image.Image:
    """Robotics Scene 1: Macro studio with shallow depth of field and radial keylight."""
    st = style or get_style_system()
    bg_rgb = _hex_to_rgb(st.primary_bg)
    is_light = bg_rgb[0] > 180 and bg_rgb[1] > 180 and bg_rgb[2] > 180

    img = Image.new("RGB", (width, height), bg_rgb)
    draw = ImageDraw.Draw(img)

    glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for radius in range(950, 80, -70):
        alpha = int(28 * (1.0 - radius / 950))
        cx, cy = 340, 420
        col = (239, 246, 255, alpha) if is_light else (45, 55, 75, alpha)
        gd.ellipse([(cx - radius, cy - radius), (cx + radius, cy + radius)], fill=col)

    bokeh_spots = [(240, 300, 160), (840, 520, 220), (720, 1380, 180), (180, 1500, 140)]
    for bx, by, br in bokeh_spots:
        for r in range(br, 20, -30):
            alpha = int(14 * (1.0 - r / br))
            gd.ellipse([(bx - r, by - r), (bx + r, by + r)], fill=(217, 119, 54, alpha))

    img.paste(Image.alpha_composite(Image.new("RGBA", (width, height), (*bg_rgb, 255)), glow).convert("RGB"))
    draw = ImageDraw.Draw(img)
    draw.line([(0, 1280), (width, 1280)], fill=(226, 232, 240) if is_light else (36, 44, 58), width=1)
    return img


def generate_blueprint_cad_bg(width: int = 1080, height: int = 1920, style: StyleSystem | None = None) -> Image.Image:
    """Robotics Scene 2: Technical CAD drafting environment with orthographic grid and registration ticks."""
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
    """Robotics Scene 3: High-contrast tactical architecture map with perspective grid and circular rings."""
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
    """Robotics Scene 4: Deep perspective logistics warehouse racking aisle."""
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
    """Robotics Scene 5: Architectural stage with spotlight and embossed pedestal."""
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


# ---------------------------------------------------------------------------
# DOMAIN C: BIOTECH & HEALTHCARE ENVIRONMENTS
# ---------------------------------------------------------------------------

def generate_molecular_lattice_bg(width: int = 1080, height: int = 1920, style: StyleSystem | None = None) -> Image.Image:
    """Biotech Scene: Hexagonal molecular lattice with chemical bonding nodes."""
    st = style or get_style_system()
    bg_rgb = _hex_to_rgb(st.primary_bg)
    is_light = bg_rgb[0] > 180 and bg_rgb[1] > 180 and bg_rgb[2] > 180

    img = Image.new("RGB", (width, height), bg_rgb)
    draw = ImageDraw.Draw(img)

    bond_col = (203, 213, 225) if is_light else (30, 41, 59)
    node_col = (13, 148, 136) if is_light else (20, 184, 166)

    # Hexagonal bond pattern
    hex_r = 70
    for row in range(3, 11):
        for col in range(1, 7):
            cx = int(col * hex_r * 2.6 + ((row % 2) * hex_r * 1.3))
            cy = int(row * hex_r * 1.6)
            for a in range(0, 360, 60):
                rad = math.radians(a)
                x = int(cx + hex_r * math.cos(rad))
                y = int(cy + hex_r * math.sin(rad))
                draw.line([(cx, cy), (x, y)], fill=bond_col, width=1)
                draw.ellipse([(x - 4, y - 4), (x + 4, y + 4)], fill=node_col)

    draw.text((120, 160), "MOLECULAR_STRUCTURE // GENOMIC MESH", fill=node_col)
    return img


# ---------------------------------------------------------------------------
# DOMAIN D: FINANCE & MARKETS ENVIRONMENTS
# ---------------------------------------------------------------------------

def generate_candlestick_matrix_bg(width: int = 1080, height: int = 1920, style: StyleSystem | None = None) -> Image.Image:
    """Finance Scene: Technical financial chart coordinate grid and volatility corridors."""
    st = style or get_style_system()
    bg_rgb = _hex_to_rgb(st.primary_bg)
    is_light = bg_rgb[0] > 180 and bg_rgb[1] > 180 and bg_rgb[2] > 180

    img = Image.new("RGB", (width, height), bg_rgb)
    draw = ImageDraw.Draw(img)

    grid_col = (226, 232, 240) if is_light else (22, 28, 40)
    amber_col = (217, 119, 6) if is_light else (245, 158, 11)

    # Horizontal price levels
    for y in range(300, 1400, 100):
        draw.line([(80, y), (width - 80, y)], fill=grid_col, width=1)
        draw.text((90, y - 18), f"{(1500 - y) * 2.4:.2f}", fill=(148, 163, 184))

    # Vertical time intervals
    for x in range(160, width - 80, 140):
        draw.line([(x, 300), (x, 1400)], fill=grid_col, width=1)

    draw.text((120, 160), "FINANCIAL_MARKET // ORDER_BOOK_DEPTH", fill=amber_col)
    return img


# ---------------------------------------------------------------------------
# DOMAIN E: GENERAL TECH ENVIRONMENTS
# ---------------------------------------------------------------------------

def generate_isometric_grid_bg(width: int = 1080, height: int = 1920, style: StyleSystem | None = None) -> Image.Image:
    """General Tech: Modern isometric dot and diamond grid."""
    st = style or get_style_system()
    bg_rgb = _hex_to_rgb(st.primary_bg)
    is_light = bg_rgb[0] > 180 and bg_rgb[1] > 180 and bg_rgb[2] > 180

    img = Image.new("RGB", (width, height), bg_rgb)
    draw = ImageDraw.Draw(img)

    dot_col = (203, 213, 225) if is_light else (36, 46, 66)
    for x in range(80, width, 80):
        for y in range(200, height - 160, 80):
            draw.ellipse([(x - 2, y - 2), (x + 2, y + 2)], fill=dot_col)

    draw.text((120, 160), "TECHNICAL_INDEX // SPECIFICATION_STAGE", fill=dot_col)
    return img


# ---------------------------------------------------------------------------
# DOMAIN RESOLVER & ENVIRONMENT ROUTER
# ---------------------------------------------------------------------------

DOMAIN_GENERATOR_MAP: dict[TopicDomain, list[tuple[str, Any]]] = {
    TopicDomain.SOFTWARE_AI: [
        ("Vector Latent Space", generate_vector_latent_space_bg),
        ("Cloud Topology Mesh", generate_cloud_topology_mesh_bg),
        ("Neural Attention Lattice", generate_neural_attention_lattice_bg),
        ("Distributed Cluster Rack", generate_distributed_cluster_bg),
        ("Glass Command Stage", generate_glass_command_stage_bg),
    ],
    TopicDomain.ROBOTICS_HARDWARE: [
        ("Macro Precision Studio", generate_macro_studio_bg),
        ("Blueprint CAD Drafting", generate_blueprint_cad_bg),
        ("Tactical Radar Map", generate_tactical_radar_bg),
        ("Cinematic Logistics Warehouse", generate_cinematic_warehouse_bg),
        ("Premium Obsidian Brand Stage", generate_premium_brand_stage_bg),
    ],
    TopicDomain.BIOTECH_SCIENCE: [
        ("Molecular Lattice", generate_molecular_lattice_bg),
        ("Vector Latent Space", generate_vector_latent_space_bg),
        ("Molecular Lattice Deep", generate_molecular_lattice_bg),
        ("Neural Attention Lattice", generate_neural_attention_lattice_bg),
        ("Glass Command Stage", generate_glass_command_stage_bg),
    ],
    TopicDomain.FINANCE_MARKETS: [
        ("Candlestick Price Matrix", generate_candlestick_matrix_bg),
        ("Isometric Dot Grid", generate_isometric_grid_bg),
        ("Candlestick Price Matrix Deep", generate_candlestick_matrix_bg),
        ("Distributed Cluster Rack", generate_distributed_cluster_bg),
        ("Glass Command Stage", generate_glass_command_stage_bg),
    ],
    TopicDomain.GENERAL_TECH: [
        ("Macro Precision Studio", generate_macro_studio_bg),
        ("Isometric Dot Grid", generate_isometric_grid_bg),
        ("Cloud Topology Mesh", generate_cloud_topology_mesh_bg),
        ("Distributed Cluster Rack", generate_distributed_cluster_bg),
        ("Premium Obsidian Brand Stage", generate_premium_brand_stage_bg),
    ],
}


def resolve_environment_decision(
    scene_index: int,
    topic: str = "",
    subject: str = "",
    visual_purpose: str = "",
    narrative_role: str = "",
) -> EnvironmentDecision:
    """Authoritative decision engine deriving environment from topic and scene semantics."""
    domain = classify_topic_domain(topic=topic, subject=subject, visual_purpose=visual_purpose)
    generators = DOMAIN_GENERATOR_MAP.get(domain, DOMAIN_GENERATOR_MAP[TopicDomain.GENERAL_TECH])

    key_idx = min(scene_index, len(generators) - 1)
    arch_name, _ = generators[key_idx]

    rationale = (
        f"Domain '{domain.value}' chosen for topic '{topic}'. "
        f"Scene {scene_index + 1} ({narrative_role or 'content'}) assigned '{arch_name}' "
        f"to prevent mechanical robotics templates from leaking into software topics."
    )
    structural_features = [
        f"Domain: {domain.value}",
        f"Archetype: {arch_name}",
        f"SceneIndex: {scene_index}",
    ]

    return EnvironmentDecision(
        topic=topic,
        domain=domain.value,
        archetype=arch_name,
        rationale=rationale,
        structural_features=structural_features,
    )


def generate_environment_for_scene(
    scene_index: int,
    width: int = 1080,
    height: int = 1920,
    style: StyleSystem | None = None,
    topic: str = "",
    subject: str = "",
    visual_purpose: str = "",
    visual_metaphor: str = "",
    narrative_role: str = "",
) -> Image.Image:
    """Selects and renders the environment for a scene (guarantees no environment survives > 8s).
    
    Derived from topic, subject, and scene semantics—NOT just scene_index.
    Two unrelated topics receive fundamentally different visual environments.
    """
    decision = resolve_environment_decision(
        scene_index=scene_index,
        topic=topic,
        subject=subject,
        visual_purpose=visual_purpose,
        narrative_role=narrative_role,
    )

    domain = TopicDomain(decision.domain)
    generators = DOMAIN_GENERATOR_MAP.get(domain, DOMAIN_GENERATOR_MAP[TopicDomain.GENERAL_TECH])
    key_idx = min(scene_index, len(generators) - 1)
    _, generator_fn = generators[key_idx]

    img = generator_fn(width, height, style)
    # Store decision in image info for QA auditing
    img.info["environment_decision"] = decision.to_dict()
    return img
