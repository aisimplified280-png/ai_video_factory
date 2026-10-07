# Remote Remotion worker runbook

The local factory is remote-first for Remotion: no Node toolchain is required
locally. A worker is any machine with Node 18+, npm, Chrome (installed by
Remotion on first render), and FFmpeg.

## What the factory sends

`package_remote_bundle()` produces `<production>_remotion-bundle.zip` with:

- `props/props.json` — validated `ProductionCompositionProps`
- `props/edit_decisions.json`, `scene_plan.json`, `asset_manifest.json`,
  `art_direction.json`, `script.json`, `platform.json` — canonical sources
- `assets/` — every manifest media file, flattened by asset id
- `remote_job.json` — `{bundle_version: "remote-job/v1", runtime: "remotion",
  production_id, edit_artifact_version, edit_artifact_hash, ...}` plus the
  exact worker steps below

## Worker steps (exact, in order)

1. Unzip the bundle next to a checkout of `remotion-composer/` at the pinned
   `package.json` versions. Never substitute dependency versions.
2. Copy `props/props.json` to a worker-local path and `assets/*` into the
   composer's `public/assets/` directory.
3. `npm install --no-audit --no-fund` (or `npm ci` when a lockfile ships).
4. `npm run validate` — must exit 0 (`tsc --noEmit`).
5. `node ./scripts/render.mjs --props <props.json> --output <final.mp4>
   --manifest <render_manifest.json>`
6. Verify with ffprobe: H.264, 1080x1920, 30fps, expected duration.
7. Sync back, at minimum: `final.mp4`, `render_manifest.json`,
   `render_report.json`, `contact_sheet.png`, `sample_frames/`.

## Worker must never

- pick a different runtime, composition mode, or renderer family;
- regenerate timing, captions, or asset choices;
- substitute a missing asset (fail the render with the asset id instead);
- report success without the ffprobe verification from step 6.
