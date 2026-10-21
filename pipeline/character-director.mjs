// pipeline/character-director.mjs - AI Simplified Lab Faceless Audience Guide ("The Curator")
// Lightweight, vector-based audience guide character with purposeful gestures and poses.

export const GUIDE_POSES = {
  DIRECT: "direct",       // Points arm toward the key concept or diagram
  TRACK: "track",         // Turns visor & head following a moving probe or metric
  REACT: "react",         // Celebrates / pauses in breakthrough posture at payoff
  CONNECT: "connect",     // Gestures between two objects (cause and effect / comparison)
  OUTRO_CTA: "outro-cta", // Gestures warmly toward the animated subscribe button
};

/**
 * Generate inline SVG for the faceless Lab Guide in the specified pose.
 */
export function renderLabGuideSvg(pose = "direct", id = "lab-guide") {
  const normPose = String(pose || "direct").toLowerCase().trim();
  // Poses adjust the right arm, head angle, and visor flare
  let armTransform = "rotate(-25 100 135)";
  let headTransform = "rotate(0 100 65)";
  let visorWidth = 32;

  if (normPose === GUIDE_POSES.DIRECT || normPose === "pointing") {
    armTransform = "rotate(-55 100 135)";
    headTransform = "rotate(-6 100 65)";
    visorWidth = 38;
  } else if (normPose === GUIDE_POSES.TRACK) {
    armTransform = "rotate(-30 100 135)";
    headTransform = "rotate(10 100 65)";
    visorWidth = 34;
  } else if (normPose === GUIDE_POSES.REACT || normPose === "celebrating") {
    armTransform = "rotate(-85 100 135)";
    headTransform = "rotate(-12 100 65)";
    visorWidth = 42;
  } else if (normPose === GUIDE_POSES.CONNECT) {
    armTransform = "rotate(-15 100 135)";
    headTransform = "rotate(0 100 65)";
    visorWidth = 32;
  } else if (normPose === GUIDE_POSES.OUTRO_CTA || normPose === "outro-cta") {
    armTransform = "rotate(-65 100 135)";
    headTransform = "rotate(-8 100 65)";
    visorWidth = 40;
  }

  return `
  <div id="${id}" class="lab-guide-character lab-guide-figure pose-${normPose}">
    <svg viewBox="0 0 200 280" width="160" height="224" class="guide-svg" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <radialGradient id="visor-glow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stop-color="#a3e635" stop-opacity="0.9" />
          <stop offset="100%" stop-color="#a3e635" stop-opacity="0" />
        </radialGradient>
        <linearGradient id="coat-grad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#2a144e" />
          <stop offset="100%" stop-color="#120726" />
        </linearGradient>
      </defs>

      <!-- Atmospheric Guide Shadow -->
      <ellipse cx="100" cy="265" rx="55" ry="10" fill="rgba(0,0,0,0.45)" />

      <!-- Body / Minimalist Lab Coat -->
      <path d="M 65 140 Q 50 200 45 255 L 155 255 Q 150 200 135 140 Z" fill="url(#coat-grad)" stroke="#c084fc" stroke-width="2.5" />
      <!-- Coat Center Lapel Accent -->
      <line x1="100" y1="140" x2="100" y2="255" stroke="#a3e635" stroke-width="1.8" stroke-dasharray="6,4" />

      <!-- Left Arm (Resting) -->
      <path d="M 68 140 Q 52 185 58 220" fill="none" stroke="#c084fc" stroke-width="10" stroke-linecap="round" />

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
        <ellipse cx="100" cy="74" rx="46" ry="16" fill="url(#visor-glow)" />
        <!-- Neon Visor Lens -->
        <rect x="${100 - visorWidth / 2}" y="67" width="${visorWidth}" height="14" rx="7" fill="#a3e635" stroke="#ffffff" stroke-width="1.5" />
      </g>
    </svg>
  </div>
  `;
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
      bottom: 240px;
      right: 40px;
      z-index: 35;
      pointer-events: none;
      filter: drop-shadow(0 18px 30px rgba(0, 0, 0, 0.75));
      transition: transform 0.3s ease;
    }
    .lab-guide-character.guide-side-left,
    .lab-guide-figure.side-left {
      left: 40px;
      right: auto;
      transform: scaleX(-1);
    }
    .lab-guide-character.guide-side-right,
    .lab-guide-figure.side-bottom {
      bottom: 240px;
      right: 60px;
    }
  `;
}
