// tests/rights-gate.test.mjs - Unit tests for License Verification, Normalization & Asset Registry
import test from "node:test";
import assert from "node:assert/strict";
import path from "node:path";
import fs from "node:fs/promises";
import {
  auditAssetRights,
  RIGHTS_STATUS,
  generateCreditsReport,
  normalizeLicenseId,
} from "../pipeline/rights-gate.mjs";
import { FixtureProvider } from "../pipeline/asset-scout/providers/fixture-provider.mjs";
import { PixabayProvider } from "../pipeline/asset-scout/providers/pixabay-provider.mjs";
import { AssetRegistry } from "../pipeline/asset-scout/registry.mjs";
import { lintVisualDiversity } from "../pipeline/visual-linter.mjs";
import { ROOT_DIR } from "../pipeline/config.mjs";

test("normalizeLicenseId correctly normalizes valid identifiers and never assumes missing licenses", () => {
  // Valid mappings
  assert.equal(normalizeLicenseId("cc0"), "CC0-1.0");
  assert.equal(normalizeLicenseId("pdm"), "Public Domain");
  assert.equal(normalizeLicenseId("by", "4.0"), "CC-BY-4.0");
  assert.equal(normalizeLicenseId("by", "3.0"), "CC-BY-3.0");
  assert.equal(normalizeLicenseId("by"), "CC-BY-4.0");
  assert.equal(normalizeLicenseId("by-nc", "4.0"), "CC-BY-NC-4.0");
  assert.equal(normalizeLicenseId("by-nd", "4.0"), "CC-BY-ND-4.0");
  assert.equal(normalizeLicenseId("apache-2.0"), "Apache-2.0");
  assert.equal(normalizeLicenseId("mit"), "MIT");

  // Missing or invalid returns null (never guesses or assumes default)
  assert.equal(normalizeLicenseId(null), null);
  assert.equal(normalizeLicenseId(""), null);
  assert.equal(normalizeLicenseId(undefined), null);
  assert.equal(normalizeLicenseId("unverified-custom-license"), null);
});

test("auditAssetRights rejects non-commercial (NC) restrictions", () => {
  const ncAsset = {
    assetId: "asset-nc-1",
    sourceProvider: "openverse",
    licenseId: "CC-BY-NC-4.0",
    commercialUse: false,
  };
  const verdict = auditAssetRights(ncAsset);
  assert.equal(verdict.status, RIGHTS_STATUS.REJECTED);
  assert.ok(verdict.reason.includes("prohibits commercial use"));
});

test("auditAssetRights rejects no-derivatives (ND) when transformations are planned", () => {
  const ndAsset = {
    assetId: "asset-nd-1",
    sourceProvider: "openverse",
    licenseId: "CC-BY-ND-4.0",
    commercialUse: true,
    modificationsAllowed: false,
  };
  const verdict = auditAssetRights(ndAsset, true);
  assert.equal(verdict.status, RIGHTS_STATUS.REJECTED);
  assert.ok(verdict.reason.includes("prohibits modifications"));
});

test("auditAssetRights rejects assets with missing licenseId", () => {
  const unlicAsset = {
    assetId: "asset-unknown-1",
    sourceProvider: "openverse",
    licenseId: null, // Missing license
    commercialUse: true,
  };
  const verdict = auditAssetRights(unlicAsset);
  assert.equal(verdict.status, RIGHTS_STATUS.REJECTED);
  assert.ok(verdict.reason.includes("missing licenseId"));
});

test("auditAssetRights flags recognizable persons to REVIEW_REQUIRED", () => {
  const personAsset = {
    assetId: "asset-person-1",
    sourceProvider: "pexels",
    licenseId: "Pexels-License",
    commercialUse: true,
    modificationsAllowed: true,
    reviewFlags: { recognizablePerson: true },
  };
  const verdict = auditAssetRights(personAsset);
  assert.equal(verdict.status, RIGHTS_STATUS.REVIEW_REQUIRED);
  assert.ok(verdict.reason.includes("model release"));
});

test("auditAssetRights approves CC0 without attribution", () => {
  const cc0Asset = {
    assetId: "asset-cc0-1",
    sourceProvider: "offline-fixture",
    licenseId: "CC0-1.0",
    commercialUse: true,
    modificationsAllowed: true,
    attributionRequired: false,
  };
  const verdict = auditAssetRights(cc0Asset);
  assert.equal(verdict.status, RIGHTS_STATUS.APPROVED);
});

test("generateCreditsReport outputs unified schema for YouTube description and QA report", () => {
  const ccByAsset = {
    assetId: "asset-ccby-1",
    sourceProvider: "openverse",
    licenseId: "CC-BY-4.0",
    commercialUse: true,
    modificationsAllowed: true,
    attributionRequired: true,
    attributionText: "Diagram by OpenSourceContributor via Openverse (CC BY 4.0)",
    status: RIGHTS_STATUS.APPROVED_WITH_ATTRIBUTION,
    sourcePage: "https://openverse.org/image/123",
    licenseUrl: "https://creativecommons.org/licenses/by/4.0/",
  };

  const credits = generateCreditsReport([ccByAsset]);
  assert.equal(credits.hasCredits, true);
  assert.equal(credits.count, 1);
  assert.ok(credits.creditsText.includes("OpenSourceContributor"));
  assert.ok(credits.youtubeDescriptionText.includes("Visual & Media Credits"));
  assert.ok(credits.reportText.includes("CC-BY-4.0"));
});

test("AssetRegistry blocks REVIEW_REQUIRED assets from returning as approved assets", async () => {
  const testCacheDir = path.join(ROOT_DIR, "assets", "test-cache-review");
  const testLedgerPath = path.join(ROOT_DIR, "assets", "test-ledger-review.json");
  const registry = new AssetRegistry({ cacheDir: testCacheDir, ledgerPath: testLedgerPath });

  const reviewAsset = {
    assetId: "asset-review-candidate",
    sourceProvider: "pexels",
    licenseId: "Pexels-License",
    commercialUse: true,
    modificationsAllowed: true,
    downloadUrl: "https://example.com/photo.jpg",
    reviewFlags: { recognizablePerson: true },
  };

  const res = await registry.acquireAndVerifyAsset(reviewAsset);
  assert.equal(res.status, RIGHTS_STATUS.REVIEW_REQUIRED);
  assert.equal(res.asset, null); // Must NEVER return approved asset object

  // Clean up
  await fs.rm(testCacheDir, { recursive: true, force: true }).catch(() => {});
  await fs.rm(testLedgerPath, { force: true }).catch(() => {});
});

test("FixtureProvider returns offline-verified CC0 SVG assets", async () => {
  const provider = new FixtureProvider();
  const results = await provider.search({ query: "prompt caching", count: 2 });
  assert.ok(results.length > 0);
  assert.equal(results[0].licenseId, "CC0-1.0");
  assert.equal(results[0].commercialUse, true);
  assert.ok(results[0].localFilePath.endsWith(".svg"));
});

test("AssetRegistry acquires, hashes with SHA-256, and records to rights-ledger.json", async () => {
  const testCacheDir = path.join(ROOT_DIR, "assets", "test-cache");
  const testLedgerPath = path.join(ROOT_DIR, "assets", "test-ledger.json");
  const registry = new AssetRegistry({ cacheDir: testCacheDir, ledgerPath: testLedgerPath });

  const fixtureProvider = new FixtureProvider();
  const [candidate] = await fixtureProvider.search({ query: "architecture" });
  assert.ok(candidate);

  const acquisition = await registry.acquireAndVerifyAsset(candidate);
  assert.equal(acquisition.status, RIGHTS_STATUS.APPROVED);
  assert.ok(acquisition.asset.sha256);
  assert.equal(acquisition.asset.sha256.length, 64);

  // Clean up
  await fs.rm(testCacheDir, { recursive: true, force: true }).catch(() => {});
  await fs.rm(testLedgerPath, { force: true }).catch(() => {});
});

test("lintVisualDiversity flags consecutive repetitions and overused layouts", () => {
  // Case 1: Consecutive repetitive modes
  const badStoryboard = {
    beats: [
      { visualMode: "architecture-diagram", spokenLine: "Line 1", visualTitle: "Title 1" },
      { visualMode: "architecture-diagram", spokenLine: "Line 2", visualTitle: "Title 2" }, // Consecutive duplicate
      { visualMode: "concept-explainer", spokenLine: "Line 3", visualTitle: "Title 3" },
    ],
  };
  const lintRes1 = lintVisualDiversity(badStoryboard);
  assert.equal(lintRes1.passed, false);
  assert.ok(lintRes1.issues.some((i) => i.includes("Consecutive visual repetition")));

  // Case 2: Diverse storyboard passes
  const goodStoryboard = {
    beats: [
      { visualMode: "hook-bold-object", spokenLine: "Hook line", visualTitle: "Hook" },
      { visualMode: "physical-metaphor", spokenLine: "Metaphor line", visualTitle: "Metaphor" },
      { visualMode: "architecture-diagram", spokenLine: "Diagram line", visualTitle: "Diagram" },
      { visualMode: "concept-explainer", spokenLine: "Payoff line", visualTitle: "Payoff" },
    ],
  };
  const lintRes2 = lintVisualDiversity(goodStoryboard);
  assert.equal(lintRes2.passed, true);
  assert.equal(lintRes2.diversityScore, 100);
});

test("PixabayProvider returns empty array when key is missing and handles unconfigured state safely", async () => {
  const unconfiguredProvider = new PixabayProvider({ apiKey: "" });
  const results = await unconfiguredProvider.search({ query: "artificial intelligence" });
  assert.deepEqual(results, []);
});

test("PixabayProvider fetches and parses valid royalty-free illustrations with active key", async () => {
  if (!process.env.PIXABAY_API_KEY) return; // Skip if no network/key in minimal CI

  const provider = new PixabayProvider();
  const results = await provider.search({ query: "artificial intelligence", count: 2 });
  assert.ok(Array.isArray(results));
  if (results.length > 0) {
    assert.ok(results[0].assetId.startsWith("pixabay-"));
    assert.equal(results[0].licenseId, "Pixabay-Content-License");
    assert.equal(results[0].commercialUse, true);
    assert.equal(results[0].modificationsAllowed, true);
    assert.ok(results[0].downloadUrl.startsWith("http"));
  }
});

test("auditAssetRights approves Pixabay-Content-License without mandatory attribution", () => {
  const pixabayAsset = {
    licenseId: "Pixabay-Content-License",
    commercialUse: true,
    modificationsAllowed: true,
  };
  const verdict = auditAssetRights(pixabayAsset, true);
  assert.equal(verdict.status, RIGHTS_STATUS.APPROVED);
});

