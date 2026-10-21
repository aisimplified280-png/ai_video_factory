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
 * Generate inline SVG for the Hipster Tech Architect Lab Guide matching the user reference.
 * Character Archetype: Modern tech specialist wearing stylish streetwear techwear, fedora/hat,
 * thick-rimmed AR glasses with glowing HUD reflections, geometric head, and classic sneakers.
 */
export function renderLabGuideSvg(pose = "direct", id = "lab-guide", options = {}) {
  const normPose = String(pose || "direct").toLowerCase().trim();
  const positionClass = options.position ? `guide-pos-${options.position}` : "";
  const scaleClass = options.scale === "compact" || options.scale < 0.9 ? "guide-scale-compact" : "guide-scale-normal";

  // Arm and head articulation transforms
  let armTransform = "rotate(-25 140 130)";
  let leftArmTransform = "rotate(0 60 130)";
  let headTransform = "rotate(0 100 65)";

  if (normPose === GUIDE_POSES.DIRECT || normPose === "pointing") {
    armTransform = "rotate(-55 140 130)";
    headTransform = "rotate(-6 100 65)";
  } else if (normPose === GUIDE_POSES.TRACK) {
    armTransform = "rotate(-30 140 130)";
    headTransform = "rotate(16 100 65)";
  } else if (normPose === GUIDE_POSES.REACT || normPose === "celebrating") {
    armTransform = "rotate(-105 140 130)";
    leftArmTransform = "rotate(35 60 130)";
    headTransform = "rotate(-14 100 65)";
  } else if (normPose === GUIDE_POSES.CONNECT) {
    armTransform = "rotate(-20 140 130)";
    leftArmTransform = "rotate(-20 60 130)";
    headTransform = "rotate(0 100 65)";
  } else if (normPose === GUIDE_POSES.CONTEMPLATE) {
    armTransform = "rotate(-88 140 130)";
    headTransform = "rotate(10 100 65)";
  } else if (normPose === GUIDE_POSES.PRESENT) {
    armTransform = "rotate(-45 140 130)";
    leftArmTransform = "rotate(25 60 130)";
    headTransform = "rotate(0 100 65)";
  } else if (normPose === GUIDE_POSES.OUTRO_CTA || normPose === "outro-cta") {
    armTransform = "rotate(-65 140 130)";
    headTransform = "rotate(-8 100 65)";
  }

  const isLeft = options.position?.includes("left");
  const innerFlip = isLeft ? `transform="translate(200, 0) scale(-1, 1)"` : "";

  return `
  <div id="${id}" class="lab-guide-character lab-guide-figure pose-${normPose} ${positionClass} ${scaleClass}">
    <svg viewBox="0 0 200 300" width="160" height="240" class="guide-svg" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <!-- AR HUD Glasses Glow -->
        <radialGradient id="visor-glow-${id}" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stop-color="#a3e635" stop-opacity="0.9" />
          <stop offset="60%" stop-color="#22c55e" stop-opacity="0.4" />
          <stop offset="100%" stop-color="#a3e635" stop-opacity="0" />
        </radialGradient>
        <!-- Dark Techwear Gradient -->
        <linearGradient id="techwear-grad-${id}" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#251445" />
          <stop offset="100%" stop-color="#120624" />
        </linearGradient>
      </defs>

      <g ${innerFlip}>
        <!-- Atmospheric Ground Shadow -->
        <ellipse cx="100" cy="292" rx="55" ry="7" fill="rgba(0,0,0,0.55)" />

        <!-- Mint / Electric Lime Low-Top Sneakers -->
        <!-- Left Sneaker -->
        <path d="M 60 274 L 84 274 L 88 285 L 54 285 Z" fill="#a3e635" stroke="#120624" stroke-width="1.8" />
        <rect x="52" y="284" width="38" height="6" rx="2" fill="#ffffff" stroke="#120624" stroke-width="1.5" />
        <path d="M 52 284 Q 58 279 66 279" stroke="#ffffff" stroke-width="2" fill="none" />
        <!-- Right Sneaker -->
        <path d="M 116 274 L 140 274 L 146 285 L 112 285 Z" fill="#a3e635" stroke="#120624" stroke-width="1.8" />
        <rect x="110" y="284" width="38" height="6" rx="2" fill="#ffffff" stroke="#120624" stroke-width="1.5" />
        <path d="M 148 284 Q 142 279 134 279" stroke="#ffffff" stroke-width="2" fill="none" />

        <!-- Tapered Camel / Tech Trousers -->
        <!-- Left Leg -->
        <polygon points="70,186 64,274 84,274 94,186" fill="#b08354" stroke="#4a3016" stroke-width="2" />
        <!-- Right Leg -->
        <polygon points="106,186 116,274 136,274 130,186" fill="#b08354" stroke="#4a3016" stroke-width="2" />
        <!-- Seam -->
        <line x1="100" y1="186" x2="100" y2="216" stroke="#4a3016" stroke-width="2" />

        <!-- Belt & Electric Lime Buckle -->
        <rect x="66" y="178" width="68" height="10" rx="1" fill="#24133b" stroke="#120624" stroke-width="1.5" />
        <rect x="94" y="177" width="12" height="12" rx="2" fill="#a3e635" stroke="#ffffff" stroke-width="1.2" />

        <!-- Dark Techwear Hoodie / Jacket -->
        <path d="M 64 126 L 50 180 L 150 180 L 136 126 Z" fill="url(#techwear-grad-${id})" stroke="#3b1d6b" stroke-width="2.5" />
        <!-- White V-neck Inner Tee -->
        <polygon points="85,126 100,148 115,126" fill="#f8fafc" stroke="#3b1d6b" stroke-width="1.5" />
        <!-- Neon Lime Drawstrings -->
        <path d="M 88 138 Q 85 158 88 170" stroke="#a3e635" stroke-width="2.2" stroke-linecap="round" fill="none" />
        <circle cx="88" cy="172" r="2.2" fill="#a3e635" />
        <path d="M 112 138 Q 115 158 112 170" stroke="#a3e635" stroke-width="2.2" stroke-linecap="round" fill="none" />
        <circle cx="112" cy="172" r="2.2" fill="#a3e635" />

        <!-- Left Arm (Casual / Stance) -->
        <g transform="${leftArmTransform}">
          <path d="M 58 130 L 44 172 L 54 180" fill="none" stroke="#251445" stroke-width="14" stroke-linecap="round" stroke-linejoin="round" />
          <circle cx="54" cy="180" r="7" fill="#f5d6b8" stroke="#3b1d6b" stroke-width="1.8" />
        </g>

        <!-- Right Arm (Gesturing & Articulated) -->
        <g transform="${armTransform}" id="${id}-gesture-arm">
          <path d="M 142 130 L 160 160 L 176 142" fill="none" stroke="#a3e635" stroke-width="12" stroke-linecap="round" stroke-linejoin="round" />
          <circle cx="178" cy="140" r="8" fill="#f5d6b8" stroke="#120624" stroke-width="2" />
        </g>

        <!-- Articulated Head & Hipster Face -->
        <g transform="${headTransform}" id="${id}-head">
          <!-- Ears -->
          <rect x="62" y="74" width="8" height="16" rx="4" fill="#f5d6b8" stroke="#3b1d6b" stroke-width="1.8" />
          <rect x="130" y="74" width="8" height="16" rx="4" fill="#f5d6b8" stroke="#3b1d6b" stroke-width="1.8" />

          <!-- Blocky Rectangular Face -->
          <rect x="68" y="56" width="64" height="70" rx="10" fill="#f5d6b8" stroke="#3b1d6b" stroke-width="2" />

          <!-- Brown Angular Hair Bangs -->
          <polygon points="68,56 74,78 86,72 96,82 104,70 120,80 132,56" fill="#6c3b1e" />

          <!-- Dark Fedora / Trilby Hat with Neon Band -->
          <!-- Hat Crown -->
          <path d="M 66 56 C 66 22 78 14 100 14 C 122 14 134 22 134 56 Z" fill="#150a26" stroke="#3b1d6b" stroke-width="2" />
          <!-- Neon Lime Accent Hatband -->
          <rect x="66" y="48" width="68" height="8" fill="#a3e635" />
          <!-- Hat Brim -->
          <ellipse cx="100" cy="56" rx="50" ry="9" fill="#150a26" stroke="#3b1d6b" stroke-width="2" />

          <!-- Eyes -->
          <circle cx="82" cy="78" r="3.2" fill="#150a26" />
          <circle cx="118" cy="78" r="3.2" fill="#150a26" />
          <!-- Subtle Cheek Freckles -->
          <circle cx="75" cy="88" r="1.2" fill="#c49575" />
          <circle cx="79" cy="91" r="1.2" fill="#c49575" />
          <circle cx="121" cy="91" r="1.2" fill="#c49575" />
          <circle cx="125" cy="88" r="1.2" fill="#c49575" />

          <!-- Signature Vertical Pill Nose from Reference -->
          <path d="M 94 74 L 93 102 Q 100 108 107 102 L 106 74 Z" fill="#d47963" stroke="#9e4b36" stroke-width="1.5" />

          <!-- Thick-Rimmed Hipster AR Glasses -->
          <!-- Frames -->
          <rect x="70" y="70" width="26" height="18" rx="4" fill="none" stroke="#120624" stroke-width="3" />
          <line x1="96" y1="78" x2="104" y2="78" stroke="#120624" stroke-width="3" />
          <rect x="104" y="70" width="26" height="18" rx="4" fill="none" stroke="#120624" stroke-width="3" />
          <!-- AR HUD Visor Glow Lenses -->
          <rect x="72" y="72" width="22" height="14" rx="2" fill="url(#visor-glow-${id})" opacity="0.75" />
          <rect x="106" y="72" width="22" height="14" rx="2" fill="url(#visor-glow-${id})" opacity="0.75" />
          <!-- Glowing Data Scan Lines -->
          <line x1="74" y1="78" x2="92" y2="78" stroke="#a3e635" stroke-width="1" stroke-dasharray="3,2" />
          <line x1="108" y1="78" x2="126" y2="78" stroke="#a3e635" stroke-width="1" stroke-dasharray="3,2" />

          <!-- Stylized Open Smile (Teeth showing) -->
          <rect x="80" y="110" width="40" height="12" rx="6" fill="#7a2a22" stroke="#4a1510" stroke-width="1.5" />
          <rect x="86" y="112" width="28" height="4" rx="1.5" fill="#ffffff" />
        </g>
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
      bottom: 60px;
      left: 30px;
      right: auto;
      transform-origin: bottom center;
      transform: scale(0.82);
    }
    .lab-guide-character.guide-pos-bottom-right,
    .lab-guide-character.guide-side-right,
    .lab-guide-figure.side-bottom {
      bottom: 60px;
      right: 30px;
      left: auto;
      transform-origin: bottom center;
      transform: scale(0.82);
    }
    .lab-guide-character.guide-pos-mid-left {
      top: 420px;
      left: 10px;
      right: auto;
      transform-origin: center center;
      transform: scale(0.82);
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
