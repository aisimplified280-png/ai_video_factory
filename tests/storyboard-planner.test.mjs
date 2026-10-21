// tests/storyboard-planner.test.mjs - Unit tests for scene graph representation and motion choreography
import test from "node:test";
import assert from "node:assert/strict";
import { validateSceneGraph, planSceneGraph } from "../pipeline/storyboard-planner.mjs";
import { lintVisualDiversity } from "../pipeline/visual-linter.mjs";

test("validateSceneGraph approves compliant scene graph with valid elements, actions, and safeZone", () => {
  const compliantGraph = {
    visualMetaphor: "hnsw-express-highway",
    metaphorExplanation: "Multi-tier highway skips dense clusters via upper express lanes.",
    primarySubject: "search-probe",
    safeZone: { top: 250, bottom: 1400, left: 90, right: 990 },
    elements: [
      { id: "highway-tiers", role: "environment-layers", assetSource: "procedural-html", depth: 1 },
      { id: "search-probe", role: "moving-focal-subject", assetSource: "procedural-svg", depth: 5 },
      { id: "node-a", role: "network-node", assetSource: "procedural-svg", depth: 3 },
      { id: "node-b", role: "network-node", assetSource: "procedural-svg", depth: 3 },
    ],
    actions: [
      {
        trigger: "spoken-phrase",
        phrase: "skip dense clusters",
        action: "traverse-express-bridge",
        target: "search-probe",
        duration: 1.6,
        purpose: "Animate query probe leaping across upper express bridge from Node A to Node B",
      },
      {
        trigger: "spoken-phrase",
        phrase: "high-dimensional space",
        action: "illuminate-express-nodes",
        target: "node-b",
        duration: 1.2,
        purpose: "Illuminate express tier nodes to highlight highway shortcut efficiency",
      },
    ],
  };

  const result = validateSceneGraph(compliantGraph);
  assert.equal(result.valid, true);
  assert.equal(result.errors.length, 0);
});

test("validateSceneGraph rejects invalid visualMetaphor or missing elements", () => {
  const missingMetaphor = {
    elements: [{ id: "el-1", role: "focal-subject" }],
    actions: [{ action: "bounce", trigger: "spoken-phrase", phrase: "test", duration: 1.0, purpose: "test" }],
  };
  const res1 = validateSceneGraph(missingMetaphor);
  assert.equal(res1.valid, false);
  assert.ok(res1.errors.some((e) => e.includes("missing valid visualMetaphor")));

  const emptyElements = {
    visualMetaphor: "test-metaphor",
    elements: [],
    actions: [{ action: "bounce", trigger: "spoken-phrase", phrase: "test", duration: 1.0, purpose: "test" }],
  };
  const res2 = validateSceneGraph(emptyElements);
  assert.equal(res2.valid, false);
  assert.ok(res2.errors.some((e) => e.includes("elements must be a non-empty array")));
});

test("validateSceneGraph strictly catches undeclared action targets and invalid durations", () => {
  const badTargetGraph = {
    visualMetaphor: "test-metaphor",
    elements: [{ id: "declared-item", role: "focal-subject" }],
    actions: [
      {
        action: "leap",
        trigger: "spoken-phrase",
        phrase: "jump",
        target: "ghost-element", // Undeclared target!
        duration: 0, // Invalid duration!
        purpose: "Explain leap",
      },
    ],
  };

  const res = validateSceneGraph(badTargetGraph);
  assert.equal(res.valid, false);
  assert.ok(res.errors.some((e) => e.includes("references undeclared target element 'ghost-element'")));
  assert.ok(res.errors.some((e) => e.includes("duration")));
});

test("validateSceneGraph catches invalid safeZone coordinates", () => {
  const badSafeZone = {
    visualMetaphor: "test-metaphor",
    safeZone: { top: 1500, bottom: 200, left: 90, right: 990 }, // Inverted top/bottom!
    elements: [{ id: "item", role: "focal-subject" }],
    actions: [{ action: "fade", trigger: "spoken-phrase", phrase: "now", duration: 1.0, purpose: "test" }],
  };

  const res = validateSceneGraph(badSafeZone);
  assert.equal(res.valid, false);
  assert.ok(res.errors.some((e) => e.includes("safeZone vertical bounds invalid")));
});

test("planSceneGraph produces compliant scene graphs for vector database beats", () => {
  const beatHook = { visualMode: "hook-bold-object" };
  const sceneHook = { visualTitle: "The Vector Search Dilemma", voiceText: "Searching millions of vectors" };
  const scriptData = { topic: "Vector Database Indexing" };

  const graphHook = planSceneGraph(sceneHook, beatHook, scriptData);
  assert.equal(graphHook.visualMetaphor, "linear-scan-bottleneck");
  assert.equal(validateSceneGraph(graphHook).valid, true);

  const beatHighway = { visualMode: "physical-metaphor" };
  const sceneHighway = { visualTitle: "The Multi-Layer Graph Highway", voiceText: "multi-tier highways across high-dimensional space" };
  const graphHighway = planSceneGraph(sceneHighway, beatHighway, scriptData);
  assert.equal(graphHighway.visualMetaphor, "hnsw-express-highway");
  assert.equal(validateSceneGraph(graphHighway).valid, true);

  const beatDescent = { visualMode: "architecture-diagram" };
  const sceneDescent = { visualTitle: "HNSW Layered Navigation", voiceText: "hops across sparse upper layers descending to base" };
  const graphDescent = planSceneGraph(sceneDescent, beatDescent, scriptData);
  assert.equal(graphDescent.visualMetaphor, "coarse-to-fine-graph-descent");
  assert.equal(validateSceneGraph(graphDescent).valid, true);
});

test("lintVisualDiversity enforces sceneGraph integrity on storyboard v2", () => {
  const v2StoryboardWithoutSceneGraph = {
    version: 2,
    beats: [
      { visualMode: "hook-bold-object", visualTitle: "Hook", spokenLine: "Hook line" }, // Missing sceneGraph!
      { visualMode: "physical-metaphor", visualTitle: "Metaphor", spokenLine: "Metaphor line" },
    ],
  };

  const lintRes = lintVisualDiversity(v2StoryboardWithoutSceneGraph);
  assert.equal(lintRes.passed, false);
  assert.equal(lintRes.hasCriticalBlockers, true);
  assert.ok(lintRes.criticalIssues.some((i) => i.includes("missing required sceneGraph structure")));
});
