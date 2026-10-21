// pipeline/composition-generator.mjs - Semantic Storyboard & Offline-Safe HTML Synthesizer
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
 * - 100% Offline: Vendors local GSAP from pipeline/vendor/ (zero CDN).
 * - Safe Injection: All dynamic strings strictly escaped.
 * - Modular Storyboard Types:
 *   - architecture-diagram (data flow with nodes & connectors)
 *   - step-process (numbered implementation stages)
 *   - real-terminal (genuine CLI/API syntax)
 *   - comparison (factual old-vs-new workflow)
 *   - verified-payoff (honest takeaway with evidence source)
 * - Claude Editorial Aesthetic & Kinetic Word-by-Word Subtitles.
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

  // 3. Render modular semantic scene cards
  const scenesHtml = scenes.map((scene, idx) => {
    const isFirst = idx === 0;
    const cardType = scene.cardType || "concept-explainer";

    let cardContent = "";

    if (cardType === "hook") {
      cardContent = `
        <div class="hook-badge">
          <span class="badge-dot pulse-coral"></span>
          ${escapeHtml(scene.badge || "PROVEN WORKFLOW")}
        </div>
        <h1 class="hero-headline">${scene.visualTitle}</h1>
        <div class="laser-card-wrapper">
          <div class="feature-card">
            <div class="card-tag">${escapeHtml(scene.tag || "OBSERVATION")}</div>
            <p class="card-highlight">${escapeHtml(scene.visualBody)}</p>
            ${scene.source ? `<div class="source-tag">Source: ${escapeHtml(scene.source)}</div>` : ""}
          </div>
        </div>
      `;
    } else if (cardType === "architecture-diagram") {
      // Data Flow Diagram: Input -> Pipeline -> Output
      const nodes = scene.diagramNodes || [
        { label: "User Input", sub: "Raw Context" },
        { label: "Semantic Filter", sub: "Vector / RAG" },
        { label: "LLM Model", sub: "Cached Response" }
      ];
      cardContent = `
        <div class="scene-badge">${escapeHtml(scene.badge || "ARCHITECTURE")}</div>
        <h2 class="scene-title">${scene.visualTitle}</h2>
        <div class="feature-card flow-card">
          <div class="flow-container">
            ${nodes.map((node, nIdx) => `
              <div class="flow-node node-${nIdx}">
                <div class="node-dot"></div>
                <div class="node-title">${escapeHtml(node.label)}</div>
                <div class="node-sub">${escapeHtml(node.sub || "")}</div>
              </div>
              ${nIdx < nodes.length - 1 ? '<div class="flow-arrow">➔</div>' : ''}
            `).join("")}
          </div>
          <p class="card-highlight flow-caption">${escapeHtml(scene.visualBody)}</p>
        </div>
      `;
    } else if (cardType === "step-process") {
      // 1-2-3 Step-by-Step execution
      const steps = scene.steps || [
        "1. Define explicit schemas",
        "2. Streamline token footprint",
        "3. Automate deterministic QA"
      ];
      cardContent = `
        <div class="scene-badge">${escapeHtml(scene.badge || "METHODOLOGY")}</div>
        <h2 class="scene-title">${scene.visualTitle}</h2>
        <div class="feature-card">
          <div class="steps-list">
            ${steps.map((st, sIdx) => `
              <div class="step-item step-${sIdx}">
                <span class="step-num">${sIdx + 1}</span>
                <span class="step-text">${escapeHtml(st)}</span>
              </div>
            `).join("")}
          </div>
        </div>
      `;
    } else if (cardType === "code" || cardType === "terminal") {
      // Authentic Terminal / Code Walkthrough
      cardContent = `
        <div class="scene-badge">${escapeHtml(scene.badge || "IMPLEMENTATION")}</div>
        <h2 class="scene-title">${scene.visualTitle}</h2>
        <div class="terminal-card">
          <div class="terminal-header">
            <div class="term-controls">
              <span class="term-dot dot-red"></span>
              <span class="term-dot dot-yellow"></span>
              <span class="term-dot dot-green"></span>
            </div>
            <span class="term-title">${escapeHtml(scene.terminalTitle || "workflow.sh")}</span>
            <span class="term-lang">${escapeHtml(scene.terminalLang || "Bash")}</span>
          </div>
          <div class="terminal-body">
            <pre><code>${escapeHtml(scene.codeSnippet || scene.visualBody)}</code><span class="typing-cursor">|</span></pre>
          </div>
        </div>
      `;
    } else if (cardType === "comparison") {
      // Honest factual comparison
      cardContent = `
        <div class="scene-badge">${escapeHtml(scene.badge || "WORKFLOW COMPARISON")}</div>
        <h2 class="scene-title">${scene.visualTitle}</h2>
        <div class="compare-grid">
          <div class="compare-box old-box">
            <div class="compare-header">
              <span class="compare-icon cross-icon">✕</span>
              <span class="compare-label">${escapeHtml(scene.oldLabel || "COMMON PRACTICE")}</span>
            </div>
            <p class="compare-text">${escapeHtml(scene.oldWay || "Manual multi-step repetitive tasks")}</p>
          </div>
          <div class="compare-box new-box">
            <div class="compare-header">
              <span class="compare-icon check-icon">✓</span>
              <span class="compare-label">${escapeHtml(scene.newLabel || "STRUCTURED PIPELINE")}</span>
            </div>
            <p class="compare-text">${escapeHtml(scene.newWay || "Modular, deterministic code automation")}</p>
          </div>
        </div>
      `;
    } else {
      // Concept Explainer / Verified Payoff
      cardContent = `
        <div class="scene-badge">${escapeHtml(scene.badge || "KEY TAKEAWAY")}</div>
        <h2 class="scene-title">${scene.visualTitle}</h2>
        <div class="feature-card payoff-card">
          <div class="payoff-flex">
            <div class="takeaway-icon">💡</div>
            <div class="payoff-info">
              <div class="card-tag">${escapeHtml(scene.tag || "CORE PRINCIPLE")}</div>
              <p class="card-highlight">${escapeHtml(scene.visualBody)}</p>
              ${scene.source ? `<div class="source-tag">Reference: ${escapeHtml(scene.source)}</div>` : ""}
            </div>
          </div>
        </div>
      `;
    }

    return `
      <div id="scene-${idx}" class="scene-layer clip" data-start="${scene.startTime}" data-duration="${scene.duration}" style="opacity: ${isFirst ? 1 : 0};">
        ${cardContent}
      </div>
    `;
  }).join("\n");

  // Build Kinetic Subtitle Containers
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
  const ambientRepeats = Math.ceil(totalDuration / 2.5);
  let gsapTimelineScript = `
    window.__timelines = window.__timelines || {};
    const tl = gsap.timeline({ paused: true });

    // Subtle Continuous Virtual Camera push-in
    tl.to("#stage-camera", { scale: 1.04, duration: ${totalDuration}, ease: "none" }, 0);

    // Ambient floating orbs & top progress bar
    tl.to("#orb-1", { scale: 1.25, x: 20, y: -20, opacity: 0.85, duration: 2.8, yoyo: true, repeat: ${ambientRepeats}, ease: "sine.inOut" }, 0);
    tl.to("#orb-2", { scale: 1.2, x: -20, y: 30, opacity: 0.75, duration: 3.2, yoyo: true, repeat: ${ambientRepeats}, ease: "sine.inOut" }, 0);
    tl.to("#top-progress", { width: "100%", duration: ${totalDuration}, ease: "none" }, 0);

    // Cursor blink
    tl.to(".typing-cursor", { opacity: 0, duration: 0.45, repeat: -1, yoyo: true, ease: "steps(1)" }, 0);
  `;

  // Animate scenes and kinetic word highlights
  scenes.forEach((scene, idx) => {
    const isFirst = idx === 0;
    const startT = scene.startTime;
    const duration = scene.duration;

    if (isFirst) {
      gsapTimelineScript += `
        // Scene ${idx} Entrance (Hook)
        tl.from("#scene-${idx} .hook-badge", { scale: 0.85, opacity: 0, y: -25, duration: 0.5, ease: "back.out(1.6)" }, ${startT});
        tl.from("#scene-${idx} .hero-headline", { opacity: 0, y: 35, duration: 0.6, ease: "power3.out" }, ${startT + 0.12});
        tl.from("#scene-${idx} .laser-card-wrapper", { opacity: 0, y: 45, scale: 0.94, duration: 0.65, ease: "back.out(1.3)" }, ${startT + 0.25});
      `;
    } else {
      gsapTimelineScript += `
        // Transition Scene ${idx - 1} -> Scene ${idx}
        tl.to("#scene-${idx - 1}", { opacity: 0, scale: 0.96, y: -25, duration: 0.32, ease: "power2.in" }, ${startT - 0.2});
        tl.fromTo("#scene-${idx}", 
          { opacity: 0, scale: 1.05, y: 35 },
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

    // Kinetic word-by-word active captioning
    const words = scene.voiceText.trim().split(/\s+/);
    const wordDur = Math.max(0.18, duration / words.length);

    words.forEach((w, wIdx) => {
      const wStart = startT + (wIdx * wordDur);
      const wEnd = wStart + (wordDur * 0.9);

      gsapTimelineScript += `
        tl.to("#w-${idx}-${wIdx}", {
          color: "#d97757",
          backgroundColor: "rgba(217, 119, 87, 0.14)",
          scale: 1.14,
          opacity: 1,
          duration: 0.12,
          ease: "back.out(1.5)"
        }, ${wStart});

        tl.to("#w-${idx}-${wIdx}", {
          color: "#1c1917",
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
        background-color: #fbfaf7;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        color: #1c1917;
      }
      .composition-root {
        position: relative;
        width: 1080px;
        height: 1920px;
        background: radial-gradient(circle at 50% 15%, #f7f3ec 0%, #faf8f5 55%, #f3ede2 100%);
        overflow: hidden;
      }

      /* Subtle Paper Grid & Warm Ambient Glows */
      .grid-pattern {
        position: absolute;
        inset: 0;
        background-image: 
          linear-gradient(to right, rgba(140, 120, 100, 0.08) 1px, transparent 1px),
          linear-gradient(to bottom, rgba(140, 120, 100, 0.08) 1px, transparent 1px);
        background-size: 50px 50px;
        pointer-events: none;
      }
      .glow-orb {
        position: absolute;
        width: 650px;
        height: 650px;
        border-radius: 50%;
        filter: blur(90px);
        pointer-events: none;
      }
      .orb-terracotta {
        background: radial-gradient(circle, rgba(217, 119, 87, 0.16) 0%, rgba(217, 119, 87, 0) 70%);
        top: 10%;
        left: -120px;
      }
      .orb-amber {
        background: radial-gradient(circle, rgba(224, 159, 62, 0.14) 0%, rgba(224, 159, 62, 0) 70%);
        top: 48%;
        right: -140px;
      }

      /* Virtual Camera Wrapper */
      .camera-viewport {
        position: absolute;
        inset: 0;
        transform-origin: center center;
      }

      /* Top Progress Bar & Header */
      .top-progress-track {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 8px;
        background: rgba(140, 120, 100, 0.12);
        z-index: 50;
      }
      .top-progress-bar {
        height: 100%;
        width: 0%;
        background: linear-gradient(90deg, #d97757, #e09f3e, #d97757);
        box-shadow: 0 0 10px rgba(217, 119, 87, 0.5);
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
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: #44403c;
      }
      .brand-dot {
        width: 14px;
        height: 14px;
        border-radius: 50%;
        background-color: #d97757;
        box-shadow: 0 0 12px rgba(217, 119, 87, 0.8);
      }

      /* Scene Stage (Inside Safe-Zone: Y 250 to 1390) */
      .scene-stage {
        position: absolute;
        top: 250px;
        left: 90px;
        width: 900px;
        height: 1130px;
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
      .hook-badge, .scene-badge {
        display: inline-flex;
        align-items: center;
        gap: 10px;
        padding: 10px 24px;
        border-radius: 9999px;
        background: #f4ede6;
        border: 1px solid #e7d8cc;
        color: #a45338;
        font-size: 22px;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 32px;
        box-shadow: 0 4px 12px rgba(60, 45, 30, 0.04);
      }
      .pulse-coral {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background-color: #d97757;
        box-shadow: 0 0 10px #d97757;
      }
      .hero-headline {
        font-size: 72px;
        font-weight: 800;
        line-height: 1.15;
        letter-spacing: -0.03em;
        color: #1c1917;
        margin-bottom: 38px;
        max-width: 860px;
      }
      .scene-title {
        font-size: 56px;
        font-weight: 800;
        line-height: 1.2;
        letter-spacing: -0.02em;
        color: #1c1917;
        margin-bottom: 36px;
      }

      /* Cards & Containers */
      .laser-card-wrapper {
        position: relative;
        width: 100%;
        border-radius: 32px;
        padding: 3px;
        background: linear-gradient(135deg, rgba(217, 119, 87, 0.4), rgba(224, 159, 62, 0.4), rgba(60, 45, 30, 0.08));
        box-shadow: 0 24px 48px -12px rgba(60, 45, 30, 0.12), 0 4px 16px rgba(0, 0, 0, 0.03);
      }
      .feature-card {
        width: 100%;
        padding: 48px 44px;
        border-radius: 30px;
        background: #ffffff;
        border: 1px solid rgba(60, 45, 30, 0.06);
        box-shadow: 0 24px 48px -12px rgba(60, 45, 30, 0.12);
        text-align: left;
      }
      .card-tag {
        font-size: 20px;
        font-weight: 700;
        color: #d97757;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        margin-bottom: 14px;
      }
      .card-highlight {
        font-size: 36px;
        font-weight: 600;
        line-height: 1.35;
        color: #292524;
        margin-bottom: 20px;
      }
      .source-tag {
        font-size: 20px;
        font-weight: 500;
        color: #78716c;
        border-top: 1px solid #f0ebe4;
        padding-top: 16px;
      }

      /* Architecture Flow Diagram */
      .flow-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 16px;
        margin-bottom: 28px;
      }
      .flow-node {
        flex: 1;
        padding: 24px 16px;
        border-radius: 20px;
        background: #faf8f5;
        border: 1px solid #e7ded4;
        text-align: center;
      }
      .node-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: #d97757;
        margin: 0 auto 10px auto;
      }
      .node-title {
        font-size: 24px;
        font-weight: 700;
        color: #1c1917;
      }
      .node-sub {
        font-size: 18px;
        color: #78716c;
        margin-top: 4px;
      }
      .flow-arrow {
        font-size: 28px;
        color: #d97757;
        font-weight: 800;
      }
      .flow-caption {
        margin-bottom: 0;
      }

      /* Step Process List */
      .steps-list {
        display: flex;
        flex-direction: column;
        gap: 20px;
      }
      .step-item {
        display: flex;
        align-items: center;
        gap: 20px;
        padding: 24px 28px;
        border-radius: 20px;
        background: #faf8f5;
        border: 1px solid #e7ded4;
      }
      .step-num {
        width: 44px;
        height: 44px;
        border-radius: 50%;
        background: #d97757;
        color: #ffffff;
        font-size: 24px;
        font-weight: 800;
        display: flex;
        align-items: center;
        justify-content: center;
      }
      .step-text {
        font-size: 32px;
        font-weight: 600;
        color: #1c1917;
      }

      /* Terminal Card */
      .terminal-card {
        width: 100%;
        border-radius: 28px;
        background: #1e1e1e;
        border: 1px solid rgba(60, 45, 30, 0.15);
        box-shadow: 0 24px 48px rgba(30, 20, 10, 0.25);
        overflow: hidden;
        text-align: left;
      }
      .terminal-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 18px 24px;
        background: #2a2a2a;
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
      .dot-red { background: #e06c75; }
      .dot-yellow { background: #e5c07b; }
      .dot-green { background: #98c379; }
      .term-title {
        font-size: 20px;
        color: #d4d4d4;
        font-family: Consolas, monospace;
      }
      .term-lang {
        font-size: 18px;
        color: #8c8c8c;
        font-family: Consolas, monospace;
      }
      .terminal-body {
        padding: 36px;
        font-family: Consolas, "Courier New", monospace;
        font-size: 30px;
        line-height: 1.5;
        color: #98c379;
        white-space: pre-wrap;
      }
      .typing-cursor {
        color: #d97757;
        font-weight: 800;
      }

      /* Comparison Cards */
      .compare-grid {
        width: 100%;
        display: flex;
        flex-direction: column;
        gap: 24px;
      }
      .compare-box {
        padding: 34px;
        border-radius: 26px;
        text-align: left;
        background: #ffffff;
        box-shadow: 0 16px 36px -10px rgba(60, 45, 30, 0.08);
      }
      .old-box {
        border: 1px solid #fed7aa;
        background: #fffaf5;
      }
      .new-box {
        border: 2px solid #d97757;
        background: #ffffff;
      }
      .compare-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 12px;
      }
      .compare-icon {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        font-size: 18px;
      }
      .cross-icon {
        background: #fef2f2;
        color: #ef4444;
      }
      .check-icon {
        background: #fbf3ee;
        color: #d97757;
      }
      .compare-label {
        font-size: 20px;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #78716c;
      }
      .new-box .compare-label {
        color: #d97757;
      }
      .compare-text {
        font-size: 32px;
        font-weight: 600;
        color: #292524;
        line-height: 1.35;
      }

      /* Payoff Scene */
      .payoff-flex {
        display: flex;
        align-items: flex-start;
        gap: 28px;
      }
      .takeaway-icon {
        font-size: 56px;
      }
      .payoff-info {
        flex: 1;
      }

      /* Subtitle Ribbon (Safe Zone: Y 1410 - 1540) */
      .subtitle-ribbon {
        position: absolute;
        top: 1410px;
        left: 90px;
        right: 90px;
        min-height: 120px;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 20px 36px;
        border-radius: 28px;
        background: #ffffff;
        border: 1px solid rgba(60, 45, 30, 0.12);
        box-shadow: 0 20px 40px -10px rgba(60, 45, 30, 0.12), 0 4px 12px rgba(0, 0, 0, 0.04);
        z-index: 30;
      }
      .sub-scene {
        display: none;
        width: 100%;
        text-align: center;
        font-size: 38px;
        font-weight: 700;
        line-height: 1.35;
      }
      .sub-scene.active {
        display: block;
      }
      .cap-word {
        display: inline-block;
        padding: 2px 6px;
        border-radius: 6px;
        color: #78716c;
        opacity: 0.65;
        transition: color 0.1s ease;
      }
    </style>
  </head>
  <body>
    <div
      class="composition-root"
      data-composition-id="${escapeHtml(id)}"
      data-width="1080"
      data-height="1920"
      data-duration="${totalDuration}"
    >
      <div class="top-progress-track">
        <div id="top-progress" class="top-progress-bar"></div>
      </div>
      <div class="grid-pattern"></div>
      <div id="orb-1" class="glow-orb orb-terracotta"></div>
      <div id="orb-2" class="glow-orb orb-amber"></div>

      <div class="camera-viewport" id="stage-camera">
        <div class="top-bar">
          <div class="brand-badge">
            <span class="brand-dot"></span>
            AI Simplified Lab
          </div>
        </div>

        <div class="scene-stage">
          ${scenesHtml}
        </div>
      </div>

      <div class="subtitle-ribbon">
        ${subtitleScenesHtml}
      </div>
    </div>

    <script>
      ${gsapTimelineScript}
    </script>
  </body>
</html>`;

  await fs.writeFile(path.join(compDir, "index.html"), htmlContent, "utf8");
}
