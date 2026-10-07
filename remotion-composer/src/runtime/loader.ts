/**
 * Asset resolution for the composition. Manifest paths are project-root
 * relative (e.g. projects/<id>/assets/x.png); the props builder copies them
 * into the composer's public/assets/ directory, so at render time every
 * asset is addressed by its public path. Nothing is invented here: an asset
 * without a public path or native spec is a validation error, never a
 * silent substitution.
 */
import {staticFile} from 'remotion';
import type {AssetProps} from './props';

export function resolveAssetUrl(asset: AssetProps): string | null {
  if (asset.publicPath) {
    return staticFile(asset.publicPath);
  }
  return null;
}

export function requireAssetUrl(asset: AssetProps): string {
  const url = resolveAssetUrl(asset);
  if (!url) {
    throw new Error(
      `Asset ${asset.asset_id} has neither a public path nor a native representation; refusing to substitute.`,
    );
  }
  return url;
}

export function assetById(assets: AssetProps[], assetId: string | null): AssetProps | null {
  if (!assetId) {
    return null;
  }
  return assets.find((asset) => asset.asset_id === assetId) ?? null;
}
