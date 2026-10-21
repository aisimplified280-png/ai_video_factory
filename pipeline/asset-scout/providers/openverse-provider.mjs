// pipeline/asset-scout/providers/openverse-provider.mjs - Openverse Creative Commons Index
import process from "node:process";

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

      return data.results.map((item) => ({
        assetId: `openverse-${item.id}`,
        type: "image",
        sourceProvider: "openverse",
        sourcePage: item.foreign_landing_url || item.url,
        downloadUrl: item.url,
        creator: item.creator || "Unknown Creator",
        licenseId: (item.license || "CC-BY-4.0").toUpperCase(),
        licenseUrl: item.license_url || "https://creativecommons.org/licenses/",
        commercialUse: true,
        modificationsAllowed: true,
        attributionRequired: item.license !== "cc0" && item.license !== "pdm",
        attributionText: `${item.title || "Image"} by ${item.creator || "Creator"} via Openverse (${(item.license || "CC-BY").toUpperCase()})`,
        reviewFlags: {
          recognizablePerson: false,
          trademarkLogo: false,
          sensitiveContent: false,
        },
      }));
    } catch {
      return [];
    }
  }
}
