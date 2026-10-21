// pipeline/composition-generator.mjs - Claude Aesthetic & Motion Graphics Engine
import fs from "node:fs/promises";
import path from "node:path";

/**
 * Generate full HTML5 / GSAP 9:16 composition for HyperFrames.
 * Features:
 * - Claude (Anthropic) Aesthetic: Warm ivory paper (#fbfaf7), clean white cards, signature terracotta (#d97757) accents.
 * - Kinetic Word-by-Word Active Captioning: Words light up in terracotta with micro-scale pops as spoken.
 * - Moving Laser Border: Shimmering illuminated border on hero cards.
 * - Interactive UI Artifacts: Animated circular progress rings, live typing cursor, floating tech chips.
 * - Dynamic Virtual Camera: Smooth continuous camera push-in.
 */
export async function generateComposition(compDir, projectData) {
  const { totalDuration, scenes, title, id } = projectData;

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

  // Build HTML scenes and GSAP timeline scripts
  const scenesHtml = scenes.map((scene, idx) => {
    const isFirst = idx === 0;

    let cardContent = "";
    if (scene.cardType === "hook") {
      cardContent = `
        <div class="hook-badge">
          <span class="badge-dot pulse-coral"></span>
          ${scene.badge || "CRITICAL WORKFLOW"}
        </div>
        <h1 class="hero-headline">${scene.visualTitle}</h1>
        <div class="laser-card-wrapper">
          <div class="laser-border"></div>
          <div class="feature-card">
            <div class="card-tag">${scene.tag || "INSIGHT"}</div>
            <p class="card-highlight">${scene.visualBody}</p>
            ${scene.stat ? `
              <div class="stat-badge">
                <span class="stat-number">${scene.stat}</span>
                <span class="stat-label">${scene.statLabel || ""}</span>
              </div>
            ` : ""}
          </div>
        </div>
      `;
    } else if (scene.cardType === "code" || scene.cardType === "terminal") {
      cardContent = `
        <div class="scene-badge">${scene.badge || "STEP " + idx}</div>
        <h2 class="scene-title">${scene.visualTitle}</h2>
        <div class="terminal-card">
          <div class="terminal-header">
            <div class="term-controls">
              <span class="term-dot dot-red"></span>
              <span class="term-dot dot-yellow"></span>
              <span class="term-dot dot-green"></span>
            </div>
            <span class="term-title">${scene.terminalTitle || "pipeline.config.ts"}</span>
            <span class="term-lang">TypeScript</span>
          </div>
          <div class="terminal-body">
            <pre><code>${scene.codeSnippet || scene.visualBody}</code><span class="typing-cursor">|</span></pre>
          </div>
        </div>
      `;
    } else if (scene.cardType === "comparison") {
      cardContent = `
        <div class="scene-badge">${scene.badge || "COMPARISON"}</div>
        <h2 class="scene-title">${scene.visualTitle}</h2>
        <div class="compare-grid">
          <div class="compare-box old-box">
            <div class="compare-header">
              <span class="compare-icon cross-icon">✕</span>
              <span class="compare-label">TRADITIONAL WAY</span>
            </div>
            <p class="compare-text">${scene.oldWay || "Hours of manual configuration & paid tools"}</p>
          </div>
          <div class="compare-box new-box">
            <div class="compare-header">
              <span class="compare-icon check-icon">✓</span>
              <span class="compare-label">AI SIMPLIFIED WAY</span>
            </div>
            <p class="compare-text">${scene.newWay || "100% Automated, instant & zero ongoing cost"}</p>
          </div>
        </div>
      `;
    } else {
      // Default / Payoff scene with animated SVG circular gauge
      cardContent = `
        <div class="scene-badge">${scene.badge || "VERIFIED RESULT"}</div>
        <h2 class="scene-title">${scene.visualTitle}</h2>
        <div class="feature-card payoff-card">
          <div class="payoff-flex">
            <div class="gauge-container">
              <svg class="gauge-svg" viewBox="0 0 120 120">
                <circle class="gauge-bg" cx="60" cy="60" r="48" />
                <circle id="gauge-ring-${idx}" class="gauge-bar" cx="60" cy="60" r="48" />
              </svg>
              <div class="gauge-center">
                <span class="gauge-val">100%</span>
              </div>
            </div>
            <div class="payoff-info">
              <div class="card-tag">${scene.tag || "DELIVERABLE"}</div>
              <p class="card-highlight">${scene.visualBody}</p>
              ${scene.stat ? `
                <div class="stat-badge green-badge">
                  <span class="stat-number">${scene.stat}</span>
                  <span class="stat-label">${scene.statLabel || ""}</span>
                </div>
              ` : ""}
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

  // Build Kinetic Subtitle Containers (one per scene, holding word spans)
  const subtitleScenesHtml = scenes.map((scene, idx) => {
    const words = scene.voiceText.trim().split(/\s+/);
    const wordsHtml = words.map((w, wIdx) => `<span class="cap-word" id="w-${idx}-${wIdx}">${w}</span>`).join(" ");

    return `
      <div id="sub-scene-${idx}" class="sub-scene ${idx === 0 ? 'active' : ''}">
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

  // Animate scenes and word-by-word kinetic captions
  scenes.forEach((scene, idx) => {
    const isFirst = idx === 0;
    const startT = scene.startTime;
    const endT = scene.endTime;
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

    // Gauge animation if payoff scene
    if (scene.cardType === "feature" || idx === scenes.length - 1) {
      gsapTimelineScript += `
        tl.fromTo("#gauge-ring-${idx}", 
          { strokeDashoffset: 301.6 },
          { strokeDashoffset: 0, duration: 1.4, ease: "power2.out" },
          ${startT + 0.3}
        );
      `;
    }

    // Word-by-Word Kinetic Subtitle Animation
    const words = scene.voiceText.trim().split(/\s+/);
    const wordDur = Math.max(0.18, duration / words.length);

    words.forEach((w, wIdx) => {
      const wStart = startT + (wIdx * wordDur);
      const wEnd = wStart + (wordDur * 0.9);

      gsapTimelineScript += `
        // Word: "${w}"
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
    <title>${title}</title>
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
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

      /* Top Progress Bar & Header (Claude Aesthetic) */
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

      /* Scene Stage (Inside Safe-Zone: Y 260 to 1390) */
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

      /* Claude Terracotta Badges & Editorial Headlines */
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

      /* Laser Border Shimmer Card */
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
        font-size: 38px;
        font-weight: 600;
        line-height: 1.35;
        color: #292524;
        margin-bottom: 24px;
      }
      .stat-badge {
        display: inline-flex;
        align-items: center;
        gap: 12px;
        padding: 12px 26px;
        border-radius: 16px;
        background: #fbf3ee;
        border: 1px solid #ebd5c7;
        color: #a45338;
      }
      .stat-number {
        font-size: 36px;
        font-weight: 800;
        color: #d97757;
      }
      .stat-label {
        font-size: 24px;
        font-weight: 600;
      }

      /* Claude Terminal Card */
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

      /* Claude Comparison Cards */
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

      /* Payoff Scene with Circular Gauge */
      .payoff-flex {
        display: flex;
        align-items: center;
        gap: 36px;
      }
      .gauge-container {
        position: relative;
        width: 140px;
        height: 140px;
        flex-shrink: 0;
      }
      .gauge-svg {
        width: 100%;
        height: 100%;
        transform: rotate(-90deg);
      }
      .gauge-bg {
        fill: none;
        stroke: #f3ede6;
        stroke-width: 12;
      }
      .gauge-bar {
        fill: none;
        stroke: #d97757;
        stroke-width: 12;
        stroke-linecap: round;
        stroke-dasharray: 301.6;
        stroke-dashoffset: 0;
      }
      .gauge-center {
        position: absolute;
        inset: 0;
        display: flex;
        align-items: center;
        justify-content: center;
      }
      .gauge-val {
        font-size: 28px;
        font-weight: 800;
        color: #d97757;
      }
      .green-badge {
        background: #f0fdf4;
        border-color: #bbf7d0;
        color: #166534;
      }
      .green-badge .stat-number {
        color: #16a34a;
      }

      /* Kinetic Word-by-Word Subtitle Ribbon (Safe Zone: Y 1410 - 1540) */
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
      data-composition-id="${id}"
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
