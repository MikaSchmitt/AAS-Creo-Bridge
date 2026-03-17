# docs/conf.py
from __future__ import annotations

import sys
from pathlib import Path

# This file lives at the repository root.
PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

project = "AAS-Creo-Bridge"
author = "Your Team"
copyright = ""

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "myst_parser",
]

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

templates_path = ["_templates"]
exclude_patterns: list[str] = []

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

latex_engine = "pdflatex"
latex_documents = [
    ("index", "AAS-Creo-Bridge.tex", "AAS-Creo-Bridge Documentation", author, "manual"),
]
latex_elements = {
    "papersize": "a4paper",
    "pointsize": "11pt",
}
