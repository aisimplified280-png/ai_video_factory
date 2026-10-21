import fs from "node:fs/promises";
import path from "node:path";
import { ROOT_DIR } from "./config.mjs";
import { renderLabGuideSvg, getLabGuideCss } from "./character-director.mjs";

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
    const metaphor = scene.sceneGraph?.visualMetaphor || "";

    if (metaphor === "linear-scan-bottleneck") {
      cardContent = `
        <div class="purple-badge">
          <span class="badge-dot pulse-lime"></span>
          ${escapeHtml(scene.badge || "VECTOR SEARCH SCALING")}
        </div>
        <h1 class="hero-headline">${escapeHtml(scene.visualTitle)}</h1>
        <div class="linear-scan-stage" id="linear-stage">
          <div class="dense-vector-cloud" id="vector-dense-field">
            ${Array.from({ length: 48 }).map((_, i) => `<span class="vec-point pt-${i}"></span>`).join("")}
            <div class="linear-search-marker" id="linear-search-marker">
              <span class="marker-pulse"></span>
              <span class="marker-icon">🔍</span>
            </div>
          </div>
          <div class="scan-status-panel">
            <div class="search-counter" id="search-counter">
              <span class="counter-label">COMPARISON COUNT</span>
              <span class="counter-num">1,420,891 / 10,000,000</span>
            </div>
            <div class="bottleneck-indicator" id="bottleneck-indicator">
              <span class="stall-badge">⚠️ O(N) LINEAR BOTTLENECK</span>
              <p class="stall-msg">Throughput collapsed: Unscalable for live inference</p>
            </div>
          </div>
        </div>
      `;
    } else if (metaphor === "hnsw-express-highway") {
      cardContent = `
        <div class="purple-badge">
          <span class="badge-dot pulse-lime"></span>
          ${escapeHtml(scene.badge || "EXPRESS HIGHWAY METAPHOR")}
        </div>
        <h2 class="scene-title">${escapeHtml(scene.visualTitle)}</h2>
        <div class="metaphor-collage-stage">
          <div class="hnsw-highway-stage" id="highway-tiers">
            <div class="highway-tier tier-express">
              <div class="tier-label">TOP LAYER 2 • EXPRESS HIGHWAY</div>
              <div class="highway-track express-track">
                <div class="highway-node active-node" id="node-a">Node A</div>
                <div class="express-arc" id="express-arc">
                  <svg class="express-svg" width="360" height="36" viewBox="0 0 360 36">
                    <path id="express-bridge-path" d="M 10 18 Q 180 -2 350 18" stroke="#a3e635" stroke-width="4" fill="none" stroke-dasharray="8 6"/>
                  </svg>
                  <span class="express-text">═════ 99% Express Skip ═════➔</span>
                </div>
                <div class="highway-node active-node" id="node-b">Node B</div>
                <div class="search-probe" id="search-probe">
                  <span class="probe-core"></span>
                  <span class="probe-glow"></span>
                </div>
              </div>
              <div class="tier-sub">Skips dense local clusters via sparse upper shortcuts</div>
            </div>

            <div class="highway-tier tier-mid">
              <div class="tier-label">LAYER 1 • CLUSTER ROUTING</div>
              <div class="highway-track">
                <div class="highway-node">A₁</div>
                <div class="local-arc">───➔</div>
                <div class="highway-node active-node" id="mid-node-active">A₂</div>
                <div class="local-arc">───➔</div>
                <div class="highway-node">A₃</div>
              </div>
            </div>

            <div class="highway-tier tier-base">
              <div class="tier-label">BASE LAYER 0 • EXACT NEAREST NEIGHBORS</div>
              <div class="highway-track base-grid">
                <span class="base-dot"></span>
                <span class="base-dot"></span>
                <span class="base-dot target-hit">🎯 Target Nearest Vector</span>
                <span class="base-dot"></span>
                <span class="base-dot"></span>
              </div>
            </div>

            <div class="skip-counter-badge" id="skip-counter">
              <span class="benchmark-tag">BENCHMARK (1M Vectors):</span> ~99% Skip Ratio via O(log N) Traversal
            </div>
          </div>
          <p class="card-highlight metaphor-caption">${escapeHtml(scene.visualBody)}</p>
        </div>
      `;
    } else if (metaphor === "coarse-to-fine-graph-descent") {
      cardContent = `
        <div class="purple-badge">
          <span class="badge-dot pulse-violet"></span>
          ${escapeHtml(scene.badge || "GRAPH NAVIGATION")}
        </div>
        <h2 class="scene-title">${escapeHtml(scene.visualTitle)}</h2>
        <div class="metaphor-collage-stage">
          <div class="descent-navigation-stage" id="descent-stage">
            <div class="nav-tier tier-top">
              <div class="nav-tier-header">LAYER 2 • ENTRY HOP</div>
              <div class="nav-nodes-row">
                <div class="graph-node entry-node" id="entry-node-l2">
                  <span class="node-icon-dot"></span>
                  Entry Point (Top Layer)
                </div>
              </div>
            </div>

            <div class="descent-beam-container">
              <svg class="beam-svg" width="100%" height="60" viewBox="0 0 400 60">
                <line id="descent-beam" x1="200" y1="0" x2="200" y2="60" stroke="#c084fc" stroke-width="4" stroke-dasharray="6 4"/>
              </svg>
              <div class="query-descent-probe" id="query-descent-probe">
                <span class="probe-light"></span>
              </div>
            </div>

            <div class="nav-tier tier-mid">
              <div class="nav-tier-header">LAYER 1 • LOCAL CLUSTER HOPS</div>
              <div class="nav-nodes-row">
                <div class="graph-node" id="intermediate-node-l1">Intermediate Hop A₂</div>
                <div class="local-arc">➔</div>
                <div class="graph-node">Cluster Hub</div>
              </div>
            </div>

            <div class="descent-beam-container">
              <svg class="beam-svg" width="100%" height="50" viewBox="0 0 400 50">
                <line x1="200" y1="0" x2="200" y2="50" stroke="#a3e635" stroke-width="4" stroke-dasharray="6 4"/>
              </svg>
            </div>

            <div class="nav-tier tier-base">
              <div class="nav-tier-header">BASE LAYER 0 • EXACT CONVERGENCE</div>
              <div class="base-vector-cluster" id="base-cluster">
                <span class="dim-dot"></span>
                <span class="dim-dot"></span>
                <div class="target-beacon" id="target-beacon-l0">
                  <span class="convergence-ring" id="convergence-ring"></span>
                  🎯 Exact Nearest Vector
                </div>
                <span class="dim-dot"></span>
                <span class="dim-dot"></span>
              </div>
            </div>
          </div>
          <p class="card-highlight metaphor-caption">${escapeHtml(scene.visualBody)}</p>
        </div>
      `;
    } else if (metaphor === "architectural-production-rule") {
      cardContent = `
        <div class="purple-badge">
          <span class="badge-dot pulse-lime"></span>
          ${escapeHtml(scene.badge || "PRODUCTION STANDARD")}
        </div>
        <h2 class="scene-title">${escapeHtml(scene.visualTitle)}</h2>
        <div class="takeaway-collage-card" id="rule-stamp">
          <div class="takeaway-header">
            <span class="takeaway-stamp">ARCHITECTURAL RULE</span>
          </div>
          <div class="param-metrics-grid" id="param-metrics">
            <div class="metric-card">
              <span class="metric-key">M (Max Edges)</span>
              <span class="metric-val">16 – 64</span>
              <span class="metric-desc">Controls recall &amp; RAM</span>
            </div>
            <div class="metric-card">
              <span class="metric-key">efConstruction</span>
              <span class="metric-val">100 – 200</span>
              <span class="metric-desc">Index build precision</span>
            </div>
          </div>
          <div class="latency-gauge-box" id="latency-gauge">
            <div class="gauge-label">SEARCH COMPLEXITY ADVANTAGE</div>
            <div class="gauge-value" id="gauge-val">O(log N)</div>
            <div class="gauge-sub">Sub-Millisecond Logarithmic Traversal vs O(N)</div>
          </div>
          <p class="card-highlight">${escapeHtml(scene.visualBody)}</p>
          ${scene.source ? `<div class="source-tag">Reference: ${escapeHtml(scene.source)}</div>` : ""}
        </div>
      `;
    } else if (cardType === "hook" || cardType === "hook-bold-object") {
      // Full-frame hook with surreal dimensional object & oversized typography
      const isVector = (scene.visualTitle || "").toLowerCase().includes("vector") || (title || "").toLowerCase().includes("vector");
      const iconSymbol = isVector ? "🧭" : "⚡";
      cardContent = `
        <div class="purple-badge">
          <span class="badge-dot pulse-lime"></span>
          ${escapeHtml(scene.badge || "AI BOTTLENECK")}
        </div>
        <h1 class="hero-headline">${escapeHtml(scene.visualTitle)}</h1>
        <div class="collage-hero-card">
          <div class="surreal-object-container">
            <div class="surreal-glow-ring"></div>
            <div class="surreal-icon">${iconSymbol}</div>
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
      // Pinned memory / Token conveyor metaphor
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
    } else if (cardType === "subscribe-outro") {
      cardContent = `
        <div class="purple-badge">
          <span class="badge-dot pulse-lime"></span>
          ${escapeHtml(scene.badge || "AI SIMPLIFIED LAB")}
        </div>
        <div class="subscribe-outro-stage" id="outro-stage">
          <h2 class="outro-headline">${escapeHtml(scene.visualTitle || "Subscribe for Honest AI Workflows")}</h2>
          <p class="outro-subline">${escapeHtml(scene.visualBody || "Zero fluff. Real code architectures.")}</p>

          <div class="cta-interaction-container">
            <div class="yt-subscribe-btn" id="yt-sub-btn">
              <span class="sub-play-icon">▶</span>
              <span class="sub-btn-text" id="sub-btn-text">SUBSCRIBE</span>
            </div>
            <div class="yt-bell-btn" id="yt-bell-btn">
              <span class="bell-icon">🔔</span>
            </div>
          </div>

          <div class="outro-guide-anchor">
            ${renderLabGuideSvg("outro-cta", "guide-outro")}
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

    let charHtml = "";
    const cue = scene.characterCue;
    if (cue && cue.visible && cardType !== "subscribe-outro") {
      charHtml = renderLabGuideSvg(cue.pose || "direct", `guide-scene-${idx}`, {
        position: cue.position || "bottom-left",
        scale: cue.scale || "compact",
      });
    }

    return `
      <div id="scene-${idx}" class="scene-layer clip" data-start="${scene.startTime}" data-duration="${scene.duration}" style="opacity: ${isFirst ? 1 : 0};">
        ${cardContent}
        ${charHtml}
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

  // Helper: Build element-level GSAP motion choreography from sceneGraph.actions
  function buildMotionChoreographyScript(scene, idx) {
    if (!scene.sceneGraph || !Array.isArray(scene.sceneGraph.actions)) return "";
    let script = `\n        // --- Scene ${idx} Motion Choreography (${scene.sceneGraph.visualMetaphor}) ---\n`;
    const words = scene.voiceText.trim().split(/\s+/);
    const totalWords = Math.max(1, words.length);
    const startT = scene.startTime;
    const dur = scene.duration;

    scene.sceneGraph.actions.forEach((act) => {
      // 1. Calculate precise trigger timestamp
      let actionTime = startT + (dur * 0.25);
      if (act.trigger === "spoken-phrase" && act.phrase) {
        const phraseWords = act.phrase.trim().toLowerCase().split(/\s+/);
        const firstWord = phraseWords[0].replace(/[^a-z0-9]/g, "");
        let foundWordIdx = -1;
        for (let w = 0; w < words.length; w++) {
          const cleanW = words[w].toLowerCase().replace(/[^a-z0-9]/g, "");
          if (cleanW === firstWord) {
            foundWordIdx = w;
            break;
          }
        }
        if (foundWordIdx >= 0) {
          actionTime = startT + (foundWordIdx / totalWords) * dur;
        }
      } else if (act.trigger === "timestamp" && typeof act.timestamp === "number") {
        actionTime = act.timestamp;
      }
      actionTime = Math.max(startT + 0.1, Math.min(startT + dur - 0.35, actionTime));
      const actionDur = Math.min(act.duration || 1.0, dur - (actionTime - startT) - 0.1);

      switch (act.action) {
        case "step-scan-points":
          script += `
          // Action: step-scan-points on #${act.target}
          tl.fromTo("#scene-${idx} #${act.target}", 
            { x: -260, opacity: 0, scale: 0.8 }, 
            { x: -90, opacity: 1, scale: 1, duration: ${Math.min(0.5, actionDur * 0.3).toFixed(2)}, ease: "power2.out" }, 
            ${actionTime.toFixed(3)}
          );
          tl.to("#scene-${idx} #${act.target}", { 
            x: 80, 
            duration: ${Math.min(0.6, actionDur * 0.35).toFixed(2)}, 
            ease: "steps(4)" 
          }, ${(actionTime + Math.min(0.5, actionDur * 0.3)).toFixed(3)});
          tl.to("#scene-${idx} #${act.target}", { 
            x: 240, 
            duration: ${Math.min(0.6, actionDur * 0.35).toFixed(2)}, 
            ease: "power1.inOut" 
          }, ${(actionTime + Math.min(0.5, actionDur * 0.3) + Math.min(0.6, actionDur * 0.35)).toFixed(3)});
          tl.to("#scene-${idx} .vec-point:nth-child(-n+24)", { 
            backgroundColor: "#c084fc", 
            scale: 1.25, 
            duration: 0.3, 
            stagger: 0.02 
          }, ${(actionTime + 0.15).toFixed(3)});
          tl.to("#scene-${idx} .counter-num", { 
            color: "#facc15", 
            duration: 0.6 
          }, ${actionTime.toFixed(3)});
          `;
          break;

        case "stall-and-flash-bottleneck":
          script += `
          // Action: stall-and-flash-bottleneck on #${act.target}
          tl.to("#scene-${idx} #linear-search-marker", { 
            x: "+=8", 
            yoyo: true, 
            repeat: 7, 
            duration: 0.07, 
            ease: "sine.inOut" 
          }, ${actionTime.toFixed(3)});
          tl.fromTo("#scene-${idx} #${act.target}", 
            { y: 25, opacity: 0, scale: 0.92 }, 
            { y: 0, opacity: 1, scale: 1, duration: 0.45, ease: "back.out(1.8)" }, 
            ${actionTime.toFixed(3)}
          );
          tl.to("#scene-${idx} #${act.target}", { 
            backgroundColor: "rgba(239, 68, 68, 0.28)", 
            borderColor: "#ef4444", 
            boxShadow: "0 0 24px rgba(239, 68, 68, 0.7)", 
            duration: 0.25, 
            yoyo: true, 
            repeat: 3 
          }, ${(actionTime + 0.35).toFixed(3)});
          tl.to("#scene-${idx} .counter-num", { 
            color: "#ef4444", 
            duration: 0.2 
          }, ${(actionTime + 0.3).toFixed(3)});
          `;
          break;

        case "enter-probe-and-lock-node-a":
          script += `
          // Action: enter-probe-and-lock-node-a on #${act.target}
          tl.fromTo("#scene-${idx} #${act.target}", 
            { scale: 0, opacity: 0, x: -20 }, 
            { scale: 1, opacity: 1, x: 0, duration: ${Math.min(0.5, actionDur).toFixed(2)}, ease: "back.out(2)" }, 
            ${actionTime.toFixed(3)}
          );
          tl.to("#scene-${idx} #node-a", { 
            borderColor: "#a3e635", 
            boxShadow: "0 0 22px rgba(163, 230, 53, 0.85)", 
            scale: 1.12, 
            duration: 0.35 
          }, ${(actionTime + 0.15).toFixed(3)});
          `;
          break;

        case "traverse-express-bridge":
          script += `
          // Action: traverse-express-bridge on #${act.target}
          tl.fromTo("#scene-${idx} #express-bridge-path", 
            { strokeDashoffset: 120 }, 
            { strokeDashoffset: 0, duration: ${Math.min(1.2, actionDur).toFixed(2)}, ease: "power2.inOut" }, 
            ${actionTime.toFixed(3)}
          );
          tl.to("#scene-${idx} #${act.target}", { 
            x: 380, 
            duration: ${Math.min(1.4, actionDur).toFixed(2)}, 
            ease: "power2.inOut" 
          }, ${(actionTime + 0.15).toFixed(3)});
          tl.to("#scene-${idx} #${act.target} .probe-glow", { 
            scale: 2.4, 
            opacity: 0.9, 
            duration: 0.6, 
            yoyo: true, 
            repeat: 1 
          }, ${(actionTime + 0.2).toFixed(3)});
          `;
          break;

        case "illuminate-express-nodes":
          script += `
          // Action: illuminate-express-nodes on #${act.target}
          tl.to("#scene-${idx} #${act.target}", { 
            borderColor: "#a3e635", 
            boxShadow: "0 0 26px rgba(163, 230, 53, 0.9)", 
            scale: 1.15, 
            duration: 0.35, 
            ease: "back.out(2)" 
          }, ${actionTime.toFixed(3)});
          tl.fromTo("#scene-${idx} #skip-counter", 
            { y: 20, opacity: 0, scale: 0.9 }, 
            { y: 0, opacity: 1, scale: 1, duration: 0.45, ease: "back.out(1.6)" }, 
            ${(actionTime + 0.2).toFixed(3)}
          );
          `;
          break;

        case "activate-entry-hop":
          script += `
          // Action: activate-entry-hop on #${act.target}
          tl.fromTo("#scene-${idx} #query-descent-probe", 
            { y: -35, opacity: 0, scale: 0.5 }, 
            { y: 0, opacity: 1, scale: 1, duration: 0.45, ease: "back.out(2)" }, 
            ${actionTime.toFixed(3)}
          );
          tl.to("#scene-${idx} #${act.target}", { 
            borderColor: "#a3e635", 
            boxShadow: "0 0 20px rgba(163, 230, 53, 0.8)", 
            scale: 1.1, 
            duration: 0.35 
          }, ${(actionTime + 0.15).toFixed(3)});
          `;
          break;

        case "descend-to-base":
          script += `
          // Action: descend-to-base on #${act.target}
          tl.to("#scene-${idx} #${act.target}", { 
            y: 155, 
            duration: ${(actionDur * 0.48).toFixed(2)}, 
            ease: "power2.inOut" 
          }, ${actionTime.toFixed(3)});
          tl.to("#scene-${idx} #intermediate-node-l1", { 
            borderColor: "#c084fc", 
            boxShadow: "0 0 16px rgba(192, 132, 252, 0.8)", 
            scale: 1.08, 
            duration: 0.3 
          }, ${(actionTime + actionDur * 0.4).toFixed(3)});
          tl.to("#scene-${idx} #${act.target}", { 
            y: 310, 
            duration: ${(actionDur * 0.48).toFixed(2)}, 
            ease: "power2.inOut" 
          }, ${(actionTime + actionDur * 0.52).toFixed(3)});
          `;
          break;

        case "lock-target-nearest-vector":
          script += `
          // Action: lock-target-nearest-vector on #${act.target}
          tl.to("#scene-${idx} #${act.target}", { 
            scale: 1.25, 
            color: "#a3e635", 
            borderColor: "#a3e635", 
            boxShadow: "0 0 35px rgba(163, 230, 53, 0.95)", 
            duration: 0.5, 
            ease: "back.out(2.2)" 
          }, ${actionTime.toFixed(3)});
          tl.fromTo("#scene-${idx} #convergence-ring", 
            { scale: 0.6, opacity: 1 }, 
            { scale: 2.6, opacity: 0, duration: 0.75, ease: "power2.out" }, 
            ${(actionTime + 0.1).toFixed(3)}
          );
          tl.to("#scene-${idx} .dim-dot", { 
            opacity: 0.2, 
            scale: 0.7, 
            duration: 0.4 
          }, ${(actionTime + 0.2).toFixed(3)});
          `;
          break;

        case "stamp-rule-entrance":
          script += `
          // Action: stamp-rule-entrance on #${act.target}
          tl.fromTo("#scene-${idx} #${act.target}", 
            { y: 50, opacity: 0, scale: 0.92 }, 
            { y: 0, opacity: 1, scale: 1, duration: 0.55, ease: "back.out(1.8)" }, 
            ${actionTime.toFixed(3)}
          );
          tl.fromTo("#scene-${idx} .takeaway-stamp", 
            { scale: 1.5, opacity: 0 }, 
            { scale: 1, opacity: 1, duration: 0.4, ease: "bounce.out" }, 
            ${(actionTime + 0.2).toFixed(3)}
          );
          `;
          break;

        case "lock-latency-meter":
          script += `
          // Action: lock-latency-meter on #${act.target}
          tl.fromTo("#scene-${idx} #param-metrics .metric-card", 
            { x: -20, opacity: 0 }, 
            { x: 0, opacity: 1, duration: 0.4, stagger: 0.12, ease: "power2.out" }, 
            ${actionTime.toFixed(3)}
          );
          tl.fromTo("#scene-${idx} #${act.target}", 
            { scale: 0.88, opacity: 0 }, 
            { scale: 1, opacity: 1, duration: 0.45, ease: "back.out(1.6)" }, 
            ${(actionTime + 0.2).toFixed(3)}
          );
          tl.to("#scene-${idx} #gauge-val", { 
            color: "#a3e635", 
            textShadow: "0 0 24px rgba(163, 230, 53, 0.95)", 
            scale: 1.15, 
            duration: 0.35, 
            yoyo: true, 
            repeat: 1 
          }, ${(actionTime + 0.45).toFixed(3)});
          `;
          break;

        case "pin-cache-ram":
          script += `
          // Action: pin-cache-ram on #${act.target}
          tl.fromTo("#scene-${idx} #${act.target}", 
            { scale: 0.9, opacity: 0, x: -30 }, 
            { scale: 1, opacity: 1, x: 0, duration: 0.5, ease: "power2.out" }, 
            ${actionTime.toFixed(3)}
          );
          tl.to("#scene-${idx} #${act.target}", { 
            borderColor: "#c084fc", 
            boxShadow: "0 0 20px rgba(192, 132, 252, 0.6)", 
            duration: 0.3 
          }, ${(actionTime + 0.4).toFixed(3)});
          `;
          break;

        case "instant-query-hit":
          script += `
          // Action: instant-query-hit on #${act.target}
          tl.fromTo("#scene-${idx} #${act.target}", 
            { y: 30, opacity: 0 }, 
            { y: 0, opacity: 1, duration: 0.5, ease: "back.out(1.6)" }, 
            ${actionTime.toFixed(3)}
          );
          tl.to("#scene-${idx} #${act.target}", { 
            borderColor: "#a3e635", 
            boxShadow: "0 0 24px rgba(163, 230, 53, 0.8)", 
            scale: 1.05, 
            duration: 0.3, 
            yoyo: true, 
            repeat: 1 
          }, ${(actionTime + 0.35).toFixed(3)});
          `;
          break;

        case "advance-flow-packet":
          script += `
          // Action: advance-flow-packet on #${act.target}
          tl.fromTo("#scene-${idx} .purple-flow-node", 
            { scale: 0.92, opacity: 0.4 }, 
            { scale: 1.05, opacity: 1, duration: 0.4, stagger: 0.25, ease: "back.out(1.4)" }, 
            ${actionTime.toFixed(3)}
          );
          `;
          break;

        case "animate-subscribe-conversion":
          script += `
          // Action: animate-subscribe-conversion on #${act.target}
          tl.fromTo("#scene-${idx} .outro-guide-anchor", 
            { x: 80, opacity: 0 }, 
            { x: 0, opacity: 1, duration: 0.5, ease: "back.out(1.8)" }, 
            ${startT + 0.15}
          );
          tl.to("#scene-${idx} #yt-sub-btn", { 
            scale: 0.92, 
            duration: 0.12, 
            ease: "power2.in" 
          }, ${actionTime.toFixed(3)});
          tl.to("#scene-${idx} #yt-sub-btn", { 
            scale: 1.0, 
            backgroundColor: "#160a2c", 
            borderColor: "#a3e635", 
            boxShadow: "0 0 28px rgba(163, 230, 53, 0.75)", 
            duration: 0.25, 
            ease: "back.out(2)" 
          }, ${(actionTime + 0.12).toFixed(3)});
          tl.to("#scene-${idx} #sub-btn-text", { 
            innerText: "✓ SUBSCRIBED", 
            color: "#a3e635", 
            duration: 0.2 
          }, ${(actionTime + 0.12).toFixed(3)});
          tl.to("#scene-${idx} #yt-bell-btn", { 
            rotation: 20, 
            yoyo: true, 
            repeat: 5, 
            duration: 0.08, 
            color: "#facc15", 
            borderColor: "#a3e635",
            ease: "sine.inOut" 
          }, ${(actionTime + 0.35).toFixed(3)});
          `;
          break;

        case "burst-emblem":
        default:
          script += `
          // Action: ${act.action} on #${act.target || "focal"}
          tl.fromTo("#scene-${idx} ${act.target ? "#" + act.target : ".surreal-icon"}", 
            { scale: 0.7, opacity: 0, rotation: -15 }, 
            { scale: 1, opacity: 1, rotation: 0, duration: ${actionDur.toFixed(2)}, ease: "back.out(1.8)" }, 
            ${actionTime.toFixed(3)}
          );
          `;
          break;
      }
    });

    return script;
  }

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
      let continuityScript = "";
      const prevScene = scenes[idx - 1];
      const prevContinuity = prevScene?.sceneGraph?.transition?.continuity;
      if (prevContinuity?.persistentElement && prevContinuity?.morphTarget) {
        continuityScript = `
        // Continuous Object Transformation: #${prevContinuity.persistentElement} -> #${prevContinuity.morphTarget}
        tl.to("#scene-${idx - 1} #${prevContinuity.persistentElement}", {
          scale: 0.55,
          opacity: 0.6,
          duration: 0.25,
          ease: "power2.in"
        }, ${(startT - 0.25).toFixed(3)});
        tl.fromTo("#scene-${idx} #${prevContinuity.morphTarget}", 
          { scale: 0.6, opacity: 0.7 },
          { scale: 1.0, opacity: 1, duration: 0.42, ease: "back.out(2)" },
          ${startT.toFixed(3)}
        );`;
      }

      gsapTimelineScript += `
        // Transition Scene ${idx - 1} -> Scene ${idx}
        tl.to("#scene-${idx - 1}", { opacity: 0, scale: 0.96, y: -25, duration: 0.3, ease: "power2.in" }, ${startT - 0.2});
        tl.fromTo("#scene-${idx}", 
          { opacity: 0, scale: 1.04, y: 30 },
          { opacity: 1, scale: 1, y: 0, duration: 0.45, ease: "power3.out" },
          ${startT}
        );
        ${continuityScript}

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

    // Execute Element-Level Motion Choreography
    gsapTimelineScript += buildMotionChoreographyScript(scene, idx);

    // Full-Story Character Choreography for Scene idx
    if (scene.characterCue && scene.characterCue.visible && scene.cardType !== "subscribe-outro") {
      const cue = scene.characterCue;
      const charSelector = `#scene-${idx} #guide-scene-${idx}`;
      const isLeft = cue.position?.includes("left");
      const scaleXVal = isLeft ? -0.82 : 0.82;
      const initialScaleX = isLeft ? -0.72 : 0.72;
      gsapTimelineScript += `
        // Character Choreography for Scene ${idx} (${cue.role || "guide"})
        tl.fromTo("${charSelector}",
          { y: 35, opacity: 0, scaleX: ${initialScaleX}, scaleY: 0.72 },
          { y: 0, opacity: 1, scaleX: ${scaleXVal}, scaleY: 0.82, duration: 0.55, ease: "back.out(1.6)" },
          ${(startT + 0.12).toFixed(3)}
        );
      `;

      if (cue.pose === "react") {
        gsapTimelineScript += `
          tl.to("${charSelector} [id$='gesture-arm']", {
            rotation: -115,
            duration: 0.35,
            yoyo: true,
            repeat: 1,
            ease: "back.out(2)"
          }, ${(startT + duration * 0.4).toFixed(3)});
        `;
      } else if (cue.pose === "track") {
        gsapTimelineScript += `
          tl.to("${charSelector} [id$='head']", {
            rotation: 20,
            duration: 1.0,
            ease: "sine.inOut"
          }, ${(startT + 0.35).toFixed(3)});
        `;
      } else if (cue.pose === "contemplate") {
        gsapTimelineScript += `
          tl.to("${charSelector} [id$='head']", {
            rotation: 14,
            duration: 0.8,
            ease: "sine.inOut"
          }, ${(startT + 0.25).toFixed(3)});
        `;
      }

      gsapTimelineScript += `
        tl.to("${charSelector}", {
          opacity: 0,
          y: 20,
          duration: 0.25,
          ease: "power2.in"
        }, ${(startT + duration - 0.25).toFixed(3)});
        tl.set("${charSelector}", { opacity: 0 }, ${(startT + duration).toFixed(3)});
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
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: flex-start;
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

      /* Linear Scan Dense Vector Field Stage (Beat 1) */
      .linear-scan-stage {
        width: 100%;
        padding: 26px;
        border-radius: 26px;
        background: rgba(20, 10, 42, 0.92);
        border: 1px solid rgba(192, 132, 252, 0.35);
        box-shadow: 0 24px 50px rgba(0, 0, 0, 0.5);
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 16px;
      }
      .dense-vector-cloud {
        width: 100%;
        display: grid;
        grid-template-columns: repeat(8, 1fr);
        gap: 14px 18px;
        padding: 24px 18px;
        background: rgba(10, 4, 22, 0.85);
        border-radius: 20px;
        border: 1px dashed rgba(192, 132, 252, 0.3);
        position: relative;
        overflow: hidden;
      }
      .vec-point {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background: rgba(192, 132, 252, 0.35);
        margin: 0 auto;
        transition: transform 0.2s, background-color 0.2s;
      }
      .linear-search-marker {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        display: flex;
        align-items: center;
        justify-content: center;
        pointer-events: none;
        z-index: 10;
      }
      .marker-pulse {
        width: 48px;
        height: 48px;
        border-radius: 50%;
        border: 2px solid #a3e635;
        box-shadow: 0 0 20px #a3e635;
        animation: pulseRing 1.5s ease-out infinite;
      }
      @keyframes pulseRing {
        0% { transform: scale(0.6); opacity: 1; }
        100% { transform: scale(1.6); opacity: 0; }
      }
      .marker-icon {
        position: absolute;
        font-size: 24px;
        filter: drop-shadow(0 0 10px rgba(163, 230, 53, 0.8));
      }
      .scan-status-panel {
        width: 100%;
        display: flex;
        flex-direction: column;
        gap: 12px;
      }
      .search-counter {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 14px 22px;
        border-radius: 14px;
        background: rgba(32, 16, 62, 0.85);
        border: 1px solid rgba(192, 132, 252, 0.3);
      }
      .counter-label {
        font-size: 18px;
        font-weight: 800;
        color: #c084fc;
        letter-spacing: 0.08em;
      }
      .counter-num {
        font-size: 22px;
        font-weight: 800;
        color: #e2e8f0;
        font-family: monospace;
      }
      .bottleneck-indicator {
        padding: 16px 20px;
        border-radius: 16px;
        background: rgba(239, 68, 68, 0.12);
        border: 1px solid rgba(239, 68, 68, 0.4);
        text-align: center;
      }
      .stall-badge {
        font-size: 20px;
        font-weight: 800;
        color: #ef4444;
        letter-spacing: 0.08em;
      }
      .stall-msg {
        font-size: 17px;
        color: #fca5a5;
        margin-top: 6px;
      }

      /* HNSW Multi-Layer Highway Stage (Beat 2) */
      .hnsw-highway-stage {
        width: 100%;
        padding: 28px;
        border-radius: 26px;
        background: rgba(22, 10, 44, 0.92);
        border: 1px solid rgba(192, 132, 252, 0.4);
        box-shadow: 0 24px 50px rgba(0, 0, 0, 0.5);
        display: flex;
        flex-direction: column;
        gap: 16px;
      }
      .highway-tier {
        padding: 16px 20px;
        border-radius: 18px;
        text-align: left;
      }
      .tier-express {
        background: rgba(163, 230, 53, 0.12);
        border: 1px solid rgba(163, 230, 53, 0.45);
        position: relative;
      }
      .tier-mid {
        background: rgba(192, 132, 252, 0.12);
        border: 1px solid rgba(192, 132, 252, 0.35);
      }
      .tier-base {
        background: rgba(147, 51, 234, 0.1);
        border: 1px dashed rgba(192, 132, 252, 0.3);
      }
      .tier-label {
        font-size: 16px;
        font-weight: 800;
        letter-spacing: 0.08em;
        color: #a3e635;
        margin-bottom: 8px;
      }
      .tier-sub {
        font-size: 16px;
        color: #cbd5e1;
        margin-top: 6px;
      }
      .highway-track {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 10px;
        position: relative;
      }
      .express-track {
        position: relative;
        padding: 6px 0;
      }
      .highway-node {
        padding: 8px 18px;
        border-radius: 12px;
        background: rgba(36, 18, 66, 0.9);
        border: 1px solid rgba(192, 132, 252, 0.5);
        font-size: 18px;
        font-weight: 700;
        color: #ffffff;
        position: relative;
        z-index: 5;
      }
      .highway-node.active-node {
        border-color: #a3e635;
        box-shadow: 0 0 14px rgba(163, 230, 53, 0.5);
      }
      .express-arc {
        position: relative;
        display: flex;
        align-items: center;
        justify-content: center;
        width: 380px;
      }
      .express-svg {
        position: absolute;
        top: -6px;
        left: 0;
        width: 100%;
        height: 36px;
        pointer-events: none;
      }
      .express-text {
        font-size: 15px;
        font-weight: 800;
        color: #a3e635;
        letter-spacing: 0.05em;
        position: relative;
        z-index: 2;
      }
      .search-probe {
        position: absolute;
        left: 20px;
        top: 8px;
        width: 22px;
        height: 22px;
        border-radius: 50%;
        background: #a3e635;
        box-shadow: 0 0 18px #a3e635;
        z-index: 10;
        display: flex;
        align-items: center;
        justify-content: center;
      }
      .probe-glow {
        position: absolute;
        inset: -6px;
        border-radius: 50%;
        background: rgba(163, 230, 53, 0.35);
        filter: blur(5px);
      }
      .skip-counter-badge {
        padding: 12px 20px;
        border-radius: 14px;
        background: rgba(163, 230, 53, 0.15);
        border: 1px solid rgba(163, 230, 53, 0.5);
        color: #a3e635;
        font-size: 19px;
        font-weight: 800;
        text-align: center;
      }
      .local-arc {
        font-size: 20px;
        color: #c084fc;
        font-weight: 800;
      }
      .base-grid {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 16px;
        padding: 8px 0;
      }
      .base-dot {
        width: 14px;
        height: 14px;
        border-radius: 50%;
        background: rgba(192, 132, 252, 0.4);
      }
      .base-dot.target-hit {
        width: auto;
        height: auto;
        background: transparent;
        font-size: 18px;
        font-weight: 800;
        color: #a3e635;
        text-shadow: 0 0 10px rgba(163, 230, 53, 0.8);
      }
      .metaphor-caption {
        text-align: left;
        margin-bottom: 0;
      }

      /* Coarse to Fine Graph Descent Stage (Beat 3) */
      .descent-navigation-stage {
        width: 100%;
        padding: 24px;
        border-radius: 26px;
        background: rgba(20, 10, 42, 0.92);
        border: 1px solid rgba(192, 132, 252, 0.35);
        box-shadow: 0 24px 50px rgba(0, 0, 0, 0.5);
        display: flex;
        flex-direction: column;
        gap: 8px;
      }
      .nav-tier {
        padding: 14px 18px;
        border-radius: 16px;
        text-align: left;
      }
      .tier-top {
        background: rgba(163, 230, 53, 0.1);
        border: 1px solid rgba(163, 230, 53, 0.4);
      }
      .tier-mid {
        background: rgba(192, 132, 252, 0.1);
        border: 1px solid rgba(192, 132, 252, 0.35);
      }
      .tier-base {
        background: rgba(147, 51, 234, 0.12);
        border: 1px dashed rgba(192, 132, 252, 0.4);
      }
      .nav-tier-header {
        font-size: 15px;
        font-weight: 800;
        color: #a3e635;
        letter-spacing: 0.08em;
        margin-bottom: 8px;
      }
      .nav-nodes-row {
        display: flex;
        align-items: center;
        justify-content: space-around;
        gap: 12px;
      }
      .graph-node {
        padding: 8px 18px;
        border-radius: 12px;
        background: rgba(36, 18, 66, 0.9);
        border: 1px solid rgba(192, 132, 252, 0.4);
        font-size: 18px;
        font-weight: 700;
        color: #ffffff;
      }
      .graph-node.entry-node {
        border-color: #a3e635;
        box-shadow: 0 0 16px rgba(163, 230, 53, 0.5);
        display: inline-flex;
        align-items: center;
        gap: 10px;
      }
      .descent-beam-container {
        height: 54px;
        display: flex;
        justify-content: center;
        position: relative;
      }
      .beam-svg {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
      }
      .query-descent-probe {
        position: absolute;
        top: 0;
        left: 50%;
        transform: translateX(-50%);
        width: 22px;
        height: 22px;
        border-radius: 50%;
        background: #a3e635;
        box-shadow: 0 0 18px #a3e635;
        z-index: 10;
      }
      .base-vector-cluster {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 14px;
        padding: 8px 0;
      }
      .target-beacon {
        position: relative;
        padding: 8px 20px;
        border-radius: 14px;
        background: rgba(36, 18, 66, 0.95);
        border: 2px solid #a3e635;
        color: #a3e635;
        font-size: 19px;
        font-weight: 800;
        box-shadow: 0 0 16px rgba(163, 230, 53, 0.6);
      }
      .convergence-ring {
        position: absolute;
        inset: -6px;
        border-radius: 16px;
        border: 2px solid #a3e635;
        pointer-events: none;
      }
      .dim-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background: rgba(192, 132, 252, 0.4);
      }

      /* Parameter Metrics & Latency Speedometer (Beat 4) */
      .param-metrics-grid {
        display: flex;
        gap: 16px;
        width: 100%;
        margin-bottom: 18px;
      }
      .metric-card {
        flex: 1;
        padding: 18px 16px;
        border-radius: 18px;
        background: rgba(32, 16, 62, 0.85);
        border: 1px solid rgba(192, 132, 252, 0.35);
        text-align: center;
      }
      .metric-key {
        font-size: 17px;
        font-weight: 800;
        color: #c084fc;
        letter-spacing: 0.06em;
        display: block;
      }
      .metric-val {
        font-size: 26px;
        font-weight: 900;
        color: #a3e635;
        margin: 4px 0;
        display: block;
      }
      .metric-desc {
        font-size: 15px;
        color: #cbd5e1;
      }
      .latency-gauge-box {
        padding: 20px;
        border-radius: 20px;
        background: rgba(16, 8, 34, 0.9);
        border: 2px solid rgba(163, 230, 53, 0.5);
        text-align: center;
        box-shadow: 0 0 24px rgba(163, 230, 53, 0.25);
        margin-bottom: 20px;
      }
      .gauge-label {
        font-size: 16px;
        font-weight: 800;
        color: #e9d5ff;
        letter-spacing: 0.1em;
      }
      .gauge-value {
        font-size: 48px;
        font-weight: 900;
        color: #a3e635;
        font-family: monospace;
        text-shadow: 0 0 20px rgba(163, 230, 53, 0.8);
        margin: 4px 0;
      }
      .gauge-sub {
        font-size: 17px;
        font-weight: 700;
        color: #cbd5e1;
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

      .benchmark-tag {
        font-size: 14px;
        color: #cbd5e1;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        display: inline-block;
        margin-right: 6px;
      }

      /* Animated Subscribe Outro Stage */
      .subscribe-outro-stage {
        width: 100%;
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        padding: 44px 32px 42px;
        border-radius: 28px;
        background: rgba(22, 10, 44, 0.95);
        border: 2px solid rgba(192, 132, 252, 0.4);
        box-shadow: 0 24px 60px rgba(0, 0, 0, 0.6);
        position: relative;
        overflow: visible;
      }
      .outro-headline {
        font-size: 52px;
        font-weight: 900;
        line-height: 1.2;
        color: #ffffff;
        margin-bottom: 16px;
        max-width: 820px;
      }
      .outro-subline {
        font-size: 26px;
        color: #cbd5e1;
        margin-bottom: 36px;
        max-width: 720px;
      }
      .cta-interaction-container {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 20px;
        margin-top: 10px;
        z-index: 10;
      }
      .outro-guide-anchor {
        position: absolute;
        bottom: -25px;
        right: 15px;
        z-index: 20;
        pointer-events: none;
      }
      .outro-guide-anchor .lab-guide-figure {
        position: static;
        filter: drop-shadow(0 14px 28px rgba(0, 0, 0, 0.8));
      }
      .yt-subscribe-btn {
        display: inline-flex;
        align-items: center;
        gap: 14px;
        padding: 20px 42px;
        border-radius: 9999px;
        background: #e11d48;
        border: 2px solid #fb7185;
        box-shadow: 0 8px 30px rgba(225, 29, 72, 0.5);
        cursor: pointer;
        transition: transform 0.15s ease;
      }
      .sub-play-icon {
        font-size: 24px;
        color: #ffffff;
      }
      .sub-btn-text {
        font-size: 26px;
        font-weight: 900;
        letter-spacing: 0.08em;
        color: #ffffff;
      }
      .yt-bell-btn {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 72px;
        height: 72px;
        border-radius: 50%;
        background: rgba(30, 16, 56, 0.95);
        border: 2px solid rgba(192, 132, 252, 0.5);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
      }
      .bell-icon {
        font-size: 30px;
        color: #cbd5e1;
      }

      /* Lab Guide SVG Styles */
      ${getLabGuideCss()}

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
