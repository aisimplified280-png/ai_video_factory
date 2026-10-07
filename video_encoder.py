import os
import subprocess
import threading
from pathlib import Path

class FFmpegRawVideoEncoder:
    """Streams PIL frames directly to FFmpeg as raw RGB bytes."""

    def __init__(self, output_path, fps=24, width=1080, height=1920):
        self.output_path = str(output_path)
        self.fps = fps
        self.width = width
        self.height = height
        self.proc = None
        self._detect_encoder()

    def _detect_encoder(self):
        """Auto-detect the best available H.264 encoder by running a dummy test."""
        self.vcodec = "libx264"
        self.preset = "fast"
        try:
            result = subprocess.run(["ffmpeg", "-encoders"], capture_output=True, text=True, timeout=3)
            encoders = result.stdout
            
            # Helper to test if an encoder actually works with current drivers
            def test_encoder(enc, preset):
                cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=black:s=128x128", "-t", "0.1", "-c:v", enc, "-preset", preset, "-f", "null", "-"]
                return subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0

            if "nvenc" in encoders and test_encoder("h264_nvenc", "p4"):
                self.vcodec = "h264_nvenc"
                self.preset = "p4"
            elif "qsv" in encoders and test_encoder("h264_qsv", "fast"):
                self.vcodec = "h264_qsv"
                self.preset = "fast"
            elif "amf" in encoders and test_encoder("h264_amf", "fast"):
                self.vcodec = "h264_amf"
                self.preset = "fast"
        except Exception as e:
            print(f"Warning: Failed to probe FFmpeg encoders: {e}. Defaulting to libx264.")

    def start(self):
        """Starts the FFmpeg subprocess."""
        cmd = [
            "ffmpeg", "-y", "-loglevel", "error",
            "-f", "rawvideo",
            "-pix_fmt", "rgb24",
            "-s", f"{self.width}x{self.height}",
            "-r", str(self.fps),
            "-i", "-",
            "-c:v", self.vcodec,
            "-preset", self.preset,
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            self.output_path
        ]
        self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)

    def encode_frame(self, img):
        """Writes a single PIL image to the FFmpeg pipe."""
        if not self.proc:
            raise RuntimeError("Encoder not started.")
        
        if img.mode != "RGB":
            img = img.convert("RGB")
            
        try:
            self.proc.stdin.write(img.tobytes())
        except BrokenPipeError:
            err = self.proc.stderr.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"FFmpeg pipeline broke during encode: {err}")

    def close(self):
        """Closes the pipe and waits for FFmpeg to finish encoding."""
        if not self.proc:
            return
            
        try:
            self.proc.stdin.close()
        except Exception:
            pass
            
        self.proc.wait()
        
        if self.proc.returncode != 0:
            err = self.proc.stderr.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"FFmpeg failed with code {self.proc.returncode}:\n{err}")
