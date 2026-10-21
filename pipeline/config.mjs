// pipeline/config.mjs - Central configuration for AI Simplified Lab Shorts Engine
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
export const ROOT_DIR = path.resolve(__dirname, "..");

export const HYPERFRAMES_BIN = path.join(ROOT_DIR, ".favstash-studio", "runtime", "node_modules", ".bin", "hyperframes.cmd");
export const SFX_SYNC_BIN = path.join(ROOT_DIR, ".favstash-studio", "skills-source", "skills", "3-editing", "edit-video", "scripts", "sfx-sync.mjs");
export const SFX_DIR = path.join(ROOT_DIR, ".favstash-studio", "skills-source", "skills", "3-editing", "edit-video", "assets", "sfx");

export const DEFAULTS = {
  fps: 30,
  width: 1080,
  height: 1920,
  voice: "en-US-ChristopherNeural", // Reliable, authoritative tech voice
  rate: "+4%",                      // Snappy YouTube Shorts pacing
  lufs: -14,                        // YouTube standard loudness
  truePeak: -2.0,                   // True peak headroom
  duckDb: 6,                        // Voice ducking dB
};
