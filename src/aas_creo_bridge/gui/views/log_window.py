from __future__ import annotations

import tkinter as tk


class LogWindow:
    def __init__(self, root: tk.Tk, *, title: str = "Log") -> None:
        self._root = root
        self._win: tk.Toplevel | None = None
        self._text: tk.Text | None = None
        self._title = title

    def is_open(self) -> bool:
        return self._win is not None and self._win.winfo_exists()

    def show(self, lines: list[str]) -> None:
        existing_win = self._win
        if existing_win is not None and existing_win.winfo_exists():
            existing_win.tkraise()
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
