import React from 'react';
import {AbsoluteFill} from 'remotion';
import type {ThemeProps} from '../runtime/props';

export interface MetricLayerProps {
  theme: ThemeProps;
  value: string;
  label?: string;
  /** 0..1 reveal driven by count motion. */
  reveal?: number;
}

/** Overlay metric (counts, gauges, emphasis figures). Positioned by the event.
 * Long values wrap inside the frame instead of overflowing: layout safety is
 * a rendering responsibility, never a reason to drop content. */
export const MetricLayer: React.FC<MetricLayerProps> = ({theme, value, label, reveal = 1}) => {
  const size = value.length > 60 ? theme.headlineSize * 0.8 : theme.headlineSize * 1.6;
  return (
    <AbsoluteFill style={{display: 'flex', alignItems: 'center', justifyContent: 'center', opacity: Math.min(1, Math.max(0, reveal))}}>
      <div style={{textAlign: 'center', maxWidth: '86%', overflowWrap: 'break-word', wordBreak: 'break-word'}}>
        <div style={{fontFamily: theme.fontFamily, fontWeight: 800, fontSize: size, color: theme.accent, lineHeight: 1.25}}>{value}</div>
        {label ? (
          <div style={{fontFamily: theme.fontFamily, fontSize: theme.bodySize, color: theme.mutedText, marginTop: 12}}>{label}</div>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};
