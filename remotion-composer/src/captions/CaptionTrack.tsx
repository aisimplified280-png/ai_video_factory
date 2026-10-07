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
 * Timing is never regenerated here; only presentation of the referenced text. */
export const CaptionTrack: React.FC<CaptionTrackProps> = ({theme, captions, fps, mode = 'emphasis_words'}) => {
  const frame = useCurrentFrame();
  const active = captions.find((caption) => {
    const range = eventFrames(caption.start, caption.end, fps);
    return frame >= range.startFrame && frame < range.endFrame;
  });
  if (!active) {
    return null;
  }
  // RULE 1: Disable standard bottom captions when on-screen CTA graphic is active
  const scLower = (active.scene_id || '').toLowerCase();
  if (scLower.includes('scene_05') || scLower.includes('sec_05') || scLower.includes('cta') || scLower.includes('outro')) {
    return null;
  }
  const emphasis = new Set(active.emphasisWords.map((word) => word.toLowerCase()));
  return (
    <AbsoluteFill style={{justifyContent: 'flex-end', alignItems: 'center', paddingBottom: 210}}>
      <div
        style={{
          fontFamily: theme.fontFamily,
          fontSize: Math.round(theme.bodySize * 1.12),
          fontWeight: 800,
          color: '#FFFFFF',
          textShadow: '0 4px 20px rgba(0,0,0,0.98), 0 2px 6px rgba(0,0,0,0.95), 0 0 30px rgba(0,0,0,0.9)',
          letterSpacing: '-0.02em',
          maxWidth: '88%',
          textAlign: 'center',
          lineHeight: 1.35,
        }}
      >
        {mode === 'emphasis_words' ? (
          <EmphasisText text={active.textReference} emphasis={emphasis} accent={theme.accent} />
        ) : (
          active.textReference
        )}
      </div>
    </AbsoluteFill>
  );
};

function EmphasisText({text, emphasis, accent}: {text: string; emphasis: Set<string>; accent: string}) {
  const words = text.split(/\s+/);
  return (
    <>
      {words.map((word, index) => {
        const hot = emphasis.has(word.replace(/[.,!?;:]+$/, '').toLowerCase());
        return (
          <span
            key={index}
            style={
              hot
                ? {
                    color: accent,
                    fontWeight: 900,
                    textShadow: `0 0 24px ${accent}cc, 0 4px 16px rgba(0,0,0,0.98)`,
                  }
                : undefined
            }
          >
            {word}
            {index < words.length - 1 ? ' ' : ''}
          </span>
        );
      })}
    </>
  );
}
