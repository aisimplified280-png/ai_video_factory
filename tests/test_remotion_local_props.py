"""Local props tests: platform values come from the profile, paths stay local."""
import json
from pathlib import Path

from composition.remotion.props_builder import build_production_props
from test_remotion_props import PROFILE, _artifacts, _write_asset

ROOT = Path(__file__).resolve().parent.parent


def test_platform_values_match_profile_file(tmp_path):
    _write_asset(tmp_path)
    edit, scenes, manifest, art, script = _artifacts()
    profile = json.loads((ROOT / "profiles" / "youtube_short.json").read_text(encoding="utf-8"))
    props, _ = build_production_props(
        edit_data=edit, scene_plan_data=scenes, manifest_data=manifest,
        art_direction_data=art, script_data=script, platform_profile=profile,
        projects_root=tmp_path / "projects", public_dir=tmp_path / "public")
    assert props["platform"]["resolution"] == {"width": 1080, "height": 1920}
    assert props["platform"]["fps"] == 30


def test_no_remote_paths_in_props(tmp_path):
    _write_asset(tmp_path)
    edit, scenes, manifest, art, script = _artifacts()
    props, _ = build_production_props(
        edit_data=edit, scene_plan_data=scenes, manifest_data=manifest,
        art_direction_data=art, script_data=script, platform_profile=PROFILE,
        projects_root=tmp_path / "projects", public_dir=tmp_path / "public")
    blob = json.dumps(props)
    assert "drive" not in blob.lower()
    assert "colab" not in blob.lower()
    assert "http://" not in blob and "https://" not in blob
    for asset in props["assets"]:
        if asset["publicPath"]:
            assert "\\" not in asset["publicPath"]
            assert "/" not in asset["publicPath"], "public paths must be flat filenames (staticFile encoding)"


def test_output_path_convention():
    from composition.remotion.renderer import package_remote_bundle  # noqa: F401 (import surface)
    from composition.composition_job import build_output_path
    assert build_output_path("/tmp/projects", "proj_x", "remotion", 1) == \
        "/tmp/projects/proj_x/composition/remotion_edit-v001.mp4"
