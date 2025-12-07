# Full Tkinter + ttkbootstrap GUI
import os
import threading
import webbrowser
import tempfile
import subprocess
import time
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from downloader.video_downloader import VideoDownloader
from editor.reel_editor import ReelEditor
from utils.file_utils import ensure_folder
from PIL import Image, ImageTk


class AppUI:
    def __init__(self, root):
        self.root = root
        self.style = tb.Style(theme="darkly")
        root.title("ReelShortMaker - Complete Studio")
        root.geometry("1100x700")

        # default folders
        self.base_folder = os.path.join(os.path.expanduser("~"), "ReelShortMaker")
        self.download_folder = os.path.join(self.base_folder, "downloads")
        self.output_folder = os.path.join(self.base_folder, "output")
        self.temp_root = os.path.join(self.base_folder, "temp")
        ensure_folder(self.base_folder)
        ensure_folder(self.download_folder)
        ensure_folder(self.output_folder)
        ensure_folder(self.temp_root)

        # components
        self.current_src = None
        self.current_video_hash = None
        self.last_downloaded = None
        self.reel_drafts = []  # list of metadata dicts for current video

        # services
        self.downloader = VideoDownloader(out_folder=self.download_folder, force_mp4=True)
        self.editor = ReelEditor(base_output=self.output_folder, temp_root=self.temp_root)

        # UI vars
        self.url_var = tk.StringVar()
        self.start_var = tk.StringVar(value="00:00:00")
        self.end_var = tk.StringVar(value="00:00:15")
        self.duration_var = tk.IntVar(value=15)
        self.overlap_var = tk.DoubleVar(value=0.0)
        self.overlay_text_var = tk.StringVar(value="")
        self.bg_music_var = tk.StringVar(value="")
        self.quality_var = tk.StringVar(value="high")

        self._build_ui()

    def _build_ui(self):
        main = tb.Frame(self.root, padding=8)
        main.pack(fill='both', expand=True)

        left = tb.Frame(main)
        left.pack(side='left', fill='y', padx=(0,8))

        center = tb.Frame(main)
        center.pack(side='left', fill='both', expand=True, padx=(0,8))

        right = tb.Frame(main, width=320)
        right.pack(side='right', fill='y')
        right.pack_propagate(False)

        # ------------------ Left: Source / Download ------------------
        src_frame = tb.Labelframe(left, text="Source")
        src_frame.pack(fill='x', pady=6)

        tb.Label(src_frame, text="Local file:").grid(row=0, column=0, sticky='w')
        tb.Button(src_frame, text="Browse", bootstyle="secondary", command=self.browse_local).grid(row=0, column=1, sticky='e')

        tb.Label(src_frame, text="OR Paste URL:").grid(row=1, column=0, sticky='w', pady=(6,0))
        tb.Entry(src_frame, textvariable=self.url_var, width=40).grid(row=1, column=1, sticky='we', padx=4)
        tb.Button(src_frame, text="Download", bootstyle="primary", command=self.download_url).grid(row=2, column=1, sticky='e', pady=6)

        # Info area
        self.info_box = tb.LabelFrame(left, text="Video Info")
        self.info_box.pack(fill='both', expand=False, pady=6)
        self.info_label = tk.Label(self.info_box, text="No video loaded", justify='left', anchor='w')
        self.info_label.pack(fill='both', padx=6, pady=6)

        # Reels from current video list
        list_frame = tb.Labelframe(left, text="Reels (from current video)")
        list_frame.pack(fill='both', expand=True, pady=6)
        self.reel_listbox = tk.Listbox(list_frame, width=40, height=18)
        self.reel_listbox.pack(side='left', fill='both', expand=True, padx=(6,0), pady=6)
        self.reel_listbox.bind("<<ListboxSelect>>", self.on_reel_select)

        list_btn_frame = tb.Frame(list_frame)
        list_btn_frame.pack(side='right', fill='y', padx=6)
        tb.Button(list_btn_frame, text="Refresh", bootstyle="secondary", command=self.refresh_drafts).pack(fill='x', pady=4)
        tb.Button(list_btn_frame, text="Export Selected", bootstyle="success", command=self.export_selected).pack(fill='x', pady=4)
        tb.Button(list_btn_frame, text="Delete Selected", bootstyle="danger", command=self.delete_selected).pack(fill='x', pady=4)
        tb.Button(list_btn_frame, text="Open Folder", bootstyle="secondary", command=self.open_temp_folder).pack(fill='x', pady=4)

        # ------------------ Center: Editor ------------------
        editor_frame = tb.Labelframe(center, text="Editor / Trim")
        editor_frame.pack(fill='both', expand=False, pady=6)

        row1 = tb.Frame(editor_frame)
        row1.pack(fill='x', pady=4, padx=6)
        tb.Label(row1, text="Start (sec):").pack(side='left')
        tb.Entry(row1, width=10, textvariable=self.start_var).pack(side='left', padx=6)
        tb.Label(row1, text="Duration (s):").pack(side='left', padx=(6,0))
        tb.Spinbox(row1, from_=3, to=60, increment=1, textvariable=self.duration_var, width=6).pack(side='left', padx=6)
        tb.Label(row1, text="Overlap (s):").pack(side='left', padx=(6,0))
        tb.Entry(row1, width=6, textvariable=self.overlap_var).pack(side='left', padx=6)

        row2 = tb.Frame(editor_frame)
        row2.pack(fill='x', pady=4, padx=6)
        tb.Label(row2, text="Overlay Text:").pack(side='left')
        tb.Entry(row2, textvariable=self.overlay_text_var).pack(side='left', fill='x', expand=True, padx=6)

        row3 = tb.Frame(editor_frame)
        row3.pack(fill='x', pady=4, padx=6)
        tb.Label(row3, text="Background Music:").pack(side='left')
        tb.Entry(row3, textvariable=self.bg_music_var).pack(side='left', fill='x', expand=True, padx=6)
        tb.Button(row3, text="Browse", bootstyle="secondary", command=self.browse_music).pack(side='left', padx=6)

        op_row = tb.Frame(editor_frame)
        op_row.pack(fill='x', pady=6, padx=6)
        tb.Button(op_row, text="Create Single Reel (draft)", bootstyle="info", command=self.create_single_reel).pack(side='left', padx=4)
        tb.Button(op_row, text="Auto Split -> Drafts", bootstyle="warning", command=self.split_into_reels).pack(side='left', padx=4)

        # ------------------ Right: Preview & Export ------------------
        preview_frame = tb.Labelframe(right, text="Preview")
        preview_frame.pack(fill='both', expand=True, pady=6, padx=6)

        self.preview_canvas = tk.Canvas(preview_frame, width=300, height=540, bg=self.style.colors.bg)
        self.preview_canvas.pack(padx=6, pady=6)

        self.meta_label = tk.Label(preview_frame, text="", justify='left', anchor='nw')
        self.meta_label.pack(fill='x', padx=6)

        preview_btns = tb.Frame(preview_frame)
        preview_btns.pack(fill='x', pady=6, padx=6)
        tb.Button(preview_btns, text="Play (system)", bootstyle="secondary", command=self.play_selected).pack(side='left', padx=4)
        tb.Button(preview_btns, text="Open Location", bootstyle="secondary", command=self.open_selected_location).pack(side='left', padx=4)

        # bottom: log
        log_frame = tb.Labelframe(self.root, text="Log")
        log_frame.pack(fill='x', padx=8, pady=(0,8))
        self.log_box = tk.Text(log_frame, height=6, state='disabled')
        self.log_box.pack(fill='both', padx=6, pady=6)

    # ------------------ Utilities ------------------
    def log(self, *parts):
        self.log_box.config(state='normal')
        self.log_box.insert('end', ' '.join(map(str, parts)) + '\n')
        self.log_box.see('end')
        self.log_box.config(state='disabled')

    def browse_local(self):
        f = filedialog.askopenfilename(title="Select video", filetypes=[("Video files", "*.mp4 *.mov *.mkv *.avi *.webm"), ("All files", "*.*")])
        if f:
            self.current_src = f
            self.current_video_hash = os.path.splitext(os.path.basename(f))[0]
            self.last_downloaded = f
            self.log("Loaded local file:", f)
            self.info_label.config(text=f"Loaded: {f}")
            self.refresh_drafts()

    def download_url(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("Input required", "Paste a video URL first.")
            return

        def worker():
            try:
                self.log("Fetching info...")
                info = self.downloader.fetch_info(url)
                title = info.get("title", "video")
                self.log(f"Downloading: {title}")
                path = self.downloader.download_best(url, title_hint=title)
                self.current_src = path
                self.current_video_hash = os.path.splitext(os.path.basename(path))[0]
                self.last_downloaded = path
                self.info_label.config(text=f"Downloaded: {path}")
                self.log("Downloaded to:", path)
                self.refresh_drafts()
            except Exception as e:
                self.log("Download error:", e)
                messagebox.showerror("Download error", str(e))

        threading.Thread(target=worker, daemon=True).start()

    def browse_music(self):
        f = filedialog.askopenfilename(title="Select music", filetypes=[("Audio", "*.mp3 *.m4a *.wav"), ("All files", "*.*")])
        if f:
            self.bg_music_var.set(f)

    def create_single_reel(self):
        if not self.current_src:
            messagebox.showwarning("No source", "Please browse or download a video first.")
            return
        try:
            start = float(self.start_var.get())
        except Exception:
            start = 0.0
        duration = int(self.duration_var.get())
        overlay = self.overlay_text_var.get().strip() or None
        bg = self.bg_music_var.get().strip() or None
        video_hash = self.current_video_hash

        def worker():
            try:
                self.log("Creating reel...")
                meta = self.editor.create_single_reel(self.current_src, start=start, duration=duration,
                                                      overlay_text=overlay, bg_music=bg, video_hash=video_hash)
                self.reel_drafts.append(meta)
                self.log("Draft created:", meta["path"])
                self.refresh_drafts()
            except Exception as e:
                self.log("Create reel error:", e)
                messagebox.showerror("Error", str(e))

        threading.Thread(target=worker, daemon=True).start()

    def split_into_reels(self):
        if not self.current_src:
            messagebox.showwarning("No source", "Please browse or download a video first.")
            return
        dur = int(self.duration_var.get())
        overlap = float(self.overlap_var.get() or 0.0)
        video_hash = self.current_video_hash

        def worker():
            try:
                self.log("Splitting into drafts...")
                metas = self.editor.split_into_reels(self.current_src, reel_duration=dur, overlap=overlap, video_hash=video_hash,
                                                     overlay_text=self.overlay_text_var.get().strip() or None,
                                                     bg_music=self.bg_music_var.get().strip() or None)
                self.reel_drafts.extend(metas)
                self.log(f"Created {len(metas)} drafts")
                self.refresh_drafts()
            except Exception as e:
                self.log("Split error:", e)
                messagebox.showerror("Error", str(e))

        threading.Thread(target=worker, daemon=True).start()

    def refresh_drafts(self):
        # load drafts from temp folder for current video
        self.reel_listbox.delete(0, 'end')
        self.reel_drafts = []
        if not self.current_src:
            return
        temp_folder = os.path.join(self.temp_root, self.current_video_hash)
        if not os.path.exists(temp_folder):
            return
        # find mp4 files in folder
        files = sorted(Path(temp_folder).glob("*.mp4"))
        for f in files:
            thumb = str(f) + ".thumb.jpg"
            meta = {"path": str(f), "thumb": thumb if os.path.exists(thumb) else "", "name": os.path.basename(f)}
            self.reel_drafts.append(meta)
            self.reel_listbox.insert('end', meta["name"])

    def on_reel_select(self, event):
        sel = self.reel_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        meta = self.reel_drafts[idx]
        self.show_preview(meta)

    def show_preview(self, meta):
        self.preview_canvas.delete('all')
        thumb = meta.get("thumb")
        if thumb and os.path.exists(thumb):
            try:
                img = Image.open(thumb)
                img.thumbnail((300, 540))
                self.preview_img = ImageTk.PhotoImage(img)
                self.preview_canvas.create_image(150, 270, image=self.preview_img)
            except Exception as e:
                self.log("Thumb load error:", e)
        else:
            # generate a quick thumb using ffmpeg (blocking but quick)
            try:
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
                tmp.close()
                FFmpegWrapper = __import__("editor.ffmpeg_wrapper", fromlist=["FFmpegWrapper"]).FFmpegWrapper
                try:
                    FFmpegWrapper.create_thumbnail(meta["path"], tmp.name, time=0.5, width=360)
                    img = Image.open(tmp.name)
                    img.thumbnail((300, 540))
                    self.preview_img = ImageTk.PhotoImage(img)
                    self.preview_canvas.create_image(150, 270, image=self.preview_img)
                finally:
                    try:
                        os.unlink(tmp.name)
                    except Exception:
                        pass
            except Exception as e:
                self.preview_canvas.create_text(150, 270, text="No preview", fill="white")

        # metadata
        size = os.path.getsize(meta["path"])
        dur = 0
        try:
            dur = FFmpegWrapper.get_duration(meta["path"])
        except Exception:
            pass
        text = f"Name: {meta.get('name')}\nSize: {round(size/1024/1024,2)} MB\nDuration: {dur:.1f}s\nPath: {meta.get('path')}"
        self.meta_label.config(text=text)

    def export_selected(self):
        sel = self.reel_listbox.curselection()
        if not sel:
            messagebox.showwarning("Select", "Select a draft to export")
            return
        idx = sel[0]
        meta = self.reel_drafts[idx]
        dest = filedialog.askdirectory(initialdir=self.output_folder, title="Select export folder")
        if not dest:
            return

        def worker():
            try:
                out = self.editor.export_reel(meta, dest)
                self.log("Exported to:", out)
                messagebox.showinfo("Exported", f"Exported: {out}")
            except Exception as e:
                self.log("Export error:", e)
                messagebox.showerror("Error", str(e))

        threading.Thread(target=worker, daemon=True).start()

    def delete_selected(self):
        sel = self.reel_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        meta = self.reel_drafts[idx]
        try:
            os.remove(meta["path"])
            if meta.get("thumb") and os.path.exists(meta.get("thumb")):
                os.remove(meta.get("thumb"))
            self.log("Deleted:", meta["path"])
            self.refresh_drafts()
        except Exception as e:
            self.log("Delete error:", e)
            messagebox.showerror("Error", str(e))

    def open_temp_folder(self):
        if not self.current_video_hash:
            return
        folder = os.path.join(self.temp_root, self.current_video_hash)
        if os.path.exists(folder):
            if os.name == 'nt':
                os.startfile(folder)
            else:
                subprocess.Popen(["xdg-open", folder])
        else:
            messagebox.showinfo("No drafts", "No drafts present for current video.")

    def play_selected(self):
        sel = self.reel_listbox.curselection()
        if not sel:
            return
        meta = self.reel_drafts[sel[0]]
        path = meta.get("path")
        if not path or not os.path.exists(path):
            messagebox.showerror("Not found", "File not found")
            return
        # open with default player
        if os.name == 'nt':
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])

    def open_selected_location(self):
        sel = self.reel_listbox.curselection()
        if not sel:
            return
        meta = self.reel_drafts[sel[0]]
        folder = os.path.dirname(meta.get("path"))
        if os.path.exists(folder):
            if os.name == 'nt':
                os.startfile(folder)
            else:
                subprocess.Popen(["xdg-open", folder])
