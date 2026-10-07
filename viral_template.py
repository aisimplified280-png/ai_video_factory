"""
VIRAL_SHORT_V2 — Locked Cinematic Visual Language for AI Simplified Lab.

Single authoritative source for:
  - Canvas / safe-zone constants
  - 3-Layer Depth System (Background, Midground, Foreground)
  - Scene-specific color accents & scale crescendos
  - Camera motion presets
  - Hero visual primitives with depth & micro-motion
  - Scene role layout resolvers (Hook, Problem, Process, Proof, Payoff, CTA)
  - Procedural visual events
  - Kinetic typography & subtitle safe zones
  - Visual QA scorecard & density auditor

AI supplies: topic, narration, headline, hero_type, key_fact (optional), motion_energy
Template supplies: every coordinate, color, font, animation timing, depth layer, safe zone
"""
from __future__ import annotations
import math
import re
from dataclasses import dataclass, field

# ── Canvas ────────────────────────────────────────────────────────────────
W, H = 1080, 1920
FPS  = 24


@dataclass
class BrandTheme:
    """Centralized visual identity for AI Simplified Lab."""
    name: str = "AI Simplified Lab"
    canonical_brand_name: str = "AI Simplified Lab"
    canonical_cta: str = "Subscribe to AI Simplified Lab"
    typography: dict = field(default_factory=lambda: {
        "brand": "sans-serif",
        "headline": "sans-serif",
        "mono": "monospace",
    })
    colors: dict = field(default_factory=lambda: {
        "background": "#070A12",
        "background_2": "#0B1020",
        "panel": "#111827",
        "panel_2": "#172033",
        "primary": "#F8FAFC",
        "secondary": "#A7B0C0",
        "muted": "#64748B",
        "brand_primary": "#7C5CFF",
        "brand_secondary": "#00D9FF",
        "brand_gold": "#FBBF24",
        "success": "#22C55E",
        "warning": "#F59E0B",
        "danger": "#FF4D6D",
    })
    glow: dict = field(default_factory=lambda: {
        "strength": 0.75,
        "radius": 32,
        "filter": "soft",
    })
    shapes: dict = field(default_factory=lambda: {
        "radius": 24,
        "border_width": 2,
        "shadow_strength": 22,
    })
    motion: dict = field(default_factory=lambda: {
        "reveal": "ease_out_back",
        "flow": "ease_out_cubic",
        "pulse": "ease_in_out_quad",
    })
    subtitle: dict = field(default_factory=lambda: {
        "background": "#0B1020",
        "text": "#F8FAFC",
        "accent": "#00D9FF",
        "max_width": 900,
        "safe_y": 1710,
    })
    cta: dict = field(default_factory=lambda: {
        "text": "Subscribe to AI Simplified Lab",
        "button_text": "SUBSCRIBE",
        "subtext": "More AI breakdowns",
        "safe_margin": 90,
        "accent": "#7C5CFF",
        "secondary": "#00D9FF",
    })
    brand_mark: dict = field(default_factory=lambda: {
        "shape": "rounded_square",
        "size": 58,
        "corner_radius": 18,
        "stroke": 2,
    })
    safe_zones: dict = field(default_factory=lambda: {
        "cta": {"left": 80, "top": 120, "right": 1000, "bottom": 1700},
        "subtitle": {"left": 90, "top": 1630, "right": 990, "bottom": 1810},
    })
    transition_accent: dict = field(default_factory=lambda: {
        "color": "#00D9FF",
        "sweep": "soft",
    })


BRAND_THEME = BrandTheme()

CHANNEL_NAME = BRAND_THEME.canonical_brand_name
CHANNEL_NAME_UPPER = CHANNEL_NAME.upper()
SUBSCRIBE_CTA_TEXT = BRAND_THEME.canonical_cta
FORBIDDEN_BRAND_VARIATIONS = {
    "ai simplified",
    "ai simplified lab",
    "ai simplified labs",
    "ai simplified channel",
    "aisimplified",
}


def get_brand_theme() -> BrandTheme:
    return BRAND_THEME


def canonical_brand_name(name: str | None = None) -> str:
    """Return the canonical AI Simplified Lab channel name and normalize generic variants."""
    value = (name or CHANNEL_NAME).strip()
    if not value:
        return CHANNEL_NAME
    cleaned = re.sub(r"\s+", " ", value).strip()
    lowered = cleaned.lower()
    if lowered in FORBIDDEN_BRAND_VARIATIONS:
        return CHANNEL_NAME
    if lowered.startswith("ai simplified") and lowered != CHANNEL_NAME.lower():
        return CHANNEL_NAME
    if "ai simplified" in lowered and ("channel" in lowered or "lab" in lowered):
        return CHANNEL_NAME
    return cleaned


def validate_brand_name(name: str | None) -> bool:
    """Strict validation: only the canonical AI Simplified Lab name is accepted."""
    raw = (name or "").strip()
    return raw.lower() == CHANNEL_NAME.lower()


def brand_safe_zone(width: int = W, height: int = H) -> tuple[int, int, int, int]:
    """Compute the CTA-safe rectangle, respecting 9:16 portrait and 16:9 landscape."""
    margin_x = max(72, int(width * 0.08))
    margin_y = max(90, int(height * 0.12))
    if height > width:
        left, top, right, bottom = margin_x, margin_y, width - margin_x, height - margin_y
    else:
        left, top, right, bottom = int(width * 0.10), max(90, int(height * 0.12)), int(width * 0.90), int(height * 0.82)
    return left, top, right, bottom


def validate_cta_bounds(x: int, y: int, w: int, h: int, width: int = W, height: int = H) -> bool:
    """Ensure a CTA block sits within the safe area and does not collide with subtitle space."""
    left, top, right, bottom = brand_safe_zone(width, height)
    cx1 = x
    cy1 = y
    cx2 = x + w
    cy2 = y + h
    return (cx1 >= left and cy1 >= top and cx2 <= right and cy2 <= bottom)

# ── Safe Zones (pixel Y) ──────────────────────────────────────────────────
ZONE_A = (55,   135)   # Brand header — AI SIMPLIFIED LAB only
ZONE_B = (170,  520)   # Hook / headline
ZONE_C = (480,  1380)  # Hero visual — dominant element (expanded for V2)
ZONE_D = (1360, 1580)  # Impact / key fact (optional)
ZONE_E = (1630, 1810)  # Caption safe area (fixed)
ZONE_F = (1810, 1920)  # Bottom margin — keep quiet

HERO_MIN_W    = int(W * 0.55)
HERO_TARGET_W = int(W * 0.80)
HERO_TARGET_H = 800
HEADLINE_MAX_WORDS = 6
HEADLINE_MAX_W     = W - 100
CAPTION_CX    = W // 2
CAPTION_Y     = 1710
CAPTION_MAX_W = 900

# ── Semantic Palette ──────────────────────────────────────────────────────
BACKGROUND_0 = "#070A12"  # Deepest dark base
BACKGROUND_1 = "#0B1020"  # Subtle elevation
PANEL        = "#111827"  # Surface
PANEL_2      = "#172033"  # Elevated surface
PANEL_GLOW   = "#1E293B"

TEXT_PRIMARY   = "#F8FAFC"
TEXT_SECONDARY = "#A7B0C0"
TEXT_DIM       = "#64748B"

# Brand Accents
ACCENT       = "#7C5CFF"  # Electric Purple
ACCENT_2     = "#00D9FF"  # Cyan Glow
ACCENT_CYAN  = "#00D9FF"
ACCENT_GOLD  = "#FBBF24"  # Amber / Gold
SUCCESS      = "#22C55E"  # Emerald
WARNING      = "#F59E0B"  # Amber
DANGER       = "#FF4D6D"  # Coral Red

# ── Template Modes ────────────────────────────────────────────────────────
VIRAL_EXPLAINER = "viral_explainer"
VIRAL_NEWS      = "viral_news"
EDITORIAL_EXPLAINER = "editorial_explainer"
EDITORIAL_VIRAL = "editorial_viral"
SUPPORTED_MODES = {VIRAL_EXPLAINER, VIRAL_NEWS, EDITORIAL_EXPLAINER, EDITORIAL_VIRAL}

EDITORIAL_LIGHT = "#F6F8FC"
EDITORIAL_BLUE = "#1E5EFF"
EDITORIAL_DEEP = "#0E1B3A"
EDITORIAL_MUTED = "#697C96"
EDITORIAL_SOFT = "#EAF2FF"

# ── Scene Roles ───────────────────────────────────────────────────────────
ROLE_HOOK    = "hook"
ROLE_PROBLEM = "problem"
ROLE_PROCESS = "process"
ROLE_PROOF   = "proof"
ROLE_PAYOFF  = "payoff"
ROLE_CTA     = "cta"

INDEX_TO_ROLE = {
    0: ROLE_HOOK, 1: ROLE_PROBLEM, 2: ROLE_PROCESS,
    3: ROLE_PROOF, 4: ROLE_PAYOFF, 5: ROLE_CTA,
}

EXPLAINER_ROLES = [ROLE_HOOK, ROLE_PROBLEM, ROLE_PROCESS, ROLE_PROOF, ROLE_PAYOFF, ROLE_CTA]
NEWS_ROLES      = [ROLE_HOOK, ROLE_PROBLEM, ROLE_PROCESS, ROLE_PROOF, ROLE_PAYOFF, ROLE_CTA]

TEMPLATE_VERSION = "VIRAL_SHORT_V2"

# ── Scene-Specific Color Accents (Requirement 12) ─────────────────────────
ROLE_ACCENTS = {
    ROLE_HOOK:    (ACCENT, ACCENT_2),        # Purple + Cyan
    ROLE_PROBLEM: (DANGER, WARNING),         # Danger / Red + Amber
    ROLE_PROCESS: (ACCENT_2, SUCCESS),       # Cyan + Emerald
    ROLE_PROOF:   (ACCENT, TEXT_PRIMARY),    # Purple + White
    ROLE_PAYOFF:  (ACCENT, ACCENT_2),        # Purple + Cyan combined
    ROLE_CTA:     (ACCENT, ACCENT_2),        # Brand Purple
}

# ── Scale Crescendo (Requirement 3) ───────────────────────────────────────
ROLE_SCALES = {
    ROLE_HOOK:    1.00,
    ROLE_PROBLEM: 0.95,
    ROLE_PROCESS: 1.00,
    ROLE_PROOF:   1.05,
    ROLE_PAYOFF:  1.15,
    ROLE_CTA:     0.90,
}

# ── Camera Presets (Requirement 11) ───────────────────────────────────────
CAMERA_STATIC      = "camera_static"
CAMERA_PUSH        = "camera_push"
CAMERA_PULL        = "camera_pull"
CAMERA_SWEEP_LEFT  = "camera_sweep_left"
CAMERA_SWEEP_RIGHT = "camera_sweep_right"
CAMERA_FOCUS       = "camera_focus"
CAMERA_IMPACT      = "camera_impact"

ROLE_CAMERA_PRESETS = {
    ROLE_HOOK:    CAMERA_PUSH,
    ROLE_PROBLEM: CAMERA_SWEEP_LEFT,
    ROLE_PROCESS: CAMERA_SWEEP_RIGHT,
    ROLE_PROOF:   CAMERA_FOCUS,
    ROLE_PAYOFF:  CAMERA_IMPACT,
    ROLE_CTA:     CAMERA_STATIC,
}


def create_template_context(mode: str = "viral_explainer", role: str = "hook") -> dict:
    """Create a lightweight template context to propagate through the pipeline."""
    m = mode if mode in SUPPORTED_MODES else VIRAL_EXPLAINER
    return {
        "template_version": "VIRAL_SHORT_V2" if m in (VIRAL_EXPLAINER, VIRAL_NEWS) else "EDITORIAL_RENDER_PLAN",
        "template_mode": m,
        "scene_role": role,
    }


def build_semantic_visual_plan(scene: dict, index: int = 0, total: int = 6) -> dict:
    """Create a deterministic visual explanation plan from the scene content."""
    if not isinstance(scene, dict):
        return {
            "scene_role": "process",
            "visual_intent": "Explain the core system clearly.",
            "main_concept": "system",
            "primary_subject": "system",
            "secondary_subjects": [],
            "action": "reveal",
            "relationship": "system",
            "visual_metaphor": "flow",
            "preferred_primitive": "pipeline",
            "camera_behavior": "push_in",
            "motion_intensity": "medium",
            "visual_density": "medium",
            "emphasis_words": [],
            "data_points": [],
            "transition_intent": "connect",
        }

    text = sanitize_text(str(scene.get("narration", "") or scene.get("headline", "") or ""), "")
    role = str(scene.get("role", "") or scene.get("scene_role", "process")).strip().lower()
    if role not in {ROLE_HOOK, ROLE_PROBLEM, ROLE_PROCESS, ROLE_PROOF, ROLE_PAYOFF, ROLE_CTA}:
        role = INDEX_TO_ROLE.get(index, ROLE_PROCESS)

    lowered = text.lower()
    if any(k in lowered for k in ["match", "connect", "pair", "route", "find", "search"]):
        action = "matching"
        visual_metaphor = "network_flow"
        preferred_primitive = "pipeline"
    elif any(k in lowered for k in ["compare", "difference", "before", "after", "vs", "versus"]):
        action = "comparison"
        visual_metaphor = "before_after"
        preferred_primitive = "comparison_split"
    elif any(k in lowered for k in ["scale", "grow", "increase", "rise", "more", "%", "million", "billion"]):
        action = "growth"
        visual_metaphor = "metric_growth"
        preferred_primitive = "stat_burst"
    elif any(k in lowered for k in ["steps", "process", "how", "then", "next", "flow", "works"]):
        action = "process"
        visual_metaphor = "process_flow"
        preferred_primitive = "pipeline"
    elif any(k in lowered for k in ["fail", "error", "block", "slow", "break", "problem"]):
        action = "failure"
        visual_metaphor = "alert"
        preferred_primitive = "warning_burst"
    elif any(k in lowered for k in ["learn", "model", "ai", "train", "prompt", "agent"]):
        action = "inference"
        visual_metaphor = "ai_inference"
        preferred_primitive = "code_panel"
    else:
        action = "reveal"
        visual_metaphor = "flow"
        preferred_primitive = "pipeline"

    headline = sanitize_text(str(scene.get("headline", "") or ""), "")
    hero_type = sanitize_text(str(scene.get("hero_type", preferred_primitive)), preferred_primitive)
    primary_subject = sanitize_text(str(scene.get("primary_subject", scene.get("headline", "system"))), "system")
    emphasis_words = [w for w in re.findall(r"[A-Za-z][A-Za-z0-9%/.-]{2,}", headline.upper()) if len(w) >= 4][:3]
    if not emphasis_words:
        emphasis_words = [w for w in re.findall(r"[A-Za-z][A-Za-z0-9%/.-]{2,}", text.upper()) if len(w) >= 4][:3]

    plan = {
        "scene_role": role,
        "visual_intent": {
            ROLE_HOOK: "Open with a strong system framing and a memorable hero reveal.",
            ROLE_PROBLEM: "Show the pain point or friction in a way the audience instantly understands.",
            ROLE_PROCESS: "Explain the mechanism with a clear sequence or movement.",
            ROLE_PROOF: "Demonstrate evidence, trust, or measurable signal.",
            ROLE_PAYOFF: "Land the moment of value with a decisive, high-contrast result.",
            ROLE_CTA: "Close cleanly with a premium, brand-forward call to action.",
        }.get(role, "Explain the idea clearly and keep the relationship understandable."),
        "main_concept": sanitize_text(str(scene.get("main_concept", role)), role),
        "primary_subject": primary_subject,
        "secondary_subjects": scene.get("secondary_subjects") or [],
        "action": action,
        "relationship": sanitize_text(str(scene.get("relationship", "connects")), "connects"),
        "visual_metaphor": visual_metaphor,
        "preferred_primitive": hero_type or preferred_primitive,
        "camera_behavior": {
            ROLE_HOOK: "push_in",
            ROLE_PROBLEM: "pan_left",
            ROLE_PROCESS: "pan_right",
            ROLE_PROOF: "focus_reveal",
            ROLE_PAYOFF: "push_in",
            ROLE_CTA: "static",
        }.get(role, "static"),
        "motion_intensity": {
            ROLE_HOOK: "high",
            ROLE_PROBLEM: "medium",
            ROLE_PROCESS: "medium",
            ROLE_PROOF: "medium",
            ROLE_PAYOFF: "high",
            ROLE_CTA: "low",
        }.get(role, "medium"),
        "visual_density": "low" if role == ROLE_CTA else ("high" if role in {ROLE_HOOK, ROLE_PAYOFF} else "medium"),
        "emphasis_words": emphasis_words,
        "data_points": list(scene.get("visual_data", {}).keys()) if isinstance(scene.get("visual_data"), dict) else [],
        "transition_intent": "connect" if index < total - 1 else "resolve",
    }

    if not plan["main_concept"]:
        plan["main_concept"] = role
    if not plan["primary_subject"]:
        plan["primary_subject"] = role
    return plan


def validate_visual_plan(scene: dict) -> tuple[bool, list[str]]:
    """Check semantic scene metadata before render, returning warnings if invalid."""
    if not isinstance(scene, dict):
        return False, ["scene must be a mapping"]
    issues: list[str] = []
    role = str(scene.get("role", "") or scene.get("scene_role", "")).strip().lower()
    if not role:
        issues.append("missing role")
    if not scene.get("headline"):
        issues.append("missing headline")
    if not scene.get("narration"):
        issues.append("missing narration")
    visual_plan = scene.get("visual_plan") or build_semantic_visual_plan(scene)
    if not visual_plan.get("primary_subject"):
        issues.append("missing primary_subject")
    if not visual_plan.get("visual_intent"):
        issues.append("missing visual_intent")
    if not visual_plan.get("preferred_primitive"):
        issues.append("missing preferred_primitive")
    if not visual_plan.get("camera_behavior"):
        issues.append("missing camera_behavior")
    if not visual_plan.get("motion_intensity"):
        issues.append("missing motion_intensity")
    return (not issues), issues


def is_viral_template_scene(scene: dict) -> bool:
    """Authoritative detection for whether a scene belongs to VIRAL_SHORT_V1 or VIRAL_SHORT_V2."""
    if not isinstance(scene, dict):
        return False
    if is_editorial_template_scene(scene):
        return False
    kind = str(scene.get("kind", "")).strip().lower()
    tm = str(scene.get("_template_mode", "")).strip().lower()
    tc = scene.get("template_context") or {}
    tcv = str(tc.get("template_version", "")).strip().upper()
    tcm = str(tc.get("template_mode", "")).strip().lower()
    role = str(scene.get("role", "")).strip().lower()

    if kind in ("viral_short_v2", "viral_short_v1", "viral"):
        return True
    if tm in ("viral_explainer", "viral_news", "viral_short_v1", "viral_short_v2"):
        return True
    if tcv in ("VIRAL_SHORT_V2", "VIRAL_SHORT_V1") or tcm in ("viral_explainer", "viral_news"):
        return True
    if role in ("hook", "problem", "process", "proof", "payoff", "cta") and (
        "hero_type" in scene or "headline" in scene
    ):
        return True
    return False


def is_editorial_template_scene(scene: dict) -> bool:
    """True for the light editorial explainers and their hybrid variants."""
    if not isinstance(scene, dict):
        return False
    kind = str(scene.get("kind", "")).strip().lower()
    tm = str(scene.get("_template_mode", "")).strip().lower()
    tc = scene.get("template_context") or {}
    tcm = str(tc.get("template_mode", "")).strip().lower()
    if kind in ("editorial_explainer", "editorial_viral"):
        return True
    if tm in (EDITORIAL_EXPLAINER, EDITORIAL_VIRAL):
        return True
    if tcm in (EDITORIAL_EXPLAINER, EDITORIAL_VIRAL):
        return True
    return False

# ── Motion Presets ────────────────────────────────────────────────────────
MOTION_FAST_POP    = "fast_pop"
MOTION_SLIDE_UP    = "slide_up"
MOTION_SWEEP       = "sweep"
MOTION_DRAW        = "draw"
MOTION_PULSE       = "pulse"
MOTION_HERO_REVEAL = "hero_reveal"
MOTION_IMPACT      = "impact"

MOTION_ENERGY_MAP = {
    "high":   MOTION_HERO_REVEAL,
    "medium": MOTION_SLIDE_UP,
    "low":    MOTION_FAST_POP,
}

ROLE_TRANSITIONS = {
    ROLE_HOOK:    "zoom_in",
    ROLE_PROBLEM: "slide_up",
    ROLE_PROCESS: "slide_up",
    ROLE_PROOF:   "zoom_in",
    ROLE_PAYOFF:  "zoom_in",
    ROLE_CTA:     "crossfade",
}

# ── Registered Hero Primitives ───────────────────────────────────────────
HERO_PRIMITIVES = {
    "hero_orb", "hero_chip", "hero_brain", "hero_robot", "hero_device",
    "hero_server", "hero_model", "hero_logo_plate", "network_node", "data_stream",
    "particle_field", "code_panel", "device_mockup", "browser_mockup", "phone_mockup",
    "dashboard_mockup", "comparison_split", "pipeline", "timeline", "stat_burst",
    "keyword_burst", "warning_burst", "glow_ring", "arrow_stream", "result_reveal",
    "quote_panel", "cta_brand", "hero_glow",
}
HERO_FALLBACK = "hero_glow"

# ── Element stagger timing ────────────────────────────────────────────────
ELEMENT_STAGGER = {0: 0.00, 1: 0.10, 2: 0.28, 3: 0.45, 4: 0.60}
MAX_ENTRANCE_EVENTS = 4


def get_element_stagger(index: int) -> float:
    return ELEMENT_STAGGER.get(min(index, MAX_ENTRANCE_EVENTS - 1), 0.60)


# ── Zone Layout ───────────────────────────────────────────────────────────

@dataclass
class ZoneLayout:
    """Resolved pixel coordinates for one scene. Owned exclusively by the template."""
    brand_x:        int   = W // 2
    brand_y:        int   = (ZONE_A[0] + ZONE_A[1]) // 2
    headline_x:     int   = W // 2
    headline_y:     int   = 310
    headline_max_w: int   = HEADLINE_MAX_W
    hero_cx:        int   = W // 2
    hero_cy:        int   = 920
    hero_w:         int   = HERO_TARGET_W
    hero_h:         int   = HERO_TARGET_H
    impact_x:       int   = W // 2
    impact_y:       int   = 1430
    caption_x:      int   = CAPTION_CX
    caption_y:      int   = CAPTION_Y
    scale_multiplier: float = 1.0
    focal_point_type: str = "center"
    headline_bounds: tuple = field(default_factory=lambda: (40,  170, W-40, 520))
    hero_bounds:     tuple = field(default_factory=lambda: (0,   480, W,    1380))
    caption_bounds:  tuple = field(default_factory=lambda: (90, 1630, W-90, 1810))


def _resolve_role(scene: dict, index: int, total: int) -> str:
    """Resolve scene role deterministically."""
    role = str(scene.get("role", "")).strip().lower()
    if role in (ROLE_HOOK, ROLE_PROBLEM, ROLE_PROCESS, ROLE_PROOF, ROLE_PAYOFF, ROLE_CTA):
        return role
    if index == 0:
        return ROLE_HOOK
    if index >= total - 1:
        return ROLE_CTA
    return INDEX_TO_ROLE.get(index, ROLE_PROCESS)


def resolve_viral_template_layout(scene: dict, index: int, total: int) -> ZoneLayout:
    """
    SINGLE AUTHORITATIVE LAYOUT FUNCTION for VIRAL_SHORT_V2.

    Owns all coordinates, scales, and safe zones.
    """
    role = _resolve_role(scene, index, total)
    L = ZoneLayout()
    scale = ROLE_SCALES.get(role, 1.0)
    L.scale_multiplier = scale

    if role == ROLE_HOOK:
        L.headline_y = 310
        L.hero_cy    = 930
        L.hero_w     = int(W * 0.85 * scale)
        L.hero_h     = int(800 * scale)
        L.focal_point_type = "hero_dominant"
    elif role == ROLE_PROBLEM:
        L.headline_y = 290
        L.hero_cy    = 910
        L.hero_w     = int(W * 0.82 * scale)
        L.hero_h     = int(740 * scale)
        L.focal_point_type = "conflict_split"
    elif role == ROLE_PROCESS:
        L.headline_y = 270
        L.hero_cy    = 890
        L.hero_w     = int(W * 0.90 * scale)
        L.hero_h     = int(700 * scale)
        L.focal_point_type = "flow_conduit"
    elif role == ROLE_PROOF:
        L.headline_y = 250
        L.hero_cy    = 910
        L.hero_w     = int(W * 0.86 * scale)
        L.hero_h     = int(780 * scale)
        L.focal_point_type = "perspective_panel"
    elif role == ROLE_PAYOFF:
        L.headline_y = 280
        L.hero_cy    = 950
        L.hero_w     = int(W * 0.90 * scale)
        L.hero_h     = int(850 * scale)
        L.focal_point_type = "giant_payoff"
    elif role == ROLE_CTA:
        L.headline_y = 390
        L.hero_cy    = 970
        L.hero_w     = int(W * 0.75 * scale)
        L.hero_h     = int(680 * scale)
        L.focal_point_type = "brand_minimal"

    # Clamp to safe zones
    L.headline_y = max(ZONE_B[0] + 20, min(ZONE_B[1] - 50, L.headline_y))
    L.hero_cy    = max(ZONE_C[0] + L.hero_h // 2 + 10,
                       min(ZONE_C[1] - L.hero_h // 2 - 10, L.hero_cy))
    L.impact_y   = max(ZONE_D[0] + 40, min(ZONE_D[1] - 30, L.impact_y))
    return L


def resolve_hero_type(hero_type: str) -> str:
    """Map hero_type to a registered primitive, fallback to hero_glow."""
    if not hero_type:
        return HERO_FALLBACK
    ht = str(hero_type).lower().strip()
    semantic_aliases = {
        "network_flow": "pipeline",
        "process_flow": "pipeline",
        "matching": "pipeline",
        "comparison": "comparison_split",
        "before_after": "comparison_split",
        "metric_growth": "stat_burst",
        "growth": "stat_burst",
        "alert": "warning_burst",
        "failure": "warning_burst",
        "ai_inference": "code_panel",
        "model_pipeline": "code_panel",
        "system_architecture": "pipeline",
        "map_flow": "browser_mockup",
        "search": "browser_mockup",
        "queue": "pipeline",
        "sync": "data_stream",
        "cause_effect": "comparison_split",
        "step_reveal": "pipeline",
    }
    if ht in HERO_PRIMITIVES:
        return ht
    if ht in semantic_aliases:
        return semantic_aliases[ht]
    for p in HERO_PRIMITIVES:
        if p in ht or ht in p:
            return p
    return HERO_FALLBACK


# ── Text Sanitizer ────────────────────────────────────────────────────────
_BANNED = {"none", "null", "undefined", "n/a", "nan", "{}", "[]", "...",
           "template", "placeholder"}


def sanitize_text(text: str, fallback: str = "") -> str:
    """Strip null/placeholder/JSON fragments before rendering."""
    if not text:
        return fallback
    t = str(text).strip()
    t = re.sub(r"```[a-z]*", "", t)
    t = re.sub(r"```", "", t)
    t = re.sub(r"[\{\}\[\]]", "", t)
    t = t.strip(chr(34)).strip(chr(39))
    t = " ".join(t.split())
    if t.lower() in _BANNED or not t:
        return fallback
    return t


def truncate_headline(text: str, max_words: int = HEADLINE_MAX_WORDS) -> str:
    text = sanitize_text(text, "")
    words = text.split()
    return " ".join(words[:max_words]) if len(words) > max_words else text


# ── Auto-detect template mode (DETERMINISTIC) ─────────────────────────────
_NEWS_ACTIONS = {
    "announces", "announced", "launches", "launched", "releases", "released",
    "unveils", "unveiled", "acquires", "acquired", "raises", "raised",
    "funding", "breaking", "incident", "breach", "attack", "merger",
}


def auto_detect_template_mode(topic: str) -> str:
    """Choose an editorial mode by topic; legacy viral modes remain explicit opt-ins."""
    words = set(re.findall(r"[a-z0-9]+", (topic or "").lower()))
    return EDITORIAL_VIRAL if words & _NEWS_ACTIONS else EDITORIAL_EXPLAINER


# ── QA Visual Scorecard (Requirements 14, 15, 26) ─────────────────────────

@dataclass
class SceneQAReport:
    scene_index:              int
    role:                     str
    coverage_pct:             float = 0.0
    hero_width_pct:           float = 0.0
    headline_clipped:         bool  = False
    caption_clipped:          bool  = False
    hero_clipped:             bool  = False
    card_count:               int   = 0
    major_objects:            int   = 0
    major_text_blocks:        int   = 0
    motion_count:             int   = 2
    focal_point:              str   = "dominant"
    empty_center:             bool  = False
    has_unresolved_primitive: bool  = False
    passed:                   bool  = True
    failure_reasons:          list  = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "scene":             self.scene_index + 1,
            "role":              self.role,
            "coverage":          f"{self.coverage_pct:.1f}%",
            "hero_size":         f"{self.hero_width_pct:.1f}% width",
            "card_count":        self.card_count,
            "major_text_blocks": self.major_text_blocks,
            "motion_count":      self.motion_count,
            "focal_point":       self.focal_point,
            "headline_bounds":   "clipped" if self.headline_clipped else "ok",
            "caption_bounds":    "clipped" if self.caption_clipped  else "ok",
            "collision_status":  "fail"    if self.hero_clipped     else "ok",
            "empty_center":      "fail"    if self.empty_center     else "ok",
            "passed":            self.passed,
            "failures":          self.failure_reasons,
        }


def qa_scene(report: SceneQAReport) -> SceneQAReport:
    """Run all visual scorecard checks for VIRAL_SHORT_V2."""
    min_cov = 35.0 if report.role == ROLE_CTA else 50.0
    if report.coverage_pct < min_cov:
        report.passed = False
        report.failure_reasons.append(f"Coverage {report.coverage_pct:.1f}% < {min_cov}%")
    if report.role in (ROLE_HOOK, ROLE_PAYOFF) and report.hero_width_pct < 55.0:
        report.passed = False
        report.failure_reasons.append(f"Hero {report.hero_width_pct:.1f}% < 55%")
    if report.card_count > 1 and report.role != ROLE_PROOF:
        report.passed = False
        report.failure_reasons.append(f"Card count {report.card_count} > 1 (card repetition)")
    if report.headline_clipped:
        report.passed = False
        report.failure_reasons.append("Headline clipped")
    if report.caption_clipped:
        report.passed = False
        report.failure_reasons.append("Caption clipped")
    if report.major_text_blocks > 2:
        report.passed = False
        report.failure_reasons.append(f"Too many text blocks: {report.major_text_blocks} > 2")
    if report.motion_count < 2:
        report.passed = False
        report.failure_reasons.append(f"Motion count {report.motion_count} < 2")
    if report.empty_center:
        report.passed = False
        report.failure_reasons.append("Empty center detected")
    if report.has_unresolved_primitive:
        report.passed = False
        report.failure_reasons.append("Unresolved primitive")
    return report

