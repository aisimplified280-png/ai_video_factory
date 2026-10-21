// pipeline/audio-generator.mjs - Voiceover generation and exact speech timing alignment
import fs from "node:fs/promises";
import path from "node:path";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { SFX_SYNC_BIN, DEFAULTS, ROOT_DIR } from "./config.mjs";

const execFileAsync = promisify(execFile);

/**
 * Generate voice audio via Python Edge-TTS exact sentence aligner and mix sound effects.
 */
export async function generateAudio(projectDir, scriptData) {
  const voice = scriptData.voice || DEFAULTS.voice;
  const rate = scriptData.rate || DEFAULTS.rate;
  const fps = scriptData.fps || DEFAULTS.fps;

  const voiceMp3 = path.join(projectDir, "voice.mp3");
  const speechTimingsFile = path.join(projectDir, "speech-timings.json");
  const sfxCuesFile = path.join(projectDir, "sfx-cues.json");
  const audioMixWav = path.join(projectDir, "audio-mix.wav");
  const alignerScript = path.join(ROOT_DIR, "pipeline", "tts-exact-aligner.py");

  // Construct full narrative text ensuring each scene ends with a clean period
  const narrative = scriptData.scenes
    .map((s) => s.voiceText.trim().replace(/[.!?]*$/, "."))
    .join(" ");

  console.log(`[Audio] Generating Edge-TTS voiceover with exact SentenceBoundary extraction...`);
  await execFileAsync("python", [
    alignerScript,
    "--text", narrative,
    "--voice", voice,
    "--rate", rate,
    "--out-audio", voiceMp3,
    "--out-timing", speechTimingsFile,
  ]);

  // Read exact sentence boundaries
  const rawTimings = JSON.parse(await fs.readFile(speechTimingsFile, "utf8"));
  console.log(`[Audio] Extracted ${rawTimings.length} exact sentence boundaries.`);

  // Strictly enforce 1-to-1 correspondence between scene beats and speech boundaries
  if (rawTimings.length !== scriptData.scenes.length) {
    throw new Error(
      `Audio speech timing mismatch: script defines ${scriptData.scenes.length} scenes, but Edge-TTS extracted ${rawTimings.length} sentence boundaries. Each scene must map cleanly to its spoken sentence.`
    );
  }

  // Measure total audio duration via ffprobe
  const { stdout: probeOut } = await execFileAsync("ffprobe", [
    "-v", "error",
    "-show_entries", "format=duration",
    "-of", "default=noprint_wrappers=1:nokey=1",
    voiceMp3,
  ]);
  const totalVoiceDuration = parseFloat(probeOut.trim());
  
  // Pad total duration to clean integer frame boundary (with 0.4s buffer for audio tail)
  const totalDuration = Math.ceil((totalVoiceDuration + 0.4) * fps) / fps;
  const totalFrames = Math.round(totalDuration * fps);

  // Map each scene to its exact spoken boundary
  const scenesWithTiming = scriptData.scenes.map((scene, idx) => {
    const timing = rawTimings[idx];
    if (!timing || typeof timing.startTime !== "number" || typeof timing.endTime !== "number") {
      throw new Error(`Malformed speech timing entry at index ${idx}.`);
    }
    
    // Scene 0 starts at frame 0 (0.0s)
    const startTime = idx === 0 ? 0.0 : timing.startTime;
    // Next scene onset or total duration
    const nextStart = idx < scriptData.scenes.length - 1 ? rawTimings[idx + 1].startTime : totalDuration;
    const endTime = idx === scriptData.scenes.length - 1 ? totalDuration : nextStart;
    const duration = Math.max(0.2, endTime - startTime);
    
    const startFrame = Math.round(startTime * fps);
    const endFrame = Math.round(endTime * fps);

    return {
      ...scene,
      startTime,
      endTime,
      duration,
      startFrame,
      endFrame,
      durationFrames: endFrame - startFrame,
    };
  });

  // Construct SFX cues sheet aligned to exact scene onsets
  const sfxCues = [];
  scenesWithTiming.forEach((scene) => {
    if (scene.sfx) {
      sfxCues.push({
        t: Math.max(0, scene.startTime),
        sound: scene.sfx,
        label: `${scene.id}-${scene.sfx}`,
      });
    }
    if (scene.extraSfx) {
      scene.extraSfx.forEach((extra) => {
        sfxCues.push({
          t: Math.max(0, scene.startTime + extra.offset),
          sound: extra.sound,
          label: `${scene.id}-${extra.sound}`,
        });
      });
    }
  });

  const cueSheet = {
    fps,
    total: totalDuration,
    cues: sfxCues,
  };
  await fs.writeFile(sfxCuesFile, JSON.stringify(cueSheet, null, 2));

  // Run sfx-sync.mjs to mix and master to -14 LUFS
  console.log(`[Audio] Mixing ${sfxCues.length} SFX cues with voiceover (Loudness target: -14 LUFS)...`);
  await execFileAsync("node", [
    SFX_SYNC_BIN,
    "mix",
    sfxCuesFile,
    "--out", audioMixWav,
    "--voice", voiceMp3,
    "--duck", String(DEFAULTS.duckDb),
    "--lufs", String(DEFAULTS.lufs),
    "--true-peak", String(DEFAULTS.truePeak),
    "--seconds", String(totalDuration),
  ]);

  return {
    voiceMp3,
    speechTimingsFile,
    audioMixWav,
    totalDuration,
    totalFrames,
    fps,
    scenes: scenesWithTiming,
    rawTimings,
  };
}
