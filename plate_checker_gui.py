"""Florida Plate Checker - desktop app (tkinter)."""

import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

import plate_core as core

SOURCES = [
    "2 Letters (LL)",
    "2 Digits (DD)",
    "Letter + Digit (LD)",
    "Digit + Letter (DL)",
    "Custom pattern",
    "Dictionary file",
]
PRESETS = {0: "LL", 1: "DD", 2: "LD", 3: "DL"}
LOG_MAX_LINES = 3000

# Palette
NAVY = "#0F2A5C"
BLUE = "#2468E8"
BLUE_DARK = "#1A4FBF"
BG = "#F3F5F9"
CARD = "#FFFFFF"
BORDER = "#DDE2EA"
TEXT = "#1F2937"
MUTED = "#6B7280"
GREEN = "#16A34A"
RED = "#DC2626"
AMBER = "#D97706"

FONT = "Segoe UI"
MONO = "Consolas"


def resource_path(name):
    """Bundled file (icon, logo): works from source and inside the .exe."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(core.APP_NAME)
        self.configure(bg=BG)
        scale = self.winfo_fpixels("1i") / 96
        self.geometry(f"{int(900 * scale)}x{int(800 * scale)}")
        self.minsize(int(800 * scale), int(700 * scale))
        try:
            self.iconbitmap(resource_path("app.ico"))
        except tk.TclError:
            pass

        self.events = queue.Queue()
        self.stop_event = threading.Event()
        self.thread = None
        self.output_file = None
        self.available = []
        self.total = self.done = self.taken = self.errors = 0
        self.status_text = "Ready."

        self._style()
        self._build_ui()
        self._on_source_change()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(100, self._poll)

    # ---------------------------------------------------------------- style
    def _style(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        base = (FONT, 10)
        s.configure(".", font=base, background=CARD, foreground=TEXT)
        s.configure("TFrame", background=CARD)
        s.configure("TLabel", background=CARD, foreground=TEXT)
        s.configure("Muted.TLabel", background=CARD, foreground=MUTED)

        for name in ("TCombobox", "TEntry", "TSpinbox"):
            s.configure(name, fieldbackground="#FFFFFF", foreground=TEXT,
                        bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER,
                        padding=5)
        s.configure("TCombobox", arrowcolor=MUTED, background=CARD)
        s.configure("TSpinbox", arrowcolor=MUTED, background=CARD)
        s.map("TCombobox", fieldbackground=[("disabled", "#EEF0F4"), ("readonly", "#FFFFFF")],
              foreground=[("disabled", "#9CA3AF")], bordercolor=[("focus", BLUE)])
        s.map("TEntry", fieldbackground=[("disabled", "#EEF0F4")],
              foreground=[("disabled", "#9CA3AF")], bordercolor=[("focus", BLUE)])
        s.map("TSpinbox", fieldbackground=[("disabled", "#EEF0F4")],
              foreground=[("disabled", "#9CA3AF")], bordercolor=[("focus", BLUE)])
        self.option_add("*TCombobox*Listbox.font", (FONT, 10))
        self.option_add("*TCombobox*Listbox.selectBackground", BLUE)

        def button(style, bg, fg, hover, disabled_bg="#C7CEDA", border=None):
            s.configure(style, font=(FONT, 10, "bold"), background=bg, foreground=fg,
                        borderwidth=1, bordercolor=border or bg, lightcolor=bg, darkcolor=bg,
                        focuscolor=bg, padding=(18, 8), relief="flat")
            s.map(style,
                  background=[("disabled", disabled_bg), ("active", hover)],
                  foreground=[("disabled", "#FFFFFF")],
                  bordercolor=[("disabled", disabled_bg), ("active", hover)],
                  lightcolor=[("disabled", disabled_bg), ("active", hover)],
                  darkcolor=[("disabled", disabled_bg), ("active", hover)])

        button("Accent.TButton", BLUE, "#FFFFFF", BLUE_DARK)
        button("Danger.TButton", RED, "#FFFFFF", "#B91C1C")
        s.configure("Ghost.TButton", font=(FONT, 10), background=CARD, foreground=TEXT,
                    bordercolor=BORDER, lightcolor=CARD, darkcolor=CARD, focuscolor=CARD,
                    padding=(14, 7), relief="flat")
        s.map("Ghost.TButton", background=[("active", "#EEF2F8")],
              bordercolor=[("active", BLUE)])

        s.configure("Green.Horizontal.TProgressbar", troughcolor="#E3E8F0", background=GREEN,
                    bordercolor="#E3E8F0", lightcolor=GREEN, darkcolor=GREEN, thickness=10)

    # ------------------------------------------------------------------- UI
    def _card(self, parent, **grid):
        frame = tk.Frame(parent, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        return frame

    def _build_ui(self):
        # Header bar
        header = tk.Frame(self, bg=NAVY)
        header.pack(fill="x")
        try:
            self.logo = tk.PhotoImage(file=resource_path("logo.png"))
            tk.Label(header, image=self.logo, bg=NAVY).pack(side="left", padx=(20, 12), pady=12)
        except tk.TclError:
            pass
        titles = tk.Frame(header, bg=NAVY)
        titles.pack(side="left", pady=12)
        tk.Label(titles, text="Florida Plate Checker", bg=NAVY, fg="white",
                 font=(FONT, 17, "bold")).pack(anchor="w")
        tk.Label(titles, text="Find available personalized license plates", bg=NAVY,
                 fg="#B8C7E8", font=(FONT, 10)).pack(anchor="w")
        tk.Label(header, text=f"v{core.APP_VERSION}", bg=NAVY, fg="#7E93C0",
                 font=(FONT, 9)).pack(side="right", padx=20)

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=20, pady=16)

        # Settings card
        card = self._card(body)
        card.pack(fill="x")
        inner = ttk.Frame(card, padding=(16, 12))
        inner.pack(fill="x")
        inner.columnconfigure(1, weight=1, uniform="c")
        inner.columnconfigure(3, weight=1, uniform="c")

        self.source = tk.StringVar(value=SOURCES[0])
        self.pattern = tk.StringVar(value="LLL")
        self.min_len = tk.IntVar(value=1)
        self.max_len = tk.IntVar(value=7)
        self.count = tk.StringVar(value="all")
        self.mode = tk.StringVar(value="Sequential")
        self.workers = tk.IntVar(value=5)
        self.pause = tk.DoubleVar(value=3.0)

        def label(text, row, col):
            ttk.Label(inner, text=text, style="Muted.TLabel").grid(
                row=row, column=col, sticky="w", padx=(0, 10), pady=6)

        label("Plates to check", 0, 0)
        combo = ttk.Combobox(inner, textvariable=self.source, values=SOURCES, state="readonly")
        combo.grid(row=0, column=1, sticky="ew", padx=(0, 24), pady=6)
        combo.bind("<<ComboboxSelected>>", lambda e: self._on_source_change())

        label("Custom pattern (L = letter, D = digit)", 0, 2)
        self.pattern_entry = ttk.Entry(inner, textvariable=self.pattern)
        self.pattern_entry.grid(row=0, column=3, sticky="ew", pady=6)

        label("Dictionary: min length", 1, 0)
        self.min_spin = ttk.Spinbox(inner, from_=1, to=7, textvariable=self.min_len)
        self.min_spin.grid(row=1, column=1, sticky="ew", padx=(0, 24), pady=6)
        label("Dictionary: max length", 1, 2)
        self.max_spin = ttk.Spinbox(inner, from_=1, to=7, textvariable=self.max_len)
        self.max_spin.grid(row=1, column=3, sticky="ew", pady=6)

        label("How many ('all' or a number)", 2, 0)
        ttk.Entry(inner, textvariable=self.count).grid(
            row=2, column=1, sticky="ew", padx=(0, 24), pady=6)
        label("Order", 2, 2)
        ttk.Combobox(inner, textvariable=self.mode, values=["Sequential", "Random"],
                     state="readonly").grid(row=2, column=3, sticky="ew", pady=6)

        label("Parallel requests (1-8)", 3, 0)
        ttk.Spinbox(inner, from_=1, to=8, textvariable=self.workers).grid(
            row=3, column=1, sticky="ew", padx=(0, 24), pady=6)
        label("Pause between batches (sec)", 3, 2)
        ttk.Spinbox(inner, from_=0, to=30, increment=0.5, textvariable=self.pause).grid(
            row=3, column=3, sticky="ew", pady=6)

        # Action bar
        bar = tk.Frame(body, bg=BG)
        bar.pack(fill="x", pady=(14, 10))
        self.start_btn = ttk.Button(bar, text="Start scan", style="Accent.TButton",
                                    command=self._start)
        self.start_btn.pack(side="left")
        self.stop_btn = ttk.Button(bar, text="Stop", style="Danger.TButton",
                                   command=self._stop, state="disabled")
        self.stop_btn.pack(side="left", padx=8)
        ttk.Button(bar, text="Open results folder", style="Ghost.TButton",
                   command=self._open_results).pack(side="right")
        ttk.Button(bar, text="Copy all available", style="Ghost.TButton",
                   command=self._copy).pack(side="right", padx=8)

        # Progress + status
        self.progress = ttk.Progressbar(body, mode="determinate",
                                        style="Green.Horizontal.TProgressbar")
        self.progress.pack(fill="x")
        self.status_var = tk.StringVar(value=self.status_text)
        self.status_label = tk.Label(body, textvariable=self.status_var, bg=BG, fg=MUTED,
                                     font=(FONT, 9), anchor="w")
        self.status_label.pack(fill="x", pady=(4, 8))

        # Stat tiles
        tiles = tk.Frame(body, bg=BG)
        tiles.pack(fill="x")
        self.stat_vars = {}
        for i, (key, title, color) in enumerate((
                ("checked", "CHECKED", TEXT), ("available", "AVAILABLE", GREEN),
                ("taken", "TAKEN", RED), ("errors", "ERRORS", AMBER))):
            tiles.columnconfigure(i, weight=1, uniform="t")
            tile = self._card(tiles)
            tile.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 6, 0))
            var = tk.StringVar(value="0")
            self.stat_vars[key] = var
            tk.Label(tile, textvariable=var, bg=CARD, fg=color,
                     font=(FONT, 20, "bold")).pack(pady=(8, 0))
            tk.Label(tile, text=title, bg=CARD, fg=MUTED, font=(FONT, 8, "bold")).pack(pady=(0, 8))

        # Results + activity
        panes = tk.Frame(body, bg=BG)
        panes.pack(fill="both", expand=True, pady=(12, 0))
        panes.columnconfigure(1, weight=1)
        panes.rowconfigure(1, weight=1)

        tk.Label(panes, text="Available plates  (double-click to copy)", bg=BG, fg=TEXT,
                 font=(FONT, 10, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 4))
        tk.Label(panes, text="Activity", bg=BG, fg=TEXT,
                 font=(FONT, 10, "bold")).grid(row=0, column=1, sticky="w", padx=(12, 0), pady=(0, 4))

        left = self._card(panes)
        left.grid(row=1, column=0, sticky="ns")
        self.avail_list = tk.Listbox(
            left, width=20, exportselection=False, font=(MONO, 12), bd=0, relief="flat",
            highlightthickness=0, bg=CARD, fg=GREEN, activestyle="none",
            selectbackground="#DCE8FF", selectforeground=TEXT)
        sb1 = ttk.Scrollbar(left, command=self.avail_list.yview)
        sb1.pack(side="right", fill="y")
        self.avail_list.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=6)
        self.avail_list.config(yscrollcommand=sb1.set)
        self.avail_list.bind("<Double-Button-1>", self._copy_selected)

        right = self._card(panes)
        right.grid(row=1, column=1, sticky="nsew", padx=(12, 0))
        self.log = tk.Text(right, height=10, state="disabled", wrap="word", bd=0, relief="flat",
                           highlightthickness=0, font=(MONO, 10), bg="#FBFCFE", padx=10, pady=8)
        sb2 = ttk.Scrollbar(right, command=self.log.yview)
        sb2.pack(side="right", fill="y")
        self.log.pack(side="left", fill="both", expand=True)
        self.log.config(yscrollcommand=sb2.set)
        self.log.tag_config("AVAILABLE", foreground=GREEN)
        self.log.tag_config("TAKEN", foreground=RED)
        self.log.tag_config("ERROR", foreground=AMBER)
        self.log.tag_config("INFO", foreground=MUTED)

        tk.Label(body, bg=BG, fg=MUTED, font=(FONT, 8), anchor="w", justify="left",
                 text="Unofficial tool, not affiliated with FLHSMV. Always confirm availability "
                      "on the official site before ordering.").pack(fill="x", pady=(10, 0))

    def _on_source_change(self):
        idx = SOURCES.index(self.source.get())
        self.pattern_entry.config(state="normal" if idx == 4 else "disabled")
        dict_state = "normal" if idx == 5 else "disabled"
        self.min_spin.config(state=dict_state)
        self.max_spin.config(state=dict_state)

    # ------------------------------------------------------------- actions
    def _build_plates(self):
        idx = SOURCES.index(self.source.get())
        if idx in PRESETS:
            pool = core.generate_pattern_plates(PRESETS[idx])
            label = PRESETS[idx]
        elif idx == 4:
            label = core.clean_pattern(self.pattern.get(), default="LL")
            pool = core.generate_pattern_plates(label)
        else:
            lo, hi = int(self.min_len.get()), int(self.max_len.get())
            if lo > hi:
                lo, hi = hi, lo
            try:
                pool = core.load_dictionary(lo, hi)
            except FileNotFoundError:
                raise ValueError(
                    "plate_dictionary.txt wasn't found. It needs to be in the same "
                    f"folder as the app:\n{core.app_dir()}"
                )
            if not pool:
                raise ValueError("No dictionary words matched that length range.")
            label = f"Dictionary ({lo}-{hi} chars)"

        try:
            n = core.parse_count(self.count.get(), len(pool))
        except ValueError:
            raise ValueError("'How many' must be 'all' or a whole number.")
        randomize = self.mode.get() == "Random"
        return core.select_plates(pool, n, randomize), label, randomize

    def _start(self):
        try:
            plates, label, randomize = self._build_plates()
            workers = max(1, min(8, int(self.workers.get())))
            pause = max(0.0, float(self.pause.get()))
        except (ValueError, tk.TclError) as exc:
            messagebox.showerror("Can't start", str(exc))
            return

        if len(plates) > 2000 and not messagebox.askyesno(
            "Large scan",
            f"This will check {len(plates):,} plates, which can take a long time "
            "and may get your connection temporarily blocked by the site.\n\nContinue?",
        ):
            return

        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_file = os.path.join(core.results_dir(), f"available_plates_{stamp}.txt")
        with open(self.output_file, "w", encoding="utf-8") as f:
            f.write("Florida DHSMV Available Plates\n")
            f.write(f"Source: {label}\n")
            f.write(f"Mode: {'Random' if randomize else 'Sequential'}\n")
            f.write(f"Count: {len(plates)}\n")
            f.write(f"Date: {datetime.now():%Y-%m-%d %H:%M:%S}\n")
            f.write("-" * 30 + "\n")

        self.available.clear()
        self.avail_list.delete(0, "end")
        self.log.config(state="normal")
        self.log.delete("1.0", "end")
        self.log.config(state="disabled")
        self.total, self.done, self.taken, self.errors = len(plates), 0, 0, 0
        self.progress.config(maximum=self.total, value=0)
        self._log(f"Saving results to {self.output_file}", "INFO")
        self._update_summary("Scanning...")

        self.stop_event = threading.Event()
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.thread = threading.Thread(
            target=self._scan, args=(plates, workers, pause, self.stop_event), daemon=True
        )
        self.thread.start()

    def _scan(self, plates, workers, pause, stop_event):
        try:
            core.run_scan(
                plates,
                on_result=lambda p, s: self.events.put(("result", p, s)),
                stop_event=stop_event,
                on_status=lambda m: self.events.put(("status", m)),
                workers=workers,
                batch_pause=(pause * 0.6, pause * 1.4),
            )
        except Exception as exc:  # never let the thread die silently
            self.events.put(("status", f"Unexpected error: {exc}"))
        finally:
            self.events.put(("done",))

    def _stop(self):
        self.stop_event.set()
        self.stop_btn.config(state="disabled")
        self._update_summary("Stopping after current requests...")

    def _copy(self):
        if not self.available:
            messagebox.showinfo("Nothing to copy", "No available plates found yet.")
            return
        self.clipboard_clear()
        self.clipboard_append("\n".join(self.available))
        self._update_summary(f"Copied {len(self.available)} plate(s) to the clipboard.")

    def _copy_selected(self, _event=None):
        sel = self.avail_list.curselection()
        if sel:
            plate = self.avail_list.get(sel[0])
            self.clipboard_clear()
            self.clipboard_append(plate)
            self._update_summary(f"Copied {plate}")

    def _open_results(self):
        folder = core.results_dir()
        if sys.platform.startswith("win"):
            os.startfile(folder)  # noqa: S606 (Windows only)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", folder])
        else:
            subprocess.Popen(["xdg-open", folder])

    def _on_close(self):
        self.stop_event.set()
        self.destroy()

    # -------------------------------------------------------- event pump
    def _poll(self):
        try:
            for _ in range(200):
                self._handle(self.events.get_nowait())
        except queue.Empty:
            pass
        self.after(100, self._poll)

    def _handle(self, event):
        kind = event[0]
        if kind == "result":
            _, plate, status = event
            self.done += 1
            if status == "AVAILABLE":
                self.available.append(plate)
                self.avail_list.insert("end", plate)
                self.avail_list.see("end")
                with open(self.output_file, "a", encoding="utf-8") as f:
                    f.write(plate + "\n")
            elif status == "TAKEN":
                self.taken += 1
            else:
                self.errors += 1
            self._log(f"{status:<10} {plate}", status)
            self.progress.config(value=self.done)
            self._update_summary()
        elif kind == "status":
            self._update_summary(event[1])
        elif kind == "done":
            self._finish()

    def _finish(self):
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        if self.output_file and os.path.exists(self.output_file):
            with open(self.output_file, "a", encoding="utf-8") as f:
                f.write("-" * 30 + "\n")
                f.write(f"Total Available: {len(self.available)}\n")
                f.write(f"Total Taken: {self.taken}\n")
                f.write(f"Total Errors: {self.errors}\n")
        stopped = self.done < self.total
        self._update_summary("Stopped." if stopped else "Finished.")
        self._log(f"{'Stopped' if stopped else 'Finished'}. Results saved to {self.output_file}", "INFO")

    def _update_summary(self, message=None):
        if message:
            self.status_text = message
        self.stat_vars["checked"].set(f"{self.done}/{self.total}")
        self.stat_vars["available"].set(str(len(self.available)))
        self.stat_vars["taken"].set(str(self.taken))
        self.stat_vars["errors"].set(str(self.errors))

        text, color = self.status_text, MUTED
        if self.done >= 25 and self.errors / max(1, self.done) > 0.5:
            text += "  -  Lots of errors: the site may be blocking you. Stop and try again later."
            color = RED
        self.status_var.set(text)
        self.status_label.config(fg=color)

    def _log(self, text, tag):
        self.log.config(state="normal")
        self.log.insert("end", text + "\n", tag)
        if int(self.log.index("end-1c").split(".")[0]) > LOG_MAX_LINES:
            self.log.delete("1.0", "500.0")
        self.log.see("end")
        self.log.config(state="disabled")


if __name__ == "__main__":
    try:  # crisp text on high-DPI Windows screens
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    App().mainloop()
