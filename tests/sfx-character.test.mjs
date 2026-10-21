// tests/sfx-character.test.mjs - Unit tests for Free SFX Engine, Character Director & Topic Visual Strategy
import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import path from "node:path";
import { ROOT_DIR } from "../pipeline/config.mjs";
import {
  encodeWav,
  synthesizeSoundEffect,
  resolveSfx,
  buildSfxManifest,
  SFX_DIR,
} from "../pipeline/sfx-engine.mjs";
import {
  renderLabGuideSvg,
  getLabGuideCss,
  GUIDE_POSES,
} from "../pipeline/character-director.mjs";
import {
  selectTopicVisualStrategy,
  VISUAL_STRATEGIES,
  planSceneGraph,
} from "../pipeline/storyboard-planner.mjs";

test("synthesizeSoundEffect generates valid WAV buffers with RIFF headers offline", () => {
  const types = ["laser-descend", "bell-chime", "whoosh-sweep", "click-tick"];

  for (const type of types) {
    const wavBuffer = synthesizeSoundEffect(type, { durationSec: 0.3 });
    assert.ok(wavBuffer instanceof Buffer, `${type} must return a Buffer`);
    assert.ok(wavBuffer.length > 44, `${type} buffer must be larger than standard 44-byte header`);

    // Verify RIFF WAV magic bytes
    assert.equal(wavBuffer.toString("ascii", 0, 4), "RIFF", "Header must begin with RIFF");
    assert.equal(wavBuffer.toString("ascii", 8, 12), "WAVE", "Header must contain WAVE");
    assert.equal(wavBuffer.toString("ascii", 12, 16), "fmt ", "Header must contain fmt chunk");
  }
});

test("buildSfxManifest verifies and catalogs audio files in assets/sfx with SHA-256 hashes", async () => {
  const manifest = await buildSfxManifest();
  assert.ok(manifest.count >= 10, "Manifest should index at least 10 audio effects");
  assert.ok(Array.isArray(manifest.sounds), "Manifest must contain sounds array");

  // Verify manifest items contain essential fields
  for (const sound of manifest.sounds) {
    assert.ok(sound.file, `Effect ${sound.id} must have file`);
    assert.ok(sound.sha256 && sound.sha256.length === 64, `Effect ${sound.id} must have valid 64-char SHA256`);
    assert.equal(sound.license, "Apache-2.0", `Effect ${sound.id} must have license`);
  }
});

test("resolveSfx resolves existing sound and synthesizes procedural fallback for unknown cues", async () => {
  // Existing sound
  const known = await resolveSfx("hook-impact");
  assert.ok(typeof known === "string", "Known sound cue must resolve to string path");
  assert.ok(known.endsWith(".wav"), "Resolved path must be a WAV file");

  // Unknown sound should fall back to synthesized audio or default without crashing
  const fallback = await resolveSfx("unknown-future-quantum-cue");
  assert.ok(typeof fallback === "string", "Unknown cue must fall back to a valid synthesized audio path");
  assert.ok(fallback.endsWith(".wav"), "Fallback path must be a WAV file");
});

test("renderLabGuideSvg creates purposeful, lightweight, faceless SVG guide character for all poses", () => {
  const poses = Object.keys(GUIDE_POSES);
  assert.equal(poses.length, 5, "Must support 5 distinct purposeful poses");

  for (const pose of poses) {
    const svg = renderLabGuideSvg(pose, `test-guide-${pose}`);
    assert.ok(svg.includes("<svg"), `Pose ${pose} must produce valid SVG string`);
    assert.ok(svg.includes("lab-guide-character"), `Pose ${pose} must include lab-guide-character class`);
    assert.ok(svg.includes("visor-glow"), `Pose ${pose} must feature the signature glowing visor`);
    // Ensure faceless design - no realistic eyes or mouth elements
    assert.ok(!svg.includes("<mouth"), `Pose ${pose} must remain faceless`);
    assert.ok(!svg.includes("<pupil"), `Pose ${pose} must remain faceless`);
  }

  // Verify CSS styles exist and include necessary styling
  const css = getLabGuideCss();
  assert.ok(css.includes(".lab-guide-character"), "CSS must define .lab-guide-character");
  assert.ok(css.includes(".guide-side-left"), "CSS must define positioning classes");
});

test("selectTopicVisualStrategy dynamically picks topic-driven visual direction instead of rigid template", () => {
  // 1. Comparison
  const comp = selectTopicVisualStrategy("Postgres vs Vector Database Indexing");
  assert.equal(comp.strategy, VISUAL_STRATEGIES.COMPARISON_MYTHBUSTER);

  // 2. Breakthrough / News
  const news = selectTopicVisualStrategy("Anthropic Announced Claude 3.5 Sonnet Update");
  assert.equal(news.strategy, VISUAL_STRATEGIES.AI_NEWS_BREAKTHROUGH);

  // 3. Workflow / Setup
  const workflow = selectTopicVisualStrategy("How to setup local AI Video Factory pipeline CLI");
  assert.equal(workflow.strategy, VISUAL_STRATEGIES.TUTORIAL_WORKFLOW);

  // 4. Abstract concept
  const math = selectTopicVisualStrategy("High Dimensional Latent Space Embeddings & Attention");
  assert.equal(math.strategy, VISUAL_STRATEGIES.ABSTRACT_CONCEPT);

  // 5. Technical Architecture Explainer
  const tech = selectTopicVisualStrategy("Hierarchical Navigable Small World Vector Retrieval");
  assert.equal(tech.strategy, VISUAL_STRATEGIES.TECHNICAL_EXPLAINER);
});

test("planSceneGraph generates compliant scene graph for animated subscribe-outro with guide CTA", () => {
  const scene = {
    id: "outro",
    cardType: "subscribe-outro",
    visualTitle: "Subscribe for Honest AI Workflows",
    voiceText: "Subscribe to AI Simplified Lab for honest workflows.",
  };
  const beat = { beatType: "subscribe-outro" };
  const graph = planSceneGraph(scene, beat, {});

  assert.equal(graph.visualMetaphor, "channel-community-outro");
  assert.equal(graph.primarySubject, "yt-sub-btn");
  assert.ok(graph.elements.some((e) => e.id === "yt-sub-btn"));
  assert.ok(graph.elements.some((e) => e.id === "guide-outro"));
  assert.ok(graph.actions.some((a) => a.action === "animate-subscribe-conversion"));
});
