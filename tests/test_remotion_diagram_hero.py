"""Focal hero rendering behavior (§3, P0 templating fix).

DiagramLayer is compiled here with tsc and rendered in node through
react-dom/server — the real component, real SVG markup — proving:

1. A focal single-subject node WITH a concrete icon renders as a subject
   hero (glyph medallion + label + spoken facts), never a generic card.
2. A focal node WITHOUT an icon keeps the card path (concepts that genuinely
   benefit from a card keep it).
3. Multi-node diagrams and brand/CTA single nodes never take the hero path.
"""
import json
import subprocess
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
TS_SRC = ROOT / "remotion-composer" / "src" / "primitives" / "DiagramLayer.tsx"
TSC = ROOT / "remotion-composer" / "node_modules" / "typescript" / "bin" / "tsc"

THEME = {
    "fontFamily": "Inter",
    "accent": "#2563EB",
    "accentSecondary": "#F59E0B",
    "surface": "#FFFFFF",
    "text": "#0F172A",
    "mutedText": "#64748B",
    "cornerRadius": 18,
    "lineWeight": 3,
}

HERO_NODE = {
    "id": "focal_hero", "label": "YOUR PHONE", "x": 540, "y": 705,
    "details": ["Displays the date", "Time clearly"],
    "primary": True, "w": 680, "h": 310,
    "node_type": "entity", "shape_style": "card", "icon": "phone",
}

HARNESS = r"""
const nm = process.env.COMPOSER_NODE_MODULES;
const {renderToStaticMarkup} = require(nm + '/react-dom/server');
const React = require(nm + '/react');
const {DiagramLayer} = require(process.argv[2]);
const theme = JSON.parse(process.argv[3]);
const cases = JSON.parse(process.argv[4]);

const failures = [];
let checks = 0;
const check = (name, ok, detail) => {
  checks += 1;
  if (!ok) failures.push(name + (detail ? ': ' + detail : ''));
};

const render = (props) =>
  renderToStaticMarkup(React.createElement(DiagramLayer, Object.assign({theme, width: 1080, height: 1920, reveal: 1}, props)));

// 1. Focal hero with a concrete icon: medallion + label + facts, no card box.
const hero = render({topology: 'focal', nodes: [Object.assign({}, JSON.parse(process.env.HERO_NODE))], connectors: []});
check('hero renders the focal marker', hero.includes('data-hero="focal"'), hero.slice(0, 200));
check('hero shows the subject label', hero.includes('YOUR PHONE'), 'label missing');
check('hero shows the spoken facts', hero.includes('Displays the date'), 'facts missing');
check('hero draws the glyph medallion', hero.includes('<circle'), 'no medallion circle');
check('hero uses no generic card shadow box', !hero.includes('url(#diagNodeShadow)'), 'card shadow present');

// 2. Focal node without an icon keeps the card path.
const noIconNode = Object.assign({}, JSON.parse(process.env.HERO_NODE), {icon: ''});
const card = render({topology: 'focal', nodes: [noIconNode], connectors: []});
check('icon-less focal stays a card', !card.includes('data-hero="focal"'), 'hero taken without icon');
check('icon-less focal still labels', card.includes('YOUR PHONE'), 'label missing');

// 3. Other topologies never take the hero path.
const flow = render({topology: 'process_flow', nodes: [
  Object.assign({}, JSON.parse(process.env.HERO_NODE), {id: 'a'}),
  Object.assign({}, JSON.parse(process.env.HERO_NODE), {id: 'b'}),
], connectors: []});
check('multi-node flow is not a hero', !flow.includes('data-hero="focal"'), 'hero taken for flow');
const brand = render({topology: 'brand', nodes: [Object.assign({}, JSON.parse(process.env.HERO_NODE))], connectors: []});
check('brand crest is never a hero', !brand.includes('data-hero="focal"'), 'hero taken for brand');
const noTopo = render({nodes: [Object.assign({}, JSON.parse(process.env.HERO_NODE))], connectors: []});
check('hero requires the focal topology', !noTopo.includes('data-hero="focal"'), 'hero without topology');

if (failures.length > 0) {
  console.error('FAILED ' + failures.length + '/' + checks);
  failures.forEach((f) => console.error('  - ' + f));
  process.exit(1);
}
console.log('ALL DIAGRAM-HERO ASSERTIONS PASSED (' + checks + ')');
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
            "--jsx", "react",
            "--esModuleInterop", "--allowSyntheticDefaultImports",
        ],
        cwd=str(ROOT / "remotion-composer"),
        capture_output=True, text=True, timeout=180,
    )
    assert compile_run.returncode == 0, f"tsc failed:\n{compile_run.stdout}\n{compile_run.stderr}"
    compiled = next(compiled_dir.rglob("DiagramLayer.js"), None)
    assert compiled is not None, f"compiled module not found under {compiled_dir}"
    harness = tmp / "harness.js"
    harness.write_text(HARNESS, encoding="utf-8")
    import os
    composer_nm = str(ROOT / "remotion-composer" / "node_modules")
    env = dict(
        os.environ,
        HERO_NODE=json.dumps(HERO_NODE),
        COMPOSER_NODE_MODULES=composer_nm,
        NODE_PATH=composer_nm + os.pathsep + os.environ.get("NODE_PATH", ""),
    )
    return subprocess.run(
        ["node", str(harness), str(compiled), json.dumps(THEME), json.dumps({})],
        capture_output=True, text=True, timeout=60, env=env,
    )


@pytest.mark.skipif(not TSC.exists(), reason="typescript devDependency not installed")
def test_focal_hero_renders_subject_not_card():
    """The real DiagramLayer: hero for icon-focal, cards otherwise."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = _compile_and_run(Path(tmpdir))
    assert result.returncode == 0, f"diagram-hero assertions failed:\n{result.stdout}\n{result.stderr}"
    assert "ALL DIAGRAM-HERO ASSERTIONS PASSED" in result.stdout


def test_layer_content_passes_topology_to_diagram_layer():
    """Both DiagramLayer call sites must forward the native topology."""
    sc = (ROOT / "remotion-composer/src/compositions/SceneComposition.tsx").read_text("utf-8")
    assert sc.count("topology={spec.topology}") == 2, "both diagram sites must pass topology"
