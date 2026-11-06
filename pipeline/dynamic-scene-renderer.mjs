// pipeline/dynamic-scene-renderer.mjs
// Scene-specific procedural SVG renderer. No cards, slides or fixed layout presets.

const esc = (value) => String(value ?? "")
  .replace(/&/g, "&amp;")
  .replace(/</g, "&lt;")
  .replace(/>/g, "&gt;")
  .replace(/"/g, "&quot;")
  .replace(/'/g, "&#039;");

const COLOR_RE = /^#[0-9a-fA-F]{6}$/;
const ID_RE = /^[A-Za-z][A-Za-z0-9_-]{0,63}$/;
const EASES = new Set([
  "none", "linear", "power1.out", "power1.inOut", "power2.out", "power2.inOut",
  "power3.out", "power3.inOut", "back.out", "sine.inOut", "expo.out", "elastic.out"
]);
const ANIM_KEYS = ["x", "y", "scale", "rotation", "opacity"];

function color(value, fallback) {
  return COLOR_RE.test(value || "") ? value : fallback;
}
function n(value, fallback, min = -5000, max = 5000) {
  const v = Number(value);
  return Number.isFinite(v) ? Math.max(min, Math.min(max, v)) : fallback;
}
function safeId(value, fallback) {
  return ID_RE.test(value || "") ? value : fallback;
}
function safeEase(value) {
  return EASES.has(value) ? value : "power2.out";
}
function safeAssetPath(value) {
  if (typeof value !== "string" || value.includes("..") || /^https?:/i.test(value)) return null;
  return /^(\.\/)?assets\/[A-Za-z0-9._/-]+$/.test(value) ? value : null;
}
function localAnimationState(state = {}) {
  const result = {};
  for (const key of ANIM_KEYS) {
    if (Number.isFinite(state[key])) result[key] = n(state[key], key === "scale" || key === "opacity" ? 1 : 0, key === "opacity" ? 0 : -2500, key === "opacity" ? 1 : 2500);
  }
  return result;
}
function elementSvg(element, index, sceneIndex) {
  const id = safeId(element.id, `element-${index + 1}`);
  const g = element.geometry || {};
  const a = element.appearance || {};
  const primitive = a.primitive;
  const x = n(g.x, 0.5, 0, 1) * 1080;
  const y = n(g.y, 0.5, 0, 1) * 1920;
  const width = n(g.width, 0.18, 0.025, 0.95) * 1080;
  const height = n(g.height, 0.11, 0.025, 0.95) * 1920;
  const scale = n(g.scale, 1, 0.05, 5);
  const rotation = n(g.rotation, 0, -360, 360);
  const fill = color(a.color, "#7c3aed");
  const accent = color(a.accent, "#a3e635");
  const label = isRenderableLabel(a.label) ? a.label : "";
  const fontSize = Math.max(18, Math.min(38, height * 0.24));
  const gradId = `dyn-grad-${sceneIndex}-${index}`;
  const glowId = `dyn-glow-${sceneIndex}`;
  const transform = `translate(${x.toFixed(1)} ${y.toFixed(1)}) rotate(${rotation.toFixed(1)}) scale(${scale.toFixed(3)})`;
  const assetPath = safeAssetPath(a.assetPath);
  let shape = "";

  if (primitive === "orb") {
    shape = `
      <circle r="${Math.min(width, height) * 0.36}" fill="url(#${gradId})" filter="url(#${glowId})"/>
      <circle r="${Math.min(width, height) * 0.18}" fill="${accent}" opacity=".72"/>
    `;
  } else if (primitive === "ring") {
    shape = `
      <circle r="${Math.min(width, height) * 0.38}" fill="none" stroke="${fill}" stroke-width="18" opacity=".9"/>
      <circle r="${Math.min(width, height) * 0.27}" fill="none" stroke="${accent}" stroke-width="5" stroke-dasharray="22 14" filter="url(#${glowId})"/>
    `;
  } else if (primitive === "capsule" || primitive === "packet") {
    shape = `
      <rect x="${-width/2}" y="${-height/2}" width="${width}" height="${height}" rx="${Math.min(height/2, 48)}" fill="url(#${gradId})" stroke="${accent}" stroke-width="3" filter="url(#${glowId})"/>
      <rect x="${-width/2+9}" y="${-height/2+9}" width="12" height="${height-18}" rx="6" fill="${accent}" opacity=".95"/>
      <path d="M ${-width/2+36} 0 H ${width/2-28}" stroke="#ffffff" stroke-opacity=".45" stroke-width="3" stroke-linecap="round"/>
      ${label ? `<text x="0" y="${fontSize/3}" text-anchor="middle" class="dyn-label" font-size="${fontSize}">${esc(label)}</text>` : ""}
    `;
  } else if (primitive === "rail") {
    shape = `
      <rect x="${-width/2}" y="${-height/2}" width="${width}" height="${height}" rx="${Math.min(height/2, 38)}" fill="${fill}" fill-opacity=".22" stroke="${accent}" stroke-width="4" filter="url(#${glowId})"/>
      <path d="M ${-width/2+18} 0 H ${width/2-18}" stroke="${accent}" stroke-width="7" stroke-linecap="round"/>
      ${Array.from({length: Math.min(10, Math.max(3, Math.floor(width/100)))}, (_,i)=> {
        const px = -width/2 + 34 + i*((width-68)/Math.max(1, Math.min(10, Math.max(3, Math.floor(width/100)))-1));
        return `<circle cx="${px.toFixed(1)}" cy="0" r="5" fill="#ffffff" opacity=".75"/>`;
      }).join("")}
      ${label ? `<text x="0" y="${-height/2-18}" text-anchor="middle" class="dyn-label" font-size="25">${esc(label)}</text>` : ""}
    `;
  } else if (primitive === "beam") {
    const endX = n(g.endX, n(g.x,0.5)+0.2, 0, 1) * 1080;
    const endY = n(g.endY, n(g.y,0.5), 0, 1) * 1920;
    shape = `
      <line x1="0" y1="0" x2="${(endX-x).toFixed(1)}" y2="${(endY-y).toFixed(1)}" stroke="${accent}" stroke-width="${Math.max(5, height*0.12)}" stroke-linecap="round" marker-end="url(#dyn-arrow-${sceneIndex})" filter="url(#${glowId})"/>
    `;
  } else if (primitive === "node") {
    shape = `
      <circle r="${Math.min(width,height)*0.35}" fill="${fill}" fill-opacity=".42" stroke="${accent}" stroke-width="5" filter="url(#${glowId})"/>
      <circle r="${Math.min(width,height)*0.13}" fill="${accent}"/>
      ${label ? `<text x="0" y="${Math.min(width,height)*0.62}" text-anchor="middle" class="dyn-label" font-size="${fontSize}">${esc(label)}</text>` : ""}
    `;
  } else if (primitive === "panel") {
    shape = `
      <rect x="${-width/2}" y="${-height/2}" width="${width}" height="${height}" rx="24" fill="${fill}" fill-opacity=".22" stroke="${accent}" stroke-width="3"/>
      <path d="M ${-width/2+18} ${-height/2+22} H ${width/2-18}" stroke="${accent}" stroke-width="4" opacity=".8"/>
      ${label ? `<text x="0" y="10" text-anchor="middle" class="dyn-label" font-size="${fontSize}">${esc(label)}</text>` : ""}
    `;
  } else if (primitive === "label") {
    shape = `<text x="0" y="0" text-anchor="middle" dominant-baseline="middle" class="dyn-label" font-size="${fontSize}">${esc(label || a.form || element.role)}</text>`;
  } else if (primitive === "particle-field") {
    shape = Array.from({length: 32},(_,i)=>{
      const px = ((i*73)%97)/97*width-width/2;
      const py = ((i*41)%89)/89*height-height/2;
      const r = 2+(i%4)*1.5;
      return `<circle cx="${px.toFixed(1)}" cy="${py.toFixed(1)}" r="${r}" fill="${i%5===0?accent:fill}" opacity="${0.25+(i%5)*0.12}"/>`;
    }).join("");
  } else if (primitive === "image" && assetPath) {
    shape = `<image href="${esc(assetPath)}" x="${-width/2}" y="${-height/2}" width="${width}" height="${height}" preserveAspectRatio="xMidYMid meet"/>`;
  } else {
    throw new Error(`Dynamic renderer does not support primitive "${primitive}" for element "${id}".`);
  }

  return `
    <defs>
      <linearGradient id="${gradId}" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stop-color="${accent}"/>
        <stop offset="48%" stop-color="${fill}"/>
        <stop offset="100%" stop-color="#160b2c"/>
      </linearGradient>
    </defs>
    <g id="${id}" class="dyn-element" transform="${transform}" data-purpose="${esc(element.purpose)}">
      <title>${esc(element.purpose)}</title>
      ${shape}
    </g>
  `;
}
function isRenderableLabel(value) {
  return typeof value === "string" && value.trim().length > 0;
}

export function renderDynamicSceneHtml(scene, sceneIndex) {
  const d = scene?.sceneDirection;
  if (!d || !Array.isArray(d.elements) || d.elements.length < 2) {
    throw new Error(`Scene ${sceneIndex + 1} is missing a renderable dynamic sceneDirection.`);
  }
  const background = color(d.composition?.environment?.background, "#100821");
  const elements = d.elements.map((el, i) => elementSvg(el, i, sceneIndex)).join("\n");
  return `
    <div class="dynamic-scene-world" role="img" aria-label="${esc(d.visualIntent)}">
      <svg class="dynamic-scene-svg" viewBox="0 0 1080 1920" preserveAspectRatio="xMidYMid meet" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <filter id="dyn-glow-${sceneIndex}" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="13" result="blur"/>
            <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
          </filter>
          <marker id="dyn-arrow-${sceneIndex}" markerWidth="12" markerHeight="12" refX="9" refY="6" orient="auto">
            <path d="M0,0 L12,6 L0,12 Z" fill="#a3e635"/>
          </marker>
        </defs>
        <rect width="1080" height="1920" fill="${background}"/>
        <g class="dynamic-camera" id="dynamic-camera-${sceneIndex}">
          ${elements}
        </g>
      </svg>
    </div>
  `;
}

function normalizeAnchorWord(value) {
  return String(value ?? "").normalize("NFKC").toLocaleLowerCase().replace(/[^\p{L}\p{N}]+/gu, "");
}

function phraseTime(scene, trigger = {}) {
  if (trigger.type === "timecode") {
    const time = Number(trigger.anchor);
    if (!Number.isFinite(time) || time < 0) {
      throw new Error(`Invalid timecode trigger "${trigger.anchor}" in scene "${scene.id}".`);
    }
    return time;
  }

  const phraseTokens = String(trigger.anchor || "").trim().split(/\s+/).map(normalizeAnchorWord).filter(Boolean);
  const words = Array.isArray(scene.wordTimings) ? scene.wordTimings : [];
  if (phraseTokens.length === 0 || words.length === 0) {
    throw new Error(`Scene "${scene.id}" has no exact word timing for choreography trigger "${trigger.anchor}".`);
  }

  for (let start = 0; start <= words.length - phraseTokens.length; start += 1) {
    const matches = phraseTokens.every((token, offset) =>
      normalizeAnchorWord(words[start + offset]?.text) === token
    );
    if (matches) return words[start].startTime;
  }
  throw new Error(`Spoken-phrase trigger "${trigger.anchor}" was not found in scene "${scene.id}" word timings.`);
}
function motionProps(state) {
  const safe = localAnimationState(state);
  return Object.entries(safe).map(([key,value]) => `${key}: ${value}`).join(", ");
}

export function buildDynamicSceneAnimation(scene, sceneIndex) {
  const d = scene?.sceneDirection;
  if (!d) throw new Error(`Scene ${sceneIndex + 1} has no sceneDirection for animation.`);
  const output = [];
  const camera = d.composition?.camera?.animation;
  if (camera?.from && camera?.to) {
    output.push(`
      tl.fromTo("#scene-${sceneIndex} #dynamic-camera-${sceneIndex}",
        { ${motionProps(camera.from)} },
        { ${motionProps(camera.to)}, duration: ${n(camera.duration, scene.duration, 0.05, 20)}, ease: "${safeEase(camera.ease)}" },
        ${n(scene.startTime,0,0,36000).toFixed(3)}
      );
    `);
  }

  (d.choreography || []).forEach((action) => {
    const at = phraseTime(scene, action.trigger || {});
    const duration = n(action.animation?.duration, action.duration || 0.8, 0.05, 15);
    const ease = safeEase(action.animation?.ease);
    const target = safeId(action.target, "");
    if (!target) return;
    output.push(`
      tl.fromTo("#scene-${sceneIndex} #${target}",
        { ${motionProps(action.animation?.from)} },
        { ${motionProps(action.animation?.to)}, duration: ${duration}, ease: "${ease}" },
        ${at.toFixed(3)}
      );
    `);
    (action.reactionMotions || []).forEach((reaction) => {
      const reactionTarget = safeId(reaction.target, "");
      if (!reactionTarget) return;
      output.push(`
        tl.fromTo("#scene-${sceneIndex} #${reactionTarget}",
          { ${motionProps(reaction.from)} },
          { ${motionProps(reaction.to)}, duration: ${n(reaction.duration,0.4,0.05,15)}, ease: "${safeEase(reaction.ease)}" },
          ${at.toFixed(3)}
        );
      `);
    });
  });
  return output.join("\n");
}
