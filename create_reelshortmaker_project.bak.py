import os

project_structure = {
    "reel_maker": {
        "__init__.py": "",
        "app.py": "# Main application launcher\n",
        "downloader": {
            "__init__.py": "",
            "video_downloader.py": "# Handles YouTube/Facebook downloads\n",
        },
        "editor": {
            "__init__.py": "",
            "reel_editor.py": "# Handles trimming, cropping, filtering\n",
            "ffmpeg_wrapper.py": "# Low-level ffmpeg commands\n",
            "timeline_editor.py": "# Advanced editing features\n",
        },
        "ui": {
            "__init__.py": "",
            "main_window.py": "# Full Tkinter + ttkbootstrap GUI\n",
            "timeline_ui.py": "# Visual timeline editor\n",
        },
        "utils": {
            "__init__.py": "",
            "file_utils.py": "# Helper utilities for file paths\n",
            "config.py": "# App configuration\n",
        },
        "assets": {},  # Images, icons, etc.
    },
    "requirements.txt": """yt-dlp
ttkbootstrap
pillow
moviepy
opencv-python
numpy
requests
""",
    "README.md": "# ReelShortMaker – Professional Reel & Shorts Studio\n\nGenerated project structure.\n",
}


def create_structure(base_path, structure):
    for name, content in structure.items():
        path = os.path.join(base_path, name)

        if isinstance(content, dict):
            # folder
            os.makedirs(path, exist_ok=True)
            create_structure(path, content)
        else:
            # file
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)


if __name__ == "__main__":
    base_path = os.getcwd()
    create_structure(base_path, project_structure)
    print("Project structure created successfully!")
 
