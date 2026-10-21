// pipeline/audio-generator.mjs - Voiceover generation and SFX mixing
import fs from "node:fs/promises";
import path from "node:path";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { SFX_SYNC_BIN, DEFAULTS } from "./config.mjs";

const execFileAsync = promisify(execFile);

/**
 * Parse VTT time string '00:00:02,137' into seconds.
 */
function parseVttTime(timeStr) {
  const [hms, ms] = timeStr.trim().split(/[,.]/);
  const parts = hms.split(":").map(Number);
  const hours = parts.length === 3 ? parts[0] : 0;
  const minutes = parts.length === 3 ? parts[1] : parts[0];
  const seconds = parts.length === 3 ? parts[2] : parts[1];
  return hours * 3600 + minutes * 60 + seconds + (Number(ms || 0) / 1000);
}

/**
 * Parse VTT content into cue objects: [{ index, start, end, text }].
 */
export function parseVtt(vttContent) {
  const lines = vttContent.split(/\r?\n/);
  const cues = [];
  let currentCue = null;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line || line === "WEBVTT") continue;

    const timeMatch = line.match(/(\d{2}:\d{2}:\d{2}[,\.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,\.]\d{3})/);
    if (timeMatch) {
      if (currentCue) cues.push(currentCue);
      currentCue = {
        start: parseVttTime(timeMatch[1]),
        end: parseVttTime(timeMatch[2]),
        text: "",
      };
    } else if (currentCue && !line.match(/^\d+$/)) {
      currentCue.text = currentCue.text ? `${currentCue.text} ${line}` : line;
    }
  }
  if (currentCue) cues.push(currentCue);
  return cues;
}

/**
 * Generate voice audio via Edge-TTS and create aligned SFX mix.
 */
export async function generateAudio(projectDir, scriptData) {
  const voice = scriptData.voice || DEFAULTS.voice;
  const rate = scriptData.rate || DEFAULTS.rate;
  const fps = scriptData.fps || DEFAULTS.fps;

  const voiceMp3 = path.join(projectDir, "voice.mp3");
  const voiceVtt = path.join(projectDir, "voice.vtt");
  const sfxCuesFile = path.join(projectDir, "sfx-cues.json");
  const audioMixWav = path.join(projectDir, "audio-mix.wav");

  // Construct full script narrative text
  const narrative = scriptData.scenes.map((s) => s.voiceText).join(" ");

  console.log(`[Audio] Generating Edge-TTS voiceover (${voice}, rate: ${rate})...`);
  await execFileAsync("edge-tts", [
    "--text", narrative,
    "--voice", voice,
    "--rate", rate,
    "--write-media", voiceMp3,
    "--write-subtitles", voiceVtt,
  ]);

  // Read and parse VTT subtitles
  const vttRaw = await fs.readFile(voiceVtt, "utf8");
  const rawCues = parseVtt(vttRaw);
  console.log(`[Audio] Generated ${rawCues.length} speech cues from Edge-TTS.`);

  // Get exact voice duration using ffprobe
  const { stdout: probeOut } = await execFileAsync("ffprobe", [
    "-v", "error",
    "-show_entries", "format=duration",
    "-of", "default=noprint_wrappers=1:nokey=1",
    voiceMp3,
  ]);
  const totalVoiceDuration = parseFloat(probeOut.trim());
  // Add 0.5s padding at the end for clean audio reverb & seamless looping
  const totalDuration = Math.ceil((totalVoiceDuration + 0.5) * fps) / fps;
  const totalFrames = Math.round(totalDuration * fps);

  // Map each scene to its speech timing
  let cueIdx = 0;
  const scenesWithTiming = scriptData.scenes.map((scene, idx) => {
    // If scene text matches or maps to a cue
    const cue = rawCues[Math.min(idx, rawCues.length - 1)] || { start: idx * 2.0, end: (idx + 1) * 2.0 };
    const startTime = idx === 0 ? 0.0 : cue.start;
    const endTime = idx === scriptData.scenes.length - 1 ? totalDuration : (rawCues[idx + 1]?.start || cue.end);
    const startFrame = Math.round(startTime * fps);
    const endFrame = Math.round(endTime * fps);
    return {
      ...scene,
      startTime,
      endTime,
      duration: endTime - startTime,
      startFrame,
      endFrame,
      durationFrames: endFrame - startFrame,
    };
  });

  // Construct SFX cues sheet
  const sfxCues = [];
  scenesWithTiming.forEach((scene, idx) => {
    if (scene.sfx) {
      sfxCues.push({
        t: Math.max(0, scene.startTime),
        sound: scene.sfx,
        label: `${scene.id}-${scene.sfx}`,
      });
    }
    // Additional mid-scene accents if specified
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
  console.log(`[Audio] Mixing ${sfxCues.length} SFX cues with voiceover and mastering to -14 LUFS...`);
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
    voiceVtt,
    audioMixWav,
    totalDuration,
    totalFrames,
    fps,
    scenes: scenesWithTiming,
    rawCues,
  };
}
