// pipeline/asset-scout/providers/pexels-provider.mjs - Pexels API Adapter
import process from "node:process";

/**
 * Pexels API adapter.
 * Uses PEXELS_API_KEY if present in environment; returns [] if unconfigured.
 */
export class PexelsProvider {
  name = "pexels";
  apiKey = process.env.PEXELS_API_KEY || "";

  async search({ query, type = "image", count = 3 }) {
    if (!this.apiKey) return [];

    const endpoint = type === "video" 
      ? `https://api.pexels.com/videos/search?query=${encodeURIComponent(query)}&per_page=${count}`
      : `https://api.pexels.com/v1/search?query=${encodeURIComponent(query)}&per_page=${count}`;

    try {
      const response = await fetch(endpoint, {
        headers: { Authorization: this.apiKey },
      });
      if (!response.ok) return [];

      const data = await response.json();
      const items = type === "video" ? data.videos : data.photos;
      if (!Array.isArray(items)) return [];

      return items.map((item) => ({
        assetId: `pexels-${item.id}`,
        type,
        sourceProvider: "pexels",
        sourcePage: item.url,
        downloadUrl: type === "video" ? item.video_files?.[0]?.link : item.src?.large2x || item.src?.original,
        creator: type === "video" ? item.user?.name : item.photographer,
        licenseId: "Pexels-License",
        licenseUrl: "https://www.pexels.com/license/",
        commercialUse: true,
        modificationsAllowed: true,
        attributionRequired: false,
        attributionText: `Photo/Video by ${type === "video" ? item.user?.name : item.photographer} on Pexels`,
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
