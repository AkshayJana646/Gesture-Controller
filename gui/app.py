import tkinter as tk
from tkinter import messagebox
import threading
import os
import cv2
from PIL import Image, ImageTk

from core.config import Config
from core.detector import GestureDetector


# Color palette
BG      = "#0d0d0d"
PANEL   = "#1a1a1a"
BORDER  = "#2a2a2a"
GREEN   = "#00ff88"
RED     = "#ff4455"
YELLOW  = "#ffd700"
TEXT    = "#ffffff"
MUTED   = "#666666"
DIMMED  = "#333333"


# Gesture to emoji mapping for display
GESTURE_ICONS = {
    "Fist":        "✊",
    "Open Hand":   "✋",
    "Thumbs Up":   "👍",
    "Thumbs Down": "👎",
    "Peace":       "✌️",
    "Point":       "☝️",
    "—":           " ",
}


class GestureApp(tk.Tk):

    def __init__(self):
        super().__init__()
        self.cfg = Config()
        self.detector = None
        self._preview_running = False
        self._history = []   # list of last 5 gesture strings

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._poll()

    def _build_ui(self):
        self.title("Gesture Controller")
        self.configure(bg=BG)

        # Fullscreen
        self.attributes("-fullscreen", True)
        self.bind("<Escape>", lambda e: self._on_close())

        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()

        # ── Top bar ───────────────────────────────────────────────────
        topbar = tk.Frame(self, bg=PANEL, height=56)
        topbar.pack(fill=tk.X, side=tk.TOP)
        topbar.pack_propagate(False)

        tk.Label(topbar, text="✋  GESTURE CONTROLLER",
                 font=("Segoe UI", 13, "bold"),
                 bg=PANEL, fg=TEXT).pack(side=tk.LEFT, padx=24)

        # Status dot + label
        self._status_dot = tk.Label(topbar, text="●",
                                    font=("Segoe UI", 16),
                                    bg=PANEL, fg=RED)
        self._status_dot.pack(side=tk.RIGHT, padx=(0, 8))
        self._status_label = tk.Label(topbar, text="STOPPED",
                                      font=("Segoe UI", 10, "bold"),
                                      bg=PANEL, fg=RED)
        self._status_label.pack(side=tk.RIGHT)

        self._fps_label = tk.Label(topbar, text="",
                                   font=("Courier New", 11),
                                   bg=PANEL, fg=MUTED)
        self._fps_label.pack(side=tk.RIGHT, padx=24)

        # ── Main content area ─────────────────────────────────────────
        content = tk.Frame(self, bg=BG)
        content.pack(fill=tk.BOTH, expand=True)

        # Left panel — camera feed
        left = tk.Frame(content, bg=BG)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(24, 12), pady=24)

        cam_label = tk.Label(left, text="CAMERA FEED",
                             font=("Segoe UI", 9, "bold"),
                             bg=BG, fg=MUTED)
        cam_label.pack(anchor=tk.W, pady=(0, 8))

        # Camera feed canvas
        self._cam_frame = tk.Label(left, bg=DIMMED,
                                   text="Camera feed will appear here\nwhen running",
                                   font=("Segoe UI", 12),
                                   fg=MUTED, compound=tk.CENTER)
        self._cam_frame.pack(fill=tk.BOTH, expand=True)

        # Right panel — controls and info
        right = tk.Frame(content, bg=BG, width=320)
        right.pack(side=tk.RIGHT, fill=tk.Y, padx=(12, 24), pady=24)
        right.pack_propagate(False)

        # ── Current gesture card ──────────────────────────────────────
        self._gesture_var = tk.StringVar(value="—")
        self._action_var  = tk.StringVar(value="—")

        gesture_card = tk.Frame(right, bg=PANEL,
                                highlightbackground=BORDER,
                                highlightthickness=1)
        gesture_card.pack(fill=tk.X, pady=(0, 12))

        tk.Label(gesture_card, text="CURRENT GESTURE",
                 font=("Segoe UI", 8, "bold"),
                 bg=PANEL, fg=MUTED).pack(anchor=tk.W, padx=16, pady=(12, 0))

        self._gesture_icon = tk.Label(gesture_card, text=" ",
                                      font=("Segoe UI", 48),
                                      bg=PANEL, fg=TEXT)
        self._gesture_icon.pack(pady=(4, 0))

        self._gesture_name = tk.Label(gesture_card, textvariable=self._gesture_var,
                                      font=("Segoe UI", 18, "bold"),
                                      bg=PANEL, fg=GREEN)
        self._gesture_name.pack()

        tk.Label(gesture_card, text="LAST ACTION",
                 font=("Segoe UI", 8, "bold"),
                 bg=PANEL, fg=MUTED).pack(anchor=tk.W, padx=16, pady=(12, 0))

        self._action_label = tk.Label(gesture_card, textvariable=self._action_var,
                                      font=("Segoe UI", 13),
                                      bg=PANEL, fg=YELLOW)
        self._action_label.pack(pady=(2, 12))

        # ── Buttons ───────────────────────────────────────────────────
        btn_frame = tk.Frame(right, bg=BG)
        btn_frame.pack(fill=tk.X, pady=(0, 12))

        self._start_btn = tk.Button(btn_frame, text="▶  START",
                                    font=("Segoe UI", 11, "bold"),
                                    bg=GREEN, fg="#000000",
                                    activebackground="#00cc66",
                                    padx=0, pady=12, bd=0,
                                    cursor="hand2",
                                    command=self._start)
        self._start_btn.pack(fill=tk.X, pady=(0, 6))

        self._stop_btn = tk.Button(btn_frame, text="■  STOP",
                                   font=("Segoe UI", 11, "bold"),
                                   bg=DIMMED, fg=MUTED,
                                   activebackground=RED,
                                   padx=0, pady=12, bd=0,
                                   cursor="hand2",
                                   state=tk.DISABLED,
                                   command=self._stop)
        self._stop_btn.pack(fill=tk.X)

        # ── Gesture history ───────────────────────────────────────────
        tk.Label(right, text="RECENT GESTURES",
                 font=("Segoe UI", 8, "bold"),
                 bg=BG, fg=MUTED).pack(anchor=tk.W, pady=(12, 6))

        self._history_frame = tk.Frame(right, bg=BG)
        self._history_frame.pack(fill=tk.X)

        self._history_labels = []
        for i in range(5):
            row = tk.Frame(self._history_frame, bg=PANEL,
                           highlightbackground=BORDER,
                           highlightthickness=1)
            row.pack(fill=tk.X, pady=2)
            lbl = tk.Label(row, text="—",
                           font=("Segoe UI", 10),
                           bg=PANEL, fg=DIMMED,
                           anchor=tk.W, padx=12, pady=6)
            lbl.pack(fill=tk.X)
            self._history_labels.append(lbl)

        # ── Gesture map ───────────────────────────────────────────────
        tk.Label(right, text="GESTURE MAP",
                 font=("Segoe UI", 8, "bold"),
                 bg=BG, fg=MUTED).pack(anchor=tk.W, pady=(16, 6))

        gestures = [
            ("✊  Fist",        "Space — Play/Pause"),
            ("✋  Open Hand",   "M — Mute"),
            ("👍  Thumbs Up",   "Volume Up"),
            ("👎  Thumbs Down", "Volume Down"),
            ("✌️  Peace",        "Next Track"),
            ("☝️  Point",        "Prev Track"),
        ]

        for gesture, action in gestures:
            row = tk.Frame(right, bg=PANEL,
                           highlightbackground=BORDER,
                           highlightthickness=1)
            row.pack(fill=tk.X, pady=2)
            tk.Label(row, text=gesture,
                     font=("Segoe UI", 9),
                     bg=PANEL, fg=TEXT,
                     anchor=tk.W, padx=12, pady=5,
                     width=16).pack(side=tk.LEFT)
            tk.Label(row, text=action,
                     font=("Segoe UI", 9),
                     bg=PANEL, fg=MUTED,
                     anchor=tk.W, padx=8, pady=5).pack(side=tk.LEFT)

        # ── Footer ────────────────────────────────────────────────────
        footer = tk.Frame(self, bg=PANEL, height=32)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)
        tk.Label(footer, text="Press ESC to exit",
                 font=("Segoe UI", 8),
                 bg=PANEL, fg=MUTED).pack(side=tk.RIGHT, padx=16)

    # ── Start / Stop ──────────────────────────────────────────────────

    def _start(self):
        if self.detector and self.detector.running:
            return

        if not os.path.exists(self.cfg.MODEL_PATH):
            messagebox.showerror("Model not found",
                f"'{self.cfg.MODEL_PATH}' is missing.\n\nDownload from:\n"
                "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
                "hand_landmarker/float16/latest/hand_landmarker.task")
            return

        self.detector = GestureDetector(self.cfg)
        self.detector.start()
        self._preview_running = True
        threading.Thread(target=self._preview_loop, daemon=True).start()
        self._set_running(True)

    def _stop(self):
        self._preview_running = False
        if self.detector:
            self.detector.stop()
        self._cam_frame.config(image="",
                               text="Camera feed will appear here\nwhen running",
                               fg=MUTED)
        self._set_running(False)

    def _on_close(self):
        self._stop()
        self.destroy()

    def _set_running(self, state: bool):
        if state:
            self._status_dot.config(fg=GREEN)
            self._status_label.config(text="RUNNING", fg=GREEN)
            self._start_btn.config(state=tk.DISABLED, bg=DIMMED, fg=MUTED)
            self._stop_btn.config(state=tk.NORMAL, bg=RED, fg=TEXT)
        else:
            self._status_dot.config(fg=RED)
            self._status_label.config(text="STOPPED", fg=RED)
            self._fps_label.config(text="")
            self._gesture_var.set("—")
            self._action_var.set("—")
            self._gesture_icon.config(text=" ")
            self._start_btn.config(state=tk.NORMAL, bg=GREEN, fg="#000000")
            self._stop_btn.config(state=tk.DISABLED, bg=DIMMED, fg=MUTED)

    # ── Poll detector state every 100ms ──────────────────────────────

    def _poll(self):
        if self.detector and self.detector.running:
            gesture = self.detector.last_gesture
            action  = self.detector.last_action

            self._gesture_var.set(gesture)
            self._action_var.set(action)
            self._fps_label.config(text=f"{int(self.detector.fps)} FPS")

            # Update emoji icon
            icon = GESTURE_ICONS.get(gesture, " ")
            self._gesture_icon.config(text=icon)

            # Update history when a new action fires
            if action != "—" and (not self._history or self._history[0] != action):
                self._history.insert(0, f"{icon}  {gesture}  →  {action}")
                self._history = self._history[:5]
                for i, lbl in enumerate(self._history_labels):
                    if i < len(self._history):
                        lbl.config(text=self._history[i],
                                   fg=GREEN if i == 0 else MUTED)
                    else:
                        lbl.config(text="—", fg=DIMMED)

        self.after(100, self._poll)

    # ── Camera preview embedded in GUI ───────────────────────────────

    def _preview_loop(self):
        while self._preview_running:
            if self.detector and self.detector.frame is not None:
                with self.detector._lock:
                    frame = self.detector.frame.copy()

                # Get current size of the camera panel
                panel_w = self._cam_frame.winfo_width()
                panel_h = self._cam_frame.winfo_height()

                if panel_w > 1 and panel_h > 1:
                    # Resize frame to fit panel while keeping aspect ratio
                    frame_h, frame_w = frame.shape[:2]
                    scale = min(panel_w / frame_w, panel_h / frame_h)
                    new_w = int(frame_w * scale)
                    new_h = int(frame_h * scale)
                    frame = cv2.resize(frame, (new_w, new_h))

                # Convert BGR to RGB for tkinter
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                imgtk = ImageTk.PhotoImage(image=img)

                # Update label on main thread
                self._cam_frame.config(image=imgtk, text="")
                self._cam_frame.image = imgtk

            self._cam_frame.after(30)
