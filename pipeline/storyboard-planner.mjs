// pipeline/storyboard-planner.mjs - Story-First Semantic Storyboard Engine
import fs from "node:fs/promises";
import path from "node:path";

/**
 * Valid visual modes supported by the composition builder.
 */
export const VISUAL_MODES = new Set([
  "hook",
  "architecture-diagram",
  "step-process",
  "code",
  "terminal",
  "comparison",
  "concept-explainer",
  "asset-reveal",
]);

/**
 * Plan a structured, editable storyboard from a topic or script data,
 * matching beats to visual modes, narrative purposes, and verified assets.
 */
export async function planStoryboard(projectDir, scriptData, assetRegistry) {
  const beats = [];
  const scenes = scriptData.scenes || [];

  for (let idx = 0; idx < scenes.length; idx++) {
    const scene = scenes[idx];
    const isFirst = idx === 0;
    const isLast = idx === scenes.length - 1;

    let visualMode = scene.cardType || (isFirst ? "hook" : isLast ? "concept-explainer" : "architecture-diagram");
    if (!VISUAL_MODES.has(visualMode)) visualMode = "concept-explainer";

    // Narrative Intent Mapping
    let narrativePurpose = "";
    let viewerQuestion = "";

    if (isFirst) {
      narrativePurpose = "Hook attention and isolate the core operational bottleneck.";
      viewerQuestion = "What mistake is slowing down my system or workflow?";
    } else if (visualMode === "architecture-diagram") {
      narrativePurpose = "Visually demonstrate data flow and memory lifecycle.";
      viewerQuestion = "How does data move through the actual system components?";
    } else if (visualMode === "code" || visualMode === "terminal") {
      narrativePurpose = "Provide authentic, copy-pasteable syntax with zero pseudo-code.";
      viewerQuestion = "What exact configuration or command line syntax is needed?";
    } else if (visualMode === "step-process") {
      narrativePurpose = "Establish a reproducible, linear execution checklist.";
      viewerQuestion = "What sequential stages must be followed?";
    } else if (isLast) {
      narrativePurpose = "Deliver verifiable conclusion citing authentic documentation.";
      viewerQuestion = "What is the concrete architectural takeaway?";
    } else {
      narrativePurpose = "Compare traditional manual friction with structured automation.";
      viewerQuestion = "How does the improved methodology differ from legacy practice?";
    }

    // Asset Discovery & Rights Verification for visual modes that benefit from assets
    let assignedAsset = null;
    if (assetRegistry && (visualMode === "architecture-diagram" || visualMode === "asset-reveal")) {
      const candidates = await assetRegistry.searchAssets(scene.assetQuery || scriptData.topic || "ai-architecture", { count: 1 });
      if (candidates.length > 0) {
        const acquisition = await assetRegistry.acquireAndVerifyAsset(candidates[0]);
        if (acquisition.asset) {
          assignedAsset = acquisition.asset;
        }
      }
    }

    const beat = {
      beatId: `beat-${idx + 1}-${scene.id || "scene"}`,
      sceneIndex: idx,
      narrativePurpose,
      viewerQuestion,
      spokenLine: scene.voiceText,
      startTime: scene.startTime ?? idx * 3.0,
      endTime: scene.endTime ?? (idx + 1) * 3.0,
      duration: scene.duration ?? 3.0,
      visualMode,
      visualTitle: scene.visualTitle || scriptData.title,
      visualBody: scene.visualBody || "",
      badge: scene.badge || "METHODOLOGY",
      source: scene.source || null,
      assetId: assignedAsset ? assignedAsset.assetId : null,
      assetData: assignedAsset
        ? {
            assetId: assignedAsset.assetId,
            cachedPath: assignedAsset.cachedPath,
            licenseId: assignedAsset.licenseId,
            attributionText: assignedAsset.attributionText,
          }
        : null,
      motion: {
        transition: isFirst ? "back.out(1.5)" : "power3.out",
        cameraPush: true,
        staggerRate: 0.12,
      },
      sfxCue: scene.sfx || (isFirst ? "hook-impact" : isLast ? "clean-ding" : "ui-pop"),
    };

    // Copy specialized metadata for diagram or terminal
    if (scene.diagramNodes) beat.diagramNodes = scene.diagramNodes;
    if (scene.codeSnippet) beat.codeSnippet = scene.codeSnippet;
    if (scene.terminalTitle) beat.terminalTitle = scene.terminalTitle;
    if (scene.terminalLang) beat.terminalLang = scene.terminalLang;
    if (scene.steps) beat.steps = scene.steps;
    if (scene.oldWay) beat.oldWay = scene.oldWay;
    if (scene.newWay) beat.newWay = scene.newWay;

    beats.push(beat);
  }

  const storyboard = {
    version: 1,
    id: scriptData.id,
    topic: scriptData.topic || scriptData.title,
    totalDuration: scriptData.totalDuration,
    beatsCount: beats.length,
    beats,
    createdAt: new Date().toISOString(),
  };

  const storyboardPath = path.join(projectDir, "storyboard.json");
  await fs.writeFile(storyboardPath, JSON.stringify(storyboard, null, 2), "utf8");
  console.log(`[Storyboard] Plan generated with ${beats.length} beats: ${storyboardPath}`);

  return storyboard;
}
