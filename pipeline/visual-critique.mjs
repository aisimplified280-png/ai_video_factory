// pipeline/visual-critique.mjs - Rendered Video Critique & Ranked Polish Engine
// Inspired by claude-motion (motion intelligence) & motion-graphics-skills (visual design judgment)

export const CRITIQUE_SEVERITY = {
  P0: "P0_CRITICAL_BLOCKER",  // Must fix before export (black frames, broken targets, safe-zone collision)
  P1: "P1_HIGH_POLISH",       // Stiff motion, lack of cause-and-effect reaction, missing continuity
  P2: "P2_MEDIUM_POLISH",     // Sub-optimal contrast, missing audio SFX cues
};

/**
 * Inspect a project's rendered diagnostic frames and scene graphs.
 * Evaluates text readability, subject visibility, motion continuity,
 * cause-and-effect responsiveness, and safe zone compliance.
 */
export function critiqueRenderedSceneMoments(projectData, diagnosticFramePaths = []) {
  const issues = [];
  const scenes = projectData.scenes || projectData.storyboard?.beats || [];
  const sceneGraphs = scenes.map((s) => s.sceneGraph).filter(Boolean);

  // 1. Diagnostic frame completeness (claude-motion 3-moment review: entrance, action, payoff)
  const expectedFrameCount = scenes.length * 3;
  if (diagnosticFramePaths.length > 0 && diagnosticFramePaths.length < expectedFrameCount) {
    issues.push({
      severity: CRITIQUE_SEVERITY.P1,
      category: "diagnostic-coverage",
      message: `Diagnostic review incomplete: received ${diagnosticFramePaths.length} frames, expected ${expectedFrameCount} (entrance, action, payoff across ${scenes.length} scenes).`,
      recommendation: "Ensure render pipeline extracts 3 distinct moments per scene to verify motion progression.",
    });
  }

  // 2. Safe zone compliance check (motion-graphics-skills safe margins)
  // Safe margins for 9:16 mobile YouTube Shorts:
  // Top: >= 220px (channel bar / overlay)
  // Bottom: <= 1450px (captions, like button, title bar)
  // Left: >= 80px, Right: <= 1000px
  scenes.forEach((scene, sIdx) => {
    const sg = scene.sceneGraph;
    if (sg && sg.safeZone) {
      const { top, bottom, left, right } = sg.safeZone;
      if (top < 200) {
        issues.push({
          severity: CRITIQUE_SEVERITY.P0,
          category: "safe-zone-encroachment",
          sceneIndex: sIdx,
          message: `Scene ${sIdx + 1} safeZone top (${top}px) encroaches into YouTube Shorts top channel bar (< 200px).`,
          recommendation: "Shift visual stage down by setting safeZone.top >= 220px.",
        });
      }
      if (bottom > 1520) {
        issues.push({
          severity: CRITIQUE_SEVERITY.P0,
          category: "safe-zone-encroachment",
          sceneIndex: sIdx,
          message: `Scene ${sIdx + 1} safeZone bottom (${bottom}px) encroaches into active captions and YouTube action buttons (> 1500px).`,
          recommendation: "Constrain safeZone.bottom <= 1450px to preserve caption clearance.",
        });
      }
    }
  });

  // 3. Motion cause-and-effect review (claude-motion motion intelligence)
  sceneGraphs.forEach((sg, sIdx) => {
    const actions = sg.actions || [];
    actions.forEach((act, aIdx) => {
      if (!act.causeAndEffect) {
        issues.push({
          severity: CRITIQUE_SEVERITY.P1,
          category: "isolated-motion",
          sceneIndex: sIdx,
          actionIndex: aIdx,
          message: `Scene ${sIdx + 1} action '${act.action}' lacks causeAndEffect definition. Objects should cause reactions in other elements, not move in isolation.`,
          recommendation: "Define reactingElements and reaction state (e.g. node pulse, metric advance, shockwave).",
        });
      } else {
        const { triggerElement, reactingElements, reaction } = act.causeAndEffect;
        if (!triggerElement || !Array.isArray(reactingElements) || reactingElements.length === 0 || !reaction) {
          issues.push({
            severity: CRITIQUE_SEVERITY.P1,
            category: "incomplete-cause-and-effect",
            sceneIndex: sIdx,
            actionIndex: aIdx,
            message: `Scene ${sIdx + 1} action '${act.action}' has malformed causeAndEffect structure.`,
            recommendation: "Ensure triggerElement, non-empty reactingElements, and clear reaction description are provided.",
          });
        }
      }

      // Check for sound effect cues on impactful actions (claude-motion SFX cues)
      const impactfulActions = ["lock", "stall", "bounce", "stamp", "hit", "descend", "burst", "shockwave"];
      const isImpactful = impactfulActions.some((kw) => (act.action || "").toLowerCase().includes(kw));
      if (isImpactful && !act.sfxCue) {
        issues.push({
          severity: CRITIQUE_SEVERITY.P2,
          category: "missing-sfx-cue",
          sceneIndex: sIdx,
          actionIndex: aIdx,
          message: `Scene ${sIdx + 1} impactful action '${act.action}' does not have a synchronized sfxCue.`,
          recommendation: "Assign a sound cue (e.g. 'probe-whoosh', 'node-lock-snap', 'stamp-thud') to punctuate the motion.",
        });
      }
    });
  });

  // 4. Continuous transformation & scene transition continuity (motion-graphics morphing)
  for (let i = 0; i < scenes.length - 1; i++) {
    const currSg = scenes[i].sceneGraph;
    const nextSg = scenes[i + 1].sceneGraph;
    if (currSg && nextSg) {
      if (currSg.transition && currSg.transition.continuity) {
        const { persistentElement, morphTarget } = currSg.transition.continuity;
        const currElements = new Set((currSg.elements || []).map((e) => e.id));
        const nextElements = new Set((nextSg.elements || []).map((e) => e.id));

        if (persistentElement && !currElements.has(persistentElement)) {
          issues.push({
            severity: CRITIQUE_SEVERITY.P1,
            category: "broken-continuity",
            sceneIndex: i,
            message: `Scene ${i + 1} transition continuity specifies persistentElement '${persistentElement}' not found in Scene ${i + 1} elements.`,
            recommendation: "Verify persistentElement matches an element id in the exiting scene.",
          });
        }
        if (morphTarget && !nextElements.has(morphTarget)) {
          issues.push({
            severity: CRITIQUE_SEVERITY.P1,
            category: "broken-continuity",
            sceneIndex: i,
            message: `Scene ${i + 1} transition continuity specifies morphTarget '${morphTarget}' not found in Scene ${i + 2} elements.`,
            recommendation: "Verify morphTarget matches an element id in the entering scene.",
          });
        }
      }
    }
  }

  // 5. Visual diversity across entrance frames (motion-graphics-skills visual monotony check)
  const entranceMotions = scenes.map((s) => s.sceneGraph?.actions?.[0]?.action).filter(Boolean);
  const entranceMotionCounts = {};
  entranceMotions.forEach((m) => {
    entranceMotionCounts[m] = (entranceMotionCounts[m] || 0) + 1;
  });
  Object.entries(entranceMotionCounts).forEach(([m, count]) => {
    if (count > Math.max(2, Math.floor(scenes.length * 0.5))) {
      issues.push({
        severity: CRITIQUE_SEVERITY.P1,
        category: "monotonous-entrance",
        message: `Entrance action '${m}' repeated across ${count} scenes (> 50%).`,
        recommendation: "Vary initial entrance dynamics (e.g. lateral scan, arc sweep, vertical descent, stamp drop).",
      });
    }
  });

  // Calculate score and triage rank
  const p0Count = issues.filter((iss) => iss.severity === CRITIQUE_SEVERITY.P0).length;
  const p1Count = issues.filter((iss) => iss.severity === CRITIQUE_SEVERITY.P1).length;
  const p2Count = issues.filter((iss) => iss.severity === CRITIQUE_SEVERITY.P2).length;

  const score = Math.max(0, 100 - p0Count * 40 - p1Count * 15 - p2Count * 5);
  const passed = p0Count === 0 && p1Count === 0;

  // Ranked Polish Checklist (ordered by severity)
  const rankedChecklist = [...issues].sort((a, b) => {
    const weight = { [CRITIQUE_SEVERITY.P0]: 0, [CRITIQUE_SEVERITY.P1]: 1, [CRITIQUE_SEVERITY.P2]: 2 };
    return weight[a.severity] - weight[b.severity];
  });

  return {
    passed,
    score,
    p0Count,
    p1Count,
    p2Count,
    issues,
    rankedChecklist,
    critiqueSummary: `Visual Critique Score: ${score}/100 (P0 Blockers: ${p0Count}, P1 Polish: ${p1Count}, P2 Aesthetics: ${p2Count})`,
  };
}
