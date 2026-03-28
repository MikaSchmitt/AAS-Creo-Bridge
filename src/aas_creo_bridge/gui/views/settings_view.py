from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from aas_creo_bridge.adapters.creo import (
    probe_creoson_status,
    CreosonSettings,
    DEFAULT_JSON_PORT,
    detect_proe_commons,
    load_creoson_settings,
    save_creoson_settings,
    write_setvars_bat,
)


class SettingsView(tk.Frame):
    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent)

        title = tk.Label(self, text="Settings", font=("Segoe UI", 16, "bold"))
        title.pack(anchor="w")

        hint = tk.Label(self, text="Configure CREOSON startup values and generate setvars.bat.", fg="gray")
        hint.pack(anchor="w", pady=(6, 10))

        self._proe_common_var = tk.StringVar()
        self._proe_env_var = tk.StringVar()
        self._java_home_var = tk.StringVar()
        self._json_port_var = tk.StringVar(value=str(DEFAULT_JSON_PORT))
        self._status_var = tk.StringVar(value="")

        form = ttk.LabelFrame(self, text="CREOSON", padding=12)
        form.pack(fill="x", padx=4, pady=4)

        form.columnconfigure(1, weight=1)

        ttk.Label(form, text="PROE_COMMON").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=(0, 8))
        self._proe_common_combo = ttk.Combobox(
            form,
            textvariable=self._proe_common_var,
            state="normal",
        )
        self._proe_common_combo.grid(row=0, column=1, sticky="ew", pady=(0, 8))
        ttk.Button(form, text="Browse", command=self._choose_proe_common).grid(row=0, column=2, padx=(8, 0),
                                                                               pady=(0, 8))

        ttk.Label(form, text="PROE_ENV").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=(0, 8))
        ttk.Combobox(
            form,
            textvariable=self._proe_env_var,
            values=("x86e_win64", "x86e_win32"),
            state="readonly",
        ).grid(row=1, column=1, sticky="w", pady=(0, 8))

        ttk.Label(form, text="JAVA_HOME").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=(0, 8))
        ttk.Entry(form, textvariable=self._java_home_var).grid(row=2, column=1, sticky="ew", pady=(0, 8))
        ttk.Button(form, text="Browse", command=self._choose_java_home).grid(row=2, column=2, padx=(8, 0), pady=(0, 8))

        ttk.Label(form, text="JSON_PORT").grid(row=3, column=0, sticky="w", padx=(0, 8))
        ttk.Entry(form, textvariable=self._json_port_var, state="disabled").grid(row=3, column=1, sticky="w")

        actions = ttk.Frame(self)
        actions.pack(fill="x", padx=4, pady=(8, 0))

        ttk.Button(actions, text="Save", command=self._save).pack(side="left")
        ttk.Button(actions, text="Reload", command=self._load).pack(side="left", padx=(8, 0))
        ttk.Button(actions, text="Test CREOSON", command=self._test_creoson).pack(side="left", padx=(8, 0))

        status_label = ttk.Label(self, textvariable=self._status_var, foreground="gray")
        status_label.pack(anchor="w", padx=4, pady=(8, 0))

        self._load()

    def _load(self) -> None:
        settings = load_creoson_settings()
        self._populate_proe_common_options(settings.proe_common)
        self._proe_common_var.set(settings.proe_common)
        self._proe_env_var.set(settings.proe_env)
        self._java_home_var.set(settings.java_home)
        self._json_port_var.set(str(DEFAULT_JSON_PORT))
        self._status_var.set("Loaded current settings.")

    def _populate_proe_common_options(self, selected: str = "") -> None:
        options: list[str] = []

        for path in detect_proe_commons():
            candidate = str(path).strip()
            if candidate and candidate not in options:
                options.append(candidate)

        selected = selected.strip()
        if selected and selected not in options:
            options.append(selected)

        self._proe_common_combo.configure(values=options)

    def _save(self) -> None:
        proe_common = self._proe_common_var.get().strip()
        if not proe_common:
            messagebox.showerror("Missing value", "PROE_COMMON must be set to the Creo 'Common Files' folder.")
            return
        if not Path(proe_common).is_dir():
            messagebox.showerror("Invalid path", "PROE_COMMON must point to an existing folder.")
            return

        java_home = self._java_home_var.get().strip()
        if not java_home:
            messagebox.showerror("Missing value", "JAVA_HOME cannot be empty.")
            return
        if java_home.lower() != "jre" and not Path(java_home).is_dir():
            messagebox.showerror("Invalid path", "JAVA_HOME must be 'jre' or an existing JRE folder.")
            return

        settings = CreosonSettings(
            proe_common=proe_common,
            proe_env=self._proe_env_var.get().strip() or "x86e_win64",
            java_home=java_home,
            json_port=DEFAULT_JSON_PORT,
        )

        save_creoson_settings(settings)
        setvars_path = write_setvars_bat(settings)
        self._populate_proe_common_options(proe_common)
        self._status_var.set(f"Saved. Generated: {setvars_path}")
        messagebox.showinfo("Settings saved", f"setvars.bat updated:\n{setvars_path}")

    def _choose_proe_common(self) -> None:
        selected = filedialog.askdirectory(title="Select Creo Common Files folder")
        if selected:
            self._proe_common_var.set(selected)
            self._populate_proe_common_options(selected)

    def _choose_java_home(self) -> None:
        selected = filedialog.askdirectory(title="Select JAVA_HOME folder")
        if selected:
            self._java_home_var.set(selected)

    def _test_creoson(self) -> None:
        result = probe_creoson_status(port=DEFAULT_JSON_PORT)
        creoson_status = "running" if result.creoson_running else "not running"
        creo_status = "connected" if result.creo_connected else "not connected"

        messagebox.showinfo(
            "CREOSON Test",
            f"CREOSON is {creoson_status}.\nCreo is {creo_status}.\n\n{result.details}",
        )
