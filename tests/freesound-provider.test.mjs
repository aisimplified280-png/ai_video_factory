// tests/freesound-provider.test.mjs - Unit tests for Freesound API Adapter & Audio Scouting
import { test } from "node:test";
import assert from "node:assert/strict";
import { FreesoundProvider } from "../pipeline/asset-scout/providers/freesound-provider.mjs";
import { normalizeLicenseId, COMPATIBLE_LICENSES } from "../pipeline/rights-gate.mjs";

test("FreesoundProvider returns empty array when apiKey is missing or unconfigured", async () => {
  const provider = new FreesoundProvider({ apiKey: "" });
  const results = await provider.search({ query: "laser whoosh" });
  assert.deepEqual(results, []);
});

test("FreesoundProvider searches and parses CC0 audio effects with active key", async () => {
  const provider = new FreesoundProvider();
  if (!provider.apiKey) {
    // If running in environment without key, skip remote network call
    return;
  }

  const results = await provider.search({
    query: "click",
    count: 2,
    licenseFilter: "Creative Commons 0",
    maxDuration: 5,
  });

  assert.ok(Array.isArray(results), "Results must be an array");
  assert.ok(results.length > 0, "Should find at least 1 CC0 click effect");

  const sound = results[0];
  assert.ok(sound.assetId.startsWith("freesound-"), "assetId must prefix with freesound-");
  assert.equal(sound.type, "audio", "type must be audio");
  assert.equal(sound.sourceProvider, "freesound");
  assert.equal(sound.licenseId, "CC0-1.0", "licenseId must normalize to CC0-1.0");
  assert.equal(sound.commercialUse, true, "commercialUse must be true for CC0");
  assert.equal(sound.modificationsAllowed, true, "modifications must be allowed");
  assert.ok(sound.downloadUrl && sound.downloadUrl.includes("freesound.org"), "Must have preview download URL");
});

test("normalizeLicenseId recognizes Creative Commons URLs from Freesound API", () => {
  // CC0
  assert.equal(normalizeLicenseId("http://creativecommons.org/publicdomain/zero/1.0/"), "CC0-1.0");
  assert.equal(normalizeLicenseId("https://creativecommons.org/publicdomain/zero/1.0/"), "CC0-1.0");

  // CC-BY
  assert.equal(normalizeLicenseId("https://creativecommons.org/licenses/by/4.0/"), "CC-BY-4.0");
  assert.equal(normalizeLicenseId("http://creativecommons.org/licenses/by/3.0/"), "CC-BY-3.0");

  // Non-commercial (Strict rejection)
  const ncLic = normalizeLicenseId("https://creativecommons.org/licenses/by-nc/4.0/");
  assert.equal(ncLic, "CC-BY-NC-4.0");
  assert.equal(COMPATIBLE_LICENSES.has(ncLic), false, "NC license must NOT be in COMPATIBLE_LICENSES");
});
