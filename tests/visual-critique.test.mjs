// tests/visual-critique.test.mjs - Visual Critique, Asset Intelligence, and Polish Checklist Tests
import test from "node:test";
import assert from "node:assert/strict";
import { evaluateAssetChoice } from "../pipeline/storyboard-planner.mjs";
import { critiqueRenderedSceneMoments, CRITIQUE_SEVERITY } from "../pipeline/visual-critique.mjs";
import { evaluateReleaseEligibility, STATUS } from "../pipeline/qa-gate.mjs";

test("evaluateAssetChoice prioritizes bespoke procedural SVG when preferOriginalDiagram is true", () => {
  const scene = {
    visualTitle: "Vector Graph Highway",
    preferOriginalDiagram: true,
  };
  const candidates = [
    { assetId: "stock-highway", title: "Highway road", type: "image", licenseId: "CC0-1.0" },
  ];

  const result = evaluateAssetChoice(candidates, scene);
  assert.equal(result.decision, "bespoke-procedural-svg");
  assert.equal(result.selectedCandidate, null);
  assert.match(result.reason, /prioritizes interactive procedural SVG/);
});

test("evaluateAssetChoice rejects low-relevance stock media and falls back to bespoke procedural graphic", () => {
  const scene = {
    visualTitle: "HNSW Vector Database Indexing",
    visualIntent: "Hierarchical graph navigation",
    spokenLine: "Hierarchical Navigable Small World graphs skip dense clusters",
  };
  const irrelevantCandidates = [
    { assetId: "bar-cocktail", title: "Cocktail drink at bar", type: "image", licenseId: "CC0-1.0" },
    { assetId: "wedding-fashion", title: "Wedding dress fashion", type: "image", licenseId: "CC0-1.0" },
  ];

  const result = evaluateAssetChoice(irrelevantCandidates, scene);
  assert.equal(result.decision, "bespoke-procedural-svg");
  assert.equal(result.selectedCandidate, null);
  assert.match(result.reason, /Abstract computational concept requires bespoke interactive SVG/);
});

test("evaluateAssetChoice selects high-scoring vector SVG candidate with verified license", () => {
  const scene = {
    visualTitle: "Server Database Infrastructure",
    visualIntent: "Database server cluster",
    keywords: ["server", "database", "cluster"],
  };
  const candidates = [
    {
      assetId: "svg-database-cluster",
      title: "Vector database server cluster icon",
      type: "svg",
      licenseId: "CC0-1.0",
      downloadUrl: "https://example.com/database.svg",
    },
  ];

  const result = evaluateAssetChoice(candidates, scene);
  assert.equal(result.decision, "approved-stock");
  assert.equal(result.selectedCandidate.assetId, "svg-database-cluster");
  assert.ok(result.score >= 35);
});

test("critiqueRenderedSceneMoments flags P0 on safe zone encroachment", () => {
  const projectData = {
    scenes: [
      {
        sceneGraph: {
          visualMetaphor: "encroached-header",
          safeZone: { top: 120, bottom: 1400, left: 90, right: 990 }, // Encroaches into top < 200px
          elements: [{ id: "elem1", role: "focal" }],
          actions: [{ action: "move", trigger: "timestamp", duration: 1, purpose: "test", causeAndEffect: { triggerElement: "elem1", reactingElements: ["elem1"], reaction: "move" } }],
        },
      },
    ],
  };

  const critique = critiqueRenderedSceneMoments(projectData, []);
  assert.equal(critique.passed, false);
  assert.ok(critique.p0Count >= 1);
  const p0 = critique.issues.find((i) => i.severity === CRITIQUE_SEVERITY.P0);
  assert.ok(p0);
  assert.match(p0.message, /encroaches into YouTube Shorts top channel bar/);
});

test("critiqueRenderedSceneMoments flags P1 on broken transition continuity", () => {
  const projectData = {
    scenes: [
      {
        sceneGraph: {
          visualMetaphor: "scene-1",
          safeZone: { top: 250, bottom: 1400, left: 90, right: 990 },
          elements: [{ id: "marker-a", role: "focal" }],
          actions: [{ action: "move", trigger: "timestamp", duration: 1, purpose: "test", causeAndEffect: { triggerElement: "marker-a", reactingElements: ["marker-a"], reaction: "pulse" } }],
          transition: {
            continuity: {
              persistentElement: "ghost-element", // Not in elements
              morphTarget: "probe-b",
            },
          },
        },
      },
      {
        sceneGraph: {
          visualMetaphor: "scene-2",
          safeZone: { top: 250, bottom: 1400, left: 90, right: 990 },
          elements: [{ id: "probe-b", role: "focal" }],
          actions: [{ action: "move", trigger: "timestamp", duration: 1, purpose: "test", causeAndEffect: { triggerElement: "probe-b", reactingElements: ["probe-b"], reaction: "pulse" } }],
        },
      },
    ],
  };

  const critique = critiqueRenderedSceneMoments(projectData, []);
  assert.ok(critique.p1Count >= 1);
  const p1 = critique.issues.find((i) => i.severity === CRITIQUE_SEVERITY.P1 && i.category === "broken-continuity");
  assert.ok(p1);
  assert.match(p1.message, /ghost-element/);
});

test("critiqueRenderedSceneMoments passes on compliant scene graphs and full 12-moment coverage", () => {
  const projectData = {
    scenes: [
      {
        sceneGraph: {
          visualMetaphor: "linear-scan",
          safeZone: { top: 250, bottom: 1400, left: 90, right: 990 },
          elements: [{ id: "search-marker", role: "focal" }, { id: "cloud", role: "bg" }],
          actions: [
            {
              action: "step-scan",
              trigger: "timestamp",
              duration: 1,
              sfxCue: "tick",
              purpose: "Scan points",
              causeAndEffect: { triggerElement: "search-marker", reactingElements: ["cloud"], reaction: "advance" },
            },
          ],
          transition: {
            continuity: { persistentElement: "search-marker", morphTarget: "probe", transformType: "compress" },
          },
        },
      },
      {
        sceneGraph: {
          visualMetaphor: "highway",
          safeZone: { top: 250, bottom: 1400, left: 90, right: 990 },
          elements: [{ id: "probe", role: "focal" }, { id: "node-a", role: "node" }],
          actions: [
            {
              action: "traverse",
              trigger: "timestamp",
              duration: 1,
              sfxCue: "whoosh",
              purpose: "Traverse bridge",
              causeAndEffect: { triggerElement: "probe", reactingElements: ["node-a"], reaction: "illuminate" },
            },
          ],
        },
      },
    ],
  };

  const frames = ["e1.png", "a1.png", "p1.png", "e2.png", "a2.png", "p2.png"];
  const critique = critiqueRenderedSceneMoments(projectData, frames);
  assert.equal(critique.passed, true);
  assert.equal(critique.p0Count, 0);
  assert.equal(critique.p1Count, 0);
  assert.ok(critique.score >= 90);
});

test("evaluateReleaseEligibility blocks release if visual critique has P0 blockers", () => {
  const mediaQA = { streamIntegrity: STATUS.PASS, decodeErrors: 0, blackFrameDetection: STATUS.PASS };
  const contentIntegrity = { offlineVendoredAssets: STATUS.PASS, scriptTimingSync: STATUS.PASS };
  const rightsAudit = { status: STATUS.PASS, reason: "Approved" };
  const visualDiversity = { passed: true, criticalIssues: [] };

  const failedCritique = {
    passed: false,
    p0Count: 1,
    issues: [
      {
        severity: "P0_CRITICAL_BLOCKER",
        message: "Safe zone encroached into top channel bar",
      },
    ],
  };

  const result = evaluateReleaseEligibility(mediaQA, contentIntegrity, rightsAudit, visualDiversity, failedCritique);
  assert.equal(result.releaseEligible, false);
  assert.ok(result.blockers.some((b) => b.includes("Visual critique identified 1 P0 critical blocker(s)")));
});
