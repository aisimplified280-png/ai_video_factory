"""Behavioral scene-boundary timing tests.

The timing math lives in remotion-composer/src/runtime/eventTiming.ts — the
exact module ProductionComposition and SceneComposition execute at render time.
These tests compile that real module with tsc and drive it in node, asserting
frame-by-frame rendered behavior at a scene boundary (not source strings):

1. Outgoing event fully visible immediately before the boundary.
2. Exit begins within the configured tail (exactly at the event's true end).
3. Exit completes on the event's LAST visible frame, before parent unmount.
4. Incoming element reaches its stable layout while still on screen.
5. No frame where all scene content disappears (outgoing ∪ incoming > 0).
6. No outgoing element abruptly vanishes at the exact boundary.
Also: the transition overlap is counted exactly once anywhere in the math.
"""
import subprocess
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
TS_SRC = ROOT / "remotion-composer" / "src" / "runtime" / "eventTiming.ts"
TSC = ROOT / "remotion-composer" / "node_modules" / "typescript" / "bin" / "tsc"

# Drives the compiled production module through a real boundary crossing.
HARNESS = r"""
const mod = require(process.argv[2]);
const {placeEvent, renderedLength, sceneLength, frameState, enterState, exitState} = mod;

const failures = [];
let checks = 0;
const check = (name, ok, detail) => {
  checks += 1;
  if (!ok) failures.push(name + (detail ? ': ' + detail : ''));
};

const OVERLAP = 12;
const SCENE = 160;
const BOUNDARY = SCENE;
const ROLE = 'midground';

// Production configuration: outgoing scene event + incoming scene event.
const outgoing = placeEvent({startFrame: 0, frameCount: SCENE}, 0, OVERLAP, OVERLAP);
const incoming = placeEvent({startFrame: BOUNDARY, frameCount: SCENE}, BOUNDARY, OVERLAP, 0);

// --- Overlap counted exactly once, everywhere. ---
check('duration is true event length', outgoing.duration === SCENE, 'duration=' + outgoing.duration);
check('rendered = duration + one tail', renderedLength(outgoing) === SCENE + OVERLAP, 'rendered=' + renderedLength(outgoing));
check('scene sequence = scene + one tail', sceneLength(SCENE, OVERLAP) === SCENE + OVERLAP);
check(
  'full-scene event unmounts exactly with its scene',
  renderedLength(outgoing) === sceneLength(SCENE, OVERLAP),
  'rendered=' + renderedLength(outgoing) + ' scene=' + sceneLength(SCENE, OVERLAP),
);

// --- 1. Fully visible before the boundary. ---
const before = frameState(BOUNDARY - 1, outgoing);
check('pre-boundary: not in exit window', !before.inTail, JSON.stringify(before));
check('pre-boundary: entrance complete/stable', enterState(before.local, outgoing.head, ROLE).p === 1);

// --- 2. Exit begins within the configured tail, at the true end. ---
const atBoundary = frameState(BOUNDARY, outgoing);
check('boundary: exit window open at frame 0 of tail', atBoundary.inTail && atBoundary.intoTail === 0, JSON.stringify(atBoundary));

// --- 3. Exit completes before parent scene unmount. ---
const lastVisible = frameState(renderedLength(outgoing) - 1, outgoing);
check('last visible frame still inside tail window', lastVisible.inTail && lastVisible.intoTail === OVERLAP - 1, JSON.stringify(lastVisible));
const finalExit = exitState(lastVisible.intoTail, outgoing.tail, ROLE);
check('exit progress reaches 1 on last visible frame', finalExit.active && finalExit.q === 1, JSON.stringify(finalExit));

// --- 4. Incoming reaches stable layout while on screen. ---
// (Inside its Sequence the incoming scene sees scene-relative frames: 0..SCENE.)
const stableLocal = OVERLAP - 1;
const incStable = enterState(stableLocal, OVERLAP, ROLE);
check('incoming stable at head-1 (p=1, visible)', incStable.p === 1 && !incStable.hidden, JSON.stringify(incStable));
const incomingAtStable = frameState(stableLocal, incoming);
check('incoming not entering after its head window', !frameState(OVERLAP, incoming).entering);
check('incoming local advances with frames', incomingAtStable.local === stableLocal, JSON.stringify(incomingAtStable));

// --- 5 + 6. Boundary overlap: union never empty, outgoing fades smoothly. ---
const opacityAt = (frame, timing, role) => {
  const st = frameState(frame, timing);
  if (!st.inTail) return 1;
  const e = exitState(st.intoTail, timing.tail, role);
  return e.active ? 1 - e.q : 1;
};
const enterOpacityAt = (frame, timing, role) => {
  const st = frameState(frame, timing);
  if (!st.entering) return 1;
  const en = enterState(st.local, timing.head, role);
  return en.hidden ? 0 : en.p;
};

let prevOut = null;
let maxStep = 0;
for (let f = BOUNDARY; f < BOUNDARY + OVERLAP; f += 1) {
  const outO = opacityAt(f, outgoing, ROLE);
  const inO = enterOpacityAt(f - BOUNDARY, incoming, ROLE);
  check('content union non-empty @' + f, Math.max(outO, inO) > 0, 'out=' + outO.toFixed(3) + ' in=' + inO.toFixed(3));
  if (prevOut !== null) {
    maxStep = Math.max(maxStep, Math.abs(prevOut - outO));
  }
  prevOut = outO;
}
const atBoundaryOut = opacityAt(BOUNDARY, outgoing, ROLE);
check('outgoing full opacity at exact boundary', atBoundaryOut === 1, 'opacity=' + atBoundaryOut);
check('outgoing fade never jumps >0.5/frame', maxStep <= 0.5, 'maxStep=' + maxStep.toFixed(3));
check('outgoing fully faded on final frame', prevOut === 0, 'final=' + prevOut);

// Roles other than content also complete their exits (details lead the exit).
for (const role of ['foreground', 'character', 'primary_visual', '']) {
  const lead = exitState(OVERLAP - 1, OVERLAP, role);
  check('exit completes for role "' + role + '"', lead.active && lead.q === 1, JSON.stringify(lead));
}

if (failures.length > 0) {
  console.error('FAILED ' + failures.length + '/' + checks);
  failures.forEach((f) => console.error('  - ' + f));
  process.exit(1);
}
console.log('ALL TIMING ASSERTIONS PASSED (' + checks + ')');
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
    compiled = next(compiled_dir.rglob("eventTiming.js"), None)
    assert compiled is not None, f"compiled module not found under {compiled_dir}"
    harness = tmp / "harness.js"
    harness.write_text(HARNESS, encoding="utf-8")
    return subprocess.run(
        ["node", str(harness), str(compiled)],
        capture_output=True, text=True, timeout=60,
    )


@pytest.mark.skipif(not TSC.exists(), reason="typescript devDependency not installed")
def test_boundary_exit_has_visible_frames_and_completes_before_unmount():
    """The outgoing scene's exit runs in real frames and finishes before unmount."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = _compile_and_run(Path(tmpdir))
    assert result.returncode == 0, f"timing assertions failed:\n{result.stdout}\n{result.stderr}"
    assert "ALL TIMING ASSERTIONS PASSED" in result.stdout


def test_compositions_are_wired_to_the_shared_timing_module():
    """Wiring guard: both compositions must execute the tested module, and the
    old double-count (`frameCount + (isVisual ? tail : 0)`) must not return."""
    pc = (ROOT / "remotion-composer/src/compositions/ProductionComposition.tsx").read_text("utf-8")
    sc = (ROOT / "remotion-composer/src/compositions/SceneComposition.tsx").read_text("utf-8")
    assert "placeEvent(" in pc, "ProductionComposition must place events via runtime/eventTiming"
    assert "isVisual ? tail : 0" not in pc, "tail must never be added to an event's duration"
    assert "frameState(" in sc, "SceneComposition must derive per-frame state via runtime/eventTiming"
    assert "duration + tail" not in sc, "SceneComposition must not add the tail a second time"
    assert "from '../runtime/eventTiming'" in sc
