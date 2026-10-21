// pipeline/asset-scout/providers/pixabay-provider.mjs - Pixabay API Adapter
import process from "node:process";

/**
 * Pixabay API Adapter for royalty-free stock illustrations, vectors, and graphics.
 * Docs: https://pixabay.com/api/docs/
 */
export class PixabayProvider {
  name = "pixabay";

  constructor(options = {}) {
    this.apiKey = options.apiKey !== undefined ? options.apiKey : (process.env.PIXABAY_API_KEY || "");
  }

  /**
   * Search Pixabay API.
   * @param {Object} params
   * @param {string} params.query - Search keywords
   * @param {string} [params.type='image'] - 'image' or 'video'
   * @param {number} [params.count=3] - Number of results to request
   * @returns {Promise<Array>}
   */
  async search({ query, type = "image", count = 3, imageType = "all" } = {}) {
    const key = this.apiKey;
    if (!key) return [];

    try {
      const isVideo = type === "video";
      const baseEndpoint = isVideo
        ? "https://pixabay.com/api/videos/"
        : "https://pixabay.com/api/";

      const url = new URL(baseEndpoint);
      url.searchParams.set("key", key);
      url.searchParams.set("q", query);
      url.searchParams.set("per_page", String(Math.max(3, Math.min(20, count))));
      url.searchParams.set("safesearch", "true");

      if (!isVideo) {
        // Allow all image types (photos, vectors, illustrations) or specific imageType if passed
        const imgType = imageType || "all";
        if (imgType !== "all") {
          url.searchParams.set("image_type", imgType);
        }
      }

      const response = await fetch(url.toString(), {
        headers: { "User-Agent": "AISimplifiedLab-VideoFactory/1.0" },
      });

      if (!response.ok) return [];

      const data = await response.json();
      if (!Array.isArray(data.hits)) return [];

      return data.hits.map((hit) => {
        const downloadUrl = isVideo
          ? hit.videos?.medium?.url || hit.videos?.large?.url || hit.videos?.small?.url
          : hit.largeImageURL || hit.webformatURL;

        // Check tags for potential real person / face depiction to uphold faceless policy
        const rawTags = (hit.tags || "").toLowerCase();
        const tagList = rawTags.split(",").map((t) => t.trim()).filter(Boolean);
        const hasPersonTag = /\b(face|portrait|selfie|model|woman|man|person|girl|boy|businessman|headshot)\b/i.test(rawTags);

        return {
          assetId: `pixabay-${hit.id}`,
          type: isVideo ? "video" : (hit.type || "image"),
          title: tagList[0] ? tagList[0].replace(/^[a-z]/, (c) => c.toUpperCase()) : "Pixabay Asset",
          tags: tagList,
          rawTags: hit.tags || "",
          description: hit.tags || "",
          sourceProvider: "pixabay",
          sourcePage: hit.pageURL,
          downloadUrl,
          previewUrl: hit.previewURL || hit.webformatURL,
          dimensions: { width: hit.imageWidth || 0, height: hit.imageHeight || 0 },
          creator: hit.user || "Pixabay Creator",
          licenseId: "Pixabay-Content-License",
          licenseUrl: "https://pixabay.com/service/license-summary/",
          commercialUse: true,
          modificationsAllowed: true,
          attributionRequired: false,
          attributionText: `Visual by ${hit.user} via Pixabay (Pixabay Content License)`,
          qualityMetrics: {
            likes: hit.likes || 0,
            views: hit.views || 0,
            downloads: hit.downloads || 0,
          },
          reviewFlags: {
            recognizablePerson: hasPersonTag,
            trademarkLogo: false,
            sensitiveContent: false,
          },
        };
      });
    } catch (err) {
      console.warn(`[AssetScout:Pixabay] Search failed:`, err.message);
      return [];
    }
  }
}
