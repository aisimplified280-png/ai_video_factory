// pipeline/asset-scout/providers/freesound-provider.mjs - Freesound API Adapter
import process from "node:process";
import fs from "node:fs/promises";
import path from "node:path";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { normalizeLicenseId } from "../../rights-gate.mjs";

const execFileAsync = promisify(execFile);

/**
 * Freesound API Adapter for free sound effects discovery and preview retrieval.
 * Docs: https://freesound.org/docs/api/
 */
export class FreesoundProvider {
  name = "freesound";

  constructor(options = {}) {
    this.apiKey = options.apiKey !== undefined ? options.apiKey : (process.env.FREESOUND_API_KEY || "");
  }

  /**
   * Search Freesound API for audio effects.
   * @param {Object} params
   * @param {string} params.query - Search keywords (e.g. "click", "whoosh", "bell")
   * @param {number} [params.count=3] - Number of results to request
   * @param {string} [params.licenseFilter='Creative Commons 0'] - License filter ('Creative Commons 0' or 'Attribution')
   * @param {number} [params.maxDuration=10] - Maximum audio duration in seconds
   * @returns {Promise<Array>}
   */
  async search({ query, count = 3, licenseFilter = "Creative Commons 0", maxDuration = 10 }) {
    const key = this.apiKey;
    if (!key) return [];

    try {
      const url = new URL("https://freesound.org/apiv2/search/text/");
      url.searchParams.set("token", key);
      url.searchParams.set("query", query);
      url.searchParams.set("page_size", String(Math.max(1, Math.min(15, count))));
      url.searchParams.set("fields", "id,name,tags,description,license,previews,username,duration,url");

      // Construct filter ensuring non-commercial sounds are excluded
      let filterString = `duration:[0.1 TO ${maxDuration}]`;
      if (licenseFilter) {
        filterString += ` license:"${licenseFilter}"`;
      }
      url.searchParams.set("filter", filterString);

      const response = await fetch(url.toString(), {
        headers: { "User-Agent": "AISimplifiedLab-VideoFactory/1.0" },
      });

      if (!response.ok) return [];

      const data = await response.json();
      if (!Array.isArray(data.results)) return [];

      return data.results.map((hit) => {
        const rawLicense = hit.license || "";
        const normLicense = normalizeLicenseId(rawLicense) || "UNKNOWN";
        const isNc = rawLicense.includes("nc") || rawLicense.includes("noncommercial");
        const isNd = rawLicense.includes("nd") || rawLicense.includes("noderivs");
        const isCc0 = normLicense === "CC0-1.0" || rawLicense.includes("zero");

        const previewUrl = hit.previews?.["preview-hq-mp3"] || hit.previews?.["preview-hq-ogg"] || "";

        return {
          assetId: `freesound-${hit.id}`,
          type: "audio",
          title: hit.name || `Freesound ${hit.id}`,
          sourceProvider: "freesound",
          sourcePage: hit.url || `https://freesound.org/people/${hit.username}/sounds/${hit.id}/`,
          downloadUrl: previewUrl,
          creator: hit.username || "Freesound Creator",
          licenseId: normLicense,
          licenseUrl: rawLicense,
          commercialUse: !isNc,
          modificationsAllowed: !isNd,
          attributionRequired: !isCc0,
          attributionText: isCc0
            ? ""
            : `Sound "${hit.name}" by ${hit.username} via Freesound (${normLicense})`,
          durationSec: Number(hit.duration) || 0,
          tags: Array.isArray(hit.tags) ? hit.tags : [],
          reviewFlags: {
            recognizablePerson: false,
            trademarkLogo: false,
            sensitiveContent: false,
          },
        };
      });
    } catch (err) {
      console.warn(`[AssetScout:Freesound] Search failed:`, err.message);
      return [];
    }
  }

  /**
   * Download a sound preview and convert it to 16-bit 48kHz WAV using ffmpeg.
   * @param {Object} soundAsset - Scouted asset object with downloadUrl
   * @param {string} destinationWavPath - Destination WAV file path
   * @returns {Promise<string>} Destination path
   */
  async downloadAndConvertWav(soundAsset, destinationWavPath) {
    if (!soundAsset.downloadUrl) {
      throw new Error(`Asset ${soundAsset.assetId} has no downloadUrl`);
    }

    const tempDir = path.dirname(destinationWavPath);
    await fs.mkdir(tempDir, { recursive: true });
    const tempFile = path.join(tempDir, `temp-${soundAsset.assetId}.mp3`);

    // Download audio stream
    const res = await fetch(soundAsset.downloadUrl);
    if (!res.ok) {
      throw new Error(`Failed to download Freesound preview: HTTP ${res.status}`);
    }
    const arrayBuffer = await res.arrayBuffer();
    await fs.writeFile(tempFile, Buffer.from(arrayBuffer));

    // Convert via ffmpeg to standard 48kHz 16-bit PCM mono WAV
    try {
      await execFileAsync("ffmpeg", [
        "-v", "error",
        "-y",
        "-i", tempFile,
        "-ac", "1",
        "-ar", "48000",
        "-c:a", "pcm_s16le",
        destinationWavPath,
      ]);
    } finally {
      // Clean up temporary MP3
      try {
        await fs.unlink(tempFile);
      } catch {
        // ignore cleanup error
      }
    }

    return destinationWavPath;
  }
}
