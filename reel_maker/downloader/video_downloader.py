# Handles YouTube/Facebook downloads
import os
from typing import Optional, Dict, Any
from yt_dlp import YoutubeDL
from utils.file_utils import join_path, ensure_folder, safe_filename
from editor.ffmpeg_wrapper import FFmpegWrapper


class VideoDownloader:
    """
    Simple wrapper for yt-dlp to fetch info and download videos.
    """

    def __init__(self, out_folder: str = "ReelShortMaker/downloads", force_mp4: bool = True):
        self.out_folder = out_folder
        ensure_folder(self.out_folder)
        self.force_mp4 = force_mp4

    def fetch_info(self, url: str) -> Dict[str, Any]:
        opts = {'quiet': True, 'no_warnings': True}
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
        return info

    def download_best(self, url: str, title_hint: Optional[str] = None) -> str:
        """
        Download best video+audio. If force_mp4 is True, attempt bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4
        Returns the path to the saved file.
        """
        outtmpl = os.path.join(self.out_folder, "%(title)s.%(ext)s")
        ydl_opts = {
            'outtmpl': outtmpl,
            'quiet': True,
            'no_warnings': True,
            'merge_output_format': 'mp4'
        }
        if self.force_mp4:
            ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4'
        else:
            ydl_opts['format'] = 'bestvideo+bestaudio/best'

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        # Try to find actual saved filename
        filename = info.get('_filename') or info.get('requested_downloads', [{}])[0].get('filepath')
        if not filename:
            title = safe_filename(info.get('title') or title_hint or "video")
            ext = info.get('ext') or "mp4"
            filename = os.path.join(self.out_folder, f"{title}.{ext}")

        # If the file is not mp4 and force_mp4 requested, convert
        if self.force_mp4 and not filename.lower().endswith(".mp4"):
            target = os.path.splitext(filename)[0] + ".mp4"
            try:
                FFmpegWrapper.convert_to_mp4(filename, target)
                filename = target
            except Exception:
                # If conversion fails, just return original path
                pass

        return filename
