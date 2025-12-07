# Helper utilities for file paths
import os
from datetime import datetime
import re


def ensure_folder(path: str):
    os.makedirs(path, exist_ok=True)


def safe_filename(name: str) -> str:
    if not name:
        return ""
    name = str(name).strip()
    # replace forbidden characters
    name = re.sub(r'[<>:"/\\|?*\']', "", name)
    # collapse spaces
    name = re.sub(r'\s+', '_', name)
    return name


def timestamped_filename(base: str, ext: str) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = safe_filename(base) or "output"
    ext = ext.lstrip(".")
    return f"{base}_{ts}.{ext}"


def join_path(folder: str, filename: str) -> str:
    ensure_folder(folder)
    return os.path.join(folder, filename)


def human_size(num: int, suffix='B') -> str:
    try:
        num = float(num)
    except Exception:
        return "0B"
    for unit in ['','K','M','G','T','P']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'P', suffix)
