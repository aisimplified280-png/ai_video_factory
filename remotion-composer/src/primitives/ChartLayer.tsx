import React from 'react';
import type {ThemeProps} from '../runtime/props';

export interface ChartBar {
  label: string;
  /** 0..1 normalized value. */
  value: number;
}

export interface ChartLayerProps {
  theme: ThemeProps;
  bars: ChartBar[];
  /** 0..1 overall reveal driven by count/compare motion. */
  reveal?: number;
}

/** Declarative bar chart rendered from a chart asset's native spec. */
export const ChartLayer: React.FC<ChartLayerProps> = ({theme, bars, reveal = 1}) => {
  const shown = Math.max(1, Math.round(bars.length * Math.min(1, Math.max(0, reveal))));
  const visible = bars.slice(0, shown);
  return (
    <div style={{display: 'flex', alignItems: 'flex-end', justifyContent: 'center', gap: 36, height: '100%', padding: 80}}>
      {visible.map((bar) => (
        <div key={bar.label} style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16}}>
          <div
            style={{
              width: 90,
              height: Math.max(8, 640 * Math.min(1, Math.max(0, bar.value))),
              background: `linear-gradient(180deg, ${theme.accent} 0%, ${theme.accentSecondary} 100%)`,
              borderRadius: theme.cornerRadius,
            }}
          />
          <div style={{fontFamily: theme.fontFamily, fontSize: theme.bodySize * 0.7, color: theme.mutedText}}>{bar.label}</div>
        </div>
      ))}
    </div>
  );
};
