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
 * Score a candidate asset's relevance to a scene based on keywords,
 * visual intent, and spoken narration.
 */
export function scoreCandidateRelevance(candidate, scene, usedAssetIds = new Map()) {
  if (!candidate) return 0;
  
  // Rule: Prevent accidental asset repetition across scenes unless narrative continuity is explicitly justified
  if (usedAssetIds.has(candidate.assetId) && !scene.narrativeContinuityReason) {
    return -100; // Hard rejection for unjustified reuse
  }

  let score = 0;
  const candText = `${candidate.title || ""} ${candidate.tags || ""} ${candidate.assetId || ""}`.toLowerCase();
  const sceneKeywords = Array.isArray(scene.keywords)
    ? scene.keywords
    : (scene.visualIntent || scene.visualTitle || "").toLowerCase().split(/\s+/).filter((w) => w.length > 3);

  // 1. Keyword matches (+5 points per keyword)
  for (const kw of sceneKeywords) {
    const cleanKw = kw.toLowerCase().trim();
    if (cleanKw && candText.includes(cleanKw)) {
      score += 5;
    }
  }

  // 2. Visual query match (+10 points)
  if (scene.assetQuery) {
    const queryWords = scene.assetQuery.toLowerCase().split(/\s+/).filter((w) => w.length > 3);
    for (const qw of queryWords) {
      if (candText.includes(qw)) score += 3;
    }
  }

  // 3. Negative mismatch penalty for unrelated subjects (e.g. food, drinks, fashion)
  const unrelatedWords = ["cocktail", "bar", "bottle", "wine", "beer", "drink", "recipe", "food", "kitchen", "fashion", "wedding"];
  const isTechTopic = /\b(vector|graph|database|prompt|cache|token|model|server|api|code|algorithm|latency)\b/i.test(
    `${scene.visualTitle || ""} ${scene.visualIntent || ""} ${scene.spokenLine || ""}`
  );
  if (isTechTopic) {
    for (const uw of unrelatedWords) {
      if (candText.includes(uw)) {
        score -= 20; // Severe penalty for irrelevant stock media
      }
    }
  }

  return score;
}

/**
 * Plan a structured, editable storyboard from a topic or script data,
 * matching beats to visual modes, narrative purposes, and strictly approved assets.
 */
export async function planStoryboard(projectDir, scriptData, assetRegistry) {
  const beats = [];
  const scenes = scriptData.scenes || [];
  const projectAssets = [];
  const usedAssetIds = new Map(); // assetId -> [beatIndex]

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

    // Story-Aware Asset Discovery & Rights Verification
    let assignedAsset = null;
    const allowsAssets = (visualMode === "architecture-diagram" || visualMode === "asset-reveal" || visualMode === "physical-metaphor");
    const preferProcedural = scene.preferOriginalDiagram === true;

    if (assetRegistry && allowsAssets && !preferProcedural) {
      const searchQuery = scene.assetQuery || scene.visualIntent || scriptData.topic;
      const candidates = await assetRegistry.searchAssets(searchQuery, { count: 5 });

      // Rank candidates by scene relevance score
      const rankedCandidates = candidates
        .map((cand) => ({
          candidate: cand,
          score: scoreCandidateRelevance(cand, scene, usedAssetIds),
        }))
        .filter((entry) => entry.score >= 10) // Minimum relevance threshold
        .sort((a, b) => b.score - a.score);

      for (const entry of rankedCandidates) {
        const acquisition = await assetRegistry.acquireAndVerifyAsset(entry.candidate);
        if (
          acquisition.asset &&
          (acquisition.status === RIGHTS_STATUS.APPROVED || acquisition.status === RIGHTS_STATUS.APPROVED_WITH_ATTRIBUTION)
        ) {
          assignedAsset = acquisition.asset;
          projectAssets.push(acquisition.asset);
          
          const pastUsage = usedAssetIds.get(acquisition.asset.assetId) || [];
          usedAssetIds.set(acquisition.asset.assetId, [...pastUsage, idx]);
          break; // Highest-scoring compliant candidate chosen
        } else {
          console.warn(`[Storyboard] Candidate '${entry.candidate.assetId}' skipped due to rights status: ${acquisition.status}`);
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
