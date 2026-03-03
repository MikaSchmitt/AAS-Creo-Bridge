from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from aas_creo_bridge.app.context import get_aasx_registry


class ConnectionsView(tk.Frame):
    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent)

        # --- Header ---
        title = tk.Label(self, text="Connections", font=("Segoe UI", 16, "bold"))
        title.pack(anchor="w")

        hint = tk.Label(self, text="Link AAS items to Creo models and synchronize them.", fg="gray")
        hint.pack(anchor="w", pady=(6, 10))

        # --- Top: view mode switch (List vs Hierarchical) ---
        top_bar = ttk.Frame(self)
        top_bar.pack(fill="x", pady=(0, 10))

        ttk.Label(top_bar, text="View:").pack(side="left")

        self._view_mode = tk.StringVar(value="list")  # "list" | "hier"
        self.view_mode_list = ttk.Radiobutton(
            top_bar, text="List view", value="list", variable=self._view_mode, command=self._apply_view_mode
        )
        self.view_mode_list.pack(side="left", padx=(8, 0))

        self.view_mode_hier = ttk.Radiobutton(
            top_bar, text="Hierarchical view", value="hier", variable=self._view_mode, command=self._apply_view_mode
        )
        self.view_mode_hier.pack(side="left", padx=(10, 0))

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

        self._aas_tree = ttk.Treeview(aas_panel, columns=("type",), show="tree headings", selectmode="browse")
        self._aas_tree.heading("#0", text="Element")
        self._aas_tree.heading("type", text="Type")
        self._aas_tree.column("#0", width=280, stretch=True)
        self._aas_tree.column("type", width=120, stretch=False)

        # Right: Creo panel
        creo_panel = ttk.Labelframe(body, text="Creo session parts", padding=8)
        creo_panel.grid(row=0, column=2, sticky="nsew", padx=(8, 0))

        creo_panel.grid_rowconfigure(0, weight=1)
        creo_panel.grid_columnconfigure(0, weight=1)

        self.creo_list = tk.Listbox(creo_panel, activestyle="dotbox")
        self.creo_list.grid(row=0, column=0, sticky="nsew")

        self._creo_tree = ttk.Treeview(creo_panel, columns=("kind",), show="tree headings", selectmode="browse")
        self._creo_tree.heading("#0", text="Model")
        self._creo_tree.heading("kind", text="Kind")
        self._creo_tree.column("#0", width=280, stretch=True)
        self._creo_tree.column("kind", width=120, stretch=False)

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
            width = 3
        )
        self.btn_sync_aas_to_creo.pack(fill="none", pady=(0, 8))

        self.btn_sync_creo_to_aas = ttk.Button(actions_inner, text="⬅", command=self._sync_creo_to_aas, width=3)
        self.btn_sync_creo_to_aas.pack(fill="none", pady=(0, 8))

        ttk.Separator(actions_inner, orient="horizontal").pack(fill="x", pady=(8, 8))

        self.btn_break = ttk.Button(actions_inner, text="❌", command=self._break_connection, width=3)
        self.btn_break.pack(fill="none")

        # Initial mode + placeholder content
        self._apply_view_mode()
        self._load_placeholders()

        # Subscribe to AASX registry changes to update views
        get_aasx_registry().add_listener(self._on_registry_changed)

    def _on_registry_changed(self) -> None:
        # Use all currently loaded shells from registry
        registry = get_aasx_registry()
        all_shells = []
        for res in registry.list_open():
            all_shells.extend(res.shells)

        self.set_aas_items(all_shells)

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

    # ---- View mode ----
    def _apply_view_mode(self) -> None:
        mode = self._view_mode.get()

        if mode == "hier":
            self.aas_list.grid_remove()
            self.creo_list.grid_remove()
            self._aas_tree.grid(row=0, column=0, sticky="nsew")
            self._creo_tree.grid(row=0, column=0, sticky="nsew")
        else:
            self._aas_tree.grid_remove()
            self._creo_tree.grid_remove()
            self.aas_list.grid(row=0, column=0, sticky="nsew")
            self.creo_list.grid(row=0, column=0, sticky="nsew")

    def _load_placeholders(self) -> None:
        # List placeholders
        self.set_aas_items(["[No AAS loaded]"])
        self.set_creo_parts(["[No Creo session]"])

        # Tree placeholders
        for item in self._aas_tree.get_children(""):
            self._aas_tree.delete(item)
        for item in self._creo_tree.get_children(""):
            self._creo_tree.delete(item)

        aas_root = self._aas_tree.insert("", "end", text="AAS", values=("—",), open=True)
        self._aas_tree.insert(aas_root, "end", text="Submodels", values=("—",))

        creo_root = self._creo_tree.insert("", "end", text="Creo Session", values=("—",), open=True)
        self._creo_tree.insert(creo_root, "end", text="Parts", values=("—",))

    # ---- Actions (placeholders for now) ----
    def _assert_equal(self) -> None:
        # TODO: compare selected AAS item <-> selected Creo model and mark as equivalent
        pass

    def _sync_aas_to_creo(self) -> None:
        # TODO: push from AAS to Creo (and create model if missing)
        pass

    def _sync_creo_to_aas(self) -> None:
        # TODO: pull from Creo to AAS (and create subelements if missing)
        pass

    def _break_connection(self) -> None:
        # TODO: remove link between selected AAS item and Creo model
        pass