// pipeline/asset-scout/registry.mjs - Master Asset Scout & Rights Ledger Coordinator
import fs from "node:fs/promises";
import path from "node:path";
import { ROOT_DIR } from "../config.mjs";
import { auditAssetRights, computeSha256, RIGHTS_STATUS, generateCreditsReport } from "../rights-gate.mjs";
import { FixtureProvider } from "./providers/fixture-provider.mjs";
import { OpenverseProvider } from "./providers/openverse-provider.mjs";
import { PexelsProvider } from "./providers/pexels-provider.mjs";

export class AssetRegistry {
  constructor(options = {}) {
    this.cacheDir = options.cacheDir || path.join(ROOT_DIR, "assets", "cache");
    this.ledgerPath = options.ledgerPath || path.join(ROOT_DIR, "assets", "rights-ledger.json");
    
    // Register providers (Offline fixture is primary default)
    this.providers = [
      new FixtureProvider(),
      new OpenverseProvider(),
      new PexelsProvider(),
    ];
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
   * Search across registered providers for topic-relevant assets.
   */
  async searchAssets(query, { type = "image", count = 2 } = {}) {
    const allResults = [];
    for (const provider of this.providers) {
      try {
        const results = await provider.search({ query, type, count });
        if (Array.isArray(results) && results.length > 0) {
          allResults.push(...results);
        }
      } catch (err) {
        console.warn(`[AssetScout] Provider '${provider.name}' search failed:`, err.message);
      }
    }
    return allResults.slice(0, count);
  }

  /**
   * Acquire, hash, audit, and register an asset into the Rights Ledger.
   */
  async acquireAndVerifyAsset(candidateMetadata, plannedTransformations = true) {
    await this.init();

    // 1. Audit rights first before downloading
    const rightsVerdict = auditAssetRights(candidateMetadata, plannedTransformations);
    if (rightsVerdict.status === RIGHTS_STATUS.REJECTED) {
      return {
        status: RIGHTS_STATUS.REJECTED,
        reason: rightsVerdict.reason,
        asset: null,
      };
    }

    // 2. Cache / save local file
    const ext = path.extname(candidateMetadata.downloadUrl) || (candidateMetadata.type === "svg" ? ".svg" : ".png");
    const localCachedFile = path.join(this.cacheDir, `${candidateMetadata.assetId}${ext}`);

    if (candidateMetadata.localFilePath) {
      await fs.copyFile(candidateMetadata.localFilePath, localCachedFile);
    } else if (candidateMetadata.downloadUrl.startsWith("http")) {
      const res = await fetch(candidateMetadata.downloadUrl);
      if (!res.ok) throw new Error(`Failed to download asset from ${candidateMetadata.downloadUrl}`);
      const buf = Buffer.from(await res.arrayBuffer());
      await fs.writeFile(localCachedFile, buf);
    }

    // 3. Compute SHA-256 hash for tamper-proof provenance
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
