// pipeline/composition-generator.mjs - AI Simplified Lab Purple Collage Explainer Synthesizer
import fs from "node:fs/promises";
import path from "node:path";
import { ROOT_DIR } from "./config.mjs";

/**
 * Escape HTML characters to prevent XSS and template injection.
 */
export function escapeHtml(str) {
  if (typeof str !== "string") return "";
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

/**
 * Generate full HTML5 / GSAP 9:16 composition for HyperFrames.
 * Features:
 * - AI Simplified Lab Purple Collage Explainer visual identity.
 * - Deep ink-violet canvas with tactile halftone dot-matrix pattern.
 * - Diverse composition modes (not just rounded white cards).
 * - Physical metaphors for invisible software concepts.
 * - 100% Offline: Vendors local GSAP from pipeline/vendor/ (zero CDN).
 * - Kinetic Word/Phrase-level Active Captions in safe zone.
 */
export async function generateComposition(compDir, projectData) {
  const { totalDuration, scenes, title, id } = projectData;

  // 1. Copy local vendored GSAP to composition directory
  const compVendorDir = path.join(compDir, "assets", "vendor");
  await fs.mkdir(compVendorDir, { recursive: true });
  const localGsapSrc = path.join(ROOT_DIR, "pipeline", "vendor", "gsap.min.js");
  const localGsapDest = path.join(compVendorDir, "gsap.min.js");
  await fs.copyFile(localGsapSrc, localGsapDest);

  // 2. Write hyperframes.json
  const hyperframesJson = {
    $schema: "https://hyperframes.heygen.com/schema/hyperframes.json",
    name: id,
    paths: {
      blocks: "compositions",
      components: "compositions/components",
      assets: "assets",
    },
    media: {
      autoProxy: false,
    },
  };
  await fs.writeFile(path.join(compDir, "hyperframes.json"), JSON.stringify(hyperframesJson, null, 2));

  // 2b. Copy referenced scouted assets if any
  const scoutedDir = path.join(compDir, "assets", "scouted");
  await fs.mkdir(scoutedDir, { recursive: true });
  for (const scene of scenes) {
    if (scene.assetData && scene.assetData.cachedPath) {
      const srcPath = path.isAbsolute(scene.assetData.cachedPath)
        ? scene.assetData.cachedPath
        : path.join(ROOT_DIR, scene.assetData.cachedPath);
      const filename = path.basename(srcPath);
      const destPath = path.join(scoutedDir, filename);
      try {
        await fs.copyFile(srcPath, destPath);
        scene._assetFilename = filename;
      } catch (err) {
        console.warn(`[Composition] Could not copy asset ${srcPath}:`, err.message);
      }
    }
  }

  // 3. Render modular semantic scenes with purple collage identity
  const scenesHtml = scenes.map((scene, idx) => {
    const isFirst = idx === 0;
    const cardType = scene.cardType || "concept-explainer";

    let cardContent = "";

    if (cardType === "hook" || cardType === "hook-bold-object") {
      // Full-frame hook with surreal dimensional object & oversized typography
      cardContent = `
        <div class="purple-badge">
          <span class="badge-dot pulse-lime"></span>
          ${escapeHtml(scene.badge || "AI BOTTLENECK")}
        </div>
        <h1 class="hero-headline">${escapeHtml(scene.visualTitle)}</h1>
        <div class="collage-hero-card">
          <div class="surreal-object-container">
            <div class="surreal-glow-ring"></div>
            <div class="surreal-icon">⚡</div>
          </div>
          <div class="hero-statement-box">
            <div class="card-tag">${escapeHtml(scene.tag || "OBSERVATION")}</div>
            <p class="card-highlight">${escapeHtml(scene.visualBody)}</p>
            ${scene.source ? `<div class="source-tag">Source: ${escapeHtml(scene.source)}</div>` : ""}
          </div>
        </div>
      `;
    } else if (cardType === "architecture-diagram") {
      if (scene._assetFilename) {
        // Render prominent, large scouted architecture graphic inside an illuminated glass frame
        cardContent = `
          <div class="purple-badge">
            <span class="badge-dot pulse-violet"></span>
            ${escapeHtml(scene.badge || "SYSTEM TOPOLOGY")}
          </div>
          <h2 class="scene-title">${escapeHtml(scene.visualTitle)}</h2>
          <div class="diagram-hero-frame">
            <img src="./assets/scouted/${scene._assetFilename}" class="scouted-asset-img" alt="${escapeHtml(scene.visualTitle)}" />
            <div class="diagram-caption-strip">
              <span class="caption-text">${escapeHtml(scene.visualBody)}</span>
              ${scene.assetData?.attributionText ? `<span class="asset-attribution-badge">Verified Media • ${escapeHtml(scene.assetData.licenseId || "CC0")}</span>` : ""}
            </div>
          </div>
        `;
      } else {
        // Procedural animated node pipeline with glowing connectors
        const nodes = scene.diagramNodes || [
          { label: "User Input", sub: "Raw Context" },
          { label: "Semantic Filter", sub: "Vector / RAG" },
          { label: "LLM Model", sub: "Cached Response" }
        ];
        cardContent = `
          <div class="purple-badge">
            <span class="badge-dot pulse-violet"></span>
            ${escapeHtml(scene.badge || "DATA FLOW")}
          </div>
          <h2 class="scene-title">${escapeHtml(scene.visualTitle)}</h2>
          <div class="purple-flow-container">
            ${nodes.map((node, nIdx) => `
              <div class="purple-flow-node node-${nIdx}">
                <div class="node-icon-dot"></div>
                <div class="node-title">${escapeHtml(node.label)}</div>
                <div class="node-sub">${escapeHtml(node.sub || "")}</div>
              </div>
              ${nIdx < nodes.length - 1 ? '<div class="purple-flow-arrow">➔</div>' : ''}
            `).join("")}
          </div>
          <div class="collage-note-box">
            <p class="card-highlight">${escapeHtml(scene.visualBody)}</p>
          </div>
        `;
      }
    } else if (cardType === "physical-metaphor") {
      // Physical metaphor for invisible software dynamics
      cardContent = `
        <div class="purple-badge">
          <span class="badge-dot pulse-lime"></span>
          ${escapeHtml(scene.badge || "PHYSICAL METAPHOR")}
        </div>
        <h2 class="scene-title">${escapeHtml(scene.visualTitle)}</h2>
        <div class="metaphor-collage-stage">
          <div class="metaphor-block conveyor-block">
            <div class="conveyor-track">
              <div class="conveyor-item item-static">
                <span class="item-tag">STATIC PREFIX</span>
                <span class="item-desc">System Prompt &amp; Context</span>
                <span class="item-status">📌 Pinned in RAM</span>
              </div>
              <div class="conveyor-arrow">⬇ Instant Match</div>
              <div class="conveyor-item item-dynamic">
                <span class="item-tag">DYNAMIC QUERY</span>
                <span class="item-desc">User Message</span>
                <span class="item-status">⚡ Instant Hit</span>
              </div>
            </div>
            <div class="ttl-badge">⏳ 5-Min Default • 1-Hour Extended TTL</div>
          </div>
          <p class="card-highlight metaphor-caption">${escapeHtml(scene.visualBody)}</p>
        </div>
      `;
    } else if (cardType === "code" || cardType === "terminal") {
      // Authentic syntax terminal with glowing highlighted lines
      cardContent = `
        <div class="purple-badge">
          <span class="badge-dot pulse-lime"></span>
          ${escapeHtml(scene.badge || "API IMPLEMENTATION")}
        </div>
        <h2 class="scene-title">${escapeHtml(scene.visualTitle)}</h2>
        <div class="purple-terminal-card">
          <div class="terminal-header">
            <div class="term-controls">
              <span class="term-dot dot-purple"></span>
              <span class="term-dot dot-lavender"></span>
              <span class="term-dot dot-lime"></span>
            </div>
            <span class="term-title">${escapeHtml(scene.terminalTitle || "anthropic_cache.py")}</span>
            <span class="term-lang">${escapeHtml(scene.terminalLang || "Python")}</span>
          </div>
          <div class="terminal-body">
            <pre><code>${escapeHtml(scene.codeSnippet || scene.visualBody)}</code><span class="typing-cursor">|</span></pre>
          </div>
        </div>
      `;
    } else if (cardType === "comparison") {
      // Asymmetric before/after collage
      cardContent = `
        <div class="purple-badge">
          <span class="badge-dot pulse-lime"></span>
          ${escapeHtml(scene.badge || "COMPARISON")}
        </div>
        <h2 class="scene-title">${escapeHtml(scene.visualTitle)}</h2>
        <div class="compare-collage-grid">
          <div class="compare-box box-unoptimized">
            <div class="box-label cross-label">✕ LEGACY RE-INGESTION</div>
            <p class="compare-desc">${escapeHtml(scene.oldWay || "Re-sending 100K context tokens every prompt causes high latency.")}</p>
          </div>
          <div class="compare-box box-optimized">
            <div class="box-label check-label">✓ PROMPT CACHING</div>
            <p class="compare-desc">${escapeHtml(scene.newWay || "Static prefix pinned in RAM: up to 90% latency reduction.")}</p>
          </div>
        </div>
      `;
    } else if (cardType === "asset-reveal") {
      cardContent = `
        <div class="purple-badge">
          <span class="badge-dot pulse-lime"></span>
          ${escapeHtml(scene.badge || "VERIFIED MEDIA")}
        </div>
        <h2 class="scene-title">${escapeHtml(scene.visualTitle)}</h2>
        <div class="diagram-hero-frame">
          <img src="./assets/scouted/${scene._assetFilename || 'diagram.svg'}" class="scouted-asset-img" alt="${escapeHtml(scene.visualTitle)}" />
          <div class="diagram-caption-strip">
            <span class="caption-text">${escapeHtml(scene.visualBody)}</span>
            ${scene.assetData?.attributionText ? `<span class="asset-attribution-badge">${escapeHtml(scene.assetData.attributionText)}</span>` : ""}
          </div>
        </div>
      `;
    } else {
      // Concept Explainer / Definitive Takeaway
      cardContent = `
        <div class="purple-badge">
          <span class="badge-dot pulse-lime"></span>
          ${escapeHtml(scene.badge || "KEY TAKEAWAY")}
        </div>
        <h2 class="scene-title">${escapeHtml(scene.visualTitle)}</h2>
        <div class="takeaway-collage-card">
          <div class="takeaway-header">
            <span class="takeaway-stamp">ARCHITECTURAL RULE</span>
          </div>
          <p class="card-highlight">${escapeHtml(scene.visualBody)}</p>
          ${scene.source ? `<div class="source-tag">Reference: ${escapeHtml(scene.source)}</div>` : ""}
        </div>
      `;
    }

    return `
      <div id="scene-${idx}" class="scene-layer clip" data-start="${scene.startTime}" data-duration="${scene.duration}" style="opacity: ${isFirst ? 1 : 0};">
        ${cardContent}
      </div>
    `;
  }).join("\n");

  // Build Kinetic Subtitle Containers in safe zone
  const subtitleScenesHtml = scenes.map((scene, idx) => {
    const words = scene.voiceText.trim().split(/\s+/);
    const wordsHtml = words
      .map((w, wIdx) => `<span class="cap-word" id="w-${idx}-${wIdx}">${escapeHtml(w)}</span>`)
      .join(" ");

    return `
      <div id="sub-scene-${idx}" class="sub-scene ${idx === 0 ? "active" : ""}">
        ${wordsHtml}
      </div>
    `;
  }).join("\n");

  // Build GSAP Animation Timeline
  const ambientRepeats = Math.ceil(totalDuration / 3.0);
  const cursorRepeats = Math.max(0, Math.floor(totalDuration / 0.45));
  let gsapTimelineScript = `
    window.__timelines = window.__timelines || {};
    const tl = gsap.timeline({ paused: true });

    // Continuous Subtle Virtual Camera push-in
    tl.to("#stage-camera", { scale: 1.035, duration: ${totalDuration}, ease: "none" }, 0);

    // Ambient floating purple & lime aura glow
    tl.to("#orb-violet", { scale: 1.25, x: 25, y: -20, opacity: 0.7, duration: 3.2, yoyo: true, repeat: ${ambientRepeats}, ease: "sine.inOut" }, 0);
    tl.to("#orb-lime", { scale: 1.2, x: -20, y: 30, opacity: 0.6, duration: 3.6, yoyo: true, repeat: ${ambientRepeats}, ease: "sine.inOut" }, 0);
    tl.to("#top-progress", { width: "100%", duration: ${totalDuration}, ease: "none" }, 0);

    // Cursor blink
    tl.to(".typing-cursor", { opacity: 0, duration: 0.45, repeat: ${cursorRepeats}, yoyo: true, ease: "steps(1)" }, 0);
  `;

  // Animate scenes and kinetic word highlights
  scenes.forEach((scene, idx) => {
    const isFirst = idx === 0;
    const startT = scene.startTime;
    const duration = scene.duration;

    if (isFirst) {
      gsapTimelineScript += `
        // Scene ${idx} Entrance (Hook)
        tl.from("#scene-${idx} .purple-badge", { scale: 0.85, opacity: 0, y: -25, duration: 0.5, ease: "back.out(1.6)" }, ${startT});
        tl.from("#scene-${idx} .hero-headline", { opacity: 0, y: 35, duration: 0.6, ease: "power3.out" }, ${startT + 0.12});
        tl.from("#scene-${idx} .collage-hero-card", { opacity: 0, y: 45, scale: 0.94, duration: 0.65, ease: "back.out(1.3)" }, ${startT + 0.25});
        tl.from("#scene-${idx} .surreal-icon", { rotation: -20, scale: 0.5, opacity: 0, duration: 0.6, ease: "back.out(1.8)" }, ${startT + 0.35});
      `;
    } else {
      gsapTimelineScript += `
        // Transition Scene ${idx - 1} -> Scene ${idx}
        tl.to("#scene-${idx - 1}", { opacity: 0, scale: 0.96, y: -25, duration: 0.3, ease: "power2.in" }, ${startT - 0.2});
        tl.fromTo("#scene-${idx}", 
          { opacity: 0, scale: 1.04, y: 30 },
          { opacity: 1, scale: 1, y: 0, duration: 0.45, ease: "power3.out" },
          ${startT}
        );

        // Subtitle scene switch
        tl.call(() => {
          document.querySelectorAll('.sub-scene').forEach(el => el.classList.remove('active'));
          const target = document.getElementById("sub-scene-${idx}");
          if (target) target.classList.add('active');
        }, null, ${startT});
      `;
    }

    if (scene._assetFilename) {
      gsapTimelineScript += `
        tl.from("#scene-${idx} .diagram-hero-frame", {
          scale: 0.92,
          opacity: 0,
          y: 20,
          duration: 0.5,
          ease: "back.out(1.4)"
        }, ${startT + 0.2});
      `;
    }

    // Kinetic word-by-word active captioning
    const words = scene.voiceText.trim().split(/\s+/);
    const wordDur = Math.max(0.18, duration / words.length);

    words.forEach((w, wIdx) => {
      const wStart = startT + (wIdx * wordDur);
      const wEnd = wStart + (wordDur * 0.9);

      gsapTimelineScript += `
        tl.to("#w-${idx}-${wIdx}", {
          color: "#a3e635",
          backgroundColor: "rgba(163, 230, 53, 0.18)",
          scale: 1.15,
          opacity: 1,
          duration: 0.12,
          ease: "back.out(1.5)"
        }, ${wStart});

        tl.to("#w-${idx}-${wIdx}", {
          color: "#e2e8f0",
          backgroundColor: "transparent",
          scale: 1.0,
          duration: 0.14,
          ease: "power2.out"
        }, ${wEnd});
      `;
    });
  });

  gsapTimelineScript += `
    window.__timelines["${id}"] = tl;
  `;

  const htmlContent = `<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <title>${escapeHtml(title)}</title>
    <!-- Local Offline Vendored GSAP -->
    <script src="./assets/vendor/gsap.min.js"></script>
    <style>
      * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
      }
      html, body {
        width: 1080px;
        height: 1920px;
        overflow: hidden;
        background-color: #0b0518;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        color: #f8fafc;
      }
      .composition-root {
        position: relative;
        width: 1080px;
        height: 1920px;
        background: radial-gradient(circle at 50% 15%, #241147 0%, #13082a 55%, #080312 100%);
        overflow: hidden;
      }

      /* Tactile Halftone Dot-Matrix Pattern */
      .halftone-overlay {
        position: absolute;
        inset: 0;
        background-image: radial-gradient(rgba(192, 132, 252, 0.13) 1.5px, transparent 1.5px);
        background-size: 26px 26px;
        pointer-events: none;
        z-index: 2;
      }

      /* Ambient Atmospheric Glows */
      .glow-orb {
        position: absolute;
        border-radius: 50%;
        filter: blur(100px);
        pointer-events: none;
        z-index: 1;
      }
      .orb-violet {
        width: 700px;
        height: 700px;
        background: radial-gradient(circle, rgba(168, 85, 247, 0.22) 0%, rgba(168, 85, 247, 0) 70%);
        top: 8%;
        left: -150px;
      }
      .orb-lime {
        width: 550px;
        height: 550px;
        background: radial-gradient(circle, rgba(163, 230, 53, 0.16) 0%, rgba(163, 230, 53, 0) 70%);
        top: 50%;
        right: -120px;
      }

      /* Virtual Camera Wrapper */
      .camera-viewport {
        position: absolute;
        inset: 0;
        transform-origin: center center;
        z-index: 3;
      }

      /* Top Progress Bar & Header */
      .top-progress-track {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 8px;
        background: rgba(255, 255, 255, 0.08);
        z-index: 50;
      }
      .top-progress-bar {
        height: 100%;
        width: 0%;
        background: linear-gradient(90deg, #c084fc, #a3e635, #c084fc);
        box-shadow: 0 0 14px rgba(163, 230, 53, 0.7);
      }
      .top-bar {
        position: absolute;
        top: 80px;
        left: 90px;
        right: 90px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        z-index: 20;
      }
      .brand-badge {
        display: inline-flex;
        align-items: center;
        gap: 12px;
        font-size: 24px;
        font-weight: 800;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: #e2e8f0;
      }
      .brand-dot {
        width: 14px;
        height: 14px;
        border-radius: 50%;
        background-color: #a3e635;
        box-shadow: 0 0 14px #a3e635;
      }

      /* Scene Stage (Inside Safe-Zone: Y 250 to 1420) */
      .scene-stage {
        position: absolute;
        top: 250px;
        left: 90px;
        width: 900px;
        height: 1150px;
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10;
      }
      .scene-layer {
        position: absolute;
        width: 100%;
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
      }

      /* Badges & Headlines */
      .purple-badge {
        display: inline-flex;
        align-items: center;
        gap: 10px;
        padding: 10px 24px;
        border-radius: 9999px;
        background: rgba(192, 132, 252, 0.12);
        border: 1px solid rgba(192, 132, 252, 0.35);
        color: #e9d5ff;
        font-size: 22px;
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        margin-bottom: 28px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
      }
      .pulse-lime {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background-color: #a3e635;
        box-shadow: 0 0 12px #a3e635;
      }
      .pulse-violet {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background-color: #c084fc;
        box-shadow: 0 0 12px #c084fc;
      }
      .hero-headline {
        font-size: 74px;
        font-weight: 900;
        line-height: 1.15;
        letter-spacing: -0.03em;
        color: #ffffff;
        margin-bottom: 34px;
        max-width: 860px;
        text-shadow: 0 4px 20px rgba(0, 0, 0, 0.6);
      }
      .scene-title {
        font-size: 56px;
        font-weight: 800;
        line-height: 1.2;
        letter-spacing: -0.02em;
        color: #ffffff;
        margin-bottom: 30px;
        max-width: 860px;
      }

      /* Collage Hero Card */
      .collage-hero-card {
        width: 100%;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 20px;
      }
      .surreal-object-container {
        position: relative;
        width: 140px;
        height: 140px;
        display: flex;
        align-items: center;
        justify-content: center;
      }
      .surreal-glow-ring {
        position: absolute;
        inset: 0;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(163, 230, 53, 0.25) 0%, transparent 70%);
        border: 2px dashed rgba(163, 230, 53, 0.6);
        animation: rotateRing 15s linear infinite;
      }
      @keyframes rotateRing {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
      }
      .surreal-icon {
        font-size: 64px;
        color: #a3e635;
        filter: drop-shadow(0 0 16px rgba(163, 230, 53, 0.8));
      }
      .hero-statement-box {
        width: 100%;
        border-radius: 24px;
        padding: 36px 40px;
        background: rgba(30, 16, 56, 0.85);
        border: 1px solid rgba(192, 132, 252, 0.3);
        box-shadow: 0 24px 50px rgba(0, 0, 0, 0.45);
        text-align: left;
      }
      .card-tag {
        font-size: 20px;
        font-weight: 700;
        color: #a3e635;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        margin-bottom: 12px;
      }
      .card-highlight {
        font-size: 34px;
        font-weight: 600;
        line-height: 1.35;
        color: #f1f5f9;
        margin-bottom: 18px;
      }
      .source-tag {
        font-size: 20px;
        font-weight: 500;
        color: #94a3b8;
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        padding-top: 14px;
      }

      /* Diagram Hero Frame (Large, Prominent, Non-Cramped) */
      .diagram-hero-frame {
        width: 100%;
        border-radius: 28px;
        background: rgba(22, 12, 42, 0.9);
        border: 2px solid rgba(192, 132, 252, 0.35);
        box-shadow: 0 24px 60px rgba(0, 0, 0, 0.55);
        padding: 24px;
        display: flex;
        flex-direction: column;
        align-items: center;
      }
      .scouted-asset-img {
        max-width: 100%;
        max-height: 480px;
        object-fit: contain;
        border-radius: 16px;
      }
      .diagram-caption-strip {
        width: 100%;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 18px;
        padding-top: 14px;
        border-top: 1px solid rgba(255, 255, 255, 0.08);
      }
      .caption-text {
        font-size: 22px;
        font-weight: 600;
        color: #e2e8f0;
      }
      .asset-attribution-badge {
        font-size: 15px;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: #c084fc;
        padding: 6px 14px;
        border-radius: 9999px;
        background: rgba(192, 132, 252, 0.12);
        border: 1px solid rgba(192, 132, 252, 0.3);
      }

      /* Procedural Purple Flow Diagram */
      .purple-flow-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 16px;
        width: 100%;
        margin-bottom: 24px;
      }
      .purple-flow-node {
        flex: 1;
        padding: 24px 16px;
        border-radius: 20px;
        background: rgba(36, 18, 66, 0.9);
        border: 1px solid rgba(192, 132, 252, 0.35);
        text-align: center;
        box-shadow: 0 12px 30px rgba(0, 0, 0, 0.35);
      }
      .node-icon-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background: #a3e635;
        box-shadow: 0 0 10px #a3e635;
        margin: 0 auto 10px auto;
      }
      .node-title {
        font-size: 24px;
        font-weight: 700;
        color: #ffffff;
      }
      .node-sub {
        font-size: 18px;
        color: #cbd5e1;
        margin-top: 4px;
      }
      .purple-flow-arrow {
        font-size: 30px;
        color: #a3e635;
        font-weight: 800;
      }
      .collage-note-box {
        width: 100%;
        padding: 24px 30px;
        border-radius: 20px;
        background: rgba(22, 12, 42, 0.8);
        border: 1px solid rgba(192, 132, 252, 0.2);
        text-align: left;
      }

      /* Physical Metaphor Stage */
      .metaphor-collage-stage {
        width: 100%;
        display: flex;
        flex-direction: column;
        gap: 20px;
      }
      .conveyor-block {
        width: 100%;
        padding: 30px;
        border-radius: 24px;
        background: rgba(26, 14, 50, 0.9);
        border: 1px solid rgba(163, 230, 53, 0.35);
        box-shadow: 0 20px 48px rgba(0, 0, 0, 0.45);
      }
      .conveyor-track {
        display: flex;
        flex-direction: column;
        gap: 14px;
      }
      .conveyor-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 18px 24px;
        border-radius: 16px;
      }
      .item-static {
        background: rgba(192, 132, 252, 0.15);
        border: 1px solid rgba(192, 132, 252, 0.4);
      }
      .item-dynamic {
        background: rgba(163, 230, 53, 0.15);
        border: 1px solid rgba(163, 230, 53, 0.4);
      }
      .item-tag {
        font-size: 18px;
        font-weight: 800;
        letter-spacing: 0.08em;
        color: #ffffff;
      }
      .item-desc {
        font-size: 20px;
        color: #cbd5e1;
      }
      .item-status {
        font-size: 18px;
        font-weight: 700;
        color: #a3e635;
      }
      .conveyor-arrow {
        font-size: 20px;
        font-weight: 800;
        color: #c084fc;
        text-align: center;
      }
      .ttl-badge {
        margin-top: 18px;
        font-size: 18px;
        font-weight: 700;
        color: #e9d5ff;
        text-align: center;
        letter-spacing: 0.04em;
      }
      .metaphor-caption {
        text-align: left;
        margin-bottom: 0;
      }

      /* Purple Terminal Card */
      .purple-terminal-card {
        width: 100%;
        border-radius: 28px;
        background: #100722;
        border: 1px solid rgba(192, 132, 252, 0.3);
        box-shadow: 0 24px 60px rgba(0, 0, 0, 0.55);
        overflow: hidden;
        text-align: left;
      }
      .terminal-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 18px 26px;
        background: #1a0e36;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      }
      .term-controls {
        display: flex;
        gap: 10px;
      }
      .term-dot {
        width: 14px;
        height: 14px;
        border-radius: 50%;
      }
      .dot-purple { background-color: #c084fc; }
      .dot-lavender { background-color: #e9d5ff; }
      .dot-lime { background-color: #a3e635; }
      .term-title {
        font-size: 20px;
        font-weight: 600;
        font-family: monospace;
        color: #e2e8f0;
      }
      .term-lang {
        font-size: 16px;
        font-weight: 700;
        text-transform: uppercase;
        color: #a3e635;
      }
      .terminal-body {
        padding: 32px 36px;
        font-family: "SF Mono", Consolas, Menlo, Monaco, "Courier New", monospace;
        font-size: 24px;
        line-height: 1.5;
        color: #e2e8f0;
      }
      .terminal-body pre {
        white-space: pre-wrap;
        word-break: break-all;
      }
      .typing-cursor {
        color: #a3e635;
        font-weight: 800;
      }

      /* Comparison Collage Grid */
      .compare-collage-grid {
        display: flex;
        flex-direction: column;
        gap: 20px;
        width: 100%;
      }
      .compare-box {
        padding: 28px 32px;
        border-radius: 20px;
        text-align: left;
      }
      .box-unoptimized {
        background: rgba(40, 16, 28, 0.85);
        border: 1px solid rgba(244, 63, 94, 0.35);
      }
      .box-optimized {
        background: rgba(22, 38, 26, 0.85);
        border: 1px solid rgba(163, 230, 53, 0.4);
      }
      .box-label {
        font-size: 20px;
        font-weight: 800;
        letter-spacing: 0.08em;
        margin-bottom: 10px;
      }
      .cross-label { color: #fb7185; }
      .check-label { color: #a3e635; }
      .compare-desc {
        font-size: 26px;
        font-weight: 600;
        line-height: 1.3;
        color: #f1f5f9;
      }

      /* Takeaway Collage Card */
      .takeaway-collage-card {
        width: 100%;
        padding: 38px 42px;
        border-radius: 28px;
        background: rgba(30, 16, 56, 0.9);
        border: 2px solid rgba(163, 230, 53, 0.4);
        box-shadow: 0 24px 60px rgba(0, 0, 0, 0.5);
        text-align: left;
      }
      .takeaway-header {
        margin-bottom: 16px;
      }
      .takeaway-stamp {
        display: inline-block;
        padding: 8px 18px;
        border-radius: 8px;
        background: #a3e635;
        color: #0d061c;
        font-size: 18px;
        font-weight: 900;
        letter-spacing: 0.1em;
        text-transform: uppercase;
      }

      /* Kinetic Active Captions (Safe Zone: Y 1460 to 1580) */
      .captions-wrapper {
        position: absolute;
        bottom: 240px;
        left: 90px;
        width: 900px;
        height: 180px;
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 40;
      }
      .caption-pill-backdrop {
        width: 100%;
        padding: 22px 30px;
        border-radius: 24px;
        background: rgba(14, 7, 28, 0.88);
        border: 1px solid rgba(192, 132, 252, 0.3);
        box-shadow: 0 16px 40px rgba(0, 0, 0, 0.5);
        backdrop-filter: blur(12px);
        text-align: center;
      }
      .sub-scene {
        display: none;
        flex-wrap: wrap;
        justify-content: center;
        gap: 12px 14px;
      }
      .sub-scene.active {
        display: flex;
      }
      .cap-word {
        font-size: 34px;
        font-weight: 700;
        letter-spacing: -0.01em;
        color: #cbd5e1;
        display: inline-block;
        padding: 2px 8px;
        border-radius: 6px;
        transition: transform 0.1s ease;
      }
    </style>
  </head>
  <body>
    <div class="composition-root" data-composition-id="${id}" data-width="1080" data-height="1920" data-duration="${totalDuration}">
      <div class="halftone-overlay"></div>
      <div id="orb-violet" class="glow-orb orb-violet"></div>
      <div id="orb-lime" class="glow-orb orb-lime"></div>

      <div class="camera-viewport" id="stage-camera">
        <!-- Top Track & Header -->
        <div class="top-progress-track">
          <div id="top-progress" class="top-progress-bar"></div>
        </div>
        <header class="top-bar">
          <div class="brand-badge">
            <span class="brand-dot"></span>
            AI SIMPLIFIED LAB
          </div>
        </header>

        <!-- Main Scene Stage -->
        <main class="scene-stage">
          ${scenesHtml}
        </main>
      </div>

      <!-- Kinetic Captions Frame -->
      <footer class="captions-wrapper">
        <div class="caption-pill-backdrop">
          ${subtitleScenesHtml}
        </div>
      </footer>
    </div>

    <!-- Timeline Animation Script -->
    <script>
      ${gsapTimelineScript}
    </script>
  </body>
</html>`;

  await fs.writeFile(path.join(compDir, "index.html"), htmlContent, "utf8");
  return { compDir, scenesCount: scenes.length };
}
