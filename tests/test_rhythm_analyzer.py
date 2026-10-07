from stages.edit.edit_director import EditDirector
from stages.edit.rhythm_analyzer import RhythmAnalyzer
from tests.edit_fixtures import inputs, state


def test_rhythm_reports_edit_diversity():
    data = EditDirector().run("edit", state(), inputs()).data
    rhythm = RhythmAnalyzer().analyze(data["timeline"], 12)
    assert rhythm["shot_count"] == 3
    assert rhythm["average_shot_duration"] == 4.0
    assert rhythm["framing_diversity"] >= 1


def test_rhythm_reports_cut_intervals_and_scene_changes():
    data = EditDirector().run("edit", state(), inputs()).data
    rhythm = RhythmAnalyzer().analyze(data["timeline"], 12)
    assert rhythm["cut_intervals"] == [3.0, 3.0]
    assert rhythm["average_cut_interval"] == 3.0
    assert rhythm["visual_changes_per_scene"] == {"scene_01": 2, "scene_02": 1}
    assert rhythm["transition_counts"] == {"hard_cut": 1, "fade": 1}


def test_rhythm_warns_on_repeated_transition():
    rhythm = RhythmAnalyzer().analyze(
        [
            {"role": "primary_visual", "duration": 2.0, "start": 0.0, "transition_in": "hard_cut", "scene_id": "scene_01"},
            {"role": "primary_visual", "duration": 2.0, "start": 2.0, "transition_in": "hard_cut", "scene_id": "scene_01"},
            {"role": "primary_visual", "duration": 2.0, "start": 4.0, "transition_in": "hard_cut", "scene_id": "scene_02"},
        ],
        6.0,
    )
    assert "TRANSITION_REPETITION" in {f["code"] for f in RhythmAnalyzer().warnings(rhythm)}


def test_rhythm_warns_on_dominant_transition():
    rhythm = RhythmAnalyzer().analyze(
        [
            {"role": "primary_visual", "duration": 1.0, "start": 0.0, "transition_in": "fade", "scene_id": "scene_01"},
            {"role": "primary_visual", "duration": 1.0, "start": 1.0, "transition_in": "hard_cut", "scene_id": "scene_02"},
            {"role": "primary_visual", "duration": 1.0, "start": 2.0, "transition_in": "hard_cut", "scene_id": "scene_03"},
            {"role": "primary_visual", "duration": 1.0, "start": 3.0, "transition_in": "hard_cut", "scene_id": "scene_04"},
            {"role": "primary_visual", "duration": 1.0, "start": 4.0, "transition_in": "hard_cut", "scene_id": "scene_05"},
        ],
        5.0,
    )
    assert "TRANSITION_DOMINANCE" in {f["code"] for f in RhythmAnalyzer().warnings(rhythm)}


def test_rhythm_warns_on_long_static_interval():
    rhythm = RhythmAnalyzer().analyze(
        [{"role": "primary_visual", "duration": 7.0, "start": 0.0, "scene_id": "scene_01"}],
        7.0,
    )
    assert "LONG_STATIC_INTERVAL" in {f["code"] for f in RhythmAnalyzer().warnings(rhythm)}
