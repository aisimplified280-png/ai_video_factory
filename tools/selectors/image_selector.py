"""Ranking and selection of image generation providers based on capability, cost, and availability."""
from __future__ import annotations

import os
from typing import Any


class ImageProviderSelector:
    """Ranks image providers by task fit, quality, speed, cost, and availability."""

    PROVIDERS = {
        "dall_e": {
            "name": "dall_e",
            "model": "dall-e-3",
            "resolution": "1024x1792",
            "quality": 95,
            "cost_per_image": 0.040,
            "latency_seconds": 12.0,
            "remote_capable": True,
            "env_key": "OPENAI_API_KEY",
        },
        "gemini_imagen": {
            "name": "gemini_imagen",
            "model": "imagen-3.0-generate-002",
            "resolution": "1024x1792",
            "quality": 92,
            "cost_per_image": 0.030,
            "latency_seconds": 8.0,
            "remote_capable": True,
            "env_key": "GEMINI_API_KEY",
        },
        "native_canvas": {
            "name": "native_diagram",
            "model": "native_pil_svg",
            "resolution": "1080x1920",
            "quality": 88,
            "cost_per_image": 0.0,
            "latency_seconds": 0.1,
            "remote_capable": False,
            "env_key": None,
        },
    }

    def select_best_provider(
        self,
        task_requirements: dict[str, Any],
        budget_remaining: float = 10.0,
    ) -> dict[str, Any]:
        """Rank and return the optimal provider candidate for the image task."""
        candidates = []
        for name, spec in self.PROVIDERS.items():
            # Check availability
            env_var = spec["env_key"]
            is_available = True
            if env_var:
                val = os.getenv(env_var, "")
                is_available = bool(val and not val.startswith("mock_"))

            if not is_available and name != "native_canvas":
                continue

            # Check budget fit
            if spec["cost_per_image"] > budget_remaining:
                continue

            # Score calculation
            score = spec["quality"]
            if spec["cost_per_image"] == 0:
                score += 5.0  # Reward free native execution

            candidates.append((score, spec))

        candidates.sort(key=lambda x: x[0], reverse=True)
        if candidates:
            return candidates[0][1]

        return self.PROVIDERS["native_canvas"]
