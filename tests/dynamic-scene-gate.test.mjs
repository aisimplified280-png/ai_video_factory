import test from "node:test";
import assert from "node:assert/strict";
import { validateDynamicScenePlan } from "../pipeline/dynamic-scene-gate.mjs";

function makeScene(id, signature = id) {
  return {
    id,
    voiceText: `Explain the ${id} mechanism.`,
    sceneDirection: {
      narrativePurpose: `Show why ${id} matters.`,
      visualIntent: `The viewer sees ${id} change state.`,
      visualMetaphor: `A moving ${id} mechanism.`,
      primarySubject: `${id}-subject`,
      composition: {
        signature,
        shotType: "tracking macro",
        camera: { move: "tracking", target: `${id}-subject`, path: "Follow the mechanism as it changes state." },
        depthLayers: ["environment", "moving mechanism", "focal object"],
        focalHierarchy: [`${id}-subject`, `${id}-reactor`],
        negativeSpace: "Upper left holds only short timed captions."
      },
      visualEvent: {
        setup: "The mechanism is idle.",
        action: "The moving part engages the target.",
        payoff: "The target changes state."
      },
      elements: [
        { id: `${id}-subject`, role: "focal subject", purpose: "Shows the main operation.", source: "procedural", geometry: { x: 0.5, y: 0.5 }, motionRole: "Travels into the target." },
        { id: `${id}-reactor`, role: "reacting system", purpose: "Shows the result of the operation.", source: "original", geometry: { x: 0.75, y: 0.6 }, motionRole: "Changes state when the subject arrives." }
      ],
      choreography: [{
        trigger: { type: "spoken-phrase", anchor: "changes state" },
        target: `${id}-subject`,
        event: "engage-target",
        duration: 1.2,
        pathOrChange: "Travels right and locks into the receiver.",
        purpose: "Make the mechanism visible.",
        causeAndEffect: { reacts: [`${id}-reactor`], reaction: "Receiver illuminates and rotates." },
        soundCue: { type: "impact", purpose: "Mark the contact point." }
      }],
      audio: {
        voiceSegment: `Explain the ${id} mechanism.`,
        ambience: "Low mechanical room tone.",
        musicCue: "Subtle tension that resolves at payoff.",
        ducking: "Keep narration 6 dB above score and ambience."
      },
      captions: { mode: "word-synced", anchor: "lower third away from moving target", treatment: "Short phrase emphasis with high-contrast type." },
      transition: { type: "match-cut", continuityReason: "The moving subject's trajectory motivates the next shot." }
    }
  };
}

test("dynamic scene gate accepts a fully directed, scene-specific animated plan", () => {
  const result = validateDynamicScenePlan({
    productionMode: "dynamic",
    scenes: [makeScene("cache"), makeScene("probe")]
  });
  assert.equal(result.passed, true, result.errors.join("\n"));
  assert.equal(result.uniqueCompositionCount, 2);
});

test("dynamic scene gate rejects slide/card layouts", () => {
  const scene = makeScene("cache");
  scene.cardType = "concept-explainer";
  const result = validateDynamicScenePlan({ productionMode: "dynamic", scenes: [scene] });
  assert.equal(result.passed, false);
  assert.ok(result.errors.some((item) => item.includes("cardType/template/slide layout")));
});

test("dynamic scene gate rejects duplicate scene compositions without continuity", () => {
  const result = validateDynamicScenePlan({
    productionMode: "dynamic",
    scenes: [makeScene("cache", "same-layout"), makeScene("probe", "same-layout")]
  });
  assert.equal(result.passed, false);
  assert.ok(result.errors.some((item) => item.includes("repeats Scene 1")));
});

test("dynamic scene gate rejects missing choreography and asset purpose", () => {
  const scene = makeScene("cache");
  scene.sceneDirection.choreography = [];
  scene.sceneDirection.elements[0].purpose = "";
  const result = validateDynamicScenePlan({ productionMode: "dynamic", scenes: [scene] });
  assert.equal(result.passed, false);
  assert.ok(result.errors.some((item) => item.includes("motion event")));
  assert.ok(result.errors.some((item) => item.includes("explicit narrative purpose")));
});
