from __future__ import annotations


LAYOUT_MAP = {
    "centered_hero": {"label": "centered hero", "composition": "single story object with strong headline"},
    "split_screen": {"label": "split screen", "composition": "left-right comparison or transformation"},
    "horizontal_process": {"label": "horizontal process", "composition": "step sequence flowing across the frame"},
    "vertical_process": {"label": "vertical process", "composition": "stacked progression from top to bottom"},
    "network": {"label": "radial network", "composition": "connected nodes and relationship lines"},
    "diagram": {"label": "full-canvas diagram", "composition": "system diagram with clear object hierarchy"},
    "detail_zoom": {"label": "zoomed detail", "composition": "tight close-up on the critical object or interface"},
    "timeline": {"label": "timeline", "composition": "ordered event progression with markers"},
    "map": {"label": "location map", "composition": "geographic or spatial logic"},
    "editorial": {"label": "editorial stack", "composition": "premium narrative card with supporting details"},
}


def resolve_composition(layout_family: str, aspect_ratio: str = "9:16") -> dict:
    layout = LAYOUT_MAP.get(layout_family, LAYOUT_MAP["editorial"])
    return {
        "layout_family": layout_family,
        "layout_label": layout["label"],
        "composition": layout["composition"],
        "aspect_ratio": aspect_ratio,
        "safe_margins": {"left": 80, "right": 80, "top": 120, "bottom": 120},
    }
