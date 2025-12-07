# Low-level ffmpeg commands
import subprocess
import json
import shutil
from typing import Dict, Any, Optional


class FFmpegError(RuntimeError):
    pass


class FFmpegWrapper:
    """
    Thin wrapper around ffmpeg / ffprobe command-line tools.
    Exposes probe, run and helper functions used by the editor.
    """

    FFMPEG = shutil.which("ffmpeg") or "ffmpeg"
    FFPROBE = shutil.which("ffprobe") or "ffprobe"

    @classmethod
    def run(cls, args: list, capture_output: bool = False, check: bool = True) -> subprocess.CompletedProcess:
        cmd = [cls.FFMPEG] + args
        try:
            proc = subprocess.run(cmd, capture_output=capture_output, text=True, check=check)
            return proc
        except subprocess.CalledProcessError as e:
            out = e.stdout or ""
            err = e.stderr or ""
            raise FFmpegError(f"ffmpeg failed: {e.returncode}\nSTDOUT: {out}\nSTDERR: {err}")

    @classmethod
    def probe(cls, path: str) -> Dict[str, Any]:
        cmd = [cls.FFPROBE, "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", path]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return json.loads(proc.stdout or "{}")
        except subprocess.CalledProcessError as e:
            raise FFmpegError(f"ffprobe failed: {e.stderr or e}")

    @classmethod
    def get_duration(cls, path: str) -> float:
        info = cls.probe(path)
        return float(info.get("format", {}).get("duration") or 0.0)

    @classmethod
    def create_thumbnail(cls, input_path: str, output_image: str, time: float = 1.0, width: int = 480) -> None:
        # create a thumbnail image (jpeg/png)
        args = [
            "-y",
            "-ss", str(time),
            "-i", input_path,
            "-vframes", "1",
            "-vf", f"scale={width}:-1",
            output_image
        ]
        cls.run(args, capture_output=True)

    @classmethod
    def extract_clip(cls, input_path: str, output_path: str, start: float, duration: float,
                     video_filter: Optional[str] = None, audio_only: bool = False) -> None:
        args = ["-y", "-ss", str(start), "-i", input_path, "-t", str(duration)]
        if audio_only:
            args += ["-vn", "-c:a", "aac", "-b:a", "192k", output_path]
        else:
            if video_filter:
                args += ["-vf", video_filter]
            args += ["-c:v", "libx264", "-preset", "fast", "-crf", "18", "-c:a", "aac", "-b:a", "192k", output_path]
        cls.run(args, capture_output=True)

    @classmethod
    def convert_to_mp4(cls, input_path: str, output_path: str) -> None:
        """
        Convert input video to a friendly mp4 (h264 + aac) preserving quality where possible.
        """
        args = [
            "-y",
            "-i", input_path,
            "-c:v", "libx264",
            "-preset", "slow",
            "-crf", "18",
            "-c:a", "aac",
            "-b:a", "192k",
            "-movflags", "+faststart",
            output_path
        ]
        cls.run(args, capture_output=True)
