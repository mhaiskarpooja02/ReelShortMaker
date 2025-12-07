# ReelShortMaker – Professional Reel & Shorts Studio

Generated project structure.
# ReelShortMaker — Complete Professional Studio

Create short vertical reels/shorts from videos (local or online).

## Features
- Download videos from YouTube / Facebook / Instagram (public) using yt-dlp
- Convert downloaded videos to MP4 (H.264 + AAC) automatically
- Create single or multiple short reels (vertical 1080×1920)
- Add text overlay and optional background music
- Keep multiple drafts per source video (temp folder). Preview and export chosen draft.
- Modern UI with ttkbootstrap

## Installation
1. Install ffmpeg (system binary) and ensure `ffmpeg` and `ffprobe` are on PATH:
   - https://ffmpeg.org/

2. Create virtual env and install Python deps:
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
