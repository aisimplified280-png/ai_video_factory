// pipeline/visual-linter.mjs - Deterministic Visual Diversity & Storyboard Linter

/**
 * Lints a storyboard and composition data for visual diversity,
 * overused layouts, accidental asset repetition, and narration relevance.
 */
export function lintVisualDiversity(storyboard) {
  const criticalIssues = [];
  const warnings = [];
  const beats = storyboard.beats || [];

  if (!Array.isArray(beats) || beats.length === 0) {
    return {
      passed: false,
      diversityScore: 0,
      criticalIssues: ["Storyboard contains no beats to evaluate."],
      warnings: [],
      issues: ["Storyboard contains no beats to evaluate."],
    };
  }

  // 1. Consecutive repetition check
  for (let i = 1; i < beats.length; i++) {
    const prev = beats[i - 1];
    const curr = beats[i];
    if (prev.visualMode === curr.visualMode) {
      warnings.push(
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
      warnings.push(
        `Visual mode '${mode}' is overused: appears in ${count} of ${beats.length} beats (> 50%). Introduce distinct explanatory compositions.`
      );
    }
  });

  // 3. Accidental asset repetition across scenes (Critical Issue)
  const seenAssets = new Map(); // assetId -> beatIndex
  beats.forEach((b, idx) => {
    if (b.assetId) {
      if (seenAssets.has(b.assetId)) {
        const firstBeat = seenAssets.get(b.assetId);
        if (!b.narrativeContinuityReason) {
          criticalIssues.push(
            `Accidental asset reuse: Beat ${idx + 1} repeats asset '${b.assetId}' (first used in Beat ${firstBeat + 1}) without an explicit narrativeContinuityReason.`
          );
        }
      } else {
        seenAssets.set(b.assetId, idx);
      }
    }
  });

  // 4. Asset to narration relevance check (Critical Issue for severe mismatches)
  const unrelatedWords = ["cocktail", "bar", "bottle", "wine", "beer", "drink", "recipe", "food", "kitchen", "fashion", "wedding"];
  beats.forEach((b, idx) => {
    if (b.assetData) {
      const astText = `${b.assetData.title || ""} ${b.assetData.attributionText || ""} ${b.assetData.assetId || ""}`.toLowerCase();
      const isTechBeat = /\b(vector|graph|database|prompt|cache|token|model|server|api|code|algorithm|latency|memory|indexing)\b/i.test(
        `${b.visualTitle || ""} ${b.spokenLine || ""}`
      );
      if (isTechBeat) {
        for (const uw of unrelatedWords) {
          if (astText.includes(uw)) {
            criticalIssues.push(
              `Irrelevant asset in technical scene: Beat ${idx + 1} uses asset '${b.assetId}' referencing '${uw}' which does not explain '${b.visualTitle}'.`
            );
            break;
          }
        }
      }
    }
  });

  // 5. Narrative focal object & spoken line presence
  beats.forEach((b, idx) => {
    if (!b.spokenLine || !b.spokenLine.trim()) {
      criticalIssues.push(`Beat ${idx + 1} has empty spokenLine.`);
    }
    if (!b.visualTitle || !b.visualTitle.trim()) {
      criticalIssues.push(`Beat ${idx + 1} has empty visualTitle.`);
    }
  });

  // Combined issues list
  const allIssues = [...criticalIssues, ...warnings];
  const diversityScore = Math.max(0, 100 - criticalIssues.length * 30 - warnings.length * 15);

  return {
    passed: allIssues.length === 0,
    hasCriticalBlockers: criticalIssues.length > 0,
    diversityScore,
    criticalIssues,
    warnings,
    issues: allIssues,
    uniqueModesCount: Object.keys(modeCounts).length,
    modeDistribution: modeCounts,
  };
}
