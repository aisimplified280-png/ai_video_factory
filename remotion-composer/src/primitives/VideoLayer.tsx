import React from 'react';
import {AbsoluteFill, Video} from 'remotion';

export interface VideoLayerProps {
  src: string;
  opacity?: number;
  style?: React.CSSProperties;
}

/** Video asset from the manifest. Playback follows the edit event timing. */
export const VideoLayer: React.FC<VideoLayerProps> = ({src, opacity = 1, style}) => {
  return (
    <AbsoluteFill style={{opacity, ...style}}>
      <Video src={src} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
    </AbsoluteFill>
  );
};
