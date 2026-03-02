from __future__ import annotations

import tkinter as tk


class ConnectionsView(tk.Frame):
    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent)

        title = tk.Label(self, text="Connections", font=("Segoe UI", 16, "bold"))
        title.pack(anchor="w")

        hint = tk.Label(self, text="Manage connections (e.g., Creo, file sources).", fg="gray")
        hint.pack(anchor="w", pady=(6, 0))