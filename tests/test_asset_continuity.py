"""Unit tests for stages/assets/continuity.py."""
import pytest
from stages.assets.asset_manifest import AssetItem
from stages.assets.continuity import AssetContinuityTracker


def test_track_and_link_references():
    tracker = AssetContinuityTracker()

    item1 = AssetItem(
        asset_id="ast_scene_01",
        scene_id="scene_01",
        purpose="Establish the industrial control room",
        environment="Industrial high-voltage control room with metallic panels",
        subject="Control switchboard",
    )
    item2 = AssetItem(
        asset_id="ast_scene_02",
        scene_id="scene_02",
        purpose="Show pipeline strain in the same control room",
        environment="Industrial high-voltage control room with metallic panels",
        subject="Overloaded conduits",
    )
    item3 = AssetItem(
        asset_id="ast_scene_03",
        scene_id="scene_03",
        purpose="Zoom into planetary network space",
        environment="Global planetary satellite data grid",
        subject="Planetary network",
    )

    art_direction = {
        "palette_discipline": {"primary": "#0A0D14", "accent_1": "#00FF88"},
    }

    assets = [item1, item2, item3]
    tracker.track_and_link_references(assets, art_direction)

    # Scene 2 shares the environment with Scene 1, so reference_assets must include ast_scene_01
    assert "ast_scene_01" in item2.reference_assets
    assert len(item1.reference_assets) == 0
    assert len(item3.reference_assets) == 0

    score = tracker.evaluate_continuity_score(assets, art_direction)
    assert score >= 90.0
