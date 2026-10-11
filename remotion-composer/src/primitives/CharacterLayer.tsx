import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {CharacterSpec, ThemeProps} from '../runtime/props';

export interface CharacterLayerProps {
  spec: CharacterSpec;
  progress: number;
  width: number;
  height: number;
  theme: ThemeProps;
}

export const CharacterLayer: React.FC<CharacterLayerProps> = ({
  spec,
  progress,
  width,
  height,
  theme,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Spring entrance
  const entrance = spring({
    frame,
    fps,
    config: {
      damping: 14,
      stiffness: 120,
      mass: 0.8,
    },
  });

  const posX = spec.position?.x ?? width * 0.5;
  const posY = spec.position?.y ?? height * 0.5;
  const scale = (spec.scale ?? 1.0) * entrance;

  // Determine glow color based on role
  const isEngineer = spec.role === 'engineer';
  const isAnalyst = spec.role === 'analyst';
  const visorColor = isEngineer ? '#D97706' : (isAnalyst ? '#10B981' : theme.accent); // Amber, Emerald, or Royal Blue

  // Tap-vector direction: where the pointing arm extends (no drawn line).
  const handSvgX = 206;
  const handSvgY = 121;
  let targetSvgX = 280;
  let targetSvgY = spec.pose?.includes('upward') ? 40 : 90;
  if (spec.target_anchor) {
    const handCanvasX = posX + (handSvgX - 110) * (scale || 1.0);
    const handCanvasY = posY + (handSvgY - 130) * (scale || 1.0);
    const dx = (spec.target_anchor.x - handCanvasX) / Math.max(0.1, scale || 1.0);
    const dy = (spec.target_anchor.y - handCanvasY) / Math.max(0.1, scale || 1.0);
    targetSvgX = handSvgX + dx;
    targetSvgY = handSvgY + dy;
  }

  // Tap-vector length: the pointing arm extends along its (rotated) axis.
  // The ARM itself rotates to face the real target — direction is computed
  // from the actual scene anchor, not a fixed horizontal pose (§6).
  const shoulderX = 180;
  const shoulderY = 132;
  const armAngle = spec.target_anchor
    ? Math.max(-170, Math.min(170, (Math.atan2(targetSvgY - shoulderY, targetSvgX - shoulderX) * 180) / Math.PI))
    : 0;
  // One deliberate tap gesture toward the semantic target (CTA). Single shot, then perfectly still.
  const tapExtend = spec.pose?.includes('tap')
    ? interpolate(progress, [0.12, 0.22, 0.32], [0, 18, 0], {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      })
    : 0;
  // interact: one deliberate point-and-hold toward the highlighted element —
  // distinct from inspect (lean) and stride (slide-in). Single shot, then still.
  const pointExtend =
    spec.motion === 'interact' && !spec.pose?.includes('tap')
      ? 16 * interpolate(progress, [0.1, 0.24], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})
      : 0;
  const extendAlong = tapExtend + pointExtend;

  // Per-scene action beats — all event-based, one-shot, never oscillating.
  // stride: the guide slides in from the left margin at scene start.
  const strideIn = spec.motion === 'stride' ? (1 - entrance) * -210 : 0;
  // inspect: one deliberate lean toward the highlighted content, then hold and settle.
  const leanDeg =
    spec.motion === 'inspect' && spec.target_anchor
      ? Math.sign(targetSvgX - handSvgX || 1) *
        interpolate(progress, [0.14, 0.26, 0.6, 0.72], [0, 5, 5, 0], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
        })
      : 0;
  // (No universal mid-scene bounce: the mascot is stable by default and acts
  // only through its scene-directed motion — stride, inspect, point, tap, hop.)
  // Celebration hop after the CTA button responds (single arc, then still).
  const hop =
    spec.emotion === 'celebrate'
      ? interpolate(progress, [0.5, 0.58, 0.68, 0.76], [0, -64, -8, 0], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
        })
      : 0;

  // The held tool renders INDEPENDENTLY of the arm pose: a target anchor
  // selects the pointing arm, never hides the scene-specific tool. Both
  // branches below call this helper — inspect-with-scanner points AND shows
  // the scanner instead of dropping it.
  // Resting hand anchors per tool (exact pre-existing geometry).
  const TOOL_ANCHORS: Record<string, [number, number]> = {
    vector_token: [186, 140],
    quantum_stylus: [184, 130],
    optical_scanner: [180, 132],
    telemetry_hud_panel: [178, 125],
    briefing_tablet: [182, 135],
  };
  const renderHeldTool = (x?: number, y?: number): React.ReactNode => {
    const anchor: [number, number] =
      x !== undefined && y !== undefined ? [x, y] : (TOOL_ANCHORS[spec.tool_held ?? ''] ?? [186, 140]);
    const [ax, ay] = anchor;
    return (
    <>
      {spec.tool_held === 'vector_token' && (
        <g transform={`translate(${ax}, ${ay})`}>
          <rect x="0" y="0" width="28" height="28" rx="6" fill="#1E40AF" stroke="#60A5FA" strokeWidth={2} />
          <path d="M6 14H22M14 6V22" stroke="#FFFFFF" strokeWidth={2} strokeLinecap="round" />
        </g>
      )}

      {spec.tool_held === 'quantum_stylus' && (
        <g transform={`translate(${ax}, ${ay})`}>
          <line x1="0" y1="0" x2="16" y2="28" stroke="#D97706" strokeWidth={4} strokeLinecap="round" />
          <circle cx="16" cy="28" r="4" fill="#F59E0B" />
        </g>
      )}

      {spec.tool_held === 'optical_scanner' && (
        <g transform={`translate(${ax}, ${ay})`}>
          <rect x="0" y="0" width="26" height="20" rx="4" fill="#0F172A" stroke="#38BDF8" strokeWidth={2} />
          <circle cx="13" cy="10" r="5" fill="#38BDF8" />
        </g>
      )}

      {spec.tool_held === 'telemetry_hud_panel' && (
        <g transform={`translate(${ax}, ${ay})`}>
          <rect x="0" y="0" width="36" height="30" rx="6" fill="rgba(15, 23, 42, 0.9)" stroke="#10B981" strokeWidth={2} />
          <line x1="6" y1="8" x2="30" y2="8" stroke="#10B981" strokeWidth={2} strokeLinecap="round" />
          <line x1="6" y1="16" x2="24" y2="16" stroke="#34D399" strokeWidth={1.5} strokeLinecap="round" />
          <line x1="6" y1="22" x2="28" y2="22" stroke="#34D399" strokeWidth={1.5} strokeLinecap="round" />
        </g>
      )}

      {spec.tool_held === 'briefing_tablet' && (
        <g transform={`translate(${ax}, ${ay})`}>
          <rect x="0" y="0" width="34" height="42" rx="4" fill="#0F172A" stroke="#38BDF8" strokeWidth={2} />
          <line x1="6" y1="10" x2="28" y2="10" stroke="#38BDF8" strokeWidth={2} strokeLinecap="round" />
          <line x1="6" y1="18" x2="22" y2="18" stroke="#94A3B8" strokeWidth={2} strokeLinecap="round" />
          <line x1="6" y1="26" x2="26" y2="26" stroke="#94A3B8" strokeWidth={2} strokeLinecap="round" />
        </g>
      )}
    </>
    );
  };

  return (
    <div
      style={{
        position: 'absolute',
        left: posX,
        top: posY,
        transform: `translate(-50%, -50%) translateX(${strideIn.toFixed(1)}px) translateY(${hop.toFixed(1)}px) rotate(${leanDeg.toFixed(2)}deg) scale(${scale.toFixed(4)})`,
        transformOrigin: '50% 50%',
        pointerEvents: 'none',
        zIndex: spec.z_index ?? 15,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
      }}
    >
      {/* Bot SVG Body */}
      <svg
        width="220"
        height="260"
        viewBox="0 0 220 260"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        style={{
          overflow: 'visible',
          filter: `drop-shadow(0 20px 30px rgba(30, 64, 175, 0.25))`,
        }}
      >
        {/* Anti-Gravity Thruster Glow (Stable, zero oscillation) */}
        <ellipse
          cx="110"
          cy="235"
          rx="28"
          ry="8"
          fill={visorColor}
          opacity="0.6"
        />

        {/* Floating Shadow */}
        <ellipse
          cx="110"
          cy="252"
          rx="45"
          ry="10"
          fill="rgba(15, 23, 42, 0.12)"
        />

        {/* Head Shell */}
        <rect
          x="45"
          y="40"
          width="130"
          height="100"
          rx="42"
          fill="#FFFFFF"
          stroke="#E2E8F0"
          strokeWidth="4"
        />

        {/* Glossy Head Highlight */}
        <path
          d="M65 52C75 46 95 44 110 44C125 44 145 46 155 52"
          stroke="#F8FAFC"
          strokeWidth="4"
          strokeLinecap="round"
        />

        {/* Visor Screen */}
        <rect
          x="62"
          y="62"
          width="96"
          height="54"
          rx="24"
          fill="#0F172A"
        />

        {/* Glowing Visor Eye / Expression (Stable gaze, zero jitter) */}
        <g>
          <rect
            x="76"
            y="78"
            width="24"
            height="18"
            rx="8"
            fill={visorColor}
          />
          <rect
            x="120"
            y="78"
            width="24"
            height="18"
            rx="8"
            fill={visorColor}
          />
          {/* Eye specular glint */}
          <circle cx="82" cy="83" r="3" fill="#FFFFFF" opacity="0.9" />
          <circle cx="126" cy="83" r="3" fill="#FFFFFF" opacity="0.9" />
        </g>

        {/* Bot Antennas */}
        <path
          d="M110 40V24"
          stroke="#CBD5E1"
          strokeWidth="4"
          strokeLinecap="round"
        />
        <circle
          cx="110"
          cy="20"
          r="6"
          fill={visorColor}
        />

        {/* Torso Shell */}
        <path
          d="M65 145C65 145 75 195 110 195C145 195 155 145 155 145H65Z"
          fill="#FFFFFF"
          stroke="#E2E8F0"
          strokeWidth="4"
        />

        {/* Chest Lab Insignia Badge */}
        <rect
          x="94"
          y="156"
          width="32"
          height="20"
          rx="6"
          fill="#F1F5F9"
          stroke={visorColor}
          strokeWidth="2"
        />
        <circle cx="110" cy="166" r="4" fill={visorColor} />

        {/* Left Arm / Hand (Stable pose, zero arm wiggle) */}
        <g>
          <rect
            x="24"
            y="125"
            width="24"
            height="46"
            rx="12"
            fill="#FFFFFF"
            stroke="#CBD5E1"
            strokeWidth="3"
          />
          <circle cx="36" cy="162" r="5" fill={visorColor} opacity="0.8" />
        </g>

        {/* Right Arm — deliberate pointing gesture toward a real semantic target (event-based, never oscillating).
            No targeting line or crosshair: the mascot is PLACED by scene focus instead (§26).
            When no target anchor exists the arm rests in a stable pose holding its tool. */}
        {spec.target_anchor || spec.pose?.includes('point') || spec.action?.includes('point') ? (
          <g transform={`rotate(${armAngle.toFixed(2)} ${shoulderX} ${shoulderY})`}>
            <g transform={`translate(${extendAlong.toFixed(1)}, 0)`}>
              <rect
                x="172"
                y="110"
                width="34"
                height="22"
                rx="10"
                fill="#FFFFFF"
                stroke="#CBD5E1"
                strokeWidth="3"
              />
              <circle cx="206" cy="121" r="5" fill={visorColor} />
              {renderHeldTool(188, 96)}
            </g>
          </g>
        ) : (
          <g>
            <rect
              x="172"
              y="120"
              width="24"
              height="46"
              rx="12"
              fill="#FFFFFF"
              stroke="#CBD5E1"
              strokeWidth="3"
            />
            <circle cx="184" cy="157" r="5" fill={visorColor} opacity="0.8" />

            {renderHeldTool()}
          </g>
        )}
      </svg>
      {/* Mascot behavior is communicated by the character itself — never by a caption chip. */}
    </div>
  );
};
