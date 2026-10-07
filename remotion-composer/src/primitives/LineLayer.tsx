import React from 'react';

export interface LineLayerProps {
  width: number;
  height: number;
  /** 0..1 fraction of the path revealed (trace motion drives this). */
  reveal?: number;
  color: string;
  strokeWidth?: number;
  path?: string;
}

/** Connector/flow line with deterministic partial reveal for trace motion. */
export const LineLayer: React.FC<LineLayerProps> = ({
  width,
  height,
  reveal = 1,
  color,
  strokeWidth = 6,
  path,
}) => {
  const d = path ?? `M ${width * 0.15} ${height * 0.5} L ${width * 0.85} ${height * 0.5}`;
  const total = 1000;
  const visible = Math.max(0, Math.min(1, reveal)) * total;
  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
      <path
        d={d}
        fill="none"
        stroke={color}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeDasharray={`${visible} ${total}`}
      />
    </svg>
  );
};
