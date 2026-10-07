import React from 'react';
import {AbsoluteFill, interpolate, interpolateColors} from 'remotion';
import type {ThemeProps} from '../runtime/props';

export interface BackgroundLayerProps {
  theme: ThemeProps;
  environment: string | null;
  sceneId?: string;
  subject?: string;
  visualPurpose?: string;
  progress?: number;
  isAITopic?: boolean;
}

/**
 * Dynamic Theme & Procedural Background Engine.
 * Dynamically switches base palettes, radial tints, and procedural micro-textures
 * based on the active scene context (Deep Tech, High Density Tokens, Self-Attention, Vector Space, Alert, Outro).
 */
export const BackgroundLayer: React.FC<BackgroundLayerProps> = ({
  theme,
  environment,
  sceneId = '',
  subject = '',
  visualPurpose = '',
  progress = 0,
  isAITopic = false,
}) => {
  const p = Math.max(0, Math.min(1, progress));
  const sc = sceneId.toLowerCase();
  const sub = subject.toLowerCase();
  const vis = visualPurpose.toLowerCase();

  // Dynamic Theme Selection: Clean off-white paper canvas (#F8FAFC / #F1F5F9)
  let primaryBg = '#F8FAFC';    // Clean off-white paper canvas
  let secondaryTint = '#F1F5F9'; // Soft Slate Glow
  let microTexture: 'tech_grid' | 'cyber_matrix' | 'neural_mesh' | 'starfield' | 'hazard_ember' | 'brand_vignette' = 'tech_grid';
  let accentGlow = '#1E40AF';   // Brand Royal Blue ambient glow

  if (sc.includes('scene_05') || sc.includes('sec_05') || sc.includes('brand') || sc.includes('cta')) {
    // 1. Outro / Brand Summary: Off-white canvas with royal blue ambient glow
    primaryBg = '#F8FAFC';
    secondaryTint = '#F1F5F9';
    accentGlow = '#1E40AF';
    microTexture = 'brand_vignette';
  } else if (
    (isAITopic && (sc.includes('scene_04') || sc.includes('sec_04'))) ||
    sub.includes('vector') ||
    sub.includes('embedding') ||
    vis.includes('embedding') ||
    vis.includes('cloud')
  ) {
    // 2. 3D Vector Space: Crisp Off-White with Royal Blue Tint
    primaryBg = '#F8FAFC';
    secondaryTint = '#EDF2F7';
    accentGlow = '#1E40AF';
    microTexture = 'starfield';
  } else if (
    (isAITopic && (sc.includes('scene_03') || sc.includes('sec_03'))) ||
    sub.includes('attention') ||
    vis.includes('attention') ||
    sub.includes('weight')
  ) {
    // 3. Self-Attention / Neural Graph: Clean Off-White + Amber & Royal Blue Hue
    primaryBg = '#F8FAFC';
    secondaryTint = '#F1F5F9';
    accentGlow = '#D97706';
    microTexture = 'neural_mesh';
  } else if (
    (isAITopic && (sc.includes('scene_02') || sc.includes('sec_02'))) ||
    sub.includes('token') ||
    vis.includes('token') ||
    sub.includes('fragment') ||
    sub.includes('matrix')
  ) {
    // 4. Numerical Tokenization: Clean Paper with Royal Blue Accent
    primaryBg = '#F8FAFC';
    secondaryTint = '#EFF6FF';
    accentGlow = '#1E40AF';
    microTexture = 'cyber_matrix';
  } else if (
    sub.includes('obstacle') ||
    sub.includes('reroute') ||
    sub.includes('hazard') ||
    vis.includes('obstacle') ||
    vis.includes('reroute')
  ) {
    // 5. Alert / Action: Off-White with Amber Accent
    primaryBg = '#FAF6F0';
    secondaryTint = '#F5ECE0';
    accentGlow = '#D97706';
    microTexture = 'hazard_ember';
  } else {
    // 6. Hook / Natural Language Input: Clean Blueprint Paper
    primaryBg = '#F8FAFC';
    secondaryTint = '#F1F5F9';
    accentGlow = '#1E40AF';
    microTexture = 'tech_grid';
  }

  // Subtle breathing vignette pulse
  const vignettePulse = 0.85 + Math.sin(p * Math.PI * 2) * 0.08;
  const radialSpread = 90 + p * 15;

  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(130% ${radialSpread}% at 50% 25%, ${secondaryTint} 0%, ${primaryBg} 75%)`,
        overflow: 'hidden',
      }}
      data-environment={environment ?? undefined}
      data-texture={microTexture}
    >
      {/* Procedural Micro-Textures */}
      <svg
        width="100%"
        height="100%"
        viewBox="0 0 1080 1920"
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          pointerEvents: 'none',
          opacity: 0.95,
        }}
      >
        <defs>
          <radialGradient id="ambientOrb" cx="50%" cy="30%" r="50%">
            <stop offset="0%" stopColor={accentGlow} stopOpacity="0.04" />
            <stop offset="100%" stopColor={accentGlow} stopOpacity="0.0" />
          </radialGradient>
        </defs>

        {/* Ambient atmospheric warm glow orb */}
        <circle cx={540} cy={480} r={520} fill="url(#ambientOrb)" />

        {/* 1. Fine Engineering Blueprint Grid Micro-Texture (#CBD5E1, 20-25% Opacity) */}
        {microTexture === 'tech_grid' && (
          <g opacity={0.25}>
            {[180, 360, 540, 720, 900].map((x) => (
              <line key={`grid-x-${x}`} x1={x} y1={0} x2={x} y2={1920} stroke="#CBD5E1" strokeWidth={1} strokeDasharray="6 6" />
            ))}
            {[320, 640, 960, 1280, 1600].map((y) => (
              <line key={`grid-y-${y}`} x1={0} y1={y} x2={1080} y2={y} stroke="#CBD5E1" strokeWidth={1} strokeDasharray="6 6" />
            ))}
          </g>
        )}

        {/* 2. Cyber Matrix Subtle Dot Grid Micro-Texture */}
        {microTexture === 'cyber_matrix' && (
          <g opacity={0.35}>
            {[180, 360, 540, 720, 900].map((x) =>
              [400, 600, 800, 1000, 1200, 1400].map((y) => (
                <circle key={`dot-${x}-${y}`} cx={x} cy={y} r={2} fill="#CBD5E1" />
              ))
            )}
          </g>
        )}

        {/* 3. Neural Mesh Arcs Micro-Texture */}
        {microTexture === 'neural_mesh' && (
          <g opacity={0.45}>
            <circle cx={540} cy={800} r={280} fill="none" stroke="#E2E8F0" strokeWidth={1} strokeDasharray="6 6" />
            <circle cx={540} cy={800} r={480} fill="none" stroke="#E2E8F0" strokeWidth={1} strokeDasharray="8 8" />
            <line x1={200} y1={400} x2={880} y2={1200} stroke="#E2E8F0" strokeWidth={0.8} strokeDasharray="4 6" />
            <line x1={880} y1={400} x2={200} y2={1200} stroke="#E2E8F0" strokeWidth={0.8} strokeDasharray="4 6" />
          </g>
        )}

        {/* 4. Vector Space Subtle Coordinate Ticks */}
        {microTexture === 'starfield' && (
          <g opacity={0.35}>
            {[
              [140, 320, 1.5], [890, 420, 2], [320, 680, 1], [760, 820, 1.8],
              [210, 1100, 1.2], [940, 1240, 1.5], [480, 1420, 2], [820, 1560, 1.2],
            ].map(([sx, sy, sr], idx) => (
              <circle key={`star-${idx}`} cx={sx} cy={sy} r={sr} fill="#94A3B8" />
            ))}
          </g>
        )}

        {/* 5. Alert Hazard Subtle Guide Lines */}
        {microTexture === 'hazard_ember' && (
          <g opacity={0.25}>
            {[300, 600, 900, 1200, 1500].map((hy) => (
              <line key={`haz-${hy}`} x1={0} y1={hy} x2={1080} y2={hy + 200} stroke="#E2E8F0" strokeWidth={1} strokeDasharray="10 10" />
            ))}
          </g>
        )}

        {/* 6. Brand Vignette Vignette Border */}
        {microTexture === 'brand_vignette' && (
          <rect
            x={0}
            y={0}
            width={1080}
            height={1920}
            fill="none"
            stroke="#E5E0D8"
            strokeWidth={140}
            opacity={0.25 * vignettePulse}
          />
        )}
      </svg>
    </AbsoluteFill>
  );
};
