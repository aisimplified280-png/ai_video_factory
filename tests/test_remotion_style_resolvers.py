"""Style resolver behavior (§5 static default, cross-dissolve honesty).

The resolvers live in remotion-composer/src/runtime/styleResolvers.ts — the
exact module SceneComposition executes at render time. Compiled here with tsc
and driven in node, proving rendered styling behavior rather than grepping JSX:

1. Static is the default: null/undefined/unknown motion intent styles nothing
   (no back-door rise-and-fade). Explicit 'reveal'/'reorder' still reveal.
2. The default cross-dissolve (fade module) is opacity-only on every role, in
   both directions — vertical movement and scale are reserved for explicit
   slide_transition boundaries, which keep their transform.
3. transitionModuleFor resolves every canonical intent to its module.
"""
import subprocess
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
TS_SRC = ROOT / "remotion-composer" / "src" / "runtime" / "styleResolvers.ts"
TSC = ROOT / "remotion-composer" / "node_modules" / "typescript" / "bin" / "tsc"

HARNESS = r"""
const mod = require(process.argv[2]);
const {motionStyle, cameraStyle, headStyleFor, tailStyleFor, transitionModuleFor, mergeStyles} = mod;

const failures = [];
let checks = 0;
const check = (name, ok, detail) => {
  checks += 1;
  if (!ok) failures.push(name + (detail ? ': ' + detail : ''));
};
const hasTransform = (s) => s && s.transform !== undefined;

// 1. Static default: no intent -> no styling at any progress.
for (const intent of [null, undefined, 'bogus_intent']) {
  for (const p of [0, 0.15, 0.5, 1]) {
    const s = motionStyle(intent, p);
    check('motionStyle(' + intent + ', ' + p + ') is empty',
      Object.keys(s).length === 0, JSON.stringify(s));
  }
}
// Explicit reveal-class intents still animate.
const rev = motionStyle('reveal', 0.1);
check('explicit reveal still rises and fades', rev.opacity < 1 && hasTransform(rev), JSON.stringify(rev));
const reo = motionStyle('reorder', 0.1);
check('reorder still resolves through reveal', reo.opacity < 1 && hasTransform(reo), JSON.stringify(reo));
const settled = motionStyle('reveal', 1);
check('reveal settles at progress 1', settled.opacity === 1, JSON.stringify(settled));
// mergeStyles with nothing stays nothing.
check('mergeStyles() of empties is empty', Object.keys(mergeStyles({}, undefined, {})).length === 0);

// 2. Fade head/tail: opacity-only on every role, both directions.
for (const role of ['midground', 'primary_visual', 'foreground', 'diagram', 'overlay', 'character', '']) {
  const h = headStyleFor('cross_dissolve', 12, 6, role);
  check('fade head opacity-only for ' + (role || '(default role)'),
    h.opacity !== undefined && !hasTransform(h), JSON.stringify(h));
  const t = tailStyleFor('cross_dissolve', 12, 6, role);
  check('fade tail opacity-only for ' + (role || '(default role)'),
    t.opacity !== undefined && !hasTransform(t), JSON.stringify(t));
  const hf = headStyleFor('fade', 12, 6, role);
  check('fade intent opacity-only for ' + (role || '(default role)'),
    hf.opacity !== undefined && !hasTransform(hf), JSON.stringify(hf));
}
// Matched timing: both sides traverse the full opacity range over their window.
const hEnd = headStyleFor('cross_dissolve', 12, 11, 'midground');
const tEnd = tailStyleFor('cross_dissolve', 12, 11, 'midground');
const tStart = tailStyleFor('cross_dissolve', 12, 0, 'midground');
check('fade head reaches full opacity by window end', hEnd.opacity === 1, JSON.stringify(hEnd));
check('fade tail reaches zero by window end', tEnd.opacity === 0, JSON.stringify(tEnd));
check('fade tail starts fully visible (unstyled)', Object.keys(tStart).length === 0, JSON.stringify(tStart));
// Slide keeps its movement (reserved, not removed).
const sh = headStyleFor('slide_transition', 12, 6, 'midground');
check('slide head still moves', hasTransform(sh), JSON.stringify(sh));
const st = tailStyleFor('slide_transition', 12, 6, 'midground');
check('slide tail still moves', hasTransform(st), JSON.stringify(st));
// Head windows still behave: hidden before turn, empty after window.
const hidden = headStyleFor('cross_dissolve', 12, 0, 'midground');
check('head hidden at local 0 stays opacity 0', hidden.opacity === 0, JSON.stringify(hidden));
check('head empty past window', Object.keys(headStyleFor('cross_dissolve', 12, 12, 'midground')).length === 0);
check('tail empty without tail', Object.keys(tailStyleFor('cross_dissolve', 0, 0, 'midground')).length === 0);

// 3. Intent -> module resolution.
const mapping = {
  hard_cut: 'hardCut', fade: 'fade', cross_dissolve: 'fade', directional_wipe: 'wipe',
  object_transition: 'objectTransition', zoom_transition: 'zoom', shape_morph: 'shapeMorph',
  light_flash: 'lightFlash', motion_blur: 'motionBlur', match_cut: 'matchCut',
  slide_transition: 'slide', unknown_xyz: 'hardCut',
};
for (const [intent, module] of Object.entries(mapping)) {
  check('transitionModuleFor(' + intent + ')', transitionModuleFor(intent) === module,
    transitionModuleFor(intent));
}
// Static camera never moves.
const cam = cameraStyle('static', 0.7);
check('static camera is empty', Object.keys(cam).length === 0, JSON.stringify(cam));
const camNull = cameraStyle(null, 0.7);
check('null camera is empty', Object.keys(camNull).length === 0, JSON.stringify(camNull));

if (failures.length > 0) {
  console.error('FAILED ' + failures.length + '/' + checks);
  failures.forEach((f) => console.error('  - ' + f));
  process.exit(1);
}
console.log('ALL STYLE-RESOLVER ASSERTIONS PASSED (' + checks + ')');
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
        capture_output=True, text=True, timeout=180,
    )
    assert compile_run.returncode == 0, f"tsc failed:\n{compile_run.stdout}\n{compile_run.stderr}"
    compiled = next(compiled_dir.rglob("styleResolvers.js"), None)
    assert compiled is not None, f"compiled module not found under {compiled_dir}"
    harness = tmp / "harness.js"
    harness.write_text(HARNESS, encoding="utf-8")
    return subprocess.run(
        ["node", str(harness), str(compiled)],
        capture_output=True, text=True, timeout=60,
    )


@pytest.mark.skipif(not TSC.exists(), reason="typescript devDependency not installed")
def test_style_resolver_static_default_and_true_dissolve():
    """The real resolvers: static default, opacity-only dissolve, moving slide."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = _compile_and_run(Path(tmpdir))
    assert result.returncode == 0, f"style-resolver assertions failed:\n{result.stdout}\n{result.stderr}"
    assert "ALL STYLE-RESOLVER ASSERTIONS PASSED" in result.stdout


def test_scene_composition_uses_the_tested_resolvers():
    """SceneComposition must render through the tested module, not inline math."""
    sc = (ROOT / "remotion-composer/src/compositions/SceneComposition.tsx").read_text("utf-8")
    assert "from '../runtime/styleResolvers'" in sc
    for name in ("motionStyle(", "cameraStyle(", "headStyleFor(", "tailStyleFor(", "mergeStyles("):
        assert name in sc, f"composition must call {name.rstrip('(')}"
    # No inline resolver redefinitions.
    assert "export function motionStyle" not in sc
    assert "export function headStyleFor" not in sc
    assert "export function tailStyleFor" not in sc
