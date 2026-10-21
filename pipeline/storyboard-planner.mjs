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
  "subscribe-outro",
]);

/**
 * Supported topic visual strategies.
 */
export const VISUAL_STRATEGIES = {
  TECHNICAL_EXPLAINER: "technical-explainer",
  ABSTRACT_CONCEPT: "abstract-concept",
  COMPARISON_MYTHBUSTER: "comparison-mythbuster",
  AI_NEWS_BREAKTHROUGH: "ai-news-breakthrough",
  TUTORIAL_WORKFLOW: "tutorial-workflow",
};

/**
 * Select purposeful visual strategy per topic rather than forcing a single template.
 */
export function selectTopicVisualStrategy(topic = "", scriptData = {}) {
  const text = `${topic} ${scriptData.title || ""} ${scriptData.description || ""}`.toLowerCase();

  if (/\b(vs|compare|comparison|myth|truth|legacy|difference)\b/i.test(text)) {
    return {
      strategy: VISUAL_STRATEGIES.COMPARISON_MYTHBUSTER,
      rationale: "Topic contrasts competing paradigms; employs asymmetric comparison collages, side-by-side metrics, and match-cut transformations.",
    };
  }

  if (/\b(release|breakthrough|announced|benchmark|sota|update|news)\b/i.test(text)) {
    return {
      strategy: VISUAL_STRATEGIES.AI_NEWS_BREAKTHROUGH,
      rationale: "Topic reports an industry milestone; employs editorial headline cards, empirical evidence badges, and breakthrough reveal stamps.",
    };
  }

  if (/\b(how to|guide|tutorial|setup|install|cli|command|pipeline)\b/i.test(text)) {
    return {
      strategy: VISUAL_STRATEGIES.TUTORIAL_WORKFLOW,
      rationale: "Topic teaches an operational workflow; employs syntax terminals, sequential checklist badges, and guide character cues.",
    };
  }

  if (/\b(embeddings|latent|diffusion|attention|transformer|math)\b/i.test(text)) {
    return {
      strategy: VISUAL_STRATEGIES.ABSTRACT_CONCEPT,
      rationale: "Topic explains mathematical or multidimensional dynamics; employs custom physical metaphors, geometric fields, and interactive token tracks.",
    };
  }

  // Default: Technical architecture explainer
  return {
    strategy: VISUAL_STRATEGIES.TECHNICAL_EXPLAINER,
    rationale: "Topic explores computational systems or data structures; employs layered topology diagrams, moving search probes, and verified benchmarks.",
  };
}

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
 * Multi-criteria asset evaluation engine.
 * Evaluates candidates across semantic relevance, visual suitability, scene participation, and licensing.
 * If external candidates fall below threshold or the concept is abstract computational architecture,
 * explicitly decides on bespoke procedural SVG / graphics and records the rationale.
 */
export function evaluateAssetChoice(candidates, scene, usedAssetIds = new Map()) {
  const isTechTopic = /\b(vector|graph|database|prompt|cache|token|model|server|api|code|algorithm|latency|hnsw|hash)\b/i.test(
    `${scene.visualTitle || ""} ${scene.visualIntent || ""} ${scene.voiceText || scene.spokenLine || ""}`
  );

  if (scene.preferOriginalDiagram === true) {
    return {
      selectedCandidate: null,
      decision: "bespoke-procedural-svg",
      reason: "Scene explicitly prioritizes interactive procedural SVG geometry over stock imagery.",
    };
  }

  if (!Array.isArray(candidates) || candidates.length === 0) {
    return {
      selectedCandidate: null,
      decision: "bespoke-procedural-svg",
      reason: "No external stock candidates found. Generated bespoke procedural vector graphic.",
    };
  }

  const scored = candidates.map((cand) => {
    const relevanceScore = scoreCandidateRelevance(cand, scene, usedAssetIds);

    // Visual suitability (SVG/vector format preferred for scaling and transparent-background choreography)
    let visualSuitability = 0;
    if (cand.type === "svg" || (cand.downloadUrl && cand.downloadUrl.endsWith(".svg"))) {
      visualSuitability += 20;
    } else if (cand.type === "illustration") {
      visualSuitability += 10;
    }

    // Participation score (Can this asset be animated as an interactive element in choreography?)
    const participation = cand.type === "svg" ? 15 : 5;

    // License safety bonus
    const licenseBonus = cand.licenseId === "CC0-1.0" ? 10 : 5;

    const totalScore = relevanceScore + visualSuitability + participation + licenseBonus;
    return { candidate: cand, totalScore, relevanceScore };
  });

  scored.sort((a, b) => b.totalScore - a.totalScore);
  const best = scored[0];

  if (!best || best.totalScore < 25 || best.relevanceScore < 5) {
    return {
      selectedCandidate: null,
      decision: "bespoke-procedural-svg",
      reason: isTechTopic
        ? "Abstract computational concept requires bespoke interactive SVG geometry; stock media is insufficiently relevant or cannot participate in scene choreography."
        : "Stock candidates failed relevance and scene-participation thresholds; choosing procedural artwork.",
    };
  }

  return {
    selectedCandidate: best.candidate,
    decision: "approved-stock",
    score: best.totalScore,
    reason: `Candidate '${best.candidate.assetId}' selected with multi-criteria score ${best.totalScore}.`,
  };
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

    // Story-Aware Asset Discovery & Multi-Criteria Evaluation
    let assignedAsset = null;
    let assetDecision = "bespoke-procedural-svg";
    let assetDecisionReason = "Scene uses bespoke procedural graphics.";
    const allowsAssets = (visualMode === "architecture-diagram" || visualMode === "asset-reveal" || visualMode === "physical-metaphor");

    if (assetRegistry && allowsAssets) {
      const searchQuery = scene.assetQuery || scene.visualIntent || scriptData.topic;
      const candidates = await assetRegistry.searchAssets(searchQuery, { count: 5 });
      const evaluation = evaluateAssetChoice(candidates, scene, usedAssetIds);

      assetDecision = evaluation.decision;
      assetDecisionReason = evaluation.reason;

      if (evaluation.selectedCandidate) {
        const acquisition = await assetRegistry.acquireAndVerifyAsset(evaluation.selectedCandidate);
        if (
          acquisition.asset &&
          (acquisition.status === RIGHTS_STATUS.APPROVED || acquisition.status === RIGHTS_STATUS.APPROVED_WITH_ATTRIBUTION)
        ) {
          assignedAsset = acquisition.asset;
          projectAssets.push(acquisition.asset);
          
          const pastUsage = usedAssetIds.get(acquisition.asset.assetId) || [];
          usedAssetIds.set(acquisition.asset.assetId, [...pastUsage, idx]);
        } else {
          console.warn(`[Storyboard] Candidate '${evaluation.selectedCandidate.assetId}' skipped due to rights status: ${acquisition.status}`);
          assetDecision = "bespoke-procedural-svg";
          assetDecisionReason = `Candidate rights verification yielded ${acquisition.status}; defaulted to bespoke procedural graphic.`;
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
      assetDecision,
      assetDecisionReason,
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

    // Attach structured scene graph and motion actions
    beat.sceneGraph = planSceneGraph(scene, beat, scriptData);

    beats.push(beat);
  }

  const topicStrategy = selectTopicVisualStrategy(scriptData.topic || scriptData.title, scriptData);

  const storyboard = {
    version: 2,
    id: scriptData.id,
    topic: scriptData.topic || scriptData.title,
    visualStrategy: topicStrategy.strategy,
    strategyRationale: topicStrategy.rationale,
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

/**
 * Validate a scene-graph structure.
 * Returns { valid: boolean, errors: string[] }
 */
export function validateSceneGraph(sceneGraph) {
  const errors = [];
  if (!sceneGraph || typeof sceneGraph !== "object") {
    return { valid: false, errors: ["Missing sceneGraph object."] };
  }
  if (!sceneGraph.visualMetaphor || typeof sceneGraph.visualMetaphor !== "string") {
    errors.push("sceneGraph missing valid visualMetaphor string.");
  }
  if (sceneGraph.safeZone) {
    const { top, bottom, left, right } = sceneGraph.safeZone;
    if (typeof top !== "number" || typeof bottom !== "number" || top >= bottom) {
      errors.push("sceneGraph safeZone vertical bounds invalid (top must be < bottom).");
    }
    if (typeof left !== "number" || typeof right !== "number" || left >= right) {
      errors.push("sceneGraph safeZone horizontal bounds invalid (left must be < right).");
    }
  }
  if (!Array.isArray(sceneGraph.elements) || sceneGraph.elements.length === 0) {
    errors.push("sceneGraph elements must be a non-empty array.");
  } else {
    sceneGraph.elements.forEach((el, elIdx) => {
      if (!el.id) errors.push(`Element [${elIdx}] missing id.`);
      if (!el.role) errors.push(`Element '${el.id || elIdx}' missing role.`);
    });
  }
  if (!Array.isArray(sceneGraph.actions) || sceneGraph.actions.length === 0) {
    errors.push("sceneGraph actions must be a non-empty array.");
  } else {
    const elementIds = new Set((sceneGraph.elements || []).map((e) => e.id));
    sceneGraph.actions.forEach((act, actIdx) => {
      if (!act.action) errors.push(`Action [${actIdx}] missing action type.`);
      if (!act.trigger) errors.push(`Action '${act.action || actIdx}' missing trigger.`);
      if (act.trigger === "spoken-phrase" && (!act.phrase || !act.phrase.trim())) {
        errors.push(`Action '${act.action || actIdx}' with spoken-phrase trigger missing valid phrase anchor.`);
      }
      if (typeof act.duration !== "number" || act.duration <= 0) {
        errors.push(`Action '${act.action || actIdx}' missing valid duration.`);
      }
      if (!act.purpose) errors.push(`Action '${act.action || actIdx}' missing narrative purpose.`);
      if (act.target && !elementIds.has(act.target)) {
        errors.push(`Action '${act.action}' references undeclared target element '${act.target}'.`);
      }
    });
  }
  if (sceneGraph.primarySubject) {
    const elementIds = new Set((sceneGraph.elements || []).map((e) => e.id));
    if (!elementIds.has(sceneGraph.primarySubject)) {
      errors.push(`sceneGraph primarySubject '${sceneGraph.primarySubject}' not found in elements.`);
    }
  }
  if (sceneGraph.transition && sceneGraph.transition.continuity) {
    const { persistentElement, morphTarget } = sceneGraph.transition.continuity;
    if (persistentElement && typeof persistentElement !== "string") {
      errors.push("transition continuity persistentElement must be a string.");
    }
    if (morphTarget && typeof morphTarget !== "string") {
      errors.push("transition continuity morphTarget must be a string.");
    }
  }
  return { valid: errors.length === 0, errors };
}

/**
 * Plan a structured scene graph with objects, roles, and choreographed actions.
 */
export function planSceneGraph(scene, beat, scriptData) {
  // If scene already defines an explicit valid sceneGraph, preserve it
  if (scene.sceneGraph) {
    const val = validateSceneGraph(scene.sceneGraph);
    if (val.valid) return scene.sceneGraph;
  }

  const titleLower = `${scene.visualTitle || ""} ${scriptData.topic || ""}`.toLowerCase();
  const isVector = titleLower.includes("vector") || titleLower.includes("hnsw");
  const mode = beat.visualMode || beat.beatType || scene.cardType;

  const defaultSafeZone = { top: 250, bottom: 1400, left: 90, right: 990 };

  if (mode === "hook" || mode === "hook-bold-object") {
    if (isVector) {
      return {
        visualMetaphor: "linear-scan-bottleneck",
        metaphorExplanation: "Dense coordinate point cloud inspected one by one causes scanning stall and bottleneck collapse.",
        primarySubject: "linear-search-marker",
        safeZone: defaultSafeZone,
        elements: [
          { id: "vector-dense-field", role: "environment", assetSource: "procedural-svg", depth: 1 },
          {
            id: "linear-search-marker",
            role: "moving-focal-subject",
            assetSource: "procedural-svg",
            depth: 3,
            initialState: { x: -280, y: 0, scale: 0.8, opacity: 0 },
            finalState: { x: 260, y: 0, scale: 1.1, opacity: 1 }
          },
          { id: "bottleneck-indicator", role: "status-overlay", assetSource: "procedural-html", depth: 4 },
          { id: "search-counter", role: "parameter-metrics", assetSource: "procedural-html", depth: 2 },
        ],
        actions: [
          {
            trigger: "spoken-phrase",
            phrase: "Searching millions",
            audioAnchor: "Searching millions",
            action: "step-scan-points",
            target: "linear-search-marker",
            duration: 1.8,
            sfxCue: "linear-scan-tick",
            purpose: "Demonstrate marker checking vector points one-by-one linearly",
            causeAndEffect: {
              triggerElement: "linear-search-marker",
              reactingElements: ["vector-dense-field", "search-counter"],
              reaction: "advance-scanned-points"
            }
          },
          {
            trigger: "spoken-phrase",
            phrase: "unscalable bottleneck",
            audioAnchor: "unscalable bottleneck",
            action: "stall-and-flash-bottleneck",
            target: "bottleneck-indicator",
            duration: 1.4,
            sfxCue: "bottleneck-alarm",
            purpose: "Visually emphasize search stalling and bottleneck collapse",
            causeAndEffect: {
              triggerElement: "bottleneck-indicator",
              reactingElements: ["linear-search-marker", "search-counter"],
              reaction: "halt-and-alarm"
            }
          },
        ],
        transition: {
          type: "match-cut-compress",
          persistingElements: ["linear-search-marker"],
          continuity: {
            persistentElement: "linear-search-marker",
            morphTarget: "search-probe",
            transformType: "compress-to-highway-probe"
          },
          duration: 0.4
        }
      };
    }

    return {
      visualMetaphor: "attention-hook",
      metaphorExplanation: "Radial burst focal object establishes architectural problem context.",
      primarySubject: "hero-emblem",
      safeZone: defaultSafeZone,
      elements: [
        { id: "hero-emblem", role: "focal-subject", assetSource: "procedural-svg", depth: 3 },
        { id: "glow-ring", role: "atmosphere", assetSource: "procedural-svg", depth: 1 },
        { id: "statement-box", role: "supporting-card", assetSource: "procedural-html", depth: 2 },
      ],
      actions: [
        {
          trigger: "spoken-phrase",
          phrase: scene.voiceText ? scene.voiceText.split(" ").slice(0, 3).join(" ") : "Attention",
          audioAnchor: "Attention",
          action: "burst-emblem",
          target: "hero-emblem",
          duration: 0.8,
          sfxCue: "hero-burst",
          purpose: "Capture viewer visual focus with radial burst",
          causeAndEffect: {
            triggerElement: "hero-emblem",
            reactingElements: ["glow-ring", "statement-box"],
            reaction: "expand-and-settle"
          }
        },
      ],
    };
  }

  if (mode === "physical-metaphor") {
    if (scene.metaphorType === "hnsw-highway" || isVector) {
      return {
        visualMetaphor: "hnsw-express-highway",
        metaphorExplanation: "Multi-tier hierarchical graph skips dense clusters like express lanes on a highway.",
        primarySubject: "search-probe",
        safeZone: defaultSafeZone,
        elements: [
          { id: "highway-tiers", role: "environment-layers", assetSource: "procedural-html", depth: 1 },
          { id: "express-bridge-path", role: "navigation-path", assetSource: "procedural-svg", depth: 2 },
          { id: "node-a", role: "network-node", assetSource: "procedural-svg", depth: 3 },
          { id: "node-b", role: "network-node", assetSource: "procedural-svg", depth: 3 },
          {
            id: "search-probe",
            role: "moving-focal-subject",
            assetSource: "procedural-svg",
            depth: 5,
            initialState: { x: 0, y: 0, scale: 0.8, opacity: 0 },
            finalState: { x: 380, y: 0, scale: 1.1, opacity: 1 }
          },
          { id: "express-arc", role: "navigation-path", assetSource: "procedural-svg", depth: 2 },
          { id: "skip-counter", role: "performance-meter", assetSource: "procedural-html", depth: 4 },
        ],
        actions: [
          {
            trigger: "spoken-phrase",
            phrase: "multi-tier highways",
            audioAnchor: "multi-tier highways",
            action: "enter-probe-and-lock-node-a",
            target: "search-probe",
            duration: 0.8,
            sfxCue: "probe-launch",
            purpose: "Probe enters upper express tier and locks onto Node A",
            causeAndEffect: {
              triggerElement: "search-probe",
              reactingElements: ["node-a"],
              reaction: "pulse-node-green"
            }
          },
          {
            trigger: "spoken-phrase",
            phrase: "skip dense clusters",
            audioAnchor: "skip dense clusters",
            action: "traverse-express-bridge",
            target: "search-probe",
            duration: 1.6,
            sfxCue: "express-bridge-whoosh",
            purpose: "Animate query probe leaping across upper express bridge from Node A to Node B",
            causeAndEffect: {
              triggerElement: "search-probe",
              reactingElements: ["express-bridge-path", "express-arc", "node-b"],
              reaction: "illuminate-path-and-settle"
            }
          },
          {
            trigger: "spoken-phrase",
            phrase: "high-dimensional space",
            audioAnchor: "high-dimensional space",
            action: "illuminate-express-nodes",
            target: "node-b",
            duration: 1.2,
            sfxCue: "skip-counter-chime",
            purpose: "Illuminate express tier nodes to highlight highway shortcut efficiency",
            causeAndEffect: {
              triggerElement: "node-b",
              reactingElements: ["skip-counter"],
              reaction: "stamp-skip-metric"
            }
          },
        ],
        transition: {
          type: "layer-descent-prep",
          persistingElements: ["search-probe"],
          continuity: {
            persistentElement: "search-probe",
            morphTarget: "query-descent-probe",
            transformType: "bridge-to-vertical-descent"
          },
          duration: 0.3
        }
      };
    }

    return {
      visualMetaphor: "token-conveyor",
      metaphorExplanation: "Memory conveyor shows static prefix pinned in warm RAM while dynamic query hits instantly.",
      primarySubject: "dynamic-query-item",
      safeZone: defaultSafeZone,
      elements: [
        { id: "conveyor-track", role: "motion-path", assetSource: "procedural-svg", depth: 1 },
        { id: "static-pinned-item", role: "fixed-focal-subject", assetSource: "procedural-html", depth: 2 },
        { id: "dynamic-query-item", role: "moving-focal-subject", assetSource: "procedural-html", depth: 3 },
      ],
      actions: [
        {
          trigger: "spoken-phrase",
          phrase: "stores your system instructions",
          audioAnchor: "stores your system instructions",
          action: "pin-cache-ram",
          target: "static-pinned-item",
          duration: 1.0,
          sfxCue: "cache-pin-snap",
          purpose: "Lock static system prompt into warm ephemeral RAM",
          causeAndEffect: {
            triggerElement: "static-pinned-item",
            reactingElements: ["conveyor-track"],
            reaction: "lock-slot-color"
          }
        },
        {
          trigger: "spoken-phrase",
          phrase: "read directly from cache",
          audioAnchor: "read directly from cache",
          action: "instant-query-hit",
          target: "dynamic-query-item",
          duration: 1.2,
          sfxCue: "cache-hit-ding",
          purpose: "Slide query into match position with instant latency hit",
          causeAndEffect: {
            triggerElement: "dynamic-query-item",
            reactingElements: ["static-pinned-item"],
            reaction: "flash-cache-match"
          }
        },
      ],
    };
  }

  if (mode === "architecture-diagram") {
    if (isVector) {
      return {
        visualMetaphor: "coarse-to-fine-graph-descent",
        metaphorExplanation: "Search hops across sparse upper tiers before descending to dense base layer to lock nearest vector.",
        primarySubject: "query-descent-probe",
        safeZone: defaultSafeZone,
        elements: [
          {
            id: "query-descent-probe",
            role: "moving-focal-subject",
            assetSource: "procedural-svg",
            depth: 5,
            initialState: { x: 0, y: -30, scale: 0.5, opacity: 0 },
            finalState: { x: 0, y: 310, scale: 1.2, opacity: 1 }
          },
          { id: "entry-node-l2", role: "network-node", assetSource: "procedural-svg", depth: 3 },
          { id: "intermediate-node-l1", role: "network-node", assetSource: "procedural-svg", depth: 3 },
          { id: "target-beacon-l0", role: "nearest-target", assetSource: "procedural-svg", depth: 4 },
          { id: "descent-beam", role: "descent-path", assetSource: "procedural-svg", depth: 2 },
          { id: "convergence-ring", role: "status-overlay", assetSource: "procedural-svg", depth: 4 },
        ],
        actions: [
          {
            trigger: "spoken-phrase",
            phrase: "hops across sparse upper layers",
            audioAnchor: "hops across sparse upper layers",
            action: "activate-entry-hop",
            target: "entry-node-l2",
            duration: 0.9,
            sfxCue: "entry-hop-blip",
            purpose: "Hit entry point in sparse top layer",
            causeAndEffect: {
              triggerElement: "query-descent-probe",
              reactingElements: ["entry-node-l2"],
              reaction: "ripple-entry-node"
            }
          },
          {
            trigger: "spoken-phrase",
            phrase: "descending to the base",
            audioAnchor: "descending to the base",
            action: "descend-to-base",
            target: "query-descent-probe",
            duration: 1.4,
            sfxCue: "laser-descent-whoosh",
            purpose: "Animate probe sliding down vertical descent beam to intermediate and base tiers",
            causeAndEffect: {
              triggerElement: "query-descent-probe",
              reactingElements: ["descent-beam", "intermediate-node-l1"],
              reaction: "illuminate-descent-track"
            }
          },
          {
            trigger: "spoken-phrase",
            phrase: "nearest neighbor convergence",
            audioAnchor: "nearest neighbor convergence",
            action: "lock-target-nearest-vector",
            target: "target-beacon-l0",
            duration: 1.2,
            sfxCue: "target-lock-snap",
            purpose: "Target beacon pulses with neon flare while surrounding points dim down",
            causeAndEffect: {
              triggerElement: "target-beacon-l0",
              reactingElements: ["convergence-ring"],
              reaction: "expand-target-shockwave"
            }
          },
        ],
        transition: {
          type: "converged-focus",
          continuity: {
            persistentElement: "target-beacon-l0",
            morphTarget: "rule-stamp",
            transformType: "target-radiate-to-stamp"
          },
          duration: 0.4
        }
      };
    }

    return {
      visualMetaphor: "pipeline-data-flow",
      metaphorExplanation: "Node topology animates data flow through modular components.",
      primarySubject: "flow-packet",
      safeZone: defaultSafeZone,
      elements: [
        { id: "flow-packet", role: "moving-focal-subject", assetSource: "procedural-svg", depth: 3 },
        { id: "flow-nodes", role: "network-node", assetSource: "procedural-html", depth: 2 },
      ],
      actions: [
        {
          trigger: "spoken-phrase",
          phrase: "flow",
          audioAnchor: "flow",
          action: "advance-flow-packet",
          target: "flow-packet",
          duration: 1.5,
          sfxCue: "packet-flow",
          purpose: "Trace data movement through topology nodes",
          causeAndEffect: {
            triggerElement: "flow-packet",
            reactingElements: ["flow-nodes"],
            reaction: "pulse-node-stream"
          }
        },
      ],
    };
  }

  if (mode === "subscribe-outro") {
    return {
      visualMetaphor: "channel-community-outro",
      metaphorExplanation: "Branded channel outro with faceless guide character directing viewer to interactive subscribe action.",
      primarySubject: "yt-sub-btn",
      safeZone: defaultSafeZone,
      elements: [
        { id: "brand-crest", role: "brand-emblem", assetSource: "procedural-html", depth: 1 },
        { id: "yt-sub-btn", role: "focal-subject", assetSource: "procedural-html", depth: 3 },
        { id: "yt-bell-btn", role: "action-trigger", assetSource: "procedural-html", depth: 3 },
        { id: "guide-outro", role: "audience-guide", assetSource: "procedural-svg", depth: 4 },
      ],
      actions: [
        {
          trigger: "spoken-phrase",
          phrase: "Subscribe",
          audioAnchor: "Subscribe",
          action: "animate-subscribe-conversion",
          target: "yt-sub-btn",
          duration: 0.9,
          sfxCue: "ui-click",
          purpose: "Animate subscribe button transition into subscribed state",
          causeAndEffect: {
            triggerElement: "yt-sub-btn",
            reactingElements: ["yt-bell-btn", "guide-outro"],
            reaction: "ring-bell-and-wave"
          }
        },
      ],
      transition: { type: "fade-out", duration: 0.3 }
    };
  }

  // Default: concept explainer / payoff
  return {
    visualMetaphor: "architectural-production-rule",
    metaphorExplanation: "Definitive architectural rule stamp establishes concrete engineering parameters and latency limits.",
    primarySubject: "rule-stamp",
    safeZone: defaultSafeZone,
    elements: [
      { id: "rule-stamp", role: "focal-subject", assetSource: "procedural-html", depth: 3 },
      { id: "param-metrics", role: "parameter-metrics", assetSource: "procedural-html", depth: 2 },
      { id: "latency-gauge", role: "performance-meter", assetSource: "procedural-html", depth: 4 },
    ],
    actions: [
      {
        trigger: "spoken-phrase",
        phrase: scene.voiceText ? scene.voiceText.split(" ").slice(0, 3).join(" ") : "Balancing",
        audioAnchor: "Balancing",
        action: "stamp-rule-entrance",
        target: "rule-stamp",
        duration: 0.7,
        sfxCue: "stamp-bounce-thud",
        purpose: "Drop definitive production rule stamp with physical bounce",
        causeAndEffect: {
          triggerElement: "rule-stamp",
          reactingElements: ["param-metrics"],
          reaction: "settle-and-reveal"
        }
      },
      {
        trigger: "spoken-phrase",
        phrase: "latency",
        audioAnchor: "latency",
        action: "lock-latency-meter",
        target: "latency-gauge",
        duration: 1.0,
        sfxCue: "latency-speedometer-lock",
        purpose: "Lock metric to sub-millisecond status",
        causeAndEffect: {
          triggerElement: "latency-gauge",
          reactingElements: ["rule-stamp"],
          reaction: "glow-pass-confirmation"
        }
      },
    ],
    transition: { type: "final-hold", duration: 0.5 }
  };
}
