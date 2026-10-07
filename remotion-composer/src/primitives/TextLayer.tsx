import React from 'react';
import {AbsoluteFill} from 'remotion';
import type {ThemeProps} from '../runtime/props';

export interface TextLayerProps {
  theme: ThemeProps;
  text: string;
  variant?: 'headline' | 'body' | 'label';
  align?: 'left' | 'center' | 'right';
}

/** Subordinate text primitive. Text never dominates the frame by itself;
 * layout and sizing always arrive via props derived from the scene plan. */
export const TextLayer: React.FC<TextLayerProps> = ({theme, text, variant = 'body', align = 'center'}) => {
  const size = variant === 'headline' ? theme.headlineSize : variant === 'label' ? theme.bodySize * 0.7 : theme.bodySize;
  return (
    <AbsoluteFill style={{display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 64}}>
      <div
        style={{
          fontFamily: theme.fontFamily,
          fontSize: size,
          fontWeight: variant === 'headline' ? 800 : 500,
          color: variant === 'label' ? theme.mutedText : theme.text,
          textAlign: align,
          lineHeight: 1.25,
        }}
      >
        {text}
      </div>
    </AbsoluteFill>
  );
};
