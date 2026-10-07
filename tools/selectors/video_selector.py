"""Ranking and selection of video generation modes and adapters."""
from __future__ import annotations

import os
from typing import Any


class VideoProviderSelector:
    """Ranks video modes: remote neural video, image + native motion, or native technical animation."""

    MODES = {
        "remote_generated_video": {
            "name": "remote_video",
            "model": "svd_colab_remote",
            "max_duration": 4.0,
            "cost_per_second": 0.05,
            "latency_seconds": 30.0,
            "remote_capable": True,
            "env_key": "RUNWAY_API_KEY",
        },
        "generated_image_native_motion": {
            "name": "image_native_motion",
            "model": "ken_burns_camera_motion",
            "max_duration": 10.0,
            "cost_per_second": 0.0,
            "latency_seconds": 0.2,
            "remote_capable": False,
            "env_key": None,
        },
        "native_technical_animation": {
            "name": "native_animation",
            "model": "pil_svg_flow_animation",
            "max_duration": 15.0,
            "cost_per_second": 0.0,
            "latency_seconds": 0.1,
            "remote_capable": False,
            "env_key": None,
        },
    }

    def select_video_mode(
        self,
        scene_duration: float,
        motion_intent: str,
        budget_remaining: float = 10.0,
    ) -> dict[str, Any]:
        """Rank and return best video execution strategy."""
        # If remote neural video API key is set and budget permits, use remote neural video
        rem_key = os.getenv("RUNWAY_API_KEY") or os.getenv("LUMA_API_KEY")
        if rem_key and not rem_key.startswith("mock_"):
            cost = self.MODES["remote_generated_video"]["cost_per_second"] * scene_duration
            if cost <= budget_remaining:
                return self.MODES["remote_generated_video"]

        # Default robust strategy: High-res generated anchor image + native camera motion
        return self.MODES["generated_image_native_motion"]
