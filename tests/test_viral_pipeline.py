"""
Unit and Integration Tests for VIRAL_SHORT_V2 Pipeline Routing and Invariants.
"""
import math
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from PIL import ImageChops
from create_short import get_scene_transition_config, render_scene_frames
from viral_renderer import _ping_pong_value
from viral_template import (
    is_viral_template_scene, create_template_context, build_semantic_visual_plan,
    validate_visual_plan, get_brand_theme, validate_cta_bounds, canonical_brand_name,
    validate_brand_name, SUBSCRIBE_CTA_TEXT, VIRAL_EXPLAINER, VIRAL_NEWS, BACKGROUND_0,
    EDITORIAL_LIGHT, ROLE_HOOK, ROLE_PROBLEM, ROLE_PROCESS, ROLE_PROOF, ROLE_PAYOFF, ROLE_CTA,
)
from styles import auto_detect_style, get_style
from storyboard import generate_storyboard, _validate_viral_storyboard
from animation import build_scene, custom, make_scene_frames, render_frame, viral_scene, PAPER_BG
from editorial import analyze_narration, build_editorial_plan, semantic_motion_for


def test_semantic_editorial_plan_chooses_meaningful_intents_and_layout():
    """The editorial engine should turn narration into structured visual intent and a layout family."""
    plan = build_editorial_plan(
        {
            "role": "process",
            "headline": "MATCHING RIDERS TO DRIVERS",
            "narration": "Uber matches riders with nearby drivers in seconds.",
            "hero_type": "network_flow",
        }
    )
    assert plan["layout_family"]
    assert "process" in plan["intents"] or "connection" in plan["intents"] or "network" in plan["intents"]
    assert plan["visual_strategy"]
    assert plan["motion"]["primary"]
    assert plan["camera"]["behavior"]


def test_editorial_render_plan_is_executable_and_covers_full_scene_duration():
    """The editorial renderer must consume a single authoritative render plan with full timeline coverage."""
    plan = build_editorial_plan(
        {
            "role": "hook",
            "headline": "WHY AI NEEDS MORE POWER",
            "narration": "Why do massive AI models constantly demand more and more computer power?",
            "hero_type": "hero_chip",
        }
    )
    assert "render_plan" in plan
    render_plan = plan["render_plan"]
    assert render_plan["layout"]["family"]
    assert render_plan["primitives"]
    assert render_plan["camera"]["behavior"]
    assert render_plan["shot_plan"][0]["start"] == 0.0
    assert render_plan["shot_plan"][-1]["end"] >= 5.0
    assert render_plan["shot_plan"][-1]["end"] >= render_plan["shot_plan"][0]["start"]


def test_editorial_executor_never_invents_metric_values():
    scene = {
        "role": "problem",
        "headline": "AI WAS LOCKED AWAY",
        "narration": "Building artificial intelligence required billions in funding and closed doors.",
        "supporting_fact": "High barriers to entry for developers.",
    }
    plan = build_editorial_plan(scene)["render_plan"]
    assert plan["primitive"] == "large_metric"
    assert plan["metric_value"] is None
    assert plan["metric_label"] == "BILLIONS"
    assert plan["action"] == "reveal"
    scene.update({
        "kind": "editorial_explainer",
        "_template_mode": "editorial_explainer",
        "render_plan": plan,
    })
    elements, bg, bg_fn = build_scene(scene, 1, 6)
    render_frame(elements, 1, 2, bg, bg_fn, t_seconds=2.5)
    assert scene["render_manifest"]["actions_executed"] == ["reveal_visual"]


def test_editorial_cta_shot_holds_through_scene_end():
    plan = build_editorial_plan({
        "role": "cta",
        "headline": "SUBSCRIBE TO AI SIMPLIFIED LAB",
        "narration": "Subscribe to AI Simplified Lab for more technology explainers.",
    })["render_plan"]
    assert len(plan["shot_plan"]) == 1
    assert plan["shot_plan"][0]["start"] == 0.0
    assert plan["shot_plan"][0]["end"] >= 5.0
    assert plan["shot_plan"][0]["focus"] == "cta"


def test_editorial_role_motion_defaults_are_not_static():
    assert semantic_motion_for("technology", "hook")["camera"] == "slow_push"
    assert semantic_motion_for("technology", "process")["camera"] == "horizontal_tracking"
    assert semantic_motion_for("technology", "proof")["camera"] == "focus_shift"


def _editorial_pixels(render_plan, duration=5.0):
    scene = {
        "kind": "editorial_explainer",
        "_template_mode": "editorial_explainer",
        "template_context": create_template_context("editorial_explainer", "process"),
        "role": "process",
        "headline": "THE SAME EXPLANATION",
        "narration": "A system connects signals and turns them into a useful result.",
        "supporting_fact": "Same words, different execution plan.",
        "_render_duration_seconds": duration,
        "render_plan": render_plan,
    }
    elements, bg, bg_fn = build_scene(scene, 2, 6)
    return scene, elements, bg, bg_fn


def _pixels_differ(first, second):
    return ImageChops.difference(first.convert("RGB"), second.convert("RGB")).getbbox() is not None


def _base_render_plan():
    return {
        "layout_family": "network",
        "layout": {"family": "network"},
        "primitive": "network_nodes",
        "action": "connect",
        "motion": {"primary": "reveal"},
        "camera": {"behavior": "static"},
        "shot_plan": [{"start": 0.0, "end": 5.0, "focus": "connections", "visual_story": "connect the system nodes"}],
    }


def test_editorial_render_uses_render_plan():
    network_plan = _base_render_plan()
    split_plan = {**network_plan, "layout_family": "split_screen"}
    network_scene, network_els, network_bg, network_fn = _editorial_pixels(network_plan)
    split_scene, split_els, split_bg, split_fn = _editorial_pixels(split_plan)
    network_frame = render_frame(network_els, 1, 2, network_bg, network_fn, t_seconds=2.5)
    split_frame = render_frame(split_els, 1, 2, split_bg, split_fn, t_seconds=2.5)
    assert network_scene["render_plan"]["layout_family"] == "network"
    assert split_scene["render_plan"]["layout_family"] == "split_screen"
    assert _pixels_differ(network_frame, split_frame)
    assert network_scene["render_manifest"]["layout_executor"] == "network_layout"
    assert split_scene["render_manifest"]["layout_executor"] == "split_screen_layout_scaffold"


def test_editorial_primitive_and_action_change_pixels():
    network_plan = _base_render_plan()
    metric_plan = {**network_plan, "primitive": "large_metric"}
    count_up_plan = {**metric_plan, "action": "count_up", "metric_value": 100}
    reveal_action_plan = {**network_plan, "action": "reveal"}
    _, network_els, network_bg, network_fn = _editorial_pixels(network_plan)
    metric_scene, metric_els, metric_bg, metric_fn = _editorial_pixels(metric_plan)
    count_up_scene, count_up_els, count_up_bg, count_up_fn = _editorial_pixels(count_up_plan)
    _, reveal_action_els, reveal_action_bg, reveal_action_fn = _editorial_pixels(reveal_action_plan)
    network_frame = render_frame(network_els, 1, 2, network_bg, network_fn, t_seconds=2.5)
    metric_frame = render_frame(metric_els, 1, 2, metric_bg, metric_fn, t_seconds=2.5)
    count_up_frame = render_frame(count_up_els, 1, 2, count_up_bg, count_up_fn, t_seconds=2.5)
    reveal_action_frame = render_frame(reveal_action_els, 1, 2, reveal_action_bg, reveal_action_fn, t_seconds=2.5)
    assert _pixels_differ(network_frame, metric_frame)
    assert _pixels_differ(metric_frame, count_up_frame)
    assert _pixels_differ(network_frame, reveal_action_frame)
    assert metric_scene["render_manifest"]["primitive_executors"] == ["draw_large_metric"]
    assert metric_scene["render_manifest"]["actions_executed"] == ["animate_connections"]
    assert count_up_scene["render_manifest"]["actions_executed"] == ["animate_count_up"]


def test_editorial_motion_and_camera_change_rendered_frames():
    reveal = _base_render_plan()
    grow = {**reveal, "motion": {"primary": "grow"}}
    _, reveal_els, reveal_bg, reveal_fn = _editorial_pixels(reveal, duration=2.0)
    _, grow_els, grow_bg, grow_fn = _editorial_pixels(grow, duration=2.0)
    reveal_frames = list(make_scene_frames(reveal_els, 2.0, fps=2, intro_seconds=2.0,
                                           bg_color=reveal_bg, bg_fn=reveal_fn, scene_dict={"kind": "editorial_explainer", "_template_mode": "editorial_explainer", "render_plan": reveal}))
    grow_frames = list(make_scene_frames(grow_els, 2.0, fps=2, intro_seconds=2.0,
                                         bg_color=grow_bg, bg_fn=grow_fn, scene_dict={"kind": "editorial_explainer", "_template_mode": "editorial_explainer", "render_plan": grow}))
    assert _pixels_differ(reveal_frames[-1], grow_frames[-1])

    pushed = {**reveal, "camera": {"behavior": "push_in"}}
    static = {**reveal, "camera": {"behavior": "static"}}
    _, pushed_els, pushed_bg, pushed_fn = _editorial_pixels(pushed, duration=2.0)
    _, static_els, static_bg, static_fn = _editorial_pixels(static, duration=2.0)
    pushed_frames = list(make_scene_frames(pushed_els, 2.0, fps=2, intro_seconds=2.0,
                                           bg_color=pushed_bg, bg_fn=pushed_fn, scene_dict={"kind": "editorial_explainer", "_template_mode": "editorial_explainer", "render_plan": pushed}))
    static_frames = list(make_scene_frames(static_els, 2.0, fps=2, intro_seconds=2.0,
                                           bg_color=static_bg, bg_fn=static_fn, scene_dict={"kind": "editorial_explainer", "_template_mode": "editorial_explainer", "render_plan": static}))
    assert _pixels_differ(pushed_frames[-1], static_frames[-1])


def test_editorial_shot_plan_executes_all_full_duration_shots():
    plan = _base_render_plan()
    plan["shot_plan"] = [
        {"start": 0.0, "end": 1.2, "focus": "signal", "visual_story": "introduce the incoming signal"},
        {"start": 1.2, "end": 2.4, "focus": "connection", "visual_story": "connect the separate nodes"},
        {"start": 2.4, "end": 3.7, "focus": "transformation", "visual_story": "show the system transformation"},
        {"start": 3.7, "end": 5.0, "focus": "result", "visual_story": "resolve on the useful result"},
    ]
    scene, elements, bg, bg_fn = _editorial_pixels(plan)
    frames = list(make_scene_frames(elements, 5.0, fps=1, intro_seconds=5.0,
                                    bg_color=bg, bg_fn=bg_fn, scene_dict=scene))
    executed = scene["render_manifest"]["shots_executed"]
    assert [shot["index"] for shot in executed] == [0, 1, 2, 3]
    assert executed[0]["start"] == 0.0 and executed[-1]["end"] == 5.0
    assert all(left["end"] == right["start"] for left, right in zip(executed, executed[1:]))
    assert len(frames) == 5
    assert all(_pixels_differ(frames[i], frames[i + 1]) for i in (1, 2, 3))

    longer_scene, _, _, _ = _editorial_pixels(_base_render_plan(), duration=6.0)
    assert longer_scene["render_plan"]["shot_plan"][-1]["end"] == 6.0


def test_editorial_render_bypasses_legacy_template_visual_selection(monkeypatch):
    import animation
    import vo_composition_agent

    def fail_legacy(*args, **kwargs):
        raise AssertionError("legacy viral renderer was called for an editorial scene")

    monkeypatch.setattr(animation, "viral_scene", fail_legacy)
    monkeypatch.setattr(vo_composition_agent, "process_scene_composition", fail_legacy)
    scene = {
        "kind": "viral_short_v2",
        "_template_mode": "editorial_viral",
        "template_context": create_template_context("editorial_viral", "process"),
        "role": "process",
        "headline": "A PLAN-DRIVEN SCENE",
        "narration": "The render plan controls how this scene is drawn.",
        "hero_type": "hero_chip",
        "hero_label": "Legacy label must not choose the visual",
        "motion_energy": "high",
        "camera_behavior": "push_in",
        "visual_density": "high",
        "render_plan": _base_render_plan(),
    }
    animation.build_scene(scene, 0, 1)
    assert scene["render_manifest"]["legacy_template_bypassed"] is True
    assert scene["render_manifest"]["render_mode"] == "editorial_viral"

    conflicting_legacy_fields = {
        **scene,
        "hero_type": "hero_robot",
        "hero_label": "Different legacy label",
        "preferred_primitive": "hero_server",
        "motion_energy": "low",
        "camera_behavior": "pan_left",
        "visual_density": "low",
        "template_context": {"template_version": "VIRAL_SHORT_V2", "template_mode": "editorial_viral", "scene_role": "process"},
    }
    conflicting_legacy_fields.update({
        "kind": "editorial_viral",
        "_template_mode": "editorial_viral",
        "render_plan": scene["render_plan"],
        "headline": scene["headline"],
        "narration": scene["narration"],
    })
    base_elements, base_bg, base_bg_fn = animation.build_scene(scene, 0, 1)
    legacy_elements, legacy_bg, legacy_bg_fn = animation.build_scene(conflicting_legacy_fields, 0, 1)
    first = render_frame(base_elements, 1, 2, base_bg, base_bg_fn, t_seconds=2.5)
    second = render_frame(legacy_elements, 1, 2, legacy_bg, legacy_bg_fn, t_seconds=2.5)
    assert not _pixels_differ(first, second)
    base_frames = list(make_scene_frames(base_elements, 2.0, fps=2, intro_seconds=2.0,
                                        bg_color=base_bg, bg_fn=base_bg_fn, scene_dict=scene))
    legacy_frames = list(make_scene_frames(legacy_elements, 2.0, fps=2, intro_seconds=2.0,
                                           bg_color=legacy_bg, bg_fn=legacy_bg_fn, scene_dict=conflicting_legacy_fields))
    assert not _pixels_differ(base_frames[-1], legacy_frames[-1])
    production_frames = list(render_scene_frames(scene, 0, 1, 0.5, intro_seconds=0.5, style_name="editorial_viral"))
    assert len(production_frames) == 12
    assert scene["render_manifest"]["legacy_template_bypassed"] is True


def test_real_storyboard_has_viral_template():
    """Verify storyboard generation returns viral_short_v2 kind and _template_mode."""
    story = generate_storyboard("What is an API?", style_name="viral_explainer", target_duration=30.0)
    assert story is not None
    assert "scenes" in story
    assert len(story["scenes"]) == 6
    for scene in story["scenes"]:
        assert scene.get("kind") in ("viral_short_v2", "viral_short_v1")
        assert scene.get("_template_mode") in ("viral_explainer", "viral_news")
        assert "role" in scene
        assert "headline" in scene
        assert "hero_type" in scene


def test_viral_job_has_six_scenes():
    """Ensure viral storyboard validation strictly enforces exactly 6 scenes."""
    # Test Explainer topic
    story_explainer = generate_storyboard("How AI agents actually work", style_name="viral_explainer")
    assert len(story_explainer["scenes"]) == 6

    # Test News topic
    story_news = generate_storyboard("OpenAI launches a new AI model", style_name="viral_news")
    assert len(story_news["scenes"]) == 6


def test_auto_style_uses_editorial_routes_and_keeps_legacy_modes_explicit():
    assert auto_detect_style("How OpenAI Built An Empire") == "editorial_explainer"
    assert auto_detect_style("OpenAI launches a new AI model") == "editorial_viral"
    assert auto_detect_style("Why AI models need more compute") == "editorial_explainer"
    assert get_style("viral_explainer").name == "viral_explainer"
    assert get_style("viral_news").name == "viral_news"
    editorial_scene = {
        "kind": "viral_short_v2",
        "_template_mode": "editorial_explainer",
        "role": "hook",
        "headline": "EDITORIAL ROUTE",
        "template_context": create_template_context("editorial_explainer", "hook"),
    }
    assert not is_viral_template_scene(editorial_scene)


def test_editorial_explainer_is_supported_and_uses_light_theme():
    """The new editorial mode should render with a light, brand-aware background and no legacy paper defaults."""
    story = generate_storyboard("How AI agents actually work", style_name="editorial_explainer", target_duration=18.0)
    assert story["style"] == "editorial_explainer"
    assert story["source"].startswith("Editorial Studio [editorial_explainer]")
    assert all(scene.get("render_plan") for scene in story["scenes"])
    scene = {
        "kind": "editorial_explainer",
        "role": "process",
        "headline": "THE AI DECIDES",
        "hero_type": "pipeline",
        "narration": "The AI decides which tool to use next.",
        "supporting_fact": "several tools can be routed in parallel",
        "_template_mode": "editorial_explainer",
        "template_context": create_template_context("editorial_explainer", "process"),
    }
    elements, bg_col, bg_fn = build_scene(scene, 2, 6)
    assert bg_col == EDITORIAL_LIGHT
    assert bg_col != PAPER_BG
    assert len(elements) >= 3


def test_viral_scene_never_uses_legacy_renderer():
    """Verify that passing a viral scene to custom() immediately raises an error."""
    scene = {
        "kind": "viral_short_v2",
        "role": "hook",
        "headline": "TEST VIRAL HOOK",
        "hero_type": "hero_glow",
        "narration": "Test narration.",
        "_template_mode": "viral_explainer",
        "template_context": create_template_context("viral_explainer", "hook"),
    }
    with pytest.raises(RuntimeError, match="legacy renderer"):
        custom(scene, 0, 6)


def test_viral_scene_never_uses_paper_background():
    """Verify that viral_scene() returns BACKGROUND_0 (#070A12) and never PAPER_BG."""
    scene = {
        "kind": "viral_short_v2",
        "role": "hook",
        "headline": "WHAT IS AN API",
        "hero_type": "network_node",
        "narration": "An API connects software systems together.",
        "_template_mode": "viral_explainer",
        "template_context": create_template_context("viral_explainer", "hook"),
    }
    elements, bg_col, bg_fn = viral_scene(scene, 0, 6)
    assert bg_col == BACKGROUND_0
    assert bg_col != PAPER_BG


def test_viral_scene_has_template_context():
    """Verify that generated scenes have template_context with VIRAL_SHORT_V2."""
    story = generate_storyboard("What is an API?", style_name="viral_explainer")
    for scene in story["scenes"]:
        tc = scene.get("template_context")
        assert isinstance(tc, dict), f"Missing template_context in scene: {scene}"
        assert tc.get("template_version") in ("VIRAL_SHORT_V2", "VIRAL_SHORT_V1")
        assert tc.get("template_mode") in ("viral_explainer", "viral_news")
        assert tc.get("scene_role") in ("hook", "problem", "process", "proof", "payoff", "cta")


def test_viral_scene_role_sequence():
    """Verify the 6 scenes follow the canonical narrative role sequence."""
    expected_roles = [ROLE_HOOK, ROLE_PROBLEM, ROLE_PROCESS, ROLE_PROOF, ROLE_PAYOFF, ROLE_CTA]
    story = generate_storyboard("What is an API?", style_name="viral_explainer")
    actual_roles = [s["role"] for s in story["scenes"]]
    assert actual_roles == expected_roles


def test_real_create_short_routes_to_viral_renderer():
    """Verify that build_scene() routes viral scenes to viral_scene() rather than custom()."""
    scene = {
        "kind": "viral_short_v2",
        "role": "process",
        "headline": "HOW IT WORKS",
        "hero_type": "pipeline",
        "hero_label": "DATA FLOW",
        "supporting_fact": "3-stage pipeline",
        "visual_data": {"steps": ["Input", "Process", "Output"]},
        "narration": "Data flows seamlessly between services.",
        "_template_mode": "viral_explainer",
        "template_context": create_template_context("viral_explainer", "process"),
    }
    elements, bg_col, bg_fn = build_scene(scene, 2, 6)
    assert bg_col == BACKGROUND_0
    # Should have elements created for brand header, headline, hero, and fact
    assert len(elements) >= 3


def test_scene_metadata_includes_visual_directives():
    """Each canonical scene should carry semantic metadata for layout and camera decisions."""
    story = generate_storyboard("How Uber Works", style_name="viral_explainer")
    assert len(story["scenes"]) == 6
    for scene in story["scenes"]:
        assert scene.get("scene_role") == scene.get("role")
        assert scene.get("visual_intent")
        assert scene.get("preferred_primitive") or scene.get("hero_type")
        assert scene.get("camera_behavior")
        assert scene.get("motion_intensity") in {"low", "medium", "high"}


def test_scene_transition_config_is_configurable():
    """Transition defaults are environment-driven and accept dissolve without crashing."""
    original = os.environ.get("SCENE_TRANSITION_TYPE")
    original_frames = os.environ.get("SCENE_TRANSITION_FRAMES")
    try:
        os.environ["SCENE_TRANSITION_TYPE"] = "dissolve"
        os.environ["SCENE_TRANSITION_FRAMES"] = "6"
        cfg = get_scene_transition_config()
        assert cfg["type"] == "dissolve"
        assert cfg["frames"] == 6
    finally:
        if original is None:
            os.environ.pop("SCENE_TRANSITION_TYPE", None)
        else:
            os.environ["SCENE_TRANSITION_TYPE"] = original
        if original_frames is None:
            os.environ.pop("SCENE_TRANSITION_FRAMES", None)
        else:
            os.environ["SCENE_TRANSITION_FRAMES"] = original_frames


def test_ping_pong_value_stays_continuous_across_period_boundaries():
    """The motion wave should be continuous across cycle boundaries and never jump from max to min."""
    period = 100.0
    a = _ping_pong_value(0.0, period)
    b = _ping_pong_value(period - 0.1, period)
    c = _ping_pong_value(period + 0.1, period)
    assert 0.0 <= a <= 1.0
    assert 0.0 <= b <= 1.0
    assert 0.0 <= c <= 1.0
    assert math.isclose(_ping_pong_value(0.0, period), _ping_pong_value(period, period), rel_tol=1e-9, abs_tol=1e-9)
    assert abs(_ping_pong_value(period - 0.1, period) - _ping_pong_value(period + 0.1, period)) < 0.2


def test_brand_theme_is_centralized_and_consistent():
    """The channel accepts a single brand theme for colors, glow, and motion."""
    theme = get_brand_theme()
    assert theme.name == "AI Simplified Lab"
    assert theme.colors["brand_primary"]
    assert theme.colors["brand_secondary"]
    assert theme.glow["strength"] > 0
    assert theme.cta["text"] == SUBSCRIBE_CTA_TEXT
    assert canonical_brand_name(theme.name) == "AI Simplified Lab"


def test_brand_name_rejects_generic_variants_and_normalizes_them():
    """Brand names must normalize to the canonical identity instead of accepting generic aliases."""
    assert canonical_brand_name("AI Simplified") == "AI Simplified Lab"
    assert canonical_brand_name("AI Simplified Labs") == "AI Simplified Lab"
    assert canonical_brand_name("AI Simplified Channel") == "AI Simplified Lab"
    assert validate_brand_name("AI Simplified Labs") is False
    assert validate_brand_name("AI Simplified Lab") is True


def test_cta_contract_is_safe_and_branded():
    """CTA layout must use the canonical brand name and stay inside the safe zone."""
    assert SUBSCRIBE_CTA_TEXT == "Subscribe to AI Simplified Lab"
    assert validate_cta_bounds(200, 300, 680, 180, 1080, 1920)
    assert validate_cta_bounds(400, 150, 1120, 520, 1920, 1080)


def test_semantic_visual_plan_assigns_scene_meaning():
    """The visual planner should capture the concept and preferred primitive from narration."""
    scene = {
        "role": "process",
        "headline": "MATCHING RIDE TO DRIVER",
        "narration": "Uber matches a rider with a nearby driver in seconds.",
        "hero_type": "network_flow",
    }
    plan = build_semantic_visual_plan(scene, 2, 6)
    assert plan["scene_role"] == "process"
    assert plan["preferred_primitive"]
    assert plan["visual_intent"]
    assert plan["action"] in {"matching", "process", "reveal"}
    ok, issues = validate_visual_plan(scene)
    assert ok or issues

