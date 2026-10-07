from stages.edit.edit_director import EditDirector
from stages.edit.edit_validator import EditValidator
from tests.edit_fixtures import inputs, state


def test_validator_blocks_missing_assets_and_primary_gaps():
    bundle = inputs(); data = EditDirector().run("edit", state(), bundle).data
    data["timeline"][1]["asset_id"] = "does_not_exist"
    data["timeline"][1]["start"] = 4; data["timeline"][1]["duration"] = 2
    report = EditValidator().validate(data, bundle["scene_plan"].data, bundle["asset_manifest"].data, bundle["proposal_packet"].data)
    assert report["status"] == "rejected"
    assert {f["code"] for f in report["findings"]} >= {"INVALID_ASSET_REFERENCE", "TIMELINE_GAP"}


def test_validator_blocks_unresolved_primary_asset():
    bundle = inputs()
    data = EditDirector().run("edit", state(), bundle).data
    data["timeline"][0]["asset_id"] = None
    report = EditValidator().validate(data, bundle["scene_plan"].data, bundle["asset_manifest"].data, bundle["proposal_packet"].data)
    assert report["status"] == "rejected"
    assert "PRIMARY_ASSET_UNRESOLVED" in {f["code"] for f in report["findings"]}
    assert report["flags"]["all_assets_resolved"] is False


def test_validator_blocks_asset_used_outside_planned_scene():
    from copy import deepcopy

    bundle = inputs()
    data = EditDirector().run("edit", state(), bundle).data
    manifest = deepcopy(bundle["asset_manifest"].data)
    manifest["assets"][0]["scene_id"] = "scene_02"
    report = EditValidator().validate(data, bundle["scene_plan"].data, manifest, bundle["proposal_packet"].data)
    assert report["status"] == "rejected"
    assert "ASSET_SCENE_MISMATCH" in {f["code"] for f in report["findings"]}


def test_validator_blocks_missing_generated_file(tmp_path):
    from copy import deepcopy

    bundle = inputs()
    data = EditDirector().run("edit", state(), bundle).data
    manifest = deepcopy(bundle["asset_manifest"].data)
    manifest["assets"][0].update({"type": "image", "source": "generated", "diagram_spec": None, "file_path": "assets/missing.png"})
    report = EditValidator().validate(data, bundle["scene_plan"].data, manifest, bundle["proposal_packet"].data, projects_root=tmp_path, production_id="edit_fixture")
    assert report["status"] == "rejected"
    assert "MISSING_ASSET_FILE" in {f["code"] for f in report["findings"]}


def test_validator_blocks_trailing_informational_after_cta():
    bundle = inputs()
    data = EditDirector().run("edit", state(), bundle).data
    data["timeline"][0]["start"] = 7.0
    report = EditValidator().validate(data, bundle["scene_plan"].data, bundle["asset_manifest"].data, bundle["proposal_packet"].data)
    assert "CTA_NOT_FINAL" in {f["code"] for f in report["findings"]}


def test_validator_blocks_renderer_lock_mismatch():
    bundle = inputs()
    data = EditDirector().run("edit", state(), bundle).data
    data["render_runtime"] = "ffmpeg_pil"
    report = EditValidator().validate(data, bundle["scene_plan"].data, bundle["asset_manifest"].data, bundle["proposal_packet"].data)
    assert report["status"] == "rejected"
    assert "RENDERER_MISMATCH" in {f["code"] for f in report["findings"]}
    assert report["flags"]["renderer_locked"] is False


def test_validator_rejects_invalid_layer_and_transition():
    bundle = inputs()
    data = EditDirector().run("edit", state(), bundle).data
    data["timeline"][0]["role"] = "hero_card"
    data["timeline"][0]["transition_in"] = "sparkle_wipe"
    report = EditValidator().validate(data, bundle["scene_plan"].data, bundle["asset_manifest"].data, bundle["proposal_packet"].data)
    assert {"INVALID_LAYER", "INVALID_TRANSITION"} <= {f["code"] for f in report["findings"]}


def test_validator_rejects_platform_duration_violation():
    bundle = inputs()
    data = EditDirector().run("edit", state(), bundle).data
    data["total_duration"] = 120.0
    report = EditValidator().validate(data, bundle["scene_plan"].data, bundle["asset_manifest"].data, bundle["proposal_packet"].data)
    assert "PLATFORM_DURATION_INVALID" in {f["code"] for f in report["findings"]}
    assert report["flags"]["duration_covered"] is False


def test_validator_warns_on_missing_continuity_links():
    from copy import deepcopy

    bundle = inputs()
    plan = deepcopy(bundle["scene_plan"].data)
    plan["scenes"][0].pop("continuity_to_next", None)
    plan["scenes"][1].pop("continuity_from_previous", None)
    data = EditDirector().run("edit", state(), bundle).data
    report = EditValidator().validate(data, plan, bundle["asset_manifest"].data, bundle["proposal_packet"].data)
    assert report["status"] == "warning"
    assert sum(1 for f in report["findings"] if f["code"] == "CONTINUITY_LINK_MISSING") == 2


def test_validator_warns_on_low_change_for_high_density():
    from copy import deepcopy

    bundle = inputs()
    plan = deepcopy(bundle["scene_plan"].data)
    plan["scenes"][1]["text_density"] = "high"
    data = EditDirector().run("edit", state(), bundle).data
    report = EditValidator().validate(data, plan, bundle["asset_manifest"].data, bundle["proposal_packet"].data)
    assert "LOW_VISUAL_CHANGE_FOR_INTENSITY" in {f["code"] for f in report["findings"]}


def test_asset_paths_resolve_from_project_root_not_cwd(tmp_path, monkeypatch):
    from stages.edit.timeline import resolve_asset_path

    asset_dir = tmp_path / "projects" / "proj_paths" / "assets"
    asset_dir.mkdir(parents=True)
    target = asset_dir / "frame.png"
    target.write_bytes(b"png")
    relative = {"file_path": "projects/proj_paths/assets/frame.png"}
    bare = {"file_path": "assets/frame.png"}
    other = tmp_path / "elsewhere"
    other.mkdir()
    monkeypatch.chdir(other)
    assert resolve_asset_path("proj_paths", relative, tmp_path / "projects") == target
    assert resolve_asset_path("proj_paths", bare, tmp_path / "projects") == target
    assert resolve_asset_path("proj_paths", {"file_path": str(target)}, tmp_path / "projects") == target
    assert resolve_asset_path("proj_paths", {"file_path": "https://example.org/frame.png"}) is None
    assert resolve_asset_path("proj_paths", {}) is None


def test_validator_detects_unknown_shot_reference():
    bundle = inputs()
    data = EditDirector().run("edit", state(), bundle).data
    data["timeline"][0]["shot_id"] = "scene_01_shot_99"
    report = EditValidator().validate(data, bundle["scene_plan"].data, bundle["asset_manifest"].data, bundle["proposal_packet"].data)
    assert report["status"] == "rejected"
    assert "INVALID_SHOT_REFERENCE" in {f["code"] for f in report["findings"]}


def test_validator_checks_cta_against_script_section():
    from copy import deepcopy

    bundle = inputs()
    script = deepcopy(bundle["script"].data)
    script["cta"]["section_id"] = "s2"
    data = EditDirector().run("edit", state(), bundle).data
    data["caption_track"][1]["caption_text_reference"] = "s1"
    report = EditValidator().validate(
        data, bundle["scene_plan"].data, bundle["asset_manifest"].data, bundle["proposal_packet"].data, script=script
    )
    assert report["status"] == "rejected"
    assert "CTA_SCRIPT_MISMATCH" in {f["code"] for f in report["findings"]}


def test_validator_checks_cta_audio_against_script_text():
    bundle = inputs()
    data = EditDirector().run("edit", state(), bundle).data
    data["cta"]["audio_requirement"]["spoken_text"] = "A different closing line."
    report = EditValidator().validate(
        data, bundle["scene_plan"].data, bundle["asset_manifest"].data, bundle["proposal_packet"].data, script=bundle["script"].data
    )
    assert report["status"] == "rejected"
    assert "CTA_AUDIO_MISMATCH" in {f["code"] for f in report["findings"]}


def test_validator_checks_fallback_asset_resolution(tmp_path):
    from copy import deepcopy

    bundle = inputs()
    manifest = deepcopy(bundle["asset_manifest"].data)
    manifest["assets"][0].update({
        "type": "image",
        "source": "generated",
        "provider": "native_diagram",
        "fallback_used": "native_diagram_schematic",
        "diagram_spec": None,
        "file_path": "projects/edit_fixture/assets/fallback.png",
    })
    target = tmp_path / "projects" / "edit_fixture" / "assets" / "fallback.png"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"png")
    data = EditDirector().run("edit", state(), bundle).data
    report = EditValidator().validate(
        data, bundle["scene_plan"].data, manifest, bundle["proposal_packet"].data,
        projects_root=tmp_path / "projects", production_id="edit_fixture",
    )
    assert report["status"] == "pass"


def test_validator_checks_persisted_parent_lineage():
    from types import SimpleNamespace

    bundle = inputs()
    parents = [
        SimpleNamespace(artifact_type=kind, version=env.artifact_version, content_hash=env.content_hash)
        for kind, env in bundle.items()
    ]
    edit = SimpleNamespace(parent_artifacts=parents)
    assert EditValidator.validate_artifact_lineage(edit, bundle)["status"] == "pass"

    stale = [
        SimpleNamespace(artifact_type=kind, version=env.artifact_version, content_hash=env.content_hash)
        for kind, env in bundle.items()
    ]
    stale[1] = SimpleNamespace(artifact_type="proposal_packet", version=99, content_hash=bundle["proposal_packet"].content_hash)
    report = EditValidator.validate_artifact_lineage(SimpleNamespace(parent_artifacts=stale), bundle)
    assert report["status"] == "rejected"
    assert "LINEAGE_VERSION_MISMATCH" in {f["code"] for f in report["findings"]}


def test_validator_warns_on_unused_primary_and_template_language():
    from copy import deepcopy

    bundle = inputs()
    data = EditDirector().run("edit", state(), bundle).data
    manifest = deepcopy(bundle["asset_manifest"].data)
    manifest["assets"].append({
        "asset_id": "unused_primary",
        "scene_id": "scene_01",
        "purpose": "Show an alternate HeroCard",
        "visual_role": "primary",
        "type": "image",
        "source": "generated",
        "status": "ready",
        "file_path": "assets/unused.png",
    })
    report = EditValidator().validate(data, bundle["scene_plan"].data, manifest, bundle["proposal_packet"].data)
    assert report["status"] == "warning"
    assert {"UNUSED_PRIMARY_ASSET", "TEMPLATE_VOCABULARY"} <= {f["code"] for f in report["findings"]}
