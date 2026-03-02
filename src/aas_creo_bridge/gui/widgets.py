from __future__ import annotations

import tkinter as tk

from aas_creo_bridge.app.logging import AppLogger, LogEntry, LogLevel


class LeftNav(tk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        *,
        views: list[str],
        on_select_view: callable,
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


class StatusBar(tk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        *,
        on_clear_log: callable,
        on_show_log: callable,
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


class LogWindow:
    def __init__(self, root: tk.Tk, *, title: str = "Log") -> None:
        self._root = root
        self._win: tk.Toplevel | None = None
        self._text: tk.Text | None = None
        self._title = title

    def is_open(self) -> bool:
        return self._win is not None and self._win.winfo_exists()

    def show(self, lines: list[str]) -> None:
        if self.is_open():
            self._win.lift()
            return

        win = tk.Toplevel(self._root)
        win.title(self._title)
        win.geometry("700x400")
        win.minsize(500, 300)
        self._win = win

        win.grid_rowconfigure(0, weight=1)
        win.grid_columnconfigure(0, weight=1)

        text = tk.Text(win, wrap="word")
        text.grid(row=0, column=0, sticky="nsew")
        self._text = text

        scrollbar = tk.Scrollbar(win, command=text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        text.configure(yscrollcommand=scrollbar.set)

        text.insert("end", "\n".join(lines) + ("\n" if lines else ""))
        text.configure(state="disabled")

        def _on_close() -> None:
            self._text = None
            self._win = None
            win.destroy()

        win.protocol("WM_DELETE_WINDOW", _on_close)

    def append(self, line: str) -> None:
        if self._text is None:
            return
        self._text.configure(state="normal")
        self._text.insert("end", line + "\n")
        self._text.see("end")
        self._text.configure(state="disabled")

    def clear(self) -> None:
        if self._text is None:
            return
        self._text.configure(state="normal")
        self._text.delete("1.0", "end")
        self._text.configure(state="disabled")