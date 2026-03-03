from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from aas_creo_bridge.app.context import get_aasx_registry, get_logger


class ExplorerView(tk.Frame):
    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent)

        # --- Header ---
        title = tk.Label(self, text="Explorer", font=("Segoe UI", 16, "bold"))
        title.pack(anchor="w")

        hint = tk.Label(self, text="Browse AAS structures and objects.", fg="gray")
        hint.pack(anchor="w", pady=(6, 10))

        # --- Top bar: AAS selector dropdown ---
        top_bar = tk.Frame(self)
        top_bar.pack(fill="x", pady=(0, 10))

        tk.Label(top_bar, text="AAS:").pack(side="left")

        self._selected_aas = tk.StringVar(value="No AAS loaded")
        self.aas_selector = ttk.Combobox(
            top_bar,
            textvariable=self._selected_aas,
            state="disabled",  # enabled once AAS options exist
            width=48,
            values=[],
        )
        self.aas_selector.pack(side="left", padx=(8, 0), fill="x", expand=True)
        self.aas_selector.bind("<<ComboboxSelected>>", self._on_aas_selected)

        # --- Main area: two side-by-side views (tree + details frame) ---
        main_pane = ttk.Panedwindow(self, orient="horizontal")
        main_pane.pack(fill="both", expand=True)

        # Left: AAS structure tree
        left = ttk.Frame(main_pane, padding=(0, 0, 8, 0))
        main_pane.add(left, weight=1)

        self.aas_tree = ttk.Treeview(left, columns=("type",), show="tree headings", selectmode="browse")
        self.aas_tree.heading("#0", text="Element")
        self.aas_tree.heading("type", text="Type")
        self.aas_tree.column("#0", width=320, stretch=True)
        self.aas_tree.column("type", width=140, stretch=False)

        y_scroll = ttk.Scrollbar(left, orient="vertical", command=self.aas_tree.yview)
        self.aas_tree.configure(yscrollcommand=y_scroll.set)

        self.aas_tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")

        left.grid_rowconfigure(0, weight=1)
        left.grid_columnconfigure(0, weight=1)

        self.aas_tree.bind("<<TreeviewSelect>>", self._on_tree_selection_changed)

        # Right: details frame (to be populated based on selected subelement)
        right = ttk.Frame(main_pane, padding=(8, 0, 0, 0))
        main_pane.add(right, weight=2)

        header = ttk.Label(right, text="Details", font=("Segoe UI", 12, "bold"))
        header.pack(anchor="w")

        self.details_container = ttk.Frame(right)
        self.details_container.pack(fill="both", expand=True, pady=(8, 0))

        self.details_placeholder = ttk.Label(
            self.details_container,
            text="Select an element in the tree to see its details.",
            foreground="gray",
        )
        self.details_placeholder.pack(anchor="w")

        # Initial empty state (no AAS manager yet)
        self._clear_tree()
        self._show_details_text("No AAS loaded. Import/load an AAS to browse its structure.")

        # Subscribe to AASX registry changes to update views
        get_aasx_registry().add_listener(self._on_registry_changed)

    def _on_registry_changed(self) -> None:
        # Use all currently loaded shells from registry
        registry = get_aasx_registry()
        all_shells = []
        for res in registry.list_by_path_open():
            all_shells.extend(res.shells)

        self.set_aas_options(all_shells)

    # ---- Hooks for a future AAS manager/controller ----
    def set_aas_options(self, names: list[str], *, select_first: bool = True) -> None:
        """
        Populate the dropdown with available AAS display names/ids.
        Enables the combobox when at least one entry exists.
        """
        self.aas_selector["values"] = names

        if not names:
            self.clear_aas_options()
            return

        self.aas_selector.configure(state="readonly")

        if select_first:
            self._selected_aas.set(names[0])
            self._on_aas_selected()

    def clear_aas_options(self) -> None:
        """Reset dropdown + views to the empty 'no AAS loaded' state."""
        self.aas_selector.configure(state="disabled")
        self.aas_selector["values"] = []
        self._selected_aas.set("No AAS loaded")
        self._clear_tree()
        self._show_details_text("No AAS loaded. Import/load an AAS to browse its structure.")

    def get_selected_aas(self) -> str | None:
        """Return the currently selected AAS name/id, or None if nothing is loaded."""
        value = (self._selected_aas.get() or "").strip()
        if not value or value == "No AAS loaded":
            return None
        return value

    # ---- UI event handlers ----
    def _on_aas_selected(self, _event: object | None = None) -> None:
        """
        Called when the user picks an AAS in the dropdown.
        Replace the placeholder behavior with real AAS loading + tree building.
        """
        selected = self.get_selected_aas()
        get_logger().info(f"AAS selected in Explorer: {selected}")
        if selected is None:
            self._clear_tree()
            self._show_details_text("No AAS loaded. Import/load an AAS to browse its structure.")
            return

        # For now, just reset the tree and show placeholder details.
        self._clear_tree()
        self._load_placeholder_tree(aas_name=selected)
        self._show_details_text(f"Selected AAS: {selected}")

    def _on_tree_selection_changed(self, _event: object | None = None) -> None:
        """
        Called when the user selects a node in the AAS tree.
        Here is where you'd populate the details frame with subelement info.
        """
        selection = self.aas_tree.selection()
        if not selection:
            self._show_details_text("Select an element in the tree to see its details.")
            return

        item_id = selection[0]
        label = self.aas_tree.item(item_id, "text")
        element_type = ""
        values = self.aas_tree.item(item_id, "values")
        if values:
            element_type = str(values[0])

        self._show_details_text(f"Element: {label}\nType: {element_type}")

    # ---- Helpers ----
    def _show_details_text(self, text: str) -> None:
        for child in self.details_container.winfo_children():
            child.destroy()

        lbl = ttk.Label(self.details_container, text=text, justify="left")
        lbl.pack(anchor="w")

    def _clear_tree(self) -> None:
        for item in self.aas_tree.get_children(""):
            self.aas_tree.delete(item)

    def _load_placeholder_tree(self, aas_name: str = "") -> None:
        root_label = aas_name or "AAS"
        root = self.aas_tree.insert("", "end", text=root_label, values=("AssetAdministrationShell",), open=True)

        sm = self.aas_tree.insert(root, "end", text="Submodels", values=("Collection",), open=True)
        sm1 = self.aas_tree.insert(sm, "end", text="Identification", values=("Submodel",), open=True)
        self.aas_tree.insert(sm1, "end", text="SerialNumber", values=("Property",))
        self.aas_tree.insert(sm1, "end", text="Manufacturer", values=("Property",))

        sm2 = self.aas_tree.insert(sm, "end", text="Documentation", values=("Submodel",), open=True)
        self.aas_tree.insert(sm2, "end", text="Manual.pdf", values=("File",))