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
  async search({ query, type = "image", count = 3 }) {
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
        // Prioritize illustrations and vectors for our faceless editorial/collage look
        url.searchParams.set("image_type", "illustration");
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
        const tags = (hit.tags || "").toLowerCase();
        const hasPersonTag = /\b(face|portrait|selfie|model|woman|man|person|girl|boy|businessman|headshot)\b/i.test(tags);

        return {
          assetId: `pixabay-${hit.id}`,
          type: isVideo ? "video" : (hit.type || "image"),
          title: hit.tags ? hit.tags.split(",")[0].trim() : "Pixabay Asset",
          sourceProvider: "pixabay",
          sourcePage: hit.pageURL,
          downloadUrl,
          creator: hit.user || "Pixabay Creator",
          licenseId: "Pixabay-Content-License",
          licenseUrl: "https://pixabay.com/service/license-summary/",
          commercialUse: true,
          modificationsAllowed: true,
          attributionRequired: false,
          attributionText: `Visual by ${hit.user} via Pixabay (Pixabay Content License)`,
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
