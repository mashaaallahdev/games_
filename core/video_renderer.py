import subprocess
import os
from pathlib import Path
import imageio_ffmpeg
from core.config import VIDEO_WIDTH, VIDEO_HEIGHT, FPS

class VideoRenderer:
    """
    Encodes raw frame streams into high-definition 1080x1920 60FPS vertical video
    and cleanly muxes with synthesized procedural audio using FFmpeg.
    """
    def __init__(self, output_path: Path, width: int = VIDEO_WIDTH, height: int = VIDEO_HEIGHT, fps: int = FPS):
        self.output_path = Path(output_path)
        self.width = width
        self.height = height
        self.fps = fps
        self.ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        self.temp_video = self.output_path.with_name(f"temp_{self.output_path.name}")
        self.process = None

    def start(self):
        """Starts the FFmpeg subprocess reading raw video frames from stdin."""
        cmd = [
            self.ffmpeg_exe,
            "-y",  # Overwrite output
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-s", f"{self.width}x{self.height}",
            "-pix_fmt", "rgb24",
            "-r", str(self.fps),
            "-i", "-",  # Read from pipe
            "-an",      # No audio on this pass
            "-vcodec", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "fast",
            "-crf", "18",  # Visually lossless quality
            str(self.temp_video)
        ]
        self.process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE
        )

    def write_frame(self, frame_bytes: bytes):
        """Pipes a single raw RGB frame to FFmpeg."""
        if self.process and self.process.stdin:
            self.process.stdin.write(frame_bytes)

    def finish_video_only(self):
        """Closes stdin and waits for video encoding to finish."""
        if self.process:
            self.process.stdin.close()
            _, stderr = self.process.communicate()
            if self.process.returncode != 0:
                print(f"FFmpeg error: {stderr.decode('utf-8', errors='ignore')}")
            self.process = None

    def finalize_with_audio(self, wav_path: Path):
        """Muxes the generated video with the synthesized audio track into final MP4."""
        self.finish_video_only()

        cmd = [
            self.ffmpeg_exe,
            "-y",
            "-i", str(self.temp_video),
            "-i", str(wav_path),
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            str(self.output_path)
        ]

        result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        if result.returncode != 0:
            print(f"Audio Muxing error: {result.stderr.decode('utf-8', errors='ignore')}")

        # Clean up temp files
        if self.temp_video.exists():
            try:
                self.temp_video.unlink()
            except Exception:
                pass
        if wav_path.exists():
            try:
                wav_path.unlink()
            except Exception:
                pass

        return self.output_path
