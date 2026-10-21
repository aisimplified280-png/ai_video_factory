// pipeline/storyboard-planner.mjs - Story-First Semantic Storyboard Engine
import fs from "node:fs/promises";
import path from "node:path";
import { RIGHTS_STATUS } from "./rights-gate.mjs";

/**
 * Valid visual modes supported by the composition builder.
 */
export const VISUAL_MODES = new Set([
  "hook",
  "hook-bold-object",
  "architecture-diagram",
  "physical-metaphor",
  "step-process",
  "code",
  "terminal",
  "comparison",
  "concept-explainer",
  "asset-reveal",
]);

/**
 * Plan a structured, editable storyboard from a topic or script data,
 * matching beats to visual modes, narrative purposes, and strictly approved assets.
 */
export async function planStoryboard(projectDir, scriptData, assetRegistry) {
  const beats = [];
  const scenes = scriptData.scenes || [];
  const projectAssets = [];

  for (let idx = 0; idx < scenes.length; idx++) {
    const scene = scenes[idx];
    const isFirst = idx === 0;
    const isLast = idx === scenes.length - 1;

    let visualMode = scene.cardType || (isFirst ? "hook-bold-object" : isLast ? "concept-explainer" : "architecture-diagram");
    if (!VISUAL_MODES.has(visualMode)) visualMode = "concept-explainer";

    // Narrative Intent Mapping
    let narrativePurpose = "";
    let viewerQuestion = "";

    if (isFirst || visualMode === "hook" || visualMode === "hook-bold-object") {
      narrativePurpose = "Hook attention with an unexpected physical contradiction or system bottleneck.";
      viewerQuestion = "What unseen mistake is slowing down or complicating the system?";
    } else if (visualMode === "architecture-diagram") {
      narrativePurpose = "Visually demonstrate data flow, memory lifecycle, and component interactions.";
      viewerQuestion = "How does data move through the actual system components?";
    } else if (visualMode === "physical-metaphor") {
      narrativePurpose = "Translate abstract software dynamics into an intuitive physical metaphor.";
      viewerQuestion = "What real-world object or mechanic makes this invisible concept concrete?";
    } else if (visualMode === "code" || visualMode === "terminal") {
      narrativePurpose = "Provide authentic, copy-pasteable syntax with zero pseudo-code.";
      viewerQuestion = "What exact configuration or command line syntax is needed?";
    } else if (visualMode === "step-process") {
      narrativePurpose = "Establish a reproducible, linear execution checklist.";
      viewerQuestion = "What sequential stages must be followed?";
    } else if (isLast || visualMode === "concept-explainer") {
      narrativePurpose = "Deliver verifiable conclusion citing authentic documentation.";
      viewerQuestion = "What is the concrete architectural takeaway and rule of thumb?";
    } else {
      narrativePurpose = "Compare traditional manual friction with structured automation.";
      viewerQuestion = "How does the improved methodology differ from legacy practice?";
    }

    // Asset Discovery & Rights Verification for visual modes that benefit from assets
    let assignedAsset = null;
    if (assetRegistry && (visualMode === "architecture-diagram" || visualMode === "asset-reveal" || visualMode === "physical-metaphor")) {
      const candidates = await assetRegistry.searchAssets(scene.assetQuery || scriptData.topic || "ai-architecture", { count: 1 });
      if (candidates.length > 0) {
        const acquisition = await assetRegistry.acquireAndVerifyAsset(candidates[0]);
        // Strict gate: NEVER assign an asset that requires review or is rejected
        if (
          acquisition.asset &&
          (acquisition.status === RIGHTS_STATUS.APPROVED || acquisition.status === RIGHTS_STATUS.APPROVED_WITH_ATTRIBUTION)
        ) {
          assignedAsset = acquisition.asset;
          projectAssets.push(acquisition.asset);
        } else {
          console.warn(`[Storyboard] Candidate asset '${candidates[0].assetId}' skipped due to rights status: ${acquisition.status}`);
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
            attributionRequired: assignedAsset.attributionRequired ?? (assignedAsset.licenseId !== "CC0-1.0"),
            status: assignedAsset.status || "APPROVED",
            creator: assignedAsset.creator,
            sourceProvider: assignedAsset.sourceProvider,
            sourcePage: assignedAsset.sourcePage,
            licenseUrl: assignedAsset.licenseUrl,
          }
        : null,
      motion: {
        transition: isFirst ? "back.out(1.5)" : "power3.out",
        cameraPush: true,
        staggerRate: 0.12,
      },
      sfxCue: scene.sfx || (isFirst ? "hook-impact" : isLast ? "clean-ding" : "ui-pop"),
    };

    // Copy specialized metadata for diagrams, metaphors, or terminal
    if (scene.diagramNodes) beat.diagramNodes = scene.diagramNodes;
    if (scene.metaphorType) beat.metaphorType = scene.metaphorType;
    if (scene.codeSnippet) beat.codeSnippet = scene.codeSnippet;
    if (scene.highlightLines) beat.highlightLines = scene.highlightLines;
    if (scene.terminalTitle) beat.terminalTitle = scene.terminalTitle;
    if (scene.terminalLang) beat.terminalLang = scene.terminalLang;
    if (scene.steps) beat.steps = scene.steps;
    if (scene.oldWay) beat.oldWay = scene.oldWay;
    if (scene.newWay) beat.newWay = scene.newWay;

    beats.push(beat);
  }

  const storyboard = {
    version: 2,
    id: scriptData.id,
    topic: scriptData.topic || scriptData.title,
    styleProfile: "ai_simplified_purple_collage",
    totalDuration: scriptData.totalDuration,
    beatsCount: beats.length,
    beats,
    projectAssets,
    createdAt: new Date().toISOString(),
  };

  const storyboardPath = path.join(projectDir, "storyboard.json");
  await fs.writeFile(storyboardPath, JSON.stringify(storyboard, null, 2), "utf8");
  console.log(`[Storyboard] Plan generated with ${beats.length} beats: ${storyboardPath}`);

  return storyboard;
}
