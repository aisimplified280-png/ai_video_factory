from pathlib import Path
from production.stage_registry import create_default_registry
from stages.edit.edit_director import EditDirector
from tests.edit_fixtures import inputs, state


def test_edit_is_registered_and_writes_human_reports(tmp_path):
    assert create_default_registry().has("edit")
    result = EditDirector().run("edit", state(), inputs())
    EditDirector.write_human_reports(tmp_path, result.data)
    assert (tmp_path / "edit_summary.md").exists()
    assert (tmp_path / "edit_generation_report.json").exists()


def test_controller_executes_edit_and_preserves_parent_lineage(tmp_path):
    from production.artifact_store import ArtifactStore
    from production.controller import ProductionController
    from production.stage_registry import StageResultStatus
    from schemas.models.artifact import ProducerInfo
    from schemas.models.common import ProducerKind

    controller = ProductionController(projects_root=tmp_path, registry=create_default_registry())
    started = controller.start(topic="Deterministic edit fixture", pipeline="youtube-short", options={"run_mode": "auto", "target_duration": 12.0})
    bundle = inputs(started.project_id)
    store = ArtifactStore(tmp_path)
    stages = {
        "research_brief": "research",
        "proposal_packet": "proposal",
        "script": "script",
        "art_direction": "art_direction",
        "scene_plan": "scene_plan",
        "asset_manifest": "assets",
    }
    for artifact_type, stage in stages.items():
        envelope = store.create(
            artifact_type,
            started.project_id,
            stage,
            bundle[artifact_type].data,
            ProducerInfo(kind=ProducerKind.SYSTEM),
        )
        store.save(envelope)
        store.approve(artifact_type, started.project_id, envelope.artifact_version)
        state = controller.state_store.load(started.project_id)
        state.set_active_version(artifact_type, envelope.artifact_version)
        state.current_stage = "edit"
        controller.state_store.save(state)

    result = controller.run_stage(started.project_id, "edit")
    assert result.status == StageResultStatus.READY
    artifact = controller.artifact_store.latest("edit_decisions", started.project_id)
    assert artifact.data["production_id"] == started.project_id
    assert {parent.artifact_type for parent in artifact.parent_artifacts} >= set(stages)
    assert (tmp_path / started.project_id / "edit" / "edit_summary.md").read_text(encoding="utf-8").startswith("# Edit Summary\n\nTotal duration: 12.00s")


def test_edit_reports_asset_utilization_and_timeline_proof(tmp_path):
    import json

    result = EditDirector().run("edit", state(), inputs())
    EditDirector.write_human_reports(tmp_path, result.data)
    generation = json.loads((tmp_path / "edit_generation_report.json").read_text(encoding="utf-8"))
    assert generation["asset_utilization"]["used_assets"] == ["a1", "a2"]
    assert generation["asset_utilization"]["unused_assets"] == []
    assert generation["timeline_proof"]["resolved_primary_shots"] == 3
    assert generation["timeline_proof"]["manifest_scene_matches"] == 3


def test_explicit_proposal_revision_changes_locked_runtime(tmp_path):
    from copy import deepcopy
    from production.controller import ProductionController
    from production.dependencies import find_stale_artifacts, invalidate_downstream
    from production.stage_registry import StageResultStatus
    from schemas.models.artifact import ProducerInfo
    from schemas.models.common import ProducerKind

    controller = ProductionController(projects_root=tmp_path, registry=create_default_registry())
    started = controller.start(topic="Runtime revision fixture", pipeline="youtube-short", options={"run_mode": "auto", "target_duration": 12.0})
    bundle = inputs(started.project_id)
    store = controller.artifact_store
    stages = {
        "research_brief": "research",
        "proposal_packet": "proposal",
        "script": "script",
        "art_direction": "art_direction",
        "scene_plan": "scene_plan",
        "asset_manifest": "assets",
    }
    for artifact_type, stage in stages.items():
        envelope = store.create(artifact_type, started.project_id, stage, bundle[artifact_type].data, ProducerInfo(kind=ProducerKind.SYSTEM))
        store.save(envelope)
        store.approve(artifact_type, started.project_id, envelope.artifact_version)
        state = controller.state_store.load(started.project_id)
        state.set_active_version(artifact_type, envelope.artifact_version)
        state.current_stage = "edit"
        controller.state_store.save(state)
    first = controller.run_stage(started.project_id, "edit")
    assert first.status == StageResultStatus.READY
    assert controller.artifact_store.latest("edit_decisions", started.project_id).data["renderer_family"] == "explainer"

    revised = deepcopy(bundle["proposal_packet"].data)
    revised["concepts"].append({
        "concept_id": "c3",
        "hook": "A revised deterministic hook",
        "audience_promise": "A revised deterministic promise.",
        "narrative_structure": "Hook then CTA",
        "visual_direction": "Revised deterministic direction",
        "tone": "Direct",
        "target_duration": 12.0,
        "renderer_family": "documentary",
        "render_runtime": "hyperframes",
        "composition_mode": "templated",
    })
    revised["selected_concept_id"] = "c3"
    proposal_v2 = store.create("proposal_packet", started.project_id, "proposal", revised, ProducerInfo(kind=ProducerKind.SYSTEM))
    store.save(proposal_v2)
    store.approve("proposal_packet", started.project_id, proposal_v2.artifact_version)
    state = controller.state_store.load(started.project_id)
    state.set_active_version("proposal_packet", proposal_v2.artifact_version)
    controller.state_store.save(state)
    assert "edit_decisions" in find_stale_artifacts(state, controller.artifact_store)
    definition = controller._get_pipeline("youtube-short")
    assert "edit_decisions" in invalidate_downstream("proposal_packet", definition, state, controller.artifact_store)
    controller.state_store.save(state)

    second = controller.run_stage(started.project_id, "edit")
    assert second.status == StageResultStatus.READY
    latest = controller.artifact_store.latest("edit_decisions", started.project_id)
    assert latest.artifact_version == 2
    assert (latest.data["renderer_family"], latest.data["render_runtime"], latest.data["composition_mode"]) == ("documentary", "hyperframes", "templated")
    assert latest.data["runtime_lock_source"]["locked_concept_id"] == "c3"


def test_edit_layer_contains_no_renderer_implementation():
    from pathlib import Path as FilesystemPath

    banned = ("from PIL", "ImageDraw", "Image.new", "React", "useState", "className", "<div", "StyleSheet")
    edit_dir = FilesystemPath(__file__).resolve().parent.parent / "stages" / "edit"
    sources = [path for path in sorted(edit_dir.glob("*.py")) if path.name != "__init__.py"]
    assert sources
    for path in sources:
        text = path.read_text(encoding="utf-8")
        assert all(token not in text for token in banned), path.name


def test_edit_summary_describes_scenes_not_only_shots(tmp_path):
    result = EditDirector().run("edit", state(), inputs())
    EditDirector.write_human_reports(tmp_path, result.data)
    summary = (tmp_path / "edit_summary.md").read_text(encoding="utf-8")
    assert "## 0.0–6.0s · scene_01" in summary
    assert "Primary asset a1: establish becomes reveal." in summary
    assert "Caption s1 from 0.0–6.0s; emphasis: big, shift." in summary
    assert "## 6.0–12.0s · scene_02" in summary
    assert "Narration: Subscribe to AI Simplified Lab" in summary
