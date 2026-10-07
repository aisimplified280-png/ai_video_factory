import {Config} from '@remotion/cli/config';

// Deterministic output: fixed image format and JPEG quality so identical
// inputs produce identical frames. Dimensions/FPS always come from the
// platform profile via calculateMetadata, never from these defaults.
Config.setVideoImageFormat('jpeg');
Config.setJpegQuality(90);
Config.setOverwriteOutput(true);
