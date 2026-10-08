/**
 * Pre-render validation. Any failure throws and prevents the render.
 * Mirrors the Python-side props validation; both must agree.
 */
import type {ProductionCompositionProps} from './props';

export function validateProductionProps(props: ProductionCompositionProps): string[] {
  const errors: string[] = [];
  if (!props.productionId) {
    errors.push('productionId is required');
  }
  if (!props.editArtifactHash.startsWith('sha256:')) {
    errors.push('editArtifactHash must be a sha256: digest');
  }
  if (props.lock.render_runtime !== 'remotion') {
    errors.push(`This composer only executes remotion jobs; got ${props.lock.render_runtime}`);
  }
  const {width, height} = props.platform.resolution;
  if (!(width > 0 && height > 0)) {
    errors.push('platform.resolution must be positive');
  }
  if (!(props.platform.fps > 0)) {
    errors.push('platform.fps must be positive');
  }
  const assetIds = new Set(props.assets.map((asset) => asset.asset_id));
  for (const event of props.events) {
    if (event.duration <= 0) {
      errors.push(`event ${event.event_id} has non-positive duration`);
    }
    if (event.asset_id && !assetIds.has(event.asset_id)) {
      errors.push(`event ${event.event_id} references unknown asset ${event.asset_id}`);
    }
    if (!event.purpose || event.purpose.length < 3) {
      errors.push(`event ${event.event_id} has no executable purpose`);
    }
  }
  const primaries = props.events.filter((event) => event.role === 'primary_visual' || event.role === 'primary_composite');
  if (primaries.length === 0) {
    errors.push('timeline has no primary_visual events');
  }
  const covered = new Set(props.events.map((event) => event.scene_id));
  for (const scene of props.scenes) {
    if (!covered.has(scene.scene_id)) {
      errors.push(`scene ${scene.scene_id} has no timeline events`);
    }
  }
  const ctaEvents = props.events.filter((event) => event.scene_id === props.cta.scene_id);
  if (ctaEvents.length === 0) {
    errors.push('CTA scene has no timeline events');
  }
  const lastEnd = Math.max(...props.events.map((event) => event.end));
  if (Math.abs(lastEnd - props.cta.end) > 0.05) {
    errors.push('CTA must extend to the end of the timeline');
  }
  for (const audio of props.audio) {
    if (audio.publicPath === null && audio.requirement === null) {
      errors.push(`audio event ${audio.event_id} is neither a file nor a deferred requirement`);
    }
  }
  return errors;
}

export function assertValidProps(props: ProductionCompositionProps): void {
  const errors = validateProductionProps(props);
  if (errors.length > 0) {
    throw new Error(`Invalid composition props:\n- ${errors.join('\n- ')}`);
  }
}
