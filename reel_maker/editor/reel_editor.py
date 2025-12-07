# Handles trimming, cropping, filtering
import os
import math
import shutil
import tempfile
from typing import List, Optional, Dict, Any
from .ffmpeg_wrapper import FFmpegWrapper, FFmpegError
from utils.file_utils import ensure_folder, timestamped_filename, join_path, safe_filename


class ReelEditor:
    """
    High-level reel operations:
    - create single reel from a source video
    - split a source into multiple reels (drafts)
    - create thumbnails for reels
    - place drafts in a per-video temp folder
    """

    def __init__(self, base_output: str = "ReelShortMaker/output", temp_root: str = "ReelShortMaker/temp"):
        self.base_output = base_output
        self.temp_root = temp_root
        ensure_folder(self.base_output)
        ensure_folder(self.temp_root)

    def _make_video_temp_folder(self, video_hash: str) -> str:
        folder = os.path.join(self.temp_root, safe_filename(video_hash))
        ensure_folder(folder)
        return folder

    def create_single_reel(self, src_path: str, start: float = 0.0, duration: float = 15.0,
                           target_w: int = 1080, target_h: int = 1920,
                           overlay_text: Optional[str] = None, bg_music: Optional[str] = None,
                           video_hash: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a single vertical reel and place it in a per-video temp folder. Returns metadata dict.
        """
        if not video_hash:
            video_hash = os.path.splitext(os.path.basename(src_path))[0]

        temp_folder = self._make_video_temp_folder(video_hash)
        base_out = timestamped_filename(video_hash + "_reel", "mp4")
        out_path = os.path.join(temp_folder, base_out)

        # Build filter to scale then center-crop to target
        vf = f"scale='if(gt(a,{target_w}/{target_h}),{target_w},-2)':'if(gt(a,{target_w}/{target_h}),-2,{target_h})',crop={target_w}:{target_h}"
        # Add drawtext if required (font path auto-detected)
        if overlay_text:
            fontfile = self._get_default_font()
            # escape colon and single quotes in text
            text = overlay_text.replace(":", "\\:").replace("'", "\\'")
            draw = f"drawtext=fontfile='{fontfile}':text='{text}':fontsize=48:fontcolor=white:x=(w-text_w)/2:y=h-180:box=1:boxcolor=black@0.5"
            vf = vf + "," + draw

        # If bg_music provided, mix audios
        try:
            if bg_music:
                # Use filter_complex to mix original audio + bg (bg lower volume)
                audio_mix = "[0:a]volume=1.0[a0];[1:a]volume=0.4[a1];[a0][a1]amix=inputs=2:duration=first:dropout_transition=2[aout]"
                args = [
                    "-y",
                    "-ss", str(start),
                    "-i", src_path,
                    "-i", bg_music,
                    "-t", str(duration),
                    "-filter_complex", audio_mix,
                    "-map", "0:v",
                    "-map", "[aout]",
                    "-vf", vf,
                    "-c:v", "libx264",
                    "-preset", "fast",
                    "-crf", "18",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    "-pix_fmt", "yuv420p",
                    "-movflags", "+faststart",
                    out_path
                ]
                FFmpegWrapper.run(args, capture_output=True)
            else:
                # simple single input
                FFmpegWrapper.extract_clip(src_path, out_path, start=start, duration=duration, video_filter=vf)
        except FFmpegError as e:
            raise

        # generate thumbnail for the reel
        thumb_path = out_path + ".thumb.jpg"
        try:
            FFmpegWrapper.create_thumbnail(out_path, thumb_path, time=0.5, width=360)
        except Exception:
            # ignore thumbnail errors
            thumb_path = ""

        meta = {
            "path": out_path,
            "thumb": thumb_path,
            "start": start,
            "duration": duration,
            "video_hash": video_hash
        }
        return meta

    def split_into_reels(self, src_path: str, reel_duration: int = 15, overlap: float = 0.0,
                         max_reels: Optional[int] = None, video_hash: Optional[str] = None,
                         **kwargs) -> List[Dict[str, Any]]:
        """
        Split a source video into multiple reels (drafts) saved into temp/video_hash/.
        Returns list of metadata dictionaries for each created reel.
        """
        if not video_hash:
            video_hash = os.path.splitext(os.path.basename(src_path))[0]
        temp_folder = self._make_video_temp_folder(video_hash)

        info = FFmpegWrapper.probe(src_path)
        duration = float(info.get("format", {}).get("duration") or 0.0)
        if duration <= 0:
            raise RuntimeError("Could not obtain duration of source video")

        step = reel_duration - overlap if reel_duration > overlap else reel_duration
        count = math.ceil(duration / step)
        if max_reels:
            count = min(count, max_reels)

        results = []
        start = 0.0
        for i in range(count):
            if start >= duration:
                break
            meta = self.create_single_reel(src_path, start=start, duration=min(reel_duration, duration - start),
                                          video_hash=video_hash, **kwargs)
            results.append(meta)
            start += step

        return results

    def export_reel(self, reel_meta: Dict[str, Any], dest_folder: Optional[str] = None) -> str:
        """
        Move a reel from temp folder to final output folder (base_output) or to dest_folder.
        Returns path of exported file.
        """
        src = reel_meta.get("path")
        if not src or not os.path.exists(src):
            raise FileNotFoundError("Reel file not found")

        dest_folder = dest_folder or self.base_output
        ensure_folder(dest_folder)
        dst = os.path.join(dest_folder, os.path.basename(src))
        shutil.copy2(src, dst)
        # copy thumbnail too
        thumb = reel_meta.get("thumb")
        if thumb and os.path.exists(thumb):
            try:
                shutil.copy2(thumb, dst + ".thumb.jpg")
            except Exception:
                pass
        return dst

    def _get_default_font(self) -> str:
        # Try common font paths, fallback to none (ffmpeg may use default)
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # linux
            "/Library/Fonts/Arial.ttf",  # mac
            "C:/Windows/Fonts/arial.ttf",  # windows
        ]
        for p in candidates:
            if os.path.exists(p):
                return p
        return ""  # let ffmpeg use default font if empty
