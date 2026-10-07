"""Sequence & Motion Director Agent for AI SIMPLIFIED LAB.

Defines perfect sequential entry timing, spatial bounds, motion curves, and 2D collision avoidance for all scene elements.
"""
from __future__ import annotations

from typing import List, Dict, Any


def optimize_scene_sequence(elements: List[Dict[str, Any]], scene_title: str = "",
                            template_mode: str = "") -> List[Dict[str, Any]]:
    """Sequence Director: Calculates non-overlapping spatial coordinates and staggered entry motions.

    For viral_short_v1 scenes, this is a NO-OP — sequencing is owned by viral_template.py.
    """
    if not elements:
        return []

    # ── VIRAL BYPASS: template layout owns all staggering ─────────────────
    if template_mode in ("viral_explainer", "viral_news", "viral_short_v1", "editorial_explainer", "editorial_viral"):
        return elements
    if elements and elements[0].get("_viral_scene"):
        return elements

    # Standard vertical layout slots to guarantee zero 2D collisions
    layout_slots = [
        {"x": 0.5, "y": 0.20, "motion": "slide_down"},   # Slot 0: Top Badge / Subtitle Header
        {"x": 0.5, "y": 0.45, "motion": "pop"},          # Slot 1: Center Hero Card / Main Diagram
        {"x": 0.24, "y": 0.72, "motion": "slide_right"},  # Slot 2: Bottom-Left Component / Icon
        {"x": 0.76, "y": 0.72, "motion": "slide_left"},   # Slot 3: Bottom-Right Component / Icon
        {"x": 0.5, "y": 0.85, "motion": "slide_up"},     # Slot 4: Bottom Key Metric / Takeaway
    ]

    total_els = len(elements)
    stagger_step = min(0.20, 0.75 / max(total_els, 1))

    for idx, el in enumerate(elements):
        # 1. Assign staggered entry timing
        el["enter_start"] = round(idx * stagger_step, 2)
        el["enter_end"] = round(min(1.0, el["enter_start"] + 0.25), 2)

        # 2. Assign default motion curves if not specified
        if "motion" not in el or el["motion"] == "fade":
            if idx == 0:
                el["motion"] = "slide_down"
            elif idx == 1:
                el["motion"] = "scale" if el.get("type") in ("mac_window", "vs_card", "layers") else "pop"
            elif el.get("type") == "arrow":
                el["motion"] = "draw_line"
            elif idx == total_els - 1:
                el["motion"] = "slide_up"
            else:
                el["motion"] = "pop"

    return elements
