"""CTA single-lockup test (P1 duplicated branding).

SceneComposition must render exactly one logo/wordmark lockup (the large
wordmark reveal above the card) plus the mascot and one subscribe button.
The removed in-card logo row leaves a geometry-preserving spacer so the
subscribe control — and ctaSubscribeAnchor with it — does not move.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SC = ROOT / "remotion-composer" / "src" / "compositions" / "SceneComposition.tsx"


def test_cta_has_one_brand_lockup():
    text = SC.read_text(encoding="utf-8")
    assert "ctaWordmarkGrad" in text, "hero wordmark lockup must stay"
    assert "ctaLogoGrad" not in text, "in-card duplicate logo must be gone"


def test_subscribe_button_geometry_preserved():
    text = SC.read_text(encoding="utf-8")
    assert "SUBSCRIBE" in text, "subscribe button must stay"
    # 46px spacer replaces the 46px logo row: identical card height, identical
    # button position, anchor stays valid.
    assert "height: 46" in text
    assert "ctaSubscribeAnchor stays in sync" in text
    assert "height * 0.854" in text, "anchor math must be untouched"
