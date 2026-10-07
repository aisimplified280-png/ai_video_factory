"""Unit tests for stages/assets/asset_validator.py."""
import pytest
from pathlib import Path
from PIL import Image

from stages.assets.asset_manifest import AssetItem
from stages.assets.asset_validator import AssetValidator


@pytest.fixture
def validator():
    return AssetValidator(min_width=720, min_height=1280)


@pytest.fixture
def sample_art_direction():
    return {
        "visual_metaphor": "industrial power grid under load",
        "anti_patterns": ["no floating cards"],
    }


def test_validate_technical_missing_file(validator):
    item = AssetItem(
        asset_id="ast_missing",
        scene_id="scene_01",
        purpose="Test missing file",
        type="image",
        file_path="non_existent_file.png",
    )
    score, findings = validator.validate_technical(item)
    assert score == 0.0
    assert any("does not exist" in f for f in findings)


def test_validate_technical_solid_black_image(validator, tmp_path):
    img_path = tmp_path / "black.png"
    # Create solid black image
    img = Image.new("RGB", (1080, 1920), color="#000000")
    img.save(img_path)

    item = AssetItem(
        asset_id="ast_black",
        scene_id="scene_01",
        purpose="Solid black test",
        type="image",
        file_path=str(img_path),
    )
    score, findings = validator.validate_technical(item)
    assert score == 0.0
    assert any("solid black" in f for f in findings)


def test_validate_technical_valid_image(validator, tmp_path):
    img_path = tmp_path / "valid.png"
    # Create image with variation and content
    with Image.new("RGB", (1080, 1920), color="#1E293B") as img:
        from PIL import ImageDraw
        d = ImageDraw.Draw(img)
        d.rectangle([(100, 100), (900, 900)], fill="#38BDF8")
        d.line([(0, 0), (1080, 1920)], fill="#F59E0B", width=8)
        img.save(img_path)

    item = AssetItem(
        asset_id="ast_valid",
        scene_id="scene_01",
        purpose="Valid image test requirement for technical QA",
        type="image",
        file_path=str(img_path),
    )
    score, findings = validator.validate_technical(item)
    assert score == 100.0, f"Expected 100.0, got {score} with findings: {findings}"
    assert len(findings) == 0


def test_validate_semantic_anti_generic_trope_penalized(validator, sample_art_direction):
    item = AssetItem(
        asset_id="ast_trope",
        scene_id="scene_01",
        purpose="Show futuristic AI network",
        subject="Neural transformer",
        prompt="A futuristic ai brain glowing with cyberpunk neon in abstract space",
    )
    score, findings = validator.validate_semantic(item, sample_art_direction)
    assert score < 70.0
    assert any("generic trope" in f for f in findings)


def test_validate_semantic_subject_alignment(validator, sample_art_direction):
    item = AssetItem(
        asset_id="ast_aligned",
        scene_id="scene_01",
        purpose="Establish physical compute strain on electrical transformers",
        subject="Industrial power transformer",
        subject_action="Coils glowing red from electrical overload",
        prompt="An industrial power transformer with copper coils glowing red under intense operational load",
    )
    score, findings = validator.validate_semantic(item, sample_art_direction)
    assert score >= 85.0
    assert len(findings) == 0


def test_review_asset_generates_correct_status(validator, tmp_path, sample_art_direction):
    img_path = tmp_path / "good.png"
    img = Image.new("RGB", (1080, 1920), color="#0F172A")
    from PIL import ImageDraw
    d = ImageDraw.Draw(img)
    d.line([(0, 0), (1080, 1920)], fill="#00FF88", width=10)
    img.save(img_path)

    item = AssetItem(
        asset_id="ast_good",
        scene_id="scene_01",
        purpose="Show heavy power conduit lines surging with energy",
        subject="Power conduits",
        subject_action="Surging electrical current",
        prompt="Power conduits surging with electrical energy in high-contrast industrial facility",
        file_path=str(img_path),
    )
    rev = validator.review_asset(item, sample_art_direction)
    assert rev["status"] in ("pass", "warning")
    assert item.status == "ready"
