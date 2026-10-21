// pipeline/asset-scout/providers/fixture-provider.mjs - 100% Offline CC0 SVG Diagram Fixture Provider
import fs from "node:fs/promises";
import path from "node:path";
import { ROOT_DIR } from "../../config.mjs";

/**
 * Deterministic offline fixture provider for testing and offline builds.
 * Generates valid, CC0-licensed SVG architecture diagrams with the AI Simplified Lab Purple Collage aesthetic.
 */
export class FixtureProvider {
  name = "offline-fixture";

  async search({ query = "", count = 2 }) {
    const fixturesDir = path.join(ROOT_DIR, "assets", "fixtures");
    await fs.mkdir(fixturesDir, { recursive: true });

    const normalizedQuery = query.toLowerCase();
    const results = [];

    if (normalizedQuery.includes("prompt") || normalizedQuery.includes("cache") || normalizedQuery.includes("claude")) {
      const filePath = path.join(fixturesDir, "prompt-caching-diagram.svg");
      const svgContent = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 500" width="800" height="500">
        <rect width="100%" height="100%" fill="#120826" rx="24"/>
        <rect x="30" y="30" width="740" height="440" fill="#1b0e36" stroke="rgba(192, 132, 252, 0.4)" stroke-width="2" rx="20"/>
        <text x="60" y="85" font-family="-apple-system, sans-serif" font-size="26" font-weight="800" fill="#ffffff" letter-spacing="0.04em">PROMPT CACHE TOPOLOGY</text>
        <rect x="60" y="130" width="190" height="130" fill="rgba(192, 132, 252, 0.12)" stroke="#c084fc" stroke-width="2" rx="14"/>
        <text x="80" y="180" font-family="-apple-system, sans-serif" font-size="20" font-weight="700" fill="#ffffff">Static Context</text>
        <text x="80" y="215" font-family="-apple-system, sans-serif" font-size="15" fill="#cbd5e1">10k+ Tokens</text>
        <path d="M 260 195 L 320 195" stroke="#a3e635" stroke-width="3" fill="none"/>
        <rect x="330" y="130" width="200" height="130" fill="rgba(46, 16, 101, 0.6)" stroke="#8b5cf6" stroke-width="2" rx="14"/>
        <text x="350" y="180" font-family="-apple-system, sans-serif" font-size="20" font-weight="700" fill="#ffffff">Ephemeral RAM</text>
        <text x="350" y="215" font-family="-apple-system, sans-serif" font-size="15" fill="#a3e635">5-Min / 1-Hr TTL</text>
        <path d="M 540 195 L 600 195" stroke="#a3e635" stroke-width="3" fill="none"/>
        <rect x="610" y="130" width="140" height="130" fill="rgba(163, 230, 53, 0.12)" stroke="#a3e635" stroke-width="2" rx="14"/>
        <text x="625" y="180" font-family="-apple-system, sans-serif" font-size="20" font-weight="800" fill="#a3e635">Claude 3.5</text>
        <text x="625" y="215" font-family="-apple-system, sans-serif" font-size="15" fill="#ffffff">Warm Hit</text>
        <text x="60" y="310" font-family="-apple-system, sans-serif" font-size="18" fill="#e2e8f0">✓ Bypasses repetitive prompt context ingestion on subsequent API calls</text>
        <text x="60" y="340" font-family="-apple-system, sans-serif" font-size="16" fill="#94a3b8">Source: Anthropic API Prompt Caching Reference</text>
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
      <rect width="100%" height="100%" fill="#120826" rx="24"/>
      <rect x="30" y="30" width="740" height="440" fill="#1b0e36" stroke="rgba(192, 132, 252, 0.4)" stroke-width="2" rx="20"/>
      <text x="60" y="85" font-family="-apple-system, sans-serif" font-size="26" font-weight="800" fill="#ffffff">DETERMINISTIC MEDIA PIPELINE</text>
      <rect x="60" y="140" width="200" height="120" fill="rgba(192, 132, 252, 0.12)" stroke="#c084fc" stroke-width="2" rx="14"/>
      <text x="80" y="190" font-family="-apple-system, sans-serif" font-size="20" font-weight="700" fill="#ffffff">Input Contract</text>
      <text x="80" y="220" font-family="-apple-system, sans-serif" font-size="15" fill="#cbd5e1">Validated Schema</text>
      <rect x="290" y="140" width="200" height="120" fill="rgba(46, 16, 101, 0.6)" stroke="#8b5cf6" stroke-width="2" rx="14"/>
      <text x="310" y="190" font-family="-apple-system, sans-serif" font-size="20" font-weight="700" fill="#ffffff">Local Renderer</text>
      <text x="310" y="220" font-family="-apple-system, sans-serif" font-size="15" fill="#cbd5e1">HyperFrames + GSAP</text>
      <rect x="520" y="140" width="200" height="120" fill="rgba(163, 230, 53, 0.12)" stroke="#a3e635" stroke-width="2" rx="14"/>
      <text x="540" y="190" font-family="-apple-system, sans-serif" font-size="20" font-weight="800" fill="#a3e635">Quality Gate</text>
      <text x="540" y="220" font-family="-apple-system, sans-serif" font-size="15" fill="#ffffff">Fail-Closed Verification</text>
      <text x="60" y="320" font-family="-apple-system, sans-serif" font-size="18" fill="#e2e8f0">✓ Complete offline verification with zero remote runtime dependencies</text>
    </svg>`;
    await fs.writeFile(defPath, defSvg, "utf8");

    results.push({
      assetId: "fix-tech-architecture-01",
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
