// pipeline/asset-scout/providers/openverse-provider.mjs - Openverse Creative Commons Index
import { normalizeLicenseId } from "../../rights-gate.mjs";

/**
 * Openverse API adapter (Creative Commons & Public Domain media index).
 * Docs: https://api.openverse.org/v1/
 */
export class OpenverseProvider {
  name = "openverse";
  baseUrl = "https://api.openverse.org/v1/images/";

  async search({ query, count = 5 }) {
    const url = new URL(this.baseUrl);
    url.searchParams.set("q", query);
    url.searchParams.set("page_size", String(count));
    // Filter for commercial-use and modification allowed licenses
    url.searchParams.set("license_type", "commercial,modification");

    try {
      const response = await fetch(url.toString(), {
        headers: { "User-Agent": "AISimplifiedLab-VideoFactory/1.0" },
      });
      if (!response.ok) return [];

      const data = await response.json();
      if (!Array.isArray(data.results)) return [];

      const validItems = [];
      for (const item of data.results) {
        if (!item.url || !item.id) continue;

        // Strictly normalize license without guessing or assuming defaults
        const normalizedLicense = normalizeLicenseId(item.license, item.license_version);
        if (!normalizedLicense) continue; // Skip items with unverified/missing licenses

        const isPublicDomain = normalizedLicense === "CC0-1.0" || normalizedLicense === "Public Domain";

        validItems.push({
          assetId: `openverse-${item.id}`,
          type: "image",
          title: item.title || "Openverse Asset",
          sourceProvider: "openverse",
          sourcePage: item.foreign_landing_url || item.url,
          downloadUrl: item.url,
          creator: item.creator || "Unknown Creator",
          licenseId: normalizedLicense,
          licenseUrl: item.license_url || `https://creativecommons.org/licenses/`,
          commercialUse: true,
          modificationsAllowed: true,
          attributionRequired: !isPublicDomain,
          attributionText: `${item.title || "Image"} by ${item.creator || "Creator"} via Openverse (${normalizedLicense})`,
          reviewFlags: {
            recognizablePerson: false,
            trademarkLogo: false,
            sensitiveContent: false,
          },
        });
      }

      return validItems;
    } catch {
      return [];
    }
  }
}
