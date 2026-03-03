from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

from aas_creo_bridge import __version__
from aas_creo_bridge.app.context import get_logger, get_aasx_registry
from aas_creo_bridge.app.logging import AppLogger
from aas_creo_bridge.gui.widgets import StatusBar, LeftNav
from aas_creo_bridge.gui.views import HomeView, ImportView, ExplorerView, ConnectionsView, SettingsView, LogWindow


class MainWindow:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("AAS-Creo-Bridge")
        self.root.minsize(900, 600)

        self._views: dict[str, tk.Frame] = {}

        self.logger = get_logger()
        assert isinstance(self.logger, AppLogger)
        self._log_window = LogWindow(self.root)

        self._create_menu_bar()
        self._build_ui()

        # Wire UI to logger (pub/sub)
        self.status_bar.subscribe_to_logger(self.logger)
        self.logger.subscribe(lambda entry: self._log_window.append(entry.format(with_timestamp=True)))

        self.set_status("idle")
        self.logger.info("Application started.")
        self.show_view("Home")

    def _create_menu_bar(self) -> None:
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=False)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open…", command=self._open)
        file_menu.add_command(label="Save", command=self._save)
        file_menu.add_command(label="Save As…", command=self._save_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        aas_menu = tk.Menu(menubar, tearoff=False)
        menubar.add_cascade(label="AAS", menu=aas_menu)
        aas_menu.add_command(label="Import AASX…", command=self._import_aasx)
        aas_menu.add_command(label="Export AASX…", command=self._export_aasx)
        aas_menu.add_separator()
        aas_menu.add_command(label="Validate AAS", command=self._validate_aas)

        creo_menu = tk.Menu(menubar, tearoff=False)
        menubar.add_cascade(label="Creo", menu=creo_menu)
        creo_menu.add_command(label="Connect…", command=self._connect_creo)
        creo_menu.add_command(label="Disconnect", command=self._disconnect_creo)
        creo_menu.add_separator()
        creo_menu.add_command(label="Sync to Creo", command=self._sync_to_creo)
        creo_menu.add_command(label="Sync from Creo", command=self._sync_from_creo)

        tools_menu = tk.Menu(menubar, tearoff=False)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Settings…", command=lambda: self.show_view("Settings"))
        tools_menu.add_command(label="View Logs", command=self._show_full_log)

        help_menu = tk.Menu(menubar, tearoff=False)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._about)

    def _build_ui(self) -> None:
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=0)
        self.root.grid_columnconfigure(1, weight=1)

        self._build_left_nav()
        self._build_content_area()
        self._register_views()
        self._build_status_bar()

    def _build_left_nav(self) -> None:
        views = ["Home", "Import", "Explorer", "Connections", "Settings"]
        compact_icons = {
            "Home": "🏠",
            "Import": "➕",
            "Explorer": "📁",
            "Connections": "🔗",
            "Settings": "⚙",
        }

        self.left_nav = LeftNav(
            self.root,
            views=views,
            on_select_view=self.show_view,
            initial_expanded=False,
            compact_icons=compact_icons,
        )
        self.left_nav.grid(row=0, column=0, sticky="ns")

    def _build_content_area(self) -> None:
        self.content_frame = tk.Frame(self.root, padx=12, pady=12)
        self.content_frame.grid(row=0, column=1, sticky="nsew")
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)

    def _register_views(self) -> None:
        self._views = {}

        registry: list[tuple[str, type[tk.Frame]]] = [
            ("Home", HomeView),
            ("Import", ImportView),
            ("Explorer", ExplorerView),
            ("Connections", ConnectionsView),
            ("Settings", SettingsView),
        ]

        for name, view_cls in registry:
            frame = view_cls(self.content_frame)
            frame.grid(row=0, column=0, sticky="nsew")
            self._views[name] = frame

    def _build_status_bar(self) -> None:
        self.status_bar = StatusBar(
            self.root,
            on_clear_log=self.clear_log,
            on_show_log=self._show_full_log,
            initial_message="Ready.",
        )
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")

    # ---- View switching ----
    def show_view(self, view_name: str) -> None:
        """
        Switch the main content area to the given view and update navigation state.
        """
        frame = self._views.get(view_name)
        if frame is None:
            self.logger.warning(f"Unknown view requested: {view_name!r}")
            messagebox.showwarning("Unknown view", f"No view registered for: {view_name}")
            return

        frame.tkraise()

        if hasattr(self, "left_nav") and self.left_nav is not None:
            self.left_nav.set_active(view_name)

        self.set_status("idle")
        self.logger.info(f"View switched to: {view_name}")

    # ---- Status + logging API ----
    def set_status(self, status: str) -> None:
        """Sets the status of the application ('idle' or 'busy')."""
        self.status_bar.set_status(status)

    def clear_log(self) -> None:
        self.logger.clear()
        self.status_bar.set_last_message("Log cleared.")
        self._log_window.clear()

    def _show_full_log(self) -> None:
        self._log_window.show(self.logger.lines)

    def run(self) -> None:
        """Starts the application main loop."""
        self.root.mainloop()

    # ---- Top menu actions (placeholders for now) ----
    def _open(self) -> None:
        self.logger.info("Open requested.")
        messagebox.showinfo("Open", "TODO: Open a file.")

    def _save(self) -> None:
        self.logger.info("Save requested.")
        messagebox.showinfo("Save", "TODO: Save current work.")

    def _save_as(self) -> None:
        self.logger.info("Save As requested.")
        messagebox.showinfo("Save As", "TODO: Save current work as…")

    def _import_aasx(self) -> None:
        self.show_view("Import")

    def _export_aasx(self) -> None:
        self.logger.info("Export AASX requested.")
        messagebox.showinfo("Export AASX", "TODO: Export an AASX package.")

    def _validate_aas(self) -> None:
        self.set_status("busy")
        self.logger.info("Validate AAS requested.")
        messagebox.showinfo("Validate AAS", "TODO: Validate the current AAS data.")
        self.set_status("idle")

    def _connect_creo(self) -> None:
        self.show_view("Connections")

    def _disconnect_creo(self) -> None:
        self.logger.info("Disconnect requested.")
        messagebox.showinfo("Disconnect", "TODO: Disconnect from Creo.")

    def _sync_to_creo(self) -> None:
        self.set_status("busy")
        self.logger.info("Sync to Creo requested.")
        messagebox.showinfo("Sync to Creo", "TODO: Push AAS data into Creo.")
        self.set_status("idle")

    def _sync_from_creo(self) -> None:
        self.set_status("busy")
        self.logger.info("Sync from Creo requested.")
        messagebox.showinfo("Sync from Creo", "TODO: Pull data from Creo into AAS.")
        self.set_status("idle")

    def _about(self) -> None:
        self.logger.info("About opened.")
        messagebox.showinfo(
            "About",
            f"AAS-Creo Bridge v{__version__}\n\nLink AAS models with Creo Parametric.\n\n© 2026",
        )