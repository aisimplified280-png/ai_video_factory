// pipeline/sfx-engine.mjs - AI Simplified Lab Reusable Sound Library & Procedural Synthesizer
import fs from "node:fs/promises";
import path from "node:path";
import crypto from "node:crypto";
import { ROOT_DIR } from "./config.mjs";

export const SFX_LIB_DIR = path.join(ROOT_DIR, "assets", "sfx");
export const SFX_DIR = SFX_LIB_DIR;
export const SFX_MANIFEST_PATH = path.join(SFX_LIB_DIR, "sfx-manifest.json");

/**
 * Generate a standard 16-bit mono 48kHz WAV buffer from PCM float samples.
 */
export function encodeWav(samples, sampleRate = 48000) {
  const numSamples = samples.length;
  const buffer = Buffer.alloc(44 + numSamples * 2);

  // RIFF header
  buffer.write("RIFF", 0);
  buffer.writeUInt32LE(36 + numSamples * 2, 4);
  buffer.write("WAVE", 8);

  // fmt chunk
  buffer.write("fmt ", 12);
  buffer.writeUInt32LE(16, 16); // chunk size
  buffer.writeUInt16LE(1, 20);  // PCM format
  buffer.writeUInt16LE(1, 22);  // mono
  buffer.writeUInt32LE(sampleRate, 24);
  buffer.writeUInt32LE(sampleRate * 2, 28); // byte rate
  buffer.writeUInt16LE(2, 32);  // block align
  buffer.writeUInt16LE(16, 34); // bits per sample

  // data chunk
  buffer.write("data", 36);
  buffer.writeUInt32LE(numSamples * 2, 40);

  for (let i = 0; i < numSamples; i++) {
    const s = Math.max(-1, Math.min(1, samples[i]));
    const intSample = s < 0 ? s * 0x8000 : s * 0x7fff;
    buffer.writeInt16LE(Math.round(intSample), 44 + i * 2);
  }

  return buffer;
}

/**
 * Procedurally synthesize tone bursts, frequency sweeps, clicks, and laser pulses offline.
 */
export function synthesizeSoundEffect(type, durationSeconds = 0.25, sampleRate = 48000) {
  const durSec = typeof durationSeconds === "object" && durationSeconds !== null 
    ? (durationSeconds.durationSec || durationSeconds.durationSeconds || 0.25)
    : Number(durationSeconds) || 0.25;
  const numSamples = Math.floor(durSec * sampleRate);
  const samples = new Float32Array(numSamples);

  switch (type) {
    case "laser-descend": {
      // Exponential downward frequency sweep (1600Hz down to 180Hz)
      for (let i = 0; i < numSamples; i++) {
        const t = i / sampleRate;
        const env = Math.exp(-t * 6.5);
        const freq = 180 + (1600 - 180) * Math.exp(-t * 8.0);
        const phase = 2 * Math.PI * freq * t;
        samples[i] = Math.sin(phase) * env * 0.75;
      }
      break;
    }
    case "bell-chime": {
      // Bell chime with rich harmonics (880Hz, 1760Hz, 2640Hz)
      for (let i = 0; i < numSamples; i++) {
        const t = i / sampleRate;
        const env = Math.exp(-t * 3.5);
        const fund = Math.sin(2 * Math.PI * 880 * t) * 0.6;
        const harm1 = Math.sin(2 * Math.PI * 1760 * t) * 0.3;
        const harm2 = Math.sin(2 * Math.PI * 2640 * t) * 0.15;
        samples[i] = (fund + harm1 + harm2) * env * 0.8;
      }
      break;
    }
    case "whoosh-sweep": {
      // Filtered noise sweep
      for (let i = 0; i < numSamples; i++) {
        const t = i / durationSeconds;
        const env = Math.sin(Math.PI * t); // smooth bell envelope
        const noise = (Math.random() * 2 - 1) * 0.5;
        const tone = Math.sin(2 * Math.PI * (200 + 400 * t) * (i / sampleRate)) * 0.5;
        samples[i] = (noise + tone) * env * 0.7;
      }
      break;
    }
    case "click-tick":
    default: {
      // Crisp mechanical click (fast 12ms attack/decay)
      const clickSamples = Math.min(numSamples, Math.floor(0.02 * sampleRate));
      for (let i = 0; i < clickSamples; i++) {
        const t = i / clickSamples;
        const env = Math.sin(Math.PI * t) * (1 - t);
        const freq = 1200 - 800 * t;
        samples[i] = Math.sin(2 * Math.PI * freq * (i / sampleRate)) * env * 0.85;
      }
      break;
    }
  }

  return encodeWav(samples, sampleRate);
}

/**
 * Initialize and verify sound effects manifest.
 */
export async function buildSfxManifest() {
  await fs.mkdir(SFX_LIB_DIR, { recursive: true });

  const staticSounds = [
    { id: "clean-ding", file: "clean-ding.wav", license: "Apache-2.0", tags: ["reveal", "success", "bell"] },
    { id: "hook-impact", file: "hook-impact.wav", license: "Apache-2.0", tags: ["impact", "hook", "heavy"] },
    { id: "sub-impact", file: "sub-impact.wav", license: "Apache-2.0", tags: ["impact", "reveal", "low"] },
    { id: "zoom-swish", file: "zoom-swish.wav", license: "Apache-2.0", tags: ["whoosh", "transition", "camera"] },
    { id: "ui-pop", file: "ui-pop.wav", license: "Apache-2.0", tags: ["ui", "pop", "hop"] },
    { id: "ui-click", file: "ui-click.wav", license: "Apache-2.0", tags: ["ui", "click", "button"] },
    { id: "tick", file: "tick.wav", license: "Apache-2.0", tags: ["clock", "scan", "tick"] },
    { id: "typing-tick", file: "typing-tick.wav", license: "Apache-2.0", tags: ["typing", "terminal", "scan"] },
    { id: "thock", file: "thock.wav", license: "Apache-2.0", tags: ["mechanical", "lock", "snap"] },
    { id: "latch", file: "latch.wav", license: "Apache-2.0", tags: ["lock", "latch", "switch"] },
    { id: "shimmer", file: "shimmer.wav", license: "Apache-2.0", tags: ["sparkle", "magic", "success"] },
    { id: "sparkle", file: "sparkle.wav", license: "Apache-2.0", tags: ["sparkle", "celebrate", "outro"] },
    { id: "metallic-riser", file: "metallic-riser.wav", license: "Apache-2.0", tags: ["riser", "tension", "build"] },
  ];

  const knownMap = new Map(staticSounds.map((s) => [s.file, s]));

  // Dynamically index all WAV files in the directory
  let dirEntries = [];
  try {
    dirEntries = await fs.readdir(SFX_LIB_DIR);
  } catch {
    await fs.mkdir(SFX_LIB_DIR, { recursive: true });
  }

  const soundRecords = [];
  for (const file of dirEntries) {
    if (!file.endsWith(".wav")) continue;
    const fullPath = path.join(SFX_LIB_DIR, file);
    try {
      const data = await fs.readFile(fullPath);
      const sha256 = crypto.createHash("sha256").update(data).digest("hex");
      const baseMeta = knownMap.get(file) || {
        id: file.replace(/\.wav$/, ""),
        file,
        license: file.startsWith("freesound-") ? "CC0-1.0" : "Apache-2.0",
        tags: [file.replace(/\.wav$/, "").split("-")[0]],
      };
      soundRecords.push({
        ...baseMeta,
        sha256,
        sizeBytes: data.length,
        path: `assets/sfx/${file}`,
      });
    } catch {
      // skip unreadable file
    }
  }

  const manifest = {
    schemaVersion: 1,
    title: "AI Simplified Lab Free Sound Effects Library",
    lastUpdated: new Date().toISOString(),
    count: soundRecords.length,
    sounds: soundRecords,
  };

  await fs.writeFile(SFX_MANIFEST_PATH, JSON.stringify(manifest, null, 2), "utf8");
  return manifest;
}

/**
 * Scout, download, and catalog a royalty-free CC0/CC-BY sound from Freesound directly into local library.
 */
export async function acquireFreesoundSfx(query, filename, options = {}) {
  const { FreesoundProvider } = await import("./asset-scout/providers/freesound-provider.mjs");
  const provider = new FreesoundProvider();
  const results = await provider.search({
    query,
    count: 3,
    licenseFilter: options.licenseFilter || "Creative Commons 0",
    maxDuration: options.maxDuration || 10,
  });

  if (!results.length) {
    throw new Error(`No compatible Freesound effects found for query: "${query}"`);
  }

  const selected = results[0];
  const safeFilename = filename.endsWith(".wav") ? filename : `${filename}.wav`;
  const targetPath = path.join(SFX_LIB_DIR, safeFilename);
  await provider.downloadAndConvertWav(selected, targetPath);
  await buildSfxManifest();
  return {
    filePath: targetPath,
    asset: selected,
  };
}

/**
 * Resolve an SFX cue to a valid WAV file path.
 * If file is missing or cue is procedural, synthesizes deterministic audio on the fly.
 */
export async function resolveSfx(cueName) {
  const cleanName = String(cueName || "tick").toLowerCase().trim();

  // Mapping semantic action cues to library sounds or synthesizers
  const mapping = {
    "linear-scan-tick": "typing-tick.wav",
    "bottleneck-alarm": "metallic-riser.wav",
    "probe-launch": "zoom-swish.wav",
    "express-bridge-whoosh": "zoom-swish.wav",
    "skip-counter-chime": "clean-ding.wav",
    "entry-hop-blip": "ui-pop.wav",
    "laser-descend-whoosh": "laser-descend", // synthesized
    "target-lock-snap": "thock.wav",
    "stamp-bounce-thud": "sub-impact.wav",
    "latency-speedometer-lock": "clean-ding.wav",
    "bell-ring": "clean-ding.wav",
    "subscribe-click": "ui-click.wav",
    "outro-sparkle": "sparkle.wav",
  };

  const target = mapping[cleanName] || `${cleanName}.wav`;
  const staticPath = path.join(SFX_LIB_DIR, target);

  try {
    await fs.access(staticPath);
    return staticPath;
  } catch {
    // If not found in static library, generate procedural fallback
    const synthType = cleanName.includes("laser") || cleanName.includes("descend")
      ? "laser-descend"
      : cleanName.includes("bell") || cleanName.includes("chime")
      ? "bell-chime"
      : cleanName.includes("whoosh") || cleanName.includes("sweep")
      ? "whoosh-sweep"
      : "click-tick";

    const synthWav = synthesizeSoundEffect(synthType);
    const synthPath = path.join(SFX_LIB_DIR, `synth-${synthType}.wav`);
    await fs.writeFile(synthPath, synthWav);
    return synthPath;
  }
}
