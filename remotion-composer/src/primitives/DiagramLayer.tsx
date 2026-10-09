import React from 'react';
import type {ThemeProps} from '../runtime/props';

export interface DiagramNode {
  id: string;
  label: string;
  x: number;
  y: number;
  /** Narration-grounded detail lines rendered as bullets inside the box. */
  details?: string[];
  /** Primary/focal node renders as the dark emphasis card. */
  primary?: boolean;
  /** Box size in canvas units; falls back to label-derived sizing. */
  w?: number;
  h?: number;
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
  /** 0..1 reveal driven by element-level assemble motion (never page motion). */
  reveal?: number;
}

const clamp01 = (v: number) => Math.min(1, Math.max(0, v));

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

/** Hard character clip for single-line detail bullets (SVG text never truncates). */
function clip(text: string, maxChars: number): string {
  return text.length <= maxChars ? text : `${text.slice(0, Math.max(1, maxChars - 1))}…`;
}

/**
 * Wrap one detail bullet to at most two lines. Narration phrases must stay
 * readable — a single hard clip ("Rags use a…") throws away the explanation.
 */
function wrapDetailBullet(detail: string, maxChars: number): string[] {
  const lines = wrapLabel(`• ${detail}`, maxChars);
  if (lines.length <= 2) {
    return lines;
  }
  return [lines[0], `${lines[1].slice(0, Math.max(1, maxChars - 1))}…`];
}

/**
 * Declarative node diagram rendered from a diagram asset's native spec.
 *
 * Element motion by construction: each node pops in as the reveal front
 * passes it and stays; connectors draw only once both endpoints exist; the
 * camera never moves. Boxes sit at the SAME coordinates the PNG midground
 * used (spec carries x/y/w/h from scene-graph bounds), so judge cluster
 * expectations hold.
 */
export const DiagramLayer: React.FC<DiagramLayerProps> = ({theme, width, height, nodes, connectors, reveal = 1}) => {
  const r = clamp01(reveal);
  const count = Math.max(1, nodes.length);

  // Node i starts appearing when the reveal front reaches i, over ~0.6 node units.
  const nodeT = (index: number) => clamp01((r * count - index) / 0.6);
  const tById = new Map<string, number>(nodes.map((node, index) => [node.id, nodeT(index)]));
  const byId = new Map<string, DiagramNode>(nodes.map((node) => [node.id, node]));

  // Exit point of a center-to-edge ray for an axis-aligned box.
  const boxExit = (node: DiagramNode, ux: number, uy: number): number => {
    const w = Math.max(240, node.w || 420);
    const h = Math.max(96, node.h || 160);
    const tx = Math.abs(ux) < 1e-4 ? Infinity : w / 2 / Math.abs(ux);
    const ty = Math.abs(uy) < 1e-4 ? Infinity : h / 2 / Math.abs(uy);
    return Math.min(tx, ty);
  };

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
      <defs>
        <marker
          id="diagArrowHead"
          viewBox="0 0 10 10"
          refX="9"
          refY="5"
          markerWidth="7"
          markerHeight="7"
          orient="auto-start-reverse"
        >
          <path d="M0,0 L10,5 L0,10 z" fill={theme.accent} />
        </marker>
        <filter id="diagNodeShadow" x="-20%" y="-20%" width="140%" height="150%">
          <feDropShadow dx="0" dy="10" stdDeviation="14" floodColor="#0F172A" floodOpacity="0.12" />
        </filter>
      </defs>

      {connectors.map((connector, index) => {
        const from = byId.get(connector.from);
        const to = byId.get(connector.to);
        if (!from || !to) {
          return null;
        }
        const t = Math.min(tById.get(from.id) ?? 0, tById.get(to.id) ?? 0);
        if (t <= 0.08) {
          return null;
        }
        const dx = to.x - from.x;
        const dy = to.y - from.y;
        const len = Math.hypot(dx, dy) || 1;
        const ux = dx / len;
        const uy = dy / len;
        const x1 = from.x + ux * boxExit(from, ux, uy) + ux * 6;
        const y1 = from.y + uy * boxExit(from, ux, uy) + uy * 6;
        const x2 = to.x - ux * (boxExit(to, ux, uy) + 10);
        const y2 = to.y - uy * (boxExit(to, ux, uy) + 10);
        const midX = (x1 + x2) / 2;
        const midY = (y1 + y2) / 2;
        return (
          <g key={`c${index}`} opacity={t}>
            <line
              x1={x1}
              y1={y1}
              x2={x2}
              y2={y2}
              stroke={theme.accent}
              strokeWidth={theme.lineWeight + 1}
              markerEnd="url(#diagArrowHead)"
            />
            {connector.label ? (
              <text
                x={midX}
                y={midY - 12}
                textAnchor="middle"
                fontSize={24}
                fontWeight={700}
                fill={theme.mutedText}
                fontFamily={theme.fontFamily}
              >
                {clip(connector.label, 24)}
              </text>
            ) : null}
          </g>
        );
      })}

      {nodes.map((node, index) => {
        const t = nodeT(index);
        if (t <= 0.02) {
          return null;
        }
        const w = Math.max(240, node.w || 420);
        const contentH = node.h || 0;
        const labelChars = Math.max(8, Math.floor((w - 44) / 19));
        const labelLines = wrapLabel(node.label, labelChars);
        const details = (node.details ?? []).filter(Boolean).slice(0, 3);
        const detailChars = Math.max(10, Math.floor((w - 76) / 13));
        const detailRows: {line: string; indent: number}[] = [];
        for (const detail of details) {
          const wrapped = wrapDetailBullet(detail, detailChars);
          wrapped.forEach((line, li) => detailRows.push({line, indent: li > 0 ? 30 : 0}));
        }
        const lineH = 40;
        const detailH = 30;
        const neededH = 30 + labelLines.length * lineH + (detailRows.length > 0 ? 12 + detailRows.length * detailH : 0) + 18;
        const h = Math.max(contentH, neededH, 96);
        const x = node.x - w / 2;
        const y = node.y - h / 2;
        const primary = Boolean(node.primary);
        const fill = primary ? '#0F172A' : theme.surface;
        const stroke = primary ? theme.accent : '#CBD5E1';
        const labelFill = primary ? '#FFFFFF' : theme.text;
        const detailFill = primary ? '#94A3B8' : theme.mutedText;
        const firstLineY = y + 34;
        const detailsStartY = firstLineY + labelLines.length * lineH + 6;
        return (
          <g
            key={node.id}
            opacity={t}
            transform={`translate(0, ${((1 - t) * 18).toFixed(2)})`}
            style={{filter: 'url(#diagNodeShadow)'}}
          >
            <rect
              x={x}
              y={y}
              width={w}
              height={h}
              rx={theme.cornerRadius}
              fill={fill}
              stroke={stroke}
              strokeWidth={primary ? 3 : theme.lineWeight}
            />
            {primary ? (
              <rect x={x + 14} y={y + 14} width={6} height={Math.max(12, h - 28)} rx={3} fill={theme.accentSecondary} />
            ) : null}
            {labelLines.map((line, li) => (
              <text
                key={`l${li}`}
                x={node.x}
                y={firstLineY + li * lineH}
                textAnchor="middle"
                fontSize={34}
                fontWeight={800}
                fill={labelFill}
                fontFamily={theme.fontFamily}
              >
                {line}
              </text>
            ))}
            {detailRows.map((row, ri) => (
              <text
                key={`d${ri}`}
                x={x + 26 + row.indent}
                y={detailsStartY + ri * detailH}
                fontSize={24}
                fontWeight={600}
                fill={detailFill}
                fontFamily={theme.fontFamily}
              >
                {row.line}
              </text>
            ))}
          </g>
        );
      })}
    </svg>
  );
};
