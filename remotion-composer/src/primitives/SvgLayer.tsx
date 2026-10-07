import React from 'react';
import {AbsoluteFill, Img} from 'remotion';

export interface SvgLayerProps {
  src: string;
  opacity?: number;
}

/** SVG asset rendered crisply at any scale. */
export const SvgLayer: React.FC<SvgLayerProps> = ({src, opacity = 1}) => {
  return (
    <AbsoluteFill style={{opacity, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
      <Img src={src} style={{width: '100%', height: '100%', objectFit: 'contain'}} />
    </AbsoluteFill>
  );
};
