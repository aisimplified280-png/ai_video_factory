// pipeline/dynamic-scene-gate.mjs
// Fail-closed creative preflight for new, non-template AI Simplified Lab videos.

const isText = (value) => typeof value === "string" && value.trim().length > 0;
const isFiniteNumber = (value) => typeof value === "number" && Number.isFinite(value);
const hasMotionState = (state) => state && ["x", "y", "scale", "rotation", "opacity"].some((key) => isFiniteNumber(state[key]));
const ELEMENT_PRIMITIVES = new Set(["orb", "ring", "capsule", "packet", "rail", "beam", "node", "panel", "label", "particle-field", "image"]);
const ELEMENT_ID = /^[A-Za-z][A-Za-z0-9_-]{0,63}$/;
const normalizePhrase = (value) => String(value ?? "").normalize("NFKC").toLocaleLowerCase().replace(/[^\p{L}\p{N}]+/gu, " ").trim();

export function validateDynamicScenePlan(project, options = {}) {
  const errors = [];
  const scenes = Array.isArray(project?.scenes) ? project.scenes : [];

  if (project?.productionMode !== "dynamic") {
    errors.push('New projects must set productionMode to "dynamic".');
  }
  if (scenes.length === 0) {
    errors.push("Dynamic project must contain at least one scene.");
    return { passed: false, errors, sceneCount: 0 };
  }

  const signatures = new Map();

  scenes.forEach((scene, index) => {
    const n = index + 1;
    const d = scene?.sceneDirection;
    const prefix = `Scene ${n}`;

    if (!isText(scene?.voiceText)) errors.push(`${prefix}: voiceText is required.`);
    if (!d || typeof d !== "object") {
      errors.push(`${prefix}: sceneDirection is required; no legacy card fallback is allowed.`);
      return;
    }

    if (scene.cardType || d.cardType || d.template || d.layoutPreset || d.slideLayout) {
      errors.push(`${prefix}: cardType/template/slide layout is prohibited in dynamic mode.`);
    }
    if (!isText(d.narrativePurpose)) errors.push(`${prefix}: narrativePurpose is required.`);
    if (!isText(d.visualIntent)) errors.push(`${prefix}: visualIntent is required.`);
    if (!isText(d.visualMetaphor)) errors.push(`${prefix}: visualMetaphor or concrete visual mechanism is required.`);

    const composition = d.composition || {};
    if (!isText(composition.signature)) {
      errors.push(`${prefix}: a unique composition.signature is required.`);
    } else if (signatures.has(composition.signature)) {
      const hasContinuity = isText(d.transition?.continuityReason) &&
        /return|revisit|continuity|same subject|match/i.test(d.transition.continuityReason);
      if (!hasContinuity) {
        errors.push(`${prefix}: composition signature "${composition.signature}" repeats Scene ${signatures.get(composition.signature)} without a story reason.`);
      }
    } else {
      signatures.set(composition.signature, n);
    }
    if (!isText(composition.shotType)) errors.push(`${prefix}: composition.shotType is required.`);
    if (!isText(composition.camera?.move) || !isText(composition.camera?.target) || !isText(composition.camera?.path)) {
      errors.push(`${prefix}: camera move, target and path rationale are required.`);
    }
    if (!Array.isArray(composition.depthLayers) || composition.depthLayers.length < 2) {
      errors.push(`${prefix}: at least two purposeful depth layers are required.`);
    }
    if (!Array.isArray(composition.focalHierarchy) || composition.focalHierarchy.length < 1) {
      errors.push(`${prefix}: focalHierarchy is required.`);
    }
    if (!isText(composition.negativeSpace)) errors.push(`${prefix}: caption-safe negative space must be planned.`);
    if (!hasMotionState(composition.camera?.animation?.from) || !hasMotionState(composition.camera?.animation?.to)) {
      errors.push(`${prefix}: camera animation from/to states are required.`);
    }

    const event = d.visualEvent || {};
    for (const field of ["setup", "action", "payoff"]) {
      if (!isText(event[field])) errors.push(`${prefix}: visualEvent.${field} is required.`);
    }

    const elements = Array.isArray(d.elements) ? d.elements : [];
    if (elements.length < 2) errors.push(`${prefix}: at least two purposeful scene elements are required.`);
    const ids = new Set();
    elements.forEach((element, eIndex) => {
      const label = element?.id || eIndex;
      if (!isText(element?.id) || !ELEMENT_ID.test(element.id)) errors.push(`${prefix}: element [${eIndex}] needs a renderer-safe id.`);
      if (ids.has(element?.id)) errors.push(`${prefix}: duplicate element id "${element.id}".`);
      ids.add(element?.id);
      if (!isText(element?.role)) errors.push(`${prefix}: element "${label}" needs a role.`);
      if (!isText(element?.purpose)) errors.push(`${prefix}: element "${label}" needs an explicit narrative purpose.`);
      if (!isText(element?.source)) errors.push(`${prefix}: element "${label}" needs a source type.`);
      if (!isText(element?.motionRole)) errors.push(`${prefix}: element "${label}" needs a participation/motion role.`);
      if (!ELEMENT_PRIMITIVES.has(element?.appearance?.primitive)) errors.push(`${prefix}: element "${label}" needs a supported appearance.primitive.`);
      if (!element?.geometry || !isFiniteNumber(element.geometry.x) || !isFiniteNumber(element.geometry.y) || element.geometry.x < 0 || element.geometry.x > 1 || element.geometry.y < 0 || element.geometry.y > 1) {
        errors.push(`${prefix}: element "${label}" needs normalized geometry coordinates.`);
      }
      if (element?.source === "licensed" && !isText(element.licenseEvidence)) {
        errors.push(`${prefix}: licensed element "${label}" needs licence evidence.`);
      }
    });
    if (isText(d.primarySubject) && !ids.has(d.primarySubject)) {
      errors.push(`${prefix}: primarySubject "${d.primarySubject}" is not a declared element.`);
    }

    const choreography = Array.isArray(d.choreography) ? d.choreography : [];
    if (choreography.length === 0) errors.push(`${prefix}: at least one scene-specific motion event is required.`);
    choreography.forEach((action, aIndex) => {
      const label = action?.event || aIndex;
      if (!["spoken-phrase", "timecode"].includes(action?.trigger?.type) || !isText(action?.trigger?.anchor)) {
        errors.push(`${prefix}: choreography event "${label}" needs a supported spoken-phrase or timecode trigger and anchor.`);
      } else if (action.trigger.type === "spoken-phrase") {
        const phrase = normalizePhrase(action.trigger.anchor);
        const narration = normalizePhrase(scene.voiceText);
        if (!phrase || !narration.includes(phrase)) {
          errors.push(`${prefix}: spoken-phrase trigger "${action.trigger.anchor}" does not occur in the narration.`);
        }
      } else if (!Number.isFinite(Number(action.trigger.anchor)) || Number(action.trigger.anchor) < 0) {
        errors.push(`${prefix}: timecode trigger "${action.trigger.anchor}" must be a non-negative project time in seconds.`);
      }
      if (!isText(action?.target) || !ids.has(action.target)) {
        errors.push(`${prefix}: choreography event "${label}" targets an undeclared element.`);
      }
      if (!isText(action?.event) || !isText(action?.pathOrChange)) {
        errors.push(`${prefix}: choreography event [${aIndex}] needs an event and visible change/path.`);
      }
      if (!isFiniteNumber(action?.duration) || action.duration <= 0) {
        errors.push(`${prefix}: choreography event "${label}" needs a positive duration.`);
      }
      if (!isText(action?.purpose)) errors.push(`${prefix}: choreography event "${label}" needs a purpose.`);
      if (!hasMotionState(action?.animation?.from) || !hasMotionState(action?.animation?.to)) {
        errors.push(`${prefix}: choreography event "${label}" needs explicit from/to motion states.`);
      }
      const reactionMotions = Array.isArray(action?.reactionMotions) ? action.reactionMotions : [];
      if (reactionMotions.length === 0) {
        errors.push(`${prefix}: choreography event "${label}" needs executable reactionMotions for its cause-and-effect targets.`);
      }
      reactionMotions.forEach((motion) => {
        if (!ids.has(motion?.target) || !hasMotionState(motion?.from) || !hasMotionState(motion?.to)) {
          errors.push(`${prefix}: choreography event "${label}" has an invalid reaction motion target/state.`);
        }
      });
      const reactionTargets = new Set(reactionMotions.map((motion) => motion.target));
      (action?.causeAndEffect?.reacts || []).forEach((id) => {
        if (!reactionTargets.has(id)) {
          errors.push(`${prefix}: choreography event "${label}" declares reaction "${id}" without executable reaction motion.`);
        }
      });
      const reaction = action?.causeAndEffect;
      if (!Array.isArray(reaction?.reacts) || reaction.reacts.length === 0 || !isText(reaction?.reaction)) {
        errors.push(`${prefix}: choreography event "${label}" needs a visible cause-and-effect reaction.`);
      } else {
        reaction.reacts.forEach((id) => {
          if (!ids.has(id)) errors.push(`${prefix}: choreography event "${label}" reacts through undeclared element "${id}".`);
        });
      }
      if (!isText(action?.soundCue?.type) || !isText(action?.soundCue?.purpose) || (action.soundCue.type !== "deliberate-silence" && (!isText(action.soundCue.assetKey) || !isFiniteNumber(action.soundCue.offsetSeconds) || action.soundCue.offsetSeconds < 0))) {
        errors.push(`${prefix}: choreography event "${label}" needs a purpose-led SFX assetKey or documented deliberate silence.`);
      } else if (action.soundCue.type !== "deliberate-silence" && options.allowedSfxIds instanceof Set && !options.allowedSfxIds.has(action.soundCue.assetKey)) {
        errors.push(`${prefix}: choreography event "${label}" references unknown SFX asset "${action.soundCue.assetKey}".`);
      }
    });

    const audio = d.audio || {};
    if (!isText(audio.voiceSegment)) errors.push(`${prefix}: audio.voiceSegment must match the scene narration.`);
    if (!isText(audio.ambience)) errors.push(`${prefix}: ambience or deliberate silence must be declared.`);
    if (!isText(audio.musicCue)) errors.push(`${prefix}: musicCue or intentional no-music direction must be declared.`);
    if (!isText(audio.ducking)) errors.push(`${prefix}: dialogue ducking/mix direction is required.`);

    const captions = d.captions || {};
    if (!["word-synced", "phrase-synced"].includes(captions.mode)) {
      errors.push(`${prefix}: captions mode must be word-synced or phrase-synced.`);
    }
    if (!isText(captions.anchor) || !isText(captions.treatment)) {
      errors.push(`${prefix}: caption anchor and treatment are required.`);
    }
    const placement = captions.placement || {};
    if (!isFiniteNumber(placement.x) || placement.x < 5 || placement.x > 95 ||
        !isFiniteNumber(placement.y) || placement.y < 5 || placement.y > 95 ||
        !["left", "center", "right"].includes(placement.align) ||
        !isFiniteNumber(placement.maxWidth) || placement.maxWidth < 240 || placement.maxWidth > 1080) {
      errors.push(`${prefix}: scene-specific caption placement needs x/y percentages, align and maxWidth in pixels.`);
    }
    const captionStyle = captions.style || {};
    const validColor = (value) => typeof value === "string" &&
      /^#[0-9a-fA-F]{6}(?:[0-9a-fA-F]{2})?$/.test(value);
    if (!isFiniteNumber(captionStyle.fontSize) || captionStyle.fontSize < 18 || captionStyle.fontSize > 90 ||
        !isFiniteNumber(captionStyle.fontWeight) || captionStyle.fontWeight < 400 || captionStyle.fontWeight > 900 ||
        !validColor(captionStyle.color) || !validColor(captionStyle.highlightColor) ||
        !(captionStyle.activeBackgroundColor === "transparent" || validColor(captionStyle.activeBackgroundColor))) {
      errors.push(`${prefix}: scene-specific caption typography needs bounded fontSize/fontWeight and valid ink/highlight colours.`);
    }

    if (!["hard-cut", "cross-dissolve", "camera-continuation"].includes(d.transition?.type) || !isText(d.transition?.continuityReason)) {
      errors.push(`${prefix}: transition type and narrative reason are required (use a reasoned hard cut or ending when appropriate).`);
    }
  });

  return {
    passed: errors.length === 0,
    errors,
    sceneCount: scenes.length,
    uniqueCompositionCount: signatures.size,
  };
}

export function assertDynamicScenePlan(project, options = {}) {
  const result = validateDynamicScenePlan(project, options);
  if (!result.passed) {
    const detail = result.errors.map((error) => ` - ${error}`).join("\n");
    throw new Error(`Dynamic scene creative gate failed. No generation or rendering may proceed until fixed:\n${detail}`);
  }
  return result;
}
