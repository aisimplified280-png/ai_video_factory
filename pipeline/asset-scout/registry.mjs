// pipeline/asset-scout/registry.mjs - Master Asset Scout & Rights Ledger Coordinator
import fs from "node:fs/promises";
import path from "node:path";
import { ROOT_DIR } from "../config.mjs";
import { auditAssetRights, computeSha256, RIGHTS_STATUS, generateCreditsReport } from "../rights-gate.mjs";
import { FixtureProvider } from "./providers/fixture-provider.mjs";
import { PixabayProvider } from "./providers/pixabay-provider.mjs";
import { OpenverseProvider } from "./providers/openverse-provider.mjs";
import { PexelsProvider } from "./providers/pexels-provider.mjs";
import { FreesoundProvider } from "./providers/freesound-provider.mjs";

export class AssetRegistry {
  constructor(options = {}) {
    this.cacheDir = options.cacheDir || path.join(ROOT_DIR, "assets", "cache");
    this.ledgerPath = options.ledgerPath || path.join(ROOT_DIR, "assets", "rights-ledger.json");
    
    // Visual providers (images, illustrations, videos)
    this.visualProviders = [
      new PixabayProvider(),
      new OpenverseProvider(),
      new PexelsProvider(),
    ];

    // Audio providers (sound effects, Foley, ambience)
    this.audioProviders = [
      new FreesoundProvider(),
    ];

    // Backward compatibility alias
    this.onlineProviders = [...this.visualProviders, ...this.audioProviders];

    // Offline fixture provider serves as deterministic fallback
    this.fallbackProviders = [
      new FixtureProvider(),
    ];

    this.scoutHistory = [];
  }

  async init() {
    await fs.mkdir(this.cacheDir, { recursive: true });
    try {
      const raw = await fs.readFile(this.ledgerPath, "utf8");
      this.ledger = JSON.parse(raw);
    } catch {
      this.ledger = { version: 1, lastUpdated: new Date().toISOString(), assets: {} };
    }
  }

  /**
   * Search across registered providers matching the media type.
   * Collects a comprehensive candidate pool from all available providers
   * before ranking and selection rather than truncating sequentially.
   */
  async searchAssets(query, { type = "image", count = 3, poolLimit = 20, offlineOnly = false } = {}) {
    const allResults = [];
    const isAudio = type === "audio" || type === "sfx";
    const activeProviders = isAudio ? this.audioProviders : this.visualProviders;

    const scoutMetric = {
      query,
      type,
      providerCounts: {},
      timestamp: new Date().toISOString(),
    };

    // 1. Query online providers matching the requested media type
    if (!offlineOnly) {
      for (const provider of activeProviders) {
        try {
          // Request up to max(3, count) from each provider to ensure diversity
          const fetchCount = Math.max(3, count);
          const results = await provider.search({ query, type, count: fetchCount });
          const hits = Array.isArray(results) ? results : [];
          scoutMetric.providerCounts[provider.name] = hits.length;
          allResults.push(...hits);
        } catch (err) {
          scoutMetric.providerCounts[provider.name] = 0;
          console.warn(`[AssetScout] Online provider '${provider.name}' search failed:`, err.message);
        }
      }
    }

    // 2. If no online results found (or offlineOnly requested), use fallback fixture provider
    if (allResults.length === 0 && !isAudio) {
      for (const provider of this.fallbackProviders) {
        try {
          const results = await provider.search({ query, type, count: Math.max(2, count) });
          const hits = Array.isArray(results) ? results : [];
          scoutMetric.providerCounts[provider.name] = hits.length;
          allResults.push(...hits);
        } catch (err) {
          console.warn(`[AssetScout] Fallback provider '${provider.name}' failed:`, err.message);
        }
      }
    }

    scoutMetric.totalCandidates = allResults.length;
    this.scoutHistory.push(scoutMetric);

    // Return the full candidate pool up to poolLimit so relevance scorer can evaluate all options
    return allResults.slice(0, poolLimit);
  }

  /**
   * Acquire, hash, audit, and register an asset into the Rights Ledger.
   * Fails closed: REVIEW_REQUIRED and REJECTED assets are strictly excluded from approved assets.
   */
  async acquireAndVerifyAsset(candidateMetadata, plannedTransformations = true) {
    await this.init();

    // 1. Audit rights first before downloading
    const rightsVerdict = auditAssetRights(candidateMetadata, plannedTransformations);
    if (rightsVerdict.status === RIGHTS_STATUS.REJECTED || rightsVerdict.status === RIGHTS_STATUS.REVIEW_REQUIRED) {
      return {
        status: rightsVerdict.status,
        reason: rightsVerdict.reason,
        asset: null,
      };
    }

    // 2. Cache / save local file with path sanitization and boundary check
    const sanitizedId = String(candidateMetadata.assetId).replace(/[^a-zA-Z0-9_-]/g, "_");
    const rawExt = candidateMetadata.downloadUrl ? path.extname(new URL(candidateMetadata.downloadUrl, "https://example.com").pathname) : "";
    const ext = rawExt || (candidateMetadata.type === "svg" ? ".svg" : ".png");
    const localCachedFile = path.resolve(this.cacheDir, `${sanitizedId}${ext}`);

    // Verify path safety (prevent directory traversal)
    if (!localCachedFile.startsWith(path.resolve(this.cacheDir))) {
      return {
        status: RIGHTS_STATUS.REJECTED,
        reason: "Invalid asset path: directory traversal detected.",
        asset: null,
      };
    }

    if (candidateMetadata.localFilePath) {
      await fs.copyFile(candidateMetadata.localFilePath, localCachedFile);
    } else if (candidateMetadata.downloadUrl) {
      const urlStr = candidateMetadata.downloadUrl;
      if (!urlStr.startsWith("https://") && !urlStr.startsWith("http://")) {
        return {
          status: RIGHTS_STATUS.REJECTED,
          reason: "Invalid download URL protocol.",
          asset: null,
        };
      }

      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 8000); // 8-second timeout
        const res = await fetch(urlStr, { signal: controller.signal });
        clearTimeout(timeoutId);

        if (!res.ok) {
          return {
            status: RIGHTS_STATUS.REJECTED,
            reason: `Download failed with HTTP status ${res.status}`,
            asset: null,
          };
        }

        const contentLength = res.headers.get("content-length");
        const maxBytes = 15 * 1024 * 1024; // 15MB limit
        if (contentLength && parseInt(contentLength, 10) > maxBytes) {
          return {
            status: RIGHTS_STATUS.REJECTED,
            reason: `Asset size (${contentLength} bytes) exceeds 15MB limit.`,
            asset: null,
          };
        }

        const buf = Buffer.from(await res.arrayBuffer());
        if (buf.length > maxBytes) {
          return {
            status: RIGHTS_STATUS.REJECTED,
            reason: `Downloaded asset exceeds 15MB limit.`,
            asset: null,
          };
        }

        await fs.writeFile(localCachedFile, buf);
      } catch (dlErr) {
        return {
          status: RIGHTS_STATUS.REJECTED,
          reason: `Network error or timeout during download: ${dlErr.message}`,
          asset: null,
        };
      }
    }

    // 3. Compute SHA-256 hash for file content identification
    const sha256 = await computeSha256(localCachedFile);

    // 4. Construct verified asset record
    const verifiedRecord = {
      ...candidateMetadata,
      status: rightsVerdict.status,
      sha256,
      cachedPath: path.relative(ROOT_DIR, localCachedFile).replace(/\\/g, "/"),
      absolutePath: localCachedFile,
      verifiedAt: new Date().toISOString(),
      rightsAuditReason: rightsVerdict.reason,
    };

    // 5. Commit to ledger
    this.ledger.assets[verifiedRecord.assetId] = verifiedRecord;
    this.ledger.lastUpdated = new Date().toISOString();
    await fs.writeFile(this.ledgerPath, JSON.stringify(this.ledger, null, 2), "utf8");

    return {
      status: rightsVerdict.status,
      asset: verifiedRecord,
    };
  }

  /**
   * Export verified credits text for approved assets.
   */
  getCredits(assetIds = []) {
    const assets = assetIds
      .map((id) => this.ledger.assets[id])
      .filter(Boolean);
    return generateCreditsReport(assets);
  }
}
