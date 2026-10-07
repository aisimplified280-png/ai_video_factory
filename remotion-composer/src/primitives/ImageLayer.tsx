import React from 'react';
import {AbsoluteFill, Img} from 'remotion';

export interface ImageLayerProps {
  src: string;
  opacity?: number;
  style?: React.CSSProperties;
  framing?: string | null;
}

/** Still image from the asset manifest, framed according to directorial shot scale and transformed by camera/motion wrappers. */
export const ImageLayer: React.FC<ImageLayerProps> = ({src, opacity = 1, style, framing}) => {
  let framingTransform = 'scale(1.0)';
  let transformOrigin = '50% 50%';

  if (framing === 'close_up' || framing === 'detail') {
    framingTransform = 'scale(1.35)';
    transformOrigin = '50% 38%';
  } else if (framing === 'macro' || framing === 'extreme_close_up') {
    framingTransform = 'scale(1.65)';
    transformOrigin = '50% 40%';
  } else if (framing === 'medium' || framing === 'isometric') {
    framingTransform = 'scale(1.15)';
    transformOrigin = '50% 45%';
  } else if (framing === 'wide' || framing === 'full_frame' || framing === 'establishing') {
    framingTransform = 'scale(1.0)';
    transformOrigin = '50% 50%';
  } else if (framing === 'centered_studio') {
    framingTransform = 'scale(1.05)';
    transformOrigin = '50% 50%';
  }

  return (
    <AbsoluteFill style={{opacity, ...style}}>
      <div style={{width: '100%', height: '100%', overflow: 'hidden', transform: framingTransform, transformOrigin}}>
        <Img src={src} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
      </div>
    </AbsoluteFill>
  );
};
