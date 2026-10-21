// tests/qa-gate.test.mjs - Regression tests for QA and Governance Gate
import test from "node:test";
import assert from "node:assert/strict";
import {
  STATUS,
  validateScriptTimingSync,
  parseBlackDetectOutput,
  verifyStreamProperties,
  evaluateReleaseEligibility,
} from "../pipeline/qa-gate.mjs";

test("validateScriptTimingSync passes on valid chronological scenes and matching boundaries", () => {
  const validScenes = [
    { id: "s1", voiceText: "Hello world.", startTime: 0.0, endTime: 2.5 },
    { id: "s2", voiceText: "Next point.", startTime: 2.5, endTime: 5.0 },
  ];
  const rawTimings = [
    { startTime: 0.0, endTime: 2.4 },
    { startTime: 2.5, endTime: 4.8 },
  ];
  const res = validateScriptTimingSync(validScenes, 5.0, 30, rawTimings);
  assert.equal(res.status, STATUS.PASS);
  assert.equal(res.issues.length, 0);
});

test("validateScriptTimingSync fails when scenes overlap backwards or have NaN", () => {
  const invalidScenes = [
    { id: "s1", voiceText: "Hello world.", startTime: 0.0, endTime: 3.5 },
    { id: "s2", voiceText: "Backwards jump.", startTime: 1.0, endTime: 4.0 }, // Overlaps backwards
  ];
  const res = validateScriptTimingSync(invalidScenes, 4.0);
  assert.equal(res.status, STATUS.FAIL);
  assert.ok(res.issues.some((i) => i.includes("overlaps backwards")));
});

test("validateScriptTimingSync fails explicitly on sentence boundary count mismatch", () => {
  const scenes = [
    { id: "s1", voiceText: "First sentence.", startTime: 0.0, endTime: 2.5 },
    { id: "s2", voiceText: "Second sentence.", startTime: 2.5, endTime: 5.0 },
  ];
  const mismatchTimings = [
    { startTime: 0.0, endTime: 2.4 }, // Only 1 boundary for 2 scenes
  ];
  const res = validateScriptTimingSync(scenes, 5.0, 30, mismatchTimings);
  assert.equal(res.status, STATUS.FAIL);
  assert.ok(res.issues.some((i) => i.includes("boundary count mismatch")));
});

test("parseBlackDetectOutput correctly identifies black frame segments", () => {
  const sampleFfmpegLog = `
    [Parsed_blackdetect_0 @ 000001] black_start:1.200 black_end:2.500 black_duration:1.300
    [Parsed_blackdetect_0 @ 000001] black_start:4.100 black_end:5.200 black_duration:1.100
  `;
  const res = parseBlackDetectOutput(sampleFfmpegLog);
  assert.equal(res.status, STATUS.FAIL);
  assert.equal(res.blackSegmentsCount, 2);
  assert.equal(res.segments[0].duration, 1.3);
});

test("parseBlackDetectOutput returns PASS when blackdetect ran and zero black segments found", () => {
  const sampleFfmpegCleanLog = `[Parsed_blackdetect_0 @ 000001] auto-inserting filter 'auto_scale_0'
  frame=  787 fps=120 q=-0.0 Lsize=N/A time=00:00:26.23 bitrate=N/A`;
  const res = parseBlackDetectOutput(sampleFfmpegCleanLog);
  assert.equal(res.status, STATUS.PASS);
  assert.equal(res.blackSegmentsCount, 0);
});

test("parseBlackDetectOutput returns UNKNOWN when filter did not run or stderr is empty", () => {
  const resEmpty = parseBlackDetectOutput("");
  assert.equal(resEmpty.status, STATUS.UNKNOWN);
  assert.equal(resEmpty.blackSegmentsCount, null);

  const resUnrelated = parseBlackDetectOutput("ffmpeg version 7.0 Copyright (c) 2000-2024");
  assert.equal(resUnrelated.status, STATUS.UNKNOWN);
});

test("verifyStreamProperties flags wrong dimensions, wrong codec, or wrong sample rate", () => {
  const badProbe = {
    streams: [
      { codec_name: "vp9", codec_type: "video", width: 1920, height: 1080, r_frame_rate: "24/1" }, // Wrong codec, wrong dimensions, wrong fps
      { codec_name: "mp3", codec_type: "audio", sample_rate: "44100" }, // Wrong audio codec, wrong sample rate
    ],
  };
  const res = verifyStreamProperties(badProbe);
  assert.equal(res.status, STATUS.FAIL);
  assert.ok(res.issues.some((i) => i.includes("Video codec mismatch")));
  assert.ok(res.issues.some((i) => i.includes("Resolution mismatch")));
  assert.ok(res.issues.some((i) => i.includes("Framerate mismatch")));
  assert.ok(res.issues.some((i) => i.includes("Audio codec mismatch")));
  assert.ok(res.issues.some((i) => i.includes("Audio sample rate mismatch")));
});

test("evaluateReleaseEligibility fails closed on UNKNOWN black frames or missing checks", () => {
  // Case 1: blackFrameDetection is UNKNOWN
  const mediaQAUnknown = { streamIntegrity: STATUS.PASS, decodeErrors: 0, blackFrameDetection: STATUS.UNKNOWN };
  const contentIntegrity = { offlineVendoredAssets: STATUS.PASS, scriptTimingSync: STATUS.PASS };
  const rightsAudit = { status: STATUS.PASS, reason: "Verified." };

  const res1 = evaluateReleaseEligibility(mediaQAUnknown, contentIntegrity, rightsAudit);
  assert.equal(res1.releaseEligible, false);
  assert.ok(res1.blockers.some((b) => b.includes("Black frame check must be PASS")));

  // Case 2: Missing rights audit
  const res2 = evaluateReleaseEligibility(
    { streamIntegrity: STATUS.PASS, decodeErrors: 0, blackFrameDetection: STATUS.PASS },
    contentIntegrity,
    null
  );
  assert.equal(res2.releaseEligible, false);
  assert.ok(res2.blockers.some((b) => b.includes("Missing rightsAudit")));

  // Case 3: Visual diversity with critical issues blocks release
  const badVisualDiversity = {
    passed: false,
    criticalIssues: ["Accidental asset reuse: Beat 2 repeats asset 'xyz' without continuity."],
  };
  const res3 = evaluateReleaseEligibility(
    { streamIntegrity: STATUS.PASS, decodeErrors: 0, blackFrameDetection: STATUS.PASS },
    contentIntegrity,
    rightsAudit,
    badVisualDiversity
  );
  assert.equal(res3.releaseEligible, false);
  assert.ok(res3.blockers.some((b) => b.includes("Visual diversity check failed")));
});
