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

  // 6. Scene Graph & Motion Choreography Integrity (Critical Checks for v2)
  const isV2 = storyboard.version >= 2;
  const actionCounts = {};
  beats.forEach((b, idx) => {
    if (!b.sceneGraph) {
      if (isV2) {
        criticalIssues.push(`Beat ${idx + 1} is missing required sceneGraph structure.`);
      }
      return;
    }

    const sg = b.sceneGraph;
    if (!sg.visualMetaphor) {
      criticalIssues.push(`Beat ${idx + 1} sceneGraph is missing visualMetaphor.`);
    }

    if (!Array.isArray(sg.elements) || sg.elements.length === 0) {
      criticalIssues.push(`Beat ${idx + 1} sceneGraph elements must be a non-empty array.`);
    } else {
      const elementIds = new Set(sg.elements.map((el) => el.id));
      if (sg.primarySubject && !elementIds.has(sg.primarySubject)) {
        criticalIssues.push(
          `Beat ${idx + 1} sceneGraph primarySubject '${sg.primarySubject}' is not declared in elements.`
        );
      }

      if (Array.isArray(sg.actions)) {
        sg.actions.forEach((act, aIdx) => {
          if (!act.action) {
            criticalIssues.push(`Beat ${idx + 1} action [${aIdx}] is missing an action type.`);
          } else {
            actionCounts[act.action] = (actionCounts[act.action] || 0) + 1;
          }

          if (!act.trigger) {
            criticalIssues.push(`Beat ${idx + 1} action '${act.action || aIdx}' is missing a trigger.`);
          } else if (act.trigger === "spoken-phrase" && (!act.phrase || !act.phrase.trim())) {
            criticalIssues.push(
              `Beat ${idx + 1} action '${act.action}' has spoken-phrase trigger but missing phrase anchor.`
            );
          }

          if (typeof act.duration !== "number" || act.duration <= 0) {
            criticalIssues.push(`Beat ${idx + 1} action '${act.action}' duration must be > 0.`);
          }

          if (!act.purpose || !act.purpose.trim()) {
            criticalIssues.push(`Beat ${idx + 1} action '${act.action}' is missing narrative purpose.`);
          }

          if (act.target && !elementIds.has(act.target)) {
            criticalIssues.push(
              `Beat ${idx + 1} action '${act.action}' references undeclared target element '${act.target}'.`
            );
          }
        });
      } else {
        criticalIssues.push(`Beat ${idx + 1} sceneGraph actions must be a non-empty array.`);
      }
    }
  });

  // Warn if a single specific motion action is overused across > 50% of beats
  const maxAllowedActionReuse = Math.max(2, Math.floor(beats.length * 0.5));
  Object.entries(actionCounts).forEach(([actionName, count]) => {
    if (count > maxAllowedActionReuse && actionName !== "burst-emblem") {
      warnings.push(
        `Motion action '${actionName}' repeated across ${count} beats (> 50%). Diversify motion choreography.`
      );
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
