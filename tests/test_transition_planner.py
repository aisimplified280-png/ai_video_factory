from stages.edit.transition_planner import TransitionPlanner


def test_transition_planner_preserves_match_and_cta_finality():
    planner = TransitionPlanner()
    assert planner.plan({"subject": "circular gauge"}, {"subject": "gauge core"}, 1) == "match_cut"
    assert planner.plan({"subject": "engine"}, {"subject": "brand", "narrative_role": "cta"}, 2) == "fade"
    assert planner.validate("zoom_transition")
    assert not planner.validate("sparkle")


def test_transition_planner_ignores_stopword_matches():
    planner = TransitionPlanner()
    transition = planner.plan({"subject": "engine and system"}, {"subject": "vault and grid"}, 1)
    assert transition != "match_cut"


def test_transition_planner_selects_motion_wipe():
    planner = TransitionPlanner()
    assert planner.plan({"subject": "engine"}, {"subject": "vault", "motion_intent": "travel"}, 3) == "directional_wipe"


def test_transition_planner_avoids_immediate_repetition():
    planner = TransitionPlanner()
    assert planner.plan(None, {"subject": "cold open"}, 0) == "fade"
    assert planner.plan({"subject": "engine"}, {"subject": "vault"}, 1, "hard_cut") == "cross_dissolve"


def test_transition_planner_sequences_without_repeats():
    planner = TransitionPlanner()
    scenes = [
        {"scene_id": "scene_01", "subject": "cold open"},
        {"scene_id": "scene_02", "subject": "engine room"},
        {"scene_id": "scene_03", "subject": "vault interior"},
        {"scene_id": "scene_04", "subject": "assembly line", "motion_intent": "travel"},
    ]
    plan = planner.plan_sequence(scenes)
    assert list(plan) == ["scene_01", "scene_02", "scene_03", "scene_04"]
    assert all(plan[scene] != plan[previous] for scene, previous in zip(list(plan)[1:], list(plan)))
    assert set(plan.values()) <= {
        "hard_cut", "cross_dissolve", "motion_blur", "match_cut", "directional_wipe",
        "zoom_transition", "object_transition", "shape_morph", "light_flash", "fade",
    }
