from __future__ import annotations

import tkinter as tk


class SettingsView(tk.Frame):
    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent)

        title = tk.Label(self, text="Settings", font=("Segoe UI", 16, "bold"))
        title.pack(anchor="w")

        hint = tk.Label(self, text="Application configuration.", fg="gray")
        hint.pack(anchor="w", pady=(6, 0))