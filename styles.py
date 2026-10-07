"""Video style engine — defines scene templates for different video formats.

Each style maps topic concepts to scene sequences optimised for engagement.
The planner picks a style based on user preference or auto-detects from topic.

VIRAL_SHORT_V1 adds two locked modes:
  viral_explainer — tutorial / concept / definition content
  viral_news      — product launch / news / announcement content
"""
from __future__ import annotations
from dataclasses import dataclass, field

# ── Scene kinds ──────────────────────────────────────────────────────────
CUSTOM = "custom"          # Legacy kinetic compositor
VIRAL = "viral_short_v1"  # Locked viral template


# ── Virality timing ──────────────────────────────────────────────────────
FAST_PACING   = 2.5
NORMAL_PACING = 4.0
SLOW_PACING   = 5.0


@dataclass
class SceneTemplate:
    kind: str
    heading: str = ""
    subheading: str = ""
    left: str = ""
    right: str = ""
    narration: str = ""
    duration_override: float | None = None  # per-scene seconds
    # Animation motion directions for each element
    motion: dict = field(default_factory=dict)
    # UI Component Elements
    elements: list[dict] = field(default_factory=list)


@dataclass
class StyleDefinition:
    name: str
    description: str
    pacing: float  # seconds per scene
    scene_count: int
    intro_duration: float  # seconds for element animation
    outro_duration: float
    scenes: list[SceneTemplate]
    # Visual style flags
    uses_stickman: bool = False
    uses_dark_theme: bool = False
    has_comparison: bool = False


# ══════════════════════════════════════════════════════════════════════════
# STYLE: kinetic (Masterclass UI aesthetic)
# ══════════════════════════════════════════════════════════════════════════
KINETIC_STYLE = StyleDefinition(
    name="kinetic",
    description="Modern technical developer software demo — crisp kinetic typography, glassmorphic cards, data flows, and code grids. Strictly UI components, no characters.",
    pacing=3.0,
    scene_count=6,
    intro_duration=1.0,
    outro_duration=0.5,
    has_comparison=True,
    scenes=[
        SceneTemplate(
            kind=CUSTOM,
            heading="SYSTEM INITIALIZATION",
            narration="Today we are breaking down {concept}, fast.",
            elements=[{"type": "tech_header", "text": "{concept}", "lesson_num": "01", "x": 0.5, "y": 0.5}]
        ),
        SceneTemplate(
            kind=CUSTOM,
            heading="CORE ARCHITECTURE",
            narration="At its core, {concept} transforms the way we build systems.",
            elements=[{"type": "mac_window", "title": "{concept} Engine", "x": 0.5, "y": 0.5, "width": 0.8, "height": 0.5}]
        ),
        SceneTemplate(
            kind=CUSTOM,
            heading="EXECUTION MATRIX",
            narration="{point_1_narration}",
            elements=[{"type": "ui_card", "text": "{point_1}", "x": 0.5, "y": 0.5, "width": 0.6, "height": 0.2}]
        ),
        SceneTemplate(
            kind=CUSTOM,
            heading="PROCESS PIPELINE",
            narration="{point_2_narration}",
            elements=[{"type": "ui_card", "text": "{point_2}", "x": 0.5, "y": 0.5, "width": 0.6, "height": 0.2}]
        ),
        SceneTemplate(
            kind=CUSTOM,
            heading="PERFORMANCE BENCHMARK",
            narration="Side by side, the efficiency gains are massive.",
            elements=[{"type": "comparison_grid", "left_title": "Before", "right_title": "{concept}", "x": 0.5, "y": 0.5}]
        ),
        SceneTemplate(
            kind=CUSTOM,
            heading="SYSTEM TERMINATED",
            narration="Save this module for later and subscribe for more.",
            elements=[{"type": "subscribe_card", "x": 0.5, "y": 0.5}]
        ),
    ],
)


# ══════════════════════════════════════════════════════════════════════════
# VIRAL_SHORT_V1 Styles
# ══════════════════════════════════════════════════════════════════════════
VIRAL_EXPLAINER_STYLE = StyleDefinition(
    name="viral_explainer",
    description="Dark cinematic tech explainer — locked safe zones, deterministic layout, hero visuals, kinetic typography.",
    pacing=FAST_PACING,
    scene_count=6,
    intro_duration=0.8,
    outro_duration=0.3,
    uses_dark_theme=True,
    scenes=[
        SceneTemplate(kind=VIRAL, heading="HOOK",     narration=""),
        SceneTemplate(kind=VIRAL, heading="PROBLEM",  narration=""),
        SceneTemplate(kind=VIRAL, heading="PROCESS",  narration=""),
        SceneTemplate(kind=VIRAL, heading="PROOF",    narration=""),
        SceneTemplate(kind=VIRAL, heading="PAYOFF",   narration=""),
        SceneTemplate(kind=VIRAL, heading="CTA",      narration=""),
    ],
)

VIRAL_NEWS_STYLE = StyleDefinition(
    name="viral_news",
    description="Dark cinematic AI/tech news — hook, what-happened, what-changed, key-detail, why-it-matters, CTA.",
    pacing=FAST_PACING,
    scene_count=6,
    intro_duration=0.8,
    outro_duration=0.3,
    uses_dark_theme=True,
    scenes=[
        SceneTemplate(kind=VIRAL, heading="HOOK",         narration=""),
        SceneTemplate(kind=VIRAL, heading="WHAT HAPPENED", narration=""),
        SceneTemplate(kind=VIRAL, heading="WHAT CHANGED",  narration=""),
        SceneTemplate(kind=VIRAL, heading="KEY DETAIL",    narration=""),
        SceneTemplate(kind=VIRAL, heading="WHY IT MATTERS",narration=""),
        SceneTemplate(kind=VIRAL, heading="CTA",           narration=""),
    ],
)

EDITORIAL_EXPLAINER_STYLE = StyleDefinition(
    name="editorial_explainer",
    description="Clean editorial explainer — premium light canvas, subtle brand blue, process diagrams, and strong motion-driven hierarchy.",
    pacing=FAST_PACING,
    scene_count=6,
    intro_duration=0.9,
    outro_duration=0.4,
    uses_dark_theme=False,
    scenes=[
        SceneTemplate(kind=VIRAL, heading="HOOK",     narration=""),
        SceneTemplate(kind=VIRAL, heading="PROBLEM",  narration=""),
        SceneTemplate(kind=VIRAL, heading="PROCESS",  narration=""),
        SceneTemplate(kind=VIRAL, heading="PROOF",    narration=""),
        SceneTemplate(kind=VIRAL, heading="PAYOFF",   narration=""),
        SceneTemplate(kind=VIRAL, heading="CTA",      narration=""),
    ],
)

EDITORIAL_VIRAL_STYLE = StyleDefinition(
    name="editorial_viral",
    description="Editorial explainer with faster Shorts pacing and sharper visual transitions for AI simplified channel storytelling.",
    pacing=2.8,
    scene_count=6,
    intro_duration=0.8,
    outro_duration=0.3,
    uses_dark_theme=False,
    scenes=[
        SceneTemplate(kind=VIRAL, heading="HOOK",     narration=""),
        SceneTemplate(kind=VIRAL, heading="PROBLEM",  narration=""),
        SceneTemplate(kind=VIRAL, heading="PROCESS",  narration=""),
        SceneTemplate(kind=VIRAL, heading="PROOF",    narration=""),
        SceneTemplate(kind=VIRAL, heading="PAYOFF",   narration=""),
        SceneTemplate(kind=VIRAL, heading="CTA",      narration=""),
    ],
)

VIRAL_SHORT_STYLE = VIRAL_EXPLAINER_STYLE  # Alias


# ══════════════════════════════════════════════════════════════════════════
# Style registry
# ══════════════════════════════════════════════════════════════════════════
STYLES = {
    "viral_explainer":  VIRAL_EXPLAINER_STYLE,
    "viral_news":       VIRAL_NEWS_STYLE,
    "viral_short_v1":   VIRAL_SHORT_STYLE,
    "editorial_explainer": EDITORIAL_EXPLAINER_STYLE,
    "editorial_viral":  EDITORIAL_VIRAL_STYLE,
    "editorial_short":  EDITORIAL_EXPLAINER_STYLE,
    "explainer":        EDITORIAL_EXPLAINER_STYLE,
    "news":             VIRAL_NEWS_STYLE,
    "kinetic":          VIRAL_EXPLAINER_STYLE,
    "comparison":       VIRAL_EXPLAINER_STYLE,
    "interview":        VIRAL_EXPLAINER_STYLE,
    "list":             VIRAL_EXPLAINER_STYLE,
    "legacy_kinetic":   KINETIC_STYLE,
}


def get_style(name: str) -> StyleDefinition:
    key = str(name).lower().strip()
    return STYLES.get(key, EDITORIAL_EXPLAINER_STYLE)


def list_styles() -> list[dict]:
    return [
        {"key": "viral_explainer", "name": VIRAL_EXPLAINER_STYLE.name, "description": VIRAL_EXPLAINER_STYLE.description},
        {"key": "viral_news", "name": VIRAL_NEWS_STYLE.name, "description": VIRAL_NEWS_STYLE.description},
        {"key": "editorial_explainer", "name": EDITORIAL_EXPLAINER_STYLE.name, "description": EDITORIAL_EXPLAINER_STYLE.description},
        {"key": "editorial_viral", "name": EDITORIAL_VIRAL_STYLE.name, "description": EDITORIAL_VIRAL_STYLE.description},
    ]


def auto_detect_style(topic: str) -> str:
    """Retain the existing project default behavior while allowing explicit editorial mode selection."""
    try:
        from viral_template import auto_detect_template_mode
        return auto_detect_template_mode(topic)
    except ImportError:
        pass
    return "viral_explainer"
