from __future__ import annotations

import tkinter as tk
from typing import Callable

from aas_creo_bridge.app.logging import AppLogger, LogEntry, LogLevel

class StatusBar(tk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        *,
        on_clear_log: Callable[[], None],
        on_show_log: Callable[[], None],
        initial_message: str = "Ready.",
    ) -> None:
        super().__init__(master, bd=1, relief="solid", padx=8, pady=6)

        self._last_log_var = tk.StringVar(value=initial_message)

        self.grid_columnconfigure(1, weight=1)

        self._status_canvas = tk.Canvas(self, width=14, height=14, highlightthickness=0)
        self._status_canvas.grid(row=0, column=0, sticky="w")

        self._status_dot = self._status_canvas.create_oval(
            2, 2, 12, 12,
            fill="#9e9e9e",
            outline="#6e6e6e",
        )

        self._last_log_label = tk.Label(self, textvariable=self._last_log_var, anchor="w")
        self._last_log_label.grid(row=0, column=1, sticky="ew", padx=(8, 8))

        self._clear_btn = tk.Button(self, text="Clear", command=on_clear_log, width=8)
        self._clear_btn.grid(row=0, column=2, sticky="e", padx=(0, 6))

        self._show_btn = tk.Button(self, text="Show Log", command=on_show_log, width=10)
        self._show_btn.grid(row=0, column=3, sticky="e")

    def subscribe_to_logger(self, logger: AppLogger) -> None:
        """
        Subscribe this status bar to logger updates so the "last message" (and dot)
        follow the most recent log entry automatically.
        """
        logger.subscribe(self.on_log_entry)

    def on_log_entry(self, entry: LogEntry) -> None:
        # Keep it short in the status bar.
        self.set_last_message(entry.message)

        # Optional: reflect severity via dot color.
        if entry.level == LogLevel.ERROR:
            self.set_status("error")
        elif entry.level == LogLevel.WARNING:
            self.set_status("warning")
        else:
            # INFO / VERBOSE -> neutral
            self.set_status("idle")

    def set_last_message(self, message: str) -> None:
        self._last_log_var.set(message)

    def set_status(self, status: str) -> None:
        """
        Supported values:
        - idle (gray)
        - ok (green)
        - busy (blue)
        - warning (amber)
        - error (red)
        """
        colors = {
            "idle": ("#9e9e9e", "#6e6e6e"),
            "ok": ("#2e7d32", "#1b5e20"),
            "busy": ("#1565c0", "#0d47a1"),
            "warning": ("#f9a825", "#f57f17"),
            "error": ("#c62828", "#8e0000"),
        }
        fill, outline = colors.get(status, ("#9e9e9e", "#6e6e6e"))
        self._status_canvas.itemconfigure(self._status_dot, fill=fill, outline=outline)