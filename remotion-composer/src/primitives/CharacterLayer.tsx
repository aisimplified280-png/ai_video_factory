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

  // Floating anti-gravity bounce
  const floatOffset = Math.sin(frame / 12) * 14;
  const floatTilt = Math.sin(frame / 18) * 3; // subtle 3 degree tilt

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
  const posY = (spec.position?.y ?? height * 0.5) + floatOffset;
  const scale = (spec.scale ?? 1.0) * entrance;

  // Determine glow color based on role
  const isEngineer = spec.role === 'engineer';
  const isAnalyst = spec.role === 'analyst';
  const visorColor = isEngineer ? '#D97706' : (isAnalyst ? '#10B981' : theme.accent); // Amber, Emerald, or Royal Blue

  return (
    <div
      style={{
        position: 'absolute',
        left: posX,
        top: posY,
        transform: `translate(-50%, -50%) scale(${scale}) rotate(${floatTilt}deg)`,
        transformOrigin: '50% 50%',
        pointerEvents: 'none',
        zIndex: 15,
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
          filter: `drop-shadow(0 20px 30px rgba(30, 64, 175, 0.25))`,
        }}
      >
        {/* Anti-Gravity Thruster Glow */}
        <ellipse
          cx="110"
          cy="235"
          rx={28 + Math.sin(frame / 6) * 6}
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

        {/* Dynamic Glowing Visor Eye / Expression */}
        <g style={{transform: `translateX(${Math.sin(frame / 20) * 4}px)`}}>
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

        {/* Left Floating Arm / Hand */}
        <g style={{transform: `translate(${Math.sin(frame / 10) * 3}px, ${Math.cos(frame / 10) * 4}px)`}}>
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

        {/* Right Floating Arm (Dynamic Pointing or Tool Manipulation) */}
        {spec.pose?.includes('point') || spec.action?.includes('point') ? (
          <g>
            <g style={{transform: `translate(${-Math.sin(frame / 12) * 2}px, ${Math.cos(frame / 12) * 2}px)`}}>
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
            </g>
            <line
              x1="210"
              y1="121"
              x2="280"
              y2={spec.pose?.includes('upward') ? 40 : 90}
              stroke={visorColor}
              strokeWidth={2.5}
              strokeDasharray="4 4"
              opacity={0.7 + Math.sin(frame / 4) * 0.3}
            />
            <circle
              cx="280"
              cy={spec.pose?.includes('upward') ? 40 : 90}
              r={6 + Math.sin(frame / 6) * 2}
              fill="none"
              stroke={visorColor}
              strokeWidth={2}
              opacity={0.8}
            />
          </g>
        ) : (
          <g style={{transform: `translate(${-Math.sin(frame / 10) * 3}px, ${-Math.cos(frame / 10) * 4}px)`}}>
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

            {spec.tool_held === 'vector_token' && (
              <g transform="translate(186, 140)">
                <rect x="0" y="0" width="28" height="28" rx="6" fill="#1E40AF" stroke="#60A5FA" strokeWidth={2} />
                <path d="M6 14H22M14 6V22" stroke="#FFFFFF" strokeWidth={2} strokeLinecap="round" />
              </g>
            )}

            {spec.tool_held === 'quantum_stylus' && (
              <g transform="translate(184, 130)">
                <line x1="0" y1="0" x2="16" y2="28" stroke="#D97706" strokeWidth={4} strokeLinecap="round" />
                <circle cx="16" cy="28" r="4" fill="#F59E0B" />
              </g>
            )}

            {spec.tool_held === 'optical_scanner' && (
              <g transform="translate(180, 132)">
                <rect x="0" y="0" width="26" height="20" rx="4" fill="#0F172A" stroke="#38BDF8" strokeWidth={2} />
                <circle cx="13" cy="10" r="5" fill="#38BDF8" />
              </g>
            )}

            {spec.tool_held === 'telemetry_hud_panel' && (
              <g transform="translate(178, 125)">
                <rect x="0" y="0" width="36" height="30" rx="6" fill="rgba(15, 23, 42, 0.9)" stroke="#10B981" strokeWidth={2} />
                <line x1="6" y1="8" x2="30" y2="8" stroke="#10B981" strokeWidth={2} strokeLinecap="round" />
                <line x1="6" y1="16" x2="24" y2="16" stroke="#34D399" strokeWidth={1.5} strokeLinecap="round" />
                <line x1="6" y1="22" x2="28" y2="22" stroke="#34D399" strokeWidth={1.5} strokeLinecap="round" />
              </g>
            )}

            {spec.tool_held === 'briefing_tablet' && (
              <g transform="translate(182, 135)">
                <rect x="0" y="0" width="34" height="42" rx="4" fill="#0F172A" stroke="#38BDF8" strokeWidth={2} />
                <line x1="6" y1="10" x2="28" y2="10" stroke="#38BDF8" strokeWidth={2} strokeLinecap="round" />
                <line x1="6" y1="18" x2="22" y2="18" stroke="#94A3B8" strokeWidth={2} strokeLinecap="round" />
                <line x1="6" y1="26" x2="26" y2="26" stroke="#94A3B8" strokeWidth={2} strokeLinecap="round" />
              </g>
            )}
          </g>
        )}
      </svg>

      {/* Kinetic Action Callout Chip */}
      <div
        style={{
          marginTop: -10,
          background: 'rgba(255, 255, 255, 0.92)',
          backdropFilter: 'blur(12px)',
          border: `1.5px solid ${visorColor}`,
          borderRadius: 20,
          padding: '6px 16px',
          boxShadow: '0 8px 24px rgba(15, 23, 42, 0.08)',
          display: 'flex',
          alignItems: 'center',
          gap: 8,
        }}
      >
        <span
          style={{
            width: 8,
            height: 8,
            borderRadius: '50%',
            background: visorColor,
            boxShadow: `0 0 8px ${visorColor}`,
          }}
        />
        <span
          style={{
            fontFamily: theme.fontFamily,
            fontSize: 14,
            fontWeight: 700,
            letterSpacing: '0.08em',
            textTransform: 'uppercase',
            color: '#0F172A',
          }}
        >
          {spec.action}
        </span>
      </div>
    </div>
  );
};
