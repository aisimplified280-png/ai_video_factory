// pipeline/config.mjs - Central configuration for AI Simplified Lab Shorts Engine
import path from "node:path";
import { fileURLToPath } from "node:url";

import fs from "node:fs";
import process from "node:process";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
export const ROOT_DIR = path.resolve(__dirname, "..");

// Automatically load local .env file if available in Node 20.6+
try {
  if (typeof process.loadEnvFile === "function") {
    const envPath = path.join(ROOT_DIR, ".env");
    if (fs.existsSync(envPath)) {
      process.loadEnvFile(envPath);
    }
  }
} catch {
  // Silent fallback if .env is not present
}

export const HYPERFRAMES_BIN = path.join(ROOT_DIR, ".favstash-studio", "runtime", "node_modules", ".bin", "hyperframes.cmd");
export const SFX_SYNC_BIN = path.join(ROOT_DIR, ".favstash-studio", "skills-source", "skills", "3-editing", "edit-video", "scripts", "sfx-sync.mjs");
export const SFX_DIR = path.join(ROOT_DIR, "assets", "sfx");

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
