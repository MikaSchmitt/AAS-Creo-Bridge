from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from basyx.aas.model import AssetAdministrationShell, Property, MultiLanguageProperty, File

from aas_adapter import check_expected_model, get_child_elements, get_value
from aas_creo_bridge.adapters.creo import CreoSessionFile, SessionChangeAction
from aas_creo_bridge.app.context import get_aasx_registry, get_logger, get_creo_session_tracker, get_sync_manager


class ExplorerView(tk.Frame):
    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent)

        # --- Header ---
        self._node_properties: dict[str, list[list[str]]] = {}
        title = tk.Label(self, text="Explorer", font=("Segoe UI", 16, "bold"))
        title.pack(anchor="w")

        hint = tk.Label(self, text="Browse AAS structures and objects.", fg="gray")
        hint.pack(anchor="w", pady=(6, 10))

        # --- Top bar: AAS selector dropdown ---
        top_bar = tk.Frame(self)
        top_bar.pack(fill="x", pady=(0, 10))

        tk.Label(top_bar, text="AAS:").pack(side="left")

        self._selected_aas = tk.StringVar(value="No AAS loaded")
        self._follow_active_part = tk.BooleanVar(value=True)
        self.aas_selector = ttk.Combobox(
            top_bar,
            textvariable=self._selected_aas,
            state="disabled",  # enabled once AAS options exist
            width=48,
            values=[],
        )
        self.aas_selector.pack(side="left", padx=(8, 0), fill="x", expand=True)
        self.aas_selector.bind("<<ComboboxSelected>>", self._on_aas_selected)

        self.follow_active_check = ttk.Checkbutton(
            top_bar,
            text="Follow active part in Creo",
            variable=self._follow_active_part,
        )
        self.follow_active_check.pack(side="left", padx=(12, 0))

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

        self.details_container = tk.Frame(right)
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

        tracker = get_creo_session_tracker()
        tracker.add_listener(self._on_creo_session_changed)

    def _on_registry_changed(self, action: str, shells: list[str]) -> None:
        # Use all currently loaded shells from registry
        registry = get_aasx_registry()
        all_shells = []
        for res in registry.list_by_path_open():
            all_shells.extend(res.shells)

        self.set_aas_options(all_shells)

    def _on_creo_session_changed(self, action: SessionChangeAction, parts: list[CreoSessionFile]) -> None:
        sync_manager = get_sync_manager()
        match action:
            case SessionChangeAction.add:
                return
            case SessionChangeAction.remove:
                return
            case SessionChangeAction.active:
                if not self._follow_active_part.get() or not parts:
                    return

                link = sync_manager.get_link_by_creo_model(parts[0].file_name)
                if not link:
                    return

                aas_id = link.aas_shell_id
                if aas_id:
                    self._selected_aas.set(aas_id)
                    self._on_aas_selected()
                return
            case SessionChangeAction.revision:
                return

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
        self._load_tree(aas_name=selected)
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

        properties = self._node_properties.get(item_id, [])
        properties_text = "\n".join(f" {item[0]}: {item[1]}" for item in properties)
        if not properties_text:
            properties_text = " (none)"

        self._show_details_text(
            f"Element: {label}\nType: {element_type}\nProperties:\n{properties_text}"
        )

    # ---- Helpers ----
    def _show_details_text(self, text: str) -> None:
        for child in self.details_container.winfo_children():
            child.destroy()

        # Use a Text widget for selectable/copyable text
        text_widget = tk.Text(
            self.details_container,
            height=10,
            width=50,
            wrap="word",
            state="disabled",  # Read-only
            bg=self.details_container.cget("bg"),
            relief="flat",
            bd=0,
            font=("Segoe UI", 10)
        )
        text_widget.pack(anchor="w", fill="both", expand=True)

        # Enable temporarily to insert text, then disable again
        text_widget.config(state="normal")
        text_widget.insert("1.0", text)
        text_widget.config(state="disabled")

    def _clear_tree(self) -> None:
        self._node_properties.clear()
        for item in self.aas_tree.get_children(""):
            self.aas_tree.delete(item)

    def _build_tree(self, parent, object_store, element):
        index = 0
        for element in get_child_elements(object_store, element):
            if not isinstance(element, Property | MultiLanguageProperty | File):
                # if it's an element of a submodel element list use an index instead if id_short
                if "generated_submodel_list" in element.id_short:
                    id_short = f"[{index}]"
                    index += 1
                else:
                    id_short = element.id_short

                node = self.aas_tree.insert(parent, "end", text=id_short, values=(element.__class__.__name__,))
                # self._node_properties.setdefault(node, []).append([element.id_short, str(get_value(element))])
                self._build_tree(node, object_store, element)
            elif isinstance(element, Property):
                self._node_properties.setdefault(parent, []).append([element.id_short, str(get_value(element))])
            elif isinstance(element, MultiLanguageProperty):
                mlp = get_value(element)
                if mlp:
                    # get the en field or fallback to the first element if it doesn't exist
                    value = mlp.get("en") or next(iter(mlp.values()), None)
                    self._node_properties.setdefault(parent, []).append([element.id_short, str(value)])
            elif isinstance(element, File):
                self._node_properties.setdefault(parent, []).append([element.id_short, str(get_value(element))])
                self._node_properties.setdefault(parent, []).append([element.id_short, str(element.content_type)])

        return

    def _load_tree(self, aas_name: str = ""):
        if not aas_name:
            return
        self._clear_tree()

        registry = get_aasx_registry()
        aasx = registry.get(aas_name)
        if not aasx:
            return

        aas = aasx.object_store.get_identifiable(aas_name)
        check_expected_model(aas, AssetAdministrationShell)

        root = self.aas_tree.insert("", "end", text=aas_name, values=("AssetAdministrationShell",), open=True)
        self._build_tree(root, aasx.object_store, aas)
