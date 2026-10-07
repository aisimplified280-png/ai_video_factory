"""Unit tests for stages/assets/asset_manifest.py and schema validation."""
import pytest
from pathlib import Path

from schemas.models.artifact import ArtifactEnvelope, ProducerInfo
from schemas.models.common import ArtifactStatus, ProducerKind
from production.artifact_store import ArtifactStore
from stages.assets.asset_manifest import AssetItem, AssetManifestPayload


def test_asset_item_to_schema_dict():
    item = AssetItem(
        asset_id="ast_01",
        scene_id="scene_01",
        purpose="Establish scale of compute load",
        type="image",
        source="generated",
        status="ready",
        cost_usd=0.04,
    )
    d = item.to_schema_dict()
    assert d["asset_id"] == "ast_01"
    assert d["status"] == "ready"
    assert isinstance(d["fallback_chain"], list)


def test_asset_manifest_payload_schema_validity(tmp_path):
    store = ArtifactStore(projects_root=tmp_path)
    pid = "proj_test_manifest_schema"
    producer = ProducerInfo(kind=ProducerKind.TOOL, provider="asset_director")

    item1 = AssetItem(
        asset_id="ast_01",
        scene_id="scene_01",
        purpose="Show industrial power substation overloading",
        type="image",
        source="generated",
        status="ready",
        cost_usd=0.04,
    )
    item2 = AssetItem(
        asset_id="ast_02",
        scene_id="scene_02",
        purpose="Visualize routing topology with native diagram",
        type="diagram",
        source="native",
        status="ready",
        cost_usd=0.0,
    )
    manifest = AssetManifestPayload(
        assets=[item1, item2],
        total_estimated_cost=0.04,
        actual_cost=0.04,
        medium_distribution={"image": 1, "diagram": 1},
        source_distribution={"generated": 1, "native": 1},
    )

    art = store.create(
        "asset_manifest",
        pid,
        "assets",
        manifest.to_schema_dict(),
        producer,
    )
    saved_path = store.save(art)
    assert saved_path.exists()

    loaded = store.load("asset_manifest", pid, 1)
    assert len(loaded.data["assets"]) == 2
    assert loaded.data["total_estimated_cost"] == 0.04
    assert loaded.content_hash.startswith("sha256:")
