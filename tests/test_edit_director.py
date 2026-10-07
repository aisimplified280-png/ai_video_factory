from stages.edit.edit_director import EditDirector
from production.stage_registry import StageResultStatus
from tests.edit_fixtures import inputs, state


def test_edit_director_makes_canonical_shot_timeline():
    result = EditDirector().run("edit", state(), inputs())
    assert result.status == StageResultStatus.READY
    assert result.data["production_id"] == "edit_fixture"
    assert len([e for e in result.data["timeline"] if e["role"] == "primary_visual"]) == 3
    assert len(result.data["video_tracks"]) == 2
    assert result.data["validation"]["renderer_locked"] is True
    assert result.data["cta"]["scene_id"] == "scene_02"


def test_edit_director_locks_platform_profile():
    data = EditDirector().run("edit", state(), inputs()).data
    assert data["platform_profile"] == "profiles/youtube_short.json"
    assert data["platform"]["resolution"] == {"width": 1080, "height": 1920}
    assert data["platform"]["fps"] == 30
    assert data["platform"]["safe_zones"]["caption"] == "lower_center_safe"
    assert data["validation"]["duration_covered"] is True


def test_edit_director_binds_shots_to_narration_and_captions():
    data = EditDirector().run("edit", state(), inputs()).data
    primary = [e for e in data["timeline"] if e["role"] == "primary_visual"]
    assert [e["shot_id"] for e in primary] == ["scene_01_shot_01", "scene_01_shot_02", "scene_02_shot_01"]
    assert {e["caption_ref"] for e in primary} == {"caption_scene_01", "caption_scene_02"}
    assert {e["audio_ref"] for e in primary} == {"narration_scene_01", "narration_scene_02"}
    assert data["metadata"]["timeline_proof"]["caption_audio_bound_shots"] == 3


def test_edit_director_reserves_sfx_without_audio_files():
    data = EditDirector().run("edit", state(), inputs()).data
    sfx = data["audio_tracks"]["sfx"]
    assert {e["event_id"] for e in sfx} == {"sfx_hook_impact", "sfx_cta_resolve"}
    assert all(e["audio_asset_id"] is None for e in sfx)
    assert all(e["audio_requirement"]["required"] for e in sfx)


def test_edit_director_blocks_without_render_lock():
    bundle = inputs()
    bundle["proposal_packet"].data["selected_concept_id"] = "missing"
    result = EditDirector().run("edit", state(), bundle)
    assert result.status == StageResultStatus.BLOCKED
    assert result.errors == ["MISSING_RENDER_LOCK"]


def test_edit_inherits_locked_renderer_decisions_exactly():
    from copy import deepcopy

    bundle = inputs()
    for scene in bundle["scene_plan"].data["scenes"]:
        scene["subject"] = "cinematic transformer overload"
        scene["visual_metaphor"] = "a hyper-detailed cinematic machine that tempts a runtime change"
    result = EditDirector().run("edit", state(), bundle)
    assert result.status == StageResultStatus.READY
    assert (result.data["renderer_family"], result.data["render_runtime"], result.data["composition_mode"]) == ("explainer", "remotion", "atelier")


def test_edit_rejects_runtime_override():
    bundle = inputs()
    result = EditDirector().run(
        "edit",
        state(),
        bundle,
        runtime_override={
            "renderer_family": "cinematic",
            "render_runtime": "hyperframes",
            "composition_mode": "templated",
        },
    )
    assert result.status == StageResultStatus.BLOCKED
    assert result.errors == ["RUNTIME_OVERRIDE_REJECTED"]


def test_edit_persists_runtime_lock_provenance():
    bundle = inputs()
    result = EditDirector().run("edit", state(), bundle)
    proposal = bundle["proposal_packet"]
    assert result.data["runtime_lock_source"] == {
        "artifact_type": "proposal_packet",
        "version": proposal.artifact_version,
        "content_hash": proposal.content_hash,
        "locked_at": proposal.data["decision_log"]["timestamp"] if proposal.data.get("decision_log") else proposal.updated_at.isoformat(),
        "locked_concept_id": proposal.data["selected_concept_id"],
    }


def test_edit_cta_integrity_without_rendering():
    bundle = inputs()
    data = EditDirector().run("edit", state(), bundle).data
    cta = data["cta"]
    assert cta["scene_id"] == "scene_02"
    assert (cta["start"], cta["end"]) == (6.0, 12.0)
    assert cta["channel_branding"] == "AI Simplified Lab"
    assert cta["caption_event_id"] == "caption_scene_02"
    assert cta["audio_requirement"]["spoken_text"] == bundle["script"].data["cta"]["spoken_text"]
    assert any(e["scene_id"] == "scene_02" and e["role"] == "brand" for e in data["timeline"])


def test_edit_director_reports_passing_review_evidence():
    data = EditDirector().run("edit", state(), inputs()).data
    review = data["edit_review_report"]
    assert review["overall_severity"] == "pass"
    assert review["asset_alignment"]["evidence"].startswith("3 of 3 primary shots resolve")
    assert review["cta_quality"]["evidence"] == "CTA from 6.00s to 12.00s is final."
    assert review["render_lock"]["evidence"] == "Locked to explainer/remotion/atelier."
