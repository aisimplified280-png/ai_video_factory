// tests/rights-gate.test.mjs - Unit tests for License Verification & Asset Registry
import test from "node:test";
import assert from "node:assert/strict";
import path from "node:path";
import fs from "node:fs/promises";
import {
  auditAssetRights,
  RIGHTS_STATUS,
  generateCreditsReport,
} from "../pipeline/rights-gate.mjs";
import { FixtureProvider } from "../pipeline/asset-scout/providers/fixture-provider.mjs";
import { AssetRegistry } from "../pipeline/asset-scout/registry.mjs";
import { ROOT_DIR } from "../pipeline/config.mjs";

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

test("auditAssetRights approves CC-BY with attribution and formats credits report", () => {
  const ccByAsset = {
    assetId: "asset-ccby-1",
    sourceProvider: "openverse",
    licenseId: "CC-BY-4.0",
    commercialUse: true,
    modificationsAllowed: true,
    attributionRequired: true,
    attributionText: "Diagram by OpenSourceContributor via Openverse (CC BY 4.0)",
  };
  const verdict = auditAssetRights(ccByAsset);
  assert.equal(verdict.status, RIGHTS_STATUS.APPROVED_WITH_ATTRIBUTION);

  const credits = generateCreditsReport([{ ...ccByAsset, status: verdict.status }]);
  assert.equal(credits.hasCredits, true);
  assert.ok(credits.creditsText.includes("OpenSourceContributor"));
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

  const outcome = await registry.acquireAndVerifyAsset(candidate);
  assert.equal(outcome.status, RIGHTS_STATUS.APPROVED);
  assert.ok(outcome.asset.sha256 && outcome.asset.sha256.length === 64);

  // Verify ledger file was created and contains the asset record
  const ledgerRaw = await fs.readFile(testLedgerPath, "utf8");
  const ledger = JSON.parse(ledgerRaw);
  assert.ok(ledger.assets[candidate.assetId]);

  // Clean test artifacts
  await fs.rm(testCacheDir, { recursive: true, force: true });
  await fs.rm(testLedgerPath, { force: true });
});
