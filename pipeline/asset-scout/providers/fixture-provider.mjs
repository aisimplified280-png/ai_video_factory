// pipeline/asset-scout/providers/fixture-provider.mjs - Offline Verified Fixture Provider
import path from "node:path";
import fs from "node:fs/promises";
import { ROOT_DIR } from "../../config.mjs";

/**
 * Embedded SVG / visual fixture generator for 100% offline development & tests.
 * Zero network calls, zero API keys, 100% CC0 / Apache-2.0 license provenance.
 */
export class FixtureProvider {
  name = "offline-fixture";

  async search({ query, type = "image", count = 3 }) {
    const fixturesDir = path.join(ROOT_DIR, "assets", "fixtures");
    await fs.mkdir(fixturesDir, { recursive: true });

    // Generate high-quality SVG diagrams matching the query
    const results = [];
    const normalizedQuery = (query || "ai-architecture").toLowerCase();

    if (normalizedQuery.includes("prompt") || normalizedQuery.includes("cache") || normalizedQuery.includes("claude")) {
      const filePath = path.join(fixturesDir, "prompt-caching-diagram.svg");
      const svgContent = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 500" width="800" height="500">
        <rect width="100%" height="100%" fill="#faf8f5" rx="24"/>
        <rect x="40" y="40" width="720" height="420" fill="#ffffff" stroke="#e7d8cc" stroke-width="2" rx="20"/>
        <text x="70" y="90" font-family="-apple-system, sans-serif" font-size="24" font-weight="bold" fill="#1c1917">Prompt Caching Topology</text>
        <rect x="70" y="140" width="180" height="120" fill="#fbf3ee" stroke="#d97757" stroke-width="2" rx="12"/>
        <text x="90" y="190" font-family="-apple-system, sans-serif" font-size="18" font-weight="bold" fill="#a45338">Static Context</text>
        <text x="90" y="220" font-family="-apple-system, sans-serif" font-size="14" fill="#78716c">10k+ Tokens</text>
        <path d="M 260 200 L 330 200" stroke="#d97757" stroke-width="3" fill="none" marker-end="url(#arrow)"/>
        <rect x="340" y="140" width="180" height="120" fill="#f4ede6" stroke="#cc785c" stroke-width="2" rx="12"/>
        <text x="360" y="190" font-family="-apple-system, sans-serif" font-size="18" font-weight="bold" fill="#a45338">Ephemeral RAM</text>
        <text x="360" y="220" font-family="-apple-system, sans-serif" font-size="14" fill="#78716c">5-Min Warm Window</text>
        <path d="M 530 200 L 600 200" stroke="#d97757" stroke-width="3" fill="none"/>
        <rect x="610" y="140" width="130" height="120" fill="#ffffff" stroke="#16a34a" stroke-width="2" rx="12"/>
        <text x="630" y="190" font-family="-apple-system, sans-serif" font-size="18" font-weight="bold" fill="#166534">Claude 3.5</text>
        <text x="630" y="220" font-family="-apple-system, sans-serif" font-size="14" fill="#16a34a">Instant Hit</text>
      </svg>`;
      await fs.writeFile(filePath, svgContent, "utf8");

      results.push({
        assetId: "fix-prompt-caching-diagram-01",
        type: "svg",
        sourceProvider: "offline-fixture",
        sourcePage: "file:///assets/fixtures/prompt-caching-diagram.svg",
        downloadUrl: filePath,
        creator: "AI Simplified Lab Engineering Team",
        licenseId: "CC0-1.0",
        licenseUrl: "https://creativecommons.org/publicdomain/zero/1.0/",
        commercialUse: true,
        modificationsAllowed: true,
        attributionRequired: false,
        attributionText: "AI Simplified Lab (CC0)",
        localFilePath: filePath,
        reviewFlags: {
          recognizablePerson: false,
          trademarkLogo: false,
          sensitiveContent: false,
        },
      });
    }

    // Default Tech Architecture Fixture
    const defPath = path.join(fixturesDir, "tech-architecture-diagram.svg");
    const defSvg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 500" width="800" height="500">
      <rect width="100%" height="100%" fill="#faf8f5" rx="24"/>
      <rect x="40" y="40" width="720" height="420" fill="#ffffff" stroke="#e7d8cc" stroke-width="2" rx="20"/>
      <text x="70" y="90" font-family="-apple-system, sans-serif" font-size="24" font-weight="bold" fill="#1c1917">Deterministic Media Pipeline</text>
      <rect x="70" y="150" width="190" height="110" fill="#fbf3ee" stroke="#d97757" stroke-width="2" rx="12"/>
      <text x="95" y="200" font-family="-apple-system, sans-serif" font-size="18" font-weight="bold" fill="#a45338">Input Contract</text>
      <text x="95" y="230" font-family="-apple-system, sans-serif" font-size="14" fill="#78716c">Validated Schema</text>
      <rect x="310" y="150" width="190" height="110" fill="#f4ede6" stroke="#cc785c" stroke-width="2" rx="12"/>
      <text x="330" y="200" font-family="-apple-system, sans-serif" font-size="18" font-weight="bold" fill="#a45338">Local Renderer</text>
      <text x="330" y="230" font-family="-apple-system, sans-serif" font-size="14" fill="#78716c">HyperFrames + GSAP</text>
      <rect x="550" y="150" width="180" height="110" fill="#ffffff" stroke="#16a34a" stroke-width="2" rx="12"/>
      <text x="570" y="200" font-family="-apple-system, sans-serif" font-size="18" font-weight="bold" fill="#166534">Quality Gate</text>
      <text x="570" y="230" font-family="-apple-system, sans-serif" font-size="14" fill="#16a34a">FFprobe / Rights</text>
    </svg>`;
    await fs.writeFile(defPath, defSvg, "utf8");

    results.push({
      assetId: "fix-tech-architecture-diagram-02",
      type: "svg",
      sourceProvider: "offline-fixture",
      sourcePage: "file:///assets/fixtures/tech-architecture-diagram.svg",
      downloadUrl: defPath,
      creator: "AI Simplified Lab Engineering Team",
      licenseId: "CC0-1.0",
      licenseUrl: "https://creativecommons.org/publicdomain/zero/1.0/",
      commercialUse: true,
      modificationsAllowed: true,
      attributionRequired: false,
      attributionText: "AI Simplified Lab (CC0)",
      localFilePath: defPath,
      reviewFlags: {
        recognizablePerson: false,
        trademarkLogo: false,
        sensitiveContent: false,
      },
    });

    return results.slice(0, count);
  }
}
