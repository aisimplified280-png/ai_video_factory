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
};

/**
 * Validate that script scenes and timing cues are structurally aligned.
 */
export function validateScriptTimingSync(scenes, totalDuration, fps = 30) {
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
    if (idx > 0 && scene.startTime < previousEndTime - 0.1) {
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
 */
export function parseBlackDetectOutput(ffmpegStderr) {
  if (!ffmpegStderr || typeof ffmpegStderr !== "string") {
    return {
      status: STATUS.UNKNOWN,
      blackSegmentsCount: 0,
      details: "No filter output provided for inspection.",
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

  return {
    status: STATUS.PASS,
    blackSegmentsCount: 0,
    details: "Zero black segments detected.",
  };
}

/**
 * Parse FFprobe stream data and verify technical constraints.
 */
export function verifyStreamProperties(probeData, expectedResolution = { width: 1080, height: 1920 }, expectedFps = 30) {
  const issues = [];
  
  if (!probeData || !Array.isArray(probeData.streams)) {
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
    if (videoStream.width !== expectedResolution.width || videoStream.height !== expectedResolution.height) {
      issues.push(`Resolution mismatch: got ${videoStream.width}x${videoStream.height}, expected ${expectedResolution.width}x${expectedResolution.height}`);
    }
    const [num, den] = (videoStream.r_frame_rate || "0/1").split("/").map(Number);
    const measuredFps = den ? num / den : 0;
    if (Math.abs(measuredFps - expectedFps) > 0.5) {
      issues.push(`Framerate mismatch: got ${measuredFps} fps, expected ${expectedFps} fps`);
    }
  }

  if (!audioStream) {
    issues.push("Missing audio stream.");
  }

  return {
    status: issues.length === 0 ? STATUS.PASS : STATUS.FAIL,
    videoStream: videoStream ? { codec: videoStream.codec_name, width: videoStream.width, height: videoStream.height } : null,
    audioStream: audioStream ? { codec: audioStream.codec_name, sampleRate: audioStream.sample_rate } : null,
    issues,
  };
}

/**
 * Determine overall release eligibility based on audit results.
 */
export function evaluateReleaseEligibility(mediaQA, contentIntegrity, rightsAudit) {
  const blockers = [];

  // Mandatory Media Checks
  if (mediaQA.streamIntegrity !== STATUS.PASS) blockers.push("Media stream integrity failed.");
  if (mediaQA.decodeErrors > 0) blockers.push(`Found ${mediaQA.decodeErrors} decode errors.`);
  if (mediaQA.blackFrameDetection === STATUS.FAIL) blockers.push("Video contains unintended black frames.");

  // Content Integrity Checks
  if (contentIntegrity.offlineVendoredAssets !== STATUS.PASS) {
    blockers.push(`Asset vendoring check failed: ${contentIntegrity.offlineVendoredAssets}`);
  }
  if (contentIntegrity.scriptTimingSync !== STATUS.PASS) {
    blockers.push("Script timing and scene synchronization check failed.");
  }

  // Rights & Governance Checks
  if (rightsAudit && rightsAudit.status === STATUS.FAIL) {
    blockers.push(`Rights audit failed: ${rightsAudit.reason || "Unlicensed or prohibited assets found."}`);
  }
  if (rightsAudit && rightsAudit.status === STATUS.REVIEW_REQUIRED) {
    blockers.push(`Rights audit requires human review: ${rightsAudit.reason}`);
  }

  return {
    releaseEligible: blockers.length === 0,
    blockers,
  };
}
