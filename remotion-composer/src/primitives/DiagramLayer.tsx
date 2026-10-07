import React from 'react';
import type {ThemeProps} from '../runtime/props';

export interface DiagramNode {
  id: string;
  label: string;
  x: number;
  y: number;
}

export interface DiagramConnector {
  from: string;
  to: string;
  label?: string;
}

export interface DiagramLayerProps {
  theme: ThemeProps;
  width: number;
  height: number;
  nodes: DiagramNode[];
  connectors: DiagramConnector[];
  /** 0..1 reveal driven by assemble/connect motion. */
  reveal?: number;
}

/** Split a label into lines that fit the node box. SVG text never wraps alone. */
export function wrapLabel(label: string, maxChars = 22): string[] {
  const words = label.split(/\s+/).filter(Boolean);
  const lines: string[] = [];
  let current = '';
  for (const word of words) {
    const candidate = current ? `${current} ${word}` : word;
    if (candidate.length > maxChars && current) {
      lines.push(current);
      current = word;
    } else {
      current = candidate;
    }
  }
  if (current) {
    lines.push(current);
  }
  return lines.length > 0 ? lines : [''];
}

/** Declarative node diagram rendered from a diagram asset's native spec. */
export const DiagramLayer: React.FC<DiagramLayerProps> = ({theme, width, height, nodes, connectors, reveal = 1}) => {
  const shownNodes = nodes.slice(0, Math.max(1, Math.round(nodes.length * Math.min(1, Math.max(0, reveal)))));
  const shownIds = new Set(shownNodes.map((node) => node.id));
  const byId = new Map(nodes.map((node) => [node.id, node]));
  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
      {connectors.map((connector, index) => {
        const from = byId.get(connector.from);
        const to = byId.get(connector.to);
        if (!from || !to || !shownIds.has(from.id) || !shownIds.has(to.id)) {
          return null;
        }
        return <line key={index} x1={from.x} y1={from.y} x2={to.x} y2={to.y} stroke={theme.accent} strokeWidth={theme.lineWeight} opacity={0.85} />;
      })}
      {shownNodes.map((node) => {
        const lines = wrapLabel(node.label);
        const boxHeight = 60 + lines.length * 44;
        return (
          <g key={node.id}>
            <rect
              x={node.x - 200}
              y={node.y - boxHeight / 2}
              width={400}
              height={boxHeight}
              rx={theme.cornerRadius}
              fill={theme.surface}
              stroke={theme.accent}
              strokeWidth={theme.lineWeight}
            />
            {lines.map((line, lineIndex) => (
              <text
                key={lineIndex}
                x={node.x}
                y={node.y - ((lines.length - 1) * 44) / 2 + lineIndex * 44 + 12}
                textAnchor="middle"
                fill={theme.text}
                fontSize={34}
                fontFamily={theme.fontFamily}
              >
                {line}
              </text>
            ))}
          </g>
        );
      })}
    </svg>
  );
};
