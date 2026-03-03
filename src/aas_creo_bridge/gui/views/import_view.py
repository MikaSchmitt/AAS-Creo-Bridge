from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import simpledialog, ttk, filedialog, messagebox

from aas_creo_bridge.adapters.aasx.AASXImporter import import_aasx
from aas_creo_bridge.app.context import get_aasx_registry, get_logger


class ImportView(tk.Frame):
    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent)

        # ---- State ----
        self._aasx_files: list[Path] = []
        self._repositories: list[str] = []

        # ---- Layout ----
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        header = tk.Frame(self)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        title = tk.Label(header, text="Import", font=("Segoe UI", 16, "bold"))
        title.grid(row=0, column=0, sticky="w")

        hint = tk.Label(header, text="Import AASX packages and manage repositories.", fg="gray")
        hint.grid(row=1, column=0, sticky="w", pady=(6, 0))

        actions = ttk.LabelFrame(self, text="Actions", padding=10)
        actions.grid(row=1, column=0, sticky="ew", pady=(12, 12))
        actions.grid_columnconfigure(4, weight=1)

        self.import_btn = ttk.Button(actions, text="Import AASX…", command=self._on_import_aasx)
        self.import_btn.grid(row=0, column=0, padx=(0, 8), sticky="w")

        self.connect_repo_btn = ttk.Button(actions, text="Connect Repository…", command=self._on_connect_repository)
        self.connect_repo_btn.grid(row=0, column=1, padx=(0, 8), sticky="w")

        self.remove_repo_btn = ttk.Button(actions, text="Remove Repository", command=self._on_remove_repository)
        self.remove_repo_btn.grid(row=0, column=2, padx=(0, 8), sticky="w")

        self.clear_btn = ttk.Button(actions, text="Clear Lists", command=self._on_clear)
        self.clear_btn.grid(row=0, column=3, padx=(0, 8), sticky="w")

        # ---- Main content: AASX/Shells + Repositories ----
        content = tk.Frame(self)
        content.grid(row=2, column=0, sticky="nsew")
        content.grid_rowconfigure(0, weight=1)

        # Make both panes the same size
        content.grid_columnconfigure(0, weight=1, uniform="main_panes")
        content.grid_columnconfigure(1, weight=1, uniform="main_panes")

        # Left: AASX files + shells they contain (Tree)
        left = ttk.LabelFrame(content, text="AASX files and contained Administration Shells", padding=8)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        left.grid_rowconfigure(0, weight=1)
        left.grid_columnconfigure(0, weight=1)

        self.aasx_tree = ttk.Treeview(left, columns=("type",), show="tree headings", selectmode="browse")
        self.aasx_tree.heading("#0", text="Name", anchor="w")
        self.aasx_tree.heading("type", text="Type", anchor="w")
        self.aasx_tree.column("#0", stretch=True, width=420)
        self.aasx_tree.column("type", stretch=False, width=160)

        aasx_scroll = ttk.Scrollbar(left, orient="vertical", command=self.aasx_tree.yview)
        self.aasx_tree.configure(yscrollcommand=aasx_scroll.set)

        self.aasx_tree.grid(row=0, column=0, sticky="nsew")
        aasx_scroll.grid(row=0, column=1, sticky="ns")

        # Right: Connected repositories (List)
        right = ttk.LabelFrame(content, text="Connected repositories", padding=8)
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_rowconfigure(0, weight=1)
        right.grid_columnconfigure(0, weight=1)

        self.repo_list = tk.Listbox(right, height=10, activestyle="dotbox")
        repo_scroll = ttk.Scrollbar(right, orient="vertical", command=self.repo_list.yview)
        self.repo_list.configure(yscrollcommand=repo_scroll.set)

        self.repo_list.grid(row=0, column=0, sticky="nsew")
        repo_scroll.grid(row=0, column=1, sticky="ns")

    # ---- Actions ----
    def _on_import_aasx(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Import AASX",
            filetypes=[("AASX packages", "*.aasx"), ("All files", "*.*")],
        )
        if not file_path:
            return

        path = Path(file_path)

        try:
            result = import_aasx(path)
        except Exception as e:
            messagebox.showerror("AASX import failed", str(e))
            return

        # Track in the view (if you still want this list locally)
        self._aasx_files.append(path)

        # Track app-wide
        aasx_registry = get_aasx_registry()
        aasx_registry.register(result)

        # Add to tree
        aasx_node = self.aasx_tree.insert("", "end", text=path.name, values=("AASX",))

        # Populate shells from adapter result
        if result.shells:
            for shell in result.shells:
                self.aasx_tree.insert(aasx_node, "end", text=shell, values=("AAS",))
        else:
            self.aasx_tree.insert(aasx_node, "end", text="(no shells found)", values=("Info",))

        self.aasx_tree.item(aasx_node, open=True)

    def _on_connect_repository(self) -> None:
        repo = simpledialog.askstring(
            "Connect Repository",
            "Enter repository address (URL or local path):",
            parent=self,
        )
        if not repo:
            return

        repo = repo.strip()
        if not repo:
            return

        if repo in self._repositories:
            messagebox.showinfo("Repository", "This repository is already connected.")
            return

        self._repositories.append(repo)
        self.repo_list.insert("end", repo)

    def _on_remove_repository(self) -> None:
        selection = self.repo_list.curselection()
        if not selection:
            messagebox.showinfo("Remove Repository", "Select a repository to remove.")
            return

        idx = int(selection[0])
        repo_value = self.repo_list.get(idx)

        self.repo_list.delete(idx)
        try:
            self._repositories.remove(repo_value)
        except ValueError:
            # Shouldn't happen, but keep UI resilient
            pass

    def _on_clear(self) -> None:
        self._aasx_files.clear()
        self._repositories.clear()

        for item in self.aasx_tree.get_children(""):
            self.aasx_tree.delete(item)

        self.repo_list.delete(0, "end")