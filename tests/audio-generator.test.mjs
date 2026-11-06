import test from "node:test";
import assert from "node:assert/strict";
import { alignWordBoundariesToScenes } from "../pipeline/audio-generator.mjs";

const cue = (text, startTime, endTime) => ({
  text,
  startTime,
  endTime,
  duration: endTime - startTime,
});

test("aligns exact Edge-TTS word timings to each scene narration", () => {
  const scenes = [
    { voiceText: "The prompt is pinned in memory." },
    { voiceText: "Reuse it now!" },
  ];
  const cues = [
    cue("The", 0.04, 0.16),
    cue("prompt", 0.17, 0.44),
    cue("is", 0.45, 0.52),
    cue("pinned", 0.58, 0.84),
    cue("in", 0.87, 0.94),
    cue("memory.", 0.95, 1.28),
    cue("Reuse", 1.42, 1.73),
    cue("it", 1.74, 1.82),
    cue("now!", 1.85, 2.08),
  ];

  const result = alignWordBoundariesToScenes(scenes, cues);
  assert.equal(result.length, 2);
  assert.deepEqual(result[0].map((word) => word.text), ["The", "prompt", "is", "pinned", "in", "memory."]);
  assert.equal(result[0][3].startTime, 0.58);
  assert.equal(result[0][5].endTime, 1.28);
  assert.deepEqual(result[1].map((word) => word.text), ["Reuse", "it", "now!"]);
  assert.equal(result[1][0].startTime, 1.42);
});

test("groups multiple TTS word cues into a single hyphenated script token", () => {
  const scenes = [{ voiceText: "AI-powered systems scale." }];
  const cues = [
    cue("AI", 0.1, 0.24),
    cue("powered", 0.25, 0.57),
    cue("systems", 0.62, 0.9),
    cue("scale.", 0.94, 1.2),
  ];

  const result = alignWordBoundariesToScenes(scenes, cues);
  assert.deepEqual(result[0].map((word) => word.text), ["AI-powered", "systems", "scale."]);
  assert.equal(result[0][0].startTime, 0.1);
  assert.equal(result[0][0].endTime, 0.57);
});

test("fails closed when TTS words do not match the approved script", () => {
  const scenes = [{ voiceText: "The prompt is cached." }];
  const cues = [
    cue("The", 0, 0.1),
    cue("prompt", 0.11, 0.3),
    cue("was", 0.31, 0.4),
    cue("cached.", 0.41, 0.8),
  ];
  assert.throws(
    () => alignWordBoundariesToScenes(scenes, cues),
    /Word-boundary alignment failed at script word 3/
  );
});

test("fails closed when Edge-TTS returns unmatched extra words", () => {
  const scenes = [{ voiceText: "Cache the prompt." }];
  const cues = [
    cue("Cache", 0, 0.2),
    cue("the", 0.21, 0.3),
    cue("prompt.", 0.31, 0.6),
    cue("extra", 0.7, 0.9),
  ];
  assert.throws(
    () => alignWordBoundariesToScenes(scenes, cues),
    /unmatched word-boundary cue/
  );
});

test("fails when a word boundary has invalid or zero-length timing", () => {
  const scenes = [{ voiceText: "Cache this." }];
  const cues = [
    cue("Cache", 0.2, 0.1),
    cue("this.", 0.3, 0.5),
  ];
  assert.throws(
    () => alignWordBoundariesToScenes(scenes, cues),
    /Invalid timing for narration word "Cache"/
  );
});
