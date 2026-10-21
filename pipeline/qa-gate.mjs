// pipeline/qa-gate.mjs - Deterministic Quality & Governance Gate
import { execFile } from "node:child_process";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

/**
 * Gate Status Constants
 */
export const STATUS = {
  PASS: "PASS",
  FAIL: "FAIL",
  UNKNOWN: "UNKNOWN",
  REVIEW_REQUIRED: "REVIEW_REQUIRED",
  UNASSESSED: "UNASSESSED",
};

/**
 * Validate that script scenes and timing cues are structurally and chronologically aligned.
 * Fails explicitly on sentence/scene count mismatch or out-of-order timings.
 */
export function validateScriptTimingSync(scenes, totalDuration, fps = 30, rawTimings = null) {
  const issues = [];

  if (!Array.isArray(scenes) || scenes.length === 0) {
    return {
      status: STATUS.FAIL,
      issues: ["Script contains no scenes."],
    };
  }

  if (typeof totalDuration !== "number" || isNaN(totalDuration) || totalDuration <= 0) {
    issues.push(`Invalid total duration: ${totalDuration}`);
  }

  // Exact speech sentence boundary alignment check
  if (Array.isArray(rawTimings)) {
    if (rawTimings.length !== scenes.length) {
      issues.push(`Sentence boundary count mismatch: script has ${scenes.length} scenes, but speech engine returned ${rawTimings.length} sentence boundaries.`);
    }

    rawTimings.forEach((timing, idx) => {
      if (typeof timing.startTime !== "number" || isNaN(timing.startTime) || timing.startTime < 0) {
        issues.push(`Speech timing entry ${idx} has invalid startTime: ${timing.startTime}`);
      }
      if (typeof timing.endTime !== "number" || isNaN(timing.endTime) || timing.endTime <= timing.startTime) {
        issues.push(`Speech timing entry ${idx} has invalid endTime: ${timing.endTime}`);
      }
      if (idx > 0 && timing.startTime < rawTimings[idx - 1].startTime) {
        issues.push(`Speech timing entry ${idx} is chronologically out of order relative to entry ${idx - 1}`);
      }
    });
  }

  let previousEndTime = 0;
  scenes.forEach((scene, idx) => {
    if (!scene.id) issues.push(`Scene ${idx} is missing an 'id'.`);
    if (!scene.voiceText || typeof scene.voiceText !== "string" || !scene.voiceText.trim()) {
      issues.push(`Scene ${idx} has empty or missing voiceText.`);
    }

    if (typeof scene.startTime !== "number" || isNaN(scene.startTime) || scene.startTime < 0) {
      issues.push(`Scene ${idx} has invalid startTime: ${scene.startTime}`);
    }
    if (typeof scene.endTime !== "number" || isNaN(scene.endTime) || scene.endTime <= scene.startTime) {
      issues.push(`Scene ${idx} has invalid endTime (${scene.endTime}) relative to startTime (${scene.startTime})`);
    }

    // Check chronological order
    if (idx > 0 && scene.startTime < previousEndTime - 0.05) {
      issues.push(`Scene ${idx} overlaps backwards with scene ${idx - 1} (${scene.startTime}s < ${previousEndTime}s)`);
    }
    previousEndTime = scene.endTime;
  });

  return {
    status: issues.length === 0 ? STATUS.PASS : STATUS.FAIL,
    issues,
  };
}

/**
 * Parse FFmpeg blackdetect filter output to count actual black frame segments.
 * Fails closed: empty or missing filter output reports UNKNOWN, not PASS.
 */
export function parseBlackDetectOutput(ffmpegStderr) {
  if (!ffmpegStderr || typeof ffmpegStderr !== "string" || !ffmpegStderr.trim()) {
    return {
      status: STATUS.UNKNOWN,
      blackSegmentsCount: null,
      details: "No blackdetect filter output provided for inspection.",
    };
  }

  // Regex matches: [blackdetect @ ...] black_start:1.234 black_end:2.345 black_duration:1.111
  const matches = [...ffmpegStderr.matchAll(/black_start:([0-9.]+)\s+black_end:([0-9.]+)\s+black_duration:([0-9.]+)/g)];
  
  if (matches.length > 0) {
    const segments = matches.map((m) => ({
      start: parseFloat(m[1]),
      end: parseFloat(m[2]),
      duration: parseFloat(m[3]),
    }));
    return {
      status: STATUS.FAIL,
      blackSegmentsCount: matches.length,
      segments,
      details: `Detected ${matches.length} black segment(s).`,
    };
  }

  // Verify that blackdetect filter actually ran (standard ffmpeg log includes 'blackdetect' or decoded frame stream)
  if (
    !ffmpegStderr.includes("blackdetect") &&
    !ffmpegStderr.includes("Parsed_blackdetect") &&
    !ffmpegStderr.includes("frame=")
  ) {
    return {
      status: STATUS.UNKNOWN,
      blackSegmentsCount: null,
      details: "blackdetect filter was not detected in execution output.",
    };
  }

  return {
    status: STATUS.PASS,
    blackSegmentsCount: 0,
    details: "Zero black segments detected across full stream decode.",
  };
}

/**
 * Parse FFprobe stream data and verify technical constraints strictly against actual values.
 */
export function verifyStreamProperties(
  probeData,
  expectedSpecs = {
    width: 1080,
    height: 1920,
    fps: 30,
    videoCodec: "h264",
    audioCodec: "aac",
    audioSampleRate: 48000,
  }
) {
  const issues = [];
  
  if (!probeData || !Array.isArray(probeData.streams) || probeData.streams.length === 0) {
    return {
      status: STATUS.FAIL,
      issues: ["No stream metadata returned by FFprobe."],
    };
  }

  const videoStream = probeData.streams.find((s) => s.codec_name === "h264" || s.codec_type === "video");
  const audioStream = probeData.streams.find((s) => s.codec_name === "aac" || s.codec_type === "audio");

  if (!videoStream) {
    issues.push("Missing video stream.");
  } else {
    // Verify video codec
    if (expectedSpecs.videoCodec && videoStream.codec_name !== expectedSpecs.videoCodec) {
      issues.push(`Video codec mismatch: got '${videoStream.codec_name}', expected '${expectedSpecs.videoCodec}'`);
    }
    // Verify dimensions
    if (videoStream.width !== expectedSpecs.width || videoStream.height !== expectedSpecs.height) {
      issues.push(`Resolution mismatch: got ${videoStream.width}x${videoStream.height}, expected ${expectedSpecs.width}x${expectedSpecs.height}`);
    }
    // Verify framerate
    const [num, den] = (videoStream.r_frame_rate || "0/1").split("/").map(Number);
    const measuredFps = den ? num / den : 0;
    if (Math.abs(measuredFps - expectedSpecs.fps) > 0.5) {
      issues.push(`Framerate mismatch: got ${measuredFps} fps, expected ${expectedSpecs.fps} fps`);
    }
  }

  if (!audioStream) {
    issues.push("Missing audio stream.");
  } else {
    // Verify audio codec
    if (expectedSpecs.audioCodec && audioStream.codec_name !== expectedSpecs.audioCodec) {
      issues.push(`Audio codec mismatch: got '${audioStream.codec_name}', expected '${expectedSpecs.audioCodec}'`);
    }
    // Verify audio sample rate
    const sampleRate = Number(audioStream.sample_rate || 0);
    if (expectedSpecs.audioSampleRate && sampleRate !== expectedSpecs.audioSampleRate) {
      issues.push(`Audio sample rate mismatch: got ${sampleRate}Hz, expected ${expectedSpecs.audioSampleRate}Hz`);
    }
  }

  return {
    status: issues.length === 0 ? STATUS.PASS : STATUS.FAIL,
    videoStream: videoStream ? { codec: videoStream.codec_name, width: videoStream.width, height: videoStream.height, r_frame_rate: videoStream.r_frame_rate } : null,
    audioStream: audioStream ? { codec: audioStream.codec_name, sampleRate: Number(audioStream.sample_rate) } : null,
    issues,
  };
}

/**
 * Determine overall release eligibility strictly with fail-closed governance.
 * UNKNOWN, missing, or malformed checks strictly block release.
 */
export function evaluateReleaseEligibility(mediaQA, contentIntegrity, rightsAudit) {
  const blockers = [];

  // 1. Mandatory Media Checks (Fail closed: must be explicitly PASS)
  if (!mediaQA) {
    blockers.push("Missing mediaQA audit record.");
  } else {
    if (mediaQA.streamIntegrity !== STATUS.PASS) {
      blockers.push(`Stream integrity check must be PASS (got ${mediaQA.streamIntegrity || "MISSING"}).`);
    }
    if (typeof mediaQA.decodeErrors !== "number" || mediaQA.decodeErrors !== 0) {
      blockers.push(`Decode check failed: ${mediaQA.decodeErrors ?? "UNKNOWN"} errors.`);
    }
    if (mediaQA.blackFrameDetection !== STATUS.PASS) {
      blockers.push(`Black frame check must be PASS (got ${mediaQA.blackFrameDetection || "UNKNOWN"}).`);
    }
  }

  // 2. Content Integrity Checks (Fail closed)
  if (!contentIntegrity) {
    blockers.push("Missing contentIntegrity audit record.");
  } else {
    if (contentIntegrity.offlineVendoredAssets !== STATUS.PASS) {
      blockers.push(`Asset vendoring check must be PASS (got ${contentIntegrity.offlineVendoredAssets || "MISSING"}).`);
    }
    if (contentIntegrity.scriptTimingSync !== STATUS.PASS) {
      blockers.push(`Script timing sync check must be PASS (got ${contentIntegrity.scriptTimingSync || "MISSING"}).`);
    }
  }

  // 3. Rights & Governance Checks (Fail closed)
  if (!rightsAudit) {
    blockers.push("Missing rightsAudit governance record.");
  } else {
    if (rightsAudit.status !== STATUS.PASS && rightsAudit.status !== "APPROVED" && rightsAudit.status !== "APPROVED_WITH_ATTRIBUTION") {
      blockers.push(`Rights audit must be approved (got ${rightsAudit.status || "MISSING"}: ${rightsAudit.reason || "Unverified rights"}).`);
    }
  }

  const technicalChecksPassed = blockers.length === 0;

  return {
    technicalChecksPassed,
    rightsApproved: rightsAudit ? (rightsAudit.status === STATUS.PASS || rightsAudit.status === "APPROVED" || rightsAudit.status === "APPROVED_WITH_ATTRIBUTION") : false,
    editorialReviewStatus: STATUS.UNASSESSED, // Always requires human/creator review
    publishApproved: false, // Never auto-publish
    releaseEligible: blockers.length === 0,
    blockers,
  };
}
