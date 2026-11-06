// pipeline/audio-generator.mjs - Exact word-aligned narration, SFX and optional licensed music
import fs from "node:fs/promises";
import path from "node:path";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { SFX_SYNC_BIN, DEFAULTS, ROOT_DIR } from "./config.mjs";

const execFileAsync = promisify(execFile);

function normalizeWord(value) {
  return String(value ?? "")
    .normalize("NFKC")
    .toLocaleLowerCase()
    .replace(/[^\p{L}\p{N}]+/gu, "");
}

function getSceneTokens(scenes) {
  const tokens = [];
  scenes.forEach((scene, sceneIndex) => {
    if (typeof scene.voiceText !== "string" || !scene.voiceText.trim()) {
      throw new Error(`Scene ${sceneIndex + 1} has no narration text.`);
    }
    for (const raw of scene.voiceText.trim().split(/\s+/)) {
      const normalized = normalizeWord(raw);
      if (normalized) tokens.push({ sceneIndex, text: raw, normalized });
    }
  });
  return tokens;
}

/**
 * Align expected script tokens to Edge-TTS WordBoundary cues. A cue may
 * contain one or more fragments of the same script token (e.g. a hyphenated
 * or contracted token), which are grouped to one interval. A single cue
 * that spans multiple script tokens is rejected rather than guessed.
 */
export function alignWordBoundariesToScenes(scenes, wordCues) {
  if (!Array.isArray(scenes) || scenes.length === 0) {
    throw new Error("Cannot align narration: no scenes were supplied.");
  }
  if (!Array.isArray(wordCues) || wordCues.length === 0) {
    throw new Error("Edge-TTS returned no word boundaries; exact captions cannot be generated.");
  }

  const expected = getSceneTokens(scenes);
  const actual = wordCues
    .map((cue, sourceIndex) => ({
      ...cue,
      sourceIndex,
      normalized: normalizeWord(cue.text),
    }))
    .filter((cue) => cue.normalized);

  const grouped = scenes.map(() => []);
  let cursor = 0;

  for (let expectedIndex = 0; expectedIndex < expected.length; expectedIndex += 1) {
    const token = expected[expectedIndex];
    let combined = "";
    const selected = [];

    while (cursor < actual.length && combined.length < token.normalized.length) {
      const cue = actual[cursor];
      combined += cue.normalized;
      selected.push(cue);
      cursor += 1;
      if (combined === token.normalized) break;
      if (!token.normalized.startsWith(combined)) break;
    }

    if (combined !== token.normalized) {
      const found = selected.map((cue) => cue.text).join(" ") || actual[cursor]?.text || "<end>";
      throw new Error(
        `Word-boundary alignment failed at script word ${expectedIndex + 1} "${token.text}": ` +
        `Edge-TTS returned "${found}". Check pronunciation/script tokenization; no timing fallback is allowed.`
      );
    }

    const startTime = Number(selected[0]?.startTime);
    const endTime = Number(selected[selected.length - 1]?.endTime);
    if (!Number.isFinite(startTime) || !Number.isFinite(endTime) || endTime <= startTime) {
      throw new Error(`Invalid timing for narration word "${token.text}" at script word ${expectedIndex + 1}.`);
    }

    grouped[token.sceneIndex].push({
      text: token.text,
      startTime,
      endTime,
      duration: endTime - startTime,
    });
  }

  if (cursor !== actual.length) {
    const extra = actual.slice(cursor, cursor + 5).map((cue) => cue.text).join(" ");
    throw new Error(`Edge-TTS returned ${actual.length - cursor} unmatched word-boundary cue(s): "${extra}".`);
  }

  grouped.forEach((sceneWords, sceneIndex) => {
    if (sceneWords.length === 0) {
      throw new Error(`Scene ${sceneIndex + 1} has no aligned word timings.`);
    }
  });

  return grouped;
}

function resolveMusicFile(music) {
  if (!music) return null;
  if (music.usageRightsConfirmed !== true ||
      typeof music.licenseId !== "string" || !music.licenseId.trim() ||
      typeof music.source !== "string" || !music.source.trim()) {
    throw new Error(
      "Music bed blocked: usageRightsConfirmed, licenseId and source are required. " +
      "Add only a rights-cleared track (for example, one whose YouTube Audio Library terms you have checked)."
    );
  }
  if (typeof music.filePath !== "string" || !music.filePath.trim()) {
    throw new Error("Music bed blocked: music.filePath is required.");
  }

  const musicRoot = path.resolve(ROOT_DIR, "assets", "music");
  const resolved = path.resolve(ROOT_DIR, music.filePath);
  if (!resolved.startsWith(musicRoot + path.sep)) {
    throw new Error("Music bed blocked: track must be stored inside assets/music/.");
  }
  return resolved;
}

async function mixLicensedMusic({ sourceMix, musicPath, outputPath, totalDuration }) {
  await fs.access(musicPath);
  const ffmpegFilter = [
    "[1:a]volume=0.18[music]",
    "[music][0:a]sidechaincompress=threshold=0.025:ratio=8:attack=18:release=420[duckedmusic]",
    "[0:a][duckedmusic]amix=inputs=2:duration=first:dropout_transition=0,alimiter=limit=0.89125[aout]",
  ].join(";");

  await execFileAsync("ffmpeg", [
    "-v", "error",
    "-y",
    "-i", sourceMix,
    "-stream_loop", "-1",
    "-i", musicPath,
    "-filter_complex", ffmpegFilter,
    "-map", "[aout]",
    "-t", String(totalDuration),
    "-ar", "48000",
    "-ac", "2",
    "-c:a", "pcm_s16le",
    outputPath,
  ]);

  const { stdout } = await execFileAsync("ffprobe", [
    "-v", "error",
    "-show_entries", "stream=codec_name,sample_rate,channels",
    "-of", "json",
    outputPath,
  ]);
  const probe = JSON.parse(stdout);
  const stream = probe.streams?.[0];
  if (stream?.sample_rate !== "48000" || stream?.channels !== 2) {
    throw new Error("Music mix failed its 48kHz stereo verification.");
  }
  return outputPath;
}

/**
 * Generate Edge-TTS once, align every word to each scene, and mix the
 * existing licensed SFX library under narration. An optional local music
 * bed is included only when its rights metadata is explicitly confirmed.
 */
export async function generateAudio(projectDir, scriptData) {
  const voice = scriptData.voice || DEFAULTS.voice;
  const rate = scriptData.rate || DEFAULTS.rate;
  const fps = scriptData.fps || DEFAULTS.fps;

  const voiceMp3 = path.join(projectDir, "voice.mp3");
  const wordTimingsFile = path.join(projectDir, "speech-words.json");
  const sceneTimingsFile = path.join(projectDir, "speech-timings.json");
  const sfxCuesFile = path.join(projectDir, "sfx-cues.json");
  const sfxMixWav = path.join(projectDir, "audio-sfx-voice.wav");
  const audioMixWav = path.join(projectDir, "audio-mix.wav");
  const alignerScript = path.join(ROOT_DIR, "pipeline", "tts-exact-aligner.py");

  const narrative = scriptData.scenes
    .map((scene) => scene.voiceText.trim().replace(/[.!?]*$/, "."))
    .join(" ");

  console.log("[Audio] Generating Edge-TTS voiceover with exact WordBoundary extraction...");
  await execFileAsync("python", [
    alignerScript,
    "--text", narrative,
    "--voice", voice,
    "--rate", rate,
    "--out-audio", voiceMp3,
    "--out-words", wordTimingsFile,
  ]);

  const wordCues = JSON.parse(await fs.readFile(wordTimingsFile, "utf8"));
  const wordTimingsByScene = alignWordBoundariesToScenes(scriptData.scenes, wordCues);

  const { stdout: probeOut } = await execFileAsync("ffprobe", [
    "-v", "error",
    "-show_entries", "format=duration",
    "-of", "default=noprint_wrappers=1:nokey=1",
    voiceMp3,
  ]);
  const totalVoiceDuration = Number.parseFloat(probeOut.trim());
  if (!Number.isFinite(totalVoiceDuration) || totalVoiceDuration <= 0) {
    throw new Error("Could not verify the generated narration duration.");
  }
  const totalDuration = Math.ceil((totalVoiceDuration + 0.4) * fps) / fps;
  const totalFrames = Math.round(totalDuration * fps);

  // Every scene starts at its first actual word. The prior scene remains
  // visible during natural pauses; word captions end at the actual final word.
  const scenesWithTiming = scriptData.scenes.map((scene, sceneIndex) => {
    const words = wordTimingsByScene[sceneIndex];
    const startTime = sceneIndex === 0 ? 0 : words[0].startTime;
    const nextStart = sceneIndex < scriptData.scenes.length - 1
      ? wordTimingsByScene[sceneIndex + 1][0].startTime
      : totalDuration;
    const endTime = Math.max(startTime + 0.2, nextStart);
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
      wordTimings: words,
    };
  });

  const rawTimings = scenesWithTiming.map((scene) => ({
    text: scene.voiceText,
    startTime: scene.startTime,
    endTime: scene.endTime,
    duration: scene.duration,
  }));
  await fs.writeFile(sceneTimingsFile, JSON.stringify(rawTimings, null, 2), "utf8");

  const sfxCues = [];
  scenesWithTiming.forEach((scene) => {
    if (scene.sfx) {
      sfxCues.push({
        t: Math.max(0, scene.startTime),
        sound: scene.sfx,
        label: `${scene.id}-${scene.sfx}`,
      });
    }
    for (const extra of scene.extraSfx || []) {
      const offset = Number(extra.offset);
      if (!Number.isFinite(offset) || offset < 0) {
        throw new Error(`Invalid scene-relative SFX offset for scene "${scene.id}".`);
      }
      sfxCues.push({
        t: Math.max(0, scene.startTime + offset),
        sound: extra.sound,
        label: `${scene.id}-${extra.sound}`,
      });
    }
  });

  await fs.writeFile(sfxCuesFile, JSON.stringify({
    fps,
    total: totalDuration,
    cues: sfxCues,
  }, null, 2));

  console.log(`[Audio] Mixing ${sfxCues.length} licensed SFX cue(s) with narration at ${DEFAULTS.lufs} LUFS...`);
  await execFileAsync("node", [
    SFX_SYNC_BIN,
    "mix",
    sfxCuesFile,
    "--out", sfxMixWav,
    "--voice", voiceMp3,
    "--duck", String(DEFAULTS.duckDb),
    "--lufs", String(DEFAULTS.lufs),
    "--true-peak", String(DEFAULTS.truePeak),
    "--seconds", String(totalDuration),
  ]);

  const musicPath = resolveMusicFile(scriptData.audio?.music || scriptData.music || null);
  if (musicPath) {
    console.log("[Audio] Adding the rights-confirmed music bed with narration sidechain ducking...");
    await mixLicensedMusic({
      sourceMix: sfxMixWav,
      musicPath,
      outputPath: audioMixWav,
      totalDuration,
    });
  } else {
    await fs.copyFile(sfxMixWav, audioMixWav);
  }

  return {
    voiceMp3,
    speechTimingsFile: sceneTimingsFile,
    wordTimingsFile,
    sfxCuesFile,
    audioMixWav,
    totalDuration,
    totalFrames,
    fps,
    scenes: scenesWithTiming,
    rawTimings,
    wordTimingsByScene,
    musicIncluded: Boolean(musicPath),
    musicLicense: musicPath ? scriptData.audio?.music || scriptData.music : null,
  };
}
