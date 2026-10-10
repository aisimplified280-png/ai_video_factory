"""Caption set timing behavior (§19) — word-anchored windows.

The set math lives in remotion-composer/src/captions/captionSets.ts — compiled
here with tsc and driven in node (the same pure module CaptionTrack renders
with), so the test proves the opacity curve rather than grepping JSX:

1. The active word's set always owns the current progress, for any word count
   (divisible by WORDS_PER_SET or not).
2. The only invisible samples are the designed breath exactly at set
   boundaries — no sustained dead gaps.
3. Regression: the old setIndex/setCount window pushed local past 1 whenever
   the final set was partial (e.g. the real 21-word scene_03 narration at
   progress 0.899), hiding the caption for up to ~0.6s of rendered video.
"""
import subprocess
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
TS_SRC = ROOT / "remotion-composer" / "src" / "captions" / "captionSets.ts"
TSC = ROOT / "remotion-composer" / "node_modules" / "typescript" / "bin" / "tsc"

HARNESS = r"""
const {captionSetAt, WORDS_PER_SET} = require(process.argv[2]);

const failures = [];
let checks = 0;
const check = (name, ok, detail) => {
  checks += 1;
  if (!ok) failures.push(name + (detail ? ': ' + detail : ''));
};

// The real 21-word narration that rendered a dead caption gap at 15.5s.
const scene3 = 'Your receiver picks up these signals, measuring the tiny time delay from each. This delay reveals the distance to each satellite.';
const words3 = scene3.split(/\s+/).filter(Boolean);
check('fixture is 21 words (partial final set)', words3.length === 21, 'got ' + words3.length);

// 1. Regression: progress 0.899 (15.5s into scene_03) must show the caption.
const bad = captionSetAt(scene3, 0.899);
check('partial-final-set window covers 0.899', bad !== null && bad.opacity > 0.5,
  bad ? 'opacity=' + bad.opacity : 'null');
// and its words are the set that actually owns that progress (words 16-19).
check('0.899 resolves to the owning word set',
  bad && bad.setStart === 16 && bad.activeInSet === 2,
  bad ? 'setStart=' + bad.setStart + ' activeInSet=' + bad.activeInSet : 'null');

// 2. Window alignment: returned set == active word's set, for many word counts.
const sampleText = (n) => Array.from({length: n}, (_, i) => 'w' + i).join(' ');
const misaligned = [];
for (const n of [1, 4, 5, 7, 19, 20, 21, 22, 23, 25, 47]) {
  for (let i = 0; i <= 500; i++) {
    const p = i / 500;
    const s = captionSetAt(sampleText(n), p);
    const activeWord = Math.min(n - 1, Math.floor(p * n));
    const expected = Math.floor(activeWord / WORDS_PER_SET);
    if (!s || s.setIndex !== expected || s.setStart !== expected * WORDS_PER_SET) {
      misaligned.push(n + 'w@' + p);
    }
  }
}
check('set window aligned with active word for every sample',
  misaligned.length === 0, misaligned.slice(0, 5).join(','));

// 3. No dead gaps: invisible samples must be bounded by the boundary breath
//    (about two grid samples per boundary + scene start/end), never a gap.
const deadViolations = [];
for (const [label, text] of [['scene3', scene3], ['19w', sampleText(19)], ['23w', sampleText(23)]]) {
  const n = text.split(/\s+/).filter(Boolean).length;
  const boundaryBudget = 2 * (Math.ceil(n / WORDS_PER_SET) + 1);
  let dead = 0;
  for (let i = 0; i <= 1000; i++) {
    const s = captionSetAt(text, i / 1000);
    if (!s || s.opacity <= 0.03) dead += 1;
  }
  if (dead > boundaryBudget) deadViolations.push(label + ' dead=' + dead + ' budget=' + boundaryBudget);
}
check('no dead caption gaps beyond the boundary breath',
  deadViolations.length === 0, deadViolations.join('; '));

// 4. Designed behavior preserved.
check('empty text -> null', captionSetAt('   ', 0.5) === null);
const mid = captionSetAt(scene3, 0.30);
check('mid-set is fully held', mid !== null && mid.opacity === 1, mid ? 'opacity=' + mid.opacity : 'null');
const breath = captionSetAt(scene3, 4 / 21);
check('exactly at a boundary the screen breathes', breath !== null && breath.opacity === 0,
  breath ? 'opacity=' + breath.opacity : 'null');
const fadeIn = captionSetAt(scene3, 0.01);
check('first set fades in just after the start', fadeIn !== null && fadeIn.opacity > 0,
  fadeIn ? 'opacity=' + fadeIn.opacity : 'null');
const last = captionSetAt(scene3, 0.96);
check('final partial set renders its last word',
  last !== null && last.setWords.length === 1 && last.setWords[0] === 'satellite.',
  last ? JSON.stringify(last.setWords) : 'null');

if (failures.length > 0) {
  console.error('FAILED ' + failures.length + '/' + checks);
  failures.forEach((f) => console.error('  - ' + f));
  process.exit(1);
}
console.log('ALL CAPTION-SET ASSERTIONS PASSED (' + checks + ')');
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
    compiled = next(compiled_dir.rglob("captionSets.js"), None)
    assert compiled is not None, f"compiled module not found under {compiled_dir}"
    harness = tmp / "harness.js"
    harness.write_text(HARNESS, encoding="utf-8")
    return subprocess.run(
        ["node", str(harness), str(compiled)],
        capture_output=True, text=True, timeout=60,
    )


@pytest.mark.skipif(not TSC.exists(), reason="typescript devDependency not installed")
def test_caption_set_windows_cover_the_active_word():
    """The real set math: no dead gaps, windows aligned, boundary breath kept."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = _compile_and_run(Path(tmpdir))
    assert result.returncode == 0, f"caption-set assertions failed:\n{result.stdout}\n{result.stderr}"
    assert "ALL CAPTION-SET ASSERTIONS PASSED" in result.stdout


def test_caption_track_uses_the_tested_set_math():
    """CaptionTrack must render through the tested module, not inline math."""
    ct = (ROOT / "remotion-composer/src/captions/CaptionTrack.tsx").read_text("utf-8")
    assert "from './captionSets'" in ct, "component must import the tested set math"
    assert "captionSetAt(active.textReference, currentProgress)" in ct
    # The misaligned window math must not return.
    assert "setIndex / setCount" not in ct
    assert "Math.ceil(allWords.length" not in ct
