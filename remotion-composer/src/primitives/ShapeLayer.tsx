import React from 'react';

export interface ShapeSpec {
  shape: 'circle' | 'rect' | 'line';
  x: number;
  y: number;
  size: number;
  length?: number;
  color: string;
  strokeWidth?: number;
  opacity?: number;
}

export interface ShapeLayerProps {
  width: number;
  height: number;
  shapes: ShapeSpec[];
}

/** Declarative vector shapes for atelier geometry and native specs. */
export const ShapeLayer: React.FC<ShapeLayerProps> = ({width, height, shapes}) => {
  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
      {shapes.map((shape, index) => {
        if (shape.shape === 'circle') {
          return <circle key={index} cx={shape.x} cy={shape.y} r={shape.size / 2} fill={shape.color} opacity={shape.opacity ?? 1} />;
        }
        if (shape.shape === 'line') {
          return (
            <line
              key={index}
              x1={shape.x}
              y1={shape.y}
              x2={shape.x + (shape.length ?? shape.size)}
              y2={shape.y}
              stroke={shape.color}
              strokeWidth={shape.strokeWidth ?? 4}
              opacity={shape.opacity ?? 1}
            />
          );
        }
        return (
          <rect
            key={index}
            x={shape.x - shape.size / 2}
            y={shape.y - shape.size / 2}
            width={shape.size}
            height={shape.size}
            fill={shape.color}
            opacity={shape.opacity ?? 1}
          />
        );
      })}
    </svg>
  );
};
