"""Motion ownership + chrome wiring tests (§5, §7).

The ownership decision lives in remotion-composer/src/runtime/motionOwnership.ts —
compiled here with tsc and driven in node (the same real module SceneComposition
executes at render time), so the test proves behavior rather than grepping JSX:

1. The mascot (character) always owns its motion — the wrapper adds no
   camera/motion styles on top.
2. A native diagram (nativeSpec.nodes) owns its own reveal.
3. Baked image assets with no node spec receive no forced self-motion (their
   canonical camera/motion intent still applies through the wrapper).

Wiring guards pin the surrounding decisions: no parallax import in
SceneComposition, MilestoneTabs faded out over the CTA, the duplicate brand
emblem gone from the CTA midground PNG, and DiagramLayer's semantic renderer
(distinct shapes / relationships / glyphs) present.
"""
import subprocess
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
TS_SRC = ROOT / "remotion-composer" / "src" / "runtime" / "motionOwnership.ts"
TSC = ROOT / "remotion-composer" / "node_modules" / "typescript" / "bin" / "tsc"

HARNESS = r"""
const {ownsOwnMotion} = require(process.argv[2]);

const failures = [];
let checks = 0;
const check = (name, ok, detail) => {
  checks += 1;
  if (!ok) failures.push(name + (detail ? ': ' + detail : ''));
};

// 1. Mascot owns all of its motion.
check('character owns own motion', ownsOwnMotion('character', {nativeSpec: {}}) === true);
check('character owns motion even without asset', ownsOwnMotion('character', null) === true);

// 2. Native diagram owns its reveal.
const diagram = {nativeSpec: {nodes: [{id: 'n1'}], connectors: [{from: 'n1', to: 'n1'}]}};
check('diagram midground owns own motion', ownsOwnMotion('midground', diagram) === true);
check('diagram owns motion regardless of role label', ownsOwnMotion('primary_visual', diagram) === true);

// 3. Baked assets do not claim self-motion (wrapper applies canonical intent).
const bakedCard = {nativeSpec: {bars: [{label: 'a', value: 1}]}};
check('baked card does not own motion', ownsOwnMotion('midground', bakedCard) === false);
check('asset without nativeSpec does not own motion', ownsOwnMotion('foreground', {kind: 'image-still'}) === false);
check('missing asset does not own motion', ownsOwnMotion('foreground', null) === false);
check('empty node array does not own motion', ownsOwnMotion('midground', {nativeSpec: {nodes: []}}) === false);

if (failures.length > 0) {
  console.error('FAILED ' + failures.length + '/' + checks);
  failures.forEach((f) => console.error('  - ' + f));
  process.exit(1);
}
console.log('ALL MOTION-OWNERSHIP ASSERTIONS PASSED (' + checks + ')');
"""


def _compile_and_run(tmp: Path) -> subprocess.CompletedProcess:
    compiled_dir = tmp / "compiled"
    compiled_dir.mkdir(parents=True, exist_ok=True)
    compile_run = subprocess.run(
        [
            "node", str(TSC), str(TS_SRC),
            "--outDir", str(compiled_dir),
            "--module", "commonjs", "--target", "es2020",
            "--strict", "--skipLibCheck",
        ],
        cwd=str(ROOT / "remotion-composer"),
        capture_output=True, text=True, timeout=120,
    )
    assert compile_run.returncode == 0, f"tsc failed:\n{compile_run.stdout}\n{compile_run.stderr}"
    compiled = next(compiled_dir.rglob("motionOwnership.js"), None)
    assert compiled is not None, f"compiled module not found under {compiled_dir}"
    harness = tmp / "harness.js"
    harness.write_text(HARNESS, encoding="utf-8")
    return subprocess.run(
        ["node", str(harness), str(compiled)],
        capture_output=True, text=True, timeout=60,
    )


@pytest.mark.skipif(not TSC.exists(), reason="typescript devDependency not installed")
def test_motion_ownership_decision_behavior():
    """The real ownership module: character + diagram self-own, baked assets don't."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = _compile_and_run(Path(tmpdir))
    assert result.returncode == 0, f"ownership assertions failed:\n{result.stdout}\n{result.stderr}"
    assert "ALL MOTION-OWNERSHIP ASSERTIONS PASSED" in result.stdout


def test_scene_composition_wires_single_motion_owner():
    """SceneComposition must use the tested decision and never parallax drift."""
    sc = (ROOT / "remotion-composer/src/compositions/SceneComposition.tsx").read_text("utf-8")
    assert "from '../runtime/motionOwnership'" in sc, "composition must import the ownership module"
    assert "ownsOwnMotion(event.role" in sc, "ownership must gate camera/motion styling per event"
    assert "parallax" not in sc, "default parallax drift must be removed from the composition"
    # Camera/motion styles are gated by the ownership decision, not applied blind.
    assert "selfOwned ? undefined : cameraStyle(" in sc
    assert "selfOwned ? undefined : motionStyle(" in sc


def test_milestone_tabs_fade_out_over_the_cta():
    """The chapter bar must not persist as an active tab over the CTA ending."""
    pc = (ROOT / "remotion-composer/src/compositions/ProductionComposition.tsx").read_text("utf-8")
    assert "ctaStartFrame" in pc, "tabs must know when the CTA begins"
    assert "tabsOpacity" in pc, "tabs must fade rather than pop"
    assert "style={{opacity: tabsOpacity}}" in pc, "opacity must actually be applied to MilestoneTabs"
    # Captions already clear at ctaStart (regression pin).
    ct = (ROOT / "remotion-composer/src/captions/CaptionTrack.tsx").read_text("utf-8")
    assert "ctaStart" in ct


def test_cta_brand_duplicate_emblem_removed():
    """The baked robot-face emblem duplicated the TSX CTA wordmark — gone."""
    ml = (ROOT / "production/phase17/multi_layer_generator.py").read_text("utf-8")
    assert "cy_logo" not in ml, "duplicate brand emblem drawing must be removed"
    assert "Robot Silhouette Emblem" not in ml
    # The narration-driven brand line stays available.
    assert "if node.details:" in ml


def test_diagram_layer_renders_semantic_shapes_relationships_and_glyphs():
    """DiagramLayer must draw the semantics, not generic rounded rects."""
    dl = (ROOT / "remotion-composer/src/primitives/DiagramLayer.tsx").read_text("utf-8")
    # Distinct node shapes.
    for shape in ("cylindrical_storage", "transform_kernel", "stack_layer", "matrix_grid"):
        assert shape in dl, f"missing semantic shape: {shape}"
    # Relationship-aware connectors.
    assert "contrasts_with" in dl, "comparison must render a two-sided connector"
    assert "transforms_to" in dl, "transformation must be marked on the connector"
    assert "orient=\"auto-start-reverse\"" in dl or "orient='auto-start-reverse'" in dl
    # Concrete subject glyphs.
    assert "DIAGRAM_GLYPH_IDS" in dl
    for glyph in ("satellite", "phone", "document", "database", "cache", "arm"):
        assert glyph in dl, f"missing glyph: {glyph}"
