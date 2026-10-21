// pipeline/rights-gate.mjs - License & Copyright Provenance Verification Gate
import crypto from "node:crypto";
import fs from "node:fs/promises";

export const RIGHTS_STATUS = {
  APPROVED: "APPROVED",
  APPROVED_WITH_ATTRIBUTION: "APPROVED_WITH_ATTRIBUTION",
  REJECTED: "REJECTED",
  REVIEW_REQUIRED: "REVIEW_REQUIRED",
};

/**
 * Standard known compatible commercial licenses.
 */
export const COMPATIBLE_LICENSES = new Set([
  "CC0",
  "CC0-1.0",
  "Public Domain",
  "CC-BY",
  "CC-BY-4.0",
  "CC-BY-3.0",
  "CC-BY-2.0",
  "Pexels-License",
  "Pixabay-Content-License",
  "Apache-2.0",
  "MIT",
]);

/**
 * Normalize Openverse / external license identifiers explicitly.
 * Never guesses or assigns a default license if metadata is missing or contradictory.
 */
export function normalizeLicenseId(rawLicense, rawVersion = "") {
  if (!rawLicense || typeof rawLicense !== "string") return null;

  const lic = rawLicense.trim().toLowerCase();
  const ver = typeof rawVersion === "string" ? rawVersion.trim() : "";

  if (lic === "cc0" || lic === "cc0-1.0" || lic === "cc0 1.0") return "CC0-1.0";
  if (lic === "pdm" || lic === "public domain" || lic === "publicdomain") return "Public Domain";

  // Creative Commons Attribution
  if (lic === "by") {
    if (ver === "4.0" || !ver) return "CC-BY-4.0";
    if (ver === "3.0") return "CC-BY-3.0";
    if (ver === "2.0") return "CC-BY-2.0";
    return `CC-BY-${ver}`;
  }

  // Non-commercial licenses (explicitly preserved so auditAssetRights rejects them)
  if (lic.includes("nc") || lic.includes("noncommercial")) {
    return "CC-BY-NC-4.0";
  }

  // No-derivatives licenses (explicitly preserved so auditAssetRights rejects them)
  if (lic.includes("nd") || lic.includes("noderivs")) {
    return "CC-BY-ND-4.0";
  }

  // Share-alike licenses
  if (lic.includes("sa") || lic.includes("sharealike")) {
    return "CC-BY-SA-4.0";
  }

  if (lic === "apache-2.0" || lic === "apache 2.0") return "Apache-2.0";
  if (lic === "mit") return "MIT";
  if (lic === "pexels" || lic === "pexels-license") return "Pexels-License";
  if (lic === "pixabay" || lic === "pixabay-license") return "Pixabay-Content-License";

  return null;
}

/**
 * Compute SHA-256 hash of a local file.
 */
export async function computeSha256(filePath) {
  const fileBuffer = await fs.readFile(filePath);
  return crypto.createHash("sha256").update(fileBuffer).digest("hex");
}

/**
 * Verify rights and assign governance approval status.
 *
 * Rules:
 * - Reject non-commercial restrictions.
 * - Reject unknown licenses or missing metadata.
 * - Reject no-derivatives (ND) when modifications/transforms are planned.
 * - Route recognizable persons, trademarks, or sensitive likenesses to REVIEW_REQUIRED.
 * - Require attribution text if attribution_required is true.
 */
export function auditAssetRights(assetMetadata, plannedTransformations = true) {
  const issues = [];
  const flags = assetMetadata.reviewFlags || {};

  // 1. Mandatory metadata checks - Missing metadata cannot result in approval
  if (!assetMetadata.assetId) issues.push("Missing assetId.");
  if (!assetMetadata.sourceProvider) issues.push("Missing sourceProvider.");
  if (!assetMetadata.licenseId) {
    return {
      status: RIGHTS_STATUS.REJECTED,
      reason: "Asset metadata is missing licenseId; cannot assume license.",
      issues: [...issues, "Missing licenseId."],
    };
  }

  // 2. Commercial use permission
  if (assetMetadata.commercialUse === false) {
    return {
      status: RIGHTS_STATUS.REJECTED,
      reason: "Asset prohibits commercial use (Non-Commercial / NC restriction).",
      issues,
    };
  }

  // 3. Modifications / Derivatives check
  if (plannedTransformations && assetMetadata.modificationsAllowed === false) {
    return {
      status: RIGHTS_STATUS.REJECTED,
      reason: "Asset prohibits modifications (No-Derivatives / ND restriction).",
      issues,
    };
  }

  // 4. Known license compatibility
  if (!COMPATIBLE_LICENSES.has(assetMetadata.licenseId)) {
    return {
      status: RIGHTS_STATUS.REJECTED,
      reason: `License '${assetMetadata.licenseId}' is not verified for commercial code transformations.`,
      issues,
    };
  }

  // 5. Likeness, privacy, and trademark flags (Route to review, never silently approve)
  if (flags.recognizablePerson) {
    return {
      status: RIGHTS_STATUS.REVIEW_REQUIRED,
      reason: "Asset contains recognizable person; requires model release check.",
      issues,
    };
  }
  if (flags.trademarkLogo) {
    return {
      status: RIGHTS_STATUS.REVIEW_REQUIRED,
      reason: "Asset contains prominent commercial trademark/logo; requires editorial fair-use audit.",
      issues,
    };
  }

  // 6. Attribution compliance
  if (assetMetadata.attributionRequired) {
    if (!assetMetadata.attributionText || !assetMetadata.attributionText.trim()) {
      return {
        status: RIGHTS_STATUS.REJECTED,
        reason: "Attribution is required but no attributionText was supplied.",
        issues,
      };
    }
    return {
      status: RIGHTS_STATUS.APPROVED_WITH_ATTRIBUTION,
      attributionText: assetMetadata.attributionText,
      reason: "Approved with required attribution.",
      issues,
    };
  }

  return {
    status: RIGHTS_STATUS.APPROVED,
    reason: "Approved for unrestricted commercial reuse.",
    issues,
  };
}

/**
 * Format YouTube description credits and QA report from approved asset manifests.
 * Unifies schema so renderer and reports always agree:
 * { hasCredits, creditsText, reportText, youtubeDescriptionText, count, assets }
 */
export function generateCreditsReport(approvedAssets = []) {
  const lines = [];
  const attributedAssets = approvedAssets.filter(
    (a) =>
      (a.status === RIGHTS_STATUS.APPROVED_WITH_ATTRIBUTION || a.attributionRequired) &&
      a.attributionText &&
      a.status !== RIGHTS_STATUS.REJECTED &&
      a.status !== RIGHTS_STATUS.REVIEW_REQUIRED
  );

  if (attributedAssets.length === 0) {
    return {
      hasCredits: false,
      creditsText: "",
      reportText: "No external assets requiring attribution were used.",
      youtubeDescriptionText: "",
      count: 0,
      assets: [],
    };
  }

  lines.push("Visual & Media Credits (Verified Licenses):");
  attributedAssets.forEach((asset) => {
    const sourceLink = asset.sourcePage ? `— ${asset.sourcePage}` : "";
    const licLink = asset.licenseUrl ? `(${asset.licenseId}: ${asset.licenseUrl})` : `(${asset.licenseId})`;
    const line = asset.attributionText
      ? `• ${asset.attributionText} [${asset.licenseId}] ${sourceLink}`
      : `• "${asset.title || asset.assetId}" ${asset.creator ? `by ${asset.creator} ` : ""}via ${asset.sourceProvider} ${licLink} ${sourceLink}`;
    lines.push(line.trim());
  });

  const fullText = lines.join("\n");

  return {
    hasCredits: true,
    creditsText: fullText,
    reportText: fullText,
    youtubeDescriptionText: fullText,
    count: attributedAssets.length,
    assets: attributedAssets,
  };
}
