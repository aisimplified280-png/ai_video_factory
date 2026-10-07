"""Unit tests for asset providers, selectors, and deterministic caching."""
import pytest
from pathlib import Path
from PIL import Image

from stages.assets.asset_manifest import AssetItem
from stages.assets.providers import (
    AssetCache,
    NativeDiagramProvider,
    LocalLibraryProvider,
    MockAssetProvider,
)
from tools.selectors.image_selector import ImageProviderSelector
from tools.selectors.video_selector import VideoProviderSelector
from tools.selectors.diagram_selector import DiagramProviderSelector


def test_native_diagram_provider(tmp_path):
    provider = NativeDiagramProvider()
    assert provider.is_available()

    item = AssetItem(
        asset_id="ast_diag_01",
        scene_id="scene_02",
        purpose="Show request routing through neural crossbar",
        type="diagram",
        subject="Neural Routing Crossbar",
        subject_action="Distributing requests across cluster workers",
        diagram_spec={
            "subject": "Neural Routing Crossbar",
            "nodes": [
                {"id": "n1", "label": "Client Gateway", "type": "primary"},
                {"id": "n2", "label": "Compute Scheduler", "type": "metric"},
            ],
            "color_accent": "#00FF88",
            "background_color": "#0A0D14",
        },
    )

    res = provider.generate(item, tmp_path)
    assert res["success"] is True
    out_file = Path(res["file_path"])
    assert out_file.exists()
    assert out_file.stat().st_size > 1024

    with Image.open(out_file) as img:
        assert img.size == (1080, 1920)


def test_local_library_provider(tmp_path):
    provider = LocalLibraryProvider()
    assert provider.is_available()

    item = AssetItem(
        asset_id="ast_logo_01",
        scene_id="scene_05",
        purpose="Brand identification and subscriber callout",
        type="logo",
        subject="AI Simplified Lab Brand",
    )

    res = provider.generate(item, tmp_path)
    assert res["success"] is True
    out_file = Path(res["file_path"])
    assert out_file.exists()


def test_asset_cache_put_and_get(tmp_path):
    cache = AssetCache(cache_dir=tmp_path / "cache")
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    sample_file = source_dir / "sample.png"
    # Create valid sample image
    img = Image.new("RGB", (100, 100), color="#1E293B")
    img.save(sample_file)

    item = AssetItem(
        asset_id="ast_cached_01",
        scene_id="scene_01",
        purpose="Cache test item",
        type="image",
        prompt="A high-voltage transformer glowing under load",
        provider="dall_e",
        model="dall-e-3",
        subject="Transformer",
    )

    # Initially not in cache
    assert cache.get(item) is None

    # Put in cache
    saved = cache.put(item, sample_file)
    assert saved.exists()

    # Now in cache
    found = cache.get(item)
    assert found is not None
    assert found.exists()


def test_provider_selectors():
    img_sel = ImageProviderSelector()
    img_prov = img_sel.select_best_provider({}, budget_remaining=1.0)
    assert img_prov["name"] in ("dall_e", "gemini_imagen", "native_diagram")

    vid_sel = VideoProviderSelector()
    vid_mode = vid_sel.select_video_mode(scene_duration=5.0, motion_intent="assemble")
    assert vid_mode["name"] in ("remote_video", "image_native_motion")

    diag_sel = DiagramProviderSelector()
    diag_engine = diag_sel.select_diagram_engine("system_assembly")
    assert diag_engine["name"] == "native_diagram"
