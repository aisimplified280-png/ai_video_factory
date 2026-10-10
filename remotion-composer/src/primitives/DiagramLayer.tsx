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
  /** Semantic node type from the scene graph (entity/process/storage/transform/...). */
  node_type?: string;
  /** Semantic shape style (cylindrical_storage/transform_kernel/stack_layer/matrix_grid/card). */
  shape_style?: string;
  /** Concrete subject primitive glyph id ("satellite", "phone", "document"...). */
  icon?: string;
}

export interface DiagramConnector {
  from: string;
  to: string;
  label?: string;
  /** Semantic relationship (flows_to/transforms_to/contrasts_with/indexes/routes_down...). */
  relationship?: string;
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
 * Concrete subject primitives — the object the narration NAMES, drawn as a
 * simple vector glyph (§3). The scene graph assigns icon ids via its
 * deterministic lexicon; this renders them. Every glyph is a recognizable
 * schematic of the real object, not a decorative dot.
 */
export const DIAGRAM_GLYPH_IDS = [
  'satellite', 'phone', 'document', 'database', 'server', 'cpu', 'cache',
  'memory', 'embedding', 'token', 'query', 'client', 'api', 'gear', 'arm',
  'workpiece', 'sensor', 'network', 'layers', 'model',
] as const;

const DiagramGlyph: React.FC<{icon: string; x: number; y: number; size: number; accent: string}> = ({
  icon,
  x,
  y,
  size,
  accent,
}) => {
  const s = size;
  const stroke = '#0F172A';
  const common = {stroke, strokeWidth: 2.4, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const};
  let body: React.ReactNode = null;
  switch (icon) {
    case 'satellite': {
      // Body + two solar panels + signal arcs.
      body = (
        <g {...common} fill="none">
          <rect x={x + s * 0.38} y={y + s * 0.3} width={s * 0.24} height={s * 0.4} rx={s * 0.05} fill={accent} />
          <rect x={x + s * 0.06} y={y + s * 0.38} width={s * 0.26} height={s * 0.24} rx={s * 0.03} fill="#DBEAFE" />
          <rect x={x + s * 0.68} y={y + s * 0.38} width={s * 0.26} height={s * 0.24} rx={s * 0.03} fill="#DBEAFE" />
          <path d={`M${x + s * 0.5} ${y + s * 0.24} q ${s * 0.18} ${-s * 0.14} ${s * 0.34} 0`} />
          <path d={`M${x + s * 0.5} ${y + s * 0.12} q ${s * 0.26} ${-s * 0.2} ${s * 0.48} 0`} />
        </g>
      );
      break;
    }
    case 'phone': {
      // Handset slab + screen line + home dot.
      body = (
        <g {...common} fill="none">
          <rect x={x + s * 0.3} y={y + s * 0.08} width={s * 0.4} height={s * 0.84} rx={s * 0.1} fill="#FFFFFF" />
          <rect x={x + s * 0.37} y={y + s * 0.22} width={s * 0.26} height={s * 0.4} rx={s * 0.03} fill={accent} stroke="none" />
          <circle cx={x + s * 0.5} cy={y + s * 0.76} r={s * 0.05} />
        </g>
      );
      break;
    }
    case 'document': {
      // Page + text lines + folded corner.
      body = (
        <g {...common} fill="none">
          <path d={`M${x + s * 0.24} ${y + s * 0.08} h ${s * 0.34} l ${s * 0.18} ${s * 0.18} v ${s * 0.66} h ${-s * 0.52} z`} fill="#FFFFFF" />
          <path d={`M${x + s * 0.58} ${y + s * 0.08} v ${s * 0.18} h ${s * 0.18}`} />
          <line x1={x + s * 0.32} y1={y + s * 0.44} x2={x + s * 0.68} y2={y + s * 0.44} />
          <line x1={x + s * 0.32} y1={y + s * 0.58} x2={x + s * 0.68} y2={y + s * 0.58} />
          <line x1={x + s * 0.32} y1={y + s * 0.72} x2={x + s * 0.56} y2={y + s * 0.72} />
        </g>
      );
      break;
    }
    case 'database': {
      // Cylinder: storage.
      body = (
        <g {...common} fill="none">
          <path d={`M${x + s * 0.2} ${y + s * 0.22} v ${s * 0.56} a ${s * 0.3} ${s * 0.14} 0 0 0 ${s * 0.6} 0 v ${-s * 0.56}`} fill="#FFFFFF" />
          <ellipse cx={x + s * 0.5} cy={y + s * 0.22} rx={s * 0.3} ry={s * 0.14} fill={accent} />
          <path d={`M${x + s * 0.2} ${y + s * 0.5} a ${s * 0.3} ${s * 0.14} 0 0 0 ${s * 0.6} 0`} />
        </g>
      );
      break;
    }
    case 'server': {
      // Stacked rack units + status dots.
      body = (
        <g {...common} fill="none">
          <rect x={x + s * 0.16} y={y + s * 0.16} width={s * 0.68} height={s * 0.28} rx={s * 0.05} fill="#FFFFFF" />
          <rect x={x + s * 0.16} y={y + s * 0.56} width={s * 0.68} height={s * 0.28} rx={s * 0.05} fill="#FFFFFF" />
          <circle cx={x + s * 0.7} cy={y + s * 0.3} r={s * 0.045} fill={accent} stroke="none" />
          <circle cx={x + s * 0.7} cy={y + s * 0.7} r={s * 0.045} fill={accent} stroke="none" />
          <line x1={x + s * 0.26} y1={y + s * 0.3} x2={x + s * 0.54} y2={y + s * 0.3} />
          <line x1={x + s * 0.26} y1={y + s * 0.7} x2={x + s * 0.54} y2={y + s * 0.7} />
        </g>
      );
      break;
    }
    case 'cpu': {
      // Chip: core square + pins.
      body = (
        <g {...common} fill="none">
          <rect x={x + s * 0.24} y={y + s * 0.24} width={s * 0.52} height={s * 0.52} rx={s * 0.06} fill="#FFFFFF" />
          <rect x={x + s * 0.38} y={y + s * 0.38} width={s * 0.24} height={s * 0.24} rx={s * 0.03} fill={accent} stroke="none" />
          {[0.34, 0.5, 0.66].map((f) => (
            <React.Fragment key={f}>
              <line x1={x + s * f} y1={y + s * 0.12} x2={x + s * f} y2={y + s * 0.24} />
              <line x1={x + s * f} y1={y + s * 0.76} x2={x + s * f} y2={y + s * 0.88} />
              <line x1={x + s * 0.12} y1={y + s * f} x2={x + s * 0.24} y2={y + s * f} />
              <line x1={x + s * 0.76} y1={y + s * f} x2={x + s * 0.88} y2={y + s * f} />
            </React.Fragment>
          ))}
        </g>
      );
      break;
    }
    case 'cache': {
      // Fast tier: small blocks above a wide block.
      body = (
        <g {...common} fill="none">
          <rect x={x + s * 0.18} y={y + s * 0.14} width={s * 0.28} height={s * 0.24} rx={s * 0.04} fill={accent} stroke="none" />
          <rect x={x + s * 0.54} y={y + s * 0.14} width={s * 0.28} height={s * 0.24} rx={s * 0.04} fill={accent} stroke="none" />
          <rect x={x + s * 0.12} y={y + s * 0.52} width={s * 0.76} height={s * 0.32} rx={s * 0.05} fill="#FFFFFF" />
        </g>
      );
      break;
    }
    case 'memory': {
      // RAM stick: board + chips.
      body = (
        <g {...common} fill="none">
          <rect x={x + s * 0.1} y={y + s * 0.3} width={s * 0.8} height={s * 0.4} rx={s * 0.04} fill="#FFFFFF" />
          {[0.2, 0.42, 0.64].map((f) => (
            <rect key={f} x={x + s * f} y={y + s * 0.38} width={s * 0.14} height={s * 0.24} rx={s * 0.02} fill={accent} stroke="none" />
          ))}
          <line x1={x + s * 0.3} y1={y + s * 0.7} x2={x + s * 0.7} y2={y + s * 0.7} />
        </g>
      );
      break;
    }
    case 'embedding': {
      // Vector space: axes + point cloud.
      body = (
        <g {...common} fill="none">
          <line x1={x + s * 0.16} y1={y + s * 0.84} x2={x + s * 0.84} y2={y + s * 0.84} />
          <line x1={x + s * 0.16} y1={y + s * 0.84} x2={x + s * 0.16} y2={y + s * 0.14} />
          <circle cx={x + s * 0.38} cy={y + s * 0.62} r={s * 0.055} fill={accent} stroke="none" />
          <circle cx={x + s * 0.58} cy={y + s * 0.4} r={s * 0.055} fill={accent} stroke="none" />
          <circle cx={x + s * 0.72} cy={y + s * 0.58} r={s * 0.055} fill={accent} stroke="none" />
          <circle cx={x + s * 0.5} cy={y + s * 0.7} r={s * 0.055} fill={accent} stroke="none" />
        </g>
      );
      break;
    }
    case 'token': {
      // Key coin: circle + notch.
      body = (
        <g {...common} fill="none">
          <circle cx={x + s * 0.5} cy={y + s * 0.5} r={s * 0.32} fill="#FFFFFF" />
          <circle cx={x + s * 0.5} cy={y + s * 0.5} r={s * 0.12} fill={accent} stroke="none" />
          <line x1={x + s * 0.5} y1={y + s * 0.18} x2={x + s * 0.5} y2={y + s * 0.3} />
        </g>
      );
      break;
    }
    case 'query': {
      // Magnifier over a line.
      body = (
        <g {...common} fill="none">
          <circle cx={x + s * 0.42} cy={y + s * 0.4} r={s * 0.26} fill="#FFFFFF" />
          <line x1={x + s * 0.61} y1={y + s * 0.59} x2={x + s * 0.84} y2={y + s * 0.82} strokeWidth={3.6} />
          <line x1={x + s * 0.3} y1={y + s * 0.4} x2={x + s * 0.54} y2={y + s * 0.4} stroke={accent} />
        </g>
      );
      break;
    }
    case 'client': {
      // Browser window.
      body = (
        <g {...common} fill="none">
          <rect x={x + s * 0.12} y={y + s * 0.18} width={s * 0.76} height={s * 0.62} rx={s * 0.06} fill="#FFFFFF" />
          <line x1={x + s * 0.12} y1={y + s * 0.34} x2={x + s * 0.88} y2={y + s * 0.34} />
          <circle cx={x + s * 0.22} cy={y + s * 0.26} r={s * 0.028} fill={accent} stroke="none" />
          <circle cx={x + s * 0.32} cy={y + s * 0.26} r={s * 0.028} fill={accent} stroke="none" />
          <line x1={x + s * 0.24} y1={y + s * 0.5} x2={x + s * 0.64} y2={y + s * 0.5} />
          <line x1={x + s * 0.24} y1={y + s * 0.64} x2={x + s * 0.52} y2={y + s * 0.64} />
        </g>
      );
      break;
    }
    case 'api': {
      // Braces: interface contract.
      body = (
        <g {...common} fill="none">
          <path d={`M${x + s * 0.38} ${y + s * 0.2} q ${-s * 0.16} 0 ${-s * 0.16} ${s * 0.16} q 0 ${s * 0.1} ${-s * 0.14} ${s * 0.14} q ${s * 0.14} ${s * 0.04} ${s * 0.14} ${s * 0.14} q 0 ${s * 0.16} ${s * 0.16} ${s * 0.16}`} />
          <path d={`M${x + s * 0.62} ${y + s * 0.2} q ${s * 0.16} 0 ${s * 0.16} ${s * 0.16} q 0 ${s * 0.1} ${s * 0.14} ${s * 0.14} q ${-s * 0.14} ${s * 0.04} ${-s * 0.14} ${s * 0.14} q 0 ${s * 0.16} ${-s * 0.16} ${s * 0.16}`} />
          <circle cx={x + s * 0.5} cy={y + s * 0.5} r={s * 0.05} fill={accent} stroke="none" />
        </g>
      );
      break;
    }
    case 'gear': {
      // Transformation gear.
      body = (
        <g {...common} fill="none">
          <circle cx={x + s * 0.5} cy={y + s * 0.5} r={s * 0.2} fill={accent} stroke="none" />
          <circle cx={x + s * 0.5} cy={y + s * 0.5} r={s * 0.09} fill="#FFFFFF" stroke="none" />
          {[0, 45, 90, 135, 180, 225, 270, 315].map((deg) => {
            const rad = (deg * Math.PI) / 180;
            const r1 = s * 0.26;
            const r2 = s * 0.38;
            return (
              <line
                key={deg}
                x1={x + s * 0.5 + Math.cos(rad) * r1}
                y1={y + s * 0.5 + Math.sin(rad) * r1}
                x2={x + s * 0.5 + Math.cos(rad) * r2}
                y2={y + s * 0.5 + Math.sin(rad) * r2}
                strokeWidth={4.5}
              />
            );
          })}
        </g>
      );
      break;
    }
    case 'arm': {
      // Robotic arm: base + two segments + gripper.
      body = (
        <g {...common} fill="none">
          <rect x={x + s * 0.2} y={y + s * 0.74} width={s * 0.3} height={s * 0.14} rx={s * 0.03} fill="#FFFFFF" />
          <line x1={x + s * 0.35} y1={y + s * 0.74} x2={x + s * 0.58} y2={y + s * 0.38} strokeWidth={4.5} />
          <line x1={x + s * 0.58} y1={y + s * 0.38} x2={x + s * 0.82} y2={y + s * 0.5} strokeWidth={4.5} />
          <path d={`M${x + s * 0.82} ${y + s * 0.44} v ${s * 0.12} M${x + s * 0.82} ${y + s * 0.5} l ${s * 0.1} ${-s * 0.06}`} />
          <circle cx={x + s * 0.58} cy={y + s * 0.38} r={s * 0.05} fill={accent} stroke="none" />
        </g>
      );
      break;
    }
    case 'workpiece': {
      // Cube being acted on.
      body = (
        <g {...common} fill="none">
          <rect x={x + s * 0.24} y={y + s * 0.3} width={s * 0.52} height={s * 0.48} rx={s * 0.05} fill="#FFFFFF" />
          <line x1={x + s * 0.24} y1={y + s * 0.46} x2={x + s * 0.76} y2={y + s * 0.46} strokeDasharray="6 5" />
        </g>
      );
      break;
    }
    case 'sensor': {
      // Eye/dish.
      body = (
        <g {...common} fill="none">
          <path d={`M${x + s * 0.14} ${y + s * 0.5} q ${s * 0.36} ${-s * 0.42} ${s * 0.72} 0 q ${-s * 0.36} ${s * 0.42} ${-s * 0.72} 0 z`} fill="#FFFFFF" />
          <circle cx={x + s * 0.5} cy={y + s * 0.5} r={s * 0.11} fill={accent} stroke="none" />
        </g>
      );
      break;
    }
    case 'network': {
      // Three linked nodes.
      body = (
        <g {...common} fill="none">
          <line x1={x + s * 0.5} y1={y + s * 0.24} x2={x + s * 0.24} y2={y + s * 0.68} />
          <line x1={x + s * 0.5} y1={y + s * 0.24} x2={x + s * 0.76} y2={y + s * 0.68} />
          <line x1={x + s * 0.24} y1={y + s * 0.68} x2={x + s * 0.76} y2={y + s * 0.68} />
          <circle cx={x + s * 0.5} cy={y + s * 0.2} r={s * 0.1} fill={accent} stroke="none" />
          <circle cx={x + s * 0.2} cy={y + s * 0.72} r={s * 0.1} fill="#FFFFFF" />
          <circle cx={x + s * 0.8} cy={y + s * 0.72} r={s * 0.1} fill="#FFFFFF" />
        </g>
      );
      break;
    }
    case 'layers': {
      // Stacked plates.
      body = (
        <g {...common} fill="none">
          <path d={`M${x + s * 0.5} ${y + s * 0.14} l ${s * 0.36} ${s * 0.16} l ${-s * 0.36} ${s * 0.16} l ${-s * 0.36} ${-s * 0.16} z`} fill={accent} stroke="none" />
          <path d={`M${x + s * 0.14} ${y + s * 0.5} l ${s * 0.36} ${s * 0.16} l ${s * 0.36} ${-s * 0.16}`} />
          <path d={`M${x + s * 0.14} ${y + s * 0.68} l ${s * 0.36} ${s * 0.16} l ${s * 0.36} ${-s * 0.16}`} />
        </g>
      );
      break;
    }
    case 'model': {
      // Neural net: layered dots.
      body = (
        <g {...common} fill="none">
          {[0.22, 0.5, 0.78].map((cx, ci) =>
            (ci === 1 ? [0.3, 0.5, 0.7] : [0.38, 0.62]).map((cy) => (
              <circle
                key={`${cx}-${cy}`}
                cx={x + s * cx}
                cy={y + s * cy}
                r={s * 0.06}
                fill={ci === 1 ? accent : '#FFFFFF'}
                stroke="none"
              />
            ))
          )}
          <line x1={x + s * 0.26} y1={y + s * 0.38} x2={x + s * 0.46} y2={y + s * 0.3} />
          <line x1={x + s * 0.26} y1={y + s * 0.38} x2={x + s * 0.46} y2={y + s * 0.5} />
          <line x1={x + s * 0.54} y1={y + s * 0.3} x2={x + s * 0.74} y2={y + s * 0.38} />
          <line x1={x + s * 0.54} y1={y + s * 0.5} x2={x + s * 0.74} y2={y + s * 0.62} />
        </g>
      );
      break;
    }
    default:
      return null;
  }
  return <g>{body}</g>;
};

/** Connector style follows the SEMANTIC relationship — a comparison is two-sided,
 * a transformation is marked, a callout is dashed; only data flow gets one arrow. */
function connectorStyle(relationship: string | undefined): {
  markerStart?: string;
  markerEnd?: string;
  dash?: string;
  transformMark?: boolean;
} {
  switch ((relationship ?? '').toLowerCase()) {
    case 'contrasts_with':
      return {markerStart: 'url(#diagArrowHead)', markerEnd: 'url(#diagArrowHead)'};
    case 'transforms_to':
      return {markerEnd: 'url(#diagArrowHead)', transformMark: true};
    case 'callout':
      return {dash: '10 8'};
    default:
      return {markerEnd: 'url(#diagArrowHead)'};
  }
}

/**
 * Declarative node diagram rendered from a diagram asset's native spec.
 *
 * The SEMANTIC distinctions survive to pixels: storage renders as a cylinder,
 * a transformation as a hexagon kernel, a hierarchy as stacked plates, a
 * comparison as a two-sided contrast connector, and concrete subjects draw
 * their real object glyph. Element motion by construction: each node pops in
 * as the reveal front passes it and stays; connectors draw only once both
 * endpoints exist; the camera never moves.
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

  /** Semantic shape outline for a node (hexagon kernel, cylinder, plate...). */
  const shapeElement = (
    node: DiagramNode,
    x: number,
    y: number,
    w: number,
    h: number,
    fill: string,
    stroke: string,
    primary: boolean,
  ): React.ReactNode => {
    const style = (node.shape_style ?? '').toLowerCase();
    const type = (node.node_type ?? '').toLowerCase();
    const sw = primary ? 3 : theme.lineWeight;
    if (style === 'transform_kernel' || type === 'transform') {
      const cut = Math.min(30, w * 0.12);
      return (
        <polygon
          points={`${x + cut},${y} ${x + w - cut},${y} ${x + w},${y + h / 2} ${x + w - cut},${y + h} ${x + cut},${y + h} ${x},${y + h / 2}`}
          fill={fill}
          stroke={stroke}
          strokeWidth={sw}
        />
      );
    }
    if (style === 'cylindrical_storage' || type === 'storage') {
      const ry = Math.min(16, h * 0.14);
      return (
        <g>
          <path
            d={`M${x} ${y + ry} v ${h - 2 * ry} a ${w / 2} ${ry} 0 0 0 ${w} 0 v ${-(h - 2 * ry)}`}
            fill={fill}
            stroke={stroke}
            strokeWidth={sw}
          />
          <ellipse cx={x + w / 2} cy={y + ry} rx={w / 2} ry={ry} fill={fill} stroke={stroke} strokeWidth={sw} />
        </g>
      );
    }
    if (style === 'stack_layer' || type === 'layer') {
      return (
        <g>
          <rect x={x} y={y} width={w} height={h} rx={theme.cornerRadius} fill={fill} stroke={stroke} strokeWidth={sw} />
          <line x1={x + 18} y1={y + 16} x2={x + w - 18} y2={y + 16} stroke={theme.accentSecondary} strokeWidth={3} opacity={0.8} />
          <line x1={x + 18} y1={y + 24} x2={x + w - 18} y2={y + 24} stroke={theme.accentSecondary} strokeWidth={2} opacity={0.45} />
        </g>
      );
    }
    if (style === 'matrix_grid') {
      const rows = 2;
      const cols = 4;
      return (
        <g>
          <rect x={x} y={y} width={w} height={h} rx={theme.cornerRadius} fill={fill} stroke={stroke} strokeWidth={sw} />
          {Array.from({length: rows * cols}).map((_, gi) => {
            const gr = Math.floor(gi / cols);
            const gc = gi % cols;
            return (
              <rect
                key={gi}
                x={x + 20 + gc * ((w - 40) / cols)}
                y={y + h - 52 + gr * 18}
                width={(w - 40) / cols - 10}
                height={10}
                rx={3}
                fill={theme.accent}
                opacity={0.35}
              />
            );
          })}
        </g>
      );
    }
    if (type === 'process') {
      // Process step: arrow-block silhouette (distinct from a generic card).
      const notch = Math.min(26, w * 0.1);
      return (
        <polygon
          points={`${x},${y} ${x + w - notch},${y} ${x + w},${y + h / 2} ${x + w - notch},${y + h} ${x},${y + h}`}
          fill={fill}
          stroke={stroke}
          strokeWidth={sw}
        />
      );
    }
    return <rect x={x} y={y} width={w} height={h} rx={theme.cornerRadius} fill={fill} stroke={stroke} strokeWidth={sw} />;
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
        const style = connectorStyle(connector.relationship);
        return (
          <g key={`c${index}`} opacity={t}>
            <line
              x1={x1}
              y1={y1}
              x2={x2}
              y2={y2}
              stroke={theme.accent}
              strokeWidth={theme.lineWeight + 1}
              strokeDasharray={style.dash}
              markerStart={style.markerStart}
              markerEnd={style.markerEnd}
            />
            {style.transformMark ? (
              <rect
                x={midX - 9}
                y={midY - 9}
                width={18}
                height={18}
                transform={`rotate(45 ${midX} ${midY})`}
                fill={theme.accentSecondary}
                stroke="#FFFFFF"
                strokeWidth={2}
              />
            ) : null}
            {connector.label ? (
              <text
                x={midX}
                y={midY - 16}
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
        const hasIcon = Boolean(node.icon);
        const labelChars = Math.max(8, Math.floor((w - (hasIcon ? 150 : 44)) / 19));
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
        const labelX = hasIcon ? x + 128 : node.x;
        const labelAnchor = hasIcon ? 'start' : 'middle';
        return (
          <g
            key={node.id}
            opacity={t}
            transform={`translate(0, ${((1 - t) * 18).toFixed(2)})`}
            style={{filter: 'url(#diagNodeShadow)'}}
          >
            {shapeElement(node, x, y, w, h, fill, stroke, primary)}
            {primary && node.shape_style !== 'cylindrical_storage' && node.node_type !== 'storage' ? (
              <rect x={x + 14} y={y + 14} width={6} height={Math.max(12, h - 28)} rx={3} fill={theme.accentSecondary} />
            ) : null}
            {hasIcon ? (
              <DiagramGlyph icon={node.icon as string} x={x + 34} y={y + h / 2 - 34} size={68} accent={primary ? '#FFFFFF' : theme.accent} />
            ) : null}
            {labelLines.map((line, li) => (
              <text
                key={`l${li}`}
                x={labelX}
                y={firstLineY + li * lineH}
                textAnchor={labelAnchor}
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
                x={x + 26 + row.indent + (hasIcon ? 92 : 0)}
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
