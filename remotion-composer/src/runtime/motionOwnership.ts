/**
 * One motion owner per element (§5 motion audit).
 *
 * The wrapper (SceneComposition) may only style ENTRANCE/EXIT of an element
 * that animates itself — the mascot owns all of its motion, and a native
 * diagram owns its own in-sequence reveal. Everything else receives the
 * canonical camera/motion intent (or nothing at all: static is the default).
 *
 * Kept pure so tests can drive the real decision logic instead of grepping
 * for it in JSX.
 */

export interface MotionAssetLike {
  nativeSpec?: unknown;
}

/** True when the element animates itself and the wrapper must not add camera/motion styles. */
export function ownsOwnMotion(
  role: string | null | undefined,
  asset?: MotionAssetLike | null,
): boolean {
  if (role === 'character') {
    return true;
  }
  const spec = asset?.nativeSpec as {nodes?: unknown[]} | null | undefined;
  const nodes = spec?.nodes;
  return Array.isArray(nodes) && nodes.length > 0;
}
