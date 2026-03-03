from __future__ import annotations

import tkinter as tk
from typing import Callable

class LeftNav(tk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        *,
        views: list[str],
        on_select_view: Callable[[str], None],
        initial_expanded: bool = False,
        width_expanded: int = 200,
        width_collapsed: int = 52,
        compact_icons: dict[str, str] | None = None,
    ) -> None:
        super().__init__(master, bd=1, relief="solid")

        self._views = views
        self._on_select_view = on_select_view
        self._expanded = initial_expanded
        self._width_expanded = width_expanded
        self._width_collapsed = width_collapsed
        self._compact_icons = compact_icons or {}

        self._buttons: dict[str, tk.Button] = {}

        self.grid_propagate(False)
        self.grid_rowconfigure(99, weight=1)
        self.grid_columnconfigure(0, weight=1)

        header = tk.Frame(self, padx=8, pady=8)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(1, weight=1)

        self._toggle_btn = tk.Button(header, text="⟨⟨", width=4, command=self.toggle)
        self._toggle_btn.grid(row=0, column=0, sticky="w")

        self._title = tk.Label(header, text="Navigation", font=("Segoe UI", 10, "bold"))
        self._title.grid(row=0, column=1, sticky="w", padx=(8, 0))

        self._btn_container = tk.Frame(self, padx=6, pady=6)
        self._btn_container.grid(row=1, column=0, sticky="nsew")
        self._btn_container.grid_columnconfigure(0, weight=1)

        for idx, name in enumerate(self._views):
            btn = tk.Button(
                self._btn_container,
                text=name,
                anchor="w",
                command=lambda n=name: self._on_select_view(n),
            )
            btn.grid(row=idx, column=0, sticky="ew", pady=2)
            self._buttons[name] = btn

        self._apply_state()

    def set_active(self, view_name: str) -> None:
        for name, btn in self._buttons.items():
            btn.configure(relief="sunken" if name == view_name else "raised")

    def toggle(self) -> None:
        self._expanded = not self._expanded
        self._apply_state()

    def _apply_state(self) -> None:
        if self._expanded:
            self.configure(width=self._width_expanded, height=1)
            self._toggle_btn.configure(text="⟨⟨")
            self._title.configure(text="Navigation")
            for name, btn in self._buttons.items():
                btn.configure(text=name, anchor="w")
        else:
            self.configure(width=self._width_collapsed, height=1)
            self._toggle_btn.configure(text="⟩⟩")
            self._title.configure(text="")
            for name, btn in self._buttons.items():
                btn.configure(text=self._compact_icons.get(name, name[:1]), anchor="center")