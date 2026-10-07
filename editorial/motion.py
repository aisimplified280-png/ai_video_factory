from __future__ import annotations


def semantic_motion_for(primary_intent: str, role: str = "process") -> dict:
    mappings = {
        "process": {"primary": "progression", "secondary": "left_to_right", "camera": "horizontal_tracking"},
        "connection": {"primary": "connection_draw", "secondary": "node_enter", "camera": "focus_shift"},
        "network": {"primary": "network_fade", "secondary": "radial_breathe", "camera": "slow_push"},
        "comparison": {"primary": "split_reveal", "secondary": "cross_fade", "camera": "side_swap"},
        "growth": {"primary": "expand_outward", "secondary": "upward_rise", "camera": "pull_back"},
        "alert": {"primary": "pulse_emphasis", "secondary": "warning_flash", "camera": "tight_zoom"},
        "timeline": {"primary": "event_flow", "secondary": "camera_travel", "camera": "horizontal_tracking"},
        "announcement": {"primary": "hero_reveal", "secondary": "soft_glow", "camera": "slow_push"},
        "architecture": {"primary": "layer_reveal", "secondary": "depth_shift", "camera": "detail_zoom"},
        "statistics": {"primary": "metric_rise", "secondary": "highlight_glow", "camera": "focus_shift"},
    }
    role_defaults = {
        "hook": {"primary": "hero_reveal", "secondary": "soft_glow", "camera": "slow_push"},
        "problem": {"primary": "pulse_emphasis", "secondary": "tighten_focus", "camera": "tight_zoom"},
        "process": {"primary": "progression", "secondary": "left_to_right", "camera": "horizontal_tracking"},
        "proof": {"primary": "metric_rise", "secondary": "highlight_glow", "camera": "focus_shift"},
        "payoff": {"primary": "expand_outward", "secondary": "upward_rise", "camera": "pull_back"},
        "cta": {"primary": "hero_reveal", "secondary": "soft_glow", "camera": "slow_push"},
    }
    base = mappings.get(primary_intent, role_defaults.get(role, {"primary": "reveal", "secondary": "soft_fade", "camera": "static"}))
    return {
        "primary": base["primary"],
        "secondary": base["secondary"],
        "camera": base["camera"],
        "role": role,
    }
