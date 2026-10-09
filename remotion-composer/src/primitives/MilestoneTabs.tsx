import React from 'react';
import {useCurrentFrame} from 'remotion';
import type {MilestoneProps, ThemeProps} from '../runtime/props';

/**
 * Persistent top milestone bar (reference-video layout).
 *
 * The video's content scenes render as 4-7 chapter tabs pinned to the top of
 * the canvas; the active tab lights up as the voiceover moves through the
 * script, completed tabs stay readable, future tabs stay dim. The bar is
 * decorative chrome: it never captures input and never overlaps the caption
 * safe zone (bottom) or the CTA card (bottom).
 */
export const MilestoneTabs: React.FC<{
  milestones: MilestoneProps[];
  theme: ThemeProps;
  fps: number;
  width: number;
}> = ({milestones, theme, fps, width}) => {
  const frame = useCurrentFrame();
  if (!milestones || milestones.length < 2) {
    return null;
  }
  const t = frame / fps;
  // Clamp: the last content chapter stays lit through the outro.
  let activeIdx = 0;
  for (let i = 0; i < milestones.length; i++) {
    if (t >= milestones[i].start) {
      activeIdx = i;
    }
  }
  const fadeIn = Math.min(1, Math.max(0, t / 0.35));
  // 16-char labels must fit their chip at ~4 tabs across a 1080px canvas.
  const chipFont = Math.max(18, Math.min(22, Math.floor(width / 49)));

  return (
    <div
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        zIndex: 130,
        display: 'flex',
        justifyContent: 'center',
        pointerEvents: 'none',
        opacity: fadeIn,
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexWrap: 'wrap',
          gap: 4,
          rowGap: 4,
          margin: '54px 20px 0',
          padding: '10px 16px',
          maxWidth: '94%',
          background: 'rgba(24, 24, 27, 0.88)',
          backdropFilter: 'blur(10px)',
          border: '1px solid rgba(148, 163, 184, 0.25)',
          borderRadius: 20,
          overflow: 'hidden',
        }}
      >
        {milestones.map((m, i) => {
          const isActive = i === activeIdx;
          const isDone = i < activeIdx;
          return (
            <React.Fragment key={`${m.scene_id}-${i}`}>
              {i > 0 ? (
                <span style={{color: 'rgba(148, 163, 184, 0.35)', fontSize: chipFont}}>|</span>
              ) : null}
              <span
                style={{
                  fontFamily: theme.fontFamily,
                  fontSize: isActive ? chipFont : chipFont - 3,
                  fontWeight: isActive ? 800 : 600,
                  textTransform: 'uppercase',
                  letterSpacing: '0.06em',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  maxWidth: Math.floor(width / 3.4),
                  padding: '4px 10px',
                  borderRadius: 8,
                  color: isActive
                    ? '#FFFFFF'
                    : isDone
                      ? 'rgba(248, 250, 252, 0.70)'
                      : 'rgba(148, 163, 184, 0.75)',
                  background: isActive ? 'rgba(251, 191, 36, 0.14)' : 'transparent',
                  boxShadow: isActive ? `inset 0 -3px 0 ${theme.accent}` : 'none',
                  transform: isActive ? 'scale(1.04)' : 'scale(1)',
                  transition: 'transform 0.18s ease, color 0.18s ease',
                }}
              >
                {m.label}
              </span>
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};
