"""Ranking and selection of diagram rendering engines."""
from __future__ import annotations

from typing import Any


class DiagramProviderSelector:
    """Ranks diagram engines for technical architecture, system assembly, and metrics."""

    ENGINES = {
        "native_pil_svg": {
            "name": "native_diagram",
            "format": "png",
            "quality": 95,
            "cost": 0.0,
            "speed": "instant",
            "text_precision": "perfect",
        },
        "declarative_json_spec": {
            "name": "declarative_spec",
            "format": "json",
            "quality": 98,
            "cost": 0.0,
            "speed": "instant",
            "text_precision": "perfect",
        },
        "generative_schematic": {
            "name": "dall_e",
            "format": "png",
            "quality": 75,
            "cost": 0.040,
            "speed": "slow",
            "text_precision": "approximate",
        },
    }

    def select_diagram_engine(
        self,
        diagram_type: str,
        target_format: str = "png",
    ) -> dict[str, Any]:
        """Rank and return best diagram engine."""
        if target_format == "json":
            return self.ENGINES["declarative_json_spec"]
        return self.ENGINES["native_pil_svg"]
