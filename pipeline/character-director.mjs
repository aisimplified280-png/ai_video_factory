// pipeline/character-director.mjs - AI Simplified Lab Faceless Audience Guide ("The Curator")
// Lightweight, vector-based audience guide character with purposeful gestures and poses.

export const GUIDE_POSES = {
  DIRECT: "direct",             // Points arm toward the key concept or diagram
  TRACK: "track",               // Turns visor & head following a moving probe or metric
  REACT: "react",               // Celebrates / pauses in breakthrough posture at payoff
  CONNECT: "connect",           // Gestures between two objects (cause and effect / comparison)
  CONTEMPLATE: "contemplate",   // Hand near helmet/visor analyzing an architectural dilemma
  PRESENT: "present",           // Open presentation gesture displaying the takeaway
  OUTRO_CTA: "outro-cta",       // Gestures warmly toward the animated subscribe button
};

/**
 * Generate inline SVG for the faceless Lab Guide in the specified pose.
 */
export function renderLabGuideSvg(pose = "direct", id = "lab-guide", options = {}) {
  const normPose = String(pose || "direct").toLowerCase().trim();
  const positionClass = options.position ? `guide-pos-${options.position}` : "";
  const scaleClass = options.scale === "compact" || options.scale < 0.9 ? "guide-scale-compact" : "guide-scale-normal";

  // Poses adjust the right arm, head angle, and visor flare
  let armTransform = "rotate(-25 100 135)";
  let leftArmTransform = "rotate(0 68 140)";
  let headTransform = "rotate(0 100 65)";
  let visorWidth = 32;

  if (normPose === GUIDE_POSES.DIRECT || normPose === "pointing") {
    armTransform = "rotate(-55 100 135)";
    headTransform = "rotate(-6 100 65)";
    visorWidth = 38;
  } else if (normPose === GUIDE_POSES.TRACK) {
    armTransform = "rotate(-30 100 135)";
    headTransform = "rotate(16 100 65)";
    visorWidth = 36;
  } else if (normPose === GUIDE_POSES.REACT || normPose === "celebrating") {
    armTransform = "rotate(-105 100 135)";
    leftArmTransform = "rotate(35 68 140)";
    headTransform = "rotate(-14 100 65)";
    visorWidth = 44;
  } else if (normPose === GUIDE_POSES.CONNECT) {
    armTransform = "rotate(-20 100 135)";
    leftArmTransform = "rotate(-20 68 140)";
    headTransform = "rotate(0 100 65)";
    visorWidth = 34;
  } else if (normPose === GUIDE_POSES.CONTEMPLATE) {
    armTransform = "rotate(-92 100 135)";
    headTransform = "rotate(10 100 65)";
    visorWidth = 28;
  } else if (normPose === GUIDE_POSES.PRESENT) {
    armTransform = "rotate(-45 100 135)";
    leftArmTransform = "rotate(25 68 140)";
    headTransform = "rotate(0 100 65)";
    visorWidth = 38;
  } else if (normPose === GUIDE_POSES.OUTRO_CTA || normPose === "outro-cta") {
    armTransform = "rotate(-65 100 135)";
    headTransform = "rotate(-8 100 65)";
    visorWidth = 40;
  }

  return `
  <div id="${id}" class="lab-guide-character lab-guide-figure pose-${normPose} ${positionClass} ${scaleClass}">
    <svg viewBox="0 0 200 280" width="160" height="224" class="guide-svg" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <radialGradient id="visor-glow-${id}" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stop-color="#a3e635" stop-opacity="0.9" />
          <stop offset="100%" stop-color="#a3e635" stop-opacity="0" />
        </radialGradient>
        <linearGradient id="coat-grad-${id}" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#2a144e" />
          <stop offset="100%" stop-color="#120726" />
        </linearGradient>
      </defs>

      <!-- Atmospheric Guide Shadow -->
      <ellipse cx="100" cy="265" rx="55" ry="10" fill="rgba(0,0,0,0.45)" />

      <!-- Body / Minimalist Lab Coat -->
      <path d="M 65 140 Q 50 200 45 255 L 155 255 Q 150 200 135 140 Z" fill="url(#coat-grad-${id})" stroke="#c084fc" stroke-width="2.5" />
      <!-- Coat Center Lapel Accent -->
      <line x1="100" y1="140" x2="100" y2="255" stroke="#a3e635" stroke-width="1.8" stroke-dasharray="6,4" />

      <!-- Left Arm (Resting or Gesturing) -->
      <g transform="${leftArmTransform}">
        <path d="M 68 140 Q 52 185 58 220" fill="none" stroke="#c084fc" stroke-width="10" stroke-linecap="round" />
        <circle cx="58" cy="220" r="7" fill="#ffffff" stroke="#c084fc" stroke-width="2" />
      </g>

      <!-- Right Arm (Gesturing with Transform) -->
      <g transform="${armTransform}" id="${id}-gesture-arm">
        <path d="M 132 140 Q 155 170 175 145" fill="none" stroke="#a3e635" stroke-width="10" stroke-linecap="round" />
        <circle cx="178" cy="143" r="8" fill="#ffffff" stroke="#a3e635" stroke-width="2.5" />
      </g>

      <!-- Head / Geometric Visor (Faceless Design) -->
      <g transform="${headTransform}" id="${id}-head">
        <!-- Helmet Silhouette -->
        <circle cx="100" cy="75" r="42" fill="#1b0b33" stroke="#c084fc" stroke-width="3" />
        <!-- Neon Visor Halo -->
        <ellipse cx="100" cy="74" rx="46" ry="16" fill="url(#visor-glow-${id})" />
        <!-- Neon Visor Lens -->
        <rect x="${100 - visorWidth / 2}" y="67" width="${visorWidth}" height="14" rx="7" fill="#a3e635" stroke="#ffffff" stroke-width="1.5" />
      </g>
    </svg>
  </div>
  `;
}

/**
 * Plan purposeful scene-by-scene character choreography.
 * Ensures the character actively presents, tracks, and reacts while respecting safe zones
 * and stepping offstage during dense technical diagrams.
 */
export function planSceneCharacterAction(scene, visualMode, idx, totalScenes) {
  // 1. Subscribe Outro: Guides attention warmly toward subscribe & notification bell
  if (visualMode === "subscribe-outro" || idx === totalScenes - 1) {
    return {
      visible: true,
      role: "community-guide",
      pose: "outro-cta",
      position: "bottom-right",
      scale: "compact",
      action: "guide-subscribe-cta",
      purpose: "Guide viewer attention warmly toward channel subscribe button and notification bell",
    };
  }

  // 2. Hook / Problem Statement (Scene 0): Enters at bottom-left to frame the dilemma
  if (idx === 0 || visualMode === "hook" || visualMode === "hook-bold-object") {
    return {
      visible: true,
      role: "problem-presenter",
      pose: "contemplate",
      position: "bottom-left",
      scale: "compact",
      action: "enter-and-contemplate",
      purpose: "Enters to introduce the dilemma thoughtfully without blocking the central bottleneck title",
    };
  }

  // 3. Metaphor / Dynamic Motion (Scene 1): Positioned at bottom-right tracking movement
  if (visualMode === "physical-metaphor" || idx === 1) {
    return {
      visible: true,
      role: "motion-tracker",
      pose: "track",
      position: "bottom-right",
      scale: "compact",
      action: "track-probe-movement",
      purpose: "Turns glowing visor following moving elements across layers",
    };
  }

  // 4. Dense Technical Topology / Code: Steps offstage to give 100% focus to technical graphics
  if (visualMode === "code" || scene.diagramType === "hnsw-graph" || scene.cardType === "architecture-diagram") {
    return {
      visible: false,
      role: "diagram-focus",
      pose: "standby",
      position: "offstage",
      scale: "compact",
      action: "step-offstage",
      purpose: "Steps offstage cleanly to maximize visual space and legibility for dense technical topology",
    };
  }

  // 5. Payoff / Breakthrough Takeaway: Celebrates breakthrough alongside primary rule
  return {
    visible: true,
    role: "breakthrough-celebrator",
    pose: "react",
    position: "bottom-left",
    scale: "compact",
    action: "celebrate-breakthrough",
    purpose: "Celebrates breakthrough performance alongside the production rule takeaway",
  };
}

/**
 * Generate CSS rules for the Lab Guide.
 */
export function getLabGuideCss() {
  return `
    /* Lab Guide Audience Guide Figure */
    .lab-guide-character,
    .lab-guide-figure {
      position: absolute;
      z-index: 35;
      pointer-events: none;
      filter: drop-shadow(0 18px 30px rgba(0, 0, 0, 0.75));
      transition: transform 0.3s ease;
    }
    .lab-guide-character.guide-pos-bottom-left,
    .lab-guide-character.guide-side-left,
    .lab-guide-figure.side-left {
      bottom: 24px;
      left: 20px;
      right: auto;
      transform-origin: bottom center;
      transform: scaleX(-1) scale(0.82);
    }
    .lab-guide-character.guide-pos-bottom-right,
    .lab-guide-character.guide-side-right,
    .lab-guide-figure.side-bottom {
      bottom: 24px;
      right: 20px;
      left: auto;
      transform-origin: bottom center;
      transform: scale(0.82);
    }
    .lab-guide-character.guide-pos-mid-left {
      top: 420px;
      left: 10px;
      right: auto;
      transform-origin: center center;
      transform: scaleX(-1) scale(0.82);
    }
    .lab-guide-character.guide-pos-mid-right {
      top: 420px;
      right: 10px;
      left: auto;
      transform-origin: center center;
      transform: scale(0.82);
    }
    .lab-guide-character.guide-scale-compact {
      transform-origin: bottom center;
    }
    .lab-guide-character.guide-scale-normal {
      transform-origin: bottom center;
    }
  `;
}
