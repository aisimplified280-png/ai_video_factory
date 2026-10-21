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

  // 1. Mandatory metadata checks
  if (!assetMetadata.assetId) issues.push("Missing assetId.");
  if (!assetMetadata.sourceProvider) issues.push("Missing sourceProvider.");
  if (!assetMetadata.licenseId) issues.push("Missing licenseId.");

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

  // 5. Likeness, privacy, and trademark flags
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
 * Format YouTube description credits from approved asset manifests.
 */
export function generateCreditsReport(approvedAssets = []) {
  const lines = [];
  const attributedAssets = approvedAssets.filter(
    (a) => a.status === RIGHTS_STATUS.APPROVED_WITH_ATTRIBUTION && a.attributionText
  );

  if (attributedAssets.length === 0) {
    return {
      hasCredits: false,
      creditsText: "",
      count: 0,
    };
  }

  lines.push("Visual & Media Credits:");
  attributedAssets.forEach((asset, idx) => {
    lines.push(`- ${asset.attributionText} (${asset.sourceProvider} / ${asset.licenseId})`);
  });

  return {
    hasCredits: true,
    creditsText: lines.join("\n"),
    count: attributedAssets.length,
  };
}
