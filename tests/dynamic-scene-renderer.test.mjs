import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import { renderDynamicSceneHtml, buildDynamicSceneAnimation } from "../pipeline/dynamic-scene-renderer.mjs";

const example = JSON.parse(await fs.readFile(
  new URL("../examples/dynamic-scene-plan.example.json", import.meta.url),
  "utf8"
));
const scene = example.scenes[0];

test("renders original SVG scene elements without cards or slide containers", () => {
  const html = renderDynamicSceneHtml(scene, 0);
  assert.match(html, /<svg/);
  assert.match(html, /id="prompt-cartridge"/);
  assert.match(html, /id="memory-rail"/);
  assert.match(html, /id="reuse-packet"/);
  assert.doesNotMatch(html, /collage-hero-card|purple-badge|takeaway-collage-card/);
  assert.doesNotMatch(html, /dynamic-atmosphere|M0 1430|M0 1580/);
  assert.match(html, /<rect width="1080" height="1920" fill="#0d0819"\/>/);
});

test("builds camera, subject and reaction motion from scene-specific direction", () => {
  const withTiming = {
    ...scene,
    startTime: 0,
    duration: 5,
    wordTimings: scene.voiceText.split(/\s+/).map((text, index) => ({
      text: text.replace(/[.!?]$/, ""),
      startTime: index * 0.25,
      endTime: index * 0.25 + 0.18
    }))
  };
  const script = buildDynamicSceneAnimation(withTiming, 0);
  assert.match(script, /dynamic-camera-0/);
  assert.match(script, /prompt-cartridge/);
  assert.match(script, /memory-rail/);
  assert.match(script, /reuse-packet/);
  assert.match(script, /fromTo/);
});

test("fails instead of approximating a missing spoken phrase trigger", () => {
  const broken = {
    ...scene,
    startTime: 0,
    duration: 5,
    wordTimings: [{ text: "some", startTime: 0, endTime: 0.2 }]
  };
  assert.throws(
    () => buildDynamicSceneAnimation(broken, 0),
    /Spoken-phrase trigger .* was not found/
  );
});

test("renders are independent of a fixed scene title or card type", () => {
  const alternative = JSON.parse(JSON.stringify(scene));
  alternative.sceneDirection.composition.signature = "alternate-close-orbit";
  alternative.sceneDirection.elements[0].appearance.label = "PROMPT BLOCK";
  alternative.cardType = undefined;
  const html = renderDynamicSceneHtml(alternative, 2);
  assert.match(html, /PROMPT BLOCK/);
  assert.doesNotMatch(html, /card-type|slide-layout/);
});
