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

test("validateScriptTimingSync passes on valid chronological scenes", () => {
  const validScenes = [
    { id: "s1", voiceText: "Hello world.", startTime: 0.0, endTime: 2.5 },
    { id: "s2", voiceText: "Next point.", startTime: 2.5, endTime: 5.0 },
  ];
  const res = validateScriptTimingSync(validScenes, 5.0);
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

test("parseBlackDetectOutput correctly identifies black frame segments", () => {
  const sampleFfmpegLog = `
    [blackdetect @ 000001] black_start:1.200 black_end:2.500 black_duration:1.300
    [blackdetect @ 000001] black_start:4.100 black_end:5.200 black_duration:1.100
  `;
  const res = parseBlackDetectOutput(sampleFfmpegLog);
  assert.equal(res.status, STATUS.FAIL);
  assert.equal(res.blackSegmentsCount, 2);
  assert.equal(res.segments[0].duration, 1.3);
});

test("parseBlackDetectOutput returns PASS when no black segments detected", () => {
  const sampleFfmpegCleanLog = `frame= 650 fps=140 q=-0.0 Lsize=N/A time=00:00:21.66 bitrate=N/A`;
  const res = parseBlackDetectOutput(sampleFfmpegCleanLog);
  assert.equal(res.status, STATUS.PASS);
  assert.equal(res.blackSegmentsCount, 0);
});

test("verifyStreamProperties flags wrong dimensions or missing streams", () => {
  const badProbe = {
    streams: [
      { codec_name: "h264", codec_type: "video", width: 1920, height: 1080, r_frame_rate: "30/1" }, // Horizontal 16:9 instead of portrait 9:16
      // Missing audio stream
    ],
  };
  const res = verifyStreamProperties(badProbe);
  assert.equal(res.status, STATUS.FAIL);
  assert.ok(res.issues.some((i) => i.includes("Resolution mismatch")));
  assert.ok(res.issues.some((i) => i.includes("Missing audio stream")));
});

test("evaluateReleaseEligibility blocks release on failed rights or decode errors", () => {
  const mediaQA = { streamIntegrity: STATUS.PASS, decodeErrors: 1, blackFrameDetection: STATUS.PASS };
  const contentIntegrity = { offlineVendoredAssets: STATUS.PASS, scriptTimingSync: STATUS.PASS };
  const rightsAudit = { status: STATUS.FAIL, reason: "Unlicensed stock photo found." };

  const res = evaluateReleaseEligibility(mediaQA, contentIntegrity, rightsAudit);
  assert.equal(res.releaseEligible, false);
  assert.equal(res.blockers.length, 2);
});
