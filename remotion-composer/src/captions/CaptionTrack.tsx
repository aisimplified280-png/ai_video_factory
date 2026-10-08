import React from 'react';
import {AbsoluteFill, useCurrentFrame} from 'remotion';
import {eventFrames} from '../runtime/timeline';
import type {CaptionProps, ThemeProps} from '../runtime/props';

export interface CaptionTrackProps {
  theme: ThemeProps;
  captions: CaptionProps[];
  fps: number;
  mode?: 'sentence' | 'word_highlight' | 'karaoke' | 'emphasis_words';
}

/** Caption layer driven exclusively by edit_decisions caption references.
 * Timing is never regenerated here; presentation adds dynamic word-by-word karaoke reveal. */
export const CaptionTrack: React.FC<CaptionTrackProps> = ({theme, captions, fps, mode = 'karaoke'}) => {
  const frame = useCurrentFrame();
  const active = captions.find((caption) => {
    const range = eventFrames(caption.start, caption.end, fps);
    return frame >= range.startFrame && frame < range.endFrame;
  });
  if (!active) {
    return null;
  }
  // RULE C: Auto-hide subtitle renderer as soon as Scene 5 (Outro / CTA / Subscribe) triggers
  const scLower = (active.scene_id || '').toLowerCase();
  const textLower = (active.textReference || '').toLowerCase();
  if (
    scLower.includes('scene_05') ||
    scLower.includes('sec_05') ||
    scLower.includes('cta') ||
    scLower.includes('outro') ||
    scLower.includes('brand') ||
    textLower.includes('subscribe to ai simplified') ||
    textLower.includes('subscribe to')
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
  const currentProgress = Math.min(1, Math.max(0, (framesIntoScene - speechOnsetFrames) / totalSpeechFrames));

  return (
    <AbsoluteFill style={{justifyContent: 'flex-end', alignItems: 'center', paddingBottom: 200, pointerEvents: 'none'}}>
      <div
        style={{
          background: 'rgba(255, 255, 255, 0.94)',
          backdropFilter: 'blur(16px)',
          WebkitBackdropFilter: 'blur(16px)',
          border: '1.5px solid #CBD5E1',
          boxShadow: '0 12px 32px rgba(30, 64, 175, 0.08), 0 2px 8px rgba(15, 23, 42, 0.04)',
          borderRadius: 24,
          padding: '14px 28px',
          maxWidth: '82%',
          textAlign: 'center',
          maxHeight: 120,
          overflow: 'hidden',
          display: '-webkit-box',
          WebkitLineClamp: 2,
          WebkitBoxOrient: 'vertical',
        }}
      >
        <div
          style={{
            fontFamily: theme.fontFamily || '-apple-system, BlinkMacSystemFont, "Inter", "SF Pro Display", "Segoe UI", Roboto, sans-serif',
            fontSize: Math.round(theme.bodySize * 1.15),
            fontWeight: 800,
            color: '#0F172A',
            letterSpacing: '-0.02em',
            lineHeight: 1.35,
          }}
        >
          <KaraokeText
            text={active.textReference}
            progress={currentProgress}
            emphasisWords={active.emphasisWords}
          />
        </div>
      </div>
    </AbsoluteFill>
  );
};

function KaraokeText({
  text,
  progress,
  emphasisWords,
}: {
  text: string;
  progress: number;
  emphasisWords: string[];
}) {
  const words = text.split(/\s+/).filter(Boolean);
  if (words.length === 0) return null;

  const emphasis = new Set(emphasisWords.map((w) => w.toLowerCase()));
  // Calculate active word index based on time progress
  const activeWordIdx = Math.min(words.length - 1, Math.floor(progress * words.length));

  return (
    <>
      {words.map((word, index) => {
        const cleanWord = word.replace(/[.,!?;:]+$/, '').toLowerCase();
        const isEmphasized = emphasis.has(cleanWord);
        const isPast = index < activeWordIdx;
        const isActive = index === activeWordIdx;
        const isUpcoming = index > activeWordIdx;

        // Active spoken word has scale pop, royal blue or amber highlight
        let color = '#0F172A'; // Slate Ink for spoken past words
        let opacity = 1.0;
        let scale = 1.0;
        let backgroundColor = 'transparent';
        let textShadow = 'none';

        if (isActive) {
          color = isEmphasized ? '#D97706' : '#1E40AF'; // Amber for keyword, Royal Blue for active word
          backgroundColor = isEmphasized ? '#FEF3C7' : '#EFF6FF'; // Soft amber or soft blue pill
          scale = 1.12;
          opacity = 1.0;
          textShadow = '0 2px 8px rgba(30, 64, 175, 0.15)';
        } else if (isUpcoming) {
          color = '#475569'; // Dark slate
          opacity = 0.40; // 40% opacity for upcoming words
          scale = 1.0;
        } else if (isPast) {
          color = '#0F172A';
          opacity = 1.0;
        }

        return (
          <span
            key={index}
            style={{
              display: 'inline-block',
              color,
              opacity,
              transform: `scale(${scale})`,
              transformOrigin: 'center center',
              transition: 'transform 0.12s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.12s ease',
              backgroundColor,
              padding: isActive ? '2px 8px' : '0 2px',
              borderRadius: 8,
              margin: '0 2px',
              fontWeight: isActive ? 900 : 800,
              textShadow,
            }}
          >
            {word}
            {index < words.length - 1 ? ' ' : ''}
          </span>
        );
      })}
    </>
  );
}
