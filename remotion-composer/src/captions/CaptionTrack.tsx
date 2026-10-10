import React from 'react';
import {AbsoluteFill, useCurrentFrame} from 'remotion';
import {eventFrames} from '../runtime/timeline';
import {captionSetAt} from './captionSets';
import type {CaptionProps, ThemeProps} from '../runtime/props';

export interface CaptionTrackProps {
  theme: ThemeProps;
  captions: CaptionProps[];
  fps: number;
  mode?: 'sentence' | 'word_highlight' | 'karaoke' | 'emphasis_words';
  /** Absolute start time (seconds) of the CTA scene. Captions clear before the CTA takes focus. */
  ctaStart?: number;
}

const clamp01 = (v: number) => Math.min(1, Math.max(0, v));

/** Caption layer driven exclusively by edit_decisions caption references.
 * Timing is never regenerated here; presentation reveals word-by-word karaoke
 * inside the CURRENT set only. Sets fade in and out at their boundaries, so
 * between sets the screen breathes instead of showing a permanent box.
 * Captions finish and clear before the CTA begins (§19). */
export const CaptionTrack: React.FC<CaptionTrackProps> = ({theme, captions, fps, mode = 'karaoke', ctaStart}) => {
  const frame = useCurrentFrame();

  // §19 — normal narration captions run up to the CTA, then clear. No captions compete with the CTA.
  const clearAt = typeof ctaStart === 'number' && ctaStart > 0 ? ctaStart : null;
  const visible = clearAt !== null
    ? captions
        .filter((caption) => caption.start < clearAt - 0.05)
        .map((caption) => ({...caption, end: Math.min(caption.end, clearAt)}))
    : captions;
  if (visible.length === 0) {
    return null;
  }

  const active = visible.find((caption) => {
    const range = eventFrames(caption.start, caption.end, fps);
    return frame >= range.startFrame && frame < range.endFrame;
  });
  if (!active) {
    return null;
  }
  // Auto-hide subtitle renderer during Outro / CTA / branded scenes
  const scLower = (active.scene_id || '').toLowerCase();
  const textLower = (active.textReference || '').toLowerCase();
  if (
    scLower.includes('cta') ||
    scLower.includes('outro') ||
    scLower.includes('brand') ||
    textLower.includes('subscribe')
  ) {
    return null;
  }

  const range = eventFrames(active.start, active.end, fps);
  const speechOnsetFrames = Math.round(fps * 0.08);
  const speechDurationSeconds = active.audio_duration && active.audio_duration > 0
    ? active.audio_duration
    : Math.max(1, (active.end - active.start) - 0.25);
  const totalSpeechFrames = Math.max(1, Math.round((speechDurationSeconds - 0.08) * fps));
  const framesIntoScene = frame - range.startFrame;
  const currentProgress = clamp01((framesIntoScene - speechOnsetFrames) / totalSpeechFrames);

  // --- Set math: which group of words is on screen right now ---
  // Word-anchored windows (see captionSets): the active word's set always owns
  // the current progress, so the caption only dips to zero at the designed
  // breath at each set boundary — never for a sustained gap.
  const set = captionSetAt(active.textReference, currentProgress);
  if (!set || set.setWords.length === 0) {
    return null;
  }
  const {setWords, activeInSet, opacity: setOpacity} = set;
  if (setOpacity <= 0.03) {
    return null;
  }

  const emphasis = new Set(
    active.emphasisWords.map((w) => w.toLowerCase().replace(/[.,!?;:]+$/, '')),
  );

  return (
    <AbsoluteFill style={{justifyContent: 'flex-end', alignItems: 'center', paddingBottom: 190, pointerEvents: 'none'}}>
      <div
        style={{
          background: 'rgba(24, 24, 27, 0.94)',
          backdropFilter: 'blur(12px)',
          WebkitBackdropFilter: 'blur(12px)',
          border: '1.5px solid rgba(148, 163, 184, 0.35)',
          boxShadow: '0 12px 32px rgba(15, 23, 42, 0.35)',
          borderRadius: 18,
          padding: '14px 26px',
          maxWidth: '78%',
          textAlign: 'center',
          overflow: 'hidden',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          flexWrap: 'wrap',
          opacity: setOpacity,
          transform: `translateY(${(1 - setOpacity) * 8}px)`,
          transition: 'opacity 0.1s ease, transform 0.1s ease',
        }}
      >
        <div
          style={{
            fontFamily: theme.fontFamily || '-apple-system, BlinkMacSystemFont, "Inter", "SF Pro Display", "Segoe UI", Roboto, sans-serif',
            fontSize: Math.round(theme.bodySize * 1.2),
            fontWeight: 800,
            color: '#F8FAFC',
            letterSpacing: '-0.01em',
            lineHeight: 1.35,
          }}
        >
          {setWords.map((word, index) => {
            const clean = word.replace(/[.,!?;:]+$/, '').toLowerCase();
            const isEmphasized = emphasis.has(clean);
            const isPast = index < activeInSet;
            const isActive = index === activeInSet;

            let color = '#E2E8F0';
            let backgroundColor = 'transparent';
            let scale = 1;
            let fontWeight = 700;
            if (isActive) {
              color = isEmphasized ? '#FDE68A' : '#FEF3C7';
              backgroundColor = isEmphasized ? 'rgba(217, 119, 6, 0.30)' : 'rgba(251, 191, 36, 0.22)';
              scale = 1.1;
              fontWeight = 900;
            } else if (isPast) {
              color = '#FFFFFF';
            } else {
              color = '#94A3B8';
            }

            return (
              <span
                key={index}
                style={{
                  display: 'inline-block',
                  color,
                  opacity: isActive || isPast ? 1 : 0.8,
                  transform: `scale(${scale})`,
                  transformOrigin: 'center center',
                  transition: 'transform 0.12s cubic-bezier(0.16, 1, 0.3, 1), color 0.12s ease',
                  backgroundColor,
                  padding: isActive ? '3px 8px' : '2px 4px',
                  borderRadius: 8,
                  margin: '3px 3px',
                  fontWeight,
                }}
              >
                {word}
                {index < setWords.length - 1 ? ' ' : ''}
              </span>
            );
          })}
        </div>
      </div>
    </AbsoluteFill>
  );
};
