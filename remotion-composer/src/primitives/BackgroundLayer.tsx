import React from 'react';
import {AbsoluteFill} from 'remotion';
import type {ThemeProps} from '../runtime/props';

export interface BackgroundLayerProps {
  theme: ThemeProps;
  environment?: string | null;
  sceneId?: string;
  subject?: string;
  visualPurpose?: string;
  progress?: number;
  isAITopic?: boolean;
}

/**
 * The constant "light engineered canvas" — ONE background for the entire video.
 *
 * Soft blue-gray radial paper, a crisp two-scale blueprint grid with crosshair
 * registration marks, a brand ambient glow, and a depth vignette. It never
 * changes, never wipes, and never animates with the scenes: only the CONTENT
 * elements enter and leave over it, which is what keeps the video reading as a
 * living canvas instead of a slideshow of frames.
 */
export const BackgroundLayer: React.FC<BackgroundLayerProps> = ({theme, environment}) => {
  const accent = theme?.accent && /^#[0-9A-Fa-f]{6}$/.test(theme.accent) ? theme.accent : '#1E40AF';
  const fine: number[] = [];
  for (let x = 90; x < 1080; x += 90) fine.push(x);
  const fineY: number[] = [];
  for (let y = 90; y < 1920; y += 90) fineY.push(y);
  const majorX = [360, 720];
  const majorY = [360, 720, 1080, 1440];

  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(120% 85% at 50% 18%, #FFFFFF 0%, #F3F7FC 46%, #E6EDF8 100%)`,
        overflow: 'hidden',
      }}
      data-environment={environment ?? undefined}
      data-canvas="engineered"
    >
      <svg
        width="100%"
        height="100%"
        viewBox="0 0 1080 1920"
        preserveAspectRatio="xMidYMid slice"
        style={{position: 'absolute', top: 0, left: 0, pointerEvents: 'none'}}
      >
        <defs>
          <radialGradient id="bgAmbientGlow" cx="50%" cy="26%" r="52%">
            <stop offset="0%" stopColor={accent} stopOpacity="0.06" />
            <stop offset="60%" stopColor={accent} stopOpacity="0.02" />
            <stop offset="100%" stopColor={accent} stopOpacity="0" />
          </radialGradient>
          <radialGradient id="bgDepthVignette" cx="50%" cy="46%" r="72%">
            <stop offset="0%" stopColor="#64748B" stopOpacity="0" />
            <stop offset="78%" stopColor="#64748B" stopOpacity="0" />
            <stop offset="100%" stopColor="#475569" stopOpacity="0.16" />
          </radialGradient>
        </defs>

        {/* Brand ambient glow — constant, never pulses. */}
        <rect x={0} y={0} width={1080} height={1920} fill="url(#bgAmbientGlow)" />

        {/* Fine blueprint grid (every 90px). */}
        <g stroke="#DCE5F2" strokeWidth={1} opacity={0.65}>
          {fine.map((x) => (
            <line key={`fx-${x}`} x1={x} y1={0} x2={x} y2={1920} />
          ))}
          {fineY.map((y) => (
            <line key={`fy-${y}`} x1={0} y1={y} x2={1080} y2={y} />
          ))}
        </g>

        {/* Major engineering axes (every 360px) — dashed, a shade deeper. */}
        <g stroke="#C4D2E7" strokeWidth={1.4} strokeDasharray="10 8" opacity={0.9}>
          {majorX.map((x) => (
            <line key={`mx-${x}`} x1={x} y1={0} x2={x} y2={1920} />
          ))}
          {majorY.map((y) => (
            <line key={`my-${y}`} x1={0} y1={y} x2={1080} y2={y} />
          ))}
        </g>

        {/* Crosshair registration marks where the major axes meet. */}
        <g stroke="#A9BCD8" strokeWidth={1.6} opacity={0.9}>
          {majorX.map((x) =>
            majorY.map((y) => (
              <g key={`xh-${x}-${y}`}>
                <line x1={x - 9} y1={y} x2={x + 9} y2={y} />
                <line x1={x} y1={y - 9} x2={x} y2={y + 9} />
              </g>
            )),
          )}
        </g>

        {/* Corner brackets — drafting-sheet framing. */}
        <g stroke="#B7C6DE" strokeWidth={3} fill="none" opacity={0.8}>
          <path d="M34 96 V34 H96" />
          <path d="M984 34 H1046 V96" />
          <path d="M1046 1824 V1886 H984" />
          <path d="M96 1886 H34 V1824" />
        </g>

        {/* Depth vignette — keeps the canvas feeling like a lit stage. */}
        <rect x={0} y={0} width={1080} height={1920} fill="url(#bgDepthVignette)" />
      </svg>
    </AbsoluteFill>
  );
};
