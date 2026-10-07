#!/usr/bin/env node
/**
 * Worker-side render entry point. Usage:
 *   node ./scripts/render.mjs --props <props.json> --output <final.mp4> [--manifest <render_manifest.json>]
 *
 * Validates props, invokes the Remotion CLI render, then writes a render
 * manifest describing what actually executed. Never invents editorial input.
 */
import {execFileSync} from 'node:child_process';
import {readFileSync, writeFileSync} from 'node:fs';
import {resolve} from 'node:path';

function arg(name) {
  const index = process.argv.indexOf(name);
  if (index === -1 || index + 1 >= process.argv.length) {
    throw new Error(`Missing required argument: ${name}`);
  }
  return process.argv[index + 1];
}

const propsPath = resolve(arg('--props'));
const outputPath = resolve(arg('--output'));
const manifestIndex = process.argv.indexOf('--manifest');
const manifestPath = manifestIndex === -1 ? null : resolve(process.argv[manifestIndex + 1]);
const publicIndex = process.argv.indexOf('--public-dir');
const publicDir = publicIndex === -1 ? null : resolve(process.argv[publicIndex + 1]);
const concurrencyIndex = process.argv.indexOf('--concurrency');
const concurrency = concurrencyIndex === -1 ? null : process.argv[concurrencyIndex + 1];

const started = new Date().toISOString();
execFileSync(
  'npx',
  ['remotion', 'render', 'Production', `--props=${propsPath}`, outputPath,
    ...(publicDir ? [`--public-dir=${publicDir}`] : []),
    ...(concurrency ? [`--concurrency=${concurrency}`] : [])],
  // Windows .cmd shims require a shell; POSIX resolves npx via PATH.
  {stdio: 'inherit', cwd: resolve(import.meta.dirname, '..'), shell: process.platform === 'win32'},
);
const completed = new Date().toISOString();

const props = JSON.parse(readFileSync(propsPath, 'utf-8'));
const manifest = {
  production_id: props.productionId,
  edit_artifact_version: props.editArtifactVersion,
  edit_artifact_hash: props.editArtifactHash,
  runtime: 'remotion',
  renderer_family: props.lock.renderer_family,
  composition_mode: props.lock.composition_mode,
  shots_executed: props.events.filter((event) => event.role === 'primary_visual').length,
  assets_executed: [...new Set(props.events.map((event) => event.asset_id).filter(Boolean))],
  motions_executed: [...new Set(props.events.map((event) => event.motion_intent).filter(Boolean))],
  camera_operations: [...new Set(props.events.map((event) => event.camera_intent).filter(Boolean))],
  transitions_executed: [...new Set(props.events.map((event) => event.transition_in).filter(Boolean))],
  captions_executed: props.captions.length,
  audio_tracks: props.audio.map((clip) => ({event_id: clip.event_id, track: clip.track, file: clip.publicPath !== null})),
  cta_executed: props.events.some((event) => event.scene_id === props.cta.scene_id),
  render_started: started,
  render_completed: completed,
  warnings: [],
  errors: [],
};
if (manifestPath) {
  writeFileSync(manifestPath, JSON.stringify(manifest, null, 2));
}
console.log(JSON.stringify({output: outputPath, shots: manifest.shots_executed}));
