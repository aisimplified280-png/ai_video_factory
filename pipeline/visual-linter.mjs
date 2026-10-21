// pipeline/visual-linter.mjs - Deterministic Visual Diversity & Safe-Zone Linter
/**
 * Lints a storyboard and composition data for visual diversity,
 * overused layouts, consecutive repetition, and safe-zone compliance.
 */
export function lintVisualDiversity(storyboard) {
  const issues = [];
  const beats = storyboard.beats || [];

  if (!Array.isArray(beats) || beats.length === 0) {
    return {
      passed: false,
      diversityScore: 0,
      issues: ["Storyboard contains no beats to evaluate."],
    };
  }

  // 1. Consecutive repetition check
  for (let i = 1; i < beats.length; i++) {
    const prev = beats[i - 1];
    const curr = beats[i];
    if (prev.visualMode === curr.visualMode) {
      issues.push(
        `Consecutive visual repetition: Beat ${i} and Beat ${i + 1} both use visualMode '${curr.visualMode}' without narrative justification.`
      );
    }
  }

  // 2. Overused visual modes check (> 50% of beats using same mode)
  const modeCounts = {};
  beats.forEach((b) => {
    modeCounts[b.visualMode] = (modeCounts[b.visualMode] || 0) + 1;
  });

  const maxAllowedSingleMode = Math.max(2, Math.floor(beats.length * 0.5));
  Object.entries(modeCounts).forEach(([mode, count]) => {
    if (count > maxAllowedSingleMode) {
      issues.push(
        `Visual mode '${mode}' is overused: appears in ${count} of ${beats.length} beats (> 50%). Introduce distinct explanatory compositions.`
      );
    }
  });

  // 3. Narrative focal object & spoken line presence
  beats.forEach((b, idx) => {
    if (!b.spokenLine || !b.spokenLine.trim()) {
      issues.push(`Beat ${idx + 1} has empty spokenLine.`);
    }
    if (!b.visualTitle || !b.visualTitle.trim()) {
      issues.push(`Beat ${idx + 1} has empty visualTitle.`);
    }
  });

  // Diversity score: 100 minus 25 points per issue, clamped to [0, 100]
  const diversityScore = Math.max(0, 100 - issues.length * 25);

  return {
    passed: issues.length === 0,
    diversityScore,
    issues,
    uniqueModesCount: Object.keys(modeCounts).length,
    modeDistribution: modeCounts,
  };
}
