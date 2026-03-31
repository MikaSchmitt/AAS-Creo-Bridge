from __future__ import annotations

import json
import tkinter as tk
from dataclasses import asdict
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from aas_creo_bridge.app.context import (
    get_aasx_registry,
    get_creo_session_tracker,
    get_creoson_client,
    get_logger,
    get_sync_manager,
)
from aas_creo_bridge.creo_adapter import SessionChangeAction, CreoSessionFile
from aas_creo_bridge.creo_adapter.bom_export import get_assembly_data


class ConnectionsView(tk.Frame):
    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent)

        # --- Header ---
        title = tk.Label(self, text="Connections", font=("Segoe UI", 16, "bold"))
        title.pack(anchor="w")

        hint = tk.Label(self, text="Link AAS items to Creo models and synchronize them.", fg="gray")
        hint.pack(anchor="w", pady=(6, 10))

        # --- Top bar ---
        top_bar = ttk.Frame(self)
        top_bar.pack(fill="x", pady=(0, 10))

        self.btn_export_bom = ttk.Button(top_bar, text="Export BOM from Creo", command=self._export_bom)
        self.btn_export_bom.pack(side="left")

        # --- Main: 3 columns (AAS | actions | Creo parts) ---
        body = ttk.Frame(self)
        body.pack(fill="both", expand=True)

        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=0)
        body.grid_columnconfigure(2, weight=1)

        # Left: AAS panel
        aas_panel = ttk.Labelframe(body, text="AAS", padding=8)
        aas_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        aas_panel.grid_rowconfigure(0, weight=1)
        aas_panel.grid_columnconfigure(0, weight=1)

        self.aas_list = tk.Listbox(aas_panel, activestyle="dotbox")
        self.aas_list.grid(row=0, column=0, sticky="nsew")
        self.aas_list.bind("<<ListboxSelect>>", lambda _: self._on_aas_list_select)

        # Right: Creo panel
        creo_panel = ttk.Labelframe(body, text="Creo session parts", padding=8)
        creo_panel.grid(row=0, column=2, sticky="nsew", padx=(8, 0))

        creo_panel.grid_rowconfigure(0, weight=1)
        creo_panel.grid_columnconfigure(0, weight=1)

        self.creo_list = tk.Listbox(creo_panel, activestyle="dotbox")
        self.creo_list.grid(row=0, column=0, sticky="nsew")
        self.creo_list.bind("<<ListboxSelect>>", self._on_creo_list_select)

        # Middle: action buttons
        actions = ttk.Frame(body)
        actions.grid(row=0, column=1, sticky="ns")
        actions.grid_rowconfigure(0, weight=1)

        actions_inner = ttk.Frame(actions)
        actions_inner.grid(row=0, column=0, sticky="n")

        self.btn_assert_equal = ttk.Button(actions_inner, text="≡", command=self._assert_equal, width=3)
        self.btn_assert_equal.pack(fill="none", pady=(25, 8))

        self.btn_sync_aas_to_creo = ttk.Button(
            actions_inner,
            text="➡",
            command=self._sync_aas_to_creo,
            width=3
        )
        self.btn_sync_aas_to_creo.pack(fill="none", pady=(0, 8))

        self.btn_sync_creo_to_aas = ttk.Button(actions_inner, text="⬅", command=self._sync_creo_to_aas, width=3)
        self.btn_sync_creo_to_aas.pack(fill="none", pady=(0, 8))

        ttk.Separator(actions_inner, orient="horizontal").pack(fill="x", pady=(8, 8))

        self.btn_break = ttk.Button(actions_inner, text="❌", command=self._break_connection, width=3)
        self.btn_break.pack(fill="none")

        # Initial placeholder content
        self._load_placeholders()

        # Subscribe to AASX registry changes to update views
        get_aasx_registry().add_listener(self._on_registry_changed)
        get_creo_session_tracker().add_listener(self._on_creo_session_changed)

        tracker = get_creo_session_tracker()
        self.set_creo_parts([file for file in tracker.state.files])

    def _on_registry_changed(self, action: str, shells: list[str]) -> None:
        # Use all currently loaded shells from registry
        registry = get_aasx_registry()
        all_shells = []
        for res in registry.list_by_path_open():
            all_shells.extend(res.shells)

        self.set_aas_items(all_shells)

    def _on_creo_session_changed(self, action: SessionChangeAction, parts: list[CreoSessionFile]) -> None:
        if action == SessionChangeAction.add:
            pass
        if action == SessionChangeAction.remove:
            pass
        if action == SessionChangeAction.active:
            return
        if action == SessionChangeAction.revision:
            return
        tracker = get_creo_session_tracker()
        self.set_creo_parts([file for file in tracker.state.files])

    # ---- Public hooks for later wiring ----
    def set_aas_items(self, items: list[str]) -> None:
        """Populate the AAS list (List view)."""
        self.aas_list.delete(0, tk.END)
        for it in items:
            self.aas_list.insert(tk.END, it)

    def set_creo_parts(self, parts: list[str]) -> None:
        """Populate the Creo parts list (List view)."""
        self.creo_list.delete(0, tk.END)
        for p in parts:
            self.creo_list.insert(tk.END, p)

    def _load_placeholders(self) -> None:
        self.set_aas_items(["[No AAS loaded]"])
        self.set_creo_parts(["[No Creo session]"])

    # ---- Actions (placeholders for now) ----
    def _assert_equal(self) -> None:
        # TODO: compare selected AAS item <-> selected Creo model and mark as equivalent
        pass

    def _sync_aas_to_creo(self) -> None:
        selection = None

        try:
            selection = self.aas_list.selection_get()
        except tk.TclError:
            pass
        try:
            selection = self.creo_list.selection_get()
        except tk.TclError:
            pass
        if not selection:
            return

        sync_manager = get_sync_manager()
        sync_manager.sync_aas_to_creo(selection)

        # TODO: push from AAS to Creo (and create model if missing)
        pass

    def _sync_creo_to_aas(self) -> None:
        # TODO: pull from Creo to AAS (and create subelements if missing)
        pass

    def _break_connection(self) -> None:
        # TODO: remove link between selected AAS item and Creo model
        pass

    def _export_bom(self) -> None:
        tracker = get_creo_session_tracker()
        active_file_name = tracker.state.active_file_name
        if not active_file_name:
            messagebox.showinfo("Export BOM", "No active Creo model found.")
            return

        client = get_creoson_client()
        if client is None:
            messagebox.showerror("Export BOM", "Creoson client is unavailable.")
            return

        default_name = f"{Path(active_file_name).stem}_bom.json"
        export_path = filedialog.asksaveasfilename(
            title="Export BOM as JSON",
            defaultextension=".json",
            initialfile=default_name,
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not export_path:
            return

        try:
            bom = get_assembly_data(
                client,
                file_=active_file_name,
                get_transforms=True,
                include_parameters=True,
                include_mass_props=True,
                include_bounding_box=True,
            )
            with open(export_path, "w", encoding="utf-8") as out_file:
                json.dump(asdict(bom), out_file, indent=2, ensure_ascii=True)
            messagebox.showinfo("Export BOM", f"BOM exported to:\n{export_path}")
        except Exception as exc:
            get_logger(__name__).error("BOM export failed for '%s': %r", active_file_name, exc, exc_info=True)
            messagebox.showerror("Export BOM", f"Failed to export BOM:\n{exc}")

    def _on_aas_list_select(self, event: tk.Event) -> None:
        selection = self.aas_list.selection_get()
        sync_manager = get_sync_manager()
        link = sync_manager.get_link_by_aas_id(selection)
        self.creo_list.select_set(link.creo_model_name, link.creo_model_name)

    def _on_creo_list_select(self, event: tk.Event) -> None:
        selection = self.creo_list.selection_get()
        sync_manager = get_sync_manager()
        link = sync_manager.get_link_by_aas_id(selection)
        self.aas_list.select_set(link.aas_shell_id, link.aas_shell_id)
