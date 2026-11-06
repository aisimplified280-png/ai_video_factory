import test from "node:test";
import assert from "node:assert/strict";
import { validateDynamicScenePlan } from "../pipeline/dynamic-scene-gate.mjs";

function makeScene(id, signature = id) {
  return {
    id,
    voiceText: `Explain the ${id} mechanism as it changes state.`,
    sceneDirection: {
      narrativePurpose: `Show why ${id} matters.`,
      visualIntent: `The viewer sees ${id} change state.`,
      visualMetaphor: `A moving ${id} mechanism.`,
      primarySubject: `${id}-subject`,
      composition: {
        signature,
        shotType: "tracking macro",
        camera: { move: "tracking", target: `${id}-subject`, path: "Follow the mechanism as it changes state.", animation: { from: { x: -10, y: 0, scale: 0.96 }, to: { x: 0, y: -5, scale: 1.03 }, duration: 2, ease: "power2.out" } },
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
        { id: `${id}-subject`, role: "focal subject", purpose: "Shows the main operation.", source: "procedural", geometry: { x: 0.5, y: 0.5, width: 0.2, height: 0.12 }, appearance: { primitive: "packet", color: "#c084fc", accent: "#a3e635", label: "CACHE" }, motionRole: "Travels into the target." },
        { id: `${id}-reactor`, role: "reacting system", purpose: "Shows the result of the operation.", source: "original", geometry: { x: 0.75, y: 0.6, width: 0.18, height: 0.18 }, appearance: { primitive: "node", color: "#7c3aed", accent: "#a3e635", label: "RESULT" }, motionRole: "Changes state when the subject arrives." }
      ],
      choreography: [{
        trigger: { type: "spoken-phrase", anchor: "changes state" },
        target: `${id}-subject`,
        event: "engage-target",
        duration: 1.2,
        pathOrChange: "Travels right and locks into the receiver.",
        purpose: "Make the mechanism visible.",
        animation: { from: { x: -30, y: 0, scale: 0.8, opacity: 0 }, to: { x: 0, y: 0, scale: 1, opacity: 1 }, duration: 1.2, ease: "power3.out" },
        reactionMotions: [{ target: `${id}-reactor`, from: { scale: 0.8, opacity: 0.6 }, to: { scale: 1, opacity: 1 }, duration: 0.4, ease: "power2.out" }],
        causeAndEffect: { reacts: [`${id}-reactor`], reaction: "Receiver illuminates and rotates." },
        soundCue: { type: "impact", assetKey: "latch", offsetSeconds: 0.3, purpose: "Mark the contact point." }
      }],
      audio: {
        voiceSegment: `Explain the ${id} mechanism as it changes state.`,
        ambience: "Low mechanical room tone.",
        musicCue: "Subtle tension that resolves at payoff.",
        ducking: "Keep narration 6 dB above score and ambience."
      },
      captions: { mode: "word-synced", anchor: "lower third away from moving target", treatment: "Short phrase emphasis with high-contrast type.", placement: { x: 50, y: 86, align: "center", maxWidth: 900 }, style: { fontSize: 44, fontWeight: 800, color: "#ffffff", highlightColor: "#a3e635", activeBackgroundColor: "transparent" } },
      transition: { type: "cross-dissolve", continuityReason: "The moving subject's trajectory motivates the next shot." }
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

test("dynamic scene gate rejects a spoken-phrase trigger absent from narration", () => {
  const scene = makeScene("cache");
  scene.sceneDirection.choreography[0].trigger.anchor = "never spoken";
  const result = validateDynamicScenePlan({ productionMode: "dynamic", scenes: [scene] });
  assert.equal(result.passed, false);
  assert.ok(result.errors.some((item) => item.includes("does not occur in the narration")));
});

test("dynamic scene gate validates SFX keys against the curated sound library when supplied", () => {
  const scene = makeScene("cache");
  scene.sceneDirection.choreography[0].soundCue.assetKey = "unknown-sfx";
  const result = validateDynamicScenePlan(
    { productionMode: "dynamic", scenes: [scene] },
    { allowedSfxIds: new Set(["latch", "zoom-swish"]) }
  );
  assert.equal(result.passed, false);
  assert.ok(result.errors.some((item) => item.includes('unknown SFX asset "unknown-sfx"')));
});
